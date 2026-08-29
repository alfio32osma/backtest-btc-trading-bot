# 📊 BTC/USD Quantitative Backtesting Engine

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Testing](https://img.shields.io/badge/tests-pytest-green.svg)](https://docs.pytest.org/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Domain](https://img.shields.io/badge/Domain-Quantitative%20Finance-orange.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modular, high-performance Python backtesting engine built for evaluating quantitative algorithmic trading strategies on **BTC/USD Perpetual Futures**. Designed with strict software engineering standards, focusing on clean separation of concerns, zero lookahead bias, and deterministic testing.

---

## 📑 Table of Contents
- [Overview](#-overview)
- [Strategy Philosophy & Macroeconomic Rationale](#-strategy-philosophy--macroeconomic-rationale)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Quantitative Metrics & Formulation](#-quantitative-metrics--formulation)
- [Project Directory Structure](#-project-directory-structure)
- [Getting Started](#-getting-started)
- [Configuration](#-configuration)
- [Upcoming Roadmap](#-upcoming-roadmap)
- [Author \& Contact](#-author--contact)
- [License](#-license)

---

## 📌 Overview

Backtesting quantitative strategies in volatile cryptocurrency markets requires execution integrity, dynamic risk bounds, and accurate exchange cost simulations. 

This engine decouples market data ingestion, technical indicator calculation, signal generation, and performance analytics into independent, unit-tested modules. It provides quantitative developers with a flexible sandbox to evaluate strategy profitability before live deployment on decentralized exchanges like **Hyperliquid**.

---

## 🧠 Strategy Philosophy & Macroeconomic Rationale

> *"If you don't understand where money comes from and how central banks manipulate liquidity, you cannot properly engineer a quantitative strategy on a hard-money asset like Bitcoin."*

### 1. Macroeconomic Roots & The Genesis of Bitcoin
Growing up in Argentina—a nation defined by chronic monetary inflation, currency devaluations, and constant fiscal policy shifts—instilled in me an intuitive understanding of monetary fragility. 

Following the 2008 Great Financial Crisis, global central banks rescued failing financial institutions using public money, expanding sovereign debt and diluting purchasing power. Bitcoin emerged from this exact breakdown as an immutable, mathematically capped reserve asset. 

My transition from manual EUR/USD trading to automated Bitcoin quantitative modeling was driven by this core realization: **Bitcoin represents true financial sovereignty, self-custody, and decentralized market dynamics.** Real wealth creation is built on hard work, capital savings, and free-market incentives—not debt-driven fiat expansion.

### 2. Market Microstructure: The Liquidity Hunt (Sharman & Valentini Insights)
Studying top-tier algorithmic traders—such as Ivan Sharman (+400% Dow Jones algorithmic record) and proprietary firm traders like Fabio Valentini—revealed a fundamental truth about modern financial markets: **markets do not move on pure technical indicators; they move on institutional liquidity.**

* **The Retail Trap**: Institutional algorithms constantly sweep supply and demand zones to fill massive orders. When order-book liquidity thins out, stop-loss orders get triggered, causing sharp price slippage and fake breakouts.
* **The Noise Elimination**: High-frequency intraday timeframes (1M to 15M) are dominated by algorithmic noise and liquidity sweeps. Attempting to run high leverage (>5x) on these timeframes consistently leads to liquidation.
* **Higher Timeframe Solution**: To protect capital from institutional stop-hunting, this engine operates strictly on **Higher Timeframes (4H and 1D)**, trading structural macro momentum rather than intraday noise.

### 3. Core Strategy Mechanics: Long-Only & Asymmetric Compounding

* **Why Long-Only?** Bitcoin is structurally designed as an asymmetric, trend-explosive asset. Multi-directional backtesting revealed that shorting BTC during macro cycles introduces high friction, low win rates, and severe liquidation risks. Accepting localized drawdowns on pullbacks while remaining strictly **Long-Only** yielded far superior risk-adjusted returns.
* **Compound Interest Engine**: By leveraging decentralized perpetual futures (Hyperliquid) under strict risk parameters, the goal is not high-frequency gambling, but using leverage as a **long-term capital compounding engine**—turning high-probability trend expansions into exponential account growth.

### 4. Dynamic Risk & Trend Determination Engine

To solve the dynamic of leverage protection, the strategy combines two structural filters:

$$\text{Trend Determination Filter} \longrightarrow \text{ADX (Average Directional Index)}$$
$$\text{Volatility Risk Engine} \longrightarrow \text{ATR (Average True Range)}$$

* **ADX Filter**: Ensures positions are opened **only** when market determination and trend strength exceed baseline thresholds (filtering out low-volume consolidation ranges).
* **ATR Trailing Stop**: Dynamically adjusts execution stops based on real-time market volatility, expanding during explosive moves and tightening during consolidation to prevent premature liquidations.

### 5. Real-World Execution & Empirical Validation
Backtesting is an ongoing multi-year iterative process. While backtested models can show exceptional performance, real market execution is the ultimate benchmark. 

Currently, a live production instance of this strategy is deployed on **Hyperliquid** with real capital. While low-volume periods test system resilience, full empirical validation will be measured across major high-volatility macro regimes (similar to the explosive volume cycles seen in 2021).

---

## ⚡ Key Features

* **Modular Architecture**: Decoupled components for data processing, strategy logic, risk rules, and metric calculations.
* **Deterministic Execution Engine**: Built with a testing-first approach using `pytest` to guarantee calculation precision and prevent regressions.
* **Microstructure Realism**: Models exchange maker/taker fees, execution slippage, and dynamic volatility-based stops (ATR).
* **Zero Lookahead Bias**: Strict historical windowing to ensure indicators and signals only consume data available at time $t$.
* **Robust Performance Analytics**: Calculates institutional-grade quantitative metrics including Profit Factor, Maximum Drawdown (MDD), Win Rate, and Risk-Adjusted Returns.

---

## 🏗 System Architecture

The execution pipeline follows a single-direction data flow:

```text
┌─────────────────┐      ┌──────────────────────────┐      ┌──────────────────────────┐
│  Historical     │ ---> │  Technical Indicators    │ ---> │  Signal Generation Engine│
│  OHLCV Data     │      │  (ADX, ATR, Moving Avg)  │      │  (Long-Only Rules)       │
└─────────────────┘      └──────────────────────────┘      └──────────────────────────┘
                                                                        │
┌─────────────────┐      ┌──────────────────────────┐                   ▼
│  Analytics &    │ <--- │  Execution & Risk Module │ <----------------─┘
│  Metrics Suite  │      │  (Fees, Slippage, Stop)  │
└─────────────────┘      └──────────────────────────┘
```
---

## 📊 Quantitative Metrics & Formulation

The engine's evaluation suite measures strategy performance across multiple dimensions:

### 1. Profit Factor ($PF$)
Measures the ratio of gross profits to gross losses:
$$PF = \frac{\sum \text{Gross Profits}}{\sum \vert{}\text{Gross Losses}\vert{}}$$

### 2. Maximum Drawdown ($MDD$)
Calculates the peak-to-trough decline during a specific record period:
$$MDD = \max_{t \in [0, T]} \left( \frac{P_{peak} - P_t}{P_{peak}} \right)$$

### 3. Win Rate ($WR$)
The percentage of total closed trades resulting in positive net PnL:
$$WR = \frac{N_{winning\_trades}}{N_{total\_trades}} \times 100$$

---

## 📂 Project Directory Structure

```text
backtest-btc-trading-bot/
├── .vscode/               # Editor configurations & settings
├── data/                  # Historical OHLCV datasets
│   └── btc.csv
├── src/                   # Core source code engine
│   ├── backtester/        # Backtesting module architecture
│   │   ├── engine/        # Execution & simulation engine
│   │   ├── __init__.py
│   │   ├── position.py    # Position tracking & management logic
│   │   └── risk_manager.py # Risk control, trailing stops & stop losses
│   ├── __init__.py
│   ├── config.py          # Strategy parameters & global configuration
│   ├── data_loader.py     # Data ingestion & cleaning pipelines
│   └── indicators.py      # Technical indicators (ADX, ATR, Moving Averages)
├── tests/                 # Unit & integration test suite
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── test_indicators.py
│   ├── test_position.py
│   └── test_risk_manager.py
├── .gitignore
├── main.py                # Main script execution entry point
├── README.md              # Project documentation
└── requirements.txt       # Project dependencies