from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. Define the database connection URL
DATABASE_URL = "sqlite:///./database.db" # Using an in-memory SQLite database for this example

# 2. Create the base class for our models
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)