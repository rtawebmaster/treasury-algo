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

        # Database connection parameters
        DB_CONFIG = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME"),
            "port": os.getenv("DB_PORT", 3306)  # Default MySQL port
        }
        print('Database URL: ' + os.environ.get('DB_HOST'))
        connection = mysql.connector.connect(
            **DB_CONFIG
            # host=os.environ['DB_HOST'],
            # database=os.environ['DB_NAME'],
            # user=os.environ['DB_USER'],
            # password=os.environ['DB_PASSWORD']
        )
        return connection
    except Error as e:
        raise Exception(f"Database connection error: {str(e)}")