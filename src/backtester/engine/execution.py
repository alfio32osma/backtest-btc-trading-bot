import logging
import pandas as pd
from typing import Any
from src.config import BacktestConfig
from src.backtester.position import TradePosition

logger = logging.getLogger(__name__)

def execute_new_entry(current_bar: pd.Series, index: Any, state: Any, cfg: BacktestConfig) -> None:
    #Handles the execution logic for opening a new leveraged long position 
    #Applies fees and initializes the TradePosition object safely
    try:
        c_close = getattr(current_bar, 'close', None)
        if current_bar is None or c_close is None:
            raise ValueError("Invalid bar data provided for trade entry.")

        # Parameters from config
        leverage = cfg.leverage
        fee_rate = cfg.fee_rate
        stop_loss_pct = cfg.stop_loss_pct
        trailing_pct = cfg.trailing_stop_pct
        tp_parcial_pct = cfg.tp_parcial_pct

        capital_in_trade = state.equity
        entry_fee = (capital_in_trade * leverage) * fee_rate
        state.equity -= entry_fee
        state.total_fees_paid += entry_fee

        #Simulate small slippage on entry
        p_entry_real = float(c_close) * (1 + cfg.slippage)
        entry_date = index 

        state.active_position = TradePosition(
            entry_price = p_entry_real,
            capital_in_trade = capital_in_trade,
            leverage = leverage,
            stop_loss_pct = stop_loss_pct,
            trailing_stop_pct = trailing_pct,
            tp_parcial_pct = tp_parcial_pct,
            entry_date = entry_date
        )

        state.in_position = True
        state.pending_signal = False
        logger.info(f"Opened new position at {entry_date} with price {p_entry_real:.2f}")

    except Exception as e:
        logger.error(f"Critical error executing new entry at {index}: {e}")
        state.pending_signal = False

def manage_open_position(current_bar: Any, index: Any, state: Any, cfg: BacktestConfig) -> None:
    #Manages the lifecycle of an open position: updates prices, checks stop losses
    #Takes partial profits, evaluates EMA exists, and closes the trade if triggered
    try:
        if not state.in_position or state.active_position is None:
            return

        c_close = float(getattr(current_bar, 'close'))
        ema200 = float(getattr(current_bar, 'Ema200'))
        exit_ema_margin = cfg.exit_ema_margin
        fee_rate = cfg.fee_rate
        funding_rate_4h = cfg.funding_rate_4h

        #Update postion metrics
        update_result = state.active_position.update_position(
            current_close=c_close,
            ema200=ema200,
            exit_ema_margin=exit_ema_margin,
            fee_rate=fee_rate,
            funding_rate_4h=funding_rate_4h
        )

        #Deduct funding fees
        funding_cost = update_result.get("funding_cost", 0.0)
        state.equity -= funding_cost
        state.total_funding_paid += funding_cost

        #Handle partial profit execution if triggered
        if update_result.get("partial_executed", False):
            net_partial_pnl = update_result.get("net_partial_pnl", 0.0)
            partial_fee = update_result.get("partial_fee", 0.0)
            state.equity += net_partial_pnl
            state.total_fees_paid += partial_fee

        #Check EMA exit condition
        exit_ema_threshold = ema200 * (1 - exit_ema_margin)
        should_close_by_ema = (c_close < exit_ema_threshold)

        #Close poition if stop loss, trailing stop, or EMA condition met
        if update_result.get("should_close", False) or should_close_by_ema:
            net_pnl, exit_fee, final_return = state.active_position.close_position(
                current_close=c_close,
                fee_rate=fee_rate
            )
            state.total_fees_paid += exit_fee

            #Record trade details info state
            state.trade_list.append({
                'Entry Date': state.active_position.entry_date,
                'Exit Date': index,
                'Entry Price': round(state.active_position.entry_price, 2),
                'Exit Price': round(c_close, 2),
                'Net Return %': round(final_return * 100, 2),
                'Net Profit €': round(net_pnl, 2),
                'Post-Trade Equity': round(state.equity + net_pnl, 2),
                'Protection Level': state.active_level
            })

            state.equity += net_pnl

            #Update consecutive losses counter and risk levels
            if net_pnl > 0:
                state.consecutive_losses = 0
                state.active_level = 0
                state.pause_candles = 0
            else:
                state.consecutive_losses += 1

            state.in_position = False
            state.active_position = None
            logger.info(f"Closed position at {index}. Net PnL: {net_pnl:.2f} EUR")

    except Exception as e:
        logger.error(f"Critical error managing open position at {index}: {e}")
