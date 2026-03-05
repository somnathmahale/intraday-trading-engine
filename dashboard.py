import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

conn = sqlite3.connect("trading_journal.db")
df = pd.read_sql_query("SELECT * FROM trades", conn)
conn.close()

if len(df) == 0:
    print("No trades logged yet.")
    exit()

df["CumulativePnL"] = df["pnl"].cumsum()

wins = df[df["pnl"] > 0]
losses = df[df["pnl"] < 0]

win_rate = len(wins) / len(df)
avg_win = wins["pnl"].mean() if len(wins) > 0 else 0
avg_loss = losses["pnl"].mean() if len(losses) > 0 else 0
expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

roll_max = df["CumulativePnL"].cummax()
drawdown = df["CumulativePnL"] - roll_max

print("------ PERFORMANCE SUMMARY ------")
print("Total Trades:", len(df))
print("Win Rate:", round(win_rate, 2))
print("Expectancy:", round(expectancy, 2))
print("Total PnL:", round(df["pnl"].sum(), 2))
print("Max Drawdown:", round(drawdown.min(), 2))

plt.figure(figsize=(10, 5))
plt.plot(df["CumulativePnL"])
plt.title("Equity Curve")
plt.xlabel("Trade Number")
plt.ylabel("Cumulative PnL")
plt.grid(True)
plt.show()
