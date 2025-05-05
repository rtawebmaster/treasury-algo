import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from test_investment_windows import find_investment_windows

@pytest.fixture
def base_date():
    """Create a base date for our tests."""
    return datetime(2025, 5, 4)

def test_basic_stable_balance(base_date):
    """Test with a stable balance - should find one window covering the entire period."""
    dates = pd.date_range(start=base_date, periods=10)
    balances = [1000] * 10  # Constant balance of 1000

    df = pd.DataFrame({'date': dates, 'balance': balances})
    windows = find_investment_windows(df, min_days=3)

    # Check that we have the expected number of windows (with min_days=3, we should have windows of lengths 3,4,5,6,7,8,9,10)
    expected_windows = sum(range(3, 11))  # Sum of 3 to 10
    assert len(windows) == expected_windows

    # Check that the top window covers the entire period
    top_window = windows[0]
    assert top_window['start_date'] == dates[0]
    assert top_window['end_date'] == dates[-1]
    assert top_window['amount'] == 1000
    assert top_window['days'] == 10

def test_increasing_balance(base_date):
    """Test with an increasing balance - min balance should be at the start."""
    dates = pd.date_range(start=base_date, periods=10)
    balances = list(range(1000, 2000, 100))  # 1000, 1100, 1200, ..., 1900

    df = pd.DataFrame({'date': dates, 'balance': balances})
    windows = find_investment_windows(df, min_days=3)

    # For any window, the minimum balance should be the balance at the start date
    for window in windows:
        start_idx = df[df['date'] == window['start_date']].index[0]
        expected_min = df.iloc[start_idx]['balance']
        assert window['amount'] == expected_min

def test_decreasing_balance(base_date):
    """Test with a decreasing balance - min balance should be at the end."""
    dates = pd.date_range(start=base_date, periods=10)
    balances = list(range(2000, 1000, -100))  # 2000, 1900, 1800, ..., 1100

    df = pd.DataFrame({'date': dates, 'balance': balances})
    windows = find_investment_windows(df, min_days=3)

    # For any window, the minimum balance should be the balance at the end date
    for window in windows:
        end_idx = df[df['date'] == window['end_date']].index[0]
        expected_min = df.iloc[end_idx]['balance']
        assert window['amount'] == expected_min

def test_fluctuating_balance(base_date):
    """Test with a fluctuating balance."""
    dates = pd.date_range(start=base_date, periods=10)
    balances = [1000, 1500, 800, 1200, 900, 1100, 750, 1300, 950, 1000]

    df = pd.DataFrame({'date': dates, 'balance': balances})
    windows = find_investment_windows(df, min_days=3)

    # Check the first window
    first_window = windows[0]
    assert first_window['amount'] == 750  # The minimum is 750

    # Double check all windows
    for window in windows:
        start_idx = df[df['date'] == window['start_date']].index[0]
        end_idx = df[df['date'] == window['end_date']].index[0]
        window_slice = df.iloc[start_idx:end_idx+1]
        expected_min = window_slice['balance'].min()
        assert window['amount'] == expected_min

def test_negative_balance(base_date):
    """Test with some negative balances - these periods should be excluded."""
    dates = pd.date_range(start=base_date, periods=10)
    balances = [1000, 1500, -200, 1200, 900, -100, 750, 1300, 950, 1000]

    df = pd.DataFrame({'date': dates, 'balance': balances})
    windows = find_investment_windows(df, min_days=3)

    # Check that no window includes days with negative balances
    for window in windows:
        start_idx = df[df['date'] == window['start_date']].index[0]
        end_idx = df[df['date'] == window['end_date']].index[0]
        window_slice = df.iloc[start_idx:end_idx+1]
        assert (window_slice['balance'] >= 0).all()

def test_minimum_days_requirement(base_date):
    """Test that windows shorter than min_days are excluded."""
    dates = pd.date_range(start=base_date, periods=10)
    balances = [1000] * 10

    df = pd.DataFrame({'date': dates, 'balance': balances})
    windows = find_investment_windows(df, min_days=5)

    # Check that all windows have at least min_days
    for window in windows:
        assert window['days'] >= 5

    # Check number of windows (should be sum of windows from length 5 to 10)
    expected_count = sum(range(1, 7))  # 1+2+3+4+5+6 = 21
    assert len(windows) == expected_count

