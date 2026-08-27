import logging
import pandas as pd

logger = logging.getLogger(__name__)

def check_entry_signal(current_bar: pd.Series) -> bool:
    #Evaluates market conditions for a long entry signal based on indictors
    #Handles also edge cases like missing columns, NaN values, or corrupted types
    try:
        #Verify that the required indicator columns exist in the bar/row
        required_keys = ['close', 'Ema200', 'Ema50', 'volatility_ok', 'strong_trend']
        for key in required_keys:
            if key not in current_bar:
                logger.error(f"Missing mandatory column '{key}' in market bard data")
                return False

        if (pd.isna(current_bar['close']) or
            pd.isna(current_bar['Ema200']) or 
            pd.isna(current_bar['Ema50']) or 
            pd.isna(current_bar['volatility_ok']) or 
            pd.isna(current_bar['strong_trend'])):
            return False

        #Strategy entry rules logic
        c_close = float(current_bar['close'])
        ema200  = float(current_bar['Ema200'])
        ema50 = float(current_bar['Ema50'])
        vol_ok = float(current_bar['volatility_ok'])
        adx_ok = bool(current_bar['strong_trend'])

        #Bullish trend alignment and volatility check
        is_uptrend = (c_close > ema200) and (c_close > ema50) and (ema50 > ema200)

        if is_uptrend and vol_ok and adx_ok:
            return True

        return False

    except (ValueError, TypeError) as type_err:
        logger.error(f"Type conversion error while evaluating entry signal: {type_err}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error evaluating entry signnal: {e}")
        return False
