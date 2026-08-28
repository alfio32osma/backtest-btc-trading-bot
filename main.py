import logging
import sys
import os
import pandas as pd

#Sys path if necessary
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.data_loader import load_and_clean_data, resample_data
from src.indicators import calculate_adx, calculate_average_true_range
from src.backtester.risk_manager import evaluate_protection_system
from src.backtester.engine.runner import run_simulation_engine
from src.backtester.engine.metrics import calculate_performance_metrics, print_quant_report
from src.backtester.engine.plotting import plot_backtest_results

#configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main() -> None:
    #Main execution pipeline for the algorithmic trading backtester.
    #Loads data, computes indicators, runs execution engine, generates metrics
    #Exports CSV reports, and plots performance charts.
    csv_path = "btc.csv"

    logger.info("Starting algorithmic trading backtest...")

    try:
        if not os.path.exists(csv_path):
            logger.error(f"Dataset not found at '{csv_path}'. Please ensure that the file.csv is in the root directory")
            print(f"Error Dataset: '{csv_path}' not found, Please provide the historical CSV file")
            return
        
        # Load and clean raw data
        logger.info(f"Loading and cleaning data from {csv_path}...")
        df_clean = load_and_clean_data(csv_path)

        # Resample to 4h candles
        logger.info("Resampling dataset to 4h timeframe...")
        df_h = resample_data(df_clean, timeframe="4h")

        # Compute technical indicators
        logger.info("Computing technical indicators (EMA, ATR, ADX)...")
        df_h['Ema50'] = df_h['close'].ewm(span=50, adjust=False).mean()
        df_h['Ema200'] = df_h['close'].ewm(span=200, adjust=False).mean()

        # Volatility and trend conditions
        atr = calculate_average_true_range(df_h, period=14)
        atr_sma = atr.rolling(window=14).mean()
        df_h['volatility_ok'] = atr >= atr_sma

        adx = calculate_adx(df_h, period=14)
        df_h['strong_trend'] = adx > 25

        # Drop NaN rows from indicator warm-up periods
        df_h = df_h.dropna()

        if df_h.empty:
            logger.error("DataFrame is empty after indicator calculation and warm-up drop")
            return

        # Run core simulation engine
        logger.info(f"Running simulation engine over {len(df_h)} bars...")
        final_state = run_simulation_engine(df_h)

        # Calculate metrics
        logger.info("Calculating performance metrics...")
        metrics = calculate_performance_metrics(final_state)

        # Export CSV reports
        output_trades_csv = "protected_trades_report.csv"
        output_pauses_csv = "activated_pauses_report.csv"

        df_trades = metrics.get("df_trades")
        if df_trades is not None and not df_trades.empty:
            df_trades.to_csv(output_trades_csv, index=False)
            logger.info(f"Trades report saved to '{output_trades_csv}'")
            print(f"Trades report saved to: '{output_trades_csv}'")

        df_pauses = metrics.get("df_pauses")
        if df_pauses is not None and not df_pauses.empty:
            df_pauses.to_csv(output_pauses_csv, index=False)
            logger.info(f"Pauses report saved to '{output_pauses_csv}'")
            print(f"Pauses report saved to: '{output_pauses_csv}'")

        # Print report
        print_quant_report(metrics, final_state)

        # Plot performance charts
        logger.info("Generating performance plots...")
        plot_backtest_results(metrics, output_filename="backtest_performance.png")

        logger.info("Backtest execution completed succesfully")

    except Exception as e:
        logger.exception(f"Critical error in main backtest: {e}")
        sys.exit(1)

if __name__ == "__main__":
     main()