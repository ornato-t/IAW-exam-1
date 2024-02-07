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

@app.route('/')
def get_home():
    try:
        sort_price_str = request.args.get('sort_price', default='true', type=str)
        sort_price = sort_price_str.lower() == 'true'

        advertisements = ads.get_public_ads(sort_price)

        return render_template('home.html', advertisements=advertisements, sort_price=sort_price)
    except Exception as e:
        flash(str(e), 'danger')

        return redirect(url_for('get_home'))

@app.route('/advertisement/<int:id>')
def get_advertisement(id):
    try:
        advertisement = ads.get_ad_by_id(id=id)
        if advertisement == None:
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
        flash(str(e), 'danger')
        return redirect(url_for('get_home'))

@app.route('/advertisement/<int:id>/visit')
@login_required 
def get_visit(id):
    try:
        advertisement = ads.get_ad_by_id(id=id)
        if advertisement == None:
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
        flash(str(e), 'danger')
        return redirect(url_for('get_home'))

@app.route('/advertisement/<int:id>/visit', methods=['POST'])
@login_required 
def post_visit(id):
    try:
        # Check if url is correct and user permissions
        advertisement = ads.get_ad_by_id(id=id)
        if advertisement == None:
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
        flash(str(e), 'danger')
        return redirect(url_for('get_home'))

@login_required 
@app.route('/advertisement/<int:id>/edit')
def get_edit_advertisement(id):
    # TODO
    try:
        advertisement = ads.get_ad_by_id(id=id)
        if advertisement == None:
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
        flash(str(e), 'danger')
        return redirect(url_for('get_home'))

@login_required 
@app.route('/advertisement/new')
def get_new_advertisement():
    try:
        # TODO
        raise InternalServerError("Not implemented")
    except HTTPException as e:
        flash(str(e), 'warning')
        return redirect(url_for('get_personal'))
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('get_personal'))

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
        # TODO
        raise InternalServerError("Not implemented")
    except HTTPException as e:
        flash(str(e), 'warning')
        return redirect(url_for('get_personal'))
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('get_personal'))

@app.route('/rejectVisit', methods=['POST'])
@login_required
def post_reject_visit():
    try:
        # TODO
        raise InternalServerError("Not implemented")
    except HTTPException as e:
        flash(str(e), 'warning')
        return redirect(url_for('get_personal'))
    except Exception as e:
        flash(str(e), 'danger')
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
    username_regex = r'^[a-zA-Z0-9_]{1,30}$'
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    name_regex = r'^[a-zA-Z\s\']{1,30}$'
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,30}$'
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
    username_regex = r'^[a-zA-Z0-9_]{1,30}$'
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,30}$'

    if not re.match(username_regex, user['username']):
        raise BadRequest("Username non valido")
    if not re.match(password_regex, user['password']):
        raise BadRequest("Password non valida")
