from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///zakat.db'
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    hash = db.Column(db.String, nullable=False)
    income = db.relationship("Income", back_populates="user")
    expenses = db.relationship("Expenses", back_populates="user")
    
class Income(db.Model):
    __tablename__ = 'income'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10,2))
    date = db.Column(db.DateTime, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates="income")
    
class Expenses(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10,2))
    date = db.Column(db.DateTime, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates="expenses")

@event.listens_for(Expenses, 'after_insert')
def update_income(mapper, connection, target):
    remaining_amount = target.amount
    incomes = Income.query.filter(Income.user_id == target.user_id).order_by(Income.date.desc()).all()
    for income in incomes:
        if remaining_amount > 0:
            if remaining_amount >= income.amount:
                income.amount = 0
                remaining_amount -= income.amount
            else:
                income.amount -= remaining_amount
                remaining_amount = 0
        else:
            break
    db.session.commit()
