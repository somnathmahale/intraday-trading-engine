# Intraday Trading Engine (NSE)

A rule-based intraday trading engine for Indian equities using an
**Opening Range Breakout (ORB)** strategy combined with **VWAP
alignment, volume confirmation, and market bias filtering**.

The system scans selected NSE stocks after the opening range forms and
generates disciplined **BUY / SELL signals** with defined risk
parameters.

Currently the engine generates **signals only**, and trades are executed
manually through the Zerodha UI. The goal is to validate the strategy
before integrating broker APIs.

------------------------------------------------------------------------

# Strategy Overview

The engine follows a structured intraday framework based on market
microstructure.

**Key concept:**\
Trade range expansion after the first 30 minutes of the market session.

The opening phase typically establishes early price discovery. Breakouts
from this range often trigger directional momentum.

Strategy confirmations:

-   Opening Range Breakout (09:15--09:45)
-   VWAP alignment
-   Volume expansion
-   NIFTY market bias filter
-   ATR based stop loss

------------------------------------------------------------------------

# Trading Logic

## Opening Range

The engine calculates the high and low between:

    09:15 – 09:45

These levels form the **Opening Range High (ORH)** and **Opening Range
Low (ORL)**.

------------------------------------------------------------------------

## Market Bias Filter

Market direction is determined using NIFTY VWAP.

Bullish Bias:

    NIFTY Close > NIFTY VWAP

Bearish Bias:

    NIFTY Close < NIFTY VWAP

Trades are only taken **in the direction of the broader market bias**.

------------------------------------------------------------------------

## Volume Confirmation

Breakouts must show participation.

    Volume > 1.5 × 20-period average volume

This helps filter weak or false breakouts.

------------------------------------------------------------------------

## Entry Rules

### BUY Setup

    Price > Opening Range High
    Price > VWAP
    Market Bias = Bullish
    Volume Confirmation

### SELL Setup

    Price < Opening Range Low
    Price < VWAP
    Market Bias = Bearish
    Volume Confirmation

------------------------------------------------------------------------

# Risk Management

Risk management is built directly into the position sizing logic.

    Risk per trade = 1% of capital

Stop loss is calculated using **ATR (Average True Range)**.

Example:

    Entry = ₹500
    ATR = ₹5
    Stop Loss = Entry − ATR

Position quantity is dynamically calculated so that the maximum loss per
trade remains within the defined risk.

------------------------------------------------------------------------

# Exit Rules

Trades are exited when:

-   Stop loss is hit
-   Price crosses VWAP against the position
-   Break-even adjustment after reaching 1R profit

Trades are logged automatically to the database.

------------------------------------------------------------------------

# Stock Universe

Current trading universe:

    RELIANCE.NS
    ONGC.NS
    INDIGO.NS
    ICICIBANK.NS

These stocks were selected because they generally have:

-   High liquidity
-   Strong institutional participation
-   Reliable intraday volatility

------------------------------------------------------------------------

# Project Structure

    intraday_trading/
    │
    ├── engine_v3.py        # Main trading engine
    ├── dashboard.py        # Performance dashboard
    ├── trading_journal.db  # SQLite trade log
    ├── README.md
    └── venv/               # Python virtual environment

------------------------------------------------------------------------

# Technology Stack

-   Python
-   Pandas
-   NumPy
-   yfinance (market data)
-   SQLite (trade logging)

------------------------------------------------------------------------

# Setup Instructions

## Clone Repository

    git clone https://github.com/YOUR_USERNAME/intraday-trading-engine.git
    cd intraday-trading-engine

## Create Virtual Environment

    python3 -m venv venv
    source venv/bin/activate

## Install Dependencies

    pip install pandas numpy yfinance

## Run the Engine

    python engine_v3.py

------------------------------------------------------------------------

# Recommended Daily Execution Routine

1.  Run the engine around **09:46 AM IST**
2.  Observe the terminal output
3.  Execute signals manually via Zerodha
4.  Immediately place **SL‑M stop-loss order**

------------------------------------------------------------------------

# Example Output

    NIFTY Bias: BEARISH
    Scanning: RELIANCE.NS
    Scanning: ONGC.NS
    Scanning: INDIGO.NS
    Scanning: ICICIBANK.NS

If a setup appears:

    TRADE SIGNAL
    {'ticker': 'ONGC.NS', 'side': 'SELL', 'entry': 282.1, 'stop': 284.4, 'qty': 85}
    Execute manually via Zerodha.

------------------------------------------------------------------------

# Trade Logging

Trades are automatically stored in:

    trading_journal.db

Fields stored:

-   Date
-   Ticker
-   Trade side
-   Entry price
-   Exit price
-   Quantity
-   Profit/Loss

------------------------------------------------------------------------

# Dashboard

To view performance summary:

    python dashboard.py

The dashboard helps track:

-   Trade history
-   PnL
-   Strategy performance

------------------------------------------------------------------------

# Future Improvements

Potential upgrades for this system:

-   Zerodha Kite API integration
-   Automated order execution
-   Telegram / WhatsApp alerts
-   Advanced backtesting
-   Sector momentum filters
-   Multi‑ticker scanning engine

------------------------------------------------------------------------

# Disclaimer

This project is for **educational and research purposes only**.

Trading financial markets involves risk. Past performance does not
guarantee future results.
