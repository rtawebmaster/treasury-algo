import pandas as pd
import numpy as np
from datetime import timedelta
import logging

def process_investment_algorithm(running_balances):
    """
    Process the investment algorithm using running balances
    """
    windows = pd.DataFrame()
    assets = ['Certificate of Deposit', 'Mutual Fund', 'Commercial Paper', 'Money Market', 'US Treasuries', 'US Agencies']
    for asset_class in assets:
        today = pd.Timestamp.today().normalize()
        timespan = today + pd.DateOffset(months=4)
        df = running_balances[
            (running_balances['TransactionClass'] == asset_class) &
            (running_balances['TransactionDate'] >= today) &
            (running_balances['TransactionDate'] <= timespan)
        ][['TransactionDate', 'Available']].rename(
            columns={'TransactionDate': 'Date', 'Available': 'Balance'}
        )
        result = identify_low_points(df)
        progressive_result = identify_progressive_timespans(df)
        result = pd.concat([result, progressive_result], ignore_index=True) #.fillna(0)
        result['Asset Class'] = asset_class
        windows = pd.concat([windows,result], ignore_index=True)
        # result.sort_values('StartDate', ascending=True)
    # result.sort_values('StartDate', ascending=True).drop(columns=['EndDate'])

    result.to_csv('debug_result.csv', index=False)
    windows.to_csv('debug_windows.csv', index=False)
    progressive_result.to_csv('debug_progressive.csv', index=False)
    return windows

def identify_low_points(df, asset_class ='Asset Class', min_days=2):
    """
    This function identifies low points in a time series df and creates time intervals from
        those points to the max. date in the dataset. This represents the longest investment period.
    Identifies time intervals from the latest date back to progressively earlier low points.
        Each interval starts at an identified low point and extends forward to the maximum date.
    When consecutive points have the same low balance, only the first occurrence is captured.
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing at least 'Date' and 'Balance' columns
    min_days : int, default=2
        Minimum number of days for a valid time span
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing the low points and their time spans
    """
    # Ensure Date column is datetime type
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'])
    # Sort df chronologically
    df = df.sort_values('Date')
    # Get the maximum date in the dataset (end of all intervals)
    max_date = df['Date'].max()
    min_date = df['Date'].min()
    # Find local minima (low points) in reverse chronological order
    dates = df['Date'].tolist()
    balances = df['Balance'].tolist()
    local_minima = []
    # Track unique balance values we've already seen to avoid duplicates
    seen_balances = set()
    for i in range(len(df) - 1, -1, -1):  # Iterate from end to start
        current_date = dates[i]
        current_balance = balances[i]
        # Skip the maximum date (we'll always end there)
        if current_date == max_date:
            continue
        # Check if this is a local minimum by looking at adjacent points
        is_local_min = True
        # Check if the current point is lower than all future points
        for j in range(i + 1, len(df)):
            if balances[j] < current_balance:
                is_local_min = False
                break
        if is_local_min and current_balance not in seen_balances:
            local_minima.append((current_date, current_balance))
            seen_balances.add(current_balance)
    # Sort local minima from latest to earliest
    local_minima.sort(key=lambda x: x[0], reverse=True)
    # Find the absolute minimum for the entire period
    absolute_min_idx = df['Balance'].idxmin()
    absolute_min_date = df.loc[absolute_min_idx, 'Date']
    absolute_min_balance = df.loc[absolute_min_idx, 'Balance']
    # Process local minima to create time intervals
    results = []
    # Add intervals from each low point to max_date
    for i, (low_date, low_balance) in enumerate(local_minima):
        # Start date is the low point
        start_date = low_date
        # End date is always the maximum date
        end_date = max_date
        # Calculate time span
        time_span = (end_date - start_date).days + 1  # +1 to include both start and end dates
        # Check if time span meets minimum requirement
        if time_span >= min_days:
            # Find the minimum balance in this time span
            span_min_balance = df[(df['Date'] >= start_date) &
                                 (df['Date'] <= end_date)]['Balance'].min()
            results.append({
                'LowPointDate': low_date,
                'LowPointBalance': low_balance,
                'StartDate': start_date,
                'EndDate': end_date,
                'TimeSpanDays': time_span,
                'BalanceAboveMinimum': absolute_min_balance
                # 'MinimumBalanceInSpan': span_min_balance
            })
    # Check if the absolute minimum is already in our results by balance value
    absolute_min_already_included = absolute_min_balance in [res['LowPointBalance'] for res in results]
    # Always add the full time interval (min_date to max_date)
    # containing the absolute minimum balance if not already captured
    if not absolute_min_already_included:
        full_span = (max_date - min_date).days + 1
        results.append({
            'LowPointDate': absolute_min_date,
            'LowPointBalance': absolute_min_balance,
            'StartDate': min_date,
            'EndDate': max_date,
            'TimeSpanDays': full_span,
            'BalanceAboveMinimum': absolute_min_balance
            # 'MinimumBalanceInSpan': absolute_min_balance
        })
    # Convert results to DataFrame and sort by time span (ascending)
    if results:
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values('TimeSpanDays')
        return result_df
    else:
        return pd.DataFrame(columns=['LowPointDate', 'LowPointBalance',
                                    'StartDate', 'EndDate', 'TimeSpanDays'])
    
