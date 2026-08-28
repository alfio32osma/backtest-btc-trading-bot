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
    history_total: Union[List[float], np.ndarray] = field(default_factory=list)
    dates: Union[List[Any], np.ndarray] = field(default_factory=list)
    trade_list: List[Dict[str, Any]] = field(default_factory=list)

    #indexing cursor for numpy buffer pre-allocation
    _cursor: int = 0
    _is_preallocated: bool = False

    def prepare_buffers(self, total_bars: int) -> None:
        try:
            if total_bars <= 0:
                raise ValueError(f"Invalid total_bars: {total_bars}")
            
            self.history_total = np.zeros(total_bars, dtype=np.float64)
            self.dates = np.empty(total_bars, dtype=object)
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
                if self._cursor < len(self.history_total):
                    self.history_total[self._cursor] = self.equity
                    self.dates[self._cursor] = current_date
                    self._cursor += 1
                else:
                    logger.warning("Pre-allocated buffer overflow. Falling back to append")
                    if isinstance(self.history_total, np.ndarray):
                        self.history_total = self.history_total.tolist()
                        self.dates = self.dates.tolist()
                    self.history_total.append(self.equity)
                    self.dates.append(current_date)
            else:
                if isinstance(self.history_total, list):
                    self.history_total.append(self.equity)
                    self.dates.append(current_date)
                else:
                    self.history_total = list(self.history_total) + [self.equity]
                    self.dates = list(self.dates) + [current_date]

        except Exception as e: 
            logger.error(f"Failed to record history at {current_date}: {e}")

    def finalize_buffers(self) -> None:
        #trims unused pre-allocated buffer elements to guarantee clean array lengths
        try:
            if self._is_preallocated:
                if isinstance(self.history_total, np.ndarray):
                    self.history_total = self.history_total[:self._cursor]

                if isinstance(self.dates, np.ndarray):
                    self.dates = self.dates[:self._cursor]

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