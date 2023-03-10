from flask import Flask, render_template, request, redirect, flash, jsonify
from flask import session as flasksession
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import hijri_converter

# imports for sqlalchemy
from database import db_session as session
from models import User, Income, Expenses

# create the app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Initialize global variable so that it can be updated when logging in
userid = None

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
        rows = session.query(User).filter_by(username=username).first()

        # Ensure username exists and password is correct
        if not rows or not check_password_hash(rows.hash, request.form.get("password")):
            if tracker != 1:
                flash("Invalid username and/or password")
            tracker = 2

        if tracker == 0:

            # Remember which user has logged in
            flasksession["user_id"] = rows.id
            userid = rows.id

            # Redirect user to home page
            return redirect("/")
        else:
            return redirect("/login")

@app.route('/')
@app.route('/home')
def index():
    if flasksession.get("user_id"):
        user = session.query(User).filter_by(id=userid).first()
        username = user.username if user else None
        return render_template("home.html", u = username)
    else:
        return render_template("home.html", u = 'random user')

@app.route('/logout')
def logout():

    # Forget any user_id
    flasksession.clear()
    return redirect('/')

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
        existing = session.query(User).filter_by(username=username).all()
        if existing:
            flash("Username already exists!")
            tracker = 6 
        if tracker == 0:
            hashed = generate_password_hash(password)
            newuser = User(username=username, hash=hashed)
            session.add(newuser)
            session.commit()
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
        action = request.form.get('action')
        if action == 'income':
            amount = request.form.get('income')
            income = Income(amount=amount, user_id=userid)
            session.add(income)
            session.commit()
            flash("income added successfully!")
            return redirect('/')
        elif action == 'expense':
            amount = request.form.get('expense')
            expense = Expenses(amount=amount, user_id=userid)
            session.add(expense)
            session.commit()
            flash("expense added successfully!")
            return redirect('/')
    else:
        return redirect('/')
    
@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/tracked')
def tracked():
    return render_template('tracked.html')


# SQLAlchemy - Flask removes database sessions at end of request
@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()