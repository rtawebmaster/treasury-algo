## Path
C:\Users\Adam.Skrzypulec\OneDrive - RTA\www\Treasury Forecasting


## Install the dependencies (without using an virtual env)
pip install pandas
pip install mysql-connector-python
pip install python-dotenv


## Notebooks execution order
1. windows (prod) > running_balances.pkl
2. algo2 < running_balances.pkl > invest_windows.pkl
3. insert (local) < invest_windows.pkl