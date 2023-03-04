from flask import Flask, render_template, request, redirect, flash, session
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
import hijri_converter

# create the app
app = Flask(__name__)

# point to database
db = SQL("sqlite:///project.db")

app.secret_key = 'your_secret_key_here'

@app.route('/')
@app.route('/home')
def index():
    return render_template("home.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    tracker = 0

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("must provide username")
            tracker = 1

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("must provide password")
            tracker = 1

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("invalid username and/or password")
            tracker = 1

        if tracker == 0:

            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]

            # Redirect user to home page
            return redirect("/")
        else:
            return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

    

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template('register.html')
    elif request.method == "POST":
        tracker = 0
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not username or not password or not confirmation:
            flash("All fields are required!")
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
                flash("Username already exists!")
                tracker = 1
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