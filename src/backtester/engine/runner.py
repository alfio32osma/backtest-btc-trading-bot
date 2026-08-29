import logging
import pandas as pd
from src.backtester.engine.state import BacktestState
from src.backtester.engine.strategy import check_entry_signal
from src.backtester.engine.execution import manage_open_position, execute_new_entry
from src.backtester.risk_manager import evaluate_protection_system

logger = logging.getLogger(__name__)

from src.config import BacktestConfig

def run_simulation_engine(df_h: pd.DataFrame, cfg: BacktestConfig) -> BacktestState:
    #Core backtest loop, ochestrates state, risk and execution
    if df_h is None or df_h.empty:
        raise ValueError("DataFrame is empty. Cannot run simulation")

    state = BacktestState(equity=1000.0)
    state.prepare_buffers(total_bars=len(df_h))

    last_bar = None

    for current_bar in df_h.itertuples(index=True):
        last_bar = current_bar
        index = current_bar.Index
        try:
            # Skip rows with missing critical data
            c_close = getattr(current_bar, 'close', None)
            ema200 = getattr(current_bar, 'Ema200', None)

            if c_close is None or ema200 is None or pd.isna(c_close) or pd.isna(ema200):
                logger.warning(f"Missing data at {index}. Skipped bar")
                continue

            # Bankruptcy check
            if state.equity <= 0:
                logger.error(f"Bankruptcy reached at {index}. Halting simulation")
                break

            # Update equity high-water mark for drawdowns
            state.equity_peak = max(state.equity_peak, state.equity)

            # Risk Management
            new_level, pause_candles, current_drawdown = evaluate_protection_system(
                balance_bot=state.equity,
                balance_peak=state.equity_peak,
                consecutive_losses=state.consecutive_losses,
                cfg=cfg
            )

            if new_level > state.active_level and not state.in_position:
                state.activate_pause(new_level, pause_candles, index, current_drawdown)

            if state.pause_candles > 0:
                state.pause_candles -= 1

            system_locked = (state.pause_candles > 0)

            # Trade Management
            if state.in_position:
                manage_open_position(current_bar, index, state, cfg)
            else:
                if state.pending_signal:
                    if system_locked:
                        state.pending_signal = False
                        state.skipped_trades += 1
                    else:
                        execute_new_entry(current_bar, index, state, cfg)

                #ask strategy module if we should open a trade next bar
                elif not system_locked and check_entry_signal(current_bar):
                    state.pending_signal = True

            # Record metrics
            state.record_history(index)

        except Exception as e:
            # Catches math errors, corrupted data, etc
            logger.error(f"Critical error processing bar {index}: {str(e)}")
            continue
    
    #force close any open position at the end of the backtest
    if state.in_position and last_bar is not None:
        try:
            c_close = float(getattr(last_bar, 'close'))
            net_pnl, exit_fee, final_return = state.active_position.close_position(
                current_close=c_close,
                fee_rate=cfg.fee_rate
            )
            state.trade_list.append({
                'Entry Date': state.active_position.entry_date,
                'Exit Date': last_bar.Index,
                'Entry Price': round(state.active_position.entry_price, 2),
                'Exit Price': round(c_close, 2),
                'Net Return %': round(final_return * 100, 2),
                'Net Profit €': round(net_pnl, 2),
                'Post-Trade Equity': round(state.equity + net_pnl, 2),
                'Protection Level': state.active_level
            })
            state.equity += net_pnl
            state.in_position = False
            state.active_position = None

        except Exception as e:
            logger.error(f"Error closing final open position at: {e}")

    state.finalize_buffers()
    
    return state