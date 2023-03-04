from flask import Flask, render_template, request, redirect, flash
from cs50 import SQL
import hijri_converter

# create the app
app = Flask(__name__)

# point to database
db = SQL("sqlite:///project.db")

@app.route('/')
@app.route('/home')
def index():
    return render_template("home.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template('login.html')
    

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template('register.html')
    else:
        tracker = 0
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not username or not password or not confirmation:
            flash("all fields are requied!")
            tracker = 1
        if len(password) < 8:
            flash("Password must contain a minimum of 8 characters!")
            tracker = 1
        if str.isalpha(password):
            flash("Password must contain at least 1 number or special character!")
            tracker = 1
        if password != confirmation:
            flash("Passwords do not match!")
            tracker = 1
        hashed = generate_password_hash(password)
        existing = db.execute("SELECT username FROM users")
        for each in existing:
            if username == each["username"]:
                return apology("Username already exists!")
        if tracker == 0:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashed)
            return redirect("/")
        else:
            return redirect("/register")

@app.route('/guide')
def guide():
    return render_template('guide.html')

@app.route('/fatwa')
def fatwa():
    return render_template('fatwa.html')