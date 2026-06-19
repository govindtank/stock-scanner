#!/usr/bin/env python3
"""
Wishlist Stock Scanner — Entry/Exit Advisor for User's Watchlist

Scans 8 stocks: EMMVEE, CENTUM, GODAVARI BIOREFIN, ATHER ENERGY,
PARAS DEFENCE, OMNITECH ENGINEERING, GROWW, TILAKNAGAR

Generates: RSI, trend, volatility, breakout status, entry/exit advice.
"""

import datetime
import json
import os
import sys
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf

# ── Configuration ─────────────────────────────────────────────────────
WISHLIST_TICKERS = {
    "EMMVEE.NS": "Emmvee",
    "CENTUM.NS": "Centum",
    "GODAVARIB.NS": "Godavari Biorefineries",
    "ATHERENERG.NS": "Ather Energy",
    "PARAS.NS": "Paras Defence",
    "OMNI.NS": "Omnitech Engineering",
    "GROWW.NS": "Groww",
    "TI.NS": "Tilaknagar",
    "BELRISE.NS": "Belrise Industries",
    "LALPATHLAB.NS": "Dr. Lal PathLabs",
    # User's tracked stocks (added Jun 2026)
    "TARIL.NS": "Taril",
    "INDSWFTLAB.NS": "Ind-Swift Labs",
    "JSWINFRA.NS": "JSW Infrastructure",
    "PIRAMALFIN.NS": "Piramal Finance",
    "AVANTIFEED.NS": "Avanti Feeds",
    "MANINDS.NS": "Man Industries",
    "NITINSPIN.NS": "Nitin Spinners",
    "GRANULES.NS": "Granules India",
    "EDELWEISS.NS": "Edelweiss",
    "NIITLTD.NS": "NIIT",
    "RELIANCE.NS": "Reliance Industries",
    "CGCL.NS": "CGC",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WISHLIST_CACHE = os.path.join(BASE_DIR, "wishlist_scan_cache.json")


# ── Indicator Helpers ─────────────────────────────────────────────────
def compute_indicators(df: pd.DataFrame) -> dict:
    """Compute technical indicators for a stock dataframe."""
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']

    # SMAs
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()

    # RSI (14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # ATR (14)
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()

    # Volume SMA
    vol_sma20 = volume.rolling(20).mean()
    vol_ratio = volume / vol_sma20

    # Daily returns / volatility
    daily_ret = close.pct_change() * 100
    daily_vol = daily_ret.std() * (252 ** 0.5)  # annualized

    # 52-week high
    high_52w = close.rolling(252).max()
    near_52wh_pct = (close / high_52w * 100).fillna(0)

    # Drawdown
    drawdown = ((close / close.cummax()) - 1) * 100
    
    # Percent above SMA20
    pct_above_sma20 = ((close / sma20) - 1) * 100

    # Breakouts (recent close > 20d box high with volume)
    box_high_20 = close.rolling(20).max()

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
        'daily_ret': daily_ret,
        'daily_vol': daily_vol,
        'near_52wh_pct': near_52wh_pct,
        'drawdown': drawdown,
        'pct_above_sma20': pct_above_sma20,
        'box_high_20': box_high_20,
    }


