#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════
  PRO TRADER PROFILE — Mindset, Pattern Recognition & Discipline Engine
  
  "Trade the setup, not the story. Let patterns speak, not noise."
  
  This module embodies the Pro Trader mindset — a systematic, disciplined
  approach to finding high-probability setups using Darvas box theory,
  volume confirmation, and multi-timeframe pattern correlation.
  
  THREE PILLARS:
  1. MINDSET — Strict rules, discipline framework, state tracking
  2. PATTERN RECOGNITION — The "Triad" scanner (Breakout + Reversal + Momentum)
  3. EXECUTION — Entry/exit discipline checklists, no-FOMO gates
  
  Integration: Works alongside DarvasPaperTrader as the mindset layer.
══════════════════════════════════════════════════════════════════════════════
"""

import json
import os
import datetime
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path

import pandas as pd
import numpy as np
import yfinance as yf

# ──────────────────────────────────────────────────────────────────────
# PROFILE LOCATION
# ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
PROFILE_FILE = SCRIPT_DIR / "pro_trader_profile.json"
PATTERN_LOG = SCRIPT_DIR / "pro_trader_patterns.json"
MINDSET_LOG = SCRIPT_DIR / "pro_trader_mindset_log.json"


# ═══════════════════════════════════════════════════════════════════════
# PILLAR 1: THE MINDSET — Discipline, Rules & State
# ═══════════════════════════════════════════════════════════════════════

GOLDEN_RULES = [
    # ─── Sacred Rules (NEVER Break) ───
    "1️⃣  2% RISK RULE: Never risk more than 2% of capital on any single trade.",
    "2️⃣  NO FOMO: A missed setup is better than a forced trade. Market opens tomorrow.",
    "3️⃣  PLAN THE TRADE, TRADE THE PLAN: Entry price, SL, targets written BEFORE execution.",
    "4️⃣  VOLUME CONFIRMS EVERYTHING: No volume = no conviction. Stay out.",
    "5️⃣  DARVAS RULE 1: Never chase. Wait for pullback to box top for entry.",
    "6️⃣  DARVAS RULE 2: Raise stops as box rises. Never let a winner become a loser.",
    "7️⃣  REGIME FIRST: Don't force breakouts in sideways markets. Match strategy to regime.",
    # ─── Professional Conduct ───
    "8️⃣  LOG EVERY TRADE: Include entry thesis, exit reason, emotions felt.",
    "9️⃣  MAX 3 LOSSES/DAY: After 3 consecutive losses, STOP. Review. Resume tomorrow.",
    "🔟  REVIEW WEEKLY: What worked? What didn't? What did I learn?",
]

MINDSET_STATES = {
    "DISCIPLINED": {
        "emoji": "🧘",
        "description": "Calm, methodical, following the plan. Best state for trading.",
        "allowed_actions": ["all"],
        "risk_multiplier": 1.0,
    },
    "CAUTIOUS": {
        "emoji": "⚠️",
        "description": "Market uncertain or after a loss. Reduce size, tighten filters.",
        "allowed_actions": ["reduce_size", "skip_low_conviction"],
        "risk_multiplier": 0.5,
    },
    "AGGRESSIVE": {
        "emoji": "🔥",
        "description": "Hot streak or euphoria. DANGER ZONE — revert to disciplined.",
        "allowed_actions": ["review_plan", "force_cool_off"],
        "risk_multiplier": 0.3,  # Reduce size when feeling aggressive
    },
    "TILTED": {
        "emoji": "🤬",
        "description": "Emotional, chasing losses. TRADING BANNED. Go walk.",
        "allowed_actions": ["stop_trading", "journal"],
        "risk_multiplier": 0.0,  # No trading allowed
    },
    "ANALYTICAL": {
        "emoji": "🔬",
        "description": "Review mode. No new trades. Study charts, refine plan.",
        "allowed_actions": ["analyze", "journal", "backtest"],
        "risk_multiplier": 0.0,
    },
}

# ─── Pattern Archetypes (The User's "Triad") ───

PATTERN_ARCHETYPES = {
    "BREAKOUT_MOMENTUM": {
        "name": "Darvas Breakout Runner",
        "emoji": "🚀",
        "description": "Stock breaking out of consolidation with volume. Strong trend, multiple box levels.",
        "examples": ["ATHERENERG.NS", "NEPHROPLUS.NS"],
        "characteristics": {
            "rsi_range": (55, 80),
            "daily_volatility_min": 2.0,
            "volume_breakout_min": 1.5,
            "sma_trend": "BULLISH",
            "breakout_count_6m_min": 2,
            "box_height_pct_min": 5.0,
            "recent_momentum": "positive",
        },
        "setup_rules": [
            "Price breaks above 20d box high with 1.5x+ volume",
            "RSI between 55-80 (strong but not exhausted)",
            "SMA20 > SMA50 (bullish alignment)",
            "Previous breakouts confirm pattern reliability",
            "Volume sustains above average for 2+ days after breakout",
        ],
        "entry": "Wait for first pullback to box top support after breakout",
        "stop_loss": "Below the previous box midpoint or 1.5x ATR",
        "target_1": "Next resistance level (prior high or round number)",
        "target_2": "1.5x box height projected upward",
    },
    "MEAN_REVERSION_SNAPBACK": {
        "name": "Oversold Snapback",
        "emoji": "🔄",
        "description": "Deeply oversold stock showing first signs of reversal. RSI < 30 and rising.",
        "examples": ["CENTUM.NS"],
        "characteristics": {
            "rsi_range": (15, 35),
            "rsi_momentum": "rising",
            "daily_volatility_min": 2.5,
            "volume_ratio_min": 0.8,
            "drawdown_3m_min": -20,
            "sma_trend": "BEARISH",  # Acceptable — this is a counter-trend play
        },
        "setup_rules": [
            "RSI below 35 AND rising (higher low on RSI vs price)",
            "Volume declining or normal (exhaustion, not panic)",
            "Price near 20d box bottom or support level",
            "Previous Darvas breakouts show stock CAN move",
            "No catastrophic news (check for company-specific events)",
        ],
        "entry": "First green candle after RSI turns up from oversold",
        "stop_loss": "Below the recent swing low or 1x ATR",
        "target_1": "Return to 20d SMA or box midpoint",
        "target_2": "Return to box top / 50d SMA",
    },
    "GAP_AND_GO": {
        "name": "Volume Breakout Continuation",
        "emoji": "⚡",
        "description": "Stock that gapped up on volume and is holding gains. Institutional accumulation.",
        "examples": ["NEPHROPLUS.NS"],
        "characteristics": {
            "gap_pct_min": 2.0,
            "volume_spike_min": 2.0,
            "rsi_range": (50, 75),
            "holds_above_gap": True,
        },
        "setup_rules": [
            "Gap up on 2x+ average volume",
            "Price holds above gap fill for 2+ sessions",
            "RSI not overbought (below 75)",
            "Higher lows forming after the gap",
        ],
        "entry": "Buy when price takes out the gap-day high with volume",
        "stop_loss": "Below the gap fill level",
        "target_1": "Previous resistance or 1.5x gap range",
    },
    "DIRECTIONAL_VOLATILITY_BULL": {
        "name": "Directional Volatility — Bull Runner",
        "emoji": "🏃‍♂️",
        "description": "High-volatility stock with strong upward directional bias. Multiple Darvas breakouts, volume confirmation, accelerating momentum.",
        "examples": ["ATHERENERG.NS", "NEPHROPLUS.NS"],
        "characteristics": {
            "min_daily_volatility": 2.5,
            "min_above_sma20_pct": 60,
            "max_rsi": 85,
            "min_near_52wh_pct": 80,
            "min_breakouts_6m": 2,
            "volume_trend": "rising_or_confirmed",
        },
        "setup_rules": [
            "Daily σ ≥ 2.5% (top-decile NSE volatility)",
            "≥ 60% of days above 20d SMA (strong uptrend consistency)",
            "Near 52W high (>80% of 52W range)",
            "Multiple Darvas breakouts with volume in last 6 months",
            "RSI < 85 (not exhausted)",
            "Volume confirming — either expanding or sustaining above average",
            "Big moves (>3%) happen on up days more than down days",
        ],
        "entry": "Pullback to 20d SMA or box top with volume confirmation",
        "stop_loss": "Below the last breakout box midpoint (1.5x ATR)",
        "target_1": "Previous resistance / prior high",
        "target_2": "1:1 risk-reward from entry to new 52W high projection",
    },
    "DIRECTIONAL_VOLATILITY_BEAR": {
        "name": "Directional Volatility — Bear Snapback",
        "emoji": "🔄",
        "description": "High-volatility stock in a deep downtrend but showing reversal signals. The snapback counterpart to DV-Bull.",
        "examples": ["CENTUM.NS"],
        "characteristics": {
            "min_daily_volatility": 2.5,
            "max_above_sma20_pct": 40,
            "rsi_range": (10, 40),
            "rsi_momentum": "rising",
            "max_near_52wh_pct": 70,
            "min_drawdown_3m": -20,
        },
        "setup_rules": [
            "Daily σ ≥ 2.5% (high volatility confirms it CAN move)",
            "≤ 40% of days above 20d SMA (strong downtrend — deep drawdown)",
            "RSI < 40 AND rising (oversold with momentum shift)",
            "Deep drawdown > 20% from high",
            "Volume NOT spiking on down days (selling exhaustion, not panic)",
            "Previous Darvas breakouts show the stock CAN move",
        ],
        "entry": "First green candle after RSI turns up from oversold, with volume confirmation",
        "stop_loss": "Below recent swing low or 1x ATR",
        "target_1": "Return to 20d SMA or box midpoint",
        "target_2": "Return to 50d SMA or prior box high",
    },
    "TRIAD_COMPOSITE": {
        "name": "Triad Pattern — Full System",
        "emoji": "🎯",
        "description": "Portfolio of 3 patterns that self-hedge: breakout runners + oversold snapback + momentum continuation.",
        "examples": ["ATHERENERG.NS + CENTUM.NS + NEPHROPLUS.NS"],
        "allocation": {
            "BREAKOUT_MOMENTUM": 0.50,
            "MEAN_REVERSION_SNAPBACK": 0.25,
            "GAP_AND_GO": 0.25,
        },
        "rules": [
            "Run scanner daily — scan for all 3 archetypes simultaneously",
            "Breakout runners get 50% allocation (high win rate, asymmetric upside)",
            "Oversold snapbacks get 25% (defined risk, quick resolution)",
            "Gap continuation gets 25% (institutional flow catching)",
            "Max 5 positions across all archetypes",
            "No two positions in same sector (diversify beta exposure)",
        ],
    },
    # ─── DARVAX PATTERNS (from DarvaX PDF by Amitabh Jha) ────────────
    "HIGH_DRY_FRY": {
        "name": "High Dry Fry — Baby Candle Base Blast",
        "emoji": "🍟",
        "description": "Stock surges 20-50% on high volume → corrects 10-20% → baby candle base forms → blasts 65%+. The signature DarvaX profit pattern.",
        "examples": ["BSL.NS (rose 40% in 3 days, corrected 18%, blasted 65% from base)"],
        "characteristics": {
            "surge_pct": (15, 60),
            "correction_pct": (8, 35),
            "min_base_days": 5,
            "volume_surge_min": 1.3,
            "volume_base_max": 0.8,
        },
        "setup_rules": [
            "First phase: 15-60% surge on 1.3x+ volume",
            "Second phase: 8-35% pullback from peak",
            "Third phase: 5+ days of small candle base (baby candles)",
            "Volume dries up during base formation (selling exhaustion)",
            "Entry: First move off base with volume confirmation",
        ],
        "entry": "Breakout from baby candle base with volume > 1.5x average",
        "stop_loss": "Below the baby candle base low",
        "target_1": "Previous swing high (before correction)",
        "target_2": "1.5x surge extension from base breakout",
    },
    "BULLISH_TASUKI": {
        "name": "Bullish Tasuki Line Reversal",
        "emoji": "🌅",
        "description": "Long bearish candle followed by gap-up bullish candle that closes above bear's high. Classic reversal that catches early trend change.",
        "examples": ["NFL.NS"],
        "characteristics": {
            "bear_body_min": 1.2,
            "gap_up_min": 1.0,
            "close_above_bear_high": True,
        },
        "setup_rules": [
            "Previous candle: long bearish (1.2x+ avg body)",
            "Current candle: opens gap up above bear's close",
            "Closes above bearish candle's highest price",
            "Volume surge on bullish candle = icing on the cake",
        ],
        "entry": "On bullish candle close above bearish high",
        "stop_loss": "Below the gap fill level or bearish candle low",
        "target_1": "Prior resistance before the bearish move",
        "target_2": "1:1 risk-reward from entry",
    },
    "INSIDE_BAR_BREAK": {
        "name": "Inside Bar Breakout",
        "emoji": "📦",
        "description": "Inside bar (range fully inside previous bar) followed by volume breakout above mother bar high. Tight consolidation before expansion.",
        "examples": [],
        "characteristics": {
            "tightness_max": 0.5,
            "breakout_vol_min": 1.5,
        },
        "setup_rules": [
            "Inside bar: current range fully inside previous bar's range",
            "Breakout candle must close above mother bar high",
            "Volume confirmation ≥ 1.5x average on breakout",
            "Tighter inside bar = stronger breakout potential",
        ],
        "entry": "Breakout above mother bar high with volume",
        "stop_loss": "Below inside bar low or mother bar midpoint",
        "target_1": "1x mother bar range projected upward",
        "target_2": "Prior resistance level",
    },
    "MORNING_STAR": {
        "name": "Morning Star Reversal",
        "emoji": "⭐",
        "description": "3-candle reversal: long bearish → small indecision doji → long bullish closing above bear midpoint. Bottom-fishing with high win rate.",
        "examples": [],
        "characteristics": {
            "bear_body_min": 1.3,
            "doji_max_body": 0.8,
            "bull_body_min": 1.2,
        },
        "setup_rules": [
            "Candle 1: Long bearish candle (1.3x+ avg body)",
            "Candle 2: Small body candle / doji (indecision)",
            "Candle 3: Long bullish candle closing above bear candle's midpoint",
            "Volume on bullish candle adds conviction",
        ],
        "entry": "On bullish candle close confirming reversal",
        "stop_loss": "Below the doji low or second swing low",
        "target_1": "Return to 20d SMA or pre-selloff level",
        "target_2": "Prior resistance before the selloff",
    },
    "DOUBLE_BOTTOM": {
        "name": "Double Bottom — W Reversal",
        "emoji": "🔵",
        "description": "W-shaped bottom with two swing lows at near-identical level. Neckline breakout projects target = neckline + (neckline - low). Classic high-RR pattern.",
        "examples": [],
        "characteristics": {
            "low_diff_max": 5,
            "min_swing_gap_days": 10,
        },
        "setup_rules": [
            "Two distinct swing lows within 5% of each other",
            "Minimum 10 trading days between lows",
            "Neckline: peak between the two lows",
            "Breakout confirmation: price above neckline with volume",
            "Target = neckline + (neckline - low)",
        ],
        "entry": "Price breaks above neckline with volume confirmation",
        "stop_loss": "Below the lower of the two bottoms",
        "target_1": "Neckline + (neckline - low) projection",
        "target_2": "1.5x the projection for extended targets",
    },
    "BABY_CRADLE": {
        "name": "Baby Cradle Consolidation",
        "emoji": "👶",
        "description": "Multiple tiny candlesticks clustering in tight range over 10-15 days. Coiled spring — accumulation before expansion.",
        "examples": [],
        "characteristics": {
            "max_range_pct": 10,
            "body_ratio_max": 0.8,
            "min_cradle_days": 8,
        },
        "setup_rules": [
            "Tight range < 10% over 10-15 trading days",
            "Average candle body < 60% of normal (baby candles)",
            "Volume typically declining (accumulation)",
            "Breaking out from cradle = expansion phase",
        ],
        "entry": "Breakout from cradle range with volume expansion",
        "stop_loss": "Below the cradle's lowest low",
        "target_1": "1x cradle range projected upward",
        "target_2": "Previous resistance level",
    },
    "DARVAX_JALWA": {
        "name": "DarvaX Jalwa — Box Breakout",
        "emoji": "🔥",
        "description": "Tight Darvas box with 3+ touchpoints on resistance. Multiple tests of box top before explosive volume breakout. Extra juicy.",
        "examples": [],
        "characteristics": {
            "box_range_min": 2,
            "box_range_max": 12,
            "min_touches": 2,
            "breakout_vol_min": 1.5,
        },
        "setup_rules": [
            "Tight Darvas box (2-12% range) over 10-day window",
            "2+ tests of box resistance (price near box high)",
            "Explosive volume breakout above box high",
            "Price holds above box after breakout",
        ],
        "entry": "Breakout above Darvas box high with 1.5x+ volume",
        "stop_loss": "Below the Darvas box low",
        "target_1": "1x box height projected upward",
        "target_2": "2x box height for extended targets",
    },
    "LAL_DABANGG": {
        "name": "Lal Dabangg — Red Hot Surge",
        "emoji": "🌶️",
        "description": "Massive green candle (3x+ avg body) on huge volume. Institutional buying surge — often at breakout or after consolidation.",
        "examples": [],
        "characteristics": {
            "body_ratio_min": 2.0,
            "vol_ratio_min": 1.5,
            "gain_pct_min": 2.0,
        },
        "setup_rules": [
            "Bullish candle with body 2x+ average body size",
            "Volume surge 1.5x+ average",
            "Gain of 3%+ in single candle",
            "Breakout from recent range adds conviction",
        ],
        "entry": "On close of the Dabangg candle if volume confirms",
        "stop_loss": "Below the Dabangg candle midpoint or 1.5x ATR",
        "target_1": "Next resistance level (prior high)",
        "target_2": "1.5x Dabangg candle range projected upward",
    },
    "ZIGZAG_FIB": {
        "name": "ZigZag + Fibonacci Golden Entry",
        "emoji": "📐",
        "description": "Price retraces to 61.8% Fibonacci from swing high → buy above 10 EMA → ride to next swing high. Combines ZigZag structure with golden ratio precision.",
        "examples": [],
        "characteristics": {
            "fib_level": 0.618,
            "deviation_max": 3,
            "above_ema10_required": True,
        },
        "setup_rules": [
            "Identify significant swing high and low via ZigZag",
            "Price retraces to 61.8% Fibonacci golden ratio level",
            "Buy signal confirmed when price > 10 EMA",
            "Ride trend until next ZigZag swing high",
        ],
        "entry": "Price at/ near 61.8% fib retracement AND above 10 EMA",
        "stop_loss": "Below the swing low or below 10 EMA (whichever is lower)",
        "target_1": "Previous swing high",
        "target_2": "1.5x fib range extension",
    },
}


@dataclass
class MindsetState:
    """Current state of the trader's mindset."""
    current_state: str = "DISCIPLINED"
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    daily_trades_taken: int = 0
    daily_losses: int = 0
    last_state_change: str = ""
    fomo_alerts: int = 0  # Count of times FOMO was triggered
    rules_broken: List[str] = field(default_factory=list)
    journal_entries: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "MindsetState":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ProTraderProfile:
    """The complete trader identity — rules, patterns, performance."""
    name: str = "Pro Trader — Govind"
    created_date: str = datetime.date.today().isoformat()
    capital: float = 100_000.0
    version: str = "1.0.0"
    mindset: MindsetState = field(default_factory=MindsetState)
    active_archetypes: List[str] = field(default_factory=lambda: [
        "BREAKOUT_MOMENTUM", "MEAN_REVERSION_SNAPBACK", "GAP_AND_GO",
        "HIGH_DRY_FRY", "BULLISH_TASUKI", "INSIDE_BAR_BREAK",
        "MORNING_STAR", "DOUBLE_BOTTOM", "BABY_CRADLE",
        "DARVAX_JALWA", "LAL_DABANGG", "ZIGZAG_FIB",
    ])
    pattern_history: List[dict] = field(default_factory=list)
    weekly_reviews: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d['mindset'] = self.mindset.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "ProTraderProfile":
        profile = cls()
        profile.name = data.get('name', profile.name)
        profile.created_date = data.get('created_date', profile.created_date)
        profile.capital = data.get('capital', profile.capital)
        profile.version = data.get('version', profile.version)
        profile.active_archetypes = data.get('active_archetypes', profile.active_archetypes)
        profile.pattern_history = data.get('pattern_history', [])
        profile.weekly_reviews = data.get('weekly_reviews', [])
        if 'mindset' in data:
            profile.mindset = MindsetState.from_dict(data['mindset'])
        return profile


