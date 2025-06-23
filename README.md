This is the V2 of the windows algo that has been vastly simplied. V1 is looking at all the windows checking sorted balances (a lot more complex).

This version is missing the first days. Refer to:
		https://rtachicago.sharepoint.com/sites/TreasuryForecastAppDev-FIT/_layouts/Doc.aspx?sourcedoc={28290799-5FFD-4510-B425-FD0C3C573921}&wd=target%28Reporting.one%7C4FB27D2B-D94B-403E-88C4-489FB087F2B4%2FAlgo%20v1%7C626A579A-929B-46DD-BB2D-6A1523B24BF5%2F%29&wdpartid={46CED967-0DF4-463B-A1D5-AFBBF8F2CFD6}{1}&wdsectionfileid={844DCBAD-8387-4E65-AA4C-508D641726D9}
onenote:https://rtachicago.sharepoint.com/sites/TreasuryForecastAppDev-FIT/SiteAssets/Treasury%20Forecast%20App%20Dev%20-%20FIT%20Notebook/Reporting.one#Algo%20v1&section-id={4FB27D2B-D94B-403E-88C4-489FB087F2B4}&page-id={626A579A-929B-46DD-BB2D-6A1523B24BF5}&end


## Notebooks execution order (temp data storing in pkl files)
1. algo.ipynb
       first spike - don't use (kept just for reference)

2. windows.ipynb
       windows (prod) -> running_balances.pkl
              rebuild of the daily asset balances table -the df is saved into a .pkl file(s): running_balances.pkl

3. algo2.ipynb
       algo2 <- running_balances.pkl -> invest_windows.pkl
              process finding low points from the end with visual (needs the forward look by day)
                     NOTE: This is the dev reposityry with the algo code put into *_processor files that have then been later added to the Azure function project that is used for deployment.

4. Write the results back into the database
       insert (local) <- invest_windows.pkl


## Path(s)
C:\Users\Adam.Skrzypulec\OneDrive - RTA\www\Treasury Forecasting v2

## Install the dependencies (without using an virtual env)
pip install pandas
pip install mysql-connector-python
pip install python-dotenv


## SQL views issue due to MySQL Azure setup
Azure stores all the objects in lowe-case due to:
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