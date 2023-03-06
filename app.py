from flask import Flask, render_template, request, redirect, flash, session, jsonify
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
import hijri_converter

# create the app
app = Flask(__name__)

# point to database
db = SQL("sqlite:///project.db")

# Enter secret key for app to encrypt session data 
app.secret_key = 'your_secret_key_here'

@app.route('/')
@app.route('/home')
def index():
    if session.get("user_id"):
        userid = session.get("user_id")
        usernamelist = db.execute("SELECT username FROM users WHERE id IS ?", userid)
        usernamedict = usernamelist[0]
        username = usernamedict['username']
        return render_template("home.html", u = username)
    else:
        return render_template("home.html", u = 'random user')

@app.route('/logout')
def logout():

    # Forget any user_id
    session.clear()
    return redirect('/')

@app.route('/login', methods=["GET", "POST"])
def login():

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("login.html")

    # User reached route via POST (as by submitting a form via POST)
    elif request.method == "POST":
        
        tracker = 0

        # get username and password
        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure all field were submitted
        if not username or not password:
            flash("All fields are required!")
            tracker = 1

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            if tracker != 1:
                flash("Invalid username and/or password")
            tracker = 2

        if tracker == 0:

            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]

            # Redirect user to home page
            return redirect("/")
        else:
            return redirect("/login")

    

    

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template('register.html')
    elif request.method == "POST":
        tracker = 0
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not username:
            flash("Please enter username!")
            tracker = 1 
        elif not password:
            flash("Please enter password!")
            tracker = 2
        elif not confirmation:
            flash("Please confirm password!")
            tracker = 2
        if len(password) < 8:
            if tracker == 2:
                flash("Password must contain a minimum of 8 characters!")
                tracker = 1
        if str.isalpha(password):
            if tracker == 2:
                flash("Password must contain at least 1 number or special character!")
                tracker = 1
        if tracker == 4:
            if password != confirmation:
                flash("Passwords do not match!")
                tracker = 5
        existing = db.execute("SELECT username FROM users")
        for each in existing:
            if username == each["username"]:
                flash("Username already exists!")
                tracker = 6 
        if tracker == 0:
            hashed = generate_password_hash(password)
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

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/addmoney', methods=["GET", "POST"])
def addmoney():
    if request.method == "POST":
        return redirect('/')
    else:
        return redirect('/')
    
@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/tracked')
def tracked():
    return render_template('tracked.html')