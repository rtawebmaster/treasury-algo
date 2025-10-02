import pandas as pd

# Prepare the DataFrame for the investment window analysis by ensuring proper data types and sorting.
def prepare_data(df, asset_class=None, start=pd.Timestamp.now(), end=pd.Timestamp.now()+pd.DateOffset(months=3)):
    """
    Prepare and clean the DataFrame for analysis.
    Args:
        df: DataFrame with 'TransactionDate', 'TransactionClass', and 'Available' columns
        asset_class: String to filter TransactionClass column (e.g., 'US Agencies')
        start_date: Optional starting date for analysis, defaults to today
        end_date: Optional ending date for analysis, defaults to 3 months from today
    Returns:
        DataFrame: Cleaned and sorted DataFrame with relevant columns and filtered by asset class (if provided)
    """
    # Define start and end dates
    start_date = pd.Timestamp(start).normalize()
    end_date = pd.Timestamp(end).normalize()

    # 1. Filter the data within the date range
    data = df[(df['TransactionDate'] >= start_date) & (df['TransactionDate'] <= end_date)].copy()

    # 2. Filter by asset class if specified
    if asset_class is not None:
        # Check if asset_class exists in TransactionClass column
        if asset_class not in df['TransactionClass'].unique():
            raise ValueError(f"Asset class '{asset_class}' not found in data")
        data = data[data['TransactionClass'] == asset_class].copy()
        if data.empty:
            raise ValueError(f"No data found for asset class: {asset_class}")

    # Set the TransactionDate to datetime
    data['TransactionDate'] = pd.to_datetime(data['TransactionDate'])

    # Sort
    data = data.sort_values('TransactionDate').reset_index(drop=True)
    data['TransactionClass'] = asset_class if asset_class else 'Not Specified'
    return data[['TransactionDate', 'Available','TransactionClass']]


# Step 1: Function to detect window intervals
def find_window_intervals(df, threshold=1_000_000):
    """
    Determine investment windows where the available balance exceeds a threshold and track the duration of these windows.
    df: DataFrame with 'TransactionDate' and 'Available' columns
    threshold = 1,000,000 - minimum balance to consider
    Returns the investment windows as a DataFrame with columns:
        'start_date': Start date of the investment window
        'end_date': End date of the investment window (None if ongoing)
        'amount': The balance amount during the window
        The following has been moved to a separate function:
            'change': Change in balance from the previous day
            'duration': Duration of the window in days
    """
    df = df.sort_values('TransactionDate').reset_index(drop=True)
    intervals = []

    for i in range(len(df)):
        base_row = df.iloc[i]
        base_amount = base_row['Available']
        if base_amount < threshold:
            continue

        start_date = base_row['TransactionDate']
        duration = 1
        end_date = None

        for j in range(i + 1, len(df)):
            if df.iloc[j]['Available'] >= base_amount:
                duration += 1
            else:
                end_date = df.iloc[j]['TransactionDate']
                break
        else:
            end_date = df.iloc[-1]['TransactionDate']

        if not intervals or intervals[-1]['start_date'] != start_date:
            intervals.append({
                'start_date': start_date,
                'end_date': end_date,
                'amount': base_amount,
                'duration': duration,
                'asset_class': df['TransactionClass'].iloc[0] if 'TransactionClass' in df.columns else 'Not Specified'
            })
    df_intervals = pd.DataFrame(intervals)
    # Format columns
    df_intervals['start_date'] = pd.to_datetime(df_intervals['start_date']).dt.date
    df_intervals['end_date'] = pd.to_datetime(df_intervals['end_date']).dt.date
    df_intervals['amount'] = df_intervals['amount'].round(2)
    # Keep Only the Max Amount Interval for Each Overlapping Period
    result = df_intervals.loc[df_intervals.groupby(['start_date'])['amount'].idxmax()]
    # Remove intervals that are completely contained within other intervals (with the same amount).
    # Keep only the interval with the maximum TimeSpanDays for each group of overlapping intervals with the same amount.
    result = df_intervals.loc[df_intervals.groupby(['end_date'])['duration'].idxmax()]
    # TODO: Instead of filtering this way, it will be more efficient using conditional logic that prevents the creation of new intervals
    #            while there is already an open one (while looping of the dates).
    return result

# Step 3: Update Changed Amounts Based on Prior Date from the Original Data
def calc_interval_metrics(df_intervals, df_data):
    """"
    Iterative lookback: For each interval, the code now loops backward through dates until it finds a balance that's different (from the current amount)
    """
    df_intervals['start_date'] = pd.to_datetime(df_intervals['start_date'])
    df_data['TransactionDate'] = pd.to_datetime(df_data['TransactionDate'])

    # Create a dictionary for faster lookups of amounts by date
    amount_by_date = df_data.set_index('TransactionDate')['Available'].to_dict()

    previous_amounts = []

    for start_date, current_amount in zip(df_intervals['start_date'], df_intervals['amount']):
        # Start looking from the day before
        lookback_date = start_date - pd.Timedelta(days=1)
        previous_amount = None
        max_lookback_days = 365  # Prevent infinite loops
        days_searched = 0

        while days_searched < max_lookback_days:
            if lookback_date in amount_by_date:
                candidate_amount = amount_by_date[lookback_date]
                # Check if the amount is different from current amount
                if round(candidate_amount, 2) != round(current_amount, 2):
                    previous_amount = candidate_amount
                    break
                else:
                    pass
            # Move back one more day
            lookback_date -= pd.Timedelta(days=1)
            days_searched += 1

        # If no different amount found, use 0 (handles first record case)
        if previous_amount is None:
            previous_amount = 0

        previous_amounts.append(previous_amount)

    df_intervals['previous_amount'] = previous_amounts
    df_intervals['change'] = (df_intervals['amount'] - df_intervals['previous_amount']).round(2)

    # Replace -0.0 with 0.0
    df_intervals['change'] = df_intervals['change'].apply(lambda x: 0.0 if x == 0 else x)

    return df_intervals


# Main function to process the investment algorithm for different asset classes
#     This function is called from the main (Azure functions) script and then it calls all the other functions in order
def process_investment_algorithm(running_balances):
    """
    Process the investment algorithm using running balances
    """
    windows = pd.DataFrame()
    assets = ['Certificate of Deposit', 'Mutual Fund', 'Commercial Paper', 'Money Market', 'US Treasuries', 'US Agencies']
    for asset_class in assets:
        print("Processing:", asset_class)
        data = None
        data = prepare_data(running_balances, asset_class, '2025-09-04', '2025-12-31')
        all_intervals = find_window_intervals(data).sort_values(['start_date'], ascending=[True])
        final_intervals = calc_interval_metrics(all_intervals, data)
        windows = pd.concat([windows, final_intervals], ignore_index=True)
    # Rename the columns for the database write
    windows = windows.rename(columns={
        'start_date': 'StartDate',
        'end_date': 'EndDate',
        'amount': 'LowPointBalance',
        'duration': 'TimeSpanDays',
        'asset_class': 'Asset Class',
        'previous_amount': 'PreviousAmount',
        'change': 'Change'
    })
    return windows