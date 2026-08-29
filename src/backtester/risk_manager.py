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
from src.config import BacktestConfig


def evaluate_protection_system(
        balance_bot: float,
        balance_peak: float,
        consecutive_losses: int,
        cfg: BacktestConfig | None = None
        ):
    if cfg is None:
        cfg = BacktestConfig()

    #Evaluates cocnsecutive loss streaks and drawdown thresholds to determinate
    #the active pause level for the capital protection system
    try:
        #Input validation & error handling:
        if not isinstance(balance_bot, (int, float)) or not isinstance(balance_peak, (int, float)):
            raise TypeError("Balance & peak must be numeric value")
        
        if not isinstance(consecutive_losses, int):
            raise TypeError("Consecutive losses must be an integer")

        if consecutive_losses < 0:
            raise ValueError("Consecutive losses must be a non-negative integer")

        #Prevent ZeroDivisionError or negative peak anomalies
        try:
            safe_peak = max(balance_peak, balance_bot, 1e-8) if balance_peak <= 0 else balance_peak

            #if balance exceeds current peak, clamp current DD to 0
            if balance_bot >= safe_peak:
                current_drawdown = 0.0
            else:
                current_drawdown = (balance_bot - safe_peak) / safe_peak

        except ZeroDivisionError as zde:
            raise ZeroDivisionError(f"Mathematical error during drawdown calcilation: {zde}")
        
        # Use dynamic thresholds from config
        # Level based on losses:
        if consecutive_losses >= cfg.losses_level3:
            level_by_losses = 3
        elif consecutive_losses >= cfg.losses_level2:
            level_by_losses = 2
        elif consecutive_losses >= cfg.losses_level1:
            level_by_losses = 1
        else: 
            level_by_losses = 0

        #level based on drawdown:
        if current_drawdown <= -cfg.dd_level3:
            level_by_drawdown = 3
        elif current_drawdown <= -cfg.dd_level2:
            level_by_drawdown = 2
        elif current_drawdown <= -cfg.dd_level1:
            level_by_drawdown = 1
        else:
            level_by_drawdown = 0

        #Active level is the highest between losses & drawdown
        new_level = max(level_by_losses, level_by_drawdown)

        #Mapping pause candles per level using config values
        pause_map = {
            1: cfg.pause_candles_level1,
            2: cfg.pause_candles_level2,
            3: cfg.pause_candles_level3
        }
        pause_candles = pause_map.get(new_level, 0)

        return new_level, pause_candles, current_drawdown

    except (TypeError, ValueError, ZeroDivisionError) as e:
        #log or handle the exception appropriately depending on architecture standars
        print(f"[ERROR] Rist Manager Exception in evaluate_protection_system: {e}")
        raise
