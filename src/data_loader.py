import os
import pandas as pd

def load_and_clean_data(csv_path: str) -> pd.DataFrame: 
    if not os.path.exists(csv_path):    # handle error path 
        raise FileNotFoundError(f"The file {csv_path} does not exist.")  
  
    df = pd.read_csv(csv_path, sep=None, engine='python') # if not search pre-defined

    df.columns = [c.lower().strip().replace("<", "").replace(">", "") for c in df.columns] # cleaning the data lowercase and spaces for each column

    if "date" in df.columns and "time" in df.columns:
        try:
            date_str = df["date"].astype(str).str.replace(".", "-", regex=False)
            time_str = df["time"].astype(str)
            df["date"] = pd.to_datetime(date_str + " " + time_str, format="%Y-%m-%d %H:%M:%S")
            df = df.drop(columns=["time"])

        except Exception as e: 
            raise ValueError(f"Critical error trying to join 'date' and 'time': {e} ")

    else:
        possible_dates = ["timestamp", "date", "datetime", "open time", "time"] #cleaning data  
        col_date = next((c for c in possible_dates if c in df.columns), None) #searching name and on financial data the date comes at position 0

        if col_date is None:
            col_date = df.columns[0]

        try:
            #Create the column "date" using col_date while still exists
            if df[col_date].dtype == object:
                df["date"] = pd.to_datetime(
                    df[col_date].astype(str).str.replace(".", "-", regex=False)
                )

            elif df[col_date].dtype in ["int64", "float64"]: # handle unitstamps case
                unit = "ms" if df[col_date].iloc[0] > 1e11 else "s" # handling cases seconds/miliseconds
                raw_dates = df[col_date]
                df["date"] = pd.to_datetime(raw_dates, unit=unit)  #new format of pandas yyyy-mm-dd & hour
                
            else:
                df["date"] = pd.to_datetime(df[col_date])

            #after create with success "date", if the original column was different, then is delete it 
            if col_date != "date" and col_date in df.columns:
                    df = df.drop(columns=[col_date])
            
        except Exception as e: 
            raise ValueError(F"Critical error on column date {col_date}: {e}")

    return df

def resample_data(df: pd.DataFrame, timeframe: str = "4h") -> pd.DataFrame:  # take the clean Data Frame, and aggregate it to the desired timeframe, I used 4h as default value.
    col_open = next((c for c in ["open", "start"] if c in df.columns), None) 
    col_close = next((c for c in ["close", "last", "price"] if c in df.columns), None)
    col_high = next((c for c in ["high", "max"] if c in df.columns), None)
    col_low = next((c for c in ["low", "min"] if c in df.columns), None)

    if not all([col_open, col_close, col_high, col_low]):
        raise ValueError("Error loading data Open, High, Low, Close") # we manage the error if any column is not founded

    # region
    # Fix resample window alignment: origin="start" prevents Pandas 
    # from anchoring to default UTC 00:00, ensuring 4h periods start 
    # from the dataset's actual first timestamp (240-min intervals).
    # endregion
    df_resampled = (

        df.set_index("date")
        .resample(timeframe, origin="start")
        .agg({
            col_open: "first",
            col_high: "max",
            col_low: "min",      # Using .agg we calculate on the dataframe the values the we need to create a new candle
            col_close: "last"
            })             
        .dropna() # clean empty spaces and values.
    )

    df_resampled.columns = ["open", "high", "low", "close"] # we rename the columns this should be in order to .agg otherwise we can rename the higher price as the open.
    return df_resampled

# Al final de todo en data_loader.py puedes añadir esto para pruebas:
if __name__ == "__main__":
    # 1. Visualización preliminar de los datos en bruto tal como vienen en el CSV
    print("=== 1. DATOS CRUDOS (ANTES DE CARGAR) ===")
    df_raw = pd.read_csv("../btc.csv", sep=None, engine='python', nrows=5)
    print(df_raw.head())
    print("-" * 50)

    # 2. Comprobación de la limpieza, estandarización de columnas y fusión temporal
    print("=== 2. DATOS LIMPIOS (DESPUÉS DE load_and_clean_data) ===")
    df_clean = load_and_clean_data("../btc.csv")
    print("Columnas:", df_clean.columns)
    print(df_clean.head())
    print("-" * 50)

    # 3. Verificación del remuestreo de velas a alta temporalidad (4 horas)
    print("=== 3. DATOS REMUESTREADOS (DESPUÉS DE resample_data a 4H) ===")
    df_resampled = resample_data(df_clean, timeframe="4h")
    print("Columnas remuestreadas:", df_resampled.columns)
    print(df_resampled.head(10))