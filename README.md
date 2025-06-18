This is the V2 of the windows algo that has been vastly simplied. V1 is looking at all the windows checking sorted balances (a lot more complex).

## Order of things
1. algo.ipynb       first spike
2. windows.ipynb      rebuild of the daily asset balances -the df is saved into a .pkl file(s): running_balances.pkl
3. algo2.ipynb          process finding low points from the end with visual (to be replaced with forward look)
                          NOTE: For the deploy/release this code has been put into *_processor files that have then been added to the Azure function project

## Path
C:\Users\Adam.Skrzypulec\OneDrive - RTA\www\Treasury Forecasting v2

## Install the dependencies (without using an virtual env)
pip install pandas
pip install mysql-connector-python
pip install python-dotenv


## Notebooks execution order
1. windows (prod) > running_balances.pkl
2. algo2 < running_balances.pkl > invest_windows.pkl
3. insert (local) < invest_windows.pkl


```sql
SHOW VARIABLES LIKE 'lower_case%';
```


## Venv setup
```sh
rm ./.venv -r -force
python -m venv .venv
echo "" > .\.venv\.nosync
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r ./requirements.txt
.\.venv\Scripts\python.exe -m pip install ipykernel
```