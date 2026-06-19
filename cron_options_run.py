#!/usr/bin/env python3
"""
cron_options_run.py — Called by Hermes cron job.
Runs the Options Credit Spread Paper Trader and prints a Telegram-ready report.
Schedule: Weekdays (Mon-Fri) at market hours
"""

import sys
import os

# Add the repo to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from options_paper_trader import (
    OptionsPaperTrader,
    print_performance_report,
    fetch_nifty_spot,
    fetch_india_vix,
)

import datetime


def run_morning():
    """9:15 AM IST — Market opens. Scan for setups and enter trades."""
    trader = OptionsPaperTrader()
    spot = fetch_nifty_spot("NIFTY")
    vix = fetch_india_vix()
    
    if spot is None:
        return "⚠️ **Options Trader — Morning Open FAILED**\n\nCould not fetch Nifty spot price."
    
    report = trader.evaluate_and_trade(spot, vix)
    
    header = (
        f"🌅 **Options Credit Spread — Morning Open**\n"
        f"📅 {datetime.datetime.now().strftime('%b %d, %Y %I:%M %p IST')}\n"
        f"📊 Nifty: ₹{spot:,.2f} | VIX: {vix:.1f}\n"
        f"{'─' * 40}\n"
    )
    return header + report


def run_midday():
    """12:00 PM IST — Midday check. Update positions P&L, check for exits."""
    trader = OptionsPaperTrader()
    spot = fetch_nifty_spot("NIFTY")
    vix = fetch_india_vix()
    
    if spot is None:
        return "⚠️ **Options Trader — Midday Check FAILED**\n\nCould not fetch Nifty spot price."
    
    report = trader.evaluate_and_trade(spot, vix)
    
    header = (
        f"🌤️ **Options Credit Spread — Midday Update**\n"
        f"📅 {datetime.datetime.now().strftime('%b %d, %Y %I:%M %p IST')}\n"
        f"📊 Nifty: ₹{spot:,.2f} | VIX: {vix:.1f}\n"
        f"{'─' * 40}\n"
    )
    return header + report


def run_evening():
    """3:30 PM IST — Market close. Final P&L check, position updates, daily summary."""
    trader = OptionsPaperTrader()
    spot = fetch_nifty_spot("NIFTY")
    vix = fetch_india_vix()
    
    if spot is None:
        return "⚠️ **Options Trader — Evening Close FAILED**\n\nCould not fetch Nifty spot price."
    
    report = trader.evaluate_and_trade(spot, vix)
    
    header = (
        f"🌇 **Options Credit Spread — Market Close Summary**\n"
        f"📅 {datetime.datetime.now().strftime('%b %d, %Y %I:%M %p IST')}\n"
        f"📊 Nifty: ₹{spot:,.2f} | VIX: {vix:.1f}\n"
        f"{'─' * 40}\n"
    )
    return header + report


def run_end_of_day():
    """5:00 PM IST — End of day performance report."""
    report = print_performance_report()
    
    header = (
        f"📊 **Options Credit Spread — End of Day Report**\n"
        f"📅 {datetime.datetime.now().strftime('%b %d, %Y')}\n"
        f"{'─' * 40}\n"
    )
    return header + report


def run_single_check():
    """Single check for unscheduled runs."""
    trader = OptionsPaperTrader()
    spot = fetch_nifty_spot("NIFTY")
    vix = fetch_india_vix()
    
    if spot is None:
        return "⚠️ **Options Trader — Manual Check FAILED**\n\nCould not fetch Nifty spot price."
    
    now = datetime.datetime.now()
    hour = now.hour
    total_minutes = hour * 60 + now.minute
    
    if 9*15 <= total_minutes <= 10*60:
        run_type = "morning"
    elif 12*60 <= total_minutes <= 13*60:
        run_type = "midday"
    elif 15*15 <= total_minutes <= 16*60:
        run_type = "evening"
    else:
        run_type = "check"
    
    report = trader.evaluate_and_trade(spot, vix)
    
    header = (
        f"🔄 **Options Paper Trader — {'Manual' if run_type == 'check' else run_type.title()} Check**\n"
        f"📅 {now.strftime('%b %d, %Y %I:%M %p IST')}\n"
        f"📊 Nifty: ₹{spot:,.2f} | VIX: {vix:.1f}\n"
        f"{'─' * 40}\n"
    )
    return header + report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Options Paper Trader Cron Wrapper")
    parser.add_argument("--time", choices=["morning", "midday", "evening", "eod", "check"],
                        default="check", help="Which check to run")
    
    args = parser.parse_args()
    
    runners = {
        "morning": run_morning,
        "midday": run_midday,
        "evening": run_evening,
        "eod": run_end_of_day,
        "check": run_single_check,
    }
    
    result = runners[args.time]()
    print(result)