def test_zero_balance(base_date):
    """Test with zero balances - these should be treated as non-investable."""
    dates = pd.date_range(start=base_date, periods=10)
    balances = [1000, 1500, 0, 1200, 900, 0, 750, 1300, 950, 1000]

    df = pd.DataFrame({'date': dates, 'balance': balances})
    windows = find_investment_windows(df, min_days=3)

    # Check that windows with zero balances have amount = 0
    for window in windows:
        start_idx = df[df['date'] == window['start_date']].index[0]
        end_idx = df[df['date'] == window['end_date']].index[0]
        window_slice = df.iloc[start_idx:end_idx+1]
        min_balance = window_slice['balance'].min()
        assert window['amount'] == min_balance

        # If a window has a zero balance day, its amount should be zero
        if 0 in window_slice['balance'].values:
            assert window['amount'] == 0

def test_empty_dataframe():
    """Test behavior with an empty dataframe."""
    df = pd.DataFrame({'date': [], 'balance': []})
    windows = find_investment_windows(df, min_days=3)

    assert len(windows) == 0

def test_insufficient_data(base_date):
    """Test behavior when dataframe has fewer rows than min_days."""
    dates = pd.date_range(start=base_date, periods=3)
    balances = [1000, 1500, 2000]

    df = pd.DataFrame({'date': dates, 'balance': balances})
    windows = find_investment_windows(df, min_days=5)

    assert len(windows) == 0

def test_score_calculation(base_date):
    """Test that the score is calculated correctly as amount * days."""
    dates = pd.date_range(start=base_date, periods=5)
    balances = [1000, 1500, 800, 1200, 900]

    df = pd.DataFrame({'date': dates, 'balance': balances})
    windows = find_investment_windows(df, min_days=3)

    for window in windows:
        expected_score = window['amount'] * window['days']
        assert window['score'] == expected_score

def test_sorting_by_score(base_date):
    """Test that windows are sorted by score in descending order."""
    dates = pd.date_range(start=base_date, periods=10)
    balances = [1000, 1500, 800, 1200, 900, 1100, 750, 1300, 950, 1000]

    df = pd.DataFrame({'date': dates, 'balance': balances})
    windows = find_investment_windows(df, min_days=3)

    # Check that windows are sorted by score
    for i in range(1, len(windows)):
        assert windows[i-1]['score'] >= windows[i]['score']

# Additional pytest-specific tests with parametrization
@pytest.mark.parametrize("min_days,expected_count", [
    (2, 45),  # 9+8+7+6+5+4+3+2+1 = 45
    (5, 21),  # 6+5+4+3+2+1 = 21
    (8, 3),   # 3+2+1 = 6 - 3 = 3
    (10, 1),  # 1
    (11, 0)   # No windows this long
])
def test_min_days_variations(base_date, min_days, expected_count):
    """Test how the min_days parameter affects the number of windows."""
    dates = pd.date_range(start=base_date, periods=10)
    balances = [1000] * 10

    df = pd.DataFrame({'date': dates, 'balance': balances})
    windows = find_investment_windows(df, min_days=min_days)

    assert len(windows) == expected_count

@pytest.mark.parametrize("balance_pattern,expected_min", [
    ([1000, 1500, 2000], 1000),  # Increasing - min at start
    ([2000, 1500, 1000], 1000),  # Decreasing - min at end
    ([1000, 500, 2000], 500),    # Valley - min in middle
    ([2000, 3000, 1000], 1000)   # Peak - min at end
])
def test_balance_patterns(base_date, balance_pattern, expected_min):
    """Test different balance patterns and verify minimum balance."""
    dates = pd.date_range(start=base_date, periods=len(balance_pattern))

    df = pd.DataFrame({'date': dates, 'balance': balance_pattern})
    windows = find_investment_windows(df, min_days=len(balance_pattern))

    assert len(windows) == 1  # Only one window of full length
    assert windows[0]['amount'] == expected_min