import mysql.connector
from mysql.connector import Error
import logging
import pandas as pd
from datetime import datetime
from shared.config import get_db_connection

def write_results_to_database(windows_df, asset_classes_df):
    """
    Insert data from windows dataframe into the InvestmentWindow MySQL table,
    looking up AssetClassID from asset_classes dataframe.
    Args:
        windows_df: DataFrame containing window data
        asset_classes_df: DataFrame containing asset class mappings
    Returns:
        bool: True if successful
    """
    logging.info('Executing database_writer/write_results_to_database().')
    # try:
    conn = get_db_connection()
    if conn.is_connected():
        logging.info("Connected to MySQL database")
    else:
        logging.error("Failed to connect to MySQL database")
        return False
    # Create a cursor
    cursor = conn.cursor()
    # Create a mapping dictionary from asset class title to ID
    asset_class_mapping = dict(zip(asset_classes_df['AssetClassTitle'], asset_classes_df['AssetClassID']))
    # Get current datetime for LastEdited and Created fields
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Prepare insert statement
    insert_query = """
    INSERT INTO InvestmentWindow
    (ClassName, LastEdited, Created, FromDate, EndDate, Available, Days, AssetClassID)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    # Counter for successful and failed inserts
    successful = 0
    failed = 0
    # Process each row in the windows dataframe
    for _, row in windows_df.iterrows():
        try:
            # Look up AssetClassID from the asset_classes dataframe
            asset_class_title = row['Asset Class']
            asset_class_id = asset_class_mapping.get(asset_class_title)

            if asset_class_id is None:
                print(f"Warning: Asset class '{asset_class_title}' not found in asset_classes dataframe")
                failed += 1
                continue

            # Prepare data for insert
            data = (
                'App\\Model\\InvestmentWindow',  # ClassName
                current_datetime,                # LastEdited
                current_datetime,                # Created
                row['StartDate'].strftime('%Y-%m-%d'),  # FromDate
                row['EndDate'].strftime('%Y-%m-%d'),    # EndDate
                float(row['LowPointBalance']),   # Available
                int(row['TimeSpanDays']),        # Days
                int(asset_class_id)              # AssetClassID
            )
            # Execute insert
            cursor.execute(insert_query, data)
            successful += 1
        except Exception as e:
            print(f"Error inserting row: {e}")
            failed += 1
    # Commit the transaction
    conn.commit()
    cursor.close()
    print(f"Data import complete. {successful} rows inserted successfully, {failed} rows failed.")

def truncate_investment_window_table():
    """
    Truncate the InvestmentWindow table to remove all existing data.

    Args:
        None
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE InvestmentWindow")
        print("InvestmentWindow table truncated successfully")
    except Exception as e:
        print(f"Error truncating InvestmentWindow table: {e}")
    finally:
        cursor.close()