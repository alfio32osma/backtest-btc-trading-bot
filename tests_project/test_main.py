import pandas as pd
import pytest

import main


def test_main_missing_dataset_prints_error(monkeypatch, capsys):
    monkeypatch.setattr(main.os.path, "exists", lambda path: False)

    main.main()

    captured = capsys.readouterr()
    assert "Error Dataset" in captured.out


def test_main_runs_end_to_end_pipeline(monkeypatch, capsys):
    df = pd.DataFrame(
        {
            "open": [100.0, 102.0, 104.0],
            "high": [105.0, 107.0, 109.0],
            "low": [99.0, 101.0, 103.0],
            "close": [101.0, 103.0, 108.0],
        }
    )

    calls = {"plot": None, "metrics": None}
    monkeypatch.setattr(main.os.path, "exists", lambda path: str(path).endswith("btc.csv"))
    monkeypatch.setattr(main, "load_and_clean_data", lambda path: df)
    monkeypatch.setattr(main, "resample_data", lambda cleaned_df, timeframe: df.copy())
    monkeypatch.setattr(
        main,
        "calculate_average_true_range",
        lambda data_frame, period: pd.Series([1.0, 1.2, 1.4], index=data_frame.index),
    )
    monkeypatch.setattr(
        main,
        "calculate_adx",
        lambda data_frame, period: pd.Series([30.0, 35.0, 40.0], index=data_frame.index),
    )

    class DummyState:
        equity = 1100.0
        history_total = [1000.0, 1100.0]
        dates = pd.date_range("2024-01-01", periods=2, freq="1h")
        trade_list = [{"Net Profit €": 10.0}]
        pause_logs = [{"Date": "2024-01-01 00:00:00", "Level": 1}]
        skipped_trades = 0

    monkeypatch.setattr(main, "run_simulation_engine", lambda data_frame, cfg: DummyState())

    monkeypatch.setattr(
        main,
        "calculate_performance_metrics",
        lambda final_state: {
            "df_trades": pd.DataFrame({"Net Profit €": [10.0, -2.0]}),
            "df_pauses": pd.DataFrame({"Date": ["2024-01-01 00:00:00"], "Level": [1]}),
            "history_series": pd.Series([1000.0, 1100.0], index=pd.date_range("2024-01-01", periods=2, freq="1h")),
            "drawdowns": pd.Series([0.0, -0.1], index=pd.date_range("2024-01-01", periods=2, freq="1h")),
            "final_equity": 1100.0,
            "total_return_pct": 10.0,
            "max_drawdown_pct": 10.0,
            "win_rate_pct": 50.0,
            "profit_factor": 5.0,
            "total_trades": 2,
            "sharpe_ratio": 1.0,
            "sortino_ratio": 0.8,
            "pauses_l1": 1,
            "pauses_l2": 0,
            "pauses_l3": 0,
            "total_costs": 10.0,
        },
    )
    monkeypatch.setattr(main, "print_quant_report", lambda metrics, final_state: print("report generated"))

    def fake_plot(metrics, output_filename=None):
        calls["plot"] = output_filename

    monkeypatch.setattr(main, "plot_backtest_results", fake_plot)

    main.main()

    assert calls["plot"] is not None
    assert calls["plot"].endswith("backtest_performance.png")
    assert "Trades report saved to" in capsys.readouterr().out


def test_main_handles_empty_indicators(monkeypatch):
    df = pd.DataFrame({"open": [100.0], "high": [110.0], "low": [90.0], "close": [100.0]})

    monkeypatch.setattr(main.os.path, "exists", lambda path: True)
    monkeypatch.setattr(main, "load_and_clean_data", lambda path: df)
    monkeypatch.setattr(main, "resample_data", lambda cleaned_df, timeframe: df.copy())
    monkeypatch.setattr(main, "calculate_average_true_range", lambda data_frame, period: pd.Series([float("nan")], index=data_frame.index))
    monkeypatch.setattr(main, "calculate_adx", lambda data_frame, period: pd.Series([float("nan")], index=data_frame.index))

    main.main()
    # It should exit gracefully without crashing when the warmed dataframe becomes empty.
