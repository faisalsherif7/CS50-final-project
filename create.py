import app, models, utils, database
from database import Base 
from database import db_session as session

Base.metadata.create_all(bind=session.bind)