# ═══════════════════════════════════════════════════════════════════════
# PILLAR 2: PATTERN RECOGNITION ENGINE
# ═══════════════════════════════════════════════════════════════════════

def clean_yfinance_df(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Clean yfinance MultiIndex columns."""
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df = df.xs(ticker, axis=1, level=1)
    rename = {}
    for c in df.columns:
        cl = str(c).lower()
        if cl in ('open', 'high', 'low', 'close', 'volume'):
            rename[c] = cl
    return df.rename(columns=rename)


def compute_indicators(df: pd.DataFrame) -> dict:
    """Compute all technical indicators needed for pattern recognition."""
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    
    # SMAs
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    
    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # ATR
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()
    
    # Volume
    vol_sma20 = volume.rolling(20).mean()
    vol_ratio = volume / vol_sma20
    
    # Darvas Boxes
    box_high_20 = close.rolling(20).max()
    box_low_20 = close.rolling(20).min()
    box_high_10 = close.rolling(10).max()
    box_low_10 = close.rolling(10).min()
    
    # Returns
    daily_ret = close.pct_change() * 100
    ret_1m = ((close / close.shift(21)) - 1) * 100 if len(close) > 21 else pd.Series(0, index=close.index)
    ret_3m = ((close / close.shift(63)) - 1) * 100 if len(close) > 63 else pd.Series(0, index=close.index)
    
    # Drawdown
    dd = (close / close.cummax() - 1) * 100
    
    return {
        'close': close,
        'high': high,
        'low': low,
        'volume': volume,
        'sma20': sma20,
        'sma50': sma50,
        'rsi': rsi,
        'atr14': atr14,
        'vol_sma20': vol_sma20,
        'vol_ratio': vol_ratio,
        'box_high_20': box_high_20,
        'box_low_20': box_low_20,
        'box_high_10': box_high_10,
        'box_low_10': box_low_10,
        'daily_ret': daily_ret,
        'ret_1m': ret_1m,
        'ret_3m': ret_3m,
        'drawdown': dd,
    }


def detect_darvas_breakouts(df: pd.DataFrame, ind: dict, min_vol_ratio: float = 1.5) -> List[dict]:
    """Detect all Darvas breakout signals in the 6-month window."""
    close = ind['close']
    volume = ind['volume']
    box_high_20 = ind['box_high_20']
    vol_ratio = ind['vol_ratio']
    
    breakouts = []
    for i in range(1, len(close)):
        if (close.iloc[i] > box_high_20.iloc[i-1] and 
            vol_ratio.iloc[i] >= min_vol_ratio):
            breakouts.append({
                'date': str(close.index[i].date()),
                'price': round(float(close.iloc[i]), 2),
                'box_top': round(float(box_high_20.iloc[i-1]), 2),
                'pct_above_box': round(((close.iloc[i] / box_high_20.iloc[i-1]) - 1) * 100, 1),
                'volume_ratio': round(float(vol_ratio.iloc[i]), 1),
            })
    return breakouts


def classify_pattern_archetype(ticker: str, df: pd.DataFrame, ind: dict) -> dict:
    """
    Classify a stock into one of the pattern archetypes.
    Returns match score for each archetype with supporting evidence.
    """
    close = ind['close']
    volume = ind['volume']
    rsi = ind['rsi']
    sma20 = ind['sma20']
    sma50 = ind['sma50']
    box_high_20 = ind['box_high_20']
    box_low_20 = ind['box_low_20']
    vol_ratio = ind['vol_ratio']
    daily_ret = ind['daily_ret']
    ret_1m = ind['ret_1m']
    ret_3m = ind['ret_3m']
    drawdown = ind['drawdown']
    
    current_price = float(close.iloc[-1])
    current_rsi = float(rsi.iloc[-1])
    current_vol_ratio = float(vol_ratio.iloc[-1])
    current_sma20 = float(sma20.iloc[-1])
    current_sma50 = float(sma50.iloc[-1]) if not pd.isna(sma50.iloc[-1]) else 0
    daily_vol = float(daily_ret.std())
    
    # Detect breakouts in last 6 months
    breakouts = detect_darvas_breakouts(df, ind)
    recent_breakout = False
    if breakouts:
        last_breakout = breakouts[-1]
        days_since_breakout = (close.index[-1] - pd.Timestamp(last_breakout['date'])).days
        recent_breakout = days_since_breakout <= 10
    
    # Current breakout status
    is_currently_above_box = float(close.iloc[-1]) > float(box_high_20.iloc[-2]) if len(close) > 1 else False
    
    # RSI momentum
    rsi_trend = "rising" if current_rsi > float(rsi.iloc[-5]) else "falling" if len(rsi) > 5 else "stable"
    
    # Volume spike today
    vol_spike_today = current_vol_ratio >= 2.0
    
    # Check for gaps (price jump > 2% from previous close)
    gap_pct = float(close.iloc[-1] / close.iloc[-2] - 1) * 100 if len(close) > 1 else 0
    
    sma_trend = "BULLISH" if current_sma20 > current_sma50 and current_sma50 > 0 else "BEARISH"
    
    # ─── SCORE EACH ARCHETYPE ───
    
    scores = {}
    
    # BREAKOUT_MOMENTUM Score
    bm_score = 0
    bm_evidence = []
    if 55 <= current_rsi <= 80:
        bm_score += 25
        bm_evidence.append(f"RSI {current_rsi:.0f} in ideal breakout range (55-80)")
    if sma_trend == "BULLISH":
        bm_score += 20
        bm_evidence.append("SMA20 > SMA50 — bullish alignment")
    if is_currently_above_box:
        bm_score += 25
        bm_evidence.append(f"Price above 20d box high — active breakout")
    if daily_vol >= 2.0:
        bm_score += 10
        bm_evidence.append(f"Volatility {daily_vol:.1f}% — enough to run")
    if len(breakouts) >= 2:
        bm_score += 10
        bm_evidence.append(f"{len(breakouts)} historical Darvas breakouts in 6M — pattern reliable")
    if float(vol_ratio.iloc[-1]) >= 1.5:
        bm_score += 10
        bm_evidence.append(f"Volume ratio {float(vol_ratio.iloc[-1]):.1f}x — institutional confirmation")
    scores['BREAKOUT_MOMENTUM'] = {'score': bm_score, 'evidence': bm_evidence}
    
    # MEAN_REVERSION_SNAPBACK Score
    mr_score = 0
    mr_evidence = []
    if current_rsi <= 35:
        mr_score += 30
        mr_evidence.append(f"RSI {current_rsi:.0f} — oversold territory")
    if rsi_trend == "rising" and current_rsi <= 40:
        mr_score += 25
        mr_evidence.append("RSI rising from oversold — momentum shift")
    if float(drawdown.iloc[-1]) <= -20:
        mr_score += 15
        mr_evidence.append(f"Drawdown {float(drawdown.iloc[-1]):.0f}% — deep pullback")
    if daily_vol >= 2.5:
        mr_score += 10
        mr_evidence.append(f"Volatility {daily_vol:.1f}% — snapback potential")
    if current_vol_ratio < 1.5:
        mr_score += 10
        mr_evidence.append("Volume normalizing — selling exhaustion")
    if not is_currently_above_box:
        mr_score += 10
        mr_evidence.append("Inside/near box bottom — potential reversal point")
    scores['MEAN_REVERSION_SNAPBACK'] = {'score': mr_score, 'evidence': mr_evidence}
    
    # GAP_AND_GO Score
    gg_score = 0
    gg_evidence = []
    if gap_pct >= 2.0:
        gg_score += 25
        gg_evidence.append(f"Gap up of {gap_pct:.1f}% today")
    if current_vol_ratio >= 2.0:
        gg_score += 20
        gg_evidence.append(f"Volume spike {current_vol_ratio:.1f}x — institutional")
    if 50 <= current_rsi <= 75:
        gg_score += 15
        gg_evidence.append(f"RSI {current_rsi:.0f} — room to run")
    if recent_breakout and is_currently_above_box:
        gg_score += 20
        gg_evidence.append("Recent breakout holding — continuation pattern")
    if sma_trend == "BULLISH":
        gg_score += 10
        gg_evidence.append("Bullish SMA alignment")
    if float(vol_ratio.iloc[-1]) >= 1.5 and gap_pct >= 1.0:
        gg_score += 10
    scores['GAP_AND_GO'] = {'score': gg_score, 'evidence': gg_evidence}
    
    # DIRECTIONAL_VOLATILITY_BULL Score
    dvb_score = 0
    dvb_evidence = []
    
    # Core: High volatility (σ ≥ 2.5%)
    if daily_vol >= 2.5:
        dvb_score += 25
        dvb_evidence.append(f"Daily σ {daily_vol:.1f}% — top-decile volatility")
    elif daily_vol >= 2.0:
        dvb_score += 10
        dvb_evidence.append(f"Daily σ {daily_vol:.1f}% — above average volatility")
    
    # Trend strength: % days above SMA20 (≥ 60%)
    days_above = sum(1 for i in range(20, len(ind['close'])) if ind['close'].iloc[i] > ind['sma20'].iloc[i])
    total_days = max(len(ind['close']) - 20, 1)
    pct_above_sma20 = days_above / total_days * 100
    if pct_above_sma20 >= 70:
        dvb_score += 25
        dvb_evidence.append(f"{pct_above_sma20:.0f}% days above SMA20 — strong uptrend conviction")
    elif pct_above_sma20 >= 60:
        dvb_score += 15
    
    # Near 52W high
    near_52wh = current_price / (float(close.max()) if float(close.max()) > 0 else current_price) * 100
    if near_52wh >= 90:
        dvb_score += 20
        dvb_evidence.append(f"Near 52W high ({near_52wh:.0f}%) — price discovery mode")
    elif near_52wh >= 75:
        dvb_score += 10
    
    # Volume confirmation
    recent_vol_mean = float(ind['volume'].tail(5).mean())
    mid_vol_mean = float(ind['volume'].tail(20).head(15).mean()) if len(ind['volume']) >= 20 else recent_vol_mean
    vol_trend_ratio = recent_vol_mean / max(mid_vol_mean, 1)
    if vol_trend_ratio > 1.3:
        dvb_score += 15
        dvb_evidence.append(f"Volume accelerating ({vol_trend_ratio:.1f}x) — institutional accumulation")
    elif current_vol_ratio >= 1.2:
        dvb_score += 10
        dvb_evidence.append(f"Volume sustaining above average ({current_vol_ratio:.1f}x)")
    
    # Darvas breakouts count
    if breakouts:
        dvb_score += min(len(breakouts) * 3, 10)
        dvb_evidence.append(f"{len(breakouts)} Darvas breakouts in 6M — pattern reliability")
    
    # RSI check (not overbought)
    if current_rsi < 85:
        dvb_score += 5
    scores['DIRECTIONAL_VOLATILITY_BULL'] = {'score': dvb_score, 'evidence': dvb_evidence}
    
    # DIRECTIONAL_VOLATILITY_BEAR Score
    dvbear_score = 0
    dvbear_evidence = []
    
    # Core: High volatility
    if daily_vol >= 2.5:
        dvbear_score += 20
        dvbear_evidence.append(f"Daily σ {daily_vol:.1f}% — high volatility confirms movement potential")
    
    # Deep drawdown / below SMA20
    if pct_above_sma20 <= 30:
        dvbear_score += 25
        dvbear_evidence.append(f"Only {pct_above_sma20:.0f}% days above SMA20 — deep downtrend")
    elif pct_above_sma20 <= 40:
        dvbear_score += 15
    
    # RSI oversold + rising
    if current_rsi <= 35:
        dvbear_score += 15
        dvbear_evidence.append(f"RSI {current_rsi:.0f} — oversold")
    if rsi_trend == "rising" and current_rsi <= 40:
        dvbear_score += 15
        dvbear_evidence.append("RSI rising from oversold — momentum shift")
    
    # Drawdown depth
    dd_val = float(drawdown.iloc[-1])
    if dd_val <= -25:
        dvbear_score += 15
        dvbear_evidence.append(f"Drawdown {dd_val:.0f}% — deep pullback")
    elif dd_val <= -15:
        dvbear_score += 10
    
    # Volume not spiking (exhaustion)
    if current_vol_ratio < 1.2 and pct_above_sma20 < 40:
        dvbear_score += 10
        dvbear_evidence.append("Volume normalizing after sell-off — exhaustion signal")
    
    # Historical breakouts show stock CAN move
    if breakouts:
        dvbear_score += min(len(breakouts) * 2, 10)
        dvbear_evidence.append(f"{len(breakouts)} historical breakouts — stock has momentum potential")
    scores['DIRECTIONAL_VOLATILITY_BEAR'] = {'score': dvbear_score, 'evidence': dvbear_evidence}
    
    # Determine best match
    best_archetype = max(scores, key=lambda k: scores[k]['score'])
    best_score = scores[best_archetype]['score']
    
    return {
        'ticker': ticker,
        'price': current_price,
        'best_archetype': best_archetype,
        'best_score': best_score,
        'all_scores': scores,
        'breakouts_6m': len(breakouts),
        'recent_breakout': recent_breakout,
        'current_breakout': is_currently_above_box,
        'rsi': round(current_rsi, 1),
        'rsi_trend': rsi_trend,
        'sma_trend': sma_trend,
        'vol_ratio': round(current_vol_ratio, 1),
        'daily_vol': round(daily_vol, 2),
        'ret_1m': round(float(ret_1m.iloc[-1]), 1),
        'ret_3m': round(float(ret_3m.iloc[-1]), 1) if len(ret_3m.dropna()) > 0 else 0,
        'drawdown': round(float(drawdown.iloc[-1]), 1),
        'gap_pct': round(gap_pct, 1),
        'vol_spike_today': vol_spike_today,
        # DV-specific fields
        'pct_above_sma20': round(pct_above_sma20, 1),
        'near_52wh_pct': round(near_52wh, 1),
        'vol_trend_5_20': round(vol_trend_ratio, 2),
        'dv_score': dvb_score,
        'dv_bear_score': dvbear_score,
    }


# ═══════════════════════════════════════════════════════════════════════
# PILLAR 3: EXECUTION GATES & CHECKLISTS
# ═══════════════════════════════════════════════════════════════════════

class ExecutionGate:
    """
    Pre-trade checklist that prevents emotional entries.
    Every trade must pass through ALL gates before execution.
    """

    @staticmethod
    def check_mindset(state: MindsetState) -> Tuple[bool, str]:
        """GATE 1: Am I in the right state to trade?"""
        if state.current_state == "TILTED":
            return False, "🔴 BLOCKED: Trader is tilted. No trading allowed. Go walk."
        if state.current_state == "ANALYTICAL":
            return False, "🔴 BLOCKED: In analysis mode. No new trades."
        if state.current_state == "AGGRESSIVE":
            return False, "🟡 WARNING: Feeling aggressive. Reduce size by 70% and cool off."
        if state.daily_losses >= 3:
            return False, f"🔴 BLOCKED: {state.daily_losses} losses today. Max 3/day. Stop trading."
        return True, "✅ Mindset check: PASSED"

    @staticmethod
    def check_archetype_setup(pattern: dict, archetype: str) -> Tuple[bool, str]:
        """GATE 2: Does this setup meet the archetype requirements?"""
        archetype_config = PATTERN_ARCHETYPES.get(archetype)
        if not archetype_config:
            return False, f"❌ Unknown archetype: {archetype}"
        
        score = pattern['all_scores'].get(archetype, {}).get('score', 0)
        if score < 50:
            return False, f"❌ Pattern score {score}/100 — below 50 threshold. Not a clean setup."
        
        return True, f"✅ Archetype match: {score}/100 — setup confirmed"

    @staticmethod
    def check_market_regime(vix: float, nifty_change: float) -> Tuple[bool, str]:
        """GATE 3: Is the market environment favorable?"""
        warnings = []
        if vix > 25:
            warnings.append(f"VIX {vix:.0f} — high volatility regime")
        if nifty_change < -1.0:
            warnings.append(f"Nifty {nifty_change:+.1f}% — broad market weakness")
        
        if len(warnings) >= 2:
            return False, f"🔴 BLOCKED: Adverse market. {' | '.join(warnings)}"
        elif warnings:
            return True, f"🟡 WARNING: {' | '.join(warnings)}. Reduce size by 50%."
        return True, "✅ Market regime: FAVORABLE"

    @staticmethod
    def check_risk_limits(
        capital: float, position_count: int, 
        proposed_entry: float, atr: float
    ) -> Tuple[bool, str, dict]:
        """GATE 4: Risk management validation."""
        # Max positions
        if position_count >= 5:
            return False, "🔴 BLOCKED: Already at max 5 positions.", {}
        
        # 2% risk rule
        max_risk_amount = capital * 0.02
        stop_distance = max(atr * 1.5, proposed_entry * 0.02)
        max_quantity = int(max_risk_amount / stop_distance)
        position_value = max_quantity * proposed_entry
        max_position_value = capital * 0.25
        
        if position_value > max_position_value:
            max_quantity = int(max_position_value / proposed_entry)
            position_value = max_quantity * proposed_entry
        
        if max_quantity < 1:
            return False, "🔴 BLOCKED: ATR-based position sizing yields < 1 share.", {}
        
        sizing = {
            'max_quantity': max_quantity,
            'stop_distance': round(stop_distance, 2),
            'risk_amount': round(max_risk_amount, 0),
            'position_value': round(position_value, 0),
            'risk_pct': round((stop_distance / proposed_entry) * 100, 1),
        }
        
        return True, f"✅ Risk check: POSITION SIZE {max_quantity} shares (risk {sizing['risk_pct']}% per share)", sizing


def run_execution_gates(
    pattern: dict,
    archetype: str,
    state: MindsetState,
    capital: float,
    position_count: int,
    vix: float = 15,
    nifty_change: float = 0,
) -> dict:
    """Run all 4 gates. Returns PASS/FAIL with detailed breakdown."""
    result = {
        'passed': True,
        'gates': {},
        'blocked_by': [],
        'sizing': {},
    }
    
    # Gate 1: Mindset
    passed, msg = ExecutionGate.check_mindset(state)
    result['gates']['mindset'] = {'passed': passed, 'message': msg}
    if not passed:
        result['passed'] = False
        result['blocked_by'].append('mindset')
    
    # Gate 2: Setup
    passed, msg = ExecutionGate.check_archetype_setup(pattern, archetype)
    result['gates']['setup'] = {'passed': passed, 'message': msg}
    if not passed:
        result['passed'] = False
        result['blocked_by'].append('setup')
    
    # Gate 3: Market
    passed, msg = ExecutionGate.check_market_regime(vix, nifty_change)
    result['gates']['market'] = {'passed': passed, 'message': msg}
    if not passed:
        result['passed'] = False
        result['blocked_by'].append('market')
    
    # Gate 4: Risk
    atr_value = 0.02 * pattern.get('price', 100)  # Estimate if no ATR available
    passed, msg, sizing = ExecutionGate.check_risk_limits(
        capital, position_count, pattern.get('price', 100), atr_value
    )
    result['gates']['risk'] = {'passed': passed, 'message': msg}
    result['sizing'] = sizing
    if not passed:
        result['passed'] = False
        result['blocked_by'].append('risk')
    
    return result


# ═══════════════════════════════════════════════════════════════════════
# SCANNER — Find stocks matching the "Triad" patterns
# ═══════════════════════════════════════════════════════════════════════

PRO_SCAN_UNIVERSE = [
    # MEMO: The user's confirmed DV patterns
    "ATHERENERG.NS", "NEPHROPLUS.NS", "CENTUM.NS",
    # Top matches from DV scan
    "ADANIGREEN.NS", "APOLLOHOSP.NS", "MOTILALOFS.NS",
    "SONACOMS.NS", "RBLBANK.NS", "ADANIPORTS.NS",
    "GLAND.NS", "TRENT.NS", "POLYCAB.NS",
    "PIDILITIND.NS", "MANAPPURAM.NS", "COFORGE.NS",
    "ELECTCAST.NS", "EDELWEISS.NS", "FEDERALBNK.NS",
    "IIFL.NS", "FORTIS.NS", "BIOCON.NS",
    "DIXON.NS", "BAJAJ-AUTO.NS", "M&M.NS",
    # Classic NSE high-volume stocks
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "INFY.NS", "BHARTIARTL.NS",
    "TMPV.NS", "TMCV.NS", "LT.NS", "TITAN.NS",
    "BAJFINANCE.NS", "MARUTI.NS", "HAL.NS",
    "BEL.NS", "PERSISTENT.NS", "ETERNAL.NS",
    # DV candidates — high vol + trending
    "IDEA.NS", "IRFC.NS", "IREDA.NS", "YESBANK.NS",
    "NHPC.NS", "NBCC.NS", "RVNL.NS", "POWERGRID.NS",
    "COALINDIA.NS", "NTPC.NS", "IEX.NS", "ANGELONE.NS",
    "ZENSARTECH.NS", "LTTS.NS", "HCLTECH.NS",
    "WIPRO.NS", "TECHM.NS", "BANKBARODA.NS",
    "PNB.NS", "CANBK.NS", "UNIONBANK.NS",
    "INDUSINDBK.NS", "AUBANK.NS", "BANDHANBNK.NS",
    # Small/mid cap high volatility candidates
    "JPASSOCIAT.NS", "SUZLON.NS",
    "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS",
    "BRITANNIA.NS", "DABUR.NS", "HAVELLS.NS",
    "VOLTAS.NS", "SIEMENS.NS", "ABB.NS",
    "BHEL.NS", "L&T.NS", "KOTAKBANK.NS",
    "AXISBANK.NS", "MARICO.NS", "DIVISLAB.NS",
    "CIPLA.NS", "DRREDDY.NS", "SUNPHARMA.NS",
    "LUPIN.NS", "TORNTPHARM.NS", "ALKEM.NS",
    # User tracked stocks
    "BELRISE.NS", "LALPATHLAB.NS",
    # Emerging DV patterns (new finds)
    "EICHERMOT.NS", "HEROMOTOCO.NS", "TATACONSUM.NS",
    "DALBHARAT.NS", "ULTRACEMCO.NS", "GRASIM.NS",
    "HINDALCO.NS", "JSWSTEEL.NS", "TATASTEEL.NS",
    "VEDL.NS", "HINDZINC.NS", "NATIONALUM.NS",
    "PAGEIND.NS", "JUBLFOOD.NS",
    "SHRIRAMFIN.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS",
    "PVRINOX.NS", "DELTACORP.NS", "INDUSTOWER.NS",
]


def run_triad_scanner(
    universe: List[str] = None,
    min_score: int = 50,
    progress: bool = True,
) -> List[dict]:
    """
    Full pattern scan — find stocks matching the Triad archetypes.
    Returns classified patterns sorted by best match score.
    """
    if universe is None:
        universe = PRO_SCAN_UNIVERSE
    
    results = []
    total = len(universe)
    
    for idx, ticker in enumerate(universe):
        if progress:
            print(f"  [{idx+1}/{total}] Scanning {ticker}...", end="\r")
        
        try:
            df = yf.download(ticker, period="6mo", progress=False)
            if df.empty or len(df) < 20:
                continue
            df = clean_yfinance_df(df, ticker)
            ind = compute_indicators(df)
            pattern = classify_pattern_archetype(ticker, df, ind)
            results.append(pattern)
        except Exception:
            continue
    
    if progress:
        print()
    
    # Sort by best score descending
    results.sort(key=lambda r: r['best_score'], reverse=True)
    return results


def print_triad_report(results: List[dict], top_n: int = 20):
    """Print formatted Triad scan report."""
    print("\n" + "="*120)
    print("🎯 PRO TRADER — TRIAD PATTERN SCAN REPORT")
    print("="*120)
    print(f"Date: {datetime.date.today().isoformat()}")
    print(f"Stocks scanned: {len(results)}")
    print(f"Match threshold: Score >= 50\n")
    
    # Group by archetype
    archetype_groups = {}
    for r in results:
        arch = r['best_archetype']
        if arch not in archetype_groups:
            archetype_groups[arch] = []
        if r['best_score'] >= 50:
            archetype_groups[arch].append(r)
    
    for arch, stocks in sorted(archetype_groups.items()):
        config = PATTERN_ARCHETYPES.get(arch, {})
        print(f"\n{'─'*60}")
        print(f"  {config.get('emoji', '📊')} {config.get('name', arch)} ({len(stocks)} matches)")
        print(f"  {config.get('description', '')}")
        print(f"{'─'*60}")
        print(f"  {'Ticker':<20} {'Score':<8} {'Price':<10} {'RSI':<6} {'Vol%':<6} {'Breakouts':<10} {'Status':<15}")
        print(f"  {'─'*70}")
        for s in sorted(stocks, key=lambda x: x['best_score'], reverse=True)[:10]:
            status = "🟢BREAKOUT" if s.get('current_breakout') else ("🔄REVERSAL" if s.get('rsi_trend') == 'rising' and s.get('rsi') < 40 else "📦CONSOLIDATING")
            print(f"  {s['ticker']:<20} {s['best_score']:<8} ₹{s['price']:<8.1f} {s['rsi']:<6.1f} {s['daily_vol']:<6.2f} {s['breakouts_6m']:<10} {status:<15}")
    
    # Best picks summary
    print(f"\n{'='*120}")
    print("🏆 TOP 10 TRIAD PICKS")
    print(f"{'='*120}")
    print(f"  {'Rank':<5} {'Ticker':<20} {'Archetype':<25} {'Score':<8} {'Price':<10} {'RSI':<7} {'Setup':<25}")
    print(f"  {'─'*90}")
    top_picks = [r for r in results if r['best_score'] >= 50][:10]
    for i, r in enumerate(top_picks, 1):
        arch_name = PATTERN_ARCHETYPES.get(r['best_archetype'], {}).get('emoji', '📊')
        setup = f"Breakout={r.get('current_breakout', False)} | Vol={r['vol_ratio']:.1f}x | Drawdown={r.get('drawdown', 0):.0f}%"
        print(f"  {i:<5} {r['ticker']:<20} {arch_name} {r['best_archetype']:<20} {r['best_score']:<8} ₹{r['price']:<8.1f} {r['rsi']:<7.1f} {setup:<25}")


# ═══════════════════════════════════════════════════════════════════════
# DV SCANNER — Directional Volatility Pattern Finder
# ═══════════════════════════════════════════════════════════════════════

DV_SCAN_LOG = "dv_scan_results.json"

def run_dv_scanner(
    universe: List[str] = None,
    min_dv_score: int = 40,
    progress: bool = True,
) -> dict:
    """
    Dedicated Directional Volatility scanner.
    Finds stocks matching the AtherEnergy/Centrum/Nephroplus pattern.
    
    Returns categorized results:
      - dv_bull: Stocks with high σ + strong uptrend (like Ather, Nephro)
      - dv_bear: Stocks with high σ + deep drawdown (like Centrum)
      - dv_accel: Stocks with accelerating volume + expanding volatility
    """
    if universe is None:
        universe = PRO_SCAN_UNIVERSE
    
    results = run_triad_scanner(universe=universe, min_score=min_dv_score, progress=progress)
    
    dv_bull = []
    dv_bear = []
    dv_accel = []
    
    for r in results:
        pattern = r.get('pattern_data', {})
        # DV-Bull: high σ + strong uptrend + near 52WH
        dv_score = r.get('dv_score', 0)
        near_52wh = r.get('near_52wh_pct', 0)
        pct_above = r.get('pct_above_sma20', 0)
        
        if dv_score >= min_dv_score and near_52wh >= 75 and pct_above >= 55:
            dv_bull.append(r)
        
        # DV-Bear: high σ + oversold + rising RSI
        dv_bear_score = r.get('dv_bear_score', 0)
        if dv_bear_score >= min_dv_score:
            dv_bear.append(r)
        
        # DV-Accel: volume accelerating + volatility expanding
        vol_trend = r.get('vol_trend_5_20', 0)
        daily_vol = r.get('daily_vol', 0)
        if dv_score >= 30 and vol_trend >= 1.2 and daily_vol >= 2.0 and near_52wh >= 70:
            dv_accel.append(r)
    
    # Sort each category by score descending
    dv_bull.sort(key=lambda x: x.get('dv_score', 0), reverse=True)
    dv_bear.sort(key=lambda x: x.get('dv_bear_score', 0), reverse=True)
    dv_accel.sort(key=lambda x: x.get('dv_score', 0), reverse=True)
    
    result = {
        'timestamp': datetime.datetime.now().isoformat(),
        'dv_bull': dv_bull[:10],
        'dv_bear': dv_bear[:10],
        'dv_accel': dv_accel[:10],
        'total_scanned': len(results),
        'dv_bull_count': len(dv_bull),
        'dv_bear_count': len(dv_bear),
        'dv_accel_count': len(dv_accel),
    }
    
    # Save to log
    try:
        with open(DV_SCAN_LOG, 'w') as f:
            json.dump(result, f, indent=2, default=str)
    except Exception:
        pass
    
    return result


def print_dv_report(dv_result: dict):
    """Print the Directional Volatility scan report."""
    print("\n" + "=" * 120)
    print("🏃‍♂️ DIRECTIONAL VOLATILITY (DV) PATTERN SCAN")
    print("   The AtherEnergy • Centrum • Nephroplus Signature")
    print("=" * 120)
    print(f"Scanned: {dv_result['total_scanned']} stocks | "
          f"🏃‍♂️ DV-Bull: {dv_result['dv_bull_count']} | "
          f"🔄 DV-Bear: {dv_result['dv_bear_count']} | "
          f"⚡ DV-Accel: {dv_result['dv_accel_count']}")
    
    # DV BULL section
    print("\n" + "─" * 120)
    print("🏃‍♂️  DV-BULL: High volatility + Strong uptrend (Ather/Nephro pattern)")
    print("─" * 120)
    if dv_result['dv_bull']:
        print(f"{'#':<4} {'Ticker':<20} {'Price':<10} {'DV Score':<10} {'σ%':<8} {'%>SMA20':<10} {'%52WH':<8} {'VolTrend':<10} {'RSI':<8}")
        print("─" * 90)
        for i, r in enumerate(dv_result['dv_bull'][:8], 1):
            print(f"{i:<4} {r['ticker']:<20} ₹{r['price']:<8.1f} {r['dv_score']:<10} "
                  f"{r['daily_vol']:<8.1f} {r['pct_above_sma20']:<10.0f} {r['near_52wh_pct']:<8.0f} "
                  f"{r['vol_trend_5_20']:<10.1f} {r['rsi']:<8.1f}")
    else:
        print("  No DV-Bull stocks found above threshold.")
    
    # DV BEAR section
    print("\n" + "─" * 120)
    print("🔄  DV-BEAR: High volatility + Deep drawdown (Centrum pattern)")
    print("─" * 120)
    if dv_result['dv_bear']:
        print(f"{'#':<4} {'Ticker':<20} {'Price':<10} {'DV Bear':<10} {'σ%':<8} {'%>SMA20':<10} {'Draw%':<10} {'RSI':<8} {'RSI Trend':<12}")
        print("─" * 90)
        for i, r in enumerate(dv_result['dv_bear'][:8], 1):
            rsi_trend = r.get('rsi_trend', '?')
            print(f"{i:<4} {r['ticker']:<20} ₹{r['price']:<8.1f} {r['dv_bear_score']:<10} "
                  f"{r['daily_vol']:<8.1f} {r['pct_above_sma20']:<10.0f} {r['drawdown']:<10.1f} "
                  f"{r['rsi']:<8.1f} {rsi_trend:<12}")
    else:
        print("  No DV-Bear stocks found above threshold.")
    
    # DV ACCEL section
    print("\n" + "─" * 120)
    print("⚡  DV-ACCEL: Accelerating volume + Expanding volatility (Emerging pattern)")
    print("─" * 120)
    if dv_result['dv_accel']:
        print(f"{'#':<4} {'Ticker':<20} {'Price':<10} {'DV Score':<10} {'σ%':<8} {'VolTrend':<10} {'%52WH':<8}")
        print("─" * 70)
        for i, r in enumerate(dv_result['dv_accel'][:8], 1):
            print(f"{i:<4} {r['ticker']:<20} ₹{r['price']:<8.1f} {r['dv_score']:<10} "
                  f"{r['daily_vol']:<8.1f} {r['vol_trend_5_20']:<10.1f} {r['near_52wh_pct']:<8.0f}")
    else:
        print("  No DV-Accel stocks found above threshold.")
    
    print("\n" + "=" * 120)


# ═══════════════════════════════════════════════════════════════════════
# REAL-TIME MONITOR — Entry/Exit Alerts
# ═══════════════════════════════════════════════════════════════════════

DV_MONITOR_LOG = "dv_monitor_state.json"

# Entry/exit rules for DV patterns
DV_ENTRY_RULES = {
    "DIRECTIONAL_VOLATILITY_BULL": {
        "entry_signals": [
            ("Pullback to 20d SMA", lambda r: r.get('pct_above_sma20', 0) > 50 and r.get('near_52wh_pct', 0) > 75),
            ("Volume spike + near 52WH", lambda r: r.get('vol_spike_today', False) and r.get('near_52wh_pct', 0) > 85),
            ("RSI reset < 65 (not overbought)", lambda r: 45 < r.get('rsi', 50) < 65 and r.get('daily_vol', 0) > 2.5),
        ],
        "exit_signals": [
            ("RSI > 80 (exhausted)", lambda r: r.get('rsi', 50) > 80),
            ("Volume drying up", lambda r: r.get('vol_trend_5_20', 1) < 0.7),
            ("Break below 20d SMA", lambda r: r.get('pct_above_sma20', 0) < 50),
            ("50%+ gain in 30 days (profit book)", lambda r: abs(r.get('daily_vol', 0)) > 2.5 and r.get('vol_trend_5_20', 1) > 1.5 and r.get('near_52wh_pct', 0) > 90),
        ],
    },
    "DIRECTIONAL_VOLATILITY_BEAR": {
        "entry_signals": [
            ("RSI rising from < 35", lambda r: r.get('rsi', 50) < 40 and r.get('drawdown', 0) < -20),
            ("First green candle + vol", lambda r: r.get('vol_spike_today', False) and r.get('drawdown', 0) < -20),
            ("Volume exhaustion (no more selling)", lambda r: 25 < r.get('rsi', 50) < 40 and r.get('vol_spike_today', False)),
        ],
        "exit_signals": [
            ("RSI > 55 (mean reversion complete)", lambda r: r.get('rsi', 50) > 55),
            ("Volume spike on up day (profit book)", lambda r: r.get('vol_spike_today', False) and r.get('rsi', 50) > 50),
            ("Failed to hold gain for 3 days", lambda r: False),  # placeholder - needs multi-day tracking
        ],
    },
}


def init_monitor_state():
    """Initialize or load persistent monitor state."""
    try:
        with open(DV_MONITOR_LOG) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            'entries': {},
            'positions': {},
            'alert_history': [],
        }


def save_monitor_state(state: dict):
    """Persist monitor state."""
    with open(DV_MONITOR_LOG, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def check_dv_entry_exit_conditions(
    pattern: dict,
    archetype: str,
) -> dict:
    """
    Check entry/exit conditions for a DV pattern stock.
    Returns dict with entry/exit/already_entered signals.
    """
    rules = DV_ENTRY_RULES.get(archetype, {})
    entry_hits = []
    exit_hits = []
    
    for name, check_fn in rules.get("entry_signals", []):
        try:
            if check_fn(pattern):
                entry_hits.append(name)
        except Exception:
            pass
    
    for name, check_fn in rules.get("exit_signals", []):
        try:
            if check_fn(pattern):
                exit_hits.append(name)
        except Exception:
            pass
    
    return {
        'entry_signals_hit': entry_hits,
        'exit_signals_hit': exit_hits,
        'entry_count': len(entry_hits),
        'exit_count': len(exit_hits),
        'recommendation': (
            "ENTRY" if len(entry_hits) >= 2 else
            "EXIT" if len(exit_hits) >= 2 else
            "HOLD" if len(entry_hits) >= 1 else
            "WAIT"
        ),
    }


def run_dv_monitor(
    universe: List[str] = None,
    send_alerts: bool = False,
) -> dict:
    """
    Run the real-time DV pattern monitor.
    Scans universe for DV pattern stocks and checks entry/exit conditions.
    Returns alert-ready results.
    """
    print("\n" + "█" * 60)
    print("  📡 DV REAL-TIME MONITOR")
    print("  " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"))
    print("█" * 60)
    
    results = run_dv_scanner(universe=universe, min_dv_score=30, progress=True)
    state = init_monitor_state()
    
    alerts = []
    
    # Check DV-Bull for entry/exit
    for r in results.get('dv_bull', []):
        cond = check_dv_entry_exit_conditions(r, "DIRECTIONAL_VOLATILITY_BULL")
        ticker = r['ticker']
        
        if cond['recommendation'] in ('ENTRY', 'EXIT'):
            alerts.append({
                'ticker': ticker,
                'archetype': 'DV-BULL',
                'price': r['price'],
                'dv_score': r.get('dv_score', 0),
                'recommendation': cond['recommendation'],
                'entry_signals': cond['entry_signals_hit'],
                'exit_signals': cond['exit_signals_hit'],
                'daily_vol': r.get('daily_vol', 0),
                'rsi': r.get('rsi', 50),
                'near_52wh': r.get('near_52wh_pct', 0),
                'pct_above_sma20': r.get('pct_above_sma20', 0),
                'timestamp': datetime.datetime.now().isoformat(),
            })
        
        # Track state
        state['entries'][ticker] = {
            'last_price': r['price'],
            'last_dv_score': r.get('dv_score', 0),
            'last_seen': datetime.datetime.now().isoformat(),
            'last_recommendation': cond['recommendation'],
        }
    
    # Check DV-Bear for entry/exit
    for r in results.get('dv_bear', []):
        cond = check_dv_entry_exit_conditions(r, "DIRECTIONAL_VOLATILITY_BEAR")
        ticker = r['ticker']
        
        if cond['recommendation'] in ('ENTRY', 'EXIT'):
            alerts.append({
                'ticker': ticker,
                'archetype': 'DV-BEAR',
                'price': r['price'],
                'dv_bear_score': r.get('dv_bear_score', 0),
                'recommendation': cond['recommendation'],
                'entry_signals': cond['entry_signals_hit'],
                'exit_signals': cond['exit_signals_hit'],
                'daily_vol': r.get('daily_vol', 0),
                'rsi': r.get('rsi', 50),
                'drawdown': r.get('drawdown', 0),
                'timestamp': datetime.datetime.now().isoformat(),
            })
        
        state['entries'][ticker] = {
            'last_price': r['price'],
            'last_dv_bear_score': r.get('dv_bear_score', 0),
            'last_seen': datetime.datetime.now().isoformat(),
            'last_recommendation': cond['recommendation'],
        }
    
    # Save state
    if alerts:
        # Prevent duplicate alerts (same ticker + same recommendation)
        seen = set()
        unique_alerts = []
        for a in alerts:
            key = (a['ticker'], a['recommendation'])
            if key not in seen:
                seen.add(key)
                unique_alerts.append(a)
        alerts = unique_alerts
        
        state['alert_history'].extend(alerts)
        # Keep last 100 alerts
        state['alert_history'] = state['alert_history'][-100:]
    
    save_monitor_state(state)
    
    # Print results
    print(f"\n📊 Alerts generated: {len(alerts)}")
    if alerts:
        for a in alerts:
            rec_icon = "🟢 ENTRY" if a['recommendation'] == 'ENTRY' else "🔴 EXIT"
            print(f"\n  {rec_icon} | {a['ticker']} ({a['archetype']}) @ ₹{a['price']:.1f}")
            print(f"       Signals: {', '.join(a['entry_signals'] + a['exit_signals'])}")
    
    return {
        'alerts': alerts,
        'alert_count': len(alerts),
        'dv_results': results,
    }


# ═══════════════════════════════════════════════════════════════════════
# TELEGRAM ALERT — Send entry/exit signals
# ═══════════════════════════════════════════════════════════════════════

def format_dv_alert_message(alert: dict) -> str:
    """Format a DV alert into a Telegram-friendly message."""
    rec_icon = "🟢" if alert['recommendation'] == 'ENTRY' else "🔴"
    rec_word = alert['recommendation']
    
    msg = (
        f"{rec_icon} *DV-{alert['archetype']} | {alert['ticker']}*\n"
        f"Price: ₹{alert['price']:.2f}\n"
        f"Action: *{rec_word}*\n"
        f"Score: {alert.get('dv_score', alert.get('dv_bear_score', '?'))}/100\n"
    )
    
    if alert.get('entry_signals'):
        msg += f"Signals: ✅ {', '.join(alert['entry_signals'])}\n"
    if alert.get('exit_signals'):
        msg += f"Warning: ⚠️ {', '.join(alert['exit_signals'])}\n"
    
    if alert.get('daily_vol'):
        msg += f"Volatility: {alert['daily_vol']:.1f}% | RSI: {alert['rsi']:.0f}\n"
    
    if alert.get('near_52wh'):
        msg += f"52WH Proximity: {alert['near_52wh']:.0f}%\n"
    
    if alert.get('drawdown'):
        msg += f"Drawdown: {alert['drawdown']:.0f}%\n"
    
    msg += f"⏱ {alert['timestamp'][:19]}"
    return msg


def send_dv_alerts_telegram(monitor_result: dict, target: str = "origin"):
    """Send DV alerts via Telegram."""
    alerts = monitor_result.get('alerts', [])
    if not alerts:
        return {"sent": 0, "message": "No alerts to send"}
    
    sent = 0
    for alert in alerts[:5]:  # Max 5 alerts per run
        try:
            message = format_dv_alert_message(alert)
            # Use the configured delivery mechanism
            # In cron mode, this sends via the cron delivery target
            print(f"\n📨 ALERT: {alert['ticker']} — {alert['recommendation']}")
            print(message)
            sent += 1
        except Exception as e:
            print(f"  ⚠️ Failed sending alert for {alert['ticker']}: {e}")
    
    return {"sent": sent, "message": f"Sent {sent}/{len(alerts)} alerts"}


# ═══════════════════════════════════════════════════════════════════════
# REGULARLY SCHEDULED DV SCAN (for cron jobs)
# ═══════════════════════════════════════════════════════════════════════

def run_dv_cron_scan(universe: List[str] = None, send_alerts: bool = True) -> dict:
    """
    Complete DV scan for cron job execution.
    Scans → monitors → alerts → prints report.
    """
    print("\n" + "█" * 60)
    print("  🤖 DV PATTERN CRON SCAN")
    print("  " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"))
    print("█" * 60)
    
    monitor_result = run_dv_monitor(universe=universe, send_alerts=send_alerts)
    
    if send_alerts and monitor_result.get('alerts'):
        sent = send_dv_alerts_telegram(monitor_result)
        print(f"\n  📬 Telegram alerts dispatched: {sent['sent']}")
    
    print("\n" + "█" * 60)
    print("  ✅ DV Cron Scan Complete")
    print("█" * 60)
    
    return monitor_result


# ═══════════════════════════════════════════════════════════════════════
# MINDSET JOURNAL & DISCIPLINE LOG
# ═══════════════════════════════════════════════════════════════════════

class MindsetJournal:
    """Daily journal for tracking mental state, discipline, and lessons."""

    @staticmethod
    def load_profile() -> ProTraderProfile:
        if PROFILE_FILE.exists():
            with open(PROFILE_FILE) as f:
                return ProTraderProfile.from_dict(json.load(f))
        return ProTraderProfile()

    @staticmethod
    def save_profile(profile: ProTraderProfile):
        with open(PROFILE_FILE, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)

    @staticmethod
    def log_entry(profile: ProTraderProfile, entry: str):
        timestamp = datetime.datetime.now().isoformat()
        profile.mindset.journal_entries.append(f"[{timestamp}] {entry}")
        MindsetJournal.save_profile(profile)

    @staticmethod
    def update_state(profile: ProTraderProfile, new_state: str):
        if new_state in MINDSET_STATES:
            profile.mindset.current_state = new_state
            profile.mindset.last_state_change = datetime.datetime.now().isoformat()
            state_info = MINDSET_STATES[new_state]
            entry = f"State changed to {new_state}: {state_info['description']}"
            profile.mindset.journal_entries.append(f"[{profile.mindset.last_state_change}] {entry}")
            MindsetJournal.save_profile(profile)
            return True, f"State updated: {state_info['emoji']} {new_state}"
        return False, f"Unknown state: {new_state}"

    @staticmethod
    def log_trade_result(profile: ProTraderProfile, won: bool):
        if won:
            profile.mindset.consecutive_wins += 1
            profile.mindset.consecutive_losses = 0
        else:
            profile.mindset.consecutive_losses += 1
            profile.mindset.consecutive_wins = 0
            profile.mindset.daily_losses += 1
        profile.mindset.daily_trades_taken += 1
        
        # Auto-adjust state based on results
        if profile.mindset.consecutive_losses >= 3:
            profile.mindset.current_state = "TILTED"
            profile.mindset.last_state_change = datetime.datetime.now().isoformat()
        elif profile.mindset.consecutive_wins >= 5:
            profile.mindset.current_state = "CAUTIOUS"  # After hot streak, be cautious
            profile.mindset.last_state_change = datetime.datetime.now().isoformat()
        
        MindsetJournal.save_profile(profile)

    @staticmethod
    def reset_daily_counters(profile: ProTraderProfile):
        """Reset daily counters. Call at start of each trading day."""
        profile.mindset.daily_trades_taken = 0
        profile.mindset.daily_losses = 0
        profile.mindset.fomo_alerts = 0
        profile.mindset.rules_broken = []
        if profile.mindset.current_state in ("TILTED", "AGGRESSIVE"):
            profile.mindset.current_state = "DISCIPLINED"
            profile.mindset.last_state_change = datetime.datetime.now().isoformat()
        MindsetJournal.save_profile(profile)

    @staticmethod
    def print_daily_briefing(profile: ProTraderProfile):
        """Print the morning ritual — rules review + state check."""
        state_info = MINDSET_STATES.get(profile.mindset.current_state, {})
        
        print("\n" + "=" * 60)
        print(f"  🧘 PRO TRADER — DAILY MINDSET BRIEFING")
        print(f"  {profile.name} | {datetime.date.today().isoformat()}")
        print("=" * 60)
        print(f"\n  Current State: {state_info.get('emoji', '🧘')} {profile.mindset.current_state}")
        print(f"  Risk Multiplier: {state_info.get('risk_multiplier', 1.0)*100:.0f}%")
        print(f"\n  📋 GOLDEN RULES FOR TODAY:")
        for rule in GOLDEN_RULES:
            print(f"    {rule}")
        print(f"\n  📊 STATS: Capital ₹{profile.capital:,.0f} | "
              f"Consecutive Wins: {profile.mindset.consecutive_wins} | "
              f"Consecutive Losses: {profile.mindset.consecutive_losses}")
        print("=" * 60)


# ═══════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════

def run_daily_routine(universe: List[str] = None):
    """
    Full daily routine:
    1. Morning mindset briefing
    2. Triad pattern scan (legacy)
    3. DV pattern scan (new — finds AtherEnergy/Nephroplus/Centrum signatures)
    4. Execution gate check for top picks
    5. Save everything to profile
    """
    print("\n" + "█" * 60)
    print("  PRO TRADER PROFILE — DAILY ROUTINE")
    print("  " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"))
    print("█" * 60)
    
    # Phase 1: Mindset
    profile = MindsetJournal.load_profile()
    MindsetJournal.reset_daily_counters(profile)
    MindsetJournal.print_daily_briefing(profile)
    
    # Phase 2: Triad Scan (legacy)
    print("\n\n📡 SCANNING TRIAD PATTERNS (Legacy)...")
    results = run_triad_scanner(universe)
    print_triad_report(results)
    
    # Phase 3: DV Scan (New — The real AtherEnergy/Centrum/Nephroplus pattern)
    print("\n\n🏃‍♂️ SCANNING DIRECTIONAL VOLATILITY PATTERNS...")
    dv_results = run_dv_scanner(universe)
    print_dv_report(dv_results)
    
    # Phase 4: Real-time monitor for entry/exit
    print("\n\n📡 DV REAL-TIME MONITOR...")
    monitor_result = run_dv_monitor(universe, send_alerts=False)
    
    # Phase 5: Gate checks for top picks
    print("\n\n🚦 EXECUTION GATE ANALYSIS (Top 5)")
    top_picks = [r for r in results if r['best_score'] >= 50][:5]
    for i, pick in enumerate(top_picks, 1):
        print(f"\n  {'─'*50}")
        print(f"  [{i}] {pick['ticker']} — {PATTERN_ARCHETYPES.get(pick['best_archetype'], {}).get('emoji','')} {pick['best_archetype']}")
        gates = run_execution_gates(
            pick, pick['best_archetype'],
            profile.mindset, profile.capital,
            0  # position_count — would need to check actual portfolio
        )
        for gate_name, gate_result in gates['gates'].items():
            icon = "✅" if gate_result['passed'] else "❌"
            print(f"     {icon} {gate_name.upper()}: {gate_result['message']}")
        if gates['sizing']:
            s = gates['sizing']
            print(f"     📐 Suggested Size: {s.get('max_quantity', 'N/A')} shares | "
                  f"Risk ₹{s.get('risk_amount', 0):,.0f} | "
                  f"Stop {s.get('stop_distance', 'N/A')}")
    
    # Save patterns to log
    pattern_log = [r for r in results if r['best_score'] >= 50]
    with open(PATTERN_LOG, 'w') as f:
        json.dump({
            'date': datetime.date.today().isoformat(),
            'results': [{
                'ticker': r['ticker'],
                'archetype': r['best_archetype'],
                'score': r['best_score'],
                'price': r['price'],
                'rsi': r['rsi'],
            } for r in pattern_log[:20]]
        }, f, indent=2)
    
    print(f"\n\n📁 Profile saved: {PROFILE_FILE}")
    print(f"📁 Pattern log saved: {PATTERN_LOG}")
    print(f"📁 DV scan saved: {DV_SCAN_LOG}")
    
    return profile, results, dv_results


# ═══════════════════════════════════════════════════════════════════════
# CLI ENTRY
# ═══════════════════════════════════════════════════════════════════════

def print_full_analysis():
    """Print the comprehensive analysis of the user's 4 stocks."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║         PATTERN ANALYSIS REPORT: THE TRIAD STRATEGY                ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  STOCKS ANALYZED: AtherEnergy, Emvee*, Centrum, Nephroplus         ║
║  * Emvee could not be found on NSE/BSE/yfinance. May be unlisted   ║
║    or trading under a different name/entity.                       ║
║                                                                    ║
╚══════════════════════════════════════════════════════════════════════╝""")

    # Print the comparison
    print("""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                STOCK PATTERN COMPARISON MATRIX                                          ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  METRIC              │  ATHER ENERGY 🏍️     │  CENTUM CAPITAL 🏦   │  NEPHROCARE 🏥                      ║
║──────────────────────┼──────────────────────┼──────────────────────┼─────────────────────────────────────║
║  Price               │  ₹1,033              │  ₹21.80              │  ₹723                               ║
║  6M Return           │  +59.3% 🟢            │  -26.1% 🔴           │  +53.4% 🟢                          ║
║  1M Return           │  +10.1% 🟢            │  -12.3% 🔴           │  +34.0% 🟢                          ║
║  Max Drawdown 6M     │  -20.3%               │  -31.5%              │  -17.4%                             ║
║  RSI(14)             │  67.3 (NEUTRAL ↗️)     │  19.5 (OVERSOLD ↗️)  │  73.6 (OVERBOUGHT ↗️)                ║
║  Daily Volatility    │  2.9%                 │  4.0%                │  2.9%                               ║
║  Darvas Box Top 20d  │  ₹1,034               │  ₹23.83              │  ₹723                               ║
║  Darvas Box Bottom   │  ₹884                 │  ₹21.44              │  ₹581                               ║
║  % from Box Bottom   │  +16.9%               │  +1.6%               │  +24.5%                             ║
║  Breakout Signals 6M │  6 🟢                  │  5 🔄                │  3 🟢                               ║
║  Volume Spike Count  │  12                   │  11                  │  9                                 ║
║  Volume Ratio Today  │  0.8x (below avg)     │  1.0x (avg)          │  1.2x (above avg)                   ║
║  Current Darvas      │  INSIDE BOX (near top)│  INSIDE BOX (bottom) │  BREAKOUT 🟢                       ║
║  SMA20 vs SMA50      │  BULLISH 📈            │  BEARISH 📉          │  BULLISH 📈                         ║
║  RSI Momentum        │  RISING ↗️             │  RISING ↗️           │  RISING ↗️                          ║
╠══════════════════════╧══════════════════════╧══════════════════════╧══════════════════════════════════════╣
║                                                                                                          ║
║  🔑 KEY INSIGHT — All 3 have RISING RSI momentum despite being at                                     ║
║     completely different market junctures. This is the UNIFYING SIGNAL.                                 ║
║                                                                                                          ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════╝""")


def print_pattern_correlation():
    print("""
╔════════════════════════════════════════════════════════════════════════════════════╗
║             DARVAS ALGO CORRELATION — THE COMMON PATTERN                         ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                    ║
║  1. MULTI-BOX DYNAMIC:                                                             ║
║     All 3 stocks build and break MULTIPLE Darvas boxes (not just one).             ║
║     Ather broke 6 boxes in 6M — each higher than the last.                         ║
║     Nephro broke 3 boxes — each with volume confirmation.                           ║
║     Centrum broke 5 boxes (in both directions) — high volatility.                  ║
║     → SIGNAL: Look for stocks that BUILD COMPRESSION then EXPAND.                   ║
║                                                                                    ║
║  2. VOLUME CONFIRMS ALL:                                                           ║
║     Every breakout in these stocks had 1.5x-10x volume.                             ║
║     Ather: 6.3x vol on Apr 13 breakout. Nephro: 10.2x vol on Feb 11.              ║
║     Centrum spike: 24.9x vol on Mar 24 (institutional accumulation).               ║
║     → RULE: If volume doesn't confirm, the breakout is a trap.                     ║
║                                                                                    ║
║  3. THE REVERSAL PATTERN (Centrum Case Study):                                     ║
║     Centrum shows that even stocks in -31% drawdown can have Darvas merit.         ║
║     Key: RSI was 19.5 (extreme oversold) BUT RISING.                               ║
║     Volume spikes showed up at REVERSAL POINTS, not at lows.                        ║
║     → INSIGHT: Darvas works in BOTH directions — breakouts AND snapbacks.           ║
║                                                                                    ║
║  4. VOLATILITY CLUSTERS:                                                           ║
║     All 3 have high daily vol (2.9-4.0%) — 2x the market average.                  ║
║     High vol = high potential moves = Darvas-friendly.                              ║
║     → FILTER: Only scan stocks with daily vol > 2% for Darvas setup.               ║
║                                                                                    ║
║  5. SECTOR DIVERSITY:                                                              ║
║     Ather = Auto/EV | Centrum = Financials | Nephro = Healthcare                    ║
║     → INSIGHT: Darvas is SECTOR-AGNOSTIC. It works wherever volatility+volume exist.║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝""")


def print_similar_stocks():
    print("""
╔════════════════════════════════════════════════════════════════════════════════════╗
║              TOP SIMILAR STOCKS — CURRENT MARKET REAL-TIME DATA                   ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                    ║
║  TIER 1: STRONGEST PATTERN MATCH (Score 8-10/10) ★                                ║
║  ──────────────────────────────────────────────────────────────────────────────    ║
║  🥇 ADANIGREEN.NS — ₹? (Score 10) — 2 breakouts, +79% 3M, RSI 71.8, Vol 2.9%     ║
║      → Darvas breakout active, EV sector momentum                                ║
║      → MATCHES: Ather Energy pattern (breakout + sector momentum)                ║
║                                                                                    ║
║  🥇 APOLLOHOSP.NS — ₹? (Score 9) — 3 breakouts, +9.6% 3M, RSI 68.8               ║
║      → Clean breakouts, healthcare sector like Nephro                           ║
║      → MATCHES: Nephrocare pattern (healthcare breakout runner)                  ║
║                                                                                    ║
║  🥇 MOTILALOFS.NS — ₹? (Score 9) — 3 breakouts, +25% 3M, RSI 54.9                ║
║      → Financial services like Centrum, strong uptrend                          ║
║      → MATCHES: Dynamic breakout runner                                          ║
║                                                                                    ║
║  🥇 SONACOMS.NS — ₹? (Score 9) — 3 breakouts, +19.7% 3M, RSI 55.2                ║
║      → Automotive sector like Ather, volume breakout pattern                     ║
║      → MATCHES: Ather Energy pattern                                              ║
║                                                                                    ║
║  🥇 RBLBANK.NS — ₹? (Score 9) — 1 recent breakout, +21% 3M, RSI 73.7             ║
║      → Financial like Centrum but BULLISH, breakout active                      ║
║                                                                                    ║
║  🥇 ADANIPORTS.NS — (Score 9) — 4 breakouts, +28% 3M                              ║
║                                                                                    ║
║  TIER 2: HIGH POTENTIAL (Score 6-7) ★★                                            ║
║  ──────────────────────────────────────────────────────────────────────────────    ║
║  GLAND.NS — 5 breakouts! +36% 3M — Pharma (like Nephro)                         ║
║  TRENT.NS — 3 breakouts, +12.5% 3M — Retail momentum                            ║
║  POLYCAB.NS — 2 breakouts, +17% 3M — Industrial momentum                        ║
║  PIDILITIND.NS — 4 breakouts, +7% 3M — Consumer staples breakout pattern        ║
║  MANAPPURAM.NS — 4 breakouts, +20% 3M — Financial with deep value               ║
║  COFORGE.NS — 3 breakouts, +20% 3M — IT momentum                                ║
║  ELECTCAST.NS — 3 breakouts, +19.8% 3M — Auto/EV ancillaries (like Ather)       ║
║                                                                                    ║
║  TIER 3: EMERGING (Score 4-5) ★★★                                                 ║
║  ──────────────────────────────────────────────────────────────────────────────    ║
║  IIFL.NS — Financial (like Centrum), +7.5% 3M                                   ║
║  FORTIS.NS — Healthcare (like Nephro), 3 breakouts                              ║
║  BIOCON.NS — Pharma, 7 breakouts! highest count                                  ║
║  DIXON.NS — Electronics mfg, +18.5% 3M                                          ║
║  BAJAJ-AUTO.NS — Auto (like Ather), 4 breakouts                                 ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝""")


if __name__ == "__main__":
    import sys
    
    # Check args for mode
    mode = "full"  # default
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    
    if mode == "dv-scan":
        # Quick DV scanner mode (for cron)
        print("\n" + "█" * 60)
        print("  DIRECTIONAL VOLATILITY SCAN MODE")
        print("█" * 60)
        dv_result = run_dv_scanner()
        print_dv_report(dv_result)
        
    elif mode == "dv-monitor":
        # Real-time monitor mode (for intraday alerts)
        print("\n" + "█" * 60)
        print("  DV REAL-TIME MONITOR MODE")
        print("█" * 60)
        monitor_result = run_dv_monitor(send_alerts=True)
        if monitor_result.get('alerts'):
            send_dv_alerts_telegram(monitor_result)
        
    elif mode == "dv-cron":
        # Cron job mode — scan + monitor + alert
        run_dv_cron_scan()
        
    else:
        # Full daily routine (default)
        print_full_analysis()
        print_pattern_correlation()
        print_similar_stocks()
        
        print("\n" + "█" * 60)
        print("  PRO TRADER PROFILE INITIALIZATION")
        print("█" * 60)
        
        profile, results, dv_results = run_daily_routine()
        
        print("\n" + "█" * 60)
        print("  PROFILE READY")
        print("  Next step: Integrate with DarvasPaperTrader daily cron")
        print("  DV scanner ready: python pro_trader_profile.py dv-cron")
        print("█" * 60)
