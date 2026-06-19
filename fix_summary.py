#!/usr/bin/env python3
"""Fix the darvax_trade_tracker.json summary calculations after price refresh."""
import json
import os

REPO = os.path.expanduser("~/workspace/stock-scanner-repo")
tracker_path = os.path.join(REPO, "darvax_trade_tracker.json")

with open(tracker_path) as f:
    tracker = json.load(f)

trades = tracker.get("trades", [])
open_trades = [t for t in trades if t.get("status") == "OPEN"]

# Calculate from trade-level data
total_invested_open = sum(t.get("investment", 0) for t in open_trades)
total_current_value = sum(t.get("current_value", 0) for t in open_trades)
cash_balance = tracker["summary"].get("cash_balance", 0)
total_holdings = len(open_trades)

# Calculate P&L properly
unrealized_pnl = sum(t.get("unrealized_pnl", 0) for t in open_trades)
total_returns_abs = round(unrealized_pnl, 2)
total_returns_pct = round((unrealized_pnl / total_invested_open) * 100, 2) if total_invested_open else 0

# Daily change (approx from updated prices)
daily_abs = sum(
    (t.get("current_price", 0) - t.get("entry_price", 0)) * t.get("quantity", 0) * t.get("daily_change_pct", 0) / 100
    for t in open_trades if t.get("daily_change_pct")
)
daily_pct = round((daily_abs / total_current_value) * 100, 2) if total_current_value else 0

# Update summary
tracker["summary"]["current_value"] = round(total_current_value + cash_balance, 2)
tracker["summary"]["total_returns_abs"] = total_returns_abs
tracker["summary"]["total_returns_pct"] = total_returns_pct
tracker["summary"]["total_holdings"] = total_holdings
tracker["summary"]["day_returns_abs"] = round(daily_abs, 2)
tracker["summary"]["day_returns_pct"] = daily_pct

# Performance section
tracker["performance"]["total_pnl"] = total_returns_abs

# Count winners/losers
winners = sum(1 for t in open_trades if t.get("unrealized_pnl", 0) > 0)
losers = sum(1 for t in open_trades if t.get("unrealized_pnl", 0) < 0)
tracker["performance"]["winning_trades"] = max(winners, tracker["performance"].get("winning_trades", 0))
tracker["performance"]["losing_trades"] = max(losers, tracker["performance"].get("losing_trades", 0))

# Recalculate win rate
total_closed = tracker["performance"].get("closed_trades", 0)
total_wins = tracker["performance"].get("winning_trades", 0)
total_losses = tracker["performance"].get("losing_trades", 0)
tracker["performance"]["win_rate"] = round((total_wins / (total_wins + total_losses)) * 100, 1) if (total_wins + total_losses) > 0 else 0

# Best/worst performers
if open_trades:
    best = max(open_trades, key=lambda t: t.get("unrealized_pnl_pct", -999))
    worst = min(open_trades, key=lambda t: t.get("unrealized_pnl_pct", 999))
    tracker["performance"]["best_performer"] = f"{best.get('stock_name', best.get('stock','?'))} ({best.get('unrealized_pnl_pct', 0):+.2f}%)"
    tracker["performance"]["worst_performer"] = f"{worst.get('stock_name', worst.get('stock','?'))} ({worst.get('unrealized_pnl_pct', 0):+.2f}%)"

with open(tracker_path, "w") as f:
    json.dump(tracker, f, indent=2)

print("✅ Summary fixed!")
print(f"   Current portfolio value: ₹{total_current_value + cash_balance:,.2f}")
print(f"   Total invested (open):   ₹{total_invested_open:,.2f}")
print(f"   Unrealized P&L:          ₹{total_returns_abs:,.2f}")
print(f"   Return:                  {total_returns_pct:+.2f}%")
print(f"   Holdings:                {total_holdings}")
print(f"   Winners/Losers:          {winners}/{losers}")
print(f"   Best:                    {tracker['performance']['best_performer']}")
print(f"   Worst:                   {tracker['performance']['worst_performer']}")
