import matplotlib

matplotlib.use("Agg")
import pandas as pd

from src.backtester.engine.plotting import plot_backtest_results


def test_plot_backtest_results_creates_png_file(tmp_path):
    idx = pd.date_range("2024-01-01", periods=3, freq="1h")
    metrics = {
        "history_series": pd.Series([1000.0, 1050.0, 1100.0], index=idx),
        "drawdowns": pd.Series([0.0, -0.05, -0.02], index=idx),
        "df_pauses": pd.DataFrame({
            "Date": pd.to_datetime(["2024-01-01 00:00:00", "2024-01-01 02:00:00"]),
            "Level": [1, 2],
        }),
    }

    output = tmp_path / "plot.png"
    plot_backtest_results(metrics, output_filename=str(output))

    assert output.exists()
    assert output.stat().st_size > 0


def test_plot_backtest_results_handles_empty_history():
    metrics = {
        "history_series": pd.Series(dtype=float),
        "drawdowns": pd.Series(dtype=float),
        "df_pauses": pd.DataFrame(columns=["Date", "Level"]),
    }

    plot_backtest_results(metrics)


def test_plot_backtest_results_handles_timezone_aware_index(tmp_path):
    idx = pd.date_range("2024-01-01", periods=2, freq="1h", tz="UTC")
    metrics = {
        "history_series": pd.Series([1000.0, 980.0], index=idx),
        "drawdowns": pd.Series([0.0, -0.02], index=idx),
        "df_pauses": pd.DataFrame({
            "Date": pd.to_datetime(["2024-01-01 00:00:00", "2024-01-01 01:00:00"], utc=True),
            "Level": [1, 3],
        }),
    }

    output = tmp_path / "tz_plot.png"
    plot_backtest_results(metrics, output_filename=str(output))

    assert output.exists()
