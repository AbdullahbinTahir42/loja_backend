from sqlalchemy import create_engine, Column, Integer, String
from database import Base


class User(Base):
    __tablename__ = 'users' # The name of the table in the database

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)  # Default role for new users


class Items(Base):
    __tablename__ = 'items'  # The name of the table in the database

    id = Column(Integer, primary_key=True, index=True)
    image_name = Column(String)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Integer)
    quantity = Column(Integer)
    category = Column(String)