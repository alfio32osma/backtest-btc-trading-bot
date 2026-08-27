import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

@dataclass
class BacktestState:
    # Centralized container for all mutable variables during the backtest
    # Handles data validation and critical edge cases to prevent silent failures

    # Capital tracking
    equity: float = 1000.0
    equity_peak: float = 1000.0
    total_fees_paid: float = 0.0
    total_funding_paid: float = 0.0

    # Position tracking
    in_position: bool = False
    pending_signal: bool = False
    active_position: Optional[Any] = None

    # Protection system tracking
    consecutive_losses: int = 0
    pause_candles: int = 0
    active_level: int = 0
    skipped_trades: int = 0

    # Data arrays - Using default_factory to prevent shared refereces
    pause_logs: List[Dict[str, Any]] = field(default_factory= list)
    history_total: List[float] = field(default_factory= list)
    dates: List[Any] = field(default_factory= list)
    trade_list: List[Dict[str, Any]] = field(default_factory= list)

    def record_history(self, current_date: Any) -> None:
        #Appends the current equity to the history array safely
        try:
            if current_date is None:
                raise ValueError("Can't record history for a None type date")

            self.history_total.append(self.equity)
            self.dates.append(current_date)

        except Exception as e:
            logger.error(f"Failed to record history at {current_date}: {e}")

    def activate_pause(self, level: int, candles: int, date: Any, drawdown: float) -> None:
        # Registers a protection pause and validates the inputs
        try:
            if level <= 0 or candles < 0:
                raise ValueError(f"Invalid pause parameters: level = {level}")

            self.active_level = level
            self.pause_candles = candles
            self.pause_logs.append({
                'Date': date,
                'Level': self.active_level,
                'Consecutive Losses': self.consecutive_losses,
                'Drawdown %': round(drawdown * 100, 2),
                'Pause Candles': self.pause_candles
            })
            logger.info(f"Protection Level {level} activate at {date} for {candles} candles")

        except Exception as e:
            logger.error(f"Error activating pause system: {e}")

    def check_bankruptcy(self) -> bool:
        #Critical edge-case check to stop trading if capital is depleted
        try:
            if self.equity <= 0:
                logger.critical(f"BANKRUPTCY DETECTED: Equity dropped to {self.equity}. Halting operations.")
                return True
            return False
        except TypeError:
            logger.error("Equity calculation error: Non-numeric value detected")
            return True