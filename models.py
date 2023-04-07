from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, event
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from database import db_session as session
from utils import calculate_due_date


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    hash = Column(String, nullable=False)
    income = relationship("Income", back_populates="user")
    expenses = relationship("Expenses", back_populates="user")
    nisab = relationship("Nisab", back_populates="user")
    untracked_income = relationship("Untracked_Income", back_populates="user")
    
class Income(Base):
    __tablename__ = 'income'
    id = Column(Integer, primary_key=True)
    amount = Column(Numeric(10,2))
    date = Column(DateTime, default=func.now())
    due_date = Column(DateTime, default=calculate_due_date())
    due_amount = Column(Numeric(10,2))
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="income")
    paid = Column(Boolean, default=False)

class Expenses(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    amount = Column(Numeric(10,2))
    date = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="expenses")

class Nisab(Base):
    __tablename__ = 'nisab'
    id = Column(Integer, primary_key=True)
    amount = Column(Numeric(10,2))
    user_id = Column(Integer, ForeignKey('users.id'))
    nisab_reached = Column(Boolean, default=False)
    user = relationship("User", back_populates="nisab")

class Untracked_Income(Base):
    __tablename__ = 'untracked_income'
    id = Column(Integer, primary_key=True)
    amount = Column(Numeric(10,2))
    date = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="untracked_income")