import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from src.data_loader import load_and_clean_data, resample_data
from src.indicators import calculate_adx, calculate_average_true_range
from src.backtester.risk_manager import evaluate_protection_system
from src.backtester.position import TradePosition


def ejecutar_backtest_con_proteccion(csv_path):
    # 1 | Load and clean data
    df_raw = load_and_clean_data(csv_path)
    df_h = resample_data(df_raw, timeframe="4h")

    # 2 | Calculate indicators
    df_h['Ema200'] = df_h['close'].ewm(span=200, adjust=False).mean()
    df_h['Ema50'] = df_h['close'].ewm(span=50, adjust=False).mean()
    df_h['atr'] = calculate_average_true_range(df_h, period=14)
    df_h['adx'] = calculate_adx(df_h, period=14)

    df_h['volatilidad_ok'] = df_h['atr'] < (df_h['close'] * 0.02)
    df_h['tendencia_fuerte'] = df_h['adx'] > 31

    # BASE STRATEGY PARAMETERS
    balance_bot       = 1000.0
    leverage          = 3.5
    fee_rate          = 0.0006
    funding_rate_4h   = 0.0001
    stop_loss_pct     = 0.03
    trailing_pct      = 0.03
    exit_ema_margin   = 0.006
    tp_parcial_pct    = 0.247

    # STATE VARIABLES
    total_fees_paid     = 0.0
    total_funding_paid  = 0.0
    in_position         = False
    pending_signal      = False
    active_position     = None  # TradePosition instance container

    # -- CAPITAL PROTECTION SYSTEM VARIABLES --
    consecutive_losses  = 0
    pause_candles       = 0
    balance_peak        = balance_bot
    active_level        = 0
    skipped_trades      = 0    
    pause_logs          = []   

    history_total = []
    dates         = []
    trade_list    = []

    # SIMULATION LOOP
    for i in range(200, len(df_h)):
        c_close  = df_h['close'].iloc[i]
        fecha    = df_h.index[i]
        ema200   = df_h['Ema200'].iloc[i]
        ema50    = df_h['Ema50'].iloc[i]
        vol_ok   = df_h['volatilidad_ok'].iloc[i]
        adx_ok   = df_h['tendencia_fuerte'].iloc[i]

        # Update equity peak
        if balance_bot > balance_peak:
            balance_peak = balance_bot

        # Evaluate protection system via risk_manager module
        new_level, calculated_pause_candles, current_drawdown = evaluate_protection_system(
            balance_bot = balance_bot,
            balance_peak = balance_peak,
            consecutive_losses = consecutive_losses
        )

        # If tier rises, activate corresponding pause
        if new_level > active_level and not in_position:
            active_level  = new_level
            pause_candles = calculated_pause_candles
            pause_logs.append({
                'Date': fecha,
                'Level': active_level,
                'Consecutive Losses': consecutive_losses,
                'Drawdown %': round(current_drawdown * 100, 2),
                'Pause Candles': pause_candles 
            })

        # Countdown pause candles
        if pause_candles > 0:
            pause_candles -= 1

        system_locked = (pause_candles > 0)

        # OPEN POSITION MANAGEMENT - Delegated to TradePosition class
        if in_position:
            update_result = active_position.update_position(
                current_close   =   c_close,
                ema200          =   ema200,
                exit_ema_margin =   exit_ema_margin,
                fee_rate        =   fee_rate,
                funding_rate_4h =   funding_rate_4h
            )

            funding_cost         =  update_result["funding_cost"]
            balance_bot         -=  funding_cost
            total_funding_paid  +=  funding_cost

            if update_result["partial_executed"]:
                balance_bot     +=  update_result["net_partial_pnl"]
                total_fees_paid +=  update_result["partial_fee"]

            exit_ema_threshold  =   ema200 * (1 - exit_ema_margin)
            should_close_by_ema =   (c_close < exit_ema_threshold)

            if update_result["should_close"] or should_close_by_ema:
                net_pnl, exit_fee, final_return = active_position.close_position(
                    current_close   =   c_close,
                    fee_rate        =   fee_rate
                )
                total_fees_paid +=  exit_fee

                trade_list.append({
                    'Entry Date':        active_position.entry_date,
                    'Exit Date':         fecha,
                    'Entry Price':       round(active_position.entry_price, 2),
                    'Exit Price':        round(c_close, 2),
                    'Net Return %':      round(final_return * 100, 2),
                    'Net Profit €':      round(net_pnl, 2),
                    'Post-Trade Equity': round(balance_bot + net_pnl, 2),
                    'Protection Level':  active_level
                })

                balance_bot +=  net_pnl

                # Update consecutive losses counter
                if net_pnl > 0:
                    consecutive_losses = 0
                    active_level       = 0
                    pause_candles      = 0
                else:
                    consecutive_losses += 1

                in_position     =   False
                active_position =   None

        # NEW ENTRY SEARCH
        else:
            if pending_signal:
                if system_locked:
                    pending_signal  =   False
                    skipped_trades  +=  1
                else:
                    capital_in_trade    =   balance_bot
                    entry_fee           =   (capital_in_trade * leverage) * fee_rate
                    balance_bot         -=  entry_fee
                    total_fees_paid     +=  entry_fee

                    p_entry_real    =   c_close * 1.001
                    entry_date      =   fecha

                    # Initialize robust position object
                    active_position =   TradePosition(
                        entry_price         =   p_entry_real,
                        capital_in_trade    =   capital_in_trade,
                        leverage            =   leverage,
                        stop_loss_pct       =   stop_loss_pct,
                        trailing_stop_pct   =   trailing_pct,
                        tp_parcial_pct      =   tp_parcial_pct,
                        entry_date          =   entry_date      
                    )

                    in_position     =   True
                    pending_signal  =   False

            elif (not system_locked and
                c_close > ema200 and c_close > ema50 and
                ema50 > ema200 and vol_ok and adx_ok):
                pending_signal  =   True

        history_total.append(balance_bot)
        dates.append(fecha)

    # FINAL METRICS & DATAFRAMES
    history_series  =   pd.Series(history_total, index=dates)
    roll_max        =   history_series.cummax()
    drawdowns       =   (history_series - roll_max) / roll_max
    max_drawdown    =   drawdowns.min() * 100

    df_trades       =   pd.DataFrame(trade_list)
    df_pausas       =   pd.DataFrame(pause_logs)
    total_trades    =   len(df_trades)

    if not df_trades.empty:
        df_trades.to_csv('reporte_trades_con_proteccion.csv', index=False)
    
    if not df_pausas.empty:
        df_pausas.to_csv('reporte_pausas_activadas.csv', index=False)
        print("\n Pause Report saved to: 'reporte_pausas_activadas.csv'")

    if total_trades > 0:
        winners       =   df_trades[df_trades['Net Profit €'] > 0]
        losers        =   df_trades[df_trades['Net Profit €'] <= 0]
        win_rate      =   (len(winners) / total_trades) * 100
        gross_won     =   winners['Net Profit €'].sum()
        gross_lost    =   abs(losers['Net Profit €'].sum())
        profit_factor =   gross_won / gross_lost if gross_lost != 0 else float('inf')

        pausas_n1 = len(df_pausas[df_pausas['Level'] == 1]) if not df_pausas.empty else 0
        pausas_n2 = len(df_pausas[df_pausas['Level'] == 2]) if not df_pausas.empty else 0
        pausas_n3 = len(df_pausas[df_pausas['Level'] == 3]) if not df_pausas.empty else 0
    else:
        win_rate = profit_factor = 0
        pausas_n1 = pausas_n2 = pausas_n3 = 0

    print("\n" + " CAPITAL PROTECTION SYSTEM REPORT ".center(62, "="))
    print(f"💰 FINAL EQUITY:              {balance_bot:,.2f} €")
    print(f"📉 MAX DRAWDOWN:              {max_drawdown:.2f}%")
    print(f"📈 WIN RATE:                  {win_rate:.2f}%")
    print(f"📊 PROFIT FACTOR:             {profit_factor:.2f}")
    print(f"📊 TOTAL TRADES:              {total_trades}")
    print(f"⏸️  SKIPPED TRADES:            {skipped_trades}")
    print(f"💸 TOTAL COSTS:               {(total_fees_paid + total_funding_paid):,.2f} €")
    print(f"─" * 62)
    print(f"🟡 Level 1 pauses (12h):      {pausas_n1}")
    print(f"🟠 Level 2 pauses (48h):      {pausas_n2}")
    print(f"🔴 Level 3 pauses (5 days):   {pausas_n3}")
    print("=" * 62)

    # PLOT
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [3, 1]})

    ax1.plot(dates, history_total, color='royalblue', linewidth=1.2, label='Equity')
    ax1.set_yscale('log')
    ax1.set_title("Equity Curve — Capital Protection System", fontsize=13)
    ax1.grid(True, which="both", ls="--", alpha=0.4)
    ax1.set_ylabel("Equity (€, log)")

    colores_nivel = {1: 'gold', 2: 'orange', 3: 'red'}
    for _, row in df_pausas.iterrows():
        ax1.axvline(x=row['Date'], color=colores_nivel[row['Level']], alpha=0.4, linewidth=0.8)

    leyenda = [
        Line2D([0], [0], color='gold',       linewidth=1.5, label='Pause Level 1 (12h)'),
        Line2D([0], [0], color='orange',     linewidth=1.5, label='Pause Level 2 (48h)'),
        Line2D([0], [0], color='red',        linewidth=1.5, label='Pause Level 3 (5d)'),
        Line2D([0], [0], color='royalblue',  linewidth=1.5, label='Equity'),
    ]
    ax1.legend(handles=leyenda, fontsize=9)

    drawdown_series = drawdowns * 100
    ax2.fill_between(dates, drawdown_series, 0, color='crimson', alpha=0.35)
    ax2.plot(dates, drawdown_series, color='crimson', linewidth=0.8)
    ax2.axhline(y=-50, color='black', linestyle='--', linewidth=0.8, label='Limit -50%')
    ax2.set_ylabel("Drawdown (%)")
    ax2.set_ylim(bottom=min(drawdown_series.min() * 1.1, -55), top=5)
    ax2.grid(True, ls="--", alpha=0.3)
    ax2.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig('grafico_proteccion_capital.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\n📊 Chart saved to: 'grafico_proteccion_capital.png'")


if __name__ == "__main__":
    ejecutar_backtest_con_proteccion('btc.csv')