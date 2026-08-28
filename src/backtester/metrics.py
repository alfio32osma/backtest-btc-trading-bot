import logging
import pandas as pd
import numpy as np
from typing import Any, Dict

logger = logging.getLogger(__name__)

class MetricsError(Exception):
    #base exception for metrics calculation errors
    pass

def calculate_performance_metrics(final_state: Any) -> Dict[str, Any]:
    #Includes CAGR, sharpe ratio, max DD, WR, PF
    #Handle edge cases such as zero trades, constant equity, or empty hsitory
    default_metrics = {
        "final_equity": final_state.equity,
        "total_return_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "win_rate_pct": 0.0,
        "profit_factor": 0.0,
        "sharpe_ratio": 0.0,
        "sortino_ratio": 0.0,
        "pauses_l1": 0,
        "pauses_l2": 0,
        "pauses_l3": 0
    }
    try:
        if not hasattr(final_state, "history_total") or not final_state.history_total:
            logger.warning("History total is empty BacktestState. Returning default metrics")
            return default_metrics

        history_series = pd.Series(final_state.history_total, index= pd.to_datetime(final_state.dates))
        if history_series.empty:
            return default_metrics

        #Equity and returns
        initial_equity = history_series.iloc[0]
        final_equity = history_series.iloc[-1]
        total_return_pct = ((final_equity / initial_equity) - 1.0) * 100.0 if initial_equity > 0 else 0.0

        #DD calculations
        roll_max = history_series.cummax()
        drawdowns = (history_series - roll_max) / roll_max.replace(0, np.nan)
        max_drawdown_pct = float(drawdowns.min() * 100.0) if not drawdowns.empty else 0.0

        #Trade analytics
        df_trades = pd.DataFrame(final_state.trade_list)
        total_trades = len(df_trades)

        win_rate_pct = 0.0
        profit_factor = 0.0
        if total_trades > 0 and 'Net Profit €' in df_trades.columns:
            winners = df_trades[df_trades['Net Profit €'] > 0]
            losers = df_trades[df_trades['Net Profit €'] <= 0]
            win_rate_pct = (len(winners) / total_trades) * 100.0

            gross_won = float(winners['Net Profit €'].sum())
            gross_lost = float(abs(losers['Net Profit €'].sum()))

            if gross_lost == 0.0:
                profit_factor = float('inf') if gross_won > 0 else 1.0
            else:
                profit_factor = gross_won / gross_lost

        #Risk-adjusted returns (sharpe and Sortino on 4h bar returns)
        returns = history_series.pct_change().dropna()
        sharpe_ratio = 0.0
        sortino_ratio = 0.0

        if not returns.empty and returns.std() > 0:
            #4h candles to 6 candles per day is a total of 2190 periods per year
            periods_per_year = 2190
            mean_return = returns.mean()
            std_return = returns.std()
            sharpe_ratio = float((mean_return / std_return) * np.sqrt(periods_per_year))

            downside_returns = returns[returns < 0]
            downside_std = downside_returns.std() if not downside_returns.empty else 0.0

        # Pause counters
        df_pauses = pd.DataFrame(final_state.pause_logs)
        pauses_l1 = len(df_pauses[df_pauses['Level'] == 1]) if not df_pauses.empty and 'Level' in df_pauses.columns else 0
        pauses_l2 = len(df_pauses[df_pauses['Level'] == 2]) if not df_pauses.empty and 'Level' in df_pauses.columns else 0
        pauses_l3 = len(df_pauses[df_pauses['Level'] == 3]) if not df_pauses.empty and 'Level' in df_pauses.columns else 0

        total_costs = float(getattr(final_state, 'total_fees_paid', 0.0) + getattr(final_state, 'total_funding_paid', 0.0))

        metrics = {
            "history_series": history_series,
            "drawdowns": drawdowns,
            "df_trades": df_trades,
            "df_pauses": df_pauses,
            "final_equity": final_equity,
            "total_return_pct": total_return_pct,
            "max_drawdown_pct": max_drawdown_pct,
            "win_rate_pct": win_rate_pct,
            "profit_factor": profit_factor,
            "total_trades": total_trades,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "pauses_l1": pauses_l1,
            "pauses_l2": pauses_l2,
            "pauses_l3": pauses_l3,
            "total_costs": total_costs
        }
        return metrics

    except Exception as e:
        logger.error(f"Error calculating performance metrics: {e}")
        raise MetricsError(f"Failed to calculate metrics: {e}")

def print_quant_report(metrics: Dict[str, Any], final_state: Any) -> None:
    """Prints a professional institutional-grade quantitative backtest report."""
    try:
        print("\n" + " INSTITUTIONAL QUANTITATIVE BACKTEST REPORT ".center(70, "="))
        print(f"💰 INITIAL CAPITAL:          1,000.00 €")
        print(f"💰 FINAL EQUITY:             {metrics['final_equity']:,.2f} €")
        print(f"📈 TOTAL RETURN:             {metrics['total_return_pct']:+.2f}%")
        print(f"📉 MAX DRAWDOWN:             {metrics['max_drawdown_pct']:.2f}%")
        print(f"⚡ SHARPE RATIO (Ann.):      {metrics['sharpe_ratio']:.2f}")
        print(f"🛡️  SORTINO RATIO (Ann.):     {metrics['sortino_ratio']:.2f}")
        print("-" * 70)
        print(f"🎯 WIN RATE:                 {metrics['win_rate_pct']:.2f}%")
        print(f"📊 PROFIT FACTOR:            {metrics['profit_factor'] if metrics['profit_factor'] != float('inf') else 'INF':.2f}")
        print(f"📊 TOTAL TRADES:             {metrics['total_trades']}")
        print(f"⏸️  SKIPPED TRADES (Pauses):  {getattr(final_state, 'skipped_trades', 0)}")
        print(f"💸 TOTAL TRANSACTION COSTS:  {metrics['total_costs']:,.2f} €")
        print("-" * 70)
        print(f"🟡 Level 1 Pauses (12h):     {metrics['pauses_l1']}")
        print(f"🟠 Level 2 Pauses (48h):     {metrics['pauses_l2']}")
        print(f"🔴 Level 3 Pauses (5 Days):  {metrics['pauses_l3']}")
        print("=" * 70)
    except Exception as e:
        logger.error(f"Error printing quant report: {e}")