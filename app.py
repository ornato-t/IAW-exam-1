import uuid
import re
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.exceptions import HTTPException, BadRequest, Unauthorized, NotFound, Forbidden, InternalServerError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

import ads
import visits
import user_db
from models import User
import image_handler

app = Flask(__name__)
app.config["SECRET_KEY"] = uuid.uuid4().hex

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def login(username):
    db_user = user_db.get_user(username)

    if db_user is not None:
        user = User(username=db_user['username'], email=db_user['email'], landlord=db_user['landlord'], name=db_user['name'], password=db_user['password'])
    else:
        user = None

    return user

@app.errorhandler(Exception)
def handle_exception(e):
    # HTTP error
    if isinstance(e, HTTPException):
        return render_template("error.html", code=f'{e.code} - {e.name}', message=e.description)

    # Non HTTP error. To avoid leaking internal data they are masked as 500s and printed to the console
    print(str(e))
    return render_template("error.html", code='500 - Internal Server Error', message="Errore interno.")

@app.route('/')
def get_home():
    try:
        sort_price_str = request.args.get('sort_price', default='true', type=str)
        sort_price = sort_price_str.lower() == 'true'

        advertisements = ads.get_public_ads(sort_price)

        return render_template('home.html', advertisements=advertisements, sort_price=sort_price)
    except Exception as e:
        print('ERROR', str(e))
        flash('Errore interno durante il caricamento della pagina', 'danger')

        return redirect(url_for('get_home'))

@app.route('/advertisement/<int:id>')
def get_advertisement(id):
    try:
        advertisement = ads.get_ad_by_id(id=id)
        if advertisement is None:
            raise NotFound('Nessun annuncio corrispondente trovato')

        if not advertisement['available'] and (not current_user.is_authenticated or advertisement['landlord_username'] != current_user.username):
            raise NotFound('Nessun annuncio corrispondente trovato')    # Using 404 rather than 401 for security reasons: avoid leaking info on hidden houses

        already_seen = False
        pending_visit = False

        if current_user.is_authenticated:
            already_seen = visits.has_user_visited(username=current_user.username, advertisement_id=id)
            pending_visit = visits.is_user_waiting_visit(username=current_user.username, advertisement_id=id)

        return render_template('advertisement.html', ad=advertisement, seen=already_seen, pending=pending_visit)
    except HTTPException as e:
        flash(str(e), 'warning')
        return redirect(url_for('get_home'))
    except Exception as e:
        print('ERROR', str(e))
        flash('Errore interno durante il caricamento della pagina', 'danger')
        
        return redirect(url_for('get_home'))

@app.route('/advertisement/<int:id>/visit')
@login_required 
def get_visit(id):
    try:
        advertisement = ads.get_ad_by_id(id=id)
        if advertisement is None:
            raise NotFound('Nessun annuncio corrispondente trovato')

        if visits.has_user_visited(username=current_user.username, advertisement_id=id):
            raise Forbidden('Non è possibile visitare più volte la stessa casa')
        
        if visits.is_user_waiting_visit(username=current_user.username, advertisement_id=id):
            raise Forbidden('Hai già prenotato una visita a questa casa. Attendi la conferma')

        if current_user.username == advertisement['landlord_username']:
            raise Forbidden('Non puoi visitare una casa da te inserzionata')

        visit_list = visits.get_visits_next_week(advertisement_id=id)

        return render_template('visit.html', ad=advertisement, visit=visit_list)
    except HTTPException as e:
        flash(str(e), 'warning')
        return redirect(url_for('get_home'))
    except Exception as e:
        print('ERROR', str(e))
        flash('Errore interno durante il caricamento della pagina', 'danger')
        
        return redirect(url_for('get_home'))

