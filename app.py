from flask import Flask, render_template, request, redirect, flash
from flask import session as flasksession
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

# imports for sqlalchemy
from database import db_session as session
from models import User, Income, Nisab, Untracked_Income
from sqlalchemy import func

# imports from utils
from utils import login_required, usd, plus_one_hijri, isfloat


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

        # Check for valid entries
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not username:
            flash("Please enter username!")
            tracker = 1 
        elif not password:
            flash("Please enter password!")
            tracker = 1
        elif not confirmation:
            flash("Please confirm password!")
            tracker = 1
        if tracker == 0:
            if password != confirmation:
                flash("Passwords do not match!")
                tracker = 1
        
        # Ensure strong password
        if tracker == 0:
            if len(password) < 8:
                flash("Password must contain a minimum of 10 characters!")
                tracker = 1
        
        # Ensure username is not already in existance. 
        if tracker == 0:
            existing = session.query(User).filter_by(username=username).all()
            if existing:
                flash("Username already exists!")
                tracker = 1
        
        # Create account if all above checks are passed.
        if tracker == 0:
            hashed = generate_password_hash(password)
            newuser = User(username=username, hash=hashed)
            session.add(newuser)
            session.commit()
            flash('Account created successfully. You can log in now.')
            return redirect("/login")
        else:
            return redirect("/register")


@app.route('/')
@app.route('/home')
def index():
    return render_template("home.html")


@app.route('/guide')
def guide():
    return render_template('guide.html')


@app.route('/dashboard')
@login_required
def dashboard():
    userid = flasksession.get("user_id")
    incomes = session.query(Income).filter_by(user_id=userid, paid=False)
    if incomes.count() != 0:
        return render_template('dashboard.html', incomes=incomes, datetime=datetime)
    untracked_incomes = session.query(Untracked_Income).filter_by(user_id=userid)
    if untracked_incomes.count() != 0:
        return render_template('dashboard.html', untracked_incomes=untracked_incomes, datetime=datetime)
    return render_template('dashboard.html', datetime=datetime)


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@app.route('/addmoney', methods=["POST"])
@login_required
def addmoney():
    action = request.form.get('action')
    userid = flasksession.get("user_id")
    date_input = request.form.get('date')
    try:
        date = datetime.strptime(date_input, '%Y-%m-%d')
    except ValueError:
        flash("A valid date must be entered. Do not attempt to modify HTML file.")
        return redirect('/dashboard')
    

    # Check for valid amount entry
    amount = request.form.get('income')
    if not amount:
        flash("Please enter amount!")
        return redirect('/dashboard')
    if not isfloat(amount):
        flash('Please enter valid amount!')
        return redirect('/dashboard')
    if float(amount) <= 0:
        flash('Please enter valid amount!')
        return redirect('/dashboard')
    
    # First, obtain nisab value. If no nisab value is found, then prompt user to add a nisab value first.
    nisab = session.query(Nisab).filter_by(user_id=userid).first()
    if nisab == None:
        flash("Please set a nisab value before adding an income")
        return redirect('/dashboard')
    
    # Check if nisab has been reached by current savings.
    check = nisab.nisab_reached

    # If nisab reached, this means the income table is to be added to.
    if check == True:
        income = Income(amount=amount, user_id=userid, due_amount= (2.5/100 * int(amount)), date=date, due_date=plus_one_hijri(date))
        session.add(income)
        session.commit()
        flash("Income added. Your savings cross the nisab threshold and are being tracked for zakat.")
        return redirect('/dashboard')

    # If nisab not reached, get amount from untracked income table, check for nisab threshold, and add to corresponding table.
    else:
        total_before = session.query(func.sum(Untracked_Income.amount)).filter_by(user_id=userid).scalar()
        if total_before == None:
            total_now = int(amount)
        else:
            total_now = int(total_before) + int(amount)

        # If nisab threshold not reached even after new entry.
        if total_now < nisab.amount:
            income = Untracked_Income(amount=amount, user_id=userid, date=date)
            session.add(income)
            session.commit()
            flash("Income added. You have not crossed the nisab threshold yet, so the amount is not being tracked for zakat.")
            return redirect('/dashboard')
        
        # If nisab threshold reached on new income entry.
        elif total_now >= nisab.amount:
            income = Income(amount=total_now, user_id=userid, due_amount= (2.5/100 * int(total_now)), date=date, due_date=plus_one_hijri(date))
            session.add(income)
            delete_untracked = session.query(Untracked_Income).filter_by(user_id=userid).all()
            for entry in delete_untracked:
                session.delete(entry)
            nisab.nisab_reached = True
            session.commit()
            flash("Income added. You have crossed the nisab threshold. Your zakat year begins now.")
            return redirect('/dashboard')


