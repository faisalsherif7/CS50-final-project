from flask import Flask, render_template, request, redirect, flash, jsonify, session as flasksession
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
            flash("All fields are required!", "danger")
            tracker = 1

        # Query database for username
        rows = session.query(User).filter_by(username=username).first()

        # Ensure username exists and password is correct
        if tracker != 1:
            if not rows:
                flash("Username does not exist!", "danger")
                tracker = 1
        if tracker != 1:
            if not check_password_hash(rows.hash, request.form.get("password")):
                flash("Invalid username and/or password", "danger")
                tracker = 1

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
        if not username or not password or not confirmation:
            flash("All fields are required!", "danger")
            tracker = 1 
        if tracker == 0:
            if password != confirmation:
                flash("Passwords do not match!", "danger")
                tracker = 1
        
        # Ensure strong password
        if tracker == 0:
            if len(password) < 10:
                flash("Password must contain a minimum of 10 characters!", "danger")
                tracker = 1
        
        # Ensure username is not already in existance. 
        if tracker == 0:
            existing = session.query(User).filter_by(username=username).all()
            if existing:
                flash("Username already exists!", "danger")
                tracker = 1
        
        # Create account if all above checks are passed.
        if tracker == 0:
            hashed = generate_password_hash(password)
            newuser = User(username=username, hash=hashed)
            session.add(newuser)
            session.commit()
            flash('Account created successfully. You can log in now.', "success")
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
    incomes = session.query(Income).filter_by(user_id=userid, paid=False).all()
    untracked_incomes = session.query(Untracked_Income).filter_by(user_id=userid).all()
    if incomes:
        return render_template('dashboard.html', incomes=incomes, datetime=datetime)
    elif untracked_incomes:
        return render_template('dashboard.html', untracked_incomes=untracked_incomes, datetime=datetime)
    else:
        return render_template('dashboard.html', datetime=datetime)


@app.route('/settings')
@login_required
def settings():
    user = session.query(User).get(flasksession.get('user_id'))
    return render_template('settings.html', username=user.username)


