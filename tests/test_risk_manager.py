import pytest
from src.backtester.risk_manager import evaluate_protection_system

def test_normal_opertation_no_risk():
    #test standard with no losses and no drawdown
    level, pause_candle, drawdown = evaluate_protection_system(
        balance_bot=1000.0, balance_peak=1000.0, consecutive_losses=0
    )
    assert level == 0
    assert pause_candle == 0
    assert drawdown == 0.0

def test_drawndown_exceeds_peak():
    #testing behavior when the current balance exceeds the historical peak (clambing DD to 0).
    level, pause_candle, drawdown = evaluate_protection_system(
        balance_bot=1100.0, balance_peak=1000.0, consecutive_losses=0
    )
    assert level == 0
    assert pause_candle == 0
    assert drawdown == 0.0

@pytest.mark.parametrize(
    #losses, expected_level, expected_candles",
    [
        (1, 0, 0), #Below level 1 threshold
        (2, 1, 3), #Exactly level 1 losses
        (3, 2, 12), #Exactly level 2 losses
        (4, 3, 30), #Level 3 losses or higher
        (10, 3, 30), #Extreme losses streak
    ]
)
def test_consecutive_losses_thresholds(losses, expected_level, excpected_candles):
    level, pause_candles, drawdown = evaluate_protection_system(
        balance_boy=1000.0, balance_peak=1000.0, consecutive_losses=losses
    )
    assert level == expected_level
    assert pause_candles == excpected_candles

@pytest.mark.parametrize(
    #Bot_balance, peak_balance, expected_level, expected_drawdown_approx
    [
        (850.0, 1000.0, 1, -0.15), #Exactly level 1 DD (-15%)
        (750.0, 1000.0, 2, -0.25) #Exactly level 2 DD (-25%)
        (600.0, 1000.0, 3 -0.40), #Exactly level 3 DD (-40%)
        (500.0, 1000.0, 3, -0.50) #Severe drawdown (-50%)
    ],
)
def test_combined_highest_trigger():
    #Test when losses and drawdown indicates different levels, taking the max
    #Losses = 3(level 3 -> 12 candles) but DD = -40%(level 3 -> 30 candles)
    level, pause_candles, drawdown = evaluate_protection_system(
        balance_bot=600.0, balance_peak=1000.0, consecutive_losses=3
    )
    assert level == 3
    assert pause_candles == 30
    assert drawdown == -0.40

def test_invalid_type_raise_type_error():
    #Test that passing non-numeric or incorrect types to raises TypeError
    with pytest.raises(TypeError):
        evaluate_protection_system(balance_bot="1000", balance_peak=1000.0, consecutive_losses=0)

    with pytest.raises(TypeError):
        evaluate_protection_system(balance_bot=1000.0, balance_peak=1000.0, consecutive_losses="0")

def test_invalid_values_raise_value_error():
    #Test invalid values such as: negative consecutive lossesm raise ValueError
    with pytest.raises(ValueError):
        evaluate_protection_system(balance_bot=1000.0, balance_peak=1000.0, consecutive_losses=-1)

def test_zero_or_negative_peak_handling():
    #Test safety handling when peak balance is zero or negative
    #Handle peak <= 0 safely using safe_peak fallback without crashing
    level, pause_candles, drawdown = evaluate_protection_system(
        balance_bot=500.0, balance_peak=0.0, consecutive_losses=0
    )
    assert isinstance(level, int)
    assert isinstance(pause_candles, int)
    assert isinstance(drawdown, float)
    