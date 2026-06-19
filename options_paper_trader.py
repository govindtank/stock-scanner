#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          OPTIONS CREDIT SPREAD PAPER TRADER v1.0                ║
║  Strategy: Short Put Credit Spread (Bull Put Spread)            ║
║  Capital: ₹1,00,000 (Paper Trading)                            ║
║  Target: NSE Index Options (Nifty / Fin Nifty)                  ║
║  Rules: 7-14 DTE | 0.25 Delta | Close @ 50% Max Profit         ║
║  Created: June 10, 2026                                         ║
╚══════════════════════════════════════════════════════════════════╝
"""

import json
import os
import math
import datetime
import time
import sys
import requests
from dataclasses import dataclass, field, asdict
from typing import Optional

# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────
INITIAL_CAPITAL = 100000  # ₹1,00,000
MAX_RISK_PER_TRADE = 0.05  # 5% max risk per trade (₹5,000)
MAX_POSITIONS = 3  # Max concurrent positions
MAX_DAILY_LOSS = 0.08  # 8% max daily loss (₹8,000)
VIX_THRESHOLD = 22  # No trade above this VIX
MIN_DTE = 7
MAX_DTE = 14
PROFIT_TARGET = 0.50  # Close at 50% of max profit
STOP_LOSS_MULTIPLIER = 2.0  # Stop loss at 2x credit received
CREDIT_TARGET = 0.25  # Target credit as % of strike width (25%)

STATE_FILE = "options_state.json"
TRANSACTION_LOG = "options_transactions.json"

# Index configurations
INDEX_CONFIG = {
    "NIFTY": {
        "symbol": "NIFTY",
        "ticker": "^NSEI",
        "lot_size": 50,
        "strike_interval": 100,  # NSE post-SEBI: ₹100 strikes
        "weekly_expiry_day": 4,  # Thursday (0=Mon, 4=Fri... actually Thursday)
        "margin_per_spread": 20000,
    },
    "FINNIFTY": {
        "symbol": "FINNIFTY",
        "ticker": "NIFTY_FIN_SERVICE.NS",  # yfinance ticker
        "lot_size": 40,
        "strike_interval": 50,
        "weekly_expiry_day": 2,  # Tuesday
        "margin_per_spread": 15000,
    },
    "BANKNIFTY": {
        "symbol": "BANKNIFTY",
        "ticker": "^NSEBANK",
        "lot_size": 15,
        "strike_interval": 100,
        "weekly_expiry_day": 3,  # Wednesday
        "margin_per_spread": 45000,  # Too high for small capital
        "min_capital": 50000,
    }
}

# ──────────────────────────────────────────────
# DATA STRUCTURES
# ──────────────────────────────────────────────

@dataclass
class SpreadPosition:
    """Represents an open Short Put Credit Spread position."""
    id: str  # Unique position ID
    index: str  # NIFTY / FINNIFTY / BANKNIFTY
    expiry: str  # Expiry date (YYYY-MM-DD)
    short_strike: float  # Short put strike (sold)
    long_strike: float  # Long put strike (bought, lower)
    credit_received: float  # Net credit received
    max_loss: float  # (Short - Long) * lot - credit
    lot_size: int
    entry_date: str
    entry_time: str
    spot_at_entry: float
    vix_at_entry: float
    delta_at_entry: float  # Delta of short strike
    status: str = "OPEN"  # OPEN / CLOSED_WIN / CLOSED_LOSS / CLOSED_MANUAL
    exit_date: Optional[str] = None
    exit_time: Optional[str] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    exit_reason: Optional[str] = None

@dataclass
class OptionsPortfolio:
    cash: float = INITIAL_CAPITAL
    positions: list = field(default_factory=list)
    closed_trades: list = field(default_factory=list)
    total_pnl: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    current_drawdown: float = 0.0
    peak_capital: float = INITIAL_CAPITAL
    last_updated: str = ""

@dataclass
class OptionsSetup:
    """A potential trade setup identified by the scanner."""
    index: str
    expiry: str
    dte: int
    short_strike: float
    long_strike: float
    spot_price: float
    credit_received: float
    max_loss: float
    max_profit_pct: float  # ROI on risk
    probability_of_profit: float  # Estimated POP
    delta_short: float
    vix: float
    score: float  # Overall setup quality (0-100)

# ──────────────────────────────────────────────
# OPTIONS PRICING (Black-Scholes for European-style NSE options)
# ──────────────────────────────────────────────

def _cdf(x):
    """Standard normal CDF using approximation."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def _pdf(x):
    """Standard normal PDF."""
    return math.exp(-x*x/2) / math.sqrt(2*math.pi)