@app.route('/advertisement/<int:id>/visit', methods=['POST'])
@login_required 
def post_visit(id):
    try:
        # Check if url is correct and user permissions
        advertisement = ads.get_ad_by_id(id=id)
        if advertisement is None:
            raise NotFound('Nessun annuncio corrispondente trovato')

        if visits.has_user_visited(username=current_user.username, advertisement_id=id):
            raise Forbidden('Non è possibile visitare più volte la stessa casa')
        
        if visits.is_user_waiting_visit(username=current_user.username, advertisement_id=id):
            raise Forbidden('Hai già prenotato una visita a questa casa. Attendi la conferma')

        if current_user.username == advertisement['landlord_username']:
            raise Forbidden('Non puoi visitare una casa da te inserzionata')

        req = request.form.to_dict()

        # Check if form is valid
        if not re.match(r'\d{2}\/\d{2}\/\d{4}@\d', req['visit']):
            raise BadRequest("Errore di formattazione nel campo 'visit'")
        if req['type'] not in ['physical', 'virtual']:
            raise BadRequest("Errore di formattazione nel campo 'type'")

        # Parse form data
        visit_date_time = req['visit'].split('@')
        visit_date = datetime.strptime(visit_date_time[0], '%d/%m/%Y')
        visit_time = int(visit_date_time[1])

        visit_virtual = False
        if req['type'] == 'virtual':
            visit_virtual = True

        # Insert the visit in the database
        if not visits.insert_visit(username=current_user.username, advertisement_id=id, date=visit_date, time=visit_time, virtual=visit_virtual):
            raise InternalServerError('Errore durante l\'aggiunta della visita. Riprova più tardi')

        return redirect(url_for('get_personal'))
    except HTTPException as e:
        flash(str(e), 'warning')
        return redirect(url_for('get_home'))
    except Exception as e:
        print('ERROR', str(e))
        flash('Errore interno durante il caricamento della pagina', 'danger')
        
        return redirect(url_for('get_home'))

@app.route('/advertisement/<int:id>/edit')
@login_required 
def get_edit_advertisement(id):
    try:
        if not current_user.landlord:
            raise Forbidden("Solo i locatori possono modificare gli annunci")

        advertisement = ads.get_ad_by_id_raw(id=id)

        if advertisement is None:
            raise NotFound('Nessun annuncio corrispondente trovato')

        if advertisement['landlord_username'] != current_user.username:
            raise Forbidden("Non puoi modificare l'annuncio di un altro locatore")

        return render_template('edit_ad.html', ad=advertisement)
    except HTTPException as e:
        flash(str(e), 'warning')
        return redirect(url_for('get_personal'))
    except Exception as e:
        print('ERROR', str(e))
        flash('Errore interno durante il caricamento della pagina', 'danger')
        
        return redirect(url_for('get_personal'))

@app.route('/advertisement/<int:id>/edit', methods=['post'])
@login_required 
def post_edit_advertisement(id):
    try:
        req = request.form.to_dict()
        files = request.files.getlist('immagine')

        # Check if form is valid
        if not re.match(r'.+', req['title']):
            raise BadRequest("Errore di formattazione nel campo 'title'")
        if not re.match(r'.+', req['description']):
            raise BadRequest("Errore di formattazione nel campo 'description'")
        if not re.match(r'^[123456]$', req['rooms']):
            raise BadRequest("Errore di formattazione nel campo 'rooms'")
        if not re.match(r'\d+', req['rent']):
            raise BadRequest("Errore di formattazione nel campo 'rent'")
        if req['type'] not in ['detached', 'flat', 'loft', 'villa']:
            raise BadRequest("Errore di formattazione nel campo 'type'")
        if req['furniture'] not in ['true', 'false']:
            raise BadRequest("Errore di formattazione nel campo 'furniture'")
        if req['available'] not in ['true', 'false']:
            raise BadRequest("Errore di formattazione nel campo 'available'")

        # Check house ownership
        landlord_db = ads.get_ad_landlord(advertisement_id=id)
        if landlord_db is None:
            raise InternalServerError("Errore durante la modifica dell'inserzione")
        elif current_user.username != landlord_db:
            raise Forbidden("Non puoi modificare l'annuncio di un altro locatore")

        paths = []  # If no images were uploaded this remains empty. If it is empty, the images in the DB aren't udpated

        # Check if any images were uploaded
        if not any(file.filename == '' for file in files):
            # Delete the existing images
            images = ads.get_ad_images(advertisement_id=id)
            if len(images) == 0:
                raise InternalServerError("Erorre durante la modifica delle immagini")

            image_handler.delete_images(path_list=images)

            # Save the new images. Only parse the first 5 images (imposing upload cap, can't do it on client)
            for file in files[:5]:
                paths.append(image_handler.save_image(image_form=file))

        # Update the advertisement in the database
        if not ads.edit_ad(title=req['title'], available=req['available'], description=req['description'], furniture=req['furniture'], rent=req['rent'], rooms=req['rooms'], ad_type=req['type'], pictures=paths, landlord_username=current_user.username, advertisement_id=id):
            raise InternalServerError('Errore durante la modifica dell\'inserzione')

        flash('Inserzione modificata con successo', 'success')
        return redirect(url_for('get_advertisement', id=id))
    except image_handler.ImageException as e:
        flash("Errore durante il salvataggio dell'immagine: "+e.file, 'warning')
        return redirect(url_for('get_new_advertisement'))
    except HTTPException as e:
        flash(str(e), 'warning')
        return redirect(url_for('get_personal'))

