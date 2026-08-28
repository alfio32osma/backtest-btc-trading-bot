import logging
import pandas as pd
from typing import Any

logger = logging.getLogger(__name__)

def check_entry_signal(current_bar: Any) -> bool:
    #Evaluates market conditions for a long entry signal based on indictors
    #Handles also edge cases like missing columns, NaN values, or corrupted types
    try:
        def get_val(item: Any, key: str) -> Any:
            if hasattr(item, key):
                return getattr(item, key)

            elif isinstance(item, dict) or hasattr(item, '__getitem__'):
                return item[key]
            raise AttributeError(f"Missing mandatory field '{key}'")
        
        #Verify that the required indicator columns exist in the bar/row
        required_keys = ['close', 'Ema200', 'Ema50', 'volatility_ok', 'strong_trend']
        for key in required_keys:
            val = get_val(current_bar, key)
            if pd.isna(val):
                return False

        #Strategy entry rules logic
        c_close = float(get_val(current_bar, 'close'))
        ema200  = float(get_val(current_bar, 'Ema200'))
        ema50 = float(get_val(current_bar, 'Ema50'))
        vol_ok = bool(get_val(current_bar, 'volatility_ok'))
        adx_ok = bool(get_val(current_bar, 'strong_trend'))

        #Bullish trend alignment and volatility check
        is_uptrend = (c_close > ema200) and (c_close > ema50) and (ema50 > ema200)

        if is_uptrend and vol_ok and adx_ok:
            return True

        return False

    except (ValueError, TypeError) as type_err:
        logger.error(f"Type conversion error while evaluating entry signal: {type_err}")
        return False
    
    except Exception as e:
        logger.error(f"Unexpected error evaluating entry signal: {e}")
        return False
