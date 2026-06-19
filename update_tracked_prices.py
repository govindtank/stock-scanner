#!/usr/bin/env python3
"""Fetch live prices for tracked stocks (watchlist) and update tracked_stocks.json."""
import yfinance as yf
import json
from datetime import datetime

TRACKED_PATH = "/Users/govind/workspace/stock-scanner-repo/tracked_stocks.json"

def update_tracked_prices():
    with open(TRACKED_PATH) as f:
        data = json.load(f)

    prices = {}
    failed = []

    for s in data["stocks"]:
        ticker = s["ticker"]
        try:
            df = yf.download(ticker, period="5d", interval="1d", progress=False)
            if df is not None and not df.empty:
                close_df = df["Close"]
                live_price = round(float(close_df.iloc[-1, 0]), 2)
                daily_change = 0
                if len(close_df) > 1:
                    prev_close = float(close_df.iloc[-2, 0])
                    daily_change = round((live_price - prev_close) / prev_close * 100, 2)
                prices[ticker] = {
                    "price": live_price,
                    "daily_change_pct": daily_change,
                    "updated_at": datetime.now().isoformat()
                }
                print(f"  {ticker:20s} ₹{live_price:<8.2f} ({daily_change:+.2f}%)")
            else:
                prices[ticker] = {"price": 0, "daily_change_pct": 0, "error": "No data"}
                failed.append(ticker)
                print(f"  {ticker:20s} No data")
        except Exception as e:
            prices[ticker] = {"price": 0, "daily_change_pct": 0, "error": str(e)}
            failed.append(ticker)
            print(f"  {ticker:20s} Error: {e}")

    data["prices"] = prices
    data["last_updated"] = datetime.now().isoformat()

    with open(TRACKED_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"\n✅ Updated {len(prices)} tracked stocks | {len(failed)} failed")
    return prices, failed

if __name__ == "__main__":
    update_tracked_prices()