@app.route('/advertisement/new')
@login_required
def get_new_advertisement():
    try:
        if not current_user.landlord:
            raise Forbidden("Solo i locatori possono creare nuovi annunci")
            
        return render_template('new_ad.html')
    except HTTPException as e:
        flash(str(e), 'warning')
        return redirect(url_for('get_personal'))

@app.route('/advertisement/new', methods=['post'])
@login_required 
def post_new_advertisement():
    try:
        req = request.form.to_dict()
        files = request.files.getlist('immagine')

        # Check if form is valid
        if not re.match(r'.+', req['title']):
            raise BadRequest("Errore di formattazione nel campo 'title'")
        if not re.match(r'.+', req['adress']):
            raise BadRequest("Errore di formattazione nel campo 'adress'")
        if not re.match(r'.+', req['description']):
            raise BadRequest("Errore di formattazione nel campo 'description'")
        if not re.match(r'^[123456]$', req['rooms']):
            raise BadRequest("Errore di formattazione nel campo 'rooms'")
        if not re.match(r'\d+', req['rent']):
            raise BadRequest("Errore di formattazione nel campo 'rent'")
        if req['type'] not in ['detached', 'flat', 'loft', 'villa']:
            raise BadRequest("Errore di formattazione nel campo 'type'")
        if req['furniture'] not in ['true', 'false']:
            raise BadRequest("Errore di formattazione nel campo 'furniture'")
        if req['available'] not in ['true', 'false']:
            raise BadRequest("Errore di formattazione nel campo 'available'")

        # Only parse the first 5 images (imposing upload cap, can't do it on client)
        paths = []
        for file in files[:5]:
            paths.append(image_handler.save_image(image_form=file))

        if not ads.insert_ad(title=req['title'], adress=req['adress'], available=req['available'], description=req['description'], furniture=req['furniture'], rent=req['rent'], rooms=req['rooms'], ad_type=req['type'], pictures=paths, landlord_username=current_user.username):
            raise InternalServerError('Errore durante il salvataggio dell\'inserzione')

        flash('Inserzione creata con successo', 'success')
        return redirect(url_for('get_personal'))
    except image_handler.ImageException as e:
        flash("Errore durante il salvataggio dell'immagine: "+e.file, 'warning')
        return redirect(url_for('get_new_advertisement'))
    except HTTPException as e:
        flash(str(e), 'warning')
        return redirect(url_for('get_new_advertisement'))

@app.route('/about')
def get_about():
    return render_template('about.html')

@app.route('/signup')
def get_signup():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def post_signup():
    try:
        user = request.form.to_dict()
        validate_signup(user)   # Raises an exception if the form is invalid

        if user_db.user_exists(user['username']):
            raise BadRequest("Username già esistente. Scegliere un altro nome utente.")

        user['password'] = generate_password_hash(user['password'])
        
        if not user_db.add_user(user):  # Returns False if an error occurred
            raise BadRequest("Errore durante la creazione dell'account.")

        flash('Account creato con successo. Puoi procedere al login.', 'success')
        return redirect(url_for('get_login'))

    except HTTPException as e:
        flash(str(e), 'danger')
        return redirect(url_for('get_signup'))

@app.route('/login')
def get_login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def post_login():
    try:
        form_user = request.form.to_dict()
        validate_login(user = form_user)   # Raises an exception if the form is invalid
        
        db_user = user_db.get_user(username = form_user['username'])

        if not db_user or not check_password_hash(db_user['password'], form_user['password']):
            raise Unauthorized("Username o password non corretti")

        user = User(username=db_user['username'], email=db_user['email'], landlord=db_user['landlord'], name=db_user['name'], password=db_user['password'])
        login_user(user, True)

        flash('Login completato con successo', 'success')
        return redirect(url_for('get_home'))

    except HTTPException as e:
        flash(str(e), 'danger')
        return redirect(url_for('get_login'))

@app.route('/personal')
@login_required
def get_personal():
    try:
        user_visits = visits.get_user_visits(username=current_user.username)

        landlord_ads = []
        landlord_visits = []
        if current_user.landlord:
            landlord_ads = ads.get_landlord_ads(username=current_user.username)
            landlord_visits = visits.get_landlord_visits(username=current_user.username)

        return render_template('personal.html', user_visits=user_visits, landlord_ads=landlord_ads, landlord_visits=landlord_visits)
    except Exception as e:
        print('ERROR', str(e))
        flash('Errore interno durante il caricamento della pagina personale, riprova più tardi', 'danger')
        return redirect(url_for('get_home'))

