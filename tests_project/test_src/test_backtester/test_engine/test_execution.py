import pandas as pd

from src.backtester.engine.execution import execute_new_entry, manage_open_position
from src.backtester.engine.state import BacktestState
from src.backtester.position import TradePosition
from src.config import BacktestConfig


def test_execute_new_entry_opens_position_and_deducts_entry_fee():
    cfg = BacktestConfig()
    state = BacktestState(equity=1000.0)
    bar = pd.Series({
        "close": 100.0,
        "Ema200": 95.0,
        "Ema50": 98.0,
    })

    execute_new_entry(bar, "2024-01-01 00:00:00", state, cfg)

    assert state.in_position is True
    assert state.pending_signal is False
    assert state.active_position is not None
    assert state.total_fees_paid > 0
    assert state.equity < 1000.0


def test_execute_new_entry_with_invalid_bar_keeps_state_safe():
    cfg = BacktestConfig()
    state = BacktestState(equity=1000.0, pending_signal=True)

    execute_new_entry(None, "2024-01-01 00:00:00", state, cfg)

    assert state.in_position is False
    assert state.active_position is None
    assert state.pending_signal is False


def test_manage_open_position_closes_when_ema_exit_triggered():
    cfg = BacktestConfig()
    state = BacktestState(equity=1000.0)
    state.in_position = True
    state.active_position = TradePosition(
        entry_price=100.0,
        capital_in_trade=1000.0,
        leverage=2.0,
        stop_loss_pct=0.05,
        trailing_stop_pct=0.05,
        tp_parcial_pct=0.20,
        entry_date="2024-01-01",
    )
    current_bar = pd.Series({
        "close": 90.0,
        "Ema200": 95.0,
    })

    manage_open_position(current_bar, "2024-01-02 00:00:00", state, cfg)

    assert state.in_position is False
    assert state.active_position is None
    assert len(state.trade_list) == 1
    assert state.trade_list[0]["Exit Price"] == 90.0


def test_manage_open_position_handles_partial_take_profit_and_funding():
    cfg = BacktestConfig()
    state = BacktestState(equity=1000.0)
    state.in_position = True
    state.active_position = TradePosition(
        entry_price=100.0,
        capital_in_trade=1000.0,
        leverage=2.0,
        stop_loss_pct=0.05,
        trailing_stop_pct=0.05,
        tp_parcial_pct=0.20,
        entry_date="2024-01-01",
    )
    current_bar = pd.Series({
        "close": 125.0,
        "Ema200": 90.0,
    })

    manage_open_position(current_bar, "2024-01-02 00:00:00", state, cfg)

    assert state.in_position is True
    assert state.active_position.partial_taken is True
    assert state.active_position.size_actual == 0.5
    assert state.active_position.current_stop == 100.0


def test_manage_open_position_ignores_if_state_is_idle():
    cfg = BacktestConfig()
    state = BacktestState(equity=1000.0)
    bar = pd.Series({"close": 120.0, "Ema200": 100.0})

    manage_open_position(bar, "2024-01-01 00:00:00", state, cfg)

    assert state.in_position is False
    assert state.active_position is None
    assert state.trade_list == []