@app.route('/addmoney', methods=["POST"])
@login_required
def addmoney():
    userid = flasksession.get("user_id")
    date_input = request.form.get('date')
    try:
        date = datetime.strptime(date_input, '%Y-%m-%d')
    except ValueError:
        flash("Please enter valid date!", "danger")
        return redirect('/dashboard')

    # Check for valid amount entry
    amount = request.form.get('income')
    if not amount:
        flash("Please enter amount!", "danger")
        return redirect('/dashboard')
    if not isfloat(amount) or float(amount) <= 0:
        flash('Please enter valid amount!', "danger")
        return redirect('/dashboard')
    
    # First, obtain nisab value. If no nisab value is found, then prompt user to add a nisab value first.
    nisab = session.query(Nisab).filter_by(user_id=userid).first()
    if nisab == None:
        flash("Please set a nisab value before adding an income", "danger")
        return redirect('/dashboard')
    
    # Check if nisab has been reached by current savings.
    check = nisab.nisab_reached

    # If nisab reached, this means the income table is to be added to.
    if check == True:
        income = Income(amount=amount, user_id=userid, due_amount= (2.5/100 * float(amount)), date=date, due_date=plus_one_hijri(date))
        session.add(income)
        session.commit()
        flash("Amount added. Your savings cross the nisab threshold and are being tracked for zakat.", "success")
        return redirect('/dashboard')

    # If nisab not reached, get amount from untracked income table, check for nisab threshold, and add to corresponding table.
    else:
        total_before = session.query(func.sum(Untracked_Income.amount)).filter_by(user_id=userid).scalar()
        if total_before == None:
            total_now = float(amount)
        else:
            total_now = float(total_before) + float(amount)

        # If nisab threshold not reached even after new entry.
        if total_now < nisab.amount:
            income = Untracked_Income(amount=amount, user_id=userid, date=date)
            session.add(income)
            session.commit()
            flash("Amount added. Your total savings are below nisab and they are not being tracked for zakat.", "success")
            return redirect('/dashboard')
        
        # If nisab threshold reached on new income entry.
        elif total_now >= nisab.amount:

            # First, add income to untracked entry table
            latest_entry = Untracked_Income(amount=amount, user_id=userid, date=date)
            session.add(latest_entry)
            nisab.nisab_reached = True
            session.commit()

            # Transfer entries from untracked_income table to income table
            query = session.query(Untracked_Income).filter_by(user_id=userid).order_by(Untracked_Income.date).all()

            # Iterate over the results and note date when the sum reaches the target amount
            total = 0
            nisab_crossing_date = query[0].date # Just intitializing the variable as a date time
            for income in query:
                total += income.amount
                if total >= nisab.amount:
                    nisab_crossing_date = income.date
                    break
            
            # Get remaining entries from the Untracked_Income table
            untracked_incomes = session.query(Untracked_Income).filter_by(user_id=userid).order_by(Untracked_Income.date).all()

            # Loop through each entry and add it to the Income table
            for income in untracked_incomes:
                if income.date < nisab_crossing_date:
                    entry = Income(date=income.date, amount=income.amount, user_id=userid, due_amount= (2.5/100 * float(income.amount)), due_date=plus_one_hijri(nisab_crossing_date))
                elif income.date >= nisab_crossing_date:
                    entry = Income(date=income.date, amount=income.amount, user_id=userid, due_amount= (2.5/100 * float(income.amount)), due_date=plus_one_hijri(income.date))
                session.add(entry)
                session.delete(income)
                session.commit()

            # Return function
            flash("Amount added. Your total savings have crossed the nisab threshold and are now being tracked for zakat.", "success")
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
        if not isfloat(nisab_new_string) or float(nisab_new_string) <= 0:
            flash('Please enter valid nisab amount!', "danger")
            return redirect('/nisab')
        nisab_new = float(nisab_new_string)

        # If nisab wasn't set before.
        if not nisab:
            enter_nisab = Nisab(amount=nisab_new, user_id=userid)
            session.add(enter_nisab)
            session.commit()
            flash('Nisab set successfully.', "success")

        # If previous nisab is being changed.
        else:

            # If savings were above nisab threshold previously, then we work on the Income table.
            if nisab.nisab_reached == True:
                total_before = session.query(func.sum(Income.amount)).filter_by(user_id=userid, paid=False).scalar()

                # If savings are still above updated nisab, update due dates of entries according to updated nisab
                if total_before >= nisab_new:
                    query = session.query(Income).filter_by(user_id=userid, paid=False).order_by(Income.date).all()

                    # Iterate over the results and note date when the sum crosses the nisab amount
                    total = 0
                    nisab_crossing_date = query[0].date
                    for income in query:
                        total += income.amount
                        if total >= nisab_new:
                            nisab_crossing_date = income.date
                            break
                    
                    # Update due dates to account for date of crossing nisab threshold
                    for income in query:
                        if income.date <= nisab_crossing_date:
                            income.due_date = plus_one_hijri(nisab_crossing_date)
                        elif income.date > nisab_crossing_date:
                            income.due_date = plus_one_hijri(income.date)
                    flash('Nisab updated. Your savings still cross the nisab threshold and are tracked for zakat.', 'info')
                
                # If savings dip below updated nisab, change previous savings sum to untracked_income table and stop tracking.
                elif total_before < nisab_new:
                    incomes = session.query(Income).filter_by(user_id=userid, paid=False).order_by(Income.date).all()
                    for income in incomes:
                        stop_tracking = Untracked_Income(amount=income.amount, date=income.date, user_id=userid)
                        session.add(stop_tracking)
                        session.delete(income)
                    nisab.nisab_reached = False
                    flash('Nisab updated. Your savings have dipped below the updated nisab amount and are now not tracked for zakat.', 'success')
                    flash('Your savings will begin being tracked if they cross the nisab threshold in the future.', 'info')
            
            # If savings were below the previous nisab threshold, then we work on the Untracked Income table.
            elif nisab.nisab_reached == False:
                total_before = session.query(func.sum(Untracked_Income.amount)).filter_by(user_id=userid).scalar()

                # If no savings, simply update nisab and return function.
                if total_before == None:
                    nisab.nisab_reached = False
                    flash('Nisab updated.', 'success')

                # If savings are still below updated nisab, do nothing.
                elif total_before < nisab_new:
                    flash('Nisab updated. Your savings are still below the nisab threshold and are not tracked for zakat.', 'success')

                # If savings cross updated nisab threshold, transfer entries from Untracked_Income table to Income table  
                elif total_before >= nisab_new:
                    query = session.query(Untracked_Income).filter_by(user_id=userid).order_by(Untracked_Income.date).all()

                    # Iterate over the results and note date when the sum reaches the target amount
                    total = 0
                    nisab_crossing_date = query[0].date
                    for income in query:
                        total += income.amount
                        if total >= nisab_new:
                            nisab_crossing_date = income.date
                            break
                    
                    # Get remaining entries from the Untracked_Income table
                    untracked_incomes = session.query(Untracked_Income).filter_by(user_id=userid).order_by(Untracked_Income.date).all()

                    # Loop through each entry and add it to the Income table
                    for income in untracked_incomes:
                        if income.date < nisab_crossing_date:
                            entry = Income(date=income.date, amount=income.amount, user_id=userid, due_amount= (2.5/100 * float(income.amount)), due_date=plus_one_hijri(nisab_crossing_date))
                        elif income.date >= nisab_crossing_date:
                            entry = Income(date=income.date, amount=income.amount, user_id=userid, due_amount= (2.5/100 * float(income.amount)), due_date=plus_one_hijri(income.date))
                        session.add(entry)
                        session.delete(income)
                        session.commit()
                            
                    # Update nisab status and flash message
                    nisab.nisab_reached = True
                    session.commit()
                    flash('Nisab updated. Your savings now cross the updated nisab threshold and are now tracked for zakat.', 'info')
                
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
                        due_amount= (2.5/100 * float(next_amount)))
    session.add(next_entry)
    session.commit()

    # If remaining savings are above nisab, do nothing.
    nisab = session.query(Nisab).filter_by(user_id=userid).first()
    remaining_savings = session.query(func.sum(Income.amount)).filter_by(user_id=userid, paid=False).scalar()
    if remaining_savings >= nisab.amount:
        flash('Zakat paid; your remaining savings cross the nisab threshold, and so are being tracked for next hijri year.', 'success')
        return redirect('/due')
    
    # If remaining savings dip below updated nisab, shift previous savings entries to untracked_income table and stop tracking.
    elif remaining_savings < nisab.amount:
        incomes = session.query(Income).filter_by(user_id=userid, paid=False).order_by(Income.date).all()
        for income in incomes:
            stop_tracking = Untracked_Income(amount=income.amount, date=income.date, user_id=userid)
            session.add(stop_tracking)
            session.delete(income)
        nisab.nisab_reached = False
        session.commit()
        flash('Zakat paid; your remaining savings are below the nisab, and are therefore not being tracked.', 'success')
        return redirect('/due')
    

