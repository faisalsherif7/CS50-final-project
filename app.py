from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def index():
    return render_template("home.html")

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/guide')
def guide():
    return render_template('guide.html')

@app.route('/fatwa')
def fatwa():
    return render_template('fatwa.html')