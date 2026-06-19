#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
  DARVAS PAPER TRADER — Pro-Level AI Trading Assistant
  ═══════════════════════════════════════════════════════════════════
  Strategy: Nicolas Darvas Box Theory (breakout + volume confirmation)
  Capital:  ₹1,00,000 (Paper Trading)
  Market:   NSE (India) via yfinance
  Backups:  Mean Reversion, Momentum, Gap Trading
  Memory:   Self-improving with trade history & regime learning

  Runs as cron job (daily) or ad-hoc analysis.
═══════════════════════════════════════════════════════════════════
"""

import json
import os
import sys
import time
import datetime
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path

import pandas as pd
import numpy as np

# ──────────────────────────────────────────────────────────────────
# Add stock-scanner-repo to path for existing modules
# ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from darvas_detector import IndianStockMonitor, DarvasBoxDetector, TrendLineDetector
from technical_indicators import TechnicalIndicators

# ──────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────
INITIAL_CAPITAL = 100_000  # ₹1,00,000
STATE_FILE = SCRIPT_DIR / "darvas_state.json"
MEMORY_FILE = SCRIPT_DIR / "darvas_memory.json"
REPORT_DIR = SCRIPT_DIR / "reports"
MAX_POSITIONS = 5
MAX_RISK_PER_TRADE = 0.02  # 2% max risk per trade
MAX_DAILY_LOSS_PCT = 0.05  # 5% max daily loss
MIN_VOLUME_MULTIPLIER = 1.5  # 150% volume for breakout confirmation
BROKERAGE_PCT = 0.0003  # 0.03% per side (like Zerodha)
STT_PCT = 0.001  # 0.1% STT on sell

# NSE Watchlist - Tier 1: Large-cap liquid stocks suitable for Darvas
NSE_WATCHLIST = [
    # Index Leaders
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS", "AXISBANK.NS",
    # Large Cap
    "LT.NS", "WIPRO.NS", "HCLTECH.NS", "MARUTI.NS",
    "TITAN.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "NESTLEIND.NS", "HINDUNILVR.NS",
    # Mid Cap (High momentum)
    "TRENT.NS", "POLYCAB.NS", "DIXON.NS", "PIDILITIND.NS", "DMART.NS",
    "INDUSINDBK.NS", "BAJAJFINSV.NS", "VEDL.NS", "TATASTEEL.NS", "JSWSTEEL.NS",
    # Nifty 50 completions
    "ADANIPORTS.NS", "ADANIENT.NS", "APOLLOHOSP.NS", "BRITANNIA.NS",
    "CIPLA.NS", "COALINDIA.NS", "DRREDDY.NS", "EICHERMOT.NS",
    "GRASIM.NS", "HDFCLIFE.NS", "HINDALCO.NS",
    "M&M.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS",
    "SBILIFE.NS", "SUNPHARMA.NS", "TATACONSUM.NS", "TECHM.NS",
    "ULTRACEMCO.NS", "UPL.NS", "HEROMOTOCO.NS",
]


# ──────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ──────────────────────────────────────────────────────────────────
@dataclass
class Trade:
    """A single paper trade."""
    id: str
    symbol: str
    entry_price: float
    entry_date: str  # ISO date
    quantity: int
    side: str  # 'BUY' or 'SELL' (for short)
    strategy: str  # 'darvas_breakout', 'mean_reversion', 'momentum', 'gap_trading'
    box_high: Optional[float] = None
    box_low: Optional[float] = None
    stop_loss: float = 0.0
    target_1: float = 0.0
    target_2: float = 0.0
    exit_price: Optional[float] = None
    exit_date: Optional[str] = None
    exit_reason: Optional[str] = None  # 'target_hit', 'stop_loss', 'time_exit', 'manual'
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    entry_signal_strength: str = ""  # STRONG / MODERATE / WEAK
    max_favorable_excursion: float = 0.0
    max_adverse_excursion: float = 0.0
    notes: str = ""

    def calculate_pnl(self, exit_price: float) -> Tuple[float, float]:
        if self.side == 'BUY':
            pnl = (exit_price - self.entry_price) * self.quantity
            pnl_pct = ((exit_price - self.entry_price) / self.entry_price) * 100
        else:
            pnl = (self.entry_price - exit_price) * self.quantity
            pnl_pct = ((self.entry_price - exit_price) / self.entry_price) * 100
        return round(pnl, 2), round(pnl_pct, 2)


@dataclass
class Position:
    """An open paper position."""
    trade: Trade
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0


@dataclass
class Portfolio:
    cash: float = INITIAL_CAPITAL
    total_value: float = INITIAL_CAPITAL
    peak_value: float = INITIAL_CAPITAL
    positions: List[dict] = field(default_factory=list)
    closed_trades: List[dict] = field(default_factory=list)
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    daily_pnl: float = 0.0
    last_updated: str = ""
    risk_multiplier: float = 1.0

    def to_dict(self):
        return {
            'cash': self.cash,
            'total_value': self.total_value,
            'peak_value': self.peak_value,
            'positions': self.positions,
            'closed_trades': self.closed_trades,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_pnl': self.total_pnl,
            'daily_pnl': self.daily_pnl,
            'last_updated': self.last_updated,
            'risk_multiplier': self.risk_multiplier,
        }

    @classmethod
    def from_dict(cls, d):
        p = cls()
        p.cash = d.get('cash', INITIAL_CAPITAL)
        p.total_value = d.get('total_value', INITIAL_CAPITAL)
        p.peak_value = d.get('peak_value', INITIAL_CAPITAL)
        p.positions = d.get('positions', [])
        p.closed_trades = d.get('closed_trades', [])
        p.total_trades = d.get('total_trades', 0)
        p.winning_trades = d.get('winning_trades', 0)
        p.losing_trades = d.get('losing_trades', 0)
        p.total_pnl = d.get('total_pnl', 0.0)
        p.daily_pnl = d.get('daily_pnl', 0.0)
        p.last_updated = d.get('last_updated', '')
        p.risk_multiplier = d.get('risk_multiplier', 1.0)
        return p


# ──────────────────────────────────────────────────────────────────
# STRATEGY MEMORY & LEARNING
# ──────────────────────────────────────────────────────────────────
class TradingMemory:
    """
    Self-improving memory system that learns from every trade.
    Tracks:
      - Per-strategy performance with win rates
      - Market regime detection and strategy suitability
      - Lessons learned from big wins/losses
      - Adaptive position sizing
    """

    def __init__(self, filepath: Path = MEMORY_FILE):
        self.filepath = filepath
        self.data = self._load()

    def _load(self) -> dict:
        if self.filepath.exists():
            try:
                with open(self.filepath) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._default_memory()

    def _default_memory(self) -> dict:
        return {
            'strategy_stats': {
                'darvas_breakout': {'trades': 0, 'wins': 0, 'losses': 0, 'total_pnl': 0.0,
                                    'avg_win': 0.0, 'avg_loss': 0.0, 'win_rate': 0.0,
                                    'consecutive_wins': 0, 'consecutive_losses': 0,
                                    'max_drawdown': 0.0, 'allocation': 0.40},
                'mean_reversion': {'trades': 0, 'wins': 0, 'losses': 0, 'total_pnl': 0.0,
                                   'avg_win': 0.0, 'avg_loss': 0.0, 'win_rate': 0.0,
                                   'consecutive_wins': 0, 'consecutive_losses': 0,
                                   'max_drawdown': 0.0, 'allocation': 0.20},
                'momentum': {'trades': 0, 'wins': 0, 'losses': 0, 'total_pnl': 0.0,
                             'avg_win': 0.0, 'avg_loss': 0.0, 'win_rate': 0.0,
                             'consecutive_wins': 0, 'consecutive_losses': 0,
                             'max_drawdown': 0.0, 'allocation': 0.25},
                'gap_trading': {'trades': 0, 'wins': 0, 'losses': 0, 'total_pnl': 0.0,
                                'avg_win': 0.0, 'avg_loss': 0.0, 'win_rate': 0.0,
                                'consecutive_wins': 0, 'consecutive_losses': 0,
                                'max_drawdown': 0.0, 'allocation': 0.15},
            },
            'market_regime_history': [],
            'lessons': [],
            'current_regime': 'unknown',
            'vix_context': '',
            'last_optimization': '',
        }

    def save(self):
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, 'w') as f:
            json.dump(self.data, f, indent=2)

    def record_trade(self, trade: dict):
        """Record a completed trade and update strategy stats."""
        strategy = trade.get('strategy', 'darvas_breakout')
        pnl = trade.get('pnl', 0.0)
        won = pnl > 0

        stats = self.data['strategy_stats'].get(strategy)
        if not stats:
            stats = self.data['strategy_stats'][strategy] = {
                'trades': 0, 'wins': 0, 'losses': 0, 'total_pnl': 0.0,
                'avg_win': 0.0, 'avg_loss': 0.0, 'win_rate': 0.0,
                'consecutive_wins': 0, 'consecutive_losses': 0,
                'max_drawdown': 0.0, 'allocation': 0.20
            }

        stats['trades'] += 1
        stats['total_pnl'] = round(stats['total_pnl'] + pnl, 2)

        if won:
            stats['wins'] += 1
            stats['consecutive_wins'] += 1
            stats['consecutive_losses'] = 0
            # Update avg win
            if stats['avg_win'] == 0:
                stats['avg_win'] = round(pnl, 2)
            else:
                stats['avg_win'] = round((stats['avg_win'] * (stats['wins'] - 1) + pnl) / stats['wins'], 2)
        else:
            stats['losses'] += 1
            stats['consecutive_losses'] += 1
            stats['consecutive_wins'] = 0
            # Update avg loss
            if stats['avg_loss'] == 0:
                stats['avg_loss'] = round(abs(pnl), 2)
            else:
                stats['avg_loss'] = round((stats['avg_loss'] * (stats['losses'] - 1) + abs(pnl)) / stats['losses'], 2)

        # Win rate
        if stats['trades'] > 0:
            stats['win_rate'] = round((stats['wins'] / stats['trades']) * 100, 1)

        # Track drawdown
        trade_pnl_pct = trade.get('pnl_pct', 0.0)
        if trade_pnl_pct < 0:
            stats['max_drawdown'] = min(stats['max_drawdown'], trade_pnl_pct)

        # Auto-adjust allocation based on performance
        self._adjust_allocation(strategy, stats)

        # Learn from significant trades (>5% move)
        pnl_pct = abs(trade.get('pnl_pct', 0))
        if pnl_pct > 5.0:
            lesson = self._generate_lesson(trade)
            if lesson:
                self.data['lessons'].append(lesson)

        self.save()

    def _adjust_allocation(self, strategy: str, stats: dict):
        """Adjust strategy allocation based on recent performance."""
        if stats['trades'] < 5:
            return  # Not enough data

        base_allocations = {
            'darvas_breakout': 0.40,
            'mean_reversion': 0.20,
            'momentum': 0.25,
            'gap_trading': 0.15,
        }

        wr = stats['win_rate']
        allocation = base_allocations.get(strategy, 0.20)

        if wr >= 65:
            allocation = min(allocation * 1.2, 0.50)
        elif wr < 40:
            allocation = max(allocation * 0.75, 0.05)

        # Reduce if consecutive losses > 3
        if stats['consecutive_losses'] >= 3:
            allocation *= 0.5

        # Reduce if max drawdown > -10%
        if stats['max_drawdown'] < -10.0:
            allocation *= 0.6

        stats['allocation'] = round(allocation, 2)

    def _generate_lesson(self, trade: dict) -> Optional[str]:
        """Generate a learning lesson from a significant trade."""
        symbol = trade.get('symbol', '')
        strategy = trade.get('strategy', '')
        pnl_pct = trade.get('pnl_pct', 0.0)
        exit_reason = trade.get('exit_reason', '')
        notes = trade.get('notes', '')

        if pnl_pct > 5.0:
            return {
                'date': datetime.date.today().isoformat(),
                'type': 'win',
                'symbol': symbol,
                'strategy': strategy,
                'lesson': f"Big win on {symbol} ({strategy}): +{pnl_pct:.1f}%. "
                          f"Exit: {exit_reason}. Key: {notes or 'Follow the system.'}",
                'pnl_pct': pnl_pct,
            }
        elif pnl_pct < -5.0:
            return {
                'date': datetime.date.today().isoformat(),
                'type': 'loss',
                'symbol': symbol,
                'strategy': strategy,
                'lesson': f"Big loss on {symbol} ({strategy}): {pnl_pct:.1f}%. "
                          f"Exit: {exit_reason}. Lesson: {notes or 'Review stop-loss placement.'}",
                'pnl_pct': pnl_pct,
            }
        return None

    def get_best_strategy(self) -> str:
        """Get the best-performing strategy based on recent win rate."""
        best = 'darvas_breakout'
        best_wr = 0
        for s, stats in self.data['strategy_stats'].items():
            if stats['trades'] >= 3 and stats['win_rate'] > best_wr:
                best_wr = stats['win_rate']
                best = s
        return best

    def get_strategy_allocation(self, strategy: str) -> float:
        return self.data['strategy_stats'].get(strategy, {}).get('allocation', 0.20)

    def record_market_regime(self, regime: str, nifty_change: float, vix: float):
        """Record daily market regime for pattern learning."""
        today = datetime.date.today().isoformat()
        entry = {
            'date': today,
            'regime': regime,
            'nifty_change': round(nifty_change, 2),
            'vix': round(vix, 2),
        }
        self.data['market_regime_history'].append(entry)
        # Keep last 60 days
        self.data['market_regime_history'] = self.data['market_regime_history'][-60:]
        self.data['current_regime'] = regime
        self.save()

    def get_market_summary(self) -> str:
        """Get a summary of recent market conditions."""
        history = self.data['market_regime_history'][-10:]
        if not history:
            return "No recent market data."

        regimes = [h['regime'] for h in history]
        trending_days = sum(1 for r in regimes if 'TRENDING' in r)
        sideways_days = sum(1 for r in regimes if 'SIDEWAYS' in r)

        return f"Last 10 days: {trending_days} trending, {sideways_days} sideways"


# ──────────────────────────────────────────────────────────────────
# MAIN TRADING ENGINE
# ──────────────────────────────────────────────────────────────────
class DarvasPaperTrader:
    """
    The brain behind the operation.
    Analyzes NSE stocks, identifies Darvas box breakouts,
    executes paper trades, tracks portfolio, and learns.
    """

    def __init__(self):
        self.portfolio = Portfolio()
        self.memory = TradingMemory()
        self.darvas = IndianStockMonitor()
        self.indicators = TechnicalIndicators()
        self.today_pnl = 0.0
        self.report_sections = []
        self._load_state()

    # ─── State Persistence ──────────────────────────────────────────

    def _load_state(self):
        """Load portfolio state from disk."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    data = json.load(f)
                self.portfolio = Portfolio.from_dict(data)
            except (json.JSONDecodeError, IOError):
                pass

    def _save_state(self):
        """Save portfolio state to disk."""
        self.portfolio.last_updated = datetime.datetime.now().isoformat()
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(self.portfolio.to_dict(), f, indent=2)

    # ─── Market Data ─────────────────────────────────────────────────

    def _get_close_series(self, df: pd.DataFrame) -> pd.Series:
        """Extract close prices from yfinance DataFrame (handles MultiIndex)."""
        if isinstance(df.columns, pd.MultiIndex):
            close_col = ('Close', df.columns.get_level_values(1)[0])
            if close_col in df.columns:
                return df[close_col]
            # Fallback: take first Close column
            close_cols = [c for c in df.columns if c[0] == 'Close']
            if close_cols:
                return df[close_cols[0]]
        return df['Close'] if 'Close' in df.columns else df.iloc[:, 0]

    def _get_scalar(self, series: pd.Series) -> float:
        """Get a scalar float from a potentially 1-element Series."""
        if isinstance(series, pd.Series):
            return float(series.iloc[0])
        return float(series)

    def fetch_market_snapshot(self) -> dict:
        """Fetch NIFTY 50, Bank Nifty, VIX, and sector data."""
        snapshot = {
            'nifty': None, 'bank_nifty': None, 'vix': None,
            'nifty_change': 0, 'bank_nifty_change': 0,
            'sectors': {},
            'timestamp': datetime.datetime.now().isoformat(),
            'error': None,
        }

        try:
            import yfinance as yf

            # NIFTY 50
            nifty = yf.download("^NSEI", period="5d", interval="1d", progress=False)
            if not nifty.empty:
                nifty_close = self._get_close_series(nifty)
                snapshot['nifty'] = self._get_scalar(nifty_close.iloc[-1:])
                if len(nifty_close) >= 2:
                    prev = self._get_scalar(nifty_close.iloc[-2:-1])
                    curr = self._get_scalar(nifty_close.iloc[-1:])
                    snapshot['nifty_change'] = round(((curr - prev) / prev) * 100, 2)

            # Bank Nifty
            banknifty = yf.download("^NSEBANK", period="5d", interval="1d", progress=False)
            if not banknifty.empty:
                banknifty_close = self._get_close_series(banknifty)
                snapshot['bank_nifty'] = self._get_scalar(banknifty_close.iloc[-1:])
                if len(banknifty_close) >= 2:
                    prev = self._get_scalar(banknifty_close.iloc[-2:-1])
                    curr = self._get_scalar(banknifty_close.iloc[-1:])
                    snapshot['bank_nifty_change'] = round(((curr - prev) / prev) * 100, 2)

            # VIX
            try:
                vix = yf.download("^INDIAVIX", period="5d", interval="1d", progress=False)
                if not vix.empty:
                    vix_close = self._get_close_series(vix)
                    snapshot['vix'] = self._get_scalar(vix_close.iloc[-1:])
            except Exception:
                snapshot['vix'] = 15.0  # default fallback

        except Exception as e:
            snapshot['error'] = str(e)

        return snapshot

    def _clean_stock_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean yfinance DataFrame to standard column names (open, high, low, close, volume)."""
        if df.empty:
            return df
        # Handle MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            # Get the ticker from the second level
            ticker = df.columns.get_level_values(1)[0]
            df = df.xs(ticker, axis=1, level=1)
        # Rename to lowercase
        rename_map = {}
        for col in df.columns:
            col_lower = str(col).lower()
            if col_lower in ('open', 'high', 'low', 'close', 'volume'):
                rename_map[col] = col_lower
        df = df.rename(columns=rename_map)
        return df

    def analyze_stock_universe(self) -> List[dict]:
        """Analyze all stocks in the NSE watchlist for trading opportunities."""
        results = []

        # Suppress yfinance verbose logging
        import logging
        logging.getLogger('yfinance').setLevel(logging.ERROR)
        import yfinance as yf

        for i, symbol in enumerate(NSE_WATCHLIST):
            try:
                df = yf.download(symbol, period="3mo", interval="1d", progress=False)
                if df.empty or len(df) < 20:
                    continue

                df = self._clean_stock_df(df)

                # Darvas Box Detection
                boxes = self.darvas.darvas_detector.detect_boxes(df)
                breakouts = self.darvas.darvas_detector.find_breakouts(df, boxes)

                # Technical Indicators
                tech = self.indicators.calculate_all(df)

                # Trend
                trends = self.darvas.trend_detector.calculate_trend(df)
                trend = self.darvas.trend_detector.check_trend_alignment(
                    float(df['close'].iloc[-1]), trends
                )

                current_price = float(df['close'].iloc[-1])
                volume_avg = float(df['volume'].tail(20).mean())
                current_volume = float(df['volume'].iloc[-1])
                volume_ratio = current_volume / max(volume_avg, 1)

                # ATR for position sizing
                atr_val = self.indicators.atr(df['high'], df['low'], df['close'])

                # Build result
                result = {
                    'symbol': symbol,
                    'name': symbol.replace('.NS', ''),
                    'price': round(current_price, 2),
                    'change_pct': round(
                        ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100, 2
                    ) if len(df) >= 2 else 0,
                    'volume_ratio': round(volume_ratio, 2),
                    'atr': round(atr_val, 2) if atr_val else 0,
                    'trend': trend,
                    'boxes': len(boxes),
                    'breakouts': breakouts,
                    'rsi': round(tech['rsi'], 1) if tech['rsi'] else 50,
                    'adx': round(tech['adx']['adx'], 1) if tech['adx']['adx'] else 0,
                    'bollinger_upper': round(tech['bollinger']['upper'], 2) if tech['bollinger']['upper'] else 0,
                    'bollinger_lower': round(tech['bollinger']['lower'], 2) if tech['bollinger']['lower'] else 0,
                    'ema_12': round(tech['ema_12'], 2) if tech['ema_12'] else 0,
                    'momentum_10d': round(tech['momentum_10d'], 2) if tech['momentum_10d'] else 0,
                    'macd_histogram': round(tech['macd']['histogram'], 2) if tech['macd']['histogram'] else 0,
                    'active_box_high': round(boxes[-1]['high'], 2) if boxes else 0,
                    'active_box_low': round(boxes[-1]['low'], 2) if boxes else 0,
                }
                results.append(result)

            except Exception as e:
                # Silently skip stocks that fail to load
                continue

        return results

    # ─── Signal Generation ──────────────────────────────────────────

    def generate_signals(self, analysis: List[dict]) -> List[dict]:
        """Generate trading signals using Darvas + backup strategies."""
        signals = []
        active_symbols = {p['symbol'] for p in self.portfolio.positions}
        today = datetime.date.today()
        three_days_ago = today - datetime.timedelta(days=5)  # Look back 5 calendar days

        for stock in analysis:
            symbol = stock['symbol']
            if symbol in active_symbols:
                continue  # Already in a position

            price = stock['price']
            box_high = stock['active_box_high']
            box_low = stock['active_box_low']

            # ─── Primary: Darvas Box Breakout ───────────────────────
            # Check if price just broke above the most recent box high
            if box_high > 0 and price > box_high:
                # Check breakout magnitude (1-5% above box high is ideal)
                breakout_pct = ((price - box_high) / box_high) * 100
                if 0.5 <= breakout_pct <= 10:
                    # Volume confirmation check
                    vol_confirmed = stock['volume_ratio'] >= MIN_VOLUME_MULTIPLIER
                    
                    # Determine signal strength
                    is_strong = (
                        breakout_pct >= 2.0
                        and vol_confirmed
                        and 'UPTREND' in stock['trend']
                        and stock['rsi'] < 70
                    )
                    is_moderate = (
                        breakout_pct >= 1.0
                        and (vol_confirmed or stock['rsi'] < 65)
                    )

                    if is_strong or is_moderate:
                        stop_loss = round(max(box_low * 0.97, price * 0.93), 2)
                        signals.append({
                            'symbol': symbol,
                            'name': stock['name'],
                            'strategy': 'darvas_breakout',
                            'price': price,
                            'entry_zone': (round(price * 0.995, 2), price),
                            'stop_loss': stop_loss,
                            'target_1': round(price * (1 + breakout_pct / 100 + 0.03), 2),
                            'target_2': round(price * (1 + breakout_pct / 100 + 0.06), 2),
                            'signal_strength': 'STRONG' if is_strong else 'MODERATE',
                            'box_high': box_high,
                            'box_low': box_low,
                            'volume_ratio': stock['volume_ratio'],
                            'confidence': min(50 + breakout_pct * 10 + (20 if vol_confirmed else 0), 95) if is_strong else min(40 + breakout_pct * 8, 70),
                            'trend': stock['trend'],
                            'patterns': [],
                            'reason': (
                                f"Darvas breakout: ₹{box_high:,.0f}→₹{price:,.0f} "
                                f"({breakout_pct:.1f}%) | Vol: {stock['volume_ratio']:.1f}x | "
                                f"RSI: {stock['rsi']} | Trend: {stock['trend']}"
                            ),
                            'atr': stock['atr'],
                            'rsi': stock['rsi'],
                            'adx': stock['adx'],
                        })

            # ─── Backup 1: Mean Reversion (RSI oversold bounce) ────
            elif (stock['rsi'] < 30 and stock['momentum_10d'] < -3
                  and stock['trend'] in ('MODERATE_UPTREND', 'STRONG_UPTREND', 'NO_CLEAR_TREND')
                  and stock['volume_ratio'] < 1.5):  # No panic selling
                signals.append({
                    'symbol': symbol,
                    'name': stock['name'],
                    'strategy': 'mean_reversion',
                    'price': price,
                    'entry_zone': (round(price * 0.99, 2), price),
                    'stop_loss': round(price * 0.95, 2),
                    'target_1': round(price * 1.04, 2),
                    'target_2': round(price * 1.07, 2),
                    'signal_strength': 'MODERATE',
                    'box_high': 0, 'box_low': 0,
                    'volume_ratio': stock['volume_ratio'],
                    'confidence': max(30, 80 - stock['rsi'] * 1.5),
                    'trend': stock['trend'],
                    'patterns': [],
                    'reason': (
                        f"Mean reversion: RSI {stock['rsi']} oversold, "
                        f"10d mom: {stock['momentum_10d']:.1f}%. "
                        f"Trend: {stock['trend']}"
                    ),
                    'atr': stock['atr'], 'rsi': stock['rsi'], 'adx': stock['adx'],
                })

            # ─── Backup 2: Momentum (ADX trending + volume) ────────
            if (stock['adx'] >= 25
                    and stock['rsi'] < 70
                    and stock['rsi'] > 45
                    and stock['volume_ratio'] >= 1.2
                    and stock['momentum_10d'] >= 3
                    and stock['trend'] in ('STRONG_UPTREND', 'MODERATE_UPTREND')):
                signals.append({
                    'symbol': symbol,
                    'name': stock['name'],
                    'strategy': 'momentum',
                    'price': price,
                    'entry_zone': (round(price * 0.995, 2), round(price * 1.005, 2)),
                    'stop_loss': round(price * 0.95, 2),
                    'target_1': round(price * 1.06, 2),
                    'target_2': round(price * 1.10, 2),
                    'signal_strength': 'MODERATE',
                    'box_high': 0, 'box_low': 0,
                    'volume_ratio': stock['volume_ratio'],
                    'confidence': min(stock['adx'] * 2 + stock['momentum_10d'] * 3, 85),
                    'trend': stock['trend'],
                    'patterns': [],
                    'reason': (
                        f"Momentum: ADX {stock['adx']} trending, "
                        f"{stock['momentum_10d']:.1f}% in 10d, Vol {stock['volume_ratio']:.1f}x. "
                        f"RSI {stock['rsi']} in sweet spot."
                    ),
                    'atr': stock['atr'], 'rsi': stock['rsi'], 'adx': stock['adx'],
                })

            # ─── Backup 3: Strong sector leader breakout (gap + volume) ──
            if (stock['change_pct'] > 2.0
                    and stock['volume_ratio'] > 1.8
                    and stock['trend'] in ('STRONG_UPTREND', 'MODERATE_UPTREND')
                    and stock['rsi'] < 75
                    and stock['rsi'] > 40):
                signals.append({
                    'symbol': symbol,
                    'name': stock['name'],
                    'strategy': 'gap_trading',
                    'price': price,
                    'entry_zone': (price, round(price * 1.01, 2)),
                    'stop_loss': round(price * 0.97, 2),
                    'target_1': round(price * 1.035, 2),
                    'target_2': round(price * 1.06, 2),
                    'signal_strength': 'MODERATE',
                    'box_high': 0, 'box_low': 0,
                    'volume_ratio': stock['volume_ratio'],
                    'confidence': min(stock['change_pct'] * 12 + stock['volume_ratio'] * 10, 80),
                    'trend': stock['trend'],
                    'patterns': [],
                    'reason': (
                        f"Gap-up: {stock['change_pct']:.1f}% today with "
                        f"{stock['volume_ratio']:.1f}x volume. RSI {stock['rsi']}. "
                        f"Trend: {stock['trend']}"
                    ),
                    'atr': stock['atr'], 'rsi': stock['rsi'], 'adx': stock['adx'],
                })

        # Sort by confidence descending, deduplicate (keep highest confidence per symbol)
        signals.sort(key=lambda s: s['confidence'], reverse=True)
        seen_symbols = set()
        deduped = []
        for sig in signals:
            if sig['symbol'] not in seen_symbols:
                deduped.append(sig)
                seen_symbols.add(sig['symbol'])
        return deduped[:10]

    # ─── Trade Execution ────────────────────────────────────────────

    def should_trade_today(self, snapshot: dict) -> bool:
        """Check if conditions are favorable for trading."""
        # Stop trading if daily loss limit hit
        if self.today_pnl <= -INITIAL_CAPITAL * MAX_DAILY_LOSS_PCT:
            self._add_report("🚫 **TRADING HALTED** — Daily loss limit reached (-5%)")
            return False

        # Check market open (weekday, reasonable hours)
        now = datetime.datetime.now()
        if now.weekday() >= 5:
            return False  # Weekend

        # Check if NSE is likely open (9:15 AM - 3:30 PM IST)
        # We run after market close typically, so proceed
        return True

    def execute_signals(self, signals: List[dict], snapshot: dict) -> List[dict]:
        """Execute paper trades based on generated signals."""
        executed = []
        available_cash = self.portfolio.cash

        for signal in signals:
            # Check position limit
            if len(self.portfolio.positions) >= MAX_POSITIONS:
                break

            # Determine position size based on strategy allocation & risk
            strategy = signal['strategy']
            allocation = self.memory.get_strategy_allocation(strategy)
            strategy_capital = available_cash * allocation

            # Risk-based sizing: 2% of capital / distance to stop
            entry_price = signal['entry_zone'][0]
            stop_distance = abs(entry_price - signal['stop_loss']) / entry_price

            if stop_distance <= 0:
                continue

            risk_amount = min(
                available_cash * MAX_RISK_PER_TRADE * self.portfolio.risk_multiplier,
                strategy_capital * MAX_RISK_PER_TRADE * 2 * self.portfolio.risk_multiplier
            )
            quantity = max(1, int(risk_amount / (entry_price * stop_distance)))

            # Ensure minimum investment of ₹5,000
            investment = quantity * entry_price
            if investment < 5000:
                quantity = max(1, int(5000 / entry_price))
                investment = quantity * entry_price

            # Check available cash
            if investment > available_cash:
                quantity = max(1, int(available_cash / entry_price))
                investment = quantity * entry_price
                if investment < 5000:
                    continue  # Skip if can't afford minimum

            # Generate trade ID
            trade_id = hashlib.md5(
                f"{signal['symbol']}_{datetime.date.today()}_{time.time()}".encode()
            ).hexdigest()[:12]

            # Create trade
            trade = {
                'id': trade_id,
                'symbol': signal['symbol'],
                'entry_price': entry_price,
                'entry_date': datetime.date.today().isoformat(),
                'quantity': quantity,
                'side': 'BUY',
                'strategy': strategy,
                'box_high': signal.get('box_high', 0),
                'box_low': signal.get('box_low', 0),
                'stop_loss': signal['stop_loss'],
                'target_1': signal['target_1'],
                'target_2': signal['target_2'],
                'exit_price': None,
                'exit_date': None,
                'exit_reason': None,
                'pnl': None,
                'pnl_pct': None,
                'entry_signal_strength': signal['signal_strength'],
                'max_favorable_excursion': 0.0,
                'max_adverse_excursion': 0.0,
                'notes': signal['reason'],
            }

            # Execute
            brokerage = entry_price * quantity * BROKERAGE_PCT * 2  # Entry + exit
            self.portfolio.cash -= investment + brokerage
            self.portfolio.positions.append(trade)

            executed.append(trade)
            available_cash = self.portfolio.cash

            self._add_report(
                f"📈 **{signal['strategy'].replace('_', ' ').title()}**\n"
                f"• {signal['name']} ({signal['symbol']}) @ ₹{entry_price:,.2f}\n"
                f"• Qty: {quantity} | Investment: ₹{investment:,.0f}\n"
                f"• SL: ₹{signal['stop_loss']:,.2f} | T1: ₹{signal['target_1']:,.2f} | T2: ₹{signal['target_2']:,.2f}\n"
                f"• RS: {signal.get('rsi', 'N/A')} | ADX: {signal.get('adx', 'N/A')}\n"
                f"• {signal['reason']}"
            )

        return executed

    # ─── Position Management ────────────────────────────────────────

    def update_positions(self, analysis_map: dict):
        """Check open positions against current prices and manage exits."""
        today = datetime.date.today().isoformat()
        positions_to_close = []

        for i, pos in enumerate(self.portfolio.positions):
            symbol = pos['symbol']
            stock = analysis_map.get(symbol)
            if not stock:
                continue

            current_price = stock['price']
            entry_price = pos['entry_price']
            quantity = pos['quantity']

            # Track excursion
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
            if pnl_pct > pos['max_favorable_excursion']:
                pos['max_favorable_excursion'] = round(pnl_pct, 2)
            if pnl_pct < pos['max_adverse_excursion']:
                pos['max_adverse_excursion'] = round(pnl_pct, 2)

            # Check exit conditions
            exit_reason = None

            # 1. Stop Loss hit
            if current_price <= pos['stop_loss']:
                exit_reason = "stop_loss"

            # 2. Target 2 hit (take full profit)
            elif current_price >= pos['target_2']:
                exit_reason = "target_hit"

            # 3. Trailing stop (if >5% profit, trail at 3% from peak)
            if pos['max_favorable_excursion'] > 5.0:
                trail_stop = entry_price * (1 + (pos['max_favorable_excursion'] - 3.0) / 100)
                if current_price < trail_stop:
                    exit_reason = "trailing_stop"

            # 4. Time exit (14 days holding max for swing)
            if pos.get('entry_date'):
                try:
                    entry_date = datetime.date.fromisoformat(pos['entry_date'])
                    days_held = (datetime.date.today() - entry_date).days
                    if days_held >= 14:
                        exit_reason = "time_exit"
                except ValueError:
                    pass

            # 5. Trend reversal
            if stock['trend'] in ('NO_CLEAR_TREND',) and pnl_pct < 0:
                exit_reason = "trend_reversal"

            if exit_reason:
                # Calculate P&L
                pnl = (current_price - entry_price) * quantity
                pnl_pct_final = ((current_price - entry_price) / entry_price) * 100
                brokerage = entry_price * quantity * BROKERAGE_PCT  # Exit only
                stt = current_price * quantity * STT_PCT if pnl > 0 else 0
                net_pnl = round(pnl - brokerage - stt, 2)

                # Update trade record
                pos['exit_price'] = current_price
                pos['exit_date'] = today
                pos['exit_reason'] = exit_reason
                pos['pnl'] = net_pnl
                pos['pnl_pct'] = round(pnl_pct_final, 2)

                # Update portfolio
                self.portfolio.cash += current_price * quantity - brokerage - stt
                self.portfolio.total_trades += 1
                self.portfolio.total_pnl += net_pnl
                self.today_pnl += net_pnl

                if net_pnl > 0:
                    self.portfolio.winning_trades += 1
                else:
                    self.portfolio.losing_trades += 1

                # Record in memory
                self.memory.record_trade(pos)

                # Schedule for removal
                positions_to_close.append(i)

                # Report
                emoji = "✅" if net_pnl > 0 else "❌"
                self._add_report(
                    f"{emoji} **CLOSED**: {pos['symbol'].replace('.NS', '')}\n"
                    f"   Entry: ₹{entry_price:,.2f} → Exit: ₹{current_price:,.2f}\n"
                    f"   P&L: ₹{net_pnl:+,.0f} ({pos['pnl_pct']:+.1f}%)\n"
                    f"   Reason: {exit_reason.replace('_', ' ').title()}\n"
                    f"   Strategy: {pos['strategy'].replace('_', ' ').title()}"
                )

        # Remove closed positions (reverse order to preserve indices)
        for idx in sorted(positions_to_close, reverse=True):
            self.portfolio.closed_trades.append(self.portfolio.positions.pop(idx))

        # Keep only last 200 closed trades
        self.portfolio.closed_trades = self.portfolio.closed_trades[-200:]

    # ─── Reporting ──────────────────────────────────────────────────

    def _add_report(self, section: str):
        self.report_sections.append(section)

    def generate_telegram_report(self, snapshot: dict, signals: List[dict],
                                  analysis: List[dict]) -> str:
        """Generate a comprehensive Telegram-ready report."""
        today = datetime.date.today().isoformat()
        lines = []
        emoji_arrow = "📈" if snapshot.get('nifty_change', 0) >= 0 else "📉"

        # ─── Header ────────────────────────────────────────────────
        lines.append(f"🏛️ **DARVAS PAPER TRADER** | {today}")
        lines.append("═" * 35)

        # ─── Market Overview ────────────────────────────────────────
        lines.append(f"\n📊 **MARKET OVERVIEW**")
        lines.append(f"{emoji_arrow} NIFTY: {snapshot.get('nifty', 'N/A'):,.0f} ({snapshot.get('nifty_change', 0):+.2f}%)")
        if snapshot.get('bank_nifty'):
            lines.append(f"🏦 Bank Nifty: {snapshot['bank_nifty']:,.0f} ({snapshot.get('bank_nifty_change', 0):+.2f}%)")
        if snapshot.get('vix'):
            vix = snapshot['vix']
            vix_note = "🟢 Low Vol" if vix < 18 else "🟡 Moderate Vol" if vix < 25 else "🔴 High Vol"
            lines.append(f"⚡ VIX: {vix:.2f} — {vix_note}")

        # ─── Portfolio Status ───────────────────────────────────────
        total_value = self.portfolio.cash
        for pos in self.portfolio.positions:
            pos_price = next(
                (s['price'] for s in analysis if s['symbol'] == pos['symbol']),
                pos['entry_price']
            )
            total_value += pos_price * pos['quantity']

        self.portfolio.total_value = round(total_value, 2)
        self.portfolio.peak_value = max(self.portfolio.peak_value, total_value)

        total_pnl = total_value - INITIAL_CAPITAL
        total_pnl_pct = (total_pnl / INITIAL_CAPITAL) * 100
        drawdown = ((total_value - self.portfolio.peak_value) / self.portfolio.peak_value) * 100

        lines.append(f"\n💰 **PORTFOLIO**")
        lines.append(f"• Cash: ₹{self.portfolio.cash:,.0f}")
        lines.append(f"• Total Value: ₹{total_value:,.0f}")
        lines.append(f"• P&L: ₹{total_pnl:+,.0f} ({total_pnl_pct:+.2f}%)")
        lines.append(f"• Today: ₹{self.today_pnl:+,.0f}")
        lines.append(f"• Peak: ₹{self.portfolio.peak_value:,.0f} | DD: {drawdown:.1f}%")
        lines.append(f"• Trades: {self.portfolio.total_trades} | "
                     f"W: {self.portfolio.winning_trades} L: {self.portfolio.losing_trades}")

        # ─── Open Positions ─────────────────────────────────────────
        if self.portfolio.positions:
            lines.append(f"\n📋 **OPEN POSITIONS ({len(self.portfolio.positions)})**")
            for pos in self.portfolio.positions:
                price = next(
                    (s['price'] for s in analysis if s['symbol'] == pos['symbol']),
                    pos['entry_price']
                )
                pnl = (price - pos['entry_price']) * pos['quantity']
                pnl_pct = ((price - pos['entry_price']) / pos['entry_price']) * 100
                symbol = pos['symbol'].replace('.NS', '')
                emoji = "🟢" if pnl >= 0 else "🔴"
                lines.append(
                    f"{emoji} {symbol} x{pos['quantity']} @ ₹{pos['entry_price']:,.0f} "
                    f"→ ₹{price:,.0f} ({pnl_pct:+.1f}%) SL:₹{pos['stop_loss']:,.0f}"
                )

        # ─── Trade Signals ──────────────────────────────────────────
        trade_reports = [s for s in self.report_sections if s.startswith("📈") or s.startswith("🟢") or s.startswith("❌") or s.startswith("✅")]
        if trade_reports:
            lines.append(f"\n⚡ **TODAY'S ACTIVITY**")
            for report in self.report_sections:
                lines.append("")
                lines.append(report)

        # ─── Top Signal Recommendations ────────────────────────────
        if signals:
            lines.append(f"\n🎯 **TOP TRADE SETUPS**")
            for i, sig in enumerate(signals[:5], 1):
                trend_icon = "🟢" if 'UPTREND' in sig['trend'] else "🟡"
                lines.append(
                    f"{i}. {trend_icon} **{sig['name']}** ({sig['strategy'].replace('_', ' ').title()})\n"
                    f"   Entry: ₹{sig['entry_zone'][0]:,.2f}–{sig['entry_zone'][1]:,.2f} | "
                    f"SL: ₹{sig['stop_loss']:,.0f}\n"
                    f"   T1: ₹{sig['target_1']:,.0f} | T2: ₹{sig['target_2']:,.0f}\n"
                    f"   Confidence: {sig['confidence']:.0f}% | "
                    f"RSI: {sig.get('rsi', 'N/A')} | ADX: {sig.get('adx', 'N/A')}"
                )

        # ─── Strategy Stats ─────────────────────────────────────────
        lines.append(f"\n📊 **STRATEGY PERFORMANCE**")
        for s_name, stats in sorted(self.memory.data['strategy_stats'].items()):
            if stats['trades'] > 0:
                wr = stats['win_rate']
                wr_emoji = "🟢" if wr >= 60 else "🟡" if wr >= 40 else "🔴"
                lines.append(
                    f"{wr_emoji} {s_name.replace('_', ' ').title()}: "
                    f"{stats['trades']}T | {wr:.0f}% WR | "
                    f"₹{stats['total_pnl']:+,.0f} | Alloc: {stats['allocation']*100:.0f}%"
                )

        # ─── Market Regime & Lessons ───────────────────────────────
        lines.append(f"\n🧠 **LEARNING & MARKET CONTEXT**")
        lines.append(f"• Regime: {self.memory.data['current_regime']}")
        lines.append(f"• {self.memory.get_market_summary()}")
        lines.append(f"• Best Strategy: {self.memory.get_best_strategy().replace('_', ' ').title()}")

        # Show recent lessons (last 2)
        lessons = self.memory.data['lessons'][-2:]
        if lessons:
            lines.append(f"\n📝 **Recent Lessons**")
            for lesson in lessons:
                lines.append(f"• {lesson['lesson']}")

        # ─── Footer ─────────────────────────────────────────────────
        lines.append("\n" + "─" * 35)
        lines.append("🤖 _Darvas Paper Trader v2.0 | Paper Trading Only_")
        lines.append("⚠️ _Not Financial Advice — Backtest Before Real Use_")

        return "\n".join(lines)

    # ─── Main Run ───────────────────────────────────────────────────

    def run(self) -> str:
        """Main execution: fetch data, analyze, trade, report."""
        self.report_sections = []
        self.today_pnl = 0.0
        today = datetime.date.today().isoformat()

        self._add_report(f"⏰ Running analysis for {today}")

        # Step 1: Fetch market snapshot
        self._add_report("📡 Fetching market data...")
        snapshot = self.fetch_market_snapshot()

        # Step 2: Check if we should trade
        if not self.should_trade_today(snapshot):
            report = self.generate_telegram_report(snapshot, [], [])
            self._save_state()
            return report

        # Step 3: Analyze stock universe
        self._add_report(f"🔍 Analyzing {len(NSE_WATCHLIST)} NSE stocks...")
        analysis = self.analyze_stock_universe()
        self._add_report(f"✓ Analyzed {len(analysis)} stocks")

        # Build analysis map for position updates
        analysis_map = {s['symbol']: s for s in analysis}

        # Step 4: Update existing positions (check exits)
        self.update_positions(analysis_map)

        # Step 5: Generate new signals
        signals = self.generate_signals(analysis)
        self.last_signals = signals  # Expose for Pro Trader gate filtering

        # Step 6: Execute signals
        if signals:
            self._add_report(f"💡 {len(signals)} potential setups found")
            executed = self.execute_signals(signals, snapshot)
            if executed:
                self._add_report(f"✅ {len(executed)} new positions opened")
            else:
                self._add_report("⏸️ No trades met risk criteria")
        else:
            self._add_report("⏸️ No actionable signals today")

        # Step 7: Detect market regime
        regime = self._detect_market_regime(snapshot, analysis)
        self.memory.record_market_regime(
            regime, snapshot.get('nifty_change', 0), snapshot.get('vix', 15)
        )

        # Step 8: Save state
        self._save_state()

        # Step 9: Generate report
        report = self.generate_telegram_report(snapshot, signals, analysis)

        # Save report to file
        os.makedirs(REPORT_DIR, exist_ok=True)
        report_file = REPORT_DIR / f"report_{today}.md"
        with open(report_file, 'w') as f:
            f.write(report)

        return report

    def _detect_market_regime(self, snapshot: dict, analysis: List[dict]) -> str:
        """Detect the current market regime."""
        nifty_change = snapshot.get('nifty_change', 0)
        vix = snapshot.get('vix', 15)
        advancers = sum(1 for s in analysis if s.get('change_pct', 0) > 0)
        decliners = sum(1 for s in analysis if s.get('change_pct', 0) < 0)
        total = len(analysis)

        if abs(nifty_change) < 0.5 and vix < 18:
            return "SIDEWAYS_LOW_VOL"
        elif abs(nifty_change) < 0.5:
            return "SIDEWAYS"
        elif nifty_change > 1.0 and vix > 20:
            return "STRONG_UPTREND_VOLATILE"
        elif nifty_change > 0.5:
            return "MODERATE_UPTREND"
        elif nifty_change < -1.0:
            return "STRONG_DOWNTREND"
        elif nifty_change < -0.5:
            return "MODERATE_DOWNTREND"
        else:
            return "NEUTRAL"


# ──────────────────────────────────────────────────────────────────
# SELF-IMPROVEMENT MODULE
# ──────────────────────────────────────────────────────────────────
class StrategyImproviser:
    """
    Post-run analysis that reviews today's decisions and improves
    the strategy for tomorrow. Runs after each trading session.
    """

    @staticmethod
    def review_and_improve(portfolio: Portfolio, memory: TradingMemory):
        """Review today's performance and adjust strategy parameters."""
        today = datetime.date.today().isoformat()
        improvements = []

        # 1. Check if any strategy consistently losing
        for strategy, stats in memory.data['strategy_stats'].items():
            if stats['trades'] >= 5 and stats['win_rate'] < 35:
                improvements.append(
                    f"⚠️ {strategy} win rate is {stats['win_rate']:.0f}% — "
                    f"reducing allocation to {max(stats['allocation'] * 0.5, 0.05)*100:.0f}%"
                )

        # 2. Check if stop losses are too tight based on ATR
        recent_trades = portfolio.closed_trades[-10:]
        stop_loss_hits = [t for t in recent_trades if t.get('exit_reason') == 'stop_loss']
        if len(stop_loss_hits) > len(recent_trades) * 0.4 and len(recent_trades) >= 5:
            improvements.append(
                f"⚠️ {len(stop_loss_hits)}/{len(recent_trades)} last trades hit stop-loss. "
                f"Consider widening stops by 10-15% based on ATR."
            )

        # 3. Check if profit targets are too conservative
        target_hits = [t for t in recent_trades if t.get('exit_reason') == 'target_hit']
        if target_hits:
            avg_move_after_exit = 0
            for t in target_hits:
                if t.get('max_favorable_excursion', 0) > t.get('pnl_pct', 0):
                    avg_move_after_exit += t['max_favorable_excursion'] - t['pnl_pct']
            if avg_move_after_exit > 0 and len(target_hits) > 0:
                avg_extra = avg_move_after_exit / len(target_hits)
                if avg_extra > 2.0:
                    improvements.append(
                        f"📈 Stocks moved {avg_extra:.1f}% more after hitting targets. "
                        f"Consider trailing stops instead of fixed targets."
                    )

        # 4. Check regime mismatch
        regime = memory.data.get('current_regime', 'unknown')
        if 'DOWNTREND' in regime:
            improvements.append(
                f"🔴 Market in {regime}. Consider reducing position size by 30% "
                f"and focusing on mean reversion / defensive plays."
            )

        # 5. Market volatility adjustment
        vix_context = memory.data.get('vix_context', '')
        if 'High Vol' in vix_context:
            improvements.append(
                f"🟡 High volatility detected. Reduce leverage, widen stops."
            )

        return improvements