@app.route('/acceptVisit', methods=['POST'])
@login_required
def post_accept_visit():
    try:
        req = request.form.to_dict()

        # Check if form is valid
        if not re.match(r'^\d{2}\/\d{2}\/\d{4}$', req['date']):
            raise BadRequest("Errore di formattazione nel campo 'date'")
        if not re.match(r'^\d{1,2}-\d{2}$', req['time']):
            raise BadRequest("Errore di formattazione nel campo 'time'")
        if not re.match(r'^\d+$', req['advertisement']):
            raise BadRequest("Errore di formattazione nel campo 'advertisement'")
        if not re.match(r'^\w{1,30}$', req['visitor']):
            raise BadRequest("Errore di formattazione nel campo 'visitor'")

        # Run query, raise on errors
        if not visits.accept_visit(landlord_username=current_user.username, advertisement_id=req['advertisement'], date=req['date'], time=req['time'], visitor_username=req['visitor']):
            raise InternalServerError("Errore durante l'accettazione della visita")

        flash('Visita accettata con successo', 'success')
        return redirect(url_for('get_personal'))
    except HTTPException as e:
        flash(str(e), 'danger')
        return redirect(url_for('get_personal'))
    except Exception as e:
        print('ERROR', str(e))
        flash('Errore interno durante il caricamento della pagina', 'danger')
        
        return redirect(url_for('get_personal'))    

@app.route('/rejectVisit', methods=['POST'])
@login_required
def post_reject_visit():
    try:
        req = request.form.to_dict()

        # Check if form is valid
        if not re.match(r'^\d{2}\/\d{2}\/\d{4}$', req['date']):
            raise BadRequest("Errore di formattazione nel campo 'date'")
        if not re.match(r'^\d{1,2}-\d{2}$', req['time']):
            raise BadRequest("Errore di formattazione nel campo 'time'")
        if not re.match(r'^\d+$', req['advertisement']):
            raise BadRequest("Errore di formattazione nel campo 'advertisement'")
        if not re.match(r'^\w{1,30}$', req['visitor']):
            raise BadRequest("Errore di formattazione nel campo 'visitor'")
        if not re.match(r'.+', req['reason']):
            raise BadRequest("Errore di formattazione nel campo 'reason'")

        # Run query, raise on errors
        if not visits.reject_visit(landlord_username=current_user.username, advertisement_id=req['advertisement'], date=req['date'], reject_reason=req['reason'], time=req['time'], visitor_username=req['visitor']):
            raise InternalServerError("Errore durante il rifiuto della visita")

        flash('Visita rifiutata con successo', 'success')
        return redirect(url_for('get_personal'))
    except HTTPException as e:
        flash(str(e), 'danger')
        return redirect(url_for('get_personal'))
    except Exception as e:
        print('ERROR', str(e))
        flash('Errore interno durante il caricamento della pagina', 'danger')
        
        return redirect(url_for('get_personal'))        

@app.route('/logout', methods=['POST'])
@login_required
def post_logout():
    logout_user()
    return redirect(url_for('get_home'))

# VALIDATION FUNCTIONS

def validate_signup(user):
    """
    Validates a sign up form, as received by the /signup route

    :param user: the form to be validated
    :raise BadRequest: exception raised when the form isn't valid    
    """ 
    username_regex = r'^\w{1,30}$'
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    name_regex = r'^[a-zA-Z\sÀ-ž\']{1,30}$'
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,30}$'
    client_types = ["client", "landlord"]

    if not re.match(username_regex, user['username']):
        raise BadRequest("Username non valido")
    if not re.match(email_regex, user['email']):
        raise BadRequest("Email non valida")
    if not re.match(name_regex, user['name']):
        raise BadRequest("Nome non valido")
    if not re.match(password_regex, user['password']):
        raise BadRequest("Password non valida")
    if user['client_type'] not in client_types:
        raise BadRequest("Tipologia di cliente non valida")

def validate_login(user):
    """
    Validates a sign up form, as received by the /login route

    :param user: the form to be validated
    :raise BadRequest: exception raised when the form isn't valid    
    """ 
    username_regex = r'^\w{1,30}$'
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,30}$'

    if not re.match(username_regex, user['username']):
        raise BadRequest("Username non valido")
    if not re.match(password_regex, user['password']):
        raise BadRequest("Password non valida")
