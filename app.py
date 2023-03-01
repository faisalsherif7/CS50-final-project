from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def index():
    return render_template("starter.html")

@app.route('/market')
def market():
    return render_template('market.html')