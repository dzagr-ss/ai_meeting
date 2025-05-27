import os
import sys
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from config import settings

def init_db():
    # Create database if it doesn't exist
    if not database_exists(settings.DATABASE_URL):
        create_database(settings.DATABASE_URL)
        print("Database created successfully")
    else:
        print("Database already exists")

if __name__ == "__main__":
    init_db() 