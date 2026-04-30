"""
Darvas Breakout Scanner for Indian Stock Market
================================================

A comprehensive tool for detecting Darvas box breakouts in Indian stocks.
Uses yfinance (free, no API key required) to fetch live NSE/BSE data.

Features:
- Real-time breakout detection using Darvas theory
- Portfolio monitoring for wishlisted stocks
- Visual alerts and signals
- Auto-monitoring with configurable intervals
- Tutorial documentation included
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from darvas_detector import IndianStockMonitor, DarvasBoxDetector


# Default Indian stocks to monitor (popular NSE stocks)
DEFAULT_STOCKS = [
    'RELIANCE.NS',   # Reliance Industries
    'TCS.NS',        # Tata Consultancy Services
    'INFY.NS',       # Infosys
    'HDFCBANK.NS',   # HDFC Bank
    'ICICIBANK.NS',  # ICICI Bank
    'SBIN.NS',       # State Bank of India
    'BHARTIARTL.NS', # Bharti Airtel
    'ITC.NS',        # ITC Limited
    'KOTAKBANK.NS',  # Kotak Mahindra Bank
    'AXISBANK.NS',   # Axis Bank
]

# Watchlist configuration
WATCHLIST_FILE = '.watchlist.json'


def load_watchlist() -> list:
    """Load user's watchlist from file."""
    try:
        with open(WATCHLIST_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return DEFAULT_STOCKS.copy()


def save_watchlist(stocks: list):
    """Save watchlist to file."""
    with open(WATCHLIST_FILE, 'w') as f:
        json.dump(stocks, f, indent=2)


class DarvasScanner:
    """Main scanner class for monitoring Indian stocks."""
    
    def __init__(self, interval_minutes=15):
        """
        Initialize the scanner.
        
        Args:
            interval_minutes: How often to scan (default 15 minutes)
        """
        self.monitor = IndianStockMonitor()
        self.interval_minutes = interval_minutes
        self.wishlist = load_watchlist()
    
    def run_once(self) -> dict:
        """Run a single scan of all stocks in watchlist."""
        print(f"\n{'='*60}")
        print(f"Darvas Breakout Scanner - Scan at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}\n")
        
        results = {}
        for stock in self.wishlist:
            print(f"📊 Analyzing {stock}...", end=" ")
            try:
                result = self.monitor.analyze_stock(stock)
                if result and 'error' not in result:
                    results[stock] = result
                    
                    # Print if there's an active breakout
                    if result.get('breakouts'):
                        for b in result['breakouts']:
                            signal = b['signal_strength']
                            if signal == 'STRONG':
                                print(f"🚨 BREAKOUT DETECTED! {stock} at ₹{result['current_price']:.2f}")
                                print(f"   Box High: ₹{result.get('active_box_high'):.2f}")
                                print(f"   Breakout: {b['breakout_pct']:.1f}% | Volume: {b['volume_spike']:.0f}%")
                                print(f"   Signal: {signal}")
                        continue
                    
                    if result.get('boxes_detected', 0) > 0 and not result['breakouts']:
                        print(f"⚠️  Box Complete - Waiting for breakout on ₹{result.get('active_box_high'):.2f}")
                    else:
                        print(f"✅ No active box")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown')}")
                    
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
        
        return results
    
    def save_results(self, results: dict):
        """Save scan results to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'analysis_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📁 Results saved to {filename}")
    
    def get_watchlist(self) -> list:
        """Return current watchlist."""
        return self.wishlist.copy()
    
    def set_watchlist(self, stocks: list):
        """Set new watchlist."""
        self.wishlist = stocks
        save_watchlist(stocks)
        print(f"\n✅ Watchlist updated to {len(stocks)} stocks")


# Initialize scanner
scanner = DarvasScanner(interval_minutes=15)

if __name__ == '__main__':
    # Display current watchlist
    print("Current Watchlist:")
    for stock in scanner.wishlist:
        print(f"  • {stock}")
    
    # Run initial scan
    results = scanner.run_once()
    
    # Save results
    if results:
        scanner.save_results(results)
    
    print("\n" + "="*60)
    print("Darvas Breakout Scanner Ready!")
    print("="*60)
    print("\nTutorial & Usage:")
    print("1. Edit .watchlist.json to add/remove stocks")
    print("2. Run this script for scans (every 15 minutes)")
    print("3. Set up auto-scan with: python scanner.py &> log.txt | tail -f")
    print("\nDarvas Theory Tutorial:")
    print("-" * 40)
    print("""
DARVAS BOX METHOD TUTORIAL

Step 1: Build Your Box
├─ Buy on pullbacks to box highs
├─ Set stops below box lows (3% - 5%)
└─ Track daily high/low consolidations

Step 2: Identify Breakouts
├─ Price must break above box high by 2-3%
├─ Volume must be 150%+ of average
└─ Minimum gain from previous box (2-3 days)

Step 3: Take Profits
├─ First target: Previous resistance levels  
├─ Second target: 1.618x move above breakout
└─ Trail stops to protect gains

Key Rules:
• Never hold through earnings
• Always use stop-loss (below box low)
• Exit quickly on weak volume breakouts
• Focus on high-volume, liquid stocks
""")
    print("="*60)
