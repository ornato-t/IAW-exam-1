from flask import Flask, render_template
import ads

app = Flask(__name__)

@app.route('/')
def home():
    advertisements = ads.get_public_ads(sort_price=True)    # TODO: set sort_price via http parameter
    return render_template('home.html', advertisements=advertisements)

@app.route('/advertisement/<int:id>')
def advertisement(id):
    return f'Advertisement with id {id}'

@app.route('/about')
def about():
    return render_template('about.html')

