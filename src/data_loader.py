import os
import pandas as pd

def load_and_clean_data(csv_path: str) -> pd.DataFrame: 
    if not os.path.exists(csv_path):    # handle error path 
        raise FileNotFoundError(f"The file {csv_path} does not exist.")
    
    try:
        df = pd.read_csv(csv_path, sep=None, engine='python', low_memory=False) # search efficient
    except Exception:
        df = pd.read_csv(csv_path, low_memory=False) # if not search pre-defined

    df.columns = [c.lower().strip() for c in df.columns] # cleaning the data lowercase and spaces for each column

    possible_dates = ["timestamp", "date", "datetime", "open time", "time"] #cleaning data  
    col_date = next((c for c in possible_dates if c in df.columns), None) #searching name
    if col_date is None: 
        col_date = df.columns[0] # On financial data the date comes at position 0

    if df[col_date].dtype in ["int64", "float64"]: # handle unitstamps case
        unit = "ms" if df[col_date].iloc[0] > 1e11 else "s" # handling cases seconds/miliseconds
        df["date"] = pd.to_datetime(df[col_date, unit=unit]) #new format of pandas yyyy-mm-dd & hour

    else:
        df["date"] = pd.to_datetime(df[col_date])

    return df