@app.route('/delete_entry', methods = ["POST"])
@login_required
def delete_entry():
    userid = flasksession.get("user_id")
    action = request.form.get("action")
    income_id = request.form.get('income_id')

    # If user deletes one entry from history (paid zakat)
    if action == 'paid':
        entry = session.query(Income).get(income_id)
        session.delete(entry)
        session.commit()
        flash('Entry deleted.', 'success')
        return redirect('/history')
    
    # If user clears history
    if action == 'clear_history':
        history = session.query(Income).filter_by(user_id=userid, paid=True)
        for income in history:
            session.delete(income)
        session.commit()
        flash('Cleared History.', 'success')
        return redirect('/history')

    # If user deletes from untracked table
    if action == 'untracked':
        entry = session.query(Untracked_Income).get(income_id)
        session.delete(entry)
        session.commit()
        flash('Entry deleted.', 'success')
        return redirect('/dashboard')

    # If user deletes tracked (unpaid) entries from Income table
    entry = session.query(Income).get(income_id)
    session.delete(entry)
    session.commit()

    # Check if remaining amount is above/below nisab
    nisab = session.query(Nisab).filter_by(user_id=userid).first()
    remaining_savings = session.query(func.sum(Income.amount)).filter_by(user_id=userid, paid=False).scalar()

    # If no remaining savings, say so.
    if remaining_savings == None:
        flash('Entry deleted. You have no remaining savings.', 'success')
        nisab.nisab_reached = False
        session.commit()
        return redirect('/dashboard')
    
    # If still above nisab, do nothing
    if remaining_savings >= nisab.amount:
        flash('Entry deleted. Your remaining savings still cross the nisab threshold and zakat is still due.', 'success')
        return redirect('/dashboard')
    
    # If remaining savings dip below nisab, change tables and stop tracking.
    elif remaining_savings < nisab.amount:
        incomes = session.query(Income).filter_by(user_id=userid, paid=False).order_by(Income.date).all()
        for income in incomes:
            stop_tracking = Untracked_Income(user_id=userid, amount=income.amount, date=income.date)
            session.add(stop_tracking)
            session.delete(income)
        nisab.nisab_reached = False
        session.commit()
        flash('Entry deleted. Your remaining savings are below the nisab, and are therefore not being tracked.', 'success')
        return redirect('/dashboard')
    