# ──────────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ──────────────────────────────────────────────────────────────────
def main():
    """Main entry point for the Darvas Paper Trader."""
    print("=" * 60)
    print("  DARVAS PAPER TRADER v2.0")
    print("  Pro-Level AI Trading Assistant")
    print("  Capital: ₹1,00,000 (Paper)")
    print("=" * 60)

    trader = DarvasPaperTrader()
    report = trader.run()

    # Run strategy improvisor
    improver = StrategyImproviser()
    improvements = improver.review_and_improve(trader.portfolio, trader.memory)

    # Print report
    print("\n" + report)

    if improvements:
        print("\n🔄 **STRATEGY IMPROVEMENTS**")
        for imp in improvements:
            print(f"  {imp}")
        print()

    # Save improvements note
    if improvements:
        today = datetime.date.today().isoformat()
        imp_file = REPORT_DIR / f"improvements_{today}.md"
        with open(imp_file, 'w') as f:
            f.write(f"# Strategy Improvements - {today}\n\n")
            for imp in improvements:
                f.write(f"- {imp}\n")

    print(f"\n📁 Report saved to: {REPORT_DIR / f'report_{datetime.date.today().isoformat()}.md'}")
    print(f"📁 State saved to: {STATE_FILE}")
    print(f"📁 Memory saved to: {MEMORY_FILE}")
    print(f"💰 Portfolio Value: ₹{trader.portfolio.total_value:,.0f}")
    print(f"📊 Total P&L: ₹{trader.portfolio.total_pnl:+,.0f}")
    print("=" * 60)

    return report


if __name__ == '__main__':
    report = main()
