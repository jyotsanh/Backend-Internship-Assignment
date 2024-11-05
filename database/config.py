"""
This module sets up the database engine and session maker.

It creates the database tables if they don't exist and sets up
the session maker for the database connection.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
import os
from dotenv import load_dotenv

load_dotenv('.env')

# The database URL is either the environment variable
# DATABASE_URL or a default SQLite database
DATABASE_URL = os.getenv('DATABASE_URL')
DATABASE_URL = "jhvjv"
try:
    # Try to create the engine with the DATABASE_URL
    engine = create_engine(DATABASE_URL)
    # Test the connection
    engine.connect()
except Exception as e:
    print(f"Failed to connect to {DATABASE_URL}: {str(e)}")
    print("Falling back to local SQLite database")
    # Fall back to local SQLite database
    DATABASE_URL = "sqlite:///./database.db"
    engine = create_engine(DATABASE_URL)

# Create the session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the database tables if they don't exist
Base.metadata.create_all(bind=engine)

