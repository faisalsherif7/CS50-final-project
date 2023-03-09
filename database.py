from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///zakat.db')
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, event
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    import models
    Base.metadata.create_all(bind=engine)