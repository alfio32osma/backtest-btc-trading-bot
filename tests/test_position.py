import pytest
from src.backtester.position import TradePosition, InvalidParameterError, InvalidPriceError

def test_position_initialization_success():
    #Verifies that a position initializes correctly with valid parameters
    pos = TradePosition(
        entry_price = 50000.0,
        capital_in_trade = 1000.0,
        leverage = 3.5,
        stop_loss_pct = 0.03,
        trailing_stop_pct = 0.03,
        tp_parcial_pct = 0.25,
        entry_date = "2026-08-01"
    )
    assert pos.entry_price == 50000.0
    assert pos.current_stop == 50000.0 * (1 - 0.03)
    assert pos.size_actual == 1.0
    assert not pos.partial_taken

def test_position_initialization_invalid_price():
    #Ensure initialization fails if the entry price is zero or negative
    with pytest.raises(InvalidPriceError):
        TradePosition(
            entry_price = 0.0,
            capital_in_trade = 1000.0,
            leverage = 3.5,
            stop_loss_pct = 0.03,
            trailing_stop_pct = 0.03,
            tp_parcial_pct = 0.25,
            entry_date = "2026-08-01"
        )

def test_update_position_normal_flow():
    #Verifies regular candle updates, trailing stop adjustments & funding costs
    pos = TradePosition(
        entry_price = 100.0,
        capital_in_trade = 1000.0,
        leverage = 2.0,
        stop_loss_pct = 0.05,
        trailing_stop_pct = 0.04,
        tp_parcial_pct = 0.20,
        entry_date = "2026-08-01"
    )

    #Update with a higher price (should update trailing stop, allow negative funding)
    result = pos.update_position(
        current_close = 110.0,
        ema200 = 90.0,
        exit_ema_margin = 0.01,
        fee_rate = 0.0006,
        funding_rate_4h = -0.0002 #Negative funding test
    )

    assert not result["has_error"]
    assert result["funding_cost"] < 0 #Receiving funds due to negative rate
    assert result["current_return"] == pytest.approx(0.10)
    assert pos.current_stop == 110.0 * (1 - 0.04) #Trailing stop moved  
    assert not result["should_close"]

def test_update_position_parcial_take_profit():
    #Verifies partial take profit execution when reaching the target percentage
    pos = TradePosition(
        entry_price = 100.0,
        capital_in_trade = 1000.0,
        leverage = 2.0,
        stop_loss_pct = 0.05,
        trailing_stop_pct = 0.05,
        tp_parcial_pct = 0.20,
        entry_date = "2026-08-01"
    )

    #Price jumps to +25%, exceeding the 20% partial take profit threshold 
    result = pos.update_position(
        current_close = 125.0,
        ema200 = 90.0,
        exit_ema_margin = 0.01,
        fee_rate = 0.0006,
        funding_rate_4h = 0.0001
    )

    assert not result["has_error"]
    assert result["partial_executed"] is True
    assert pos.partial_taken is True
    assert pos.size_actual == 0.5
    assert pos.current_stop == 100.0 #Stop moved to breakeven

def test_update_position_invalid_market_data_resilience():
    #Ensure the position handles invalid market data gracefully without crashing.
    pos = TradePosition(
        entry_price = 100.0,
        capital_in_trade = 1000.0,
        leverage = 2.0,
        stop_loss_pct = 0.05,
        trailing_stop_pct = 0.05,
        tp_parcial_pct = 0.20,
        entry_date = "2026-08-01"
    )

    #Pass an invalid negative price
    result = pos.update_position(
        current_close = -50.0,
        ema200 = 90.0,
        exit_ema_margin = 0.01,
        fee_rate = 0.0006,
        funding_rate_4h = 0.0001
    )

    #should catch the error internally and return safe default error response 
    assert result["has_error"] is True
    assert result["should_close"] is False

def test_close_position():
    #Verifies final Pnl and fee calculations when closing a position
    pos = TradePosition(
        entry_price = 100.0,
        capital_in_trade = 1000.0,
        leverage = 2.0,
        stop_loss_pct = 0.05,
        trailing_stop_pct = 0.05,
        tp_parcial_pct = 0.20,
        entry_date = "2026-08-01"
    )

    net_pnl, exit_fee, final_return = pos.close_position(current_close = 110.0, fee_rate = 0.0006)

    assert final_return == pytest.approx(0.10)
    assert net_pnl > 0
    assert exit_fee > 0