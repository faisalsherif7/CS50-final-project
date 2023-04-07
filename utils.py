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

def plus_one_hijri(input_date):
    current_date = input_date
    current_hijri_date = Gregorian(current_date.year, current_date.month, current_date.day).to_hijri()
    next_hijri_year = current_hijri_date.year + 1
    next_gregorian_date = Hijri(next_hijri_year, current_hijri_date.month, current_hijri_date.day).to_gregorian()
    return next_gregorian_date

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

def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False