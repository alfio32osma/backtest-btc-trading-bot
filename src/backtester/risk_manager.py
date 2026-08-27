def evaluate_protection_system(balance_bot: float, balance_peak: float, consecutive_losses: int):
    """ 
    Evaluates consecutive loss streaks and drawdown thresholds to determinate
    the active pause level for the capital protection system
    """
    #Input validation & error handling:
    if not isinstance(balance_bot, (int, float)) or not isinstance(balance_peak, (int, float)):
        raise TypeError("Balance & peak must be numeric value")
    
    if not isinstance(consecutive_losses, int) or consecutive_losses < 0:
        raise ValueError("Consecutive losses must be a non-negative integer")

    #Prevent ZeroDivisionError or negative peak anomalies
    if balance_peak <= 0:
        balance_peak = max(balance_bot, 1e-8)

    #If balance exceeds curret peak, clamp current DD to 0
    if balance_bot >= balance_peak:
        current_drawdown = 0.0
    else:
        current_drawdown = (balance_bot - balance_peak) / balance_peak
        
    #Configured thresholds
    LOSSES_LEVEL1, LOSSES_LEVEL2, LOSSES_LEVEL3 = 2, 3, 4
    DD_LEVEL1, DD_LEVEL2, DD_LEVEL3 = 0.15, 0.25, 0.40

    #Calculate current drawdown
    current_drawdown = (balance_bot - balance_peak) / balance_peak

    #Level based on losses:
    if consecutive_losses >= LOSSES_LEVEL3:
        level_by_losses = 3
    elif consecutive_losses >= LOSSES_LEVEL2:
        level_by_losses = 2
    elif consecutive_losses >= LOSSES_LEVEL1:
        level_by_losses = 1
    else: 
        level_by_losses = 0

    #level based on drawdown:
    if current_drawdown <= -DD_LEVEL3:
        level_by_drawdown = 3
    elif current_drawdown <= -DD_LEVEL2:
        level_by_drawdown = 2
    elif current_drawdown <= -DD_LEVEL1:
        level_by_drawdown = 1
    else:
        level_by_drawdown = 0

    #Active level is the highest between losses & drawdown
    new_level = max(level_by_losses, level_by_drawdown)

    #Mapping pause candles per level (1 candle = 4h)
    # level 1: 3 candles (12h) | level 2: 12 candles (48h) | level 3: 30 candles (5 days)
    pause_map = {1: 3, 2: 12, 3: 30}
    pause_candles = pause_map.get(new_level, 0)

    return new_level, pause_candles, current_drawdown
