
# Description: Vectorized technical indicators optimized for high-frequency quantitative backtesting.
    
import pandas as pd
import numpy as np 

def calculate_true_range(df: pd.DataFrame) -> pd.Series:
    high = df['high']
    low = df['low']
    close = df['close']

    tr1 = high - low
    tr2 = np.abs(high - close.shift(1))
    tr3 = np.abs(low - close.shift(1))

    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

def calculate_average_true_range(df: pd.DataFrame, period: int = 14) -> pd.Series:
    true_range = calculate_true_range(df)
    return true_range.rolling(window = period).mean()

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:

    required_columns = {'high', 'low', 'close'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise KeyError(f"Missing mandatory columns - ADX: {missing}")
                       
    try: 
        df_local = df.copy()
        high = df_local['high']
        low = df_local['low']

        true_range = calculate_true_range(df_local)

        # Directional Movement (DM)
        plus_dm = high.diff()
        minus_dm = low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        minus_dm = np.abs(minus_dm)

        plus_dm.loc[plus_dm < minus_dm] = 0
        minus_dm.loc[minus_dm < plus_dm.shift(0)] = 0

        #Smoothing and Directional Indicators (DI)
        true_range_smooth = true_range.rolling(window=period).mean()
        safe_true_range_smooth = true_range_smooth.replace(0, np.nan)

        plus_di = 100 * (plus_dm.rolling(window=period).mean() / safe_true_range_smooth)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / safe_true_range_smooth)

        suma_di = plus_di + minus_di
        safe_suma_di = suma_di.replace(0, np.nan)

        dx = 100 * np.abs(plus_di - minus_di) / safe_suma_di
        adx = dx.rolling(window=period).mean()

        return adx

    except Exception as e:
        raise ValueError(f"Execution Error in calculate_adx: {e}")