@app.route('/history')
@login_required
def history():
    userid = flasksession.get('user_id')
    paid = session.query(Income).filter_by(user_id=userid, paid=True).all()
    return render_template('history.html', paid=paid)


@app.route('/due')
@login_required
def due():

    # Display zakat due, if any, as of now
    current_date = datetime.now()
    incomes_due = session.query(Income).filter(Income.due_date <= current_date).filter_by(paid=False, user_id=flasksession.get("user_id"))
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
        flash("must provide username/password", "danger")
        return redirect('/settings')

    # Ensure correct username was submitted 
    user = session.query(User).get(userid)
    if username != user.username:
        flash("Invalid username!", "danger")
        return redirect('/settings')

    # Ensure username exists and password is correct
    if not user or not check_password_hash(user.hash, password):
        flash("invalid username and/or password", "danger")
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
    flash("Your account has been deleted.", "success")
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
        flash('All fields are required!', 'danger')
        return redirect('/settings')
    
    # Ensure correct password is entered
    if not check_password_hash(user.hash, old_password):
        flash('Invalid password entered!', 'danger')
        return redirect('/settings')
    
    # Ensure passwords match
    if new_password != confirmation:
        flash('Passwords do not match!', 'danger')
        return redirect('/settings')
    
    # Change password
    user.hash = generate_password_hash(new_password)
    session.commit()
    flash('Password changed successfully!', 'success')
    return redirect('/settings')


