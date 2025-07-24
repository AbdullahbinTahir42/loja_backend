from sqlalchemy import create_engine, Column, Integer, String
from database import Base


class User(Base):
    __tablename__ = 'users' # The name of the table in the database

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)