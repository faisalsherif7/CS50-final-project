from sqlalchemy import create_engine, Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy import event

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    hash = Column(String, nullable=False)
    income = relationship("Income", back_populates="user")
    expenses = relationship("Expenses", back_populates="user")
    
class Income(Base):
    __tablename__ = 'income'
    id = Column(Integer, primary_key=True)
    amount = Column(Numeric(10,2))
    date = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="income")
    
class Expenses(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    amount = Column(Numeric(10,2))
    date = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="expenses")

engine = create_engine('sqlite:///zakat.db')
Base.metadata.create_all(engine)
Session = scoped_session(sessionmaker(bind=engine))
session = Session()

@event.listens_for(Expenses, 'after_insert')
def update_income(mapper, connection, target):
    remaining_amount = int(target.amount)
    incomes = session.query(Income).filter(Income.user_id == target.user_id).order_by(Income.date.desc()).all()
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
    session.commit()