@app.route('/nisab', methods = ["GET", "POST"])
@login_required
def nisab():
    userid = flasksession.get("user_id")
    nisab = session.query(Nisab).filter_by(user_id=userid).first()
    if request.method == "GET":
        if nisab == None:
            return render_template('nisab.html', nisab=0)
        return render_template('nisab.html', nisab=nisab.amount)
    
    # If user entered a nisab amount.
    if request.method == "POST":

        # Ensure valid nisab entry
        nisab_new_string = request.form.get("nisab")
        if not isfloat(nisab_new_string):
            flash('Please enter valid nisab amount!')
            return redirect('/nisab')
        nisab_new = float(nisab_new_string)
        if nisab_new <= 0:
            flash('Please enter valid nisab amount')
            return redirect('/nisab')

        # If nisab wasn't set before.
        if not nisab:
            enter_nisab = Nisab(amount=nisab_new, user_id=userid)
            session.add(enter_nisab)
            session.commit()
            flash('Nisab set successfully.')

        # If nisab is being changed.
        else:

            # If savings were above nisab threshold previously, then we work on the Income table.
            if nisab.nisab_reached == True:
                total_before = session.query(func.sum(Income.amount)).filter_by(user_id=userid, paid=False).scalar()

                # If no savings, simply update nisab and return function.
                if total_before == None:
                    nisab.amount = nisab_new
                    nisab.nisab_reached = False
                    session.commit()
                    flash('Nisab updated.')
                    return redirect('/nisab')

                # If savings are still above updated nisab, do nothing.
                if total_before >= nisab_new:
                    flash('Nisab updated. Your savings still cross the nisab threshold and are tracked for zakat.')
                
                # If savings dip below updated nisab, change previous savings sum to untracked_income table and stop tracking.
                elif total_before < nisab_new:
                    stop_tracking = Untracked_Income(amount=total_before, user_id=userid)
                    session.add(stop_tracking)
                    incomes = session.query(Income).filter_by(user_id=userid, paid=False).all()
                    for income in incomes:
                        session.delete(income)
                    nisab.nisab_reached = False
                    flash('Nisab updated. Your savings have dipped below the updated nisab amount and are now not tracked for zakat.')
                    flash('Your savings will begin being tracked if they cross the nisab threshold in the future.')
            
            # If savings were below the previous nisab threshold, then we work on the Untracked Income table.
            elif nisab.nisab_reached == False:
                total_before = session.query(func.sum(Untracked_Income.amount)).filter_by(user_id=userid).scalar()

                # If no savings, simply update nisab and return function.
                if total_before == None:
                    nisab.amount = nisab_new
                    nisab.nisab_reached = False
                    session.commit()
                    flash('Nisab updated.')
                    return redirect('/nisab')

                # If savings are still below updated nisab, do nothing.
                if total_before < nisab_new:
                    flash('Nisab updated. Your savings are still below the nisab threshold and are not tracked for zakat.')

                # If savings cross updated nisab threshold, change savings to income table and start tracking.
                elif total_before >= nisab_new:
                    date_now = datetime.now().strftime('%Y-%m-%d')
                    date = datetime.strptime(date_now, '%Y-%m-%d')
                    start_tracking = Income(amount=total_before, user_id=userid, due_amount= (2.5/100 * int(total_before)), date=date, due_date=plus_one_hijri(date))
                    session.add(start_tracking)
                    incomes = session.query(Untracked_Income).filter_by(user_id=userid).all()
                    for income in incomes:
                        session.delete(income)
                    nisab.nisab_reached = True
                    flash('Nisab updated. Your savings now cross the updated nisab threshold and are now tracked for zakat.')
                
            # Update nisab. 
            nisab.amount = nisab_new
            session.commit()
        return redirect('/nisab')
    

