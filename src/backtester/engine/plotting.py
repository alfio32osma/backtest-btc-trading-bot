import logging 
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger(__name__)

def plot_backtest_results(metrics: Dict[str, Any], output_filename: str = "backtest_performance.png") -> None:
    #Generate a publication quality institutional level with multi-panel performance chart
    #Displays also the Equity Curve, Underwater Drawdown, and Capital protection pauses
    try: 
        history_series = metrics.get("history_series")
        drawdowns = metrics.get("drawdowns")
        df_pauses = metrics.get("df_pauses")

        if history_series is None or history_series.empty:
            logger.warning("No history series available for plotting")
            return 

        plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
        fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

        ax_equity, ax_dd = axes

        #Equity curve panel

        ax_equity.plot(
            history_series.index, history_series.values,
            color= '#1f77b4',
            linewidth=1.5,
            label='Strategy Equity (€)'
        )
        ax_equity.set_title(
            'Algorithmic trend-following strategy with capital protection system',
            fontsize=12,
            fontweight='bold',
            pad=12
        )
        ax_equity.set_ylabel(
            'Portfolio Equity (€)',
            fontsize=10,
            fontweight='bold'
        )
        ax_equity.legend(
            loc='upper left',
            frameon=True,
            facecolor='white',
            framealpha=0.9
        )
        ax_equity.grid(
            True,
            linestyle= '--',
            alpha=0.5
        )

        #Highlight pause events on equity curve
        if df_pauses is not None and not df_pauses.empty and 'Date' in df_pauses.columns and 'Level' in df_pauses.columns:
            try:
                # TimeZone Normalization
                hist_idx = history_series.index
                if getattr(hist_idx, 'tz', None) is not None:
                    hist_idx = hist_idx.tz_localize(None)

                pause_dates = pd.to_datetime(df_pauses['Date'])
                if getattr(pause_dates.dt, 'tz', None) is not None:
                    pause_dates = pause_dates.dt.tz_localize(None)

                pause_levels = df_pauses['Level'].values
                color_map = {
                    1: 'gold',
                    2: 'darkorange',
                    3: 'crimson'
                }

                idx_matches = hist_idx.get_indexer(
                    pause_dates,
                    method='nearest',
                    tolerance=pd.Timedelta('4h')
                )

                for idx, p_lvl in zip(idx_matches, pause_levels):
                    if idx != -1: # -1 means it was out of tolerance range
                        matched_date = history_series.index[idx]
                        eq_val = history_series.iloc[idx]
                        ax_equity.scatter(
                            matched_date,
                            eq_val,
                            color= color_map.get(p_lvl, 'red'),
                            s=50,
                            zorder=5,
                            edgecolor='black',
                            linewidth=0.5
                        )
                        
            except Exception as sub_e:
                logger.warning(f"Could not plot pause markers: {sub_e}")

        #Underwater drawdown panel
        if drawdowns is not None and not drawdowns.empty:
            dd_pct = drawdowns * 100.0
            ax_dd.fill_between(
                dd_pct.index,
                dd_pct.values,
                0,
                color='crimson',
                alpha=0.3,
                label='Drawdown (%)'
            ) 
            ax_dd.plot(
                dd_pct.index,
                dd_pct.values,
                color='crimson',
                linewidth=1.0
            )
            ax_dd.set_ylabel(
                'Drawdown (%)',
                fontsize=10,
                fontweight='bold'
            )
            ax_dd.set_xlabel(
                'Timeline',
                fontsize=10,
                fontweight='bold'
            )
            ax_dd.legend(
                loc='lower left',
                frameon=True,
                facecolor='white',
                framealpha=0.9
            )
            ax_dd.grid(
                True,
                linestyle='--',
                alpha=0.5
            )

        plt.tight_layout()
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Performance plot successfully saved to: '{output_filename}'")
        print(f"Performance chart saved to: '{output_filename}'")

    except Exception as e:
        logger.error(f"Critical error generating backtest plots: {e}")