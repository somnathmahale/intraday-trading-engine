import pandas as pd
import numpy as np
import yfinance as yf
import time
from datetime import datetime
import sqlite3


def safe_download(ticker, period="5d", interval="5m"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)

        if df is None or df.empty:
            return None

        df.columns = df.columns.get_level_values(0)
        df = df.dropna()

        if df.empty:
            return None

        return df

    except Exception:
        return None


# =============================
# CONFIG
# =============================
# TICKERS = ["RELIANCE.NS", "ONGC.NS", "TATAMOTORS.NS", "INDIGO.NS", "ICICIBANK.NS"]
TICKERS = ["RELIANCE.NS", "ONGC.NS", "INFY.NS", "INDIGO.NS", "ICICIBANK.NS"]

INDEX_TICKER = "^NSEI"

CAPITAL = 20000
RISK_PERCENT = 0.01
VOL_MULTIPLIER = 1.5
MAX_TRADES_PER_DAY = 1

DB_NAME = "trading_journal.db"

position = None
trades_today = 0


# =============================
# DATABASE INIT
# =============================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            ticker TEXT,
            side TEXT,
            entry REAL,
            exit REAL,
            qty INTEGER,
            pnl REAL
        )
        """
    )

    conn.commit()
    conn.close()


# =============================
# INDICATORS
# =============================
def calculate_vwap(df):
    df["cum_vol_price"] = (df["Close"] * df["Volume"]).cumsum()
    df["cum_volume"] = df["Volume"].cumsum()
    df["VWAP"] = df["cum_vol_price"] / df["cum_volume"]
    return df


def calculate_atr(df, period=14):
    df["H-L"] = df["High"] - df["Low"]
    df["H-PC"] = abs(df["High"] - df["Close"].shift(1))
    df["L-PC"] = abs(df["Low"] - df["Close"].shift(1))
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
    df["ATR"] = df["TR"].rolling(period).mean()
    return df


def opening_range(df):
    first_30 = df.between_time("09:15", "09:45")
    return first_30["High"].max(), first_30["Low"].min()


# =============================
# NIFTY TREND
# =============================
def nifty_trend():
    df = safe_download(INDEX_TICKER, period="1d", interval="5m")

    if df.empty:
        print("NIFTY data unavailable")
        return "NEUTRAL"

    df.columns = df.columns.get_level_values(0)
    df = df.dropna()

    if df.empty:
        print("NIFTY data empty after cleaning")
        return "NEUTRAL"

    df = calculate_vwap(df)

    latest = df.iloc[-1]

    close_price = latest["Close"]
    vwap_price = latest["VWAP"]

    if close_price > vwap_price:
        return "BULLISH"
    else:
        return "BEARISH"


# =============================
# SCAN MARKET
# =============================
def scan_market():
    global position, trades_today

    trade_found = False

    if trades_today >= MAX_TRADES_PER_DAY:
        return

    now = datetime.now().time()

    if now.hour > 11 or (now.hour == 11 and now.minute > 15):
        print("Scan window closed.")
        return

    market_bias = nifty_trend()
    print("NIFTY Bias:", market_bias)

    for ticker in TICKERS:
        print("Scanning:", ticker)

        df = safe_download(ticker)

        if df.empty:
            print(f"Skipping {ticker} - no data returned")
            continue

        df.columns = df.columns.get_level_values(0)
        df = df.dropna()

        if df.empty:
            print(f"Skipping {ticker} - empty after cleaning")
            continue

        df = calculate_vwap(df)
        df = calculate_atr(df)

        or_high, or_low = opening_range(df)

        latest = df.iloc[-1]

        avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
        # --- DEBUG: explain why trade may be rejected ---
        """
        price = latest["Close"]
        vwap = latest["VWAP"]

        buy_break = price > or_high
        sell_break = price < or_low
        vwap_buy_ok = price > vwap
        vwap_sell_ok = price < vwap
        vol_ok = latest["Volume"] >= VOL_MULTIPLIER * avg_vol

        print(
            f"{ticker} | Price:{price:.2f} ORH:{or_high:.2f} ORL:{or_low:.2f} "
            f"VWAP:{vwap:.2f} VolOK:{vol_ok} "
            f"BuyBreak:{buy_break} SellBreak:{sell_break} "
            f"VWAPBuy:{vwap_buy_ok} VWAPSell:{vwap_sell_ok}"
        )
        """

        if latest["Volume"] < VOL_MULTIPLIER * avg_vol:
            continue

        risk_amount = CAPITAL * RISK_PERCENT

        # BUY CONDITION
        if (
            latest["Close"] > or_high
            and latest["Close"] > latest["VWAP"]
            and market_bias == "BULLISH"
        ):

            entry = latest["Close"]
            stop = entry - latest["ATR"]

            risk = entry - stop

            qty = int(risk_amount / risk)

            if qty > 0:
                create_position(ticker, "BUY", entry, stop, qty, risk)
                trade_found = True
                return

        # SELL CONDITION
        if (
            latest["Close"] < or_low
            and latest["Close"] < latest["VWAP"]
            and market_bias == "BEARISH"
        ):

            entry = latest["Close"]
            stop = entry + latest["ATR"]

            risk = stop - entry

            qty = int(risk_amount / risk)

            if qty > 0:
                create_position(ticker, "SELL", entry, stop, qty, risk)
                trade_found = True
                return

    if not trade_found:
        print("\nNO TRADE SIGNAL for today")


# =============================
# CREATE POSITION
# =============================
def create_position(ticker, side, entry, stop, qty, risk):
    global position, trades_today

    position = {
        "ticker": ticker,
        "side": side,
        "entry": entry,
        "stop": stop,
        "target": entry + 2 * risk if side == "BUY" else entry - 2 * risk,
        "qty": qty,
        "risk": risk,
        "breakeven": False,
    }

    trades_today += 1

    print("\nTRADE SIGNAL")
    print(position)
    print("Execute manually via Zerodha.")


# =============================
# MONITOR POSITION
# =============================
def monitor():
    global position

    while position:

        df = safe_download(ticker)

        if df.empty:
            print("Waiting for data...")
            time.sleep(60)
            continue

        df.columns = df.columns.get_level_values(0)

        df = calculate_vwap(df)

        latest = df.iloc[-1]

        price = latest["Close"]
        vwap = latest["VWAP"]

        # Move stop to breakeven
        if not position["breakeven"]:

            if (
                position["side"] == "BUY"
                and price >= position["entry"] + position["risk"]
            ):
                position["stop"] = position["entry"]
                position["breakeven"] = True

            if (
                position["side"] == "SELL"
                and price <= position["entry"] - position["risk"]
            ):
                position["stop"] = position["entry"]
                position["breakeven"] = True

        exit_trade = False

        if position["side"] == "BUY":

            if price <= position["stop"] or price < vwap:
                exit_trade = True

        else:

            if price >= position["stop"] or price > vwap:
                exit_trade = True

        if exit_trade:

            log_trade(price)

            position = None

            break

        time.sleep(60)


# =============================
# LOG TRADE
# =============================
def log_trade(exit_price):
    pnl = (
        (exit_price - position["entry"]) * position["qty"]
        if position["side"] == "BUY"
        else (position["entry"] - exit_price) * position["qty"]
    )

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        "INSERT INTO trades (date,ticker,side,entry,exit,qty,pnl) VALUES (?,?,?,?,?,?,?)",
        (
            str(datetime.now()),
            position["ticker"],
            position["side"],
            position["entry"],
            exit_price,
            position["qty"],
            pnl,
        ),
    )

    conn.commit()
    conn.close()

    print("Trade Logged | PnL:", round(pnl, 2))


# =============================
# MAIN
# =============================
if __name__ == "__main__":
    init_db()
    scan_market()

    if position:
        monitor()
