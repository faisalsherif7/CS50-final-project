# for functions called by app
from database import db_session as session

from hijri_converter import Hijri, Gregorian
from datetime import datetime, timedelta
from sqlalchemy.sql import func

# for login_required
from functools import wraps
from flask import redirect, session as flasksession, flash


def calculate_due_date():
    current_date = datetime.now()
    current_hijri_date = Gregorian(current_date.year, current_date.month, current_date.day).to_hijri()
    next_hijri_year = current_hijri_date.year + 1
    next_gregorian_date = Hijri(next_hijri_year, current_hijri_date.month, current_hijri_date.day).to_gregorian()
    return next_gregorian_date

def plus_one_hijri(input_date):
    current_date = input_date
    current_hijri_date = Gregorian(current_date.year, current_date.month, current_date.day).to_hijri()
    next_hijri_year = current_hijri_date.year + 1
    next_gregorian_date = Hijri(next_hijri_year, current_hijri_date.month, current_hijri_date.day).to_gregorian()
    return next_gregorian_date

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if flasksession.get("user_id") is None:
            flash('Please log in to access this page', 'info')
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

# Import at this line to prevent circular imports
from models import Income, Untracked_Income
    
# Ensure correct due dates of entries on addition/modification/deletion of savings or on updation of nisab
def update_due_dates(userid, nisab_amount):

    # Ensure correct due dates
    query = session.query(Income).filter_by(user_id=userid, paid=False).order_by(Income.date).all()

    # Iterate over the results and note date when the sum crosses the nisab amount
    total = 0
    nisab_crossing_date = query[0].date # Just initializing variable as a datetime object
    for income in query:
        total += income.amount
        if total >= nisab_amount:
            nisab_crossing_date = income.date
            break
    
    # Update due dates to account for date of crossing nisab threshold
    for income in query:
        if income.date <= nisab_crossing_date:
            income.due_date = plus_one_hijri(nisab_crossing_date)
        elif income.date > nisab_crossing_date:
            income.due_date = plus_one_hijri(income.date)
    session.commit()
    return 


# Start tracking incomes and shift from Untracked_Income to Income table
def start_tracking(userid, nisab_amount):

    # Get all entries from Untracked_Income table 
    query = session.query(Untracked_Income).filter_by(user_id=userid).order_by(Untracked_Income.date).all()

    # Iterate over the results to find date when the sum reaches the target amount
    total = 0
    nisab_crossing_date = query[0].date # Just intitializing the variable as a datetime object
    for income in query:
        total += income.amount
        if total >= nisab_amount:
            nisab_crossing_date = income.date
            break

    # Loop through each entry and add it to the Income table
    for income in query:

        # For entries before the sum crosses the nisab threshold, calculate due date from the date of nisab crossing
        if income.date <= nisab_crossing_date:
            entry = Income(date=income.date, amount=income.amount, user_id=userid, due_amount= (2.5/100 * float(income.amount)), due_date=plus_one_hijri(nisab_crossing_date))

        # For entries after the sum crosses nisab threshold, calculate due date normally (ie according to entry date)
        elif income.date > nisab_crossing_date:
            entry = Income(date=income.date, amount=income.amount, user_id=userid, due_amount= (2.5/100 * float(income.amount)), due_date=plus_one_hijri(income.date))
        
        session.add(entry)
        session.delete(income)
        session.commit()
        
    return
    

# Stop tracking and shift from Incomes to Untracked_Incomes table
def stop_tracking(userid, nisab):
    incomes = session.query(Income).filter_by(user_id=userid, paid=False).order_by(Income.date).all()
    for income in incomes:
        stop_tracking = Untracked_Income(amount=income.amount, date=income.date, user_id=userid)
        session.add(stop_tracking)
        session.delete(income)
    nisab.nisab_reached = False
    session.commit()
    return