@app.route('/update_untracked', methods=["POST"])
@login_required
def update_untracked():

    # Get the form data into variables
    income_id = request.form.get('income_id')
    date_input = request.form.get('date')
    income = request.form.get('income')
    date = datetime.strptime(date_input, '%Y-%m-%d')
    userid = flasksession.get("user_id")

    if not isfloat(income) or float(income) <= 0:
        response_data = {'message': 'Please enter valid amount!'}
        flash('Please enter valid amount!', 'danger')
        return jsonify(response_data)

    # Get nisab
    nisab = session.query(Nisab).filter_by(user_id=userid).first()
    
    # Update database
    entry = session.query(Untracked_Income).get(income_id)
    entry.date = date
    entry.amount = income
    session.commit()

    # Take action based on nisab
    total_now = session.query(func.sum(Untracked_Income.amount)).filter_by(user_id=userid).scalar()

    # If nisab not reached
    if total_now < nisab.amount:

        # Return a JSON response with a success message
        response_data = {'message': 'Entry updated successfully'}
        flash('Entry updated successfully!', 'success')
        return jsonify(response_data)
    
    # If nisab reached, transfer entries from Untracked_Income table to Income table   
    query = session.query(Untracked_Income).filter_by(user_id=userid).order_by(Untracked_Income.date).all()
    nisab.nisab_reached = True
    session.commit()

    # Iterate over the results and note date when the sum reaches the target amount
    total = 0
    nisab_crossing_date = query[0].date # Just intitializing the variable as a date time
    for income in query:
        total += income.amount
        if total >= nisab.amount:
            nisab_crossing_date = income.date
            break
    
    # Get remaining entries from the Untracked_Income table
    untracked_incomes = session.query(Untracked_Income).filter_by(user_id=userid).order_by(Untracked_Income.date).all()

    # Loop through each entry and add it to the Income table
    for income in untracked_incomes:

        # For entries before the sum crosses the nisab threshold, calculate due date from the date of nisab crossing
        if income.date < nisab_crossing_date:
            entry = Income(date=income.date, amount=income.amount, user_id=userid, due_amount= (2.5/100 * float(income.amount)), due_date=plus_one_hijri(nisab_crossing_date))

        # For entries after the sum crosses nisab threshold, calculate due date normally (ie according to entry date)
        elif income.date >= nisab_crossing_date:
            entry = Income(date=income.date, amount=income.amount, user_id=userid, due_amount= (2.5/100 * float(income.amount)), due_date=plus_one_hijri(income.date))

        session.add(entry)
        session.delete(income)
        session.commit()

    # Return a JSON response with a success message
    response_data = {'message': 'Entry updated successfully'}
    flash('Entry updated successfully. You have now crossed the nisab threshold and your income is being tracked for zakat.', 'success')
    return jsonify(response_data)


@app.route('/update_income', methods=["POST"])
@login_required
def update_income():

    # Get the form data into variables
    income_id = request.form.get('income_id')
    date_input = request.form.get('date')
    income = request.form.get('income')
    date = datetime.strptime(date_input, '%Y-%m-%d')
    userid = flasksession.get("user_id")

    if not isfloat(income) or float(income) <= 0:
        response_data = {'message': 'Please enter valid amount!'}
        flash('Please enter valid amount!', 'danger')
        return jsonify(response_data)

    # Get nisab
    nisab = session.query(Nisab).filter_by(user_id=userid).first()
    
    # Update database
    entry = session.query(Income).get(income_id)
    entry.date = date
    entry.amount = income
    entry.due_date = plus_one_hijri(date)
    entry.due_amount = (2.5/100 * float(income))
    session.commit()

    # Take action based on nisab
    total_now = session.query(func.sum(Income.amount)).filter_by(user_id=userid).scalar()

    # If still above nisab, update and do nothing
    if total_now >= nisab.amount:
        response_data = {'message': 'Entry updated successfully'}
        flash('Entry updated successfully. You savings still cross the nisab threshold and your income is being tracked for zakat.', 'success')
        return jsonify(response_data)
    
    # If it goes below nisab, change tables
    query = session.query(Income).filter_by(user_id=userid).order_by(Income.date).all()
    nisab.nisab_reached = False
    for income in query:
        change_table = Untracked_Income(date=income.date, amount=income.amount, user_id=userid)
        session.add(change_table)
        session.delete(income)
        session.commit() 

    # Send JSON response
    response_data = {'message': 'Entry updated successfully'}
    flash('Entry updated successfully. You savings have dipped below nisab and are now not being tracked.', 'success')
    return jsonify(response_data)


# SQLAlchemy - Flask removes database sessions at end of request
@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()