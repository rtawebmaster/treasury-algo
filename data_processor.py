import mysql.connector
from mysql.connector import Error
import logging
import pandas as pd
import numpy as np
from shared.config import get_db_connection

def load_and_process_data(): # parameters

    logging.info('Executing data_processor/load_and_process_data().')
    running_balances = pd.DataFrame()

    """
    Load and process data to generate running balances

    Parameters:
        parameters (dict): Parameters from the request

    Returns:
        pandas.DataFrame: DataFrame containing running balances
    """
    # CODE FROM THE WINDOWS NOTEBOOK

    # STEP 1: Get the asset classes combined with their parent class ID
    table_name = 'AssetClass'
    sql = """SELECT a.`ID`, a.`Title`, a.`Group`, a.`Issuer`, a.`PercentMax`,
    CASE WHEN p.`Title` IS NULL THEN a.`Title` ELSE p.`Title` END AS `AssetClassCombined`
    FROM `AssetClass` a
    LEFT JOIN ( SELECT ac.`ID`, ac.`Title`, ac.`Group`, ac.`PercentMax` FROM `AssetClass` ac
    WHERE AssetClassParentID = 0 ) p ON p.ID = a.AssetClassParentID
    WHERE AssetClassParentID = 0 AND a.Title != 'Not Assigned'
    """
    asset_classes = fetch_data(table_name, '',1,sql)
    asset_classes = asset_classes.rename(columns={'ID': 'AssetClassID', 'Title': 'AssetClassTitle', 'Group': 'AssetClassGroup', 'Issuer': 'AssetClassIssuer', 'PercentMax': 'AssetClassPercentMax'})

    # STEP 2(4): Running balance day view taken from the SQL views
    #           Q: Do we want to replace the SQL views with pandas dataframes?
    table_name = 'RunningBalanceDayView'
    running_balances = fetch_data(table_name)

    # Add the daily total portfolio balance to the running balances DataFrame
    # Convert TransactionDate to datetime if not already
    running_balances['TransactionDate'] = pd.to_datetime(running_balances['TransactionDate'])
    # Filter and pivot Portfolio balances
    portfolio_balances = running_balances[running_balances['TransactionClass'] == 'Portfolio'].copy()
    portfolio_balances['RunningTotal'] = pd.to_numeric(portfolio_balances['RunningTotal'])
    # Create a series with daily portfolio balances
    daily_portfolio = portfolio_balances.set_index('TransactionDate')['RunningTotal']
    # Add portfolio balance to runningBalances DataFrame
    running_balances = running_balances.merge(
        daily_portfolio.reset_index().rename(columns={'RunningTotal': 'Portfolio'}),
        on='TransactionDate',
        how='left'
    )
    # Add the asset class PercentMax column to the running balances DataFrame matching the on TransactionClass column
    # Create a mapping dictionary from Title to PercentMax
    percentmax_mapping = dict(zip(asset_classes['AssetClassTitle'], asset_classes['AssetClassPercentMax']))
    # Update PercentMax in running_balances using the mapping
    running_balances['PercentMax'] = running_balances['TransactionClass'].map(percentmax_mapping).fillna(1.0)
    # Convert PercentMax to float
    # running_balances['PercentMax'] = pd.to_numeric(running_balances['PercentMax'])
    # Check the PercentMax mapping
    # percentmax_mapping
    # running_balances #.info()
    # Compute the asset class's maximum based on the policy
    #       NOTE: The PercentMax map() inserts an object instead of a float. The object->float conversion resets the value to 0.0. TODO: Fix this.
                   # running_balances['PolicyMax'] = 0
    running_balances['PolicyMax'] = running_balances['Portfolio'] * running_balances['PercentMax'].astype(float)
    # running_balances.info()
    # Add the daily available cash balance to the running balances DataFrame
    # Filter and pivot cash balances
    cash_balances = running_balances[running_balances['TransactionClass'] == 'Cash/Sweep'].copy()
    cash_balances['RunningTotal'] = pd.to_numeric(cash_balances['RunningTotal'])
    # Create a series with daily portfolio balances
    daily_cash = cash_balances.set_index('TransactionDate')['RunningTotal']
    # Add portfolio balance to runningBalances DataFrame
    running_balances = running_balances.merge(
        daily_cash.reset_index().rename(columns={'RunningTotal': 'CashSweep'}),
        on='TransactionDate',
        how='left'
    )
    # Add the amount investable column
    #       if [TransactionClass] <> "Portfolio" && [TransactionClass] <> "Cash/Sweep",
    #       then [PolicyMax]-[RunningTotal] else [RunningTotal]
    # Convert RunningTotal to numeric if it's not already
    running_balances['RunningTotal'] = pd.to_numeric(running_balances['RunningTotal'])
    # Add Investable column based on the condition
    running_balances['Investable'] = np.where(
        (running_balances['TransactionClass'] != 'Portfolio') &
        (running_balances['TransactionClass'] != 'Cash/Sweep'),
        running_balances['PolicyMax'] - running_balances['RunningTotal'],
        running_balances['RunningTotal']
    )
    # Add the final available column
    #       if ([TransactionClass] <> "Portfolio" && [TransactionClass] <> "Cash/Sweep",
    #       then MIN([CashSweep],[Investable]) else [RunningTotal])
    running_balances['Available'] = np.where(
        (running_balances['TransactionClass'] != 'Portfolio') &
        (running_balances['TransactionClass'] != 'Cash/Sweep'),
        np.minimum(running_balances['CashSweep'], running_balances['Investable']),
        running_balances['RunningTotal']
    )
    # Test output the final dataframe
    # Suppress scientific notation by setting float_format
    pd.options.display.float_format = '{:,.0f}'.format
    # Display the dataframe without scientific notation
    running_balances[running_balances['TransactionClass'] == 'US Agencies']
    return running_balances

# Fetch data from database and return as a DataFrame
def fetch_data(table_name, column_names='*', condition='1', sql=False):
    logging.info(f'Fetching data from {table_name}')
    try:
        # Get a connection to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        # Fetch
        if sql:
            cursor.execute(sql)
        else:
            query = f"SELECT {column_names} FROM {table_name} WHERE {condition}"
            cursor.execute(query)
        # Fetch column names
        columns = [col[0] for col in cursor.description]
        # Fetch data
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)
        return df
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()