# Contexto del Proyecto: Backtesting Engine Cuantitativo BTC/USD[cite: 1]

## 1. Objetivo Principal y Restricciones de Ingeniería
* **Objetivo**: Desarrollar un motor de backtesting en Python, modular y de alto rendimiento, para evaluar estrategias cuantitativas en Futuros Perpetuos de BTC/USD (específicamente simulando Hyperliquid)[cite: 1].
* **Metodología**: Enfoque "testing-first" estricto utilizando `pytest` para garantizar una ejecución determinista[cite: 1].
* **Cero Lookahead Bias**: El sistema debe asegurar mediante ventanas históricas estrictas que los indicadores solo consuman datos disponibles en el tiempo $t$[cite: 1].
* **Microestructura Realista**: El simulador debe descontar *maker/taker fees* (comisiones) y el *slippage* (deslizamiento) de ejecución[cite: 1].

## 2. Lógica de la Estrategia (Reglas de Negocio)
* **Direccionalidad**: La estrategia debe ser estrictamente **Long-Only** (solo posiciones largas)[cite: 1].
* **Timeframes**: Operar únicamente en temporalidades altas (**4H y 1D**) para evadir el ruido intradía[cite: 1].
* **Filtro de Entrada (ADX)**: Las posiciones solo se abren cuando la fuerza de la tendencia supera los umbrales base dictados por el Average Directional Index (ADX)[cite: 1].
* **Gestión de Salida (ATR Trailing Stop)**: Los stop-loss deben ser dinámicos basados en la volatilidad calculada mediante el Average True Range (ATR); se expanden en movimientos fuertes y se ajustan en consolidaciones[cite: 1].

## 3. Arquitectura del Sistema (Flujo Unidireccional)
El sistema debe desacoplarse en los siguientes módulos independientes[cite: 1]:
1. **Datos Históricos**: Ingesta de datos OHLCV (`data_loader.py`)[cite: 1].
2. **Indicadores Técnicos**: Cálculo de ADX, ATR y Medias Móviles (`indicators.py`)[cite: 1].
3. **Generador de Señales**: Evaluación de reglas Long-Only[cite: 1].
4. **Módulo de Ejecución y Riesgo**: Gestión de entradas, posiciones, simulación de comisiones y trailing stops (`position.py`, `risk_manager.py`)[cite: 1].
5. **Suite de Analíticas**: Cálculo de métricas de rendimiento[cite: 1].

## 4. Fórmulas de Analítica Cuantitativa a Implementar
El motor debe calcular y devolver las siguientes métricas al finalizar el backtest[cite: 1]:

* **Profit Factor (PF)**[cite: 1]: 
  $$PF = \frac{\sum \text{Gross Profits}}{\sum |\text{Gross Losses}|}$$

* **Maximum Drawdown (MDD)**[cite: 1]: 
  $$MDD = \max_{t \in [0,T]} \left( \frac{P_{peak} - P_t}{P_{peak}} \right)$$

* **Win Rate (WR)**[cite: 1]: 
  $$WR = \left( \frac{N_{\text{winning trades}}}{N_{\text{total trades}}} \right) \times 100$$

## 5. Estructura de Directorios (Tree)
Por favor, genera y organiza el código respetando estrictamente esta estructura de archivos[cite: 1]:

backtest-btc-trading-bot/
├── data/
│   └── btc.csv
├── src/
│   ├── backtester/
│   │   ├── engine/
│   │   ├── __init__.py
│   │   ├── position.py
│   │   └── risk_manager.py
│   ├── __init__.py
│   ├── config.py
│   ├── data_loader.py
│   └── indicators.py
├── tests/
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── test_indicators.py
│   ├── test_position.py
│   └── test_risk_manager.py
├── main.py
└── requirements.txt