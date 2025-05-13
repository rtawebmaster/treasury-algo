import logging
import json
import os
from datetime import datetime

# Import modularized code
from data_processor import load_and_process_data
from algorithm_processor import process_investment_algorithm
from database_writer import write_results_to_database

def ProcessTreasuryForecastingData():
    logging.info('Python HTTP trigger function processed a request.')
    logging.info('Treasury forecasting function processing request.')

    # try:
    investment_windows = []

    # # Part 1: Data loading and processing
    logging.info("Starting data loading and initial processing")
    running_balances = load_and_process_data() # Pass parameters if needed: req_body)
    logging.info(f"Data processing complete. Shape: {running_balances.shape}")

    # # Part 2: Algorithm processing
    logging.info("Starting algorithm processing")
    investment_windows = process_investment_algorithm(running_balances)
    logging.info(f"Algorithm processing complete. Found {len(investment_windows)} investment windows")

    # # Part 3: Database writing
    logging.info("Starting database write operation")
    write_results_to_database(investment_windows)
    logging.info("Database write operation complete")
    return 'Success'

    # except Exception as e:
    #     logging.error(f"Error processing treasury forecast: {str(e)}")
    #     return 'Failure'

if __name__ == "__main__":
    # This is for local testing
    logging.basicConfig(level=logging.INFO)
    ProcessTreasuryForecastingData()