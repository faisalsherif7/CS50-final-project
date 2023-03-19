from flask import Flask, render_template, request, redirect, flash, jsonify
from flask import session as flasksession
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from datetime import datetime

# imports for sqlalchemy
from database import db_session as session
from models import User, Income, Expenses

# imports from util
from utils import login_required, usd, plus_one_hijri

# create the app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Jinja usd filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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

            # Redirect user to home page
            return redirect("/")
        else:
            return redirect("/login")

@app.route('/')
@app.route('/home')
def index():
    if flasksession.get("user_id"):
        userid = flasksession.get("user_id")
        user = session.query(User).filter_by(id=userid).first()
        username = user.username if user else None
        return render_template("home.html", u = username)
    else:
        return render_template("home.html", u = 'random user')

@app.route('/logout')
@login_required
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
            return redirect("/login")
        else:
            return redirect("/register")

@app.route('/guide')
def guide():
    return render_template('guide.html')

@app.route('/dashboard')
@login_required
def dashboard():
    userid = flasksession.get("user_id")
    incomes = session.query(Income).filter_by(user_id=userid)
    if incomes.count() == 0:
        return render_template('dashboard.html', incomes=None, datetime=datetime)
    return render_template('dashboard.html', incomes=incomes, datetime=datetime)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/addmoney', methods=["GET", "POST"])
@login_required
def addmoney():
    if request.method == "POST":
        action = request.form.get('action')
        userid = flasksession.get("user_id")
        date_input = request.form.get('date')
        try:
            date = datetime.strptime(date_input, '%Y-%m-%d')
        except ValueError:
            flash("A valid date must be entered. Do not attempt to modify HTML file.")
            return redirect('/dashboard')
        if action == 'income':
            amount = request.form.get('income')
            if not amount:
                flash("Please enter amount!")
                return redirect('/dashboard')
            income = Income(amount=amount, user_id=userid, due_amount= (2.5/100 * int(amount)), date=date, due_date=plus_one_hijri(date))
            session.add(income)
            session.commit()
            flash("Income added")
            return redirect('/dashboard')
        elif action == 'expense':
            amount_str = request.form.get('expense')
            if not amount_str:
                flash("Please enter amount!")
                return redirect('/dashboard')
            amount = int(amount_str)
            expense = Expenses(amount=amount, user_id=userid, date=date)
            session.add(expense)
            session.commit()
            incomes = session.query(Income).filter_by(user_id=userid, paid=False).filter(Income.date <= date).order_by(Income.date.desc()).all()
            for income in incomes:
                if income.amount > amount:
                    income.amount = income.amount - amount
                    session.commit()
                    break
                elif income.amount == amount:
                    session.delete(income)
                    session.commit()
                    break
                elif income.amount < amount: 
                    session.delete(income)
                    amount = amount - income.amount
                    session.commit()
            flash("Expense added")
            return redirect('/dashboard')
    else:
        return redirect('/')
    
@app.route('/history')
def history():
    incomes = session.query(Income).all()
    expenses = session.query(Expenses).all()
    return render_template('history.html', incomes=incomes, expenses=expenses)

@app.route('/due')
@login_required
def due():
    current_date = datetime.now()
    incomes_due = session.query(Income).filter(Income.due_date <= current_date).filter_by(paid=False)
    if incomes_due.count() == 0:
        return render_template('due.html', incomes=None)
    return render_template('due.html', incomes=incomes_due)

@app.route('/delete_entry', methods = ["POST"])
@login_required
def delete_entry():

    # Functionality to completely delete an income entry from history
    income_id = request.form.get('income_id')
    if not income_id:
        flash('fail')
        return redirect('/dashboard')
    entry = session.query(Income).get(income_id)
    session.delete(entry)
    session.commit()
    flash('entry deleted!')
    return redirect('/dashboard')

@app.route('/paid', methods = ["POST"])
@login_required
def paid():
    userid = flasksession.get('user_id')
    income_id = request.form.get('income_id')
    if not income_id:
        flash('fail')
        return redirect('/dashboard')
    entry = session.query(Income).get(income_id)
    entry.paid = True
    next_amount = entry.amount - entry.due_amount
    new_entry_date = entry.due_date
    next_entry = Income(amount=next_amount, user_id=userid, 
                        date=new_entry_date, due_date=plus_one_hijri(new_entry_date), 
                        due_amount= (2.5/100 * int(next_amount)))
    session.add(next_entry)
    session.commit()
    flash('Amount paid; remaining amount being tracked for next hijri year!')
    return redirect('/dashboard')

@app.route('/delete_account', methods = ["POST"])
@login_required
def delete_account():
    userid = flasksession.get("user_id")
    username = request.form.get("username")
    password = request.form.get("password")

    # Ensure username and password are submitted
    if not username or not password:
        flash("must provide username/password")
        return redirect('/settings')

    # Ensure correct username was submitted (sqlalchemy)
    user = session.query(User).get(userid)
    if username != user.username:
        flash("Invalid username!")
        return redirect('/settings')

    # Ensure username exists and password is correct
    if not user or not check_password_hash(user.hash, password):
        flash("invalid username and/or password")
        return redirect('/settings')

    # Delete account and all data
    flasksession.clear()
    session.delete(user)
    incomes = session.query(Income).filter_by(user_id=userid).all()
    for income in incomes:
        session.delete(income)
    expenses = session.query(Expenses).filter_by(user_id=userid).all()
    for expense in expenses:
        session.delete(expense)
    session.commit()
    flash("Your account has been deleted.")
    return redirect("/")

@app.route('/change_password', methods = ["POST"])
@login_required
def change_password():
    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")
    confirmation = request.form.get("confirmation")
    userid = flasksession.get("user_id")
    user = session.query(User).get(userid)

    # Ensure all fields are filled
    if not old_password or not new_password or not confirmation:
        flash('All fields are required!')
        return redirect('/settings')
    
    # Ensure correct password is entered
    if not check_password_hash(user.hash, old_password):
        flash('Invalid password entered!')
        return redirect('/settings')
    
    # Ensure passwords match
    if new_password != confirmation:
        flash('Passwords do not match!')
        return redirect('/settings')
    
    # Change password
    user.hash = generate_password_hash(new_password)
    session.commit()
    flash('Password changed successfully!')
    return redirect('/settings')
    

# SQLAlchemy - Flask removes database sessions at end of request
@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()