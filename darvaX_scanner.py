#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════
  DARVAX PATTERN SCANNER — Based on DarvaX Trading Methodology
  ══════════════════════════════════════════════════════════════════════════════
  Author: Govind's Pro Trader Profile
  Source: DarvaX PDF by Amitabh Jha

  Detects algorithmic versions of DarvaX-specific patterns:

  1. HIGH_DRY_FRY      — 20-50% surge → 10-20% correction → baby candle base → blast off
  2. BULLISH_TASUKI    — Long bearish + gap-up bullish closing above bear's high
  3. INSIDE_BAR_BREAK  — Inside bar consolidation → breakout above range high  
  4. MORNING_STAR      — Bearish → doji → bullish (>50% of bear candle)
  5. DOUBLE_BOTTOM     — W-shaped reversal with neckline breakout
  6. BABY_CRADLE       — Tight baby candles clustering near support
  7. DARVAX_JALWA      — Tight Darvas box + explosive volume breakout
  8. LAL_DABANGG       — Tall green candle (3x avg) — momentum surge
  9. ZIGZAG_FIB        — ZigZag swing low + 61.8% fib retracement + above 10 EMA

  "Trade the setup, not the story."
══════════════════════════════════════════════════════════════════════════════
"""

import datetime
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np


# ─── Pattern Constants ──────────────────────────────────────────────────────

DARVAX_PATTERNS = {
    "HIGH_DRY_FRY": {
        "name": "High Dry Fry",
        "emoji": "🍟",
        "description": "Stock surges 20-50% on huge volume → corrects 10-20% → baby candle base → blast 65%+",
        "reference": "DarvaX Session-2: BSL example — rose 40% in 3 days, corrected 18%, made baby candles, blasted 65%",
    },
    "BULLISH_TASUKI": {
        "name": "Bullish Tasuki Line Reversal",
        "emoji": "🌅",
        "description": "Long bearish candle → gap-up bullish candle closing above bear's high — reversal signal",
        "reference": "DarvaX Tasuki Pattern: NFL example",
    },
    "INSIDE_BAR_BREAK": {
        "name": "Inside Bar Breakout",
        "emoji": "📦",
        "description": "Inside bar consolidation → volume breakout above mother bar high",
        "reference": "DarvaX Inside Bar Pattern",
    },
    "MORNING_STAR": {
        "name": "Morning Star Reversal",
        "emoji": "⭐",
        "description": "3-candle reversal: long bear → small indecision → long bull closing above midpoint",
        "reference": "DarvaX Morning Star Pattern",
    },
    "DOUBLE_BOTTOM": {
        "name": "Double Bottom",
        "emoji": "🔵",
        "description": "W-shaped bottom with two swing lows at same level — breakout above neckline",
        "reference": "DarvaX Double Bottom: Target = Neckline + (Neckline - Low)",
    },
    "BABY_CRADLE": {
        "name": "Baby Cradle Consolidation",
        "emoji": "👶",
        "description": "Multiple tiny candlesticks clustering in tight range — coiled spring before breakout",
        "reference": "DarvaX Chotu Chotu Baby Candle pattern",
    },
    "DARVAX_JALWA": {
        "name": "DarvaX Jalwa",
        "emoji": "🔥",
        "description": "Tight Darvas box with multiple touchpoints → explosive juice breakout",
        "reference": "DarvaX Jalwa Pattern (extra juicy setup)",
    },
    "LAL_DABANGG": {
        "name": "Lal Dabangg (Red Hot Strong)",
        "emoji": "🌶️",
        "description": "Tall green candle (3x+ avg body) with huge volume — institutional buying surge",
        "reference": "DarvaX — tick marks on Lal Dabangg candle",
    },
    "ZIGZAG_FIB": {
        "name": "ZigZag Fibonacci Entry",
        "emoji": "📐",
        "description": "Price retraces to 61.8% Fibonacci of previous swing → buy above 10 EMA → ride to next swing high",
        "reference": "DarvaX ZigZag Trading + Fibonacci Golden Ratio",
    },
}

# ─── Helper Functions ───────────────────────────────────────────────────────

def _candle_body(open_p, close_p):
    """Calculate absolute candle body size."""
    return abs(close_p - open_p)


def _candle_range(high, low):
    """Calculate candle range."""
    return high - low


def _is_bullish(open_p, close_p):
    """Check if candle is bullish (green)."""
    return close_p > open_p


def _is_bearish(open_p, close_p):
    """Check if candle is bearish (red)."""
    return close_p < open_p


def _avg_body_size(df: pd.DataFrame, lookback: int = 20) -> float:
    """Calculate average body size over lookback period."""
    bodies = abs(df['close'].iloc[-lookback:] - df['open'].iloc[-lookback:])
    return bodies.mean()


def _avg_range(df: pd.DataFrame, lookback: int = 20) -> float:
    """Calculate average high-low range over lookback period."""
    ranges = df['high'].iloc[-lookback:] - df['low'].iloc[-lookback:]
    return ranges.mean()


def _is_doji(open_p, close_p, high, low, threshold=0.1):
    """Check if candle is a doji (small body relative to range)."""
    body = _candle_body(open_p, close_p)
    rng = _candle_range(high, low)
    if rng == 0:
        return False
    return body / rng < threshold


# ─── Pattern Detection Functions ────────────────────────────────────────────

def detect_high_dry_fry(df: pd.DataFrame) -> dict:
    """
    DarvaX HIGH DRY FRY PATTERN (Session-2)
    
    The money pattern from the PDF:
    1. Stock moves 20-50% on huge volumes (phase 1: surge)
    2. Correction of 10-20% from peak (phase 2: pullback)
    3. Small baby candles clustering at low (phase 3: base formation)
    4. Blasts off from base (phase 4: re-entry)
    
    Returns match data with phases identified.
    """
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    n = len(close)
    
    if n < 45:
        return {"matched": False, "score": 0, "phases": []}
    
    result = {"matched": False, "score": 0, "phases": [], "evidence": []}
    
    # Use last 6 months of data
    lookback = min(n, 125)
    
    # 1. Find the surge phase (20-50% move with high volume)
    surge_candidates = []
    avg_vol_20 = np.mean(volume[-lookback:]) if lookback <= n else np.mean(volume)
    
    for i in range(max(3, n - lookback), n):
        look_fwd = min(15, n - i)
        if look_fwd < 3:
            break
        price_change = (close[i + look_fwd - 1] / close[i] - 1) * 100
        vol_ratio = np.mean(volume[i:i + look_fwd]) / max(avg_vol_20, 1)
        
        if 15 <= price_change <= 60 and vol_ratio >= 1.3:
            surge_candidates.append({
                "start_idx": i,
                "end_idx": i + look_fwd - 1,
                "surge_pct": round(price_change, 1),
                "vol_ratio": round(vol_ratio, 1),
                "peak_price": float(max(close[i:i + look_fwd])),
            })
    
    if not surge_candidates:
        return result
    
    # Pick the best/most recent surge
    best_surge = max(surge_candidates, key=lambda s: s["surge_pct"] * s["vol_ratio"])
    surge_end = best_surge["end_idx"]
    peak_price = best_surge["peak_price"]
    peak_idx = surge_end  # approximate
    
    # 2. Find correction phase (10-20% drop from peak)
    if surge_end >= n - 5:
        return result  # too recent, no time for correction yet
    
    post_surge = close[surge_end:]
    min_post_idx = np.argmin(post_surge) + surge_end
    
    if min_post_idx >= n:
        return result
    
    correction_pct = (peak_price - close[min_post_idx]) / peak_price * 100
    
    if not (8 <= correction_pct <= 35):
        return result
    
    correction_end = min_post_idx
    
    # 3. Baby candle base formation (low volatility after correction)
    if correction_end >= n - 3:
        return result  # no room for base
    
    base_candles = close[correction_end:]
    if len(base_candles) < 5:
        return result
    
    base_range_pct = (max(close[correction_end:]) - min(close[correction_end:])) / min(close[correction_end:]) * 100
    base_vol_avg = np.mean(volume[correction_end:]) / max(avg_vol_20, 1)
    base_days = len(base_candles)
    
    # Check for baby candles (low volatility in base)
    # Calculate average candle body size during base vs overall
    if correction_end > 0 and correction_end < n - 1:
        avg_body_base = np.mean(abs(close[correction_end:] - df['open'].values[correction_end:]))
        avg_body_overall = np.mean(abs(close[:n-1] - df['open'].values[:n-1])) if n > 1 else avg_body_base
        body_ratio = avg_body_base / max(avg_body_overall, 0.01)
        
        base_compression = body_ratio < 0.8  # baby candles are smaller
    else:
        base_compression = False
        body_ratio = 1.0
    
    # 4. Check if already blasting off from base (current action)
    recent_breakout = False
    if len(close[correction_end:]) >= 3:
        recent_move = (close[-1] / close[correction_end] - 1) * 100
        recent_vol = volume[-1] / max(avg_vol_20, 1)
        if recent_move > 5 and recent_vol > 1.3:
            recent_breakout = True
    
    # Calculate score
    score = 0
    evidence = []
    
    if best_surge["surge_pct"] >= 20:
        score += 25
        evidence.append(f"✅ Surge phase: +{best_surge['surge_pct']}% on {best_surge['vol_ratio']}x volume")
    elif best_surge["surge_pct"] >= 15:
        score += 15
        evidence.append(f"🟡 Surge phase: +{best_surge['surge_pct']}% (moderate surge)")
    
    if 10 <= correction_pct <= 25:
        score += 25
        evidence.append(f"✅ Correction: -{correction_pct:.1f}% from peak (ideal pullback zone)")
    elif correction_pct > 25:
        score += 10
        evidence.append(f"🟡 Correction: -{correction_pct:.1f}% (deep pullback)")
    else:
        score += 15
        evidence.append(f"🟡 Correction: -{correction_pct:.1f}% (shallow pullback)")
    
    if base_days >= 8:
        score += 20
        evidence.append(f"✅ Base formation: {base_days} days — well-developed base")
    elif base_days >= 5:
        score += 10
        evidence.append(f"🟡 Base formation: {base_days} days — early base")
    
    if base_vol_avg < 0.8 and base_days >= 5:
        score += 15
        evidence.append(f"✅ Volume drying up in base ({base_vol_avg:.1f}x avg) — selling exhaustion")
    
    if base_compression:
        score += 10
        evidence.append(f"✅ Baby candle compression (body ratio {body_ratio:.2f}) — coiled spring")
    
    if recent_breakout:
        score += 15
        evidence.append(f"🚀 Breaking out from base! +{recent_move:.1f}% on {recent_vol:.1f}x volume")
    
    if score >= 50:
        result["matched"] = True
        result["score"] = score
        result["phases"] = [
            {"phase": "surge", "pct": best_surge["surge_pct"], "vol_ratio": best_surge["vol_ratio"]},
            {"phase": "correction", "pct": round(correction_pct, 1)},
            {"phase": "base_days", "count": base_days},
            {"phase": "breakout", "active": recent_breakout},
        ]
        result["evidence"] = evidence
    
    return result


def detect_bullish_tasuki(df: pd.DataFrame) -> dict:
    """
    DarvaX BULLISH TASUKI LINE REVERSAL PATTERN
    
    Rules from PDF:
    - Previous long bearish candle
    - Bullish candle should open gap up (not touching bearish candle's close)
    - Bullish candle closing should be ABOVE the highest price of the bearish candle
    - Huge bullish volumes is icing on the cake
    """
    close = df['close'].values
    open_p = df['open'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    n = len(close)
    
    if n < 3:
        return {"matched": False, "score": 0}
    
    result = {"matched": False, "score": 0, "evidence": []}
    
    avg_body = _avg_body_size(df)
    avg_vol = np.mean(volume[-20:]) if n >= 20 else np.mean(volume)
    
    # Check the last 3 candles
    i = n - 1  # most recent candle (bullish reversal)
    j = i - 1  # bearish candle
    k = i - 2  # before bearish
    
    if k < 0:
        return result
    
    # Candle j must be bearish (long red)
    if not _is_bearish(open_p[j], close_p[j]):
        return result
    
    bear_body = _candle_body(open_p[j], close_p[j])
    if bear_body < avg_body * 1.2:
        return result  # bearish candle not long enough
    
    # Candle i must be bullish (green)
    if not _is_bullish(open_p[i], close_p[i]):
        return result
    
    # Must open gap up (candle i's open > candle j's close)
    if open_p[i] <= close_p[j]:
        return result
    
    # Must close above bearish candle's HIGH
    if close_p[i] <= high[j]:
        # Allow if very close to high and volume is huge
        if close_p[i] < high[j] * 0.98:
            return result
    
    score = 0
    evidence = []
    
    # Strong gap up
    gap_pct = (open_p[i] / close_p[j] - 1) * 100
    if gap_pct >= 2:
        score += 30
        evidence.append(f"✅ Strong gap up: +{gap_pct:.1f}%")
    else:
        score += 15
        evidence.append(f"🟡 Gap up: +{gap_pct:.1f}%")
    
    # Body size of reversal candle
    bull_body = _candle_body(open_p[i], close_p[i])
    if bull_body >= avg_body * 1.5:
        score += 20
        evidence.append(f"✅ Large bullish body: {bull_body:.1f} vs avg {avg_body:.1f}")
    
    # Volume confirmation
    vol_ratio = volume[i] / max(avg_vol, 1)
    if vol_ratio >= 2.0:
        score += 25
        evidence.append(f"✅ Massive volume: {vol_ratio:.1f}x")
    elif vol_ratio >= 1.5:
        score += 15
        evidence.append(f"🟡 Good volume: {vol_ratio:.1f}x")
    
    # Closed above bear high
    if close_p[i] > high[j]:
        score += 25
        evidence.append(f"✅ Closed above bear high (₹{high[j]:.1f}) — full reversal")
    
    if score >= 50:
        result["matched"] = True
        result["score"] = score
        result["evidence"] = evidence
    
    return result


def detect_inside_bar_breakout(df: pd.DataFrame) -> dict:
    """
    DarvaX INSIDE BAR BREAKOUT PATTERN
    
    - Inside bar candle (current range completely inside previous range)
    - Then candle breaks out above mother bar's high with volume
    """
    close = df['close'].values
    open_p = df['open'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    n = len(close)
    
    if n < 5:
        return {"matched": False, "score": 0}
    
    result = {"matched": False, "score": 0, "evidence": []}
    avg_vol = np.mean(volume[-20:]) if n >= 20 else np.mean(volume)
    
    i = n - 1  # current candle (breakout)
    if i < 2:
        return result
    
    # Look for an inside bar within last 10 candles
    for lookback in range(1, min(11, n - 1)):
        ib_idx = i - lookback  # potential inside bar
        mother_idx = ib_idx - 1  # mother bar
        
        if mother_idx < 0:
            break
        
        # Check if ib is an inside bar (range fully inside mother's range)
        inside_bar = (
            high[ib_idx] <= high[mother_idx] and
            low[ib_idx] >= low[mother_idx]
        )
        
        if not inside_bar:
            continue
        
        # Now check if the candle AFTER the inside bar breaks out
        if ib_idx + 1 >= n:
            continue
        
        breakout_idx = ib_idx + 1  # candle after inside bar
        breakout_high = close[breakout_idx] if _is_bullish(open_p[breakout_idx], close[breakout_idx]) else high[breakout_idx]
        
        is_breakout = breakout_high > high[mother_idx]
        if not is_breakout:
            continue
        
        # Found an inside bar breakout
        score = 0
        evidence = []
        
        # Volume on breakout
        vol_ratio = volume[breakout_idx] / max(avg_vol, 1)
        if vol_ratio >= 2.0:
            score += 30
            evidence.append(f"✅ Breakout on {vol_ratio:.1f}x volume — strong confirmation")
        elif vol_ratio >= 1.5:
            score += 20
            evidence.append(f"🟡 Breakout on {vol_ratio:.1f}x volume")
        else:
            score += 10
        
        # Breakout strength
        br_pct = (close[breakout_idx] / high[mother_idx] - 1) * 100
        if br_pct > 3:
            score += 25
            evidence.append(f"✅ Strong breakout: +{br_pct:.1f}% above mother bar")
        elif br_pct > 1:
            score += 15
            evidence.append(f"🟡 Breakout: +{br_pct:.1f}% above mother bar")
        
        # Inside bar tightness (very tight = better)
        ib_range = high[ib_idx] - low[ib_idx]
        mother_range = high[mother_idx] - low[mother_idx]
        if mother_range > 0:
            tightness = ib_range / mother_range
            if tightness < 0.3:
                score += 20
                evidence.append(f"✅ Very tight inside bar ({tightness:.0%} of mother) — coiled")
            elif tightness < 0.5:
                score += 10
                evidence.append(f"🟡 Moderate inside bar ({tightness:.0%} of mother)")
        
        # Recent breakout (within last 3 candles)
        if n - breakout_idx <= 3:
            score += 15
            evidence.append("🆕 Fresh breakout signal")
        
        if score >= 50:
            result["matched"] = True
            result["score"] = score
            result["evidence"] = evidence
            result["inside_bar_idx"] = int(ib_idx)
            result["breakout_idx"] = int(breakout_idx)
        
        return result  # return first/strongest match
    
    return result


def detect_morning_star(df: pd.DataFrame) -> dict:
    """
    DarvaX MORNING STAR PATTERN
    
    3-candle reversal pattern:
    1. Long bearish candle (red)
    2. Small indecision candle (doji/small body)
    3. Long bullish candle closing above midpoint of first bearish candle
    """
    close = df['close'].values
    open_p = df['open'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    n = len(close)
    
    if n < 4:
        return {"matched": False, "score": 0}
    
    result = {"matched": False, "score": 0, "evidence": []}
    avg_body = _avg_body_size(df)
    
    i = n - 1  # bullish candle (day 3)
    j = i - 1  # indecision candle (day 2)
    k = i - 2  # bearish candle (day 1)
    
    if k < 0:
        return result
    
    # Day 1: long bearish
    if not _is_bearish(open_p[k], close_p[k]):
        return result
    
    bear_body = _candle_body(open_p[k], close_p[k])
    if bear_body < avg_body * 1.3:
        return result
    
    # Day 2: small body / doji
    body2 = _candle_body(open_p[j], close_p[j])
    if body2 > avg_body * 0.8:
        return result  # not small enough
    
    # Day 3: long bullish
    if not _is_bullish(open_p[i], close_p[i]):
        return result
    
    bull_body = _candle_body(open_p[i], close_p[i])
    if bull_body < avg_body * 1.2:
        return result
    
    # Bullish candle close should be above midpoint of bearish candle
    bear_mid = (high[k] + low[k]) / 2
    if close_p[i] <= bear_mid:
        return result
    
    score = 0
    evidence = []
    
    # Strength of bearish candle
    if bear_body >= avg_body * 2:
        score += 15
        evidence.append(f"✅ Strong bearish candle (body {bear_body:.1f}) — capitulation")
    
    # Indecision candle type
    if _is_doji(open_p[j], close_p[j], high[j], low[j]):
        score += 20
        evidence.append("✅ Doji indecision — perfect reversal pause")
    else:
        score += 10
        evidence.append(f"🟡 Small candle indecision (body {body2:.1f})")
    
    # Bullish candle strength
    if bull_body >= avg_body * 2:
        score += 25
        evidence.append(f"✅ Strong bullish candle (body {bull_body:.1f}) — conviction")
    elif bull_body >= avg_body * 1.5:
        score += 15
    
    # Close above bear midpoint
    pct_above = (close_p[i] / bear_mid - 1) * 100
    if close_p[i] > high[k]:
        score += 25
        evidence.append(f"✅ Closed above bearish high (₹{high[k]:.1f}) — full reversal")
    else:
        score += 15
        evidence.append(f"🟡 Closed {pct_above:.1f}% above bear midpoint")
    
    # Volume on bullish candle
    avg_vol = np.mean(volume[-20:]) if n >= 20 else np.mean(volume)
    vol_ratio = volume[i] / max(avg_vol, 1)
    if vol_ratio >= 1.5:
        score += 15
        evidence.append(f"✅ Volume confirmation: {vol_ratio:.1f}x")
    
    if score >= 50:
        result["matched"] = True
        result["score"] = score
        result["evidence"] = evidence
    
    return result


def detect_double_bottom(df: pd.DataFrame) -> dict:
    """
    DarvaX DOUBLE BOTTOM PATTERN
    
    W-shaped reversal:
    - Two swing lows at similar price level
    - Neckline connecting the two peaks between them
    - Breakout above neckline = target = neckline + (neckline - low)
    """
    close = df['close'].values
    low = df['low'].values
    high = df['high'].values
    volume = df['volume'].values
    n = len(close)
    
    if n < 30:
        return {"matched": False, "score": 0}
    
    result = {"matched": False, "score": 0, "evidence": []}
    
    # Find local minima in the last 60 days
    lookback = min(n, 60)
    search_start = max(0, n - lookback)
    
    # Find swing lows (lower than 5 neighbors on each side)
    swing_lows = []
    for i in range(search_start + 3, n - 3):
        if (low[i] < low[i-1] and low[i] < low[i-2] and low[i] < low[i-3] and
            low[i] < low[i+1] and low[i] < low[i+2] and low[i] < low[i+3]):
            swing_lows.append((i, low[i]))
    
    if len(swing_lows) < 2:
        return result
    
    # Find two swing lows at similar level (within 5% of each other)
    for p1 in range(len(swing_lows) - 1):
        for p2 in range(p1 + 1, len(swing_lows)):
            idx1, val1 = swing_lows[p1]
            idx2, val2 = swing_lows[p2]
            
            # Time gap at least 10 days
            if abs(idx2 - idx1) < 10:
                continue
            
            # Similar low level
            if abs(val2 - val1) / min(val1, val2) > 0.05:
                continue
            
            # Neckline = higher of the two peaks between them
            peaks_between = high[idx1:idx2 + 1]
            neckline = max(peaks_between)
            neckline_idx = idx1 + list(peaks_between).index(neckline)
            
            # Check if price recently broke above neckline
            current_close = close[-1]
            if current_close <= neckline * 0.99:
                continue
            
            # We have a valid double bottom!
            score = 0
            evidence = []
            
            # Distance from low to neckline
            pattern_depth = neckline - min(val1, val2)
            target_price = neckline + pattern_depth
            
            # Low similarity
            low_diff_pct = abs(val2 - val1) / val1 * 100
            if low_diff_pct < 2:
                score += 25
                evidence.append(f"✅ Near-perfect low alignment (diff {low_diff_pct:.1f}%)")
            else:
                score += 15
                evidence.append(f"🟡 Good low alignment (diff {low_diff_pct:.1f}%)")
            
            # Breakout strength
            br_pct = (current_close / neckline - 1) * 100
            if br_pct > 2:
                score += 25
                evidence.append(f"✅ Strong neckline breakout: +{br_pct:.1f}%")
            elif br_pct > 1:
                score += 15
                evidence.append(f"🟡 Breakout above neckline: +{br_pct:.1f}%")
            
            # Volume on breakout
            avg_vol = np.mean(volume[-20:]) if n >= 20 else np.mean(volume)
            vol_ratio = volume[-1] / max(avg_vol, 1)
            if vol_ratio >= 1.5:
                score += 20
                evidence.append(f"✅ Volume on breakout: {vol_ratio:.1f}x")
            
            # Target projection
            score += 15
            evidence.append(f"🎯 Target ₹{target_price:.0f} (+{(target_price/neckline-1)*100:.0f}% from neckline)")
            
            if score >= 50:
                result["matched"] = True
                result["score"] = score
                result["evidence"] = evidence
                result["neckline"] = round(neckline, 2)
                result["target"] = round(target_price, 2)
                result["low1"] = round(float(val1), 2)
                result["low2"] = round(float(val2), 2)
                
                return result
    
    return result


def detect_baby_cradle(df: pd.DataFrame) -> dict:
    """
    DarvaX BABY CRADLE PATTERN (Chotu Chotu Baby Candles)
    
    Multiple tiny candlesticks clustering in a tight range.
    Indicates accumulation / coiled spring before a big move.
    Like the base in High Dry Fry but standalone.
    """
    close = df['close'].values
    open_p = df['open'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    n = len(close)
    
    if n < 15:
        return {"matched": False, "score": 0}
    
    result = {"matched": False, "score": 0, "evidence": []}
    
    avg_body = _avg_body_size(df)
    avg_range = _avg_range(df)
    avg_vol = np.mean(volume[-20:]) if n >= 20 else np.mean(volume)
    
    # Look at last 15 candles for tight consolidation
    lookback = min(15, n - 1)
    recent_high = max(high[-lookback:])
    recent_low = min(low[-lookback:])
    range_pct = (recent_high - recent_low) / recent_low * 100
    
    if range_pct > 10:
        return result  # too wide, not a cradle
    
    # Check for small candle bodies (baby candles)
    recent_bodies = [abs(close[-i] - open_p[-i]) for i in range(1, lookback + 1)]
    avg_recent_body = np.mean(recent_bodies)
    
    if avg_recent_body > avg_body * 0.8:
        return result  # bodies not small enough
    
    # Volume should be low during cradle (accumulation)
    recent_vol_ratio = np.mean(volume[-lookback:]) / max(avg_vol, 1)
    
    score = 0
    evidence = []
    
    # Tight range score
    if range_pct < 5:
        score += 30
        evidence.append(f"✅ Very tight range: {range_pct:.1f}% over {lookback} days")
    else:
        score += 20
        evidence.append(f"🟡 Moderate range: {range_pct:.1f}%")
    
    # Baby candle bodies
    body_ratio = avg_recent_body / max(avg_body, 0.01)
    if body_ratio < 0.4:
        score += 25
        evidence.append(f"✅ Tiny baby candles (body ratio {body_ratio:.2f})")
    elif body_ratio < 0.6:
        score += 15
        evidence.append(f"🟡 Small candles (body ratio {body_ratio:.2f})")
    
    # Volume drying up
    if recent_vol_ratio < 0.7:
        score += 20
        evidence.append(f"✅ Volume drying up ({recent_vol_ratio:.1f}x) — accumulation")
    elif recent_vol_ratio < 1.0:
        score += 10
        evidence.append(f"🟡 Normal volume ({recent_vol_ratio:.1f}x)")
    
    # Check if breaking out of cradle (recent move)
    if len(close) >= 3:
        recent_move = (close[-1] / close[-3] - 1) * 100
        if recent_move > 3:
            score += 15
            evidence.append(f"🚀 Breaking out of cradle! +{recent_move:.1f}% in 3 days")
        elif recent_move > 0:
            score += 10
            evidence.append(f"🟡 Edge of cradle (+{recent_move:.1f}% in 3 days)")
    
    # Cradle duration
    if lookback >= 12:
        score += 10
        evidence.append(f"✅ Extended cradle ({lookback} days) — tighter spring")
    
    if score >= 50:
        result["matched"] = True
        result["score"] = score
        result["evidence"] = evidence
    
    return result


def detect_darvaX_jalwa(df: pd.DataFrame) -> dict:
    """
    DarvaX JALWA PATTERN (Extra Juicy Setup)
    
    The "Jalwa" pattern is a tight Darvas box with:
    - 3+ touchpoints on box top/bottom
    - Multiple tests of resistance
    - Explosive volume breakout
    - High velocity move
    
    Named for that "juicy" feeling when everything aligns.
    """
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values
    n = len(close)
    
    if n < 30:
        return {"matched": False, "score": 0}
    
    result = {"matched": False, "score": 0, "evidence": []}
    avg_vol = np.mean(volume[-30:]) if n >= 30 else np.mean(volume)
    
    # Use sliding Darvas box detection
    # Find the most recent tight box with multiple touches
    lookback = min(n, 60)
    box_size = 10  # 10-day box
    
    best_box = None
    best_touches = 0
    
    for box_start in range(max(0, n - lookback), n - box_size - 5):
        box_high = max(high[box_start:box_start + box_size])
        box_low = min(low[box_start:box_start + box_size])
        box_range_pct = (box_high - box_low) / box_low * 100
        
        if box_range_pct > 12 or box_range_pct < 2:
            continue  # too loose or too tight
        
        # Count touches on top (price getting close to box high)
        touch_count = 0
        for t in range(box_start, box_start + box_size):
            if high[t] >= box_high * 0.97:
                touch_count += 1
        
        if touch_count > best_touches:
            best_touches = touch_count
            best_box = {
                "start": box_start,
                "end": box_start + box_size - 1,
                "high": box_high,
                "low": box_low,
                "range_pct": box_range_pct,
                "touches": touch_count,
            }
    
    if not best_box or best_touches < 2:
        return result
    
    # Now check if there's a breakout from this box
    box = best_box
    breakout_start = box["end"] + 1
    
    if breakout_start >= n:
        return result  # no data past box
    
    post_box = close[breakout_start:]
    if len(post_box) < 2:
        return result
    
    # Check if price broke above box high
    above_box = [x > box["high"] for x in post_box]
    if not any(above_box):
        return result
    
    score = 0
    evidence = []
    
    # Box tightness
    if box["range_pct"] < 6:
        score += 20
        evidence.append(f"✅ Tight Darvas box: {box['range_pct']:.1f}% range")
    
    # Touch count (more touches = stronger box)
    if box["touches"] >= 4:
        score += 25
        evidence.append(f"✅ {box['touches']} touches on box top — strong resistance test")
    elif box["touches"] >= 2:
        score += 15
        evidence.append(f"🟡 {box['touches']} touches on box top")
    
    # Breakout strength
    break_high = max(post_box)
    br_pct = (break_high / box["high"] - 1) * 100
    if br_pct > 5:
        score += 20
        evidence.append(f"✅ Strong breakout: +{br_pct:.1f}% above box")
    elif br_pct > 2:
        score += 10
    
    # Volume on breakout
    breakout_vol_idx = breakout_start + list(post_box).index(break_high)
    if breakout_vol_idx < len(volume):
        vol_ratio = volume[breakout_vol_idx] / max(avg_vol, 1)
        if vol_ratio >= 2:
            score += 20
            evidence.append(f"✅ Explosive volume: {vol_ratio:.1f}x on breakout")
        elif vol_ratio >= 1.5:
            score += 10
            evidence.append(f"🟡 Volume: {vol_ratio:.1f}x on breakout")
    
    # Post-breakout holding (price staying above box)
    recent_above = sum(1 for x in post_box[-5:] if x > box["high"]) if len(post_box) >= 5 else 0
    if recent_above >= 3:
        score += 15
        evidence.append(f"✅ Holding above box: {recent_above}/5 days above")
    
    if score >= 50:
        result["matched"] = True
        result["score"] = score
        result["evidence"] = evidence
        result["box_high"] = round(box["high"], 2)
        result["box_low"] = round(box["low"], 2)
        result["breakout_pct"] = round(br_pct, 1)
    
    return result


def detect_lal_dabangg(df: pd.DataFrame) -> dict:
    """
    DarvaX LAL DABANGG CANDLE (Red Hot Strong)
    
    Despite the name "Lal" (red), it's a powerful GREEN candle:
    - Very tall body (3x+ average)
    - Huge volume surge
    - Institutional buying pressure
    - Usually at breakout point or after consolidation
    """
    close = df['close'].values
    open_p = df['open'].values
    volume = df['volume'].values
    n = len(close)
    
    if n < 5:
        return {"matched": False, "score": 0}
    
    result = {"matched": False, "score": 0, "evidence": []}
    
    avg_body = _avg_body_size(df)
    avg_vol = np.mean(volume[-20:]) if n >= 20 else np.mean(volume)
    
    i = n - 1  # current candle
    
    # Must be bullish
    if not _is_bullish(open_p[i], close_p[i]):
        return result
    
    body = _candle_body(open_p[i], close_p[i])
    
    if body < avg_body * 2.0:
        return result  # not big enough
    
    score = 0
    evidence = []
    
    # Body size relative to average
    body_ratio = body / max(avg_body, 0.01)
    if body_ratio >= 3.0:
        score += 30
        evidence.append(f"✅ Massive candle: {body_ratio:.1f}x avg body size")
    elif body_ratio >= 2.5:
        score += 20
        evidence.append(f"🟡 Big candle: {body_ratio:.1f}x avg body size")
    else:
        score += 15
    
    # Volume confirmation
    vol_ratio = volume[i] / max(avg_vol, 1)
    if vol_ratio >= 3.0:
        score += 30
        evidence.append(f"✅ Huge volume: {vol_ratio:.1f}x — institutional buying")
    elif vol_ratio >= 2.0:
        score += 20
        evidence.append(f"🟡 Strong volume: {vol_ratio:.1f}x")
    elif vol_ratio >= 1.5:
        score += 10
    
    # Price gain % on candle
    gain_pct = (close[i] / open_p[i] - 1) * 100
    if gain_pct > 5:
        score += 25
        evidence.append(f"✅ Big gain: +{gain_pct:.1f}% in single candle")
    elif gain_pct > 3:
        score += 15
        evidence.append(f"🟡 Good gain: +{gain_pct:.1f}% in single candle")
    
    # Check if at breakout from recent range
    prev_high = max(high[:i]) if i > 5 else 0
    if prev_high > 0 and close[i] > prev_high * 0.98:
        score += 15
        evidence.append(f"✅ Breaking out from recent range high")
    
    if score >= 50:
        result["matched"] = True
        result["score"] = score
        result["evidence"] = evidence
        result["candle_body_ratio"] = round(body_ratio, 1)
        result["vol_ratio"] = round(vol_ratio, 1)
        result["gain_pct"] = round(gain_pct, 1)
    
    return result


def detect_zigzag_fib(df: pd.DataFrame) -> dict:
    """
    DarvaX ZIGZAG + FIBONACCI ENTRY
    
    Strategy from PDF:
    1. Plot ZigZag indicator (swing highs/lows)
    2. Wait for swing low of ZigZag
    3. Look for retracement to 61.8% Fibonacci golden ratio
    4. Wait for buy signal above 10 EMA
    5. Ride the trend till next ZigZag swing high
    
    Simplified to: Detect a significant swing, check retracement to 61.8%,
    and check if price is holding above 10 EMA.
    """
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    n = len(close)
    
    if n < 40:
        return {"matched": False, "score": 0}
    
    result = {"matched": False, "score": 0, "evidence": []}
    
    # Calculate 10 EMA
    ema10 = pd.Series(close).ewm(span=10, adjust=False).mean().values
    
    # Find the most recent significant swing low and high
    # A swing low is lower than 3 bars on each side
    swing_lows = []
    swing_highs = []
    
    for i in range(3, n - 3):
        if low[i] < min(low[i-3:i]) and low[i] <= min(low[i+1:i+4]):
            swing_lows.append((i, low[i]))
        if high[i] > max(high[i-3:i]) and high[i] >= max(high[i+1:i+4]):
            swing_highs.append((i, high[i]))
    
    if len(swing_lows) < 1 or len(swing_highs) < 1:
        return result
    
    # Find the most recent swing high → swing low pair
    recent_swing_high = swing_highs[-1] if swing_highs else None
    recent_swing_low = swing_lows[-1] if swing_lows else None
    
    if not recent_swing_high or not recent_swing_low:
        return result
    
    high_idx, high_val = recent_swing_high
    low_idx, low_val = recent_swing_low
    
    # Swing low must come after swing high (downtrend → retracement)
    if low_idx <= high_idx:
        return result
    
    # Calculate Fibonacci levels
    swing_range = high_val - low_val
    fib_618 = high_val - swing_range * 0.618
    fib_382 = high_val - swing_range * 0.382
    fib_50 = high_val - swing_range * 0.5
    
    current_price = close[-1]
    
    # Is current price near 61.8% fib level?
    near_618 = abs(current_price - fib_618) / fib_618 * 100 < 3
    near_50 = abs(current_price - fib_50) / fib_50 * 100 < 3
    
    if not (near_618 or near_50):
        return result
    
    # Check if price is above 10 EMA (buy signal)
    above_ema10 = current_price > ema10[-1]
    ema10_slope = (ema10[-1] - ema10[-3]) / ema10[-3] * 100 if n >= 3 else 0
    
    score = 0
    evidence = []
    
    # Fib level accuracy
    if near_618:
        score += 30
        fib_pct = (current_price / fib_618 - 1) * 100
        evidence.append(f"✅ At 61.8% golden ratio (deviation {abs(fib_pct):.1f}%)")
    elif near_50:
        score += 20
        fib_pct = (current_price / fib_50 - 1) * 100
        evidence.append(f"🟡 At 50% fib level (deviation {abs(fib_pct):.1f}%)")
    
    # Above 10 EMA 
    if above_ema10:
        score += 25
        evidence.append(f"✅ Above 10 EMA ({current_price:.1f} > {ema10[-1]:.1f}) — buy signal active")
    else:
        score += 10
        evidence.append(f"🟡 Below 10 EMA — wait for buy signal")
    
    # EMA slope (rising EMA adds conviction)
    if ema10_slope > 0:
        score += 20
        evidence.append(f"✅ 10 EMA rising ({ema10_slope:.2f}%) — trend up")
    else:
        score += 5
    
    # Swing size shows volatility
    swing_pct = (high_val / low_val - 1) * 100
    if swing_pct > 20:
        score += 15
        evidence.append(f"✅ Strong swing: {swing_pct:.1f}% from high to low")
    elif swing_pct > 10:
        score += 10
    
    # Volume on the bounce
    avg_vol = np.mean(df['volume'].values[-20:]) if n >= 20 else np.mean(df['volume'].values)
    vol_ratio = df['volume'].values[-1] / max(avg_vol, 1)
    if vol_ratio > 1.3:
        score += 10
        evidence.append(f"🟡 Volume on bounce: {vol_ratio:.1f}x")
    
    if score >= 50:
        result["matched"] = True
        result["score"] = score
        result["evidence"] = evidence
        result["fib_618"] = round(fib_618, 2)
        result["fib_382"] = round(fib_382, 2)
        result["swing_high"] = round(high_val, 2)
        result["swing_low"] = round(low_val, 2)
        result["above_ema10"] = bool(above_ema10)
    
    return result


# ─── Master Scanner ─────────────────────────────────────────────────────────

def run_darvaX_scanner(df: pd.DataFrame, ticker: str) -> dict:
    """
    Run all DarvaX pattern detectors on a stock's data.
    
    Returns the best-detectable DarvaX pattern and full scores.
    """
    detectors = {
        "HIGH_DRY_FRY": detect_high_dry_fry,
        "BULLISH_TASUKI": detect_bullish_tasuki,
        "INSIDE_BAR_BREAK": detect_inside_bar_breakout,
        "MORNING_STAR": detect_morning_star,
        "DOUBLE_BOTTOM": detect_double_bottom,
        "BABY_CRADLE": detect_baby_cradle,
        "DARVAX_JALWA": detect_darvaX_jalwa,
        "LAL_DABANGG": detect_lal_dabangg,
        "ZIGZAG_FIB": detect_zigzag_fib,
    }
    
    results = {}
    best_pattern = None
    best_score = 0
    
    for pattern_name, detector_fn in detectors.items():
        try:
            detection = detector_fn(df)
            results[pattern_name] = detection
            if detection.get("matched") and detection["score"] > best_score:
                best_pattern = pattern_name
                best_score = detection["score"]
        except Exception as e:
            results[pattern_name] = {"matched": False, "score": 0, "error": str(e)}
    
    return {
        "ticker": ticker,
        "best_darvaX_pattern": best_pattern,
        "best_darvaX_score": best_score,
        "darvaX_results": results,
    }


def scan_universe_for_darvaX(
    universe: List[str],
    data_cache: Dict[str, pd.DataFrame] = None,
    min_score: int = 40,
) -> List[dict]:
    """
    Scan a universe of stocks for DarvaX patterns.
    
    Args:
        universe: List of ticker symbols
        data_cache: Pre-fetched data dict {ticker: df}
        min_score: Minimum pattern score to include
        
    Returns:
        Sorted list of darvaX scan results
    """
    import yfinance as yf
    
    if data_cache is None:
        data_cache = {}
    
    results = []
    
    for ticker in universe:
        try:
            if ticker in data_cache:
                df = data_cache[ticker]
            else:
                df = yf.download(ticker, period="6mo", progress=False)
            
            if df.empty or len(df) < 20:
                continue
            
            # Clean the yfinance MultiIndex
            raw_cols = df.columns.tolist()
            # yfinance v0.2.4+ returns MultiIndex columns like ('Close', 'INFY.NS')
            if isinstance(raw_cols[0], tuple):
                new_cols = {}
                for col_tuple in raw_cols:
                    col_name = col_tuple[0].lower()
                    if col_name in ('open', 'high', 'low', 'close', 'volume', 'adj close'):
                        new_cols[col_name] = df[col_tuple].values
                df_clean = pd.DataFrame(new_cols, index=df.index)
            else:
                df_clean = df.copy()
                df_clean.columns = [c.lower() for c in df_clean.columns]

            # Drop incomplete rows (today's bar often has NaN OHLC)
            df_clean = df_clean.dropna(subset=['close'])

            darvaX_result = run_darvaX_scanner(df_clean, ticker)
            
            if darvaX_result["best_darvaX_score"] >= min_score:
                # Get current price (last non-NaN close)
                valid_close = df_clean['close'].dropna()
                current_price = float(valid_close.iloc[-1]) if len(valid_close) > 0 else 0.0
                darvaX_result["price"] = current_price

                # Include the pattern info
                pattern_name = darvaX_result["best_darvaX_pattern"]
                if pattern_name:
                    pattern_info = DARVAX_PATTERNS.get(pattern_name, {})
                    darvaX_result["pattern_name"] = pattern_info.get("name", pattern_name)
                    darvaX_result["pattern_emoji"] = pattern_info.get("emoji", "📊")
                    darvaX_result["pattern_desc"] = pattern_info.get("description", "")
                    
                    # Get evidence from the specific detection
                    pdr = darvaX_result["darvaX_results"].get(pattern_name, {})
                    darvaX_result["evidence"] = pdr.get("evidence", [])
                
                results.append(darvaX_result)
        
        except Exception as e:
            continue
    
    # Sort by score descending
    results.sort(key=lambda r: r["best_darvaX_score"], reverse=True)
    
    return results


def print_darvaX_report(results: List[dict], top_n: int = 15):
    """
    Print a formatted DarvaX pattern scan report.
    Matches the style of the Triad report.
    """
    print("\n" + "█" * 120)
    print("  🍟 DARVAX PATTERN SCAN — Based on DarvaX Trading Methodology")
    print("  " + datetime.date.today().isoformat())
    print("█" * 120)
    
    if not results:
        print("\n  No DarvaX patterns detected above threshold.")
        return
    
    print(f"\n  Total DarvaX matches: {len(results)}")
    print(f"\n  {'Rank':<5} {'Ticker':<20} {'Score':<8} {'Pattern':<28} {'Price':<12} {'Key Signal'}")
    print(f"  {'─'*120}")
    
    for i, r in enumerate(results[:top_n], 1):
        pattern_name = r.get("pattern_name", r.get("best_darvaX_pattern", "?"))
        emoji = r.get("pattern_emoji", "📊")
        evidence = r.get("evidence", [])
        key_signal = evidence[0][:55] if evidence else "—"
        
        print(f"  {i:<5} {r['ticker']:<20} {r['best_darvaX_score']:<8} {emoji} {pattern_name:<24} ₹{r['price']:<10.1f} {key_signal}")
    
    # Group by pattern type
    print(f"\n  {'─'*60}")
    print("  📊 DARVAX PATTERN DISTRIBUTION")
    print(f"  {'─'*60}")
    
    pattern_counts = {}
    for r in results:
        pat = r.get("best_darvaX_pattern", "UNKNOWN")
        pattern_counts[pat] = pattern_counts.get(pat, 0) + 1
    
    for pat, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        info = DARVAX_PATTERNS.get(pat, {})
        emoji = info.get("emoji", "📊")
        name = info.get("name", pat)
        fill = "█" * count
        print(f"  {emoji} {name:<25} {fill} {count}")
    
    print(f"\n  {'─'*100}")
    
    # Show detailed picks
    print("\n  🏆 TOP DARVAX PICKS (Detail)")
    for i, r in enumerate(results[:8], 1):
        pat = r.get("best_darvaX_pattern", "?")
        info = DARVAX_PATTERNS.get(pat, {})
        emoji = info.get("emoji", "📊")
        name = info.get("name", pat)
        
        print(f"\n  {i}. {emoji} {r['ticker']} — {name} (Score: {r['best_darvaX_score']}/100)")
        print(f"     Price: ₹{r['price']:.1f}")
        for ev in r.get("evidence", [])[:3]:
            print(f"     {ev}")


# ─── Entry / Exit Rules for DarvaX Patterns ──────────────────────────────

DARVAX_ENTRY_RULES = {
    "HIGH_DRY_FRY": {
        "entry_signals": [
            ("Breakout from baby candle base", lambda r: r.get('recent_breakout', False)),
            ("Volume spike > 1.5x on base breakout", lambda r: any('volume' in e.lower() for e in r.get('evidence', []))),
            ("Price above all recent baby candle highs", lambda r: r.get('best_darvaX_score', 0) >= 60),
        ],
        "exit_signals": [
            ("RSI > 80 after blast off", lambda r: False),
            ("Volume drying up after expansion", lambda r: False),
            ("Price falls below base", lambda r: False),
        ],
    },
    "BULLISH_TASUKI": {
        "entry_signals": [
            ("Bullish candle closed above bear high", lambda r: any('above bear high' in e.lower() for e in r.get('evidence', []))),
            ("Volume confirms reversal", lambda r: any('volume' in e.lower() for e in r.get('evidence', []))),
        ],
        "exit_signals": [
            ("Price fills the gap", lambda r: False),
            ("Failed to hold gain for 3 days", lambda r: False),
        ],
    },
    "DARVAX_JALWA": {
        "entry_signals": [
            ("Breakout above box high with volume", lambda r: any('explosive' in e.lower() or 'volume' in e.lower() for e in r.get('evidence', []))),
            ("Multiple box touches confirm support", lambda r: any('touch' in e.lower() for e in r.get('evidence', []))),
        ],
        "exit_signals": [
            ("Price falls back inside box", lambda r: False),
            ("Volume dries up after breakout", lambda r: False),
        ],
    },
}


if __name__ == "__main__":
    # Test mode — download and scan stocks
    import yfinance as yf
    
    test_universe = ["TMPV.NS", "TMCV.NS", "RELIANCE.NS", "TRENT.NS", "INFY.NS", "HDFCBANK.NS",
                     "BSL.NS", "M&M.NS", "BAJFINANCE.NS", "ICICIBANK.NS", "SBIN.NS"]
    
    print(f"Testing DarvaX scanner on {len(test_universe)} stocks...\n")
    
    results = scan_universe_for_darvaX(test_universe)
    print_darvaX_report(results)
