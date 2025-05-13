import mysql.connector
from mysql.connector import Error
import logging
import pandas as pd
from shared.config import get_db_connection

def write_results_to_database(investment_windows):
    """
    Write investment windows to the MySQL database

    Parameters:
        investment_windows (pandas.DataFrame): DataFrame containing investment windows

    Returns:
        bool: True if successful
    """
    try:
        connection = get_db_connection()

        # CODE FROM INSERT NOTEBOOK

        connection.close()
        return True

    except Error as e:
        logging.error(f"Database error: {str(e)}")
        raise