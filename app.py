from flask import Flask, render_template
import ads

app = Flask(__name__)

@app.route('/')
def home():
    advertisements = ads.get_public_ads()
    return render_template('home.html', advertisements=advertisements)

