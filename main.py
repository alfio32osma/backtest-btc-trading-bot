import logging
import sys
import os

#Sys path if necessary
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.config import BacktestConfig
from src.data_loader import load_and_clean_data, resample_data

from src.indicators import calculate_adx, calculate_average_true_range
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
    cfg = BacktestConfig()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, cfg.csv_filename)

    logger.info("Starting algorithmic trading backtest...")

    try:
        if not os.path.exists(csv_path):
            logger.error(f"Dataset not found at '{csv_path}'. Please ensure that the file.csv is in the root directory")
            print(f"Error Dataset: '{csv_path}' not found, Please provide the historical CSV file")
            return
        
        # Load and clean raw data
        logger.info(f"Loading and cleaning data from {csv_path}...")
        df_clean = load_and_clean_data(csv_path)

        # Resample to configured timeframe
        logger.info(f"Resampling dataset to {cfg.timeframe} timeframe...")
        df_h = resample_data(df_clean, timeframe=cfg.timeframe)
        print(f"Primera vela: {df_h.index[0]}")
        print(f"Segunda vela: {df_h.index[1]}")
        print(f"Diferencia: {df_h.index[1] - df_h.index[0]}")

        # Compute technical indicators
        logger.info(f"Computing technical indicators (EMA, ATR, ADX)...")
        df_h['Ema50'] = df_h['close'].ewm(span=cfg.ema_fast_period, adjust=False).mean()
        df_h['Ema200'] = df_h['close'].ewm(span=cfg.ema_slow_period, adjust=False).mean()

        # Volatility and trend conditions
        atr = calculate_average_true_range(df_h, period=cfg.atr_period)
        df_h['volatility_ok'] = atr < (df_h['close'] * 0.02)

        adx = calculate_adx(df_h, period=cfg.adx_period)
        df_h['strong_trend'] = adx > cfg.adx_threshold

        # Drop NaN rows from indicator warm-up periods
        df_h = df_h.dropna()

        if df_h.empty:
            logger.error("DataFrame is empty after indicator calculation and warm-up drop")
            return

        # Run core simulation engine
        logger.info(f"Running simulation engine over {len(df_h)} bars...")
        final_state = run_simulation_engine(df_h, cfg)


        # Calculate metrics
        logger.info("Calculating performance metrics...")
        metrics = calculate_performance_metrics(final_state)

        # Export CSV reports
        output_trades_csv = os.path.join(base_dir, "protected_trades_report.csv")
        output_pauses_csv = os.path.join(base_dir, "activated_pauses_report.csv")

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
        plot_backtest_results(metrics, output_filename=os.path.join(base_dir, "backtest_performance.png"))

        logger.info("Backtest execution completed succesfully")

    except Exception as e:
        logger.exception(f"Critical error in main backtest: {e}")
        sys.exit(1)
# Añade esto temporalmente en main.py después del resample
if __name__ == "__main__":
     main()