def identify_progressive_timespans(df, asset_class='Asset Class', min_days=2):
    """
    This function creates progressive timespans starting from the minimum date,
    with each timespan increasing in length by one day, until reaching the point 
    with the lowest balance in the dataset.
    
    Unlike identify_low_points which works backwards from low points to max date,
    this function works forward from min date with incrementally longer periods.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing at least 'Date' and 'Balance' columns
    asset_class : str, default='Asset Class'
        Asset class column name (for future use/compatibility)
    min_days : int, default=2
        Minimum number of days for a valid time span
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame containing progressive timespans with columns:
        - LowPointDate: Date when the absolute minimum balance occurred
        - LowPointBalance: The absolute minimum balance value in the dataset
        - StartDate: Always the minimum date in dataset
        - EndDate: Progressive end dates (min_date + n days)
        - TimeSpanDays: Length of timespan in days
        - MinBalanceInSpan: Lowest balance found in this timespan
        - EndBalance: Balance at the end date of this timespan
        - BalanceAboveMinimum: End balance minus the absolute minimum balance in entire dataset
    """
    # Ensure Date column is datetime type
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'])
    
    # Sort df chronologically
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Get the minimum and maximum dates
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    
    # Find the absolute minimum balance in the entire dataset
    absolute_min_balance = df['Balance'].min()
    
    # Find the date where the absolute minimum balance occurs (first occurrence)
    absolute_min_date = df[df['Balance'] == absolute_min_balance]['Date'].iloc[0]
    
    # Create a list of all unique dates for easier processing
    unique_dates = sorted(df['Date'].unique())
    min_date_idx = unique_dates.index(min_date)
    absolute_min_date_idx = unique_dates.index(absolute_min_date)
    
    results = []
    
    # Generate progressive timespans from min_date until we reach absolute_min_date
    for end_idx in range(min_date_idx, absolute_min_date_idx + 1):
        start_date = min_date
        end_date = unique_dates[end_idx]
        
        # Calculate time span
        time_span = (end_date - start_date).days + 1
        
        # Check if time span meets minimum requirement
        if time_span >= min_days:
            # Get data for this timespan
            span_data = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
            
            # Find minimum balance in this span
            min_balance_in_span = span_data['Balance'].min()
            
            # Get balance at end date
            end_balance = span_data[span_data['Date'] == end_date]['Balance'].iloc[0]
            
            # Calculate balance above minimum (end balance minus absolute minimum)
            balance_above_minimum = end_balance - absolute_min_balance
            
            # Only include timespans where BalanceAboveMinimum is greater than 0
            if balance_above_minimum > 0:
                results.append({
                    'LowPointDate': absolute_min_date,
                    'LowPointBalance': absolute_min_balance,
                    'StartDate': start_date,
                    'EndDate': end_date,
                    'TimeSpanDays': time_span,
                    'MinBalanceInSpan': min_balance_in_span,
                    'EndBalance': end_balance,
                    'BalanceAboveMinimum': balance_above_minimum
                })
    
    # Convert results to DataFrame
    if results:
        result_df = pd.DataFrame(results)
        return result_df
    else:
        return pd.DataFrame(columns=['LowPointDate', 'LowPointBalance', 'StartDate', 'EndDate', 'TimeSpanDays', 
                                   'MinBalanceInSpan', 'EndBalance', 'BalanceAboveMinimum'])