def clean_df(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Clean yfinance MultiIndex columns."""
    if df.empty:
        return df
    try:
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(ticker, axis=1, level=1)
    except Exception:
        pass
    # Standardize column names
    rename = {}
    for c in df.columns:
        cl = str(c).lower()
        if cl in ('open', 'high', 'low', 'close', 'volume'):
            rename[c] = cl.capitalize()
    df = df.rename(columns=rename)
    # Ensure standard names exist
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        cl = col.lower()
        if col not in df.columns and cl in df.columns:
            df.rename(columns={cl: col}, inplace=True)
    return df


# ── Advice Generation ─────────────────────────────────────────────────
def generate_advice(ticker: str, name: str, df: pd.DataFrame, ind: dict) -> dict:
    """Generate entry/exit advice for a single stock."""
    close = ind['close']
    rsi = ind['rsi']
    sma20 = ind['sma20']
    sma50 = ind['sma50']
    vol_ratio = ind['vol_ratio']
    daily_ret = ind['daily_ret']
    drawdown = ind['drawdown']
    near_52wh = ind['near_52wh_pct']
    pct_above = ind['pct_above_sma20']
    box_high_20 = ind['box_high_20']
    atr14 = ind['atr14']

    current_price = float(close.iloc[-1])
    current_rsi = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
    current_vol = float(vol_ratio.iloc[-1]) if not pd.isna(vol_ratio.iloc[-1]) else 0
    current_draw = float(drawdown.iloc[-1]) if not pd.isna(drawdown.iloc[-1]) else 0
    current_near_52wh = float(near_52wh.iloc[-1]) if not pd.isna(near_52wh.iloc[-1]) else 0
    current_pct_above = float(pct_above.iloc[-1]) if not pd.isna(pct_above.iloc[-1]) else 0
    current_atr = float(atr14.iloc[-1]) if not pd.isna(atr14.iloc[-1]) else 0
    sma20_val = float(sma20.iloc[-1]) if not pd.isna(sma20.iloc[-1]) else 0
    sma50_val = float(sma50.iloc[-1]) if not pd.isna(sma50.iloc[-1]) else 0
    daily_vol_pct = float(daily_ret.std()) if len(daily_ret) > 5 else 0

    # RSI trend (last 5 days)
    rsi_vals = rsi.dropna().values[-5:] if len(rsi.dropna()) >= 5 else []
    rsi_trend = "rising" if len(rsi_vals) >= 5 and rsi_vals[-1] > rsi_vals[0] else \
                "falling" if len(rsi_vals) >= 5 and rsi_vals[-1] < rsi_vals[0] else "stable"

    # Current breakout check
    is_breakout = False
    if len(close) > 1 and len(box_high_20) > 1:
        is_breakout = float(close.iloc[-1]) > float(box_high_20.iloc[-2]) and current_vol >= 1.5

    # SMA trend
    sma_trend = "BULLISH" if sma20_val > sma50_val > 0 else "BEARISH"

    # ── Generate Advice ────────────────────────────────────────────────
    signals = []
    reason_parts = []
    recommendation = "HOLD"
    conviction = "LOW"

    # BULL case: breakout, RSI 55-75, bullish SMA, near 52WH
    bull_score = 0
    if is_breakout:
        bull_score += 30
        signals.append("📈 Active breakout above 20d box high with volume")
    if 55 <= current_rsi <= 80:
        bull_score += 20
        signals.append(f"RSI {current_rsi:.0f} in sweet spot (55-80)")
    if sma_trend == "BULLISH":
        bull_score += 15
        signals.append("SMA20 > SMA50 — bullish alignment")
    if current_pct_above > 0:
        bull_score += 10
    if current_near_52wh >= 80:
        bull_score += 15
        signals.append(f"Near 52W high ({current_near_52wh:.0f}%)")
    if current_vol >= 1.3:
        bull_score += 10
        signals.append(f"Volume ratio {current_vol:.1f}x — institutional interest")
    if daily_vol_pct >= 2.0:
        bull_score += 5

    # BEAR/oversold case
    bear_score = 0
    if current_rsi < 35:
        bear_score += 25
        signals.append(f"RSI {current_rsi:.0f} — deeply oversold")
    if current_draw <= -15:
        bear_score += 20
        signals.append(f"Drawdown {current_draw:.0f}% — deep pullback")
    if rsi_trend == "rising" and current_rsi < 40:
        bear_score += 20
        signals.append("RSI rising from oversold — momentum shift")
    if current_vol < 0.8:
        bear_score += 10
        signals.append("Volume declining — selling exhaustion")
    if daily_vol_pct >= 2.5:
        bear_score += 10

    # DETERMINE recommendation
    if bull_score >= 50:
        recommendation = "ENTRY"
        conviction = "HIGH" if bull_score >= 70 else "MODERATE"
        reason_parts = signals[:3]
    elif bear_score >= 50:
        recommendation = "ENTRY" if current_rsi > 30 and rsi_trend == "rising" else "WATCH"
        conviction = "HIGH" if bear_score >= 70 else "MODERATE"
        reason_parts = signals[:3]
    elif current_rsi > 75:
        recommendation = "EXIT"
        conviction = "HIGH"
        reason_parts = [f"RSI {current_rsi:.0f} > 75 — overbought, consider booking"]
    elif current_draw <= -25:
        recommendation = "EXIT"
        conviction = "HIGH"
        reason_parts = [f"Drawdown {current_draw:.0f}% — consider cutting losses"]
    else:
        recommendation = "HOLD"
        conviction = "LOW"
        reason_parts = ["No strong signal — in consolidation"]
        if sma_trend == "BULLISH":
            conviction = "MODERATE"
            reason_parts = ["Bullish trend intact, wait for breakout trigger"]

    # Build support/resistance levels
    support = round(current_price - current_atr, 1)
    resistance = round(current_price + current_atr, 1)

    # Trend summary
    if sma20_val > 0:
        trend_pct = round(current_pct_above, 1)
        if trend_pct > 5:
            trend_summary = f"Strongly above SMA20 (+{trend_pct}%)"
        elif trend_pct > 0:
            trend_summary = f"Above SMA20 (+{trend_pct}%)"
        else:
            trend_summary = f"Below SMA20 ({trend_pct}%)"
    else:
        trend_summary = "Insufficient data"

    return {
        "ticker": ticker.replace(".NS", ""),
        "name": name,
        "price": round(current_price, 2),
        "rsi": round(current_rsi, 1),
        "daily_vol_pct": round(daily_vol_pct, 1),
        "volume_ratio": round(current_vol, 1),
        "sma_trend": sma_trend,
        "rsi_trend": rsi_trend,
        "near_52wh_pct": round(current_near_52wh, 1),
        "drawdown_pct": round(current_draw, 1),
        "pct_above_sma20": round(current_pct_above, 1),
        "trend_summary": trend_summary,
        "is_breakout": is_breakout,
        "support": round(sma20_val, 1) if sma20_val > 0 else support,
        "resistance": round(box_high_20.iloc[-1], 1) if not pd.isna(box_high_20.iloc[-1]) else resistance,
        "recommendation": recommendation,
        "conviction": conviction,
        "signals": signals,
        "reason": " • ".join(reason_parts),
        "bull_score": bull_score,
        "bear_score": bear_score,
    }


# ── Main Scanner ──────────────────────────────────────────────────────
def scan_wishlist(tickers: Dict[str, str] = None) -> dict:
    """Scan all wishlist stocks and return results with advice."""
    if tickers is None:
        tickers = WISHLIST_TICKERS

    results = []
    errors = []
    total = len(tickers)

    for i, (ticker, name) in enumerate(tickers.items()):
        try:
            # Track that we're processing this stock
            raw_ticker_label = ticker.replace(".NS", "").replace(".BO", "")
            
            df = yf.download(ticker, period="3mo", progress=False)
            if df.empty or len(df) < 15:
                # Include as placeholder with data_unavailable flag
                results.append({
                    "ticker": raw_ticker_label,
                    "name": name,
                    "price": 0,
                    "rsi": 0,
                    "daily_vol_pct": 0,
                    "volume_ratio": 0,
                    "sma_trend": "N/A",
                    "rsi_trend": "N/A",
                    "near_52wh_pct": 0,
                    "drawdown_pct": 0,
                    "pct_above_sma20": 0,
                    "trend_summary": "Ticker not found on NSE/BSE",
                    "is_breakout": False,
                    "support": 0,
                    "resistance": 0,
                    "recommendation": "N/A",
                    "conviction": "LOW",
                    "signals": ["⚠️ Verify NSE ticker symbol"],
                    "reason": "Stock not available on Yahoo Finance. Check NSE/BSE listing.",
                    "bull_score": 0,
                    "bear_score": 0,
                    "data_unavailable": True,
                })
                errors.append({"ticker": ticker, "name": name, "error": "Insufficient data"})
                continue
            df = clean_df(df, ticker)
            ind = compute_indicators(df)
            advice = generate_advice(ticker, name, df, ind)
            results.append(advice)
        except Exception as e:
            raw_ticker_label = ticker.replace(".NS", "").replace(".BO", "")
            results.append({
                "ticker": raw_ticker_label,
                "name": name,
                "price": 0, "rsi": 0, "daily_vol_pct": 0, "volume_ratio": 0,
                "sma_trend": "N/A", "rsi_trend": "N/A",
                "near_52wh_pct": 0, "drawdown_pct": 0, "pct_above_sma20": 0,
                "trend_summary": f"Error: {str(e)[:60]}",
                "is_breakout": False, "support": 0, "resistance": 0,
                "recommendation": "N/A", "conviction": "LOW",
                "signals": [f"⚠️ {str(e)[:60]}"],
                "reason": "Stock lookup failed. Verify NSE ticker.",
                "bull_score": 0, "bear_score": 0,
                "data_unavailable": True,
            })
            errors.append({"ticker": ticker, "name": name, "error": str(e)})

    # Sort: by recommendation priority (ENTRY first, HOLD, then WATCH/EXIT), unavailable last
    rec_priority = {"ENTRY": 0, "HOLD": 1, "WATCH": 2, "EXIT": 3, "N/A": 9}
    results.sort(key=lambda r: (rec_priority.get(r["recommendation"], 9), -r["bull_score"]))

    # Only count available stocks for summary
    available = [r for r in results if not r.get("data_unavailable")]
    output = {
        "timestamp": datetime.datetime.now().isoformat(),
        "total": total,
        "scanned": len(results),
        "available": len(available),
        "errors": len(errors),
        "results": results,
        "errors_list": errors,
        "summary": {
            "entries": len([r for r in available if r["recommendation"] == "ENTRY"]),
            "holds": len([r for r in available if r["recommendation"] == "HOLD"]),
            "watches": len([r for r in available if r["recommendation"] == "WATCH"]),
            "exits": len([r for r in available if r["recommendation"] == "EXIT"]),
            "unavailable": len([r for r in results if r.get("data_unavailable")]),
        },
    }

    # Cache results
    try:
        with open(WISHLIST_CACHE, "w") as f:
            json.dump(output, f, indent=2, default=str)
    except Exception:
        pass

    return output


def load_cached_scan() -> dict:
    """Load the last cached wishlist scan."""
    try:
        if os.path.exists(WISHLIST_CACHE):
            with open(WISHLIST_CACHE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"error": "No cached scan available", "results": []}


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if "--cached" in sys.argv:
        result = load_cached_scan()
    else:
        result = scan_wishlist()
    
    print(json.dumps(result, indent=2, default=str))
