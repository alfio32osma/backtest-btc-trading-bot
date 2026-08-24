import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.data_loader import load_and_clean_data, resample_data
from src.indicators import calculate_adx

#region
# ═══════════════════════════════════════════════════════════════════
#  SISTEMA DE PROTECCIÓN DE CAPITAL — LÓGICA GENERAL
# ═══════════════════════════════════════════════════════════════════
#
#  El sistema tiene TRES niveles de alerta que se activan de forma
#  acumulativa según las pérdidas consecutivas o el drawdown desde
#  el último máximo de balance:
#
#  NIVEL 1 — Alerta (2 pérdidas seguidas O drawdown > 15%)
#    → Pausa de 3 velas (12h) antes de aceptar nueva señal
#    → Mensaje: el mercado está en racha adversa, esperar confirmación
#
#  NIVEL 2 — Precaución (3 pérdidas seguidas O drawdown > 25%)
#    → Pausa de 12 velas (48h) antes de aceptar nueva señal
#    → Se resetea el contador de pérdidas al reanudar
#
#  NIVEL 3 — Protección máxima (4 pérdidas seguidas O drawdown > 40%)
#    → Pausa de 30 velas (5 días) antes de aceptar nueva señal
#    → Al reanudar, el sistema vuelve a nivel 0
#
#  RESET AUTOMÁTICO: si se produce un trade ganador, el contador
#  de pérdidas consecutivas vuelve a 0 y se desactiva cualquier pausa.
#
#  OBJETIVO: reducir el drawdown máximo por debajo del 50% sacrificando
#  algunos trades en momentos de racha adversa, no modificando la
#  lógica de entrada/salida de la estrategia base.
# ═══════════════════════════════════════════════════════════════════
#endregion

df_raw = load_and_clean_data("btc.csv")
df_h = resample_data(df_raw, timeframe="4h")
df_h['adx'] = calculate_adx(df_h, period=14)


