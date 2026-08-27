
# Description: Vectorized technical indicators optimized for high-frequency quantitative backtesting.
    
import pandas as pd
import numpy as np 

def calculate_true_range(df: pd.DataFrame) -> pd.Series:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")

    required_columns = {'high', 'low', 'close'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise KeyError(f"Missing mandatory columns - True Range: {missing}")

    if df.empty:
        raise ValueError("The provided DataFrame is empty.")
    
    try: 
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = np.abs(high - close.shift(1))
        tr3 = np.abs(low - close.shift(1))

        tr_result = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        if tr_result.empty:
            raise ValueError("Calculated True Range resulted in an empty series.")
        return tr_result
        
    except (KeyError, TypeError, ValueError):
        raise
    
    except Exception as e: 
        raise RuntimeError(f"Unexpected error in calculate_true_range: {e}")

def calculate_average_true_range(df: pd.DataFrame, period: int = 14) -> pd.Series:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")
    if not isinstance(period, int) or period <= 0:
        raise ValueError("Period must be a positive integer.")
    if len(df) < period:
        raise ValueError(f"DataFrame length ({len(df)}) is smaller than the required period {period}")

    try:
        true_range = calculate_true_range(df)
        atr_result = true_range.rolling(window = period).mean()
        return atr_result
    except (KeyError, TypeError, ValueError):
        raise 
    except Exception as e:
        raise RuntimeError(f"Unexpected error in calculate_average_true_range: {e}")

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    # type validation
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")
    if not isinstance(period, int) or period <= 0:
        raise ValueError("Period must be a positive integer.")

    # columns required validation
    required_columns = {'high', 'low', 'close'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise KeyError(f"Missing mandatory columns - ADX: {missing}")

    # Empty DataFrame Validation.
    if df.empty:
        raise ValueError("The provided DataFrame is empty.")
    if len(df) < period:
        raise ValueError(f"Dataframe length ({len(df)}) is smaller than the required period ({period}).")             

    try: 
        df_local = df.copy()
        high = df_local['high']
        low = df_local['low']
    except Exception as e:
        raise KeyError(f"Error accessing price series columns: {e}")
    
    try:
        true_range = calculate_true_range(df_local)

        # step-one | Directional Movement (DM)
        plus_dm = high.diff()
        minus_dm = low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        minus_dm = np.abs(minus_dm)

        plus_dm.loc[plus_dm < minus_dm] = 0
        minus_dm.loc[minus_dm < plus_dm.shift(0)] = 0
    except Exception as e:
        raise RuntimeError(f"Error calculating Directional Movement (DM): {e}")
    
    try:
        # step-two | Smoothing and Directional Indicators (DI)
        true_range_smooth = true_range.rolling(window=period).mean()
        safe_true_range_smooth = true_range_smooth.replace(0, np.nan)

        plus_di = 100 * (plus_dm.rolling(window=period).mean() / safe_true_range_smooth)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / safe_true_range_smooth)

        suma_di = plus_di + minus_di
        safe_suma_di = suma_di.replace(0, np.nan)
    except Exception as e: 
        raise RuntimeError(f"Error during smoothing or DI calculations: {e}")

    try:
        #step-three DX & ADX | end 
        dx = 100 * np.abs(plus_di - minus_di) / safe_suma_di
        adx = dx.rolling(window=period).mean()

        if adx.empty:
            raise ValueError("Calculated ADX resulted in an empty series.")
        return adx    
    except (KeyError, TypeError, ValueError):
        # Let error go through without any modification
        raise 
    except Exception as e:
        # Unexpected ejecution or mathemmatical errors (Pandas | Numpy)
        raise RuntimeError(f"Error computing final DX/ ADX metrics: {e}")