@app.route('/paid', methods = ["POST"])
@login_required
def paid():
    userid = flasksession.get('user_id')
    income_id = request.form.get('income_id')

    # Update income entry as paid
    entry = session.query(Income).get(income_id)
    entry.paid = True

    # Add remaining amount to savings
    next_amount = entry.amount - entry.due_amount
    new_entry_date = entry.due_date
    next_entry = Income(amount=next_amount, user_id=userid, 
                        date=new_entry_date, due_date=plus_one_hijri(new_entry_date), 
                        due_amount= (2.5/100 * int(next_amount)))
    session.add(next_entry)
    session.commit()

    # If remaining savings are above nisab, do nothing.
    nisab = session.query(Nisab).filter_by(user_id=userid).first()
    remaining_savings = session.query(func.sum(Income.amount)).filter_by(user_id=userid, paid=False).scalar()
    if remaining_savings >= nisab.amount:
        flash('Zakat paid; your remaining savings cross the nisab threshold, and so are being tracked for next hijri year.')
        return redirect('/dashboard')
    
    # If remaining savings dip below nisab, change tables and stop tracking.
    elif remaining_savings < nisab.amount:
        stop_tracking = Untracked_Income(amount=remaining_savings, user_id=userid)
        session.add(stop_tracking)
        incomes = session.query(Income).filter_by(user_id=userid, paid=False).all()
        for income in incomes:
            session.delete(income)
        nisab.nisab_reached = False
        session.commit()
        flash('Zakat paid; your remaining savings are below the nisab, and are therefore not being tracked.')
        return redirect('/due')
    

@app.route('/delete_entry', methods = ["POST"])
@login_required
def delete_entry():
    userid = flasksession.get("user_id")
    action = request.form.get("action")

    # If user deletes from untracked table
    if action == 'untracked':
        income_id = request.form.get('income_id')
        entry = session.query(Untracked_Income).get(income_id)
        session.delete(entry)
        session.commit()
        flash('Entry deleted.')
        return redirect('/dashboard')

    # Functionality to completely delete an income entry from history
    income_id = request.form.get('income_id')
    entry = session.query(Income).get(int(income_id))
    session.delete(entry)
    session.commit()

    # Check if remaining amount is above/below nisab
    nisab = session.query(Nisab).filter_by(user_id=userid).first()
    remaining_savings = session.query(func.sum(Income.amount)).filter_by(user_id=userid, paid=False).scalar()

    # If no remaining savings, say so.
    if remaining_savings == None:
        flash('Entry deleted. You have no remaining savings.')
        nisab.nisab_reached = False
        session.commit()
        return redirect('/dashboard')
    
    # If still above nisab, do nothing
    if remaining_savings >= nisab.amount:
        flash('Entry deleted. Your remaining savings still cross the nisab threshold and zakat is still due.')
        return redirect('/dashboard')
    
    # If remaining savings dip below nisab, change tables and stop tracking.
    elif remaining_savings < nisab.amount:
        stop_tracking = Untracked_Income(amount=remaining_savings, user_id=userid)
        session.add(stop_tracking)
        incomes = session.query(Income).filter_by(user_id=userid, paid=False).all()
        for income in incomes:
            session.delete(income)
        nisab.nisab_reached = False
        session.commit()
        flash('Entry deleted. Your remaining savings are below the nisab, and are therefore not being tracked.')
        return redirect('/dashboard')
    

@app.route('/history')
@login_required
def history():
    userid = flasksession.get('user_id')
    incomes = session.query(Income).filter_by(user_id=userid).all()
    paid = session.query(Income).filter_by(user_id=userid, paid=True).all()
    return render_template('history.html', incomes=incomes, paid=paid)


@app.route('/due')
@login_required
def due():

    # Display zakat due, if any, as of now
    current_date = datetime.now()
    incomes_due = session.query(Income).filter(Income.due_date <= current_date).filter_by(paid=False)
    if incomes_due.count() == 0:
        return render_template('due.html', incomes=None)
    return render_template('due.html', incomes=incomes_due)
    

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

    # Ensure correct username was submitted 
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
    untracked_incomes = session.query(Untracked_Income).filter_by(user_id=userid).all()
    for income in untracked_incomes:
        session.delete(income)
    nisab = session.query(Nisab).filter_by(user_id=userid).first()
    if nisab != None:
        session.delete(nisab)
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