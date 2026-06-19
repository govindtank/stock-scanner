#!/usr/bin/env python3
"""Refresh current prices in darvax_trade_tracker.json and other data files with live yfinance data."""
import sys
import os
import json
import yfinance as yf

REPO = os.path.expanduser("~/workspace/stock-scanner-repo")
print("🔄 Refreshing current prices from live market...")

# 1. Update darvax_trade_tracker.json
tracker_path = os.path.join(REPO, "darvax_trade_tracker.json")
if os.path.exists(tracker_path):
    with open(tracker_path) as f:
        tracker = json.load(f)
    
    trades = tracker.get("trades", [])
    updated_count = 0
    total_recalc = 0.0
    
    for t in trades:
        stock = t.get("stock", "")
        if not stock:
            continue
        try:
            ticker = yf.Ticker(stock)
            hist = ticker.history(period="2d")
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                prev_close = float(hist['Close'].iloc[-2]) if len(hist) >= 2 else current_price
                day_change_pct = ((current_price - prev_close) / prev_close) * 100
                
                old_price = t.get("current_price")
                t["current_price"] = round(current_price, 2)
                t["daily_change_pct"] = round(day_change_pct, 2)
                
                # Recalculate unrealized P&L
                entry = t.get("entry_price", 0)
                qty = t.get("quantity", 0)
                investment = t.get("investment", entry * qty)
                if entry and entry > 0:
                    current_value = round(current_price * qty, 2)
                    t["current_value"] = current_value
                    unrealized_pnl = round(current_value - investment, 2)
                    unrealized_pnl_pct = round(((current_price - entry) / entry) * 100, 2)
                    t["unrealized_pnl"] = unrealized_pnl
                    t["unrealized_pnl_pct"] = unrealized_pnl_pct
                    total_recalc += unrealized_pnl
                
                print(f"  {stock:20s} ₹{old_price:>8.2f} → ₹{current_price:>8.2f} ({day_change_pct:+.2f}%)")
                updated_count += 1
        except Exception as e:
            print(f"  ⚠️ {stock}: {e}")
    
    # Update summary performance
    if updated_count > 0:
        summary = tracker.get("summary", {})
        total_value = sum(t.get("current_value", 0) for t in trades if t.get("status") == "OPEN")
        total_invested = sum(t.get("investment", 0) for t in trades if t.get("status") == "OPEN")
        cash_balance = summary.get("cash_balance", 0)
        
        summary["current_value"] = round(total_value, 2)
        total_returns_abs = round(total_value + cash_balance - total_invested, 2)
        total_returns_pct = round((total_returns_abs / total_invested) * 100, 2) if total_invested else 0
        
        summary["total_returns_abs"] = total_returns_abs
        summary["total_returns_pct"] = total_returns_pct
        
        perf = tracker.get("performance", {})
        perf["total_pnl"] = round(total_returns_abs, 2)
        
        # Refresh NIFTY too
        try:
            nifty = yf.Ticker("^NSEI")
            n_data = nifty.history(period="2d")
            if not n_data.empty:
                summary["nifty_50"] = round(float(n_data['Close'].iloc[-1]), 2)
        except:
            pass
        
        tracker["last_updated"] = __import__('datetime').datetime.now().isoformat()
        
        with open(tracker_path, "w") as f:
            json.dump(tracker, f, indent=2)
        
        print(f"\n✅ Updated {updated_count}/{len(trades)} trades with live prices")
        print(f"   Total unrealized P&L: ₹{total_recalc:,.2f}")
    else:
        print("  ℹ️ No trades updated")

# 2. Update darvas_state.json with current prices (using yfinance for held stocks)
darvas_path = os.path.join(REPO, "darvas_state.json")
if os.path.exists(darvas_path):
    with open(darvas_path) as f:
        darvas = json.load(f)
    
    positions = darvas.get("positions", [])
    updated = 0
    for pos in positions:
        symbol = pos.get("symbol", "")
        if not symbol:
            continue
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                entry = pos.get("entry_price", 0)
                if entry and entry > 0:
                    pnl_pct = ((current_price - entry) / entry) * 100
                    pos["pnl_pct"] = round(pnl_pct, 2)
                    pos["current_price"] = round(current_price, 2)
                    qty = pos.get("quantity", 0)
                    pos["pnl"] = round((current_price - entry) * qty, 2)
                    updated += 1
        except:
            pass
    
    if updated > 0:
        # Recalc total value
        total_pos_value = sum(
            pos.get("current_price", pos.get("entry_price", 0)) * pos.get("quantity", 0)
            for pos in positions
        )
        cash = darvas.get("cash", 0)
        darvas["total_value"] = round(total_pos_value + cash, 2)
        darvas["total_pnl"] = round(darvas["total_value"] - 100000, 2)
        darvas["last_updated"] = __import__('datetime').datetime.now().isoformat()
        
        with open(darvas_path, "w") as f:
            json.dump(darvas, f, indent=2)
        print(f"\n✅ Updated {updated}/{len(positions)} Darvas positions with live prices")

print("\n✅ Price refresh complete!")
