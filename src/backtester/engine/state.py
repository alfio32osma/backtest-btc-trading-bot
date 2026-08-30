import logging
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Union, Any, Dict

logger = logging.getLogger(__name__)

@dataclass
class BacktestState:
    #capital tracking
    equity: float = 1000.0
    equity_peak: float = 1000.0
    total_fees_paid: float = 0.0
    total_funding_paid: float = 0.0

    #position tracking
    in_position: bool = False
    pending_signal: bool = False
    active_position: Optional[Any] = None

    #protection system tracking
    consecutive_losses: int = 0
    pause_candles: int = 0
    active_level: int = 0
    skipped_trades: int = 0

    #data arrays & pre-allocated vector buffers
    pause_logs: List[Dict[str, Any]] = field(default_factory=list)
    equity_history: Union[List[float], np.ndarray] = field(default_factory=list)
    history_dates: Union[List[Any], np.ndarray] = field(default_factory=list)
    trade_list: List[Dict[str, Any]] = field(default_factory=list)

    # Backward-compatible aliases kept for older code/tests while the new names
    # remain the canonical attribute names in the backtest state.
    @property
    def history_total(self):
        return self.equity_history

    @history_total.setter
    def history_total(self, value):
        self.equity_history = value

    @property
    def dates(self):
        return self.history_dates

    @dates.setter
    def dates(self, value):
        self.history_dates = value

    #indexing cursor for numpy buffer pre-allocation
    _cursor: int = 0
    _is_preallocated: bool = False

    def prepare_buffers(self, total_bars: int) -> None:
        try:
            if total_bars <= 0:
                raise ValueError(f"Invalid total_bars: {total_bars}")
            
            self.equity_history = np.zeros(total_bars, dtype=np.float64)
            self.history_dates = np.empty(total_bars, dtype=object)
            self._cursor = 0
            self._is_preallocated = True

        except Exception as e:
            logger.error(f"Failed to pre-allocate memory buffers: {e}")
            self._is_preallocated = False

    def record_history(self, current_date: Any) -> None:
        #trims records equity and timestamp into state history using O(1) buffer indexing
        try:
            if current_date is None:
                raise ValueError("Can't record history for a None type date")

            if self._is_preallocated:
                if self._cursor < len(self.equity_history):
                    self.equity_history[self._cursor] = self.equity
                    self.history_dates[self._cursor] = current_date
                    self._cursor += 1
                else:
                    logger.warning("Pre-allocated buffer overflow. Falling back to append")
                    if isinstance(self.equity_history, np.ndarray):
                        self.equity_history = self.equity_history.tolist()
                        self.history_dates = self.history_dates.tolist()
                    self.equity_history.append(self.equity)
                    self.history_dates.append(current_date)
            else:
                if isinstance(self.equity_history, list):
                    self.equity_history.append(self.equity)
                    self.history_dates.append(current_date)
                else:
                    self.equity_history = list(self.equity_history) + [self.equity]
                    self.history_dates = list(self.history_dates) + [current_date]

        except Exception as e: 
            logger.error(f"Failed to record history at {current_date}: {e}")

    def finalize_buffers(self) -> None:
        #trims unused pre-allocated buffer elements to guarantee clean array lengths
        try:
            if self._is_preallocated:
                if isinstance(self.equity_history, np.ndarray):
                    self.equity_history = self.equity_history[:self._cursor]

                if isinstance(self.history_dates, np.ndarray):
                    self.history_dates = self.history_dates[:self._cursor]

        except Exception as e:
            logger.error(f"Error finalizing state buffers: {e}")

    def activate_pause(self, level: int, candles: int, date: Any, drawdown: float) -> None:
        # Registers a protection pause and validates the inputs
        try:
            if level <= 0 or candles < 0:
                raise ValueError(f"Invalid pause parameters: level {level}")

            self.active_level = level
            self.pause_candles = candles
            self.pause_logs.append({
                'Date': date,
                'Level': self.active_level,
                'Consecutive Losses': self.consecutive_losses,
                'Drawdown %': round(drawdown * 100, 2),
                'Pause Candles': self.pause_candles
            })
            logger.info(f"Protection level {level} activated at {date} for {candles} candles")

        except Exception as e:
            logger.error(f"Error activating pause system: {e}")

    def check_bankruptcy(self) -> bool:
        #Critical cases check to stop trading if capital is depleted
        try:
            if self.equity <= 0:
                logger.critical(f"Bankruptcy detected: equity dropped to {self.equity}. Halting operations")
                return True
            return False
        
        except TypeError:
            logger.error("Equity calculation error: Non-numeric value detected")
            return True