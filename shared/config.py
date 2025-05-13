import pandas as pd
import numpy as np
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

def get_config():
    """Get configuration from environment variables"""
    return {
        # Any configuration values you need
    }

def get_db_connection():
    """Get database connection from environment variables"""
    try:

        # Load specific connection params from .env file
        from pathlib import Path
        env_path = Path('.') / '.env'
        load_dotenv(dotenv_path=env_path, override=True, verbose=True)

        # Database connection params from env variables (override .env values)
        DB_CONFIG = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
            "port": os.getenv("DB_PORT", 3306)  # Default MySQL port
        }
        print('Database URL: ' + os.environ.get('DB_HOST'))
        print('Database name: ' + os.environ.get('DB_NAME'))
        print('Database user: ' + os.environ.get('DB_USER'))
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        raise Exception(f"Database connection error: {str(e)}")