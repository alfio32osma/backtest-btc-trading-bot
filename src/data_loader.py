import os
import pandas as pd

def load_and_clean_data(csv_path: str) -> pd.DataFrame: 
    if not os.path.exists(csv_path):    # handle error path 
        raise FileNotFoundError(f"The file {csv_path} does not exist.")  
  
    df = pd.read_csv(csv_path, low_memory=False) # if not search pre-defined

    df.columns = [c.lower().strip().replace("<", "").replace(">", "") for c in df.columns] # cleaning the data lowercase and spaces for each column

    if "date" in df.columns and "time" in df.columns:
        date_str = df["date"].astype(str).str.replace(".", "-", regex=False)
        time_str = df["time"].astype(str)
        df["date"] = pd.to_datetime(date_str + " " + time_str)

    else:
        possible_dates = ["timestamp", "date", "datetime", "open time", "time"] #cleaning data  
        col_date = next((c for c in possible_dates if c in df.columns), None) #searching name
        
        if col_date is None: 
            col_date = df.columns[0] # On financial data the date comes at position 0

        if df[col_date].dtype in ["int64", "float64"]: # handle unitstamps case
            unit = "ms" if df[col_date].iloc[0] > 1e11 else "s" # handling cases seconds/miliseconds
            raw_dates = df[col_date]
            df["date"] = pd.to_datetime(raw_dates, unit=unit)  #new format of pandas yyyy-mm-dd & hour

        else:
            df["date"] = pd.to_datetime(df[col_date])

    return df

def resample_data(df: pd.DataFrame, timeframe: str = "4h") -> pd.DataFrame:  # take the clean Data Frame, and aggregate it to the desired timeframe, I used 4h as default value.
    col_open = next((c for c in ["open", "start"] if c in df.dataframe), None) 
    col_close = next((c for c in ["close", "last", "price"] if c in df.columns), None)
    col_high = next((c for c in ["high", "max"] if c in df.columns), None)
    col_low = next((c for c in ["low", "min"] if c in df.columns), None)

    if not all([col_open, col_close, col_high, col_low]):
        raise ValueError("Error loading data Open, High, Low, Close") # we manage the error if any column is not founded
    
    df_resampled = (
        df.resample(timeframe, on="date")
        .agg({col_open: "first", col_close: "last", col_high: "max", col_low: "low"}) # Using .agg we calculate on the dataframe the values the we need to create a new candle
        .dropna() # clean empty spaces and values.
    )

    df_resampled.columns = ["open", "close", "high", "low"] # we rename the columns this should be in order to .agg otherwise we can rename the higher price as the open.
    return df_resampled

# Al final de todo en data_loader.py puedes añadir esto para pruebas:
if __name__ == "__main__":
    # Asegúrate de poner la ruta correcta al CSV (por ejemplo "../btc.csv" si estás dentro de src)
    df_test = load_and_clean_data("../btc.csv")
    print("Columnas limpias:", df_test.columns)
    print(df_test.head())