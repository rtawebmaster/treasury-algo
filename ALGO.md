## Finding Investment Windows
The solution for identifying optimal investment windows is based on your account balance forecast. This is a practical problem for maximizing returns on temporarily available funds.

1. Identifies periods where your balance stays above a certain threshold
2. Finds the optimal balance between investment duration and amount
3. Provides a sorted list of investment opportunities

## implementation
Refer to the `algo.ipynb`
This code provides a comprehensive solution for finding optimal investment windows based on your account balance forecast.
Here's how it works:

## Key Features
Finding Investment Windows: The find_investment_windows function examines all possible date ranges where you have a consistently positive balance, calculating a "score" based on both the amount and duration.
Optimizing Non-overlapping Windows: The optimize_non_overlapping_windows function uses dynamic programming to select the best combination of non-overlapping investment windows to maximize your total return.
Visualization: The code includes a visualization function to help you see the investment windows superimposed on your balance timeline.

## How to Use It
1. Load your actual account balance forecast into a DataFrame with date and balance columns
2. Call the functions with your data:

```py
windows = find_investment_windows(df, min_days=30)  # Set your minimum investment period
optimal_windows = optimize_non_overlapping_windows(windows, top_n=20)
visualize_investment_windows(df, optimal_windows)
```

## Customization Options
You can adjust several parameters to match your investment criteria:
`min_days`: The minimum duration for an investment (e.g., 30, 60, 90 days)
`top_n`: How many top-scoring windows to consider when optimizing

The example code includes a simulated dataset with 500 days of balance data that can be easily replace it with actual data.


## Explanation of Finding Minimum Balances
The core challenge is determining how much money you can safely invest over different time periods based on your future account balance projections. Here's how the algorithm works:

Consider every possible starting day in your timeline (except for the last few days that would create windows shorter than your minimum investment period)
For each starting day:

Look at every possible ending day (that's at least your minimum investment period away)
For each start-end day pair, examine all the days in between
Find the lowest balance that occurs anywhere in that window
This lowest balance is the maximum amount you could safely invest during this entire period


Record the investment window information:

Start date and end date
The amount you can invest (the minimum balance in the window)
The duration in days
A "score" that measures how attractive this investment opportunity is (amount × days)


## Pseudo Code
```
FOR each possible start_day in the account timeline:
    # Skip start days that are too close to the end of our data
    IF start_day is too close to the end to form a minimum window:
        CONTINUE to next start_day

    FOR each possible end_day (starting from start_day + minimum_days):
        # Create a window from start_day to end_day
        window = all days from start_day to end_day (inclusive)

        # Find the minimum balance in this window
        min_balance = MINIMUM value of all balances in window

        # Only consider windows where we have money to invest
        IF min_balance > 0:
            days = number of days between start_day and end_day

            # Calculate how attractive this investment opportunity is
            score = min_balance × days

            # Save this investment opportunity
            SAVE {start_date, end_date, amount: min_balance, days, score}

# Sort all investment opportunities by score (best first)
SORT opportunities by score in DESCENDING order
```

## Idea/Strategy Summary
The idea is that for any given window of time, the amount you can safely invest is limited by the lowest balance that occurs during that window. If your balance drops to $5,000 on day 17 of a 30-day window, even if it's $20,000 on all other days, you can only invest $5,000 for the entire 30-day period.
By examining all possible windows (within practical constraints), the algorithm builds a comprehensive list of investment opportunities, which can then be filtered, ranked, or optimized based on your specific requirements.
