import pandas as pd
import pytest

from src.backtester.engine.state import BacktestState


def test_prepare_buffers_and_record_history_work_with_preallocation():
    state = BacktestState()
    state.prepare_buffers(total_bars=3)

    state.equity = 1000.0
    state.record_history("2024-01-01 00:00:00")
    state.equity = 1100.0
    state.record_history("2024-01-01 04:00:00")
    state.equity = 1200.0
    state.record_history("2024-01-01 08:00:00")
    state.finalize_buffers()

    assert len(state.equity_history) == 3
    assert len(state.history_dates) == 3
    assert state.equity_history[0] == 1000.0
    recorded_value = state.history_dates[2]
    assert pd.to_datetime(recorded_value).strftime("%Y-%m-%d %H:%M:%S") == "2024-01-01 08:00:00"


def test_record_history_with_none_date_is_ignored_without_crashing(caplog):
    state = BacktestState()

    state.record_history(None)

    assert state.equity_history == []
    assert state.history_dates == []


def test_prepare_buffers_rejects_invalid_size():
    state = BacktestState()

    state.prepare_buffers(total_bars=0)

    assert state._is_preallocated is False


def test_activate_pause_validates_bad_parameters():
    state = BacktestState()

    state.activate_pause(level=0, candles=2, date="2024-01-01", drawdown=-0.10)
    state.activate_pause(level=2, candles=-1, date="2024-01-01", drawdown=-0.10)

    assert state.pause_logs == []


def test_check_bankruptcy_detects_negative_or_zero_equity():
    state = BacktestState(equity=0.0)
    assert state.check_bankruptcy() is True

    state.equity = 50.0
    assert state.check_bankruptcy() is False


def test_legacy_aliases_remain_compatible():
    state = BacktestState()
    state.equity_history = [1000.0, 1100.0]
    state.history_dates = pd.to_datetime(["2024-01-01", "2024-01-02"])

    assert state.history_total == [1000.0, 1100.0]
    assert list(state.dates) == list(pd.to_datetime(["2024-01-01", "2024-01-02"]))

    state.history_total = [900.0, 950.0]
    assert state.equity_history == [900.0, 950.0]
