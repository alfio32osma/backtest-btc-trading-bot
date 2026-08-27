import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Tuple

#Configure a dedicated logger for the position module
logger = logging.getLogger(__name__)

class PositionError(Exception):
    #Base exception for all position-related errors
    pass

class InvalidParameterError(PositionError):
    #Raise when an initialization parameter is out of bounds or invalid
    pass

class InvalidPriceError(PositionError):
    #Raise when a price or market value is invalid
    pass

@dataclass
class TradePosition:
    # Create a class to contain and manage the state on open positions
    entry_price: float
    capital_in_trade: float
    leverage: float
    stop_loss_pct: float
    trailing_stop_pct: float
    tp_parcial_pct: float
    entry_date: Any

    #Mutable trade states
    size_actual: float = 1.0
    partial_taken: bool = False
    current_stop: float = field(init=False)

    def __post_init__(self):
        #Safely initializes the initial stop loss based on the entry price
        try:
            if not isinstance(self.entry_price, (int, float)) or not isinstance(self.capital_in_trade, (int, float)):
                raise TypeError("Entry price and capital must be numeric types")

            if self.entry_price <= 0:
                raise InvalidPriceError(f"Entry price must be greater than zero. {self.entry_price}")

            if self.capital_in_trade <= 0:
                raise InvalidParameterError(f"Capital in trade must be greater than zero. {self.capital_in_trade}")

            if self.leverage <= 0:
                raise InvalidParameterError(f"Leverage must be greater than zero. {self.leverage}")

            self.current_stop = self.entry_price * (1 - self.stop_loss_pct)

        except (TypeError, ValueError) as e:
            logger.critical(f"Critical configuration error initializing TradePosition: {e}")
            raise InvalidParameterError(f"Failed to initialize TradePosition: {e}")       

    def update_position(
            self,
            current_close: float,
            ema200: float,
            exit_ema_margin: float,
            fee_rate: float,
            funding_rate_4h: float
        ) -> Dict[str, Any]:

        #Updates the postion state safely. Captures runtime data anomalies
        # without crashing the entire simulation loop or live bot
        default_error_response = {
            'funding_cost': 0.0, 
            'partial_executed': False,
            'net_partial_pnl': 0.0,
            'partial_fee': 0.0,
            'should_close': False,
            'current_return': 0.0,
            'has_error': True
        }
        # Updates the position state on the current candle, calculating
        # funding rate, trailing stop, partial take profits, and exit conditions
        try:
            if not isinstance(current_close, (int, float)) or current_close <= 0:
                raise InvalidPriceError(f"Current close price must be positive number. {current_close}")

            if fee_rate < 0:
                raise InvalidPriceError("Fee rate cannot be negative")
            
            #Calculate and deduct funding cost
            funding_cost = (self.capital_in_trade * self.leverage * self.size_actual) * funding_rate_4h

            #Calculate current return
            current_return = (current_close / self.entry_price) - 1

            #Evaluate partial Take Profit
            partial_executed_now = False
            net_partial_pnl = 0.0
            partial_fee = 0.0

            if not self.partial_taken and current_return >= self.tp_parcial_pct:
                partial_capital = self.capital_in_trade * 0.5
                gross_partial_pnl = partial_capital * (current_return * self.leverage)
                partial_fee = (partial_capital * self.leverage) * fee_rate
                net_partial_pnl = gross_partial_pnl - partial_fee

                self.size_actual = 0.5
                self.partial_taken = True
                self.current_stop = self.entry_price # Breakeven
                partial_executed_now = True

            #Update dynamic trailing stop
            if not partial_executed_now:
                new_trailing_stop = current_close * (1 - self.trailing_stop_pct)
                if new_trailing_stop > self.current_stop:
                    self.current_stop = new_trailing_stop

            #Evaluate exit conditions
            exit_ema_threshold = ema200 * (1 - exit_ema_margin)
            should_close = (current_close < self.current_stop) or (current_close < exit_ema_threshold)

            return {
                'funding_cost': funding_cost,
                'partial_executed': partial_executed_now,
                'net_partial_pnl': net_partial_pnl,
                'partial_fee': partial_fee,
                'should_close': should_close,
                'current_return': current_return,
                'has_error': False
            }
        except (InvalidPriceError, InvalidParameterError) as e:
            logger.error(f"Market data or parameter validation error during update_position: {e}")
            return default_error_response
        except Exception as e:
            logger.exception(f"Unexpected critical error during position update: {e}")
            return default_error_response

    def close_position(self, current_close: float, fee_rate: float) -> Tuple[float, float, float]:
        #Calculated the final net PnL and fees when closing the position
        try:
            if not isinstance(current_close, (int, float)) or current_close <= 0:
                raise InvalidPriceError(f"Closing price must be a positive number. {current_close}")

            if fee_rate < 0:
                raise InvalidParameterError("Fee rate cannot be negative")
            
            remaining_capital = self.capital_in_trade * self.size_actual
            final_return = (current_close / self.entry_price) - 1

            gross_pnl = remaining_capital * (final_return * self.leverage)
            exit_fee = (remaining_capital * self.leverage) * fee_rate
            net_pnl = gross_pnl - exit_fee

            return net_pnl, exit_fee, final_return

        except InvalidPriceError as e:
            logger.error(f"Market error during position closure, returning zero PnL safety fallback: {e}")
            return 0.0, 0.0, 0.0
        except Exception as e:
            logger.exception(f"Unexpected error while closing position: {e}")
            return 0.0, 0.0, 0.0
        