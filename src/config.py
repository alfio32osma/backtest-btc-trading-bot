from dataclasses import dataclass
import math


@dataclass
class BacktestConfig:
    """Centralized configuration container for strategy parameters and risk limits."""
    # Data pipeline settings
    csv_filename: str = "data/btc.csv"
    timeframe: str = "4h"

    # Technical indicator periods and thresholds
    ema_fast_period: int = 50
    ema_slow_period: int = 200
    atr_period: int = 14
    atr_sma_period: int = 14
    adx_period: int = 14
    adx_threshold: float = 31.0

    # Risk Manager - Losses
    # The config validation enforces strict ascending thresholds; the default values
    # are intentionally set to a compact first tier to keep the configuration valid
    # and avoid false positives during validation checks.
    losses_level1: int = 2
    losses_level2: int = 3
    losses_level3: int = 4

    # Risk Manager - Drawdown
    dd_level1: float = 0.15
    dd_level2: float = 0.25
    dd_level3: float = 0.40

    # Risk Manager - Pauses
    pause_candles_level1: int = 3
    pause_candles_level2: int = 12
    pause_candles_level3: int = 30

    # Execution Parameters
    leverage: float = 3.5
    fee_rate: float = 0.0006
    slippage: float = 0.001
    stop_loss_pct: float = 0.03
    trailing_stop_pct: float = 0.03
    tp_parcial_pct: float = 0.247
    funding_rate_4h: float = 0.0001
    exit_ema_margin: float = 0.006

    @property
    def timeframe_hours(self) -> float:
        """Return the candle duration in hours from the configured timeframe."""
        value = str(self.timeframe).strip().lower().replace(" ", "")
        if not value:
            raise ValueError("Timeframe cannot be empty.")

        suffix_map = {
            "weeks": "w",
            "week": "w",
            "days": "d",
            "day": "d",
            "hours": "h",
            "hour": "h",
            "hrs": "h",
            "hr": "h",
            "mins": "m",
            "min": "m",
            "minutes": "m",
            "minute": "m",
            "secs": "s",
            "sec": "s",
            "seconds": "s",
            "second": "s",
        }

        unit = None
        for key, short in suffix_map.items():
            if value.endswith(key):
                unit = short
                value = value[:-len(key)]
                break

        if unit is None and value and value[-1] in {"w", "d", "h", "m", "s"}:
            unit = value[-1]
            value = value[:-1]

        if unit is None:
            raise ValueError(f"Unsupported timeframe '{self.timeframe}'. Use values like '1h', '4h', '15min'.")

        try:
            num = float(value)
        except ValueError as exc:
            raise ValueError(f"Unsupported timeframe '{self.timeframe}'. Use numeric values followed by a unit.") from exc

        if unit == "s":
            return num / 3600.0
        if unit == "m":
            return num / 60.0
        if unit == "h":
            return num
        if unit == "d":
            return num * 24.0
        if unit == "w":
            return num * 168.0
        raise ValueError(f"Unsupported timeframe unit '{unit}' in '{self.timeframe}'.")

    @property
    def periods_per_year(self) -> float:
        """Estimate yearly periods from the configured candle duration."""
        hours = self.timeframe_hours
        if hours <= 0:
            raise ValueError(f"Timeframe must be positive, got '{self.timeframe}'.")
        return (365.0 * 24.0) / hours

    def validate(self) -> None:
        """Validates configuration bounds to avoid invalid state execution."""
        for name, val in [
            ("ema_fast_period", self.ema_fast_period),
            ("ema_slow_period", self.ema_slow_period),
            ("atr_period", self.atr_period),
            ("atr_sma_period", self.atr_sma_period),
            ("adx_period", self.adx_period),
        ]:
            if not isinstance(val, int) or val <= 0:
                raise ValueError(f"Configuration '{name}' must be a positive integer, got: {val}")

        if not (0 <= self.losses_level1 < self.losses_level2 < self.losses_level3):
            raise ValueError(
                f"Loss levels must follow ascending order (Level1 < Level2 < Level3). "
                f"Got: {self.losses_level1}, {self.losses_level2}, {self.losses_level3}"
            )

        if self.losses_level2 == self.losses_level3:
            raise ValueError(
                f"Loss levels must be strictly increasing; got {self.losses_level1}, {self.losses_level2}, {self.losses_level3}."
            )

        for name, val in [
            ("dd_level1", self.dd_level1),
            ("dd_level2", self.dd_level2),
            ("dd_level3", self.dd_level3),
        ]:
            if not isinstance(val, (int, float)) or math.isnan(val) or not (0.0 <= val <= 1.0):
                raise ValueError(f"Drawdown threshold '{name}' must be a float between 0.0 and 1.0, got: {val}")

        if not (self.dd_level1 < self.dd_level2 < self.dd_level3):
            raise ValueError(
                f"Drawdown thresholds must follow ascending order. "
                f"Got: {self.dd_level1}, {self.dd_level2}, {self.dd_level3}"
            )

        for name, val in [
            ("pause_candles_level1", self.pause_candles_level1),
            ("pause_candles_level2", self.pause_candles_level2),
            ("pause_candles_level3", self.pause_candles_level3),
        ]:
            if not isinstance(val, int) or val < 0:
                raise ValueError(f"Pause candles parameter '{name}' must be a non-negative integer, got: {val}")

        self.timeframe_hours
        self.periods_per_year
