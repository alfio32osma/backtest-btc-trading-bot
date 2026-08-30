import math

import pytest

from src.config import BacktestConfig


@pytest.mark.parametrize(
    "timeframe, expected_hours",
    [
        ("4h", 4.0),
        ("1h", 1.0),
        ("15min", 0.25),
        ("2d", 48.0),
        ("30s", 1 / 120),
    ],
)
def test_timeframe_hours_supports_common_values(timeframe, expected_hours):
    cfg = BacktestConfig(timeframe=timeframe)
    assert cfg.timeframe_hours == pytest.approx(expected_hours)
    assert cfg.periods_per_year == pytest.approx((365.0 * 24.0) / expected_hours)


@pytest.mark.parametrize("timeframe", ["", "abc", "10xyz"])
def test_timeframe_hours_rejects_invalid_values(timeframe):
    cfg = BacktestConfig(timeframe=timeframe)
    with pytest.raises(ValueError, match="Unsupported timeframe|Timeframe cannot be empty"):
        _ = cfg.timeframe_hours


def test_validate_accepts_valid_config():
    cfg = BacktestConfig()
    cfg.validate()


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("ema_fast_period", 0),
        ("ema_slow_period", -10),
        ("losses_level1", 3),
        ("losses_level2", 3),
        ("dd_level1", -0.1),
        ("dd_level3", 1.5),
        ("pause_candles_level3", -1),
    ],
)
def test_validate_rejects_invalid_config(field_name, value):
    cfg = BacktestConfig()
    setattr(cfg, field_name, value)

    with pytest.raises(ValueError):
        cfg.validate()


def test_validate_rejects_non_numeric_drawdown_values():
    cfg = BacktestConfig(dd_level1="bad")
    with pytest.raises(ValueError):
        cfg.validate()


def test_validate_rejects_nan_drawdown_values():
    cfg = BacktestConfig(dd_level1=math.nan)
    with pytest.raises(ValueError):
        cfg.validate()
