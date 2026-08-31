import math

import pandas as pd
import pytest

from src.backtester.engine.strategy import check_entry_signal


def test_check_entry_signal_returns_true_for_valid_bullish_setup():
    bar = pd.Series({
        "close": 110.0,
        "Ema200": 100.0,
        "Ema50": 105.0,
        "volatility_ok": True,
        "strong_trend": True,
    })

    assert check_entry_signal(bar) is True


def test_check_entry_signal_returns_false_when_data_is_nan():
    bar = pd.Series({
        "close": float("nan"),
        "Ema200": 100.0,
        "Ema50": 105.0,
        "volatility_ok": True,
        "strong_trend": True,
    })

    assert check_entry_signal(bar) is False


def test_check_entry_signal_returns_false_when_required_field_missing():
    bar = {"close": 110.0, "Ema200": 100.0, "Ema50": 105.0, "strong_trend": True}

    assert check_entry_signal(bar) is False


def test_check_entry_signal_handles_dict_like_input():
    bar = {
        "close": 120.0,
        "Ema200": 100.0,
        "Ema50": 110.0,
        "volatility_ok": True,
        "strong_trend": True,
    }

    assert check_entry_signal(bar) is True


def test_check_entry_signal_false_when_uptrend_is_missing():
    bar = pd.Series({
        "close": 99.0,
        "Ema200": 100.0,
        "Ema50": 105.0,
        "volatility_ok": True,
        "strong_trend": True,
    })

    assert check_entry_signal(bar) is False


def test_check_entry_signal_handles_non_numeric_string_values():
    bar = pd.Series({
        "close": "bad",
        "Ema200": 100.0,
        "Ema50": 105.0,
        "volatility_ok": True,
        "strong_trend": True,
    })

    assert check_entry_signal(bar) is False
