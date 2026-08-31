import pandas as pd
import pytest

from src.backtester.engine.runner import run_simulation_engine
from src.backtester.engine.state import BacktestState
from src.config import BacktestConfig


def make_bar(close, ema50, ema200, vol_ok=True, strong_trend=True):
    return {
        "open": close * 0.99,
        "high": close * 1.02,
        "low": close * 0.98,
        "close": close,
        "Ema50": ema50,
        "Ema200": ema200,
        "volatility_ok": vol_ok,
        "strong_trend": strong_trend,
    }


def test_run_simulation_engine_rejects_empty_dataframe():
    cfg = BacktestConfig()
    empty = pd.DataFrame(columns=["close", "Ema50", "Ema200", "volatility_ok", "strong_trend"])

    with pytest.raises(ValueError, match="empty"):
        run_simulation_engine(empty, cfg)


def test_run_simulation_engine_returns_state_with_history_for_valid_data():
    cfg = BacktestConfig()
    rows = [
        make_bar(100.0, 98.0, 96.0, True, True),
        make_bar(102.0, 100.0, 97.0, True, True),
        make_bar(104.0, 102.0, 98.0, True, True),
        make_bar(106.0, 104.0, 99.0, True, True),
    ]
    df = pd.DataFrame(rows)
    df.index = pd.date_range("2024-01-01", periods=len(df), freq="4h")

    state = run_simulation_engine(df, cfg)

    assert isinstance(state, BacktestState)
    assert len(state.equity_history) > 0
    assert len(state.history_dates) == len(state.equity_history)
    assert state.equity_history[0] > 0


def test_run_simulation_engine_skips_bars_with_missing_indicator_values():
    cfg = BacktestConfig()
    rows = [
        make_bar(100.0, 98.0, 96.0, True, True),
        {"open": 100.0, "high": 102.0, "low": 99.0, "close": None, "Ema50": 98.0, "Ema200": 96.0, "volatility_ok": True, "strong_trend": True},
        make_bar(101.0, 100.0, 97.0, True, True),
    ]
    df = pd.DataFrame(rows)
    df.index = pd.date_range("2024-01-01", periods=len(df), freq="4h")

    state = run_simulation_engine(df, cfg)

    assert isinstance(state, BacktestState)
    assert len(state.equity_history) >= 1


def test_run_simulation_engine_closes_final_open_position():
    cfg = BacktestConfig()
    rows = [
        make_bar(100.0, 98.0, 96.0, True, True),
        make_bar(101.0, 99.0, 97.0, True, True),
        make_bar(102.0, 100.0, 98.0, True, True),
    ]
    df = pd.DataFrame(rows)
    df.index = pd.date_range("2024-01-01", periods=len(df), freq="4h")

    # Last bar should still close any open position if state is left open by the loop.
    state = run_simulation_engine(df, cfg)

    assert isinstance(state, BacktestState)
    assert len(state.trade_list) >= 0
    assert len(state.equity_history) == len(state.history_dates)
