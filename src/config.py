# src/config.py
from dataclasses import dataclass

@dataclass
class BacktestConfig:
    # --- files & data ---
    csv_filename: str = "btc.csv"
    timeframe: str = "4h"

    # --- technical indicators ---
    ema_fast_period: int = 50
    ema_slow_period: int = 200
    atr_period: int = 14
    atr_sma_period: int = 14
    adx_period: int = 14
    adx_threshold: float = 25.0

    # --- protection system (Risk Manager) ---
    loss_level_1: int = 2
    loss_level_2: int = 3
    loss_level_3: int = 4
    
    dd_level_1: float = 0.15
    dd_level_2: float = 0.25
    dd_level_3: float = 0.40

    pause_candles_l1: int = 3   # 12h
    pause_candles_l2: int = 12  # 48h
    pause_candles_l3: int = 30  # 5 días