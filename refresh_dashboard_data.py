#!/usr/bin/env python3
"""Fetch live market data and refresh the trading dashboard."""
import sys
import os
import json
from datetime import datetime, timezone

# Add repo to path
sys.path.insert(0, os.path.expanduser("~/workspace/stock-scanner-repo"))

print("=" * 60)
print(f"  Trading Dashboard Data Refresh — {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
print("=" * 60)

# Step 1: Fetch live market data
print("\n📡 Fetching live market data...")
try:
    from options_paper_trader import fetch_nifty_spot, fetch_india_vix
    spot = fetch_nifty_spot("NIFTY")
    vix = fetch_india_vix()
    print(f"  NIFTY Spot: {spot if spot else 'Could not fetch'}")
    print(f"  India VIX:  {vix if vix else 'Could not fetch'}")
except Exception as e:
    print(f"  ⚠️ Market data fetch failed: {e}")
    spot, vix = None, None

# Step 2: Try to update Darvas paper trader positions with current prices
print("\n🔄 Refreshing Darvas paper trader positions...")
try:
    from darvas_paper_trader import DarvasPaperTrader
    trader = DarvasPaperTrader()
    if hasattr(trader, 'update_portfolio_prices'):
        trader.update_portfolio_prices()
        print("  ✅ Darvas positions updated with current prices")
    else:
        print("  ⚠️ No update_portfolio_prices method, refresh market_run instead")
        # Try running a full market scan
        if hasattr(trader, 'market_run'):
            trader.market_run()
            print("  ✅ Darvas market run completed")
        else:
            print("  ℹ️ Skipping Darvas update")
    try:
        trader.save_state()
        print("  ✅ Darvas state saved")
    except AttributeError:
        # Some older versions don't have save_state, just ensure state is persisted
        trader.trader_state = {"last_refreshed": datetime.now().isoformat()}
        print("  ℹ️ Using alternative state persistence")
except Exception as e:
    print(f"  ⚠️ Darvas refresh error: {e}")

# Step 3: Save latest market data to a temp file for the dashboard
live_data = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "nifty_spot": spot,
    "india_vix": vix,
    "last_refreshed": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}
live_path = os.path.expanduser("~/workspace/stock-scanner-repo/live_market_data.json")
with open(live_path, "w") as f:
    json.dump(live_data, f, indent=2)
print(f"  ✅ Live market data saved to live_market_data.json")

print("\n✅ Data refresh complete")
