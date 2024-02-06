import uuid
import re
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.exceptions import HTTPException, BadRequest, Unauthorized, NotFound
from werkzeug.security import generate_password_hash, check_password_hash

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
    advertisements = ads.get_public_ads(sort_price=True)    # TODO: set sort_price via http parameter; add try..except
    return render_template('home.html', advertisements=advertisements)

@app.route('/advertisement/<int:id>')
def get_advertisement(id):
    try:
        advertisement = ads.get_ad_by_id(id=id)
        if advertisement == None:
            raise NotFound('Nessun annuncio corrispondente trovato')

        if not advertisement['available'] and (not current_user.is_authenticated or advertisement['landlord_username'] != current_user.username):
            raise NotFound('Nessun annuncio corrispondente trovato')    # Using 404 rather than 401 for security reasons: avoid leaking info on hidden houses

        return render_template('advertisement.html', ad=advertisement)
    except HTTPException as e:
        flash(str(e))

        return redirect(url_for('get_home'))

@app.route('/advertisement/<int:id>/visit')
# @login_required TODO
def get_visit(id):
    try:
        advertisement = ads.get_ad_by_id(id=id)
        if advertisement == None:
            raise NotFound('Nessun annuncio corrispondente trovato')
        # TODO: fetch existing visits; if user has already visited or is awaiting confirmation redirect to home
        # TODO: if current_user.username == landlord.username redirect to personal

        visit_list = visits.get_visits_next_week(current_user=current_user)

        return render_template('visit.html', ad=advertisement, visit=visit_list)
    except HTTPException as e:
        flash(str(e))

        return redirect(url_for('get_home'))

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

        flash('Account creato con successo. Puoi procedere al login.')
        return redirect(url_for('get_login'))

    except HTTPException as e:
        flash(str(e))

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

        flash('Login completato con successo')
        return redirect(url_for('get_personal'))

    except HTTPException as e:
        flash(str(e))

        return redirect(url_for('get_login'))

@app.route('/personal')
@login_required
def get_personal():
    return render_template('personal.html')

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
        raise BadRequest("Invalid username")
    if not re.match(email_regex, user['email']):
        raise BadRequest("Invalid email")
    if not re.match(name_regex, user['name']):
        raise BadRequest("Invalid name")
    if not re.match(password_regex, user['password']):
        raise BadRequest("Invalid password")
    if user['client_type'] not in client_types:
        raise BadRequest("Invalid client type")

def validate_login(user):
    """
    Validates a sign up form, as received by the /login route

    :param user: the form to be validated
    :raise BadRequest: exception raised when the form isn't valid    
    """ 
    username_regex = r'^[a-zA-Z0-9_]{1,30}$'
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,30}$'

    if not re.match(username_regex, user['username']):
        raise BadRequest("Invalid username")
    if not re.match(password_regex, user['password']):
        raise BadRequest("Invalid password")