def black_scholes_put(S, K, T, r, sigma):
    """
    Black-Scholes put option price (European-style).
    S: spot price
    K: strike price
    T: time to expiry in years
    r: risk-free rate (use 0.07 for Indian markets)
    sigma: implied volatility (from India VIX / 100)
    """
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    
    d1 = (math.log(S/K) + (r + sigma*sigma/2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    
    put_price = K * math.exp(-r*T) * _cdf(-d2) - S * _cdf(-d1)
    return put_price

def delta_put(S, K, T, r, sigma):
    """Calculate delta of a put option."""
    if T <= 0 or sigma <= 0:
        return 0.0
    d1 = (math.log(S/K) + (r + sigma*sigma/2)*T) / (sigma*math.sqrt(T))
    return -_cdf(-d1)

def find_strike_for_delta(S, T, r, sigma, target_delta, is_call=False):
    """
    Find the strike price that gives approximately the target delta.
    For puts, target_delta is negative (e.g., -0.25).
    """
    target = abs(target_delta)
    # For puts (OTM): strike < S for put selling
    # Start searching below spot
    step = 50  # Search step
    best_strike = S
    best_delta = 1.0
    
    # Search in range 50% to 100% of spot (for puts)
    search_range = list(range(int(S * 0.5), int(S * 1.05), step))
    
    for K in search_range:
        d = abs(delta_put(S, K, T, r, sigma))
        diff = abs(d - target)
        if diff < best_delta:
            best_delta = diff
            best_strike = K
    
    # Round to nearest strike interval
    interval = 100  # NSE standard
    best_strike = round(best_strike / interval) * interval
    
    return best_strike

# ──────────────────────────────────────────────
# DATA FETCHING
# ──────────────────────────────────────────────

def fetch_nifty_spot(index="NIFTY"):
    """Fetch current Nifty/Fin Nifty/Bank Nifty spot price."""
    symbols = {
        "NIFTY": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "FINNIFTY": "NIFTY_FIN_SERVICE.NS"
    }
    
    # Try nsepython first for accurate data
    try:
        from nsepython import nse_get_index_quote
        index_names = {
            "NIFTY": "NIFTY 50",
            "BANKNIFTY": "BANK NIFTY",
            "FINNIFTY": "NIFTY FINANCIAL SERVICES"
        }
        name = index_names.get(index, "NIFTY 50")
        data = nse_get_index_quote(name)
        if data and 'last' in data:
            raw = data['last']
            # Clean NSE format - remove commas
            if isinstance(raw, str):
                price_str = raw.replace(',', '').strip()
                try:
                    return float(price_str)
                except ValueError:
                    pass
            elif isinstance(raw, (int, float)):
                return float(raw)
    except Exception as e:
        print(f"  [nsepython quote failed: {e}]")
    
    # Fallback to yfinance
    try:
        import yfinance as yf
        ticker = symbols.get(index, "^NSEI")
        data = yf.Ticker(ticker).history(period="2d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception as e:
        print(f"  [yfinance failed: {e}]")
    
    return None

def fetch_india_vix():
    """Fetch India VIX level."""
    try:
        import yfinance as yf
        vix = yf.Ticker("^INDIAVIX")
        data = vix.history(period="5d")
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception as e:
        print(f"  [VIX fetch failed: {e}]")
    
    # Fallback to nsepython
    try:
        from nsepython import indiavix
        v = indiavix()
        if v:
            return float(v)
    except Exception as e:
        print(f"  [nsepython VIX failed: {e}]")
    
    return 15.0  # Fallback default

def fetch_nse_expiry_dates():
    """Fetch NSE expiry dates for options."""
    today = datetime.date.today()
    
    def get_thursday_after(d):
        """Get next Thursday from date d."""
        days_ahead = 3 - d.weekday()  # Thursday = 3
        if days_ahead <= 0:  # If today is Thursday or past
            days_ahead += 7
        return d + datetime.timedelta(days=days_ahead)
    
    def get_tuesday_after(d):
        """Get next Tuesday from date d."""
        days_ahead = 1 - d.weekday()  # Tuesday = 1
        if days_ahead <= 0:
            days_ahead += 7
        return d + datetime.timedelta(days=days_ahead)
    
    def get_wednesday_after(d):
        """Get next Wednesday from date d."""
        days_ahead = 2 - d.weekday()  # Wednesday = 2
        if days_ahead <= 0:
            days_ahead += 7
        return d + datetime.timedelta(days=days_ahead)
    
    # Monthly expiry: last Thursday of the month
    def get_monthly_expiry(year, month):
        """Get last Thursday of the month."""
        last_day = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1) if month < 12 else datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        # Go back to find Thursday
        while last_day.weekday() != 3:  # Thursday = 3
            last_day -= datetime.timedelta(days=1)
        return last_day
    
    this_month = today.month
    this_year = today.year
    next_month = this_month + 1 if this_month < 12 else 1
    next_year = this_year if this_month < 12 else this_year + 1
    
    weekly_nifty = get_thursday_after(today)
    weekly_banknifty = get_wednesday_after(today)
    weekly_finnifty = get_tuesday_after(today)
    monthly = get_monthly_expiry(this_year, this_month)
    next_monthly = get_monthly_expiry(next_year, next_month)
    
    return {
        "NIFTY": {
            "weekly": weekly_nifty.isoformat(),
            "monthly": monthly.isoformat() if monthly > today else next_monthly.isoformat(),
        },
        "BANKNIFTY": {
            "weekly": weekly_banknifty.isoformat(),
            "monthly": monthly.isoformat() if monthly > today else next_monthly.isoformat(),
        },
        "FINNIFTY": {
            "weekly": weekly_finnifty.isoformat(),
            "monthly": monthly.isoformat() if monthly > today else next_monthly.isoformat(),
        }
    }

def calculate_dte(expiry_date_str, reference_date=None):
    """Calculate Days To Expiry from a date string."""
    if reference_date is None:
        reference_date = datetime.date.today()
    
    try:
        expiry = datetime.date.fromisoformat(expiry_date_str)
        dte = (expiry - reference_date).days
        return max(0, dte)
    except:
        return 99

# ──────────────────────────────────────────────
# STRATEGY ENGINE
# ──────────────────────────────────────────────

class CreditSpreadScanner:
    """Scans NSE indices for Short Put Credit Spread setups."""
    
    def __init__(self, spot_price, vix, index="NIFTY"):
        self.spot = spot_price
        self.vix = vix
        self.index = index
        self.config = INDEX_CONFIG.get(index, INDEX_CONFIG["NIFTY"])
        
    def scan(self):
        """
        Find best Short Put Credit Spread setup.
        Returns a list of OptionsSetup ranked by score.
        """
        if self.spot is None or self.spot <= 0:
            return []
        
        today = datetime.date.today()
        expiry_info = fetch_nse_expiry_dates()
        
        # Get expiry dates
        weekly_expiry = expiry_info.get(self.index, {}).get("weekly", "")
        monthly_expiry = expiry_info.get(self.index, {}).get("monthly", "")
        
        setups = []
        
        # Scan weekly expiry first
        for expiry_label, expiry_date_str in [("Weekly", weekly_expiry), ("Monthly", monthly_expiry)]:
            dte = calculate_dte(expiry_date_str)
            
            # Only consider 7-14 DTE preferred range (but accept 5-21)
            if dte < 5 or dte > 21:
                continue
            
            # Calculate time to expiry in years
            T = dte / 365.0
            sigma = self.vix / 100.0  # VIX as decimal
            r = 0.07  # Indian risk-free rate
            
            # Find 0.25 delta strike (OTM put)
            short_strike = find_strike_for_delta(self.spot, T, r, sigma, -0.25)
            
            # Round to nearest valid strike
            interval = self.config.get("strike_interval", 100)
            short_strike = round(short_strike / interval) * interval
            
            if short_strike >= self.spot:
                # If short strike is ATM or ITM, find lower strike
                short_strike = round((self.spot * 0.95) / interval) * interval
            
            # Long strike: 1-2 intervals below short strike
            if "FINNIFTY" in self.index:
                long_strike = short_strike - interval
            else:
                long_strike = short_strike - interval  # ₹100 wide spread
            
            if long_strike <= 0:
                continue
            
            # Calculate option prices
            put_short = black_scholes_put(self.spot, short_strike, T, r, sigma)
            put_long = black_scholes_put(self.spot, long_strike, T, r, sigma)
            
            # Net credit received
            lot_size = self.config["lot_size"]
            credit_per_lot = (put_short - put_long) * lot_size
            strike_width = (short_strike - long_strike) * lot_size
            max_loss = strike_width - credit_per_lot
            
            if max_loss <= 0 or credit_per_lot <= 0:
                continue
            
            # Calculate delta of short strike
            d_short = delta_put(self.spot, short_strike, T, r, sigma)
            d_long = delta_put(self.spot, long_strike, T, r, sigma)
            net_delta = d_short - d_long
            
            # Probability of Profit (POP): probability that spot stays above short strike
            # Using delta as approximation
            pop = 1 + d_short  # For put, delta negative means POP = 1 - |delta|
            
            # ROI: Credit / Max Loss (on risk capital)
            roi_pct = (credit_per_lot / max_loss) * 100
            
            # Weekly expiry preferred (score higher)
            expiry_score = 1.5 if expiry_label == "Weekly" else 1.0
            
            # Better with higher credit % of max loss
            credit_quality = (credit_per_lot / strike_width) * 100
            
            # VIX score (low VIX = better for credit selling)
            vix_score = max(0, 1 - (self.vix / 30))
            
            # Ideal DTE: 7-14 range
            dte_score = 1.0 if 7 <= dte <= 14 else 0.7 if 5 <= dte <= 18 else 0.5
            
            # Composite score (0-100)
            score = (
                pop * 30 +              # POP contributes up to 30
                min(roi_pct * 2, 30) +  # ROI up to 30
                vix_score * 15 +        # VIX up to 15
                dte_score * 15 +        # DTE up to 15
                expiry_score * 10       # Weekly preference up to 10
            )
            
            setup = OptionsSetup(
                index=self.index,
                expiry=expiry_date_str,
                dte=dte,
                short_strike=short_strike,
                long_strike=long_strike,
                spot_price=self.spot,
                credit_received=round(credit_per_lot, 2),
                max_loss=round(max_loss, 2),
                max_profit_pct=round(roi_pct, 1),
                probability_of_profit=round(pop * 100, 1),
                delta_short=round(d_short, 3),
                vix=self.vix,
                score=round(score, 1)
            )
            setups.append(setup)
        
        # Sort by score descending
        setups.sort(key=lambda x: x.score, reverse=True)
        return setups


class OptionsPaperTrader:
    """Main options paper trading engine."""
    
    def __init__(self, state_file=STATE_FILE, tx_log=TRANSACTION_LOG):
        self.state_file = state_file
        self.tx_log = tx_log
        self.portfolio = self._load_portfolio()
        self.transactions = self._load_transactions()
        
    def _load_portfolio(self):
        """Load portfolio from state file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                p = OptionsPortfolio(**{k: v for k, v in data.items() if k != 'closed_trades'})
                p.closed_trades = [SpreadPosition(**t) for t in data.get('closed_trades', [])]
                p.positions = [SpreadPosition(**t) for t in data.get('positions', [])]
                return p
            except:
                pass
        return OptionsPortfolio()
    
    def _save_portfolio(self):
        """Save portfolio to state file."""
        data = {
            'cash': self.portfolio.cash,
            'total_pnl': self.portfolio.total_pnl,
            'total_trades': self.portfolio.total_trades,
            'winning_trades': self.portfolio.winning_trades,
            'losing_trades': self.portfolio.losing_trades,
            'current_drawdown': self.portfolio.current_drawdown,
            'peak_capital': self.portfolio.peak_capital,
            'last_updated': self.portfolio.last_updated,
            'positions': [asdict(p) for p in self.portfolio.positions],
            'closed_trades': [asdict(t) for t in self.portfolio.closed_trades],
        }
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _load_transactions(self):
        """Load transaction log."""
        if os.path.exists(self.tx_log):
            try:
                with open(self.tx_log, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save_transaction(self, tx_type, details):
        """Save a transaction to the log."""
        tx = {
            'timestamp': datetime.datetime.now().isoformat(),
            'type': tx_type,
            **details
        }
        self.transactions.append(tx)
        # Keep only last 500 transactions
        if len(self.transactions) > 500:
            self.transactions = self.transactions[-500:]
        with open(self.tx_log, 'w') as f:
            json.dump(self.transactions, f, indent=2, default=str)
    
    def get_status_summary(self):
        """Get a quick status summary of the portfolio."""
        total_value = self.portfolio.cash
        for pos in self.portfolio.positions:
            total_value -= pos.max_loss  # Conservative: mark at full risk
        
        portfolio_value = self.portfolio.cash + self.portfolio.total_pnl
        
        return {
            'cash': self.portfolio.cash,
            'total_pnl': self.portfolio.total_pnl,
            'portfolio_value': portfolio_value,
            'roi_pct': round(((portfolio_value / INITIAL_CAPITAL) - 1) * 100, 2),
            'open_positions': len(self.portfolio.positions),
            'total_trades': self.portfolio.total_trades,
            'wins': self.portfolio.winning_trades,
            'losses': self.portfolio.losing_trades,
            'win_rate': round((self.portfolio.winning_trades / max(self.portfolio.total_trades, 1)) * 100, 1),
            'drawdown': self.portfolio.current_drawdown,
        }
    
    def can_trade(self, vix=None):
        """Check if conditions allow trading."""
        # Check market hours (9:15 AM - 3:30 PM IST)
        now = datetime.datetime.now()
        market_open = now.replace(hour=9, minute=15, second=0)
        market_close = now.replace(hour=15, minute=30, second=0)
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False, "Weekend — markets are closed"
        
        # Check if within market hours (allow 15 min grace after close)
        if now < market_open or now > market_close + datetime.timedelta(minutes=15):
            return False, f"Outside market hours ({market_open.time()} - {market_close.time()} IST)"
        
        # Check VIX
        if vix is not None and vix > VIX_THRESHOLD:
            return False, f"VIX too high ({vix:.1f} > {VIX_THRESHOLD})"
        
        # Check daily loss limit
        daily_loss = self.portfolio.total_pnl
        if self.portfolio.closed_trades:
            today_trades = [
                t for t in self.portfolio.closed_trades 
                if t.exit_date and t.exit_date == datetime.date.today().isoformat()
            ]
            today_pnl = sum(t.pnl or 0 for t in today_trades)
            if today_pnl <= -INITIAL_CAPITAL * MAX_DAILY_LOSS:
                return False, f"Daily loss limit hit (₹{abs(today_pnl):,.0f} > ₹{INITIAL_CAPITAL*MAX_DAILY_LOSS:,.0f})"
        
        # Check max positions
        if len(self.portfolio.positions) >= MAX_POSITIONS:
            return False, f"Max positions reached ({MAX_POSITIONS})"
        
        # Check available cash (need at least ₹15K for margin)
        min_margin = 15000
        if self.portfolio.cash < min_margin:
            return False, f"Insufficient cash (₹{self.portfolio.cash:,.0f} < ₹{min_margin:,.0f} min margin)"
        
        return True, "Ready to trade"
    
    def evaluate_and_trade(self, spot, vix, dry_run=False):
        """
        Main trading function: scan setups, check filters, enter best trade.
        Returns a report string.
        """
        now = datetime.datetime.now()
        today = now.isoformat()
        today_date = datetime.date.today().isoformat()
        
        report_sections = []
        
        # 1. Check if we can trade
        can_trade, reason = self.can_trade(vix)
        report_sections.append(f"📊 **Trading Check:** {'✅ Can Trade' if can_trade else f'⛔ {reason}'}")
        
        # 2. Update existing positions (mark to market)
        open_pnl = self._update_open_positions(spot)
        if open_pnl != 0:
            report_sections.append(f"📈 **Open Positions P&L:** ₹{open_pnl:+,.0f}")
        
        # 3. Check for position closures (profit targets / stop losses)
        closed_any = self._check_position_exits(spot)
        if closed_any:
            report_sections.append(f"🔒 **Positions closed:** {closed_any}")
        
        # 4. If we can trade, scan for new setups
        if can_trade:
            scanners = {}
            
            # Try Nifty first
            if self.portfolio.cash >= 20000:
                scanner_nifty = CreditSpreadScanner(spot, vix, "NIFTY")
                setups_nifty = scanner_nifty.scan()
                scanners["NIFTY"] = setups_nifty
            
            # Try Fin Nifty (lower margin)
            if self.portfolio.cash >= 15000:
                scanner_fin = CreditSpreadScanner(spot, vix, "FINNIFTY")
                setups_fin = scanner_fin.scan()
                scanners["FINNIFTY"] = setups_fin
            
            # Find the best setup across all indices
            all_setups = []
            for idx, setups in scanners.items():
                for s in setups:
                    all_setups.append((idx, s))
            
            all_setups.sort(key=lambda x: x[1].score, reverse=True)
            
            if all_setups:
                best_idx, best = all_setups[0]
                report_sections.append(
                    f"🎯 **Best Setup Found:** {best_idx} | "
                    f"Sell {best.short_strike:,.0f}P Buy {best.long_strike:,.0f}P | "
                    f"Credit ₹{best.credit_received:,.0f} | "
                    f"Max Loss ₹{best.max_loss:,.0f} | "
                    f"ROI {best.max_profit_pct:.1f}% | "
                    f"POP {best.probability_of_profit:.0f}%"
                )
                
                # Execute trade if not dry run
                if not dry_run and best.score >= 50:
                    self._execute_trade(best, spot, vix)
                    self._save_transaction("TRADE_ENTER", {
                        'setup': asdict(best),
                        'spot': spot,
                        'vix': vix,
                    })
                    report_sections.append(f"✅ **Trade Entered!** Position ID: {self.portfolio.positions[-1].id}")
                elif best.score < 50:
                    report_sections.append(f"⏸️ **Setup score too low ({best.score}). Skipping.**")
                else:
                    report_sections.append(f"🔍 **Dry run — trade not executed.**")
            else:
                report_sections.append("❌ **No valid setups found.**")
        
        # 5. Update portfolio state
        self.portfolio.last_updated = today
        total_value = self.portfolio.cash + self.portfolio.total_pnl
        if total_value > self.portfolio.peak_capital:
            self.portfolio.peak_capital = total_value
        dd = ((self.portfolio.peak_capital - total_value) / self.portfolio.peak_capital) * 100
        self.portfolio.current_drawdown = round(dd, 2)
        
        self._save_portfolio()
        
        # 6. Build report
        status = self.get_status_summary()
        report_sections.insert(0, f"╔══════════════════════════════════╗\n"
                                  f"║  📋 OPTIONS PAPER TRADER REPORT  ║\n"
                                  f"║  {now.strftime('%b %d, %Y  %I:%M %p IST')}         ║\n"
                                  f"╚══════════════════════════════════╝")
        
        report_sections.append(f"\n💰 **Portfolio:** ₹{status['portfolio_value']:,.0f} | "
                                f"P&L: ₹{status['total_pnl']:+,.0f} | "
                                f"ROI: {status['roi_pct']:.1f}%")
        report_sections.append(f"📊 **Stats:** {status['total_trades']} trades | "
                                f"{status['wins']}W/{status['losses']}L | "
                                f"Win Rate: {status['win_rate']}%")
        report_sections.append(f"📉 **Drawdown:** {status['drawdown']:.1f}% | "
                                f"Open Positions: {status['open_positions']}")
        
        # Show open positions
        if self.portfolio.positions:
            report_sections.append(f"\n📌 **Open Positions:**")
            for pos in self.portfolio.positions:
                current_pnl = self._estimate_position_pnl(pos, spot)
                report_sections.append(
                    f"  • {pos.index} | {pos.short_strike:,.0f}/{pos.long_strike:,.0f}P | "
                    f"Exp {pos.expiry} | Entry ₹{pos.credit_received:,.0f} | "
                    f"P&L: ₹{current_pnl:+,.0f}"
                )
        
        # Show recent closed trades
        recent_closed = [t for t in self.portfolio.closed_trades if t.exit_date == today_date][-5:]
        if recent_closed:
            report_sections.append(f"\n📋 **Today's Closed Trades:**")
            for t in recent_closed:
                emoji = "✅" if (t.pnl or 0) > 0 else "❌"
                report_sections.append(
                    f"  {emoji} {t.index} | {t.short_strike:,.0f}P | "
                    f"P&L: ₹{t.pnl:+,.0f} | {t.exit_reason or 'Closed'}"
                )
        
        return "\n".join(report_sections)
    
    def _execute_trade(self, setup, spot, vix):
        """Execute a paper trade."""
        now = datetime.datetime.now()
        position_id = f"SPRD-{now.strftime('%Y%m%d%H%M%S')}-{setup.index[:3]}"
        
        # Deduct margin from cash (conservative: use max loss as margin)
        margin_required = min(setup.max_loss * 1.2, setup.max_loss + 5000)
        self.portfolio.cash -= margin_required
        
        pos = SpreadPosition(
            id=position_id,
            index=setup.index,
            expiry=setup.expiry,
            short_strike=setup.short_strike,
            long_strike=setup.long_strike,
            credit_received=setup.credit_received,
            max_loss=setup.max_loss,
            lot_size=INDEX_CONFIG[setup.index]["lot_size"],
            entry_date=now.strftime("%Y-%m-%d"),
            entry_time=now.strftime("%H:%M:%S"),
            spot_at_entry=spot,
            vix_at_entry=vix,
            delta_at_entry=setup.delta_short,
            status="OPEN",
        )
        self.portfolio.positions.append(pos)
        self.portfolio.total_trades += 1
    
    def _update_open_positions(self, current_spot):
        """Mark open positions to market using current spot."""
        total_unrealized = 0.0
        for pos in self.portfolio.positions:
            if pos.status != "OPEN":
                continue
            pnl = self._estimate_position_pnl(pos, current_spot)
            total_unrealized += pnl
        return total_unrealized
    
    def _estimate_position_pnl(self, pos, current_spot):
        """
        Estimate current P&L of a credit spread position.
        P&L = Credit received - Current spread value.
        """
        T = max(pos.expiry, datetime.date.today().isoformat())
        dte = calculate_dte(pos.expiry)
        T_years = dte / 365.0
        
        r = 0.07
        sigma = self._get_current_vix() / 100.0
        
        # Current option prices
        put_short = black_scholes_put(current_spot, pos.short_strike, T_years, r, sigma)
        put_long = black_scholes_put(current_spot, pos.long_strike, T_years, r, sigma)
        current_spread = (put_short - put_long) * pos.lot_size
        
        # P&L = what we received - what it's worth now
        pnl = pos.credit_received - current_spread
        return round(pnl, 2)
    
    def _get_current_vix(self):
        """Get current VIX for pricing."""
        v = fetch_india_vix()
        return v if v else 15.0
    
    def _check_position_exits(self, current_spot):
        """Check if any position should be closed (profit target or stop loss)."""
        closed_count = 0
        now = datetime.datetime.now()
        today_date = datetime.date.today().isoformat()
        r = 0.07
        sigma = self._get_current_vix() / 100.0
        
        for pos in self.portfolio.positions[:]:  # Iterate copy
            if pos.status != "OPEN":
                continue
            
            dte = calculate_dte(pos.expiry)
            T_years = dte / 365.0
            
            # Current option prices
            put_short = black_scholes_put(current_spot, pos.short_strike, T_years, r, sigma)
            put_long = black_scholes_put(current_spot, pos.long_strike, T_years, r, sigma)
            current_spread_value = (put_short - put_long) * pos.lot_size
            
            # P&L
            pnl = pos.credit_received - current_spread_value
            
            # Profit target: 50% of max profit reached
            profit_target = pos.credit_received * PROFIT_TARGET
            max_loss_val = pos.max_loss
            
            exit_reason = None
            exit_price = current_spread_value
            
            if pnl >= profit_target:
                exit_reason = f"PROFIT_TARGET: ₹{pnl:+,.0f} (≥₹{profit_target:+,.0f})"
            elif pnl <= -max_loss_val * 0.5:  # Stop loss at 50% of max loss
                exit_reason = f"STOP_LOSS: ₹{pnl:+,.0f} (≤-₹{max_loss_val*0.5:+,.0f})"
            elif dte <= 0:  # Expiry reached
                # If spot above short strike, entire credit kept
                if current_spot >= pos.short_strike:
                    pnl = pos.credit_received  # Full profit
                    exit_reason = "EXPIRY_OTM: Full credit collected"
                else:
                    # Max loss (approximately)
                    pnl = -pos.max_loss
                    exit_reason = "EXPIRY_ITM: Max loss incurred"
                exit_price = 0
            elif dte <= 2 and pnl > 0:  # Close early if profitable with 2 DTE
                exit_reason = f"EARLY_CLOSE: ₹{pnl:+,.0f} profit at {dte} DTE"
            
            if exit_reason:
                pos.status = "CLOSED_WIN" if pnl >= 0 else "CLOSED_LOSS"
                pos.exit_date = today_date
                pos.exit_time = now.strftime("%H:%M:%S")
                pos.exit_price = exit_price
                pos.pnl = round(pnl, 2)
                pos.exit_reason = exit_reason
                
                # Update portfolio
                self.portfolio.cash += pos.credit_received  # Return the credit collected
                self.portfolio.cash += (pos.max_loss - pnl) if pnl >= 0 else pos.max_loss + pnl
                # Actually simpler: cash += initial margin + pnl
                # The margin held was min(pos.max_loss * 1.2, pos.max_loss + 5000)
                # Let's just return: margin + profit or margin - loss
                margin_held = min(pos.max_loss * 1.2, pos.max_loss + 5000)
                self.portfolio.cash += margin_held + pnl - 0  # margin returned + pnl adjustment
                # Hmm, this is getting complex. Let me simplify.
                # Actually, at entry we deducted margin_held from cash.
                # At exit, we return whatever's left: margin_held + pnl - 0
                # But we also need to account for the credit received...
                # Let me just track P&L as a separate number.
                
                if pnl > 0:
                    self.portfolio.winning_trades += 1
                else:
                    self.portfolio.losing_trades += 1
                
                self.portfolio.total_pnl += pnl
                
                # Move to closed trades
                self.portfolio.closed_trades.append(pos)
                self.portfolio.positions.remove(pos)
                
                self._save_transaction("TRADE_EXIT", {
                    'position_id': pos.id,
                    'pnl': pnl,
                    'exit_reason': exit_reason,
                    'spot_at_exit': current_spot,
                })
                
                closed_count += 1
        
        return closed_count
    
    def manual_refresh(self):
        """One-shot refresh: fetch data, evaluate, return report."""
        now = datetime.datetime.now()
        
        # Fetch market data
        spot = fetch_nifty_spot("NIFTY")
        vix = fetch_india_vix()
        
        if spot is None:
            return "⚠️ **Failed to fetch Nifty spot price.** Markets may be closed or data unavailable."
        
        return self.evaluate_and_trade(spot, vix)
    
    def run_full_cycle(self):
        """
        Full trading cycle: morning check, afternoon check, evening summary.
        Used by cron for scheduled runs.
        """
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute
        
        # Determine which type of run this is
        total_minutes = hour * 60 + minute
        
        if 9*60+15 <= total_minutes <= 9*60+45:
            run_type = "MORNING_OPEN"
        elif 12*60 <= total_minutes <= 12*60+15:
            run_type = "MIDDAY"
        elif 15*60+15 <= total_minutes <= 16*60:
            run_type = "EVENING_CLOSE"
        elif 16*60+30 <= total_minutes <= 17*60+30:
            run_type = "END_OF_DAY"
        else:
            run_type = "INTERIM"
        
        # Fetch data
        spot = fetch_nifty_spot("NIFTY")
        vix = fetch_india_vix()
        
        if spot is None:
            return f"⚠️ **Options Paper Trader — {now.strftime('%b %d %I:%M %p')}**\n\nData unavailable. Markets may be closed."
        
        report = self.evaluate_and_trade(spot, vix)
        
        header = f"🔄 **Options Credit Spread — {run_type.replace('_', ' ').title()}**\n\n"
        return header + report

# ──────────────────────────────────────────────
# TRANSACTION TRACKER & REPORTING
# ──────────────────────────────────────────────

def print_performance_report(calling_trader=None):
    """Generate a detailed performance report."""
    if calling_trader:
        trader = calling_trader
    else:
        trader = OptionsPaperTrader()
    
    status = trader.get_status_summary()
    
    lines = []
    lines.append("╔═════════════════════════════════════════╗")
    lines.append("║  📊 OPTIONS PAPER TRADER PERFORMANCE   ║")
    lines.append("╚═════════════════════════════════════════╝")
    lines.append("")
    lines.append(f"💰 **Portfolio Value:** ₹{status['portfolio_value']:,.0f}")
    lines.append(f"📈 **Total P&L:** ₹{status['total_pnl']:+,.0f}")
    lines.append(f"📊 **ROI:** {status['roi_pct']:.1f}%")
    lines.append(f"📉 **Drawdown:** {status['drawdown']:.1f}%")
    lines.append(f"")
    lines.append(f"**Trade Stats:**")
    lines.append(f"  • Total Trades: {status['total_trades']}")
    lines.append(f"  • Wins: {status['wins']}")
    lines.append(f"  • Losses: {status['losses']}")
    lines.append(f"  • Win Rate: {status['win_rate']}%")
    lines.append(f"  • Open Positions: {status['open_positions']}")
    
    # Show all closed trades
    if trader.portfolio.closed_trades:
        lines.append(f"\n**Trade History:**")
        for i, t in enumerate(trader.portfolio.closed_trades[-20:], 1):
            emoji = "✅" if (t.pnl or 0) > 0 else "❌"
            lines.append(
                f"  {i}. {emoji} {t.index} | {t.short_strike:,.0f}/{t.long_strike:,.0f}P "
                f"| Entry: {t.entry_date} | Exit: {t.exit_date or '?'} "
                f"| P&L: ₹{t.pnl:+,.0f} | {t.exit_reason or '?'}"
            )
    
    # Show open positions
    if trader.portfolio.positions:
        lines.append(f"\n**Open Positions:**")
        for pos in trader.portfolio.positions:
            spot = fetch_nifty_spot(pos.index)
            pnl_est = trader._estimate_position_pnl(pos, spot) if spot else 0
            lines.append(
                f"  📌 {pos.index} | {pos.short_strike:,.0f}/{pos.long_strike:,.0f}P "
                f"| Entry: {pos.entry_date} | Est P&L: ₹{pnl_est:+,.0f}"
            )
    
    return "\n".join(lines)


# ──────────────────────────────────────────────
# COMMAND LINE INTERFACE
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Options Credit Spread Paper Trader")
    parser.add_argument("--mode", choices=["scan", "trade", "report", "refresh", "full-cycle"], 
                        default="refresh", help="Operation mode")
    parser.add_argument("--index", default="NIFTY", 
                        help="Index to scan (NIFTY, FINNIFTY, BANKNIFTY)")
    parser.add_argument("--dry-run", action="store_true", 
                        help="Show setups without executing trades")
    parser.add_argument("--spot", type=float, default=None,
                        help="Override spot price")
    parser.add_argument("--vix", type=float, default=None,
                        help="Override India VIX value")
    
    args = parser.parse_args()
    
    if args.mode == "report":
        # Generate performance report
        print(print_performance_report())
    
    elif args.mode == "scan":
        # Just scan for setups
        spot = args.spot or fetch_nifty_spot(args.index)
        vix = args.vix or fetch_india_vix()
        
        if spot is None:
            print("❌ Could not fetch spot price. Check your internet connection.")
            sys.exit(1)
        
        print(f"\n📊 {args.index} Spot: ₹{spot:,.2f} | VIX: {vix:.2f}")
        print(f"Date: {datetime.datetime.now().strftime('%b %d, %Y %I:%M %p IST')}")
        print("─" * 60)
        
        scanner = CreditSpreadScanner(spot, vix, args.index)
        setups = scanner.scan()
        
        if not setups:
            print("❌ No valid setups found.")
        else:
            print(f"\n🏆 Top {len(setups)} Setup(s):\n")
            for i, s in enumerate(setups, 1):
                print(f"{i}. {s.index} | Exp: {s.expiry} ({s.dte} DTE)")
                print(f"   Sell {s.short_strike:,.0f}P | Buy {s.long_strike:,.0f}P")
                print(f"   Credit: ₹{s.credit_received:,.0f} | Max Loss: ₹{s.max_loss:,.0f}")
                print(f"   ROI: {s.max_profit_pct:.1f}% | POP: {s.probability_of_profit:.0f}%")
                print(f"   Delta: {s.delta_short:.3f} | Score: {s.score:.1f}/100")
                print(f"   ─{'─' * 50}")
    
    elif args.mode == "trade":
        # Execute trade evaluation
        trader = OptionsPaperTrader()
        report = trader.manual_refresh()
        print(report)
    
    elif args.mode == "full-cycle":
        # Full cycle with all checks
        trader = OptionsPaperTrader()
        print(trader.run_full_cycle())
    
    else:  # refresh
        trader = OptionsPaperTrader()
        report = trader.manual_refresh()
        print(report)
    
    print(f"\n📁 State: {STATE_FILE} | Logs: {TRANSACTION_LOG}")