def ejecutar_backtest_con_proteccion(csv_path):
    # 3. INDICADORES
    df_h['Ema200'] = df_h['close'].ewm(span=200, adjust=False).mean()
    df_h['Ema50']  = df_h['close'].ewm(span=50,  adjust=False).mean()

    high_low    = df_h['high'] - df_h['low']
    high_close  = np.abs(df_h['high'] - df_h['close'].shift())
    low_close   = np.abs(df_h['low']  - df_h['close'].shift())
    df_h['atr'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(14).mean()
    df_h['adx'] = calcule_adx(df_h, period=14)

    df_h['volatilidad_ok']  = df_h['atr'] < (df_h['close'] * 0.02)
    df_h['tendencia_fuerte'] = df_h['adx'] > 31

    # 4. PARÁMETROS DE LA ESTRATEGIA BASE (sin cambios)
    balance_bot       = 1000.0
    leverage          = 3.5
    fee_rate          = 0.0006
    funding_rate_4h   = 0.0001
    stop_loss_pct     = 0.03
    trailing_pct      = 0.03
    margen_ema_salida = 0.006
    tp_parcial_pct    = 0.247

    # 5. PARÁMETROS DEL SISTEMA DE PROTECCIÓN
    # ─── Umbrales de pérdidas consecutivas ──────────────────────────
    PERDIDAS_NIVEL1 = 2      # 2 pérdidas → alerta
    PERDIDAS_NIVEL2 = 3      # 3 pérdidas → precaución
    PERDIDAS_NIVEL3 = 4      # 4 pérdidas → protección máxima

    # ─── Umbrales de drawdown desde el último máximo ─────────────────
    DD_NIVEL1 = 0.15         # -15% desde el pico
    DD_NIVEL2 = 0.25         # -25% desde el pico
    DD_NIVEL3 = 0.40         # -40% desde el pico

    # ─── Velas de pausa por nivel (1 vela = 4h) ─────────────────────
    PAUSA_NIVEL1 = 3         # 12 horas
    PAUSA_NIVEL2 = 12        # 48 horas
    PAUSA_NIVEL3 = 30        # 5 días

    # 6. VARIABLES DE ESTADO
    total_fees_paid    = 0.0
    total_funding_paid = 0.0
    in_position        = False
    hay_senal_pendiente = False
    p_entry_real       = 0
    current_stop       = 0
    fecha_entrada      = None
    capital_en_trade   = 0.0
    parcial_tomado     = False
    size_actual        = 1.0

    # ─── Variables del sistema de protección ────────────────────────
    perdidas_consecutivas = 0    # Contador de trades perdedores seguidos
    velas_en_pausa        = 0    # Velas que quedan de pausa activa
    balance_pico          = balance_bot  # Máximo histórico del balance
    nivel_activo          = 0    # Nivel de protección actual (0 = sin restricción)
    trades_saltados       = 0    # Contador informativo de trades evitados
    log_pausas            = []   # Registro de cada pausa activada

    history_total = []
    dates         = []
    lista_trades  = []

    # 7. SIMULACIÓN
    for i in range(200, len(df_h)):
        c_close  = df_h['close'].iloc[i]
        fecha    = df_h.index[i]
        ema200   = df_h['Ema200'].iloc[i]
        ema50    = df_h['Ema50'].iloc[i]
        vol_ok   = df_h['volatilidad_ok'].iloc[i]
        adx_ok   = df_h['tendencia_fuerte'].iloc[i]

        # ── Actualizar pico de balance ───────────────────────────────
        if balance_bot > balance_pico:
            balance_pico = balance_bot

        # ── Drawdown actual desde el pico ────────────────────────────
        drawdown_actual = (balance_bot - balance_pico) / balance_pico  # valor negativo

        # ── Determinar nivel de protección necesario ─────────────────
        #    Se evalúa pérdidas consecutivas Y drawdown; se toma el mayor nivel.
        nivel_por_perdidas = 0
        if perdidas_consecutivas >= PERDIDAS_NIVEL3:
            nivel_por_perdidas = 3
        elif perdidas_consecutivas >= PERDIDAS_NIVEL2:
            nivel_por_perdidas = 2
        elif perdidas_consecutivas >= PERDIDAS_NIVEL1:
            nivel_por_perdidas = 1

        nivel_por_drawdown = 0
        if drawdown_actual <= -DD_NIVEL3:
            nivel_por_drawdown = 3
        elif drawdown_actual <= -DD_NIVEL2:
            nivel_por_drawdown = 2
        elif drawdown_actual <= -DD_NIVEL1:
            nivel_por_drawdown = 1

        nuevo_nivel = max(nivel_por_perdidas, nivel_por_drawdown)

        # ── Si el nivel sube, activar pausa correspondiente ──────────
        if nuevo_nivel > nivel_activo and not in_position:
            nivel_activo = nuevo_nivel
            if nivel_activo == 1:
                velas_en_pausa = PAUSA_NIVEL1
            elif nivel_activo == 2:
                velas_en_pausa = PAUSA_NIVEL2
            elif nivel_activo == 3:
                velas_en_pausa = PAUSA_NIVEL3
            log_pausas.append({
                'Fecha': fecha,
                'Nivel': nivel_activo,
                'Pérdidas consec.': perdidas_consecutivas,
                'Drawdown %': round(drawdown_actual * 100, 2),
                'Velas pausa': velas_en_pausa
            })

        # ── Descontar velas de pausa ──────────────────────────────────
        if velas_en_pausa > 0:
            velas_en_pausa -= 1

        # ── El sistema está bloqueado si aún quedan velas de pausa ───
        sistema_bloqueado = (velas_en_pausa > 0)

        # ─────────────────────────────────────────────────────────────
        #  GESTIÓN DE POSICIÓN ABIERTA
        #  (la lógica de salida no cambia nunca — protegemos la entrada)
        # ─────────────────────────────────────────────────────────────
        if in_position:
            coste_funding = (capital_en_trade * leverage * size_actual) * funding_rate_4h
            balance_bot  -= coste_funding
            total_funding_paid += coste_funding

            rendimiento_actual = (c_close / p_entry_real) - 1

            # Salida parcial al 28.5%
            if not parcial_tomado and rendimiento_actual >= tp_parcial_pct:
                capital_parcial    = capital_en_trade * 0.5
                pnl_parcial_bruto  = capital_parcial * (rendimiento_actual * leverage)
                fee_parcial        = (capital_parcial * leverage) * fee_rate
                balance_bot       += (pnl_parcial_bruto - fee_parcial)
                total_fees_paid   += fee_parcial
                size_actual        = 0.5
                parcial_tomado     = True
                current_stop       = p_entry_real  # breakeven

            current_stop       = max(current_stop, c_close * (1 - trailing_pct))
            umbral_ema_salida  = ema200 * (1 - margen_ema_salida)

            if c_close < current_stop or c_close < umbral_ema_salida:
                capital_restante = capital_en_trade * size_actual
                pnl_bruto        = capital_restante * (rendimiento_actual * leverage)
                fee_salida       = (capital_restante * leverage) * fee_rate
                total_fees_paid += fee_salida
                pnl_neto         = pnl_bruto - fee_salida

                lista_trades.append({
                    'Fecha Entrada':     fecha_entrada,
                    'Fecha Salida':      fecha,
                    'Precio Entrada':    round(p_entry_real, 2), # AÑADIDO: Precio de entrada
                    'Precio Salida':     round(c_close, 2),      # AÑADIDO: Precio de salida
                    'Resultado Neto %':  round((pnl_neto / capital_en_trade) * 100, 2),
                    'Ganancia Neta €':   round(pnl_neto, 2),
                    'Balance Post-Trade': round(balance_bot + pnl_neto, 2),
                    'Nivel protección':  nivel_activo
                })

                balance_bot += pnl_neto

                # ── Actualizar contador de pérdidas consecutivas ─────
                if pnl_neto > 0:
                    perdidas_consecutivas = 0   # trade ganador → reset
                    nivel_activo          = 0   # se levanta la restricción
                    velas_en_pausa        = 0
                else:
                    perdidas_consecutivas += 1  # trade perdedor → sumar

                in_position      = False
                size_actual      = 1.0
                parcial_tomado   = False
                capital_en_trade = 0.0

        # ─────────────────────────────────────────────────────────────
        #  BÚSQUEDA DE NUEVA ENTRADA
        #  Solo se acepta señal si el sistema NO está bloqueado
        # ─────────────────────────────────────────────────────────────
        else:
            if hay_senal_pendiente:
                if sistema_bloqueado:
                    # La señal existe pero el sistema está en pausa → ignorar
                    hay_senal_pendiente = False
                    trades_saltados    += 1
                else:
                    # Sin bloqueo → entrar en el trade normalmente
                    capital_en_trade  = balance_bot
                    fee_entrada       = (capital_en_trade * leverage) * fee_rate
                    balance_bot      -= fee_entrada
                    total_fees_paid  += fee_entrada

                    p_entry_real  = c_close * 1.001
                    current_stop  = p_entry_real * (1 - stop_loss_pct)
                    fecha_entrada = fecha

                    in_position         = True
                    hay_senal_pendiente = False
                    parcial_tomado      = False
                    size_actual         = 1.0

            elif (not sistema_bloqueado and
                c_close > ema200 and c_close > ema50 and
                ema50 > ema200 and vol_ok and adx_ok):
                hay_senal_pendiente = True

        history_total.append(balance_bot)
        dates.append(fecha)

    # 8. MÉTRICAS FINALES
    history_series = pd.Series(history_total, index=dates)
    roll_max       = history_series.cummax()
    drawdowns      = (history_series - roll_max) / roll_max
    max_drawdown   = drawdowns.min() * 100

    df_trades  = pd.DataFrame(lista_trades)
    df_pausas  = pd.DataFrame(log_pausas)
    total_trades = len(df_trades)

    if not df_trades.empty:
        df_trades.to_csv('reporte_trades_con_proteccion.csv', index=False)

    if not df_pausas.empty:
        df_pausas.to_csv('reporte_pausas_activadas.csv', index=False)
        print(f"\n📂 Reporte de pausas guardado en: 'reporte_pausas_activadas.csv'")

    if total_trades > 0:
        ganadores    = df_trades[df_trades['Ganancia Neta €'] > 0]
        perdedores   = df_trades[df_trades['Ganancia Neta €'] <= 0]
        win_rate     = (len(ganadores) / total_trades) * 100
        bruto_ganado = ganadores['Ganancia Neta €'].sum()
        bruto_perdido = abs(perdedores['Ganancia Neta €'].sum())
        profit_factor = bruto_ganado / bruto_perdido if bruto_perdido != 0 else float('inf')

        # Pausas por nivel
        pausas_n1 = len(df_pausas[df_pausas['Nivel'] == 1]) if not df_pausas.empty else 0
        pausas_n2 = len(df_pausas[df_pausas['Nivel'] == 2]) if not df_pausas.empty else 0
        pausas_n3 = len(df_pausas[df_pausas['Nivel'] == 3]) if not df_pausas.empty else 0
    else:
        win_rate = profit_factor = 0
        pausas_n1 = pausas_n2 = pausas_n3 = 0

    print("\n" + " REPORTE CON SISTEMA DE PROTECCIÓN DE CAPITAL ".center(62, "="))
    print(f"💰 PATRIMONIO FINAL:          {balance_bot:,.2f} €")
    print(f"📉 MÁXIMO DRAWDOWN:           {max_drawdown:.2f}%")
    print(f"📈 WIN RATE:                  {win_rate:.2f}%")
    print(f"📊 PROFIT FACTOR:             {profit_factor:.2f}")
    print(f"📊 TOTAL TRADES:              {total_trades}")
    print(f"⏸️  TRADES SALTADOS:           {trades_saltados}")
    print(f"💸 COSTES TOTALES:            {(total_fees_paid + total_funding_paid):,.2f} €")
    print(f"─" * 62)
    print(f"🟡 Pausas nivel 1 (12h):      {pausas_n1}")
    print(f"🟠 Pausas nivel 2 (48h):      {pausas_n2}")
    print(f"🔴 Pausas nivel 3 (5 días):   {pausas_n3}")
    print("=" * 62)

    # 9. GRÁFICO
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={'height_ratios': [3, 1]})

    ax1.plot(dates, history_total, color='royalblue', linewidth=1.2, label='Balance')
    ax1.set_yscale('log')
    ax1.set_title("Evolución Patrimonio — Sistema de Protección de Capital", fontsize=13)
    ax1.grid(True, which="both", ls="--", alpha=0.4)
    ax1.set_ylabel("Balance (€, log)")

    # Marcar las pausas en el gráfico
    colores_nivel = {1: 'gold', 2: 'orange', 3: 'red'}
    for _, row in df_pausas.iterrows():
        ax1.axvline(x=row['Fecha'], color=colores_nivel[row['Nivel']], alpha=0.4, linewidth=0.8)

    from matplotlib.lines import Line2D
    leyenda = [
        Line2D([0], [0], color='gold',       linewidth=1.5, label='Pausa nivel 1 (12h)'),
        Line2D([0], [0], color='orange',     linewidth=1.5, label='Pausa nivel 2 (48h)'),
        Line2D([0], [0], color='red',        linewidth=1.5, label='Pausa nivel 3 (5d)'),
        Line2D([0], [0], color='royalblue',  linewidth=1.5, label='Balance'),
    ]
    ax1.legend(handles=leyenda, fontsize=9)

    # Drawdown en el panel inferior
    drawdown_series = drawdowns * 100
    ax2.fill_between(dates, drawdown_series, 0, color='crimson', alpha=0.35)
    ax2.plot(dates, drawdown_series, color='crimson', linewidth=0.8)
    ax2.axhline(y=-50, color='black', linestyle='--', linewidth=0.8, label='Límite -50%')
    ax2.set_ylabel("Drawdown (%)")
    ax2.set_ylim(bottom=min(drawdown_series.min() * 1.1, -55), top=5)
    ax2.grid(True, ls="--", alpha=0.3)
    ax2.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig('grafico_proteccion_capital.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("\n📊 Gráfico guardado en: 'grafico_proteccion_capital.png'")


if __name__ == "__main__":
    ejecutar_backtest_con_proteccion('btc.csv')