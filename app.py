from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def index():
    return render_template("layout.html")

@app.route('/login')
def login():
    return render_template('login.html')