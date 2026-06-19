#!/usr/bin/env python3
"""Update darvax_trade_tracker.json with live market prices from yfinance."""
import yfinance as yf
import json
import os
from datetime import datetime, timezone

TRACKER_PATH = "/Users/govind/workspace/stock-scanner-repo/darvax_trade_tracker.json"

def update_prices():
    with open(TRACKER_PATH) as f:
        tracker = json.load(f)

    updated_count = 0
    failed = []

    for t in tracker["trades"]:
        symbol = t["stock"]
        try:
            data = yf.download(symbol, period="5d", interval="1d", progress=False)
            if data is not None and not data.empty:
                close_df = data["Close"]
                live_price = round(float(close_df.iloc[-1, 0]), 2)

                daily_change = 0
                if len(close_df) > 1:
                    prev_close = float(close_df.iloc[-2, 0])
                    daily_change = round((live_price - prev_close) / prev_close * 100, 2)

                qty = int(t.get("quantity", 0))
                current_value = round(live_price * qty, 2)
                investment = t.get("investment", 0)
                unrealized_pnl = round(current_value - investment, 2)
                unrealized_pnl_pct = round((unrealized_pnl / investment) * 100, 2) if investment > 0 else 0

                old_price = t["current_price"]
                t["current_price"] = live_price
                t["current_value"] = current_value
                t["daily_change_pct"] = daily_change
                t["unrealized_pnl"] = unrealized_pnl
                t["unrealized_pnl_pct"] = unrealized_pnl_pct

                if abs(live_price - old_price) > 0.5:
                    updated_count += 1
                    print(f"  {symbol:20s} \u20b9{old_price:<8.2f} \u2192 \u20b9{live_price:<8.2f} ({daily_change:+.2f}%) P&L: {unrealized_pnl_pct:+.2f}%")
                else:
                    print(f"  {symbol:20s} \u20b9{live_price:<8.2f} (unchanged)")
            else:
                failed.append(symbol)
                print(f"  {symbol:20s} No data, keeping \u20b9{t['current_price']}")
        except Exception as e:
            failed.append(symbol)
            print(f"  {symbol:20s} Error: {e}")

    # Recalc summary
    total_invested = sum(t.get("investment", 0) for t in tracker["trades"])
    total_current = sum(t.get("current_value", 0) for t in tracker["trades"])
    total_returns_abs = round(total_current - total_invested, 2)
    total_returns_pct = round((total_returns_abs / total_invested) * 100, 2) if total_invested > 0 else 0

    tracker["last_updated"] = datetime.now().isoformat()
    tracker["summary"]["current_value"] = round(total_current, 2)
    tracker["summary"]["total_returns_abs"] = total_returns_abs
    tracker["summary"]["total_returns_pct"] = total_returns_pct
    tracker["summary"]["last_updated"] = datetime.now(timezone.utc).isoformat()

    best = max(tracker["trades"], key=lambda x: x.get("unrealized_pnl_pct", 0))
    worst = min(tracker["trades"], key=lambda x: x.get("unrealized_pnl_pct", 0))
    winning = sum(1 for t in tracker["trades"] if t.get("unrealized_pnl", 0) > 0)
    losing = sum(1 for t in tracker["trades"] if t.get("unrealized_pnl", 0) < 0)

    tracker["performance"]["total_pnl"] = total_returns_abs
    tracker["performance"]["winning_trades"] = winning
    tracker["performance"]["losing_trades"] = losing
    tracker["performance"]["win_rate"] = round((winning / len(tracker["trades"])) * 100, 1)
    tracker["performance"]["best_performer"] = f"{best.get('stock_name', best['stock'])} (+{best['unrealized_pnl_pct']:.2f}%)"
    tracker["performance"]["worst_performer"] = f"{worst.get('stock_name', worst['stock'])} ({worst['unrealized_pnl_pct']:.2f}%)"

    # Nifty
    try:
        nifty = yf.download("^NSEI", period="2d", interval="1d", progress=False)
        if nifty is not None and not nifty.empty:
            close_df = nifty["Close"]
            tracker["summary"]["nifty_50"] = round(float(close_df.iloc[-1, 0]), 2)
    except:
        pass

    with open(TRACKER_PATH, "w") as f:
        json.dump(tracker, f, indent=2, default=str)

    # Also update tracked_stocks.json prices
    try:
        tracked_path = os.path.join(os.path.dirname(TRACKER_PATH), "tracked_stocks.json")
        with open(tracked_path) as f:
            tracked = json.load(f)
        now_ts = datetime.now().isoformat()
        for s in tracked.get("stocks", []):
            t = s["ticker"]
            if t in tracked.get("prices", {}):
                continue  # skip, keep existing prices from NSE fetch
        # Try to fetch any stocks with zero price
        for s in tracked.get("stocks", []):
            t = s["ticker"]
            p = tracked.get("prices", {}).get(t, {})
            if p.get("price", 0) == 0:
                try:
                    data = yf.download(t, period="2d", interval="1d", progress=False)
                    if data is not None and not data.empty:
                        close_df = data["Close"]
                        live_price = round(float(close_df.iloc[-1, 0]), 2)
                        daily_change = 0
                        if len(close_df) > 1:
                            prev_close = float(close_df.iloc[-2, 0])
                            daily_change = round((live_price - prev_close) / prev_close * 100, 2)
                        tracked.setdefault("prices", {})[t] = {
                            "price": live_price,
                            "daily_change_pct": daily_change,
                            "updated_at": now_ts
                        }
                        print(f"  [Tracked] {t:20s} ₹{live_price:<8.2f} ({daily_change:+.2f}%)")
                except:
                    pass
        tracked["last_updated"] = now_ts
        with open(tracked_path, "w") as f:
            json.dump(tracked, f, indent=2)
        print(f"✅ Tracked stocks prices updated")
    except Exception as e:
        print(f"⚠️ Skipped tracked_stocks update: {e}")

    print(f"\n\u2705 Updated {updated_count} prices | {len(failed)} kept unchanged")
    print(f"\U0001f4b0 Portfolio: \u20b9{total_invested:,.2f} \u2192 \u20b9{total_current:,.2f} ({total_returns_pct:+.2f}%)")
    print(f"\U0001f4c8 Winning: {winning} | Losing: {losing} | Best: {best['stock']} (+{best['unrealized_pnl_pct']:.1f}%)")

if __name__ == "__main__":
    update_prices()
