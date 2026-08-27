import logging
import pandas as pd
from src.backtester.state import Backtest_state
from src.backtester.strategy import check_entry_signal
from src.backtester.execution import manage_open_position, execute_new_entry
from src.backtester.risk_manager import evaluate_protection_system

logger = logging.getLogger(__name__)

def run_simulation_engine(df_h: pd.DataFrame) -> Backtest_state:
    #Core backtest loop, ochestrates state, risk and execution

    if df_h is None or df_h.empty:
        raise ValueError("DataFrame is empty. Cannot run simulation")

    state = Backtest_state(initial_equity= 1000.0)

    for index, current_bar in df_h.iterrows():
        try:
            # Skip rows with missing critical data
            if pd.isna(current_bar['close']) or pd.isna(current_bar['Ema200']):
                logger.warning(f"Missing data at {index}. Skipping bar.")
                continue

            # Bankruptcy check
            if state.equity <= 0:
                logger.errors(f"Bankruptcy reached at {index}. Halting simulation")
                break

            # Update equity high-water mark for drawdowns
            state.equity_peak = max(state.equity_peak, state.equity)

            # Risk Management
            new_level, pause_candles, current_drawdown = evaluate_protection_system(
                balance_bot = state.equity,
                balance_peak = state.equity_peak,
                consecutive_losses = state.consecutive_losses
            )

            if new_level > state.active_level and not state.in_position:
                state.activate_pause(new_level, pause_candles, index, current_drawdown)

            if state.pause_candles > 0:
                state.pause_candles -= 1

            system_locked = (state.pause_candles > 0)

            # Trade Management
            if state.in_position:
                manage_open_position(current_bar, index, state)
            else:
                if state.pending_signal:
                    if system_locked:
                        state.pending_signal = False
                        state.skiped_trades += 1
                    else:
                        execute_new_entry(current_bar, index, state)

                #ask strategy module if we shoudl open a trade next bar
                elif not system_locked and check_entry_signal(current_bar):
                    state.pending_signal = True

            # Record metrics
            state.record_history(index)

        except Exception as e:
            # Catches match errors, corrupted data, etc
            logger.error(f"Critical error processing bar {index}: {str(e)}")
            continue
        
    return state