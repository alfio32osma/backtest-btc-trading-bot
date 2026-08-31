import math

import pandas as pd

from src.backtester.engine.metrics import calculate_performance_metrics
from src.backtester.engine.state import BacktestState
from src.config import BacktestConfig


def test_sharpe_and_sortino_use_configured_timeframe():
    dates = pd.date_range("2024-01-01", periods=5, freq="1h")
    history = [1000.0, 1010.0, 1000.0, 1015.0, 1030.0]

    state = BacktestState()
    state.history_total = history
    state.dates = dates
    state.trade_list = []
    state.pause_logs = []

    metrics_4h = calculate_performance_metrics(state, cfg=BacktestConfig(timeframe="4h"))
    metrics_1h = calculate_performance_metrics(state, cfg=BacktestConfig(timeframe="1h"))

    expected_ratio = math.sqrt((365 * 24) / 1.0) / math.sqrt((365 * 24) / 4.0)
    assert metrics_1h["sharpe_ratio"] != metrics_4h["sharpe_ratio"]
    assert abs(metrics_1h["sharpe_ratio"] / metrics_4h["sharpe_ratio"] - expected_ratio) < 1e-6
    assert abs(metrics_1h["sortino_ratio"] / metrics_4h["sortino_ratio"] - expected_ratio) < 1e-6
