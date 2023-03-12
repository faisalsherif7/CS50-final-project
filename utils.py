from hijri_converter import Hijri, Gregorian
from datetime import datetime, timedelta
from sqlalchemy.sql import func

# for login_required
from functools import wraps
from flask import redirect, session

def calculate_due_date():
        current_date = datetime.now()
        current_hijri_date = Gregorian(current_date.year, current_date.month, current_date.day).to_hijri()
        next_hijri_year = current_hijri_date.year + 1
        next_gregorian_date = Hijri(next_hijri_year, current_hijri_date.month, current_hijri_date.day).to_gregorian()
        return next_gregorian_date

# not in use
def calculate_zakat_due(savings_amount, user_id):
    # Get the current Hijri year
    current_hijri_year = hijri_converter.Gregorian(datetime.now()).to_hijri().year
    
    # Calculate the Hijri year for the savings_amount
    hijri_year = hijri_converter.Gregorian(datetime.now().replace(month=1, day=1) - timedelta(days=1) + relativedelta(years=-savings_amount)).to_hijri().year
    
    # Check if the difference between the current and savings Hijri year is >= 1
    if current_hijri_year - hijri_year >= 1:
        # Create a new zakat record in the database
        zakat_amount = savings_amount * 0.025
        due_date = datetime.now() + timedelta(days=30)
        zakat_record = Zakat(user_id=user_id, savings_amount=savings_amount, zakat_amount=zakat_amount, due_date=due_date)
        db.session.add(zakat_record)
        db.session.commit()

        # Update the user's current zakat due
        user = User.query.get(user_id)
        user.current_zakat_due = zakat_amount
        user.current_zakat_due_date = due_date
        db.session.commit()

# not in use
def calculate_due_amount(context):
        income = context.current_parameters['amount']
        return income * 2.5

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
