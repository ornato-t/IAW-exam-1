import uuid
import re
from flask import Flask, render_template, redirect, url_for, request, flash
from werkzeug.exceptions import HTTPException, BadRequest
from werkzeug.security import generate_password_hash, check_password_hash

import ads
import user_db
from models import User

app = Flask(__name__)
app.config["SECRET_KEY"] = uuid.uuid4().hex

@app.route('/')
def get_home():
    advertisements = ads.get_public_ads(sort_price=True)    # TODO: set sort_price via http parameter; add try..except
    return render_template('home.html', advertisements=advertisements)

@app.route('/advertisement/<int:id>')
def get_advertisement(id):
    return f'Advertisement with id {id}'

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
