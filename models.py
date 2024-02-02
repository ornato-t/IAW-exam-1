from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, username, email, password, name, landlord):
        self.username = username
        self.email = email
        self.password = password
        self.name = name
        self.landlord = landlord
