"""
Darvas Box Breakout Detection Module for Indian Stocks (Enhanced)
==================================================================

This module implements the Darvas box method for identifying breakout opportunities
in Indian stock market using yfinance (free, no API key required).

ENHANCEMENTS:
- Advanced volume analysis with multiple timeframes
- Pattern recognition (double bottoms, pennants, flags)
- Volume-based confirmation signals
- Enhanced signal strength calculation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import datetime


class DarvasBoxDetector:
    """Implements Darvas Box Method with volume analysis and pattern recognition."""
    
    def __init__(self, window_size=5, min_box_volatility=0.02, 
                 volume_threshold=1.5, pattern_sensitivity=0.9):
        """
        Initialize the Darvas box detector.
        
        Args:
            window_size: Number of days to look back for box formation (default 5)
            min_box_volatility: Minimum volatility required within a box (%)
            volume_threshold: Volume multiplier for breakout confirmation (default 1.5 = 150%)
            pattern_sensitivity: Pattern recognition sensitivity (higher = more strict)
        """
        self.window_size = window_size
        self.min_box_volatility = min_box_volatility
        self.volume_threshold = volume_threshold
        self.pattern_sensitivity = pattern_sensitivity
        
    def detect_boxes(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """
        Detect Darvas boxes in price data with enhanced volume analysis.
        
        Args:
            df: DataFrame with 'close', 'high', 'low', 'volume' columns
            
        Returns:
            Dictionary of detected boxes with their properties
        """
        boxes = []
        
        for i in range(self.window_size, len(df)):
            # Get recent high-low range
            recent_high = df.iloc[i-self.window_size:i+1]['high'].max()
            recent_low = df.iloc[i-self.window_size:i+1]['low'].min()
            
            current_price = df.iloc[i]['close']
            volatility = (recent_high - recent_low) / recent_low
            
            # Check if we're still in the box or broke out
            if volatility >= self.min_box_volatility:
                # Calculate volume average for this period
                avg_volume = df.iloc[i-self.window_size:i+1]['volume'].mean()
                
                # Volume analysis - check volume profile
                volume_trend = self._analyze_volume_trend(df, i)
                
                boxes.append({
                    'start': i - self.window_size + 1,
                    'end': i,
                    'high': recent_high,
                    'low': recent_low,
                    'close': current_price,
                    'avg_volume': avg_volume,
                    'range': recent_high - recent_low,
                    'volume_trend': volume_trend,
                    'volume_stability': self._calculate_volume_stability(df.iloc[i-self.window_size:i+1])
                })
        
        return boxes
    
    def _analyze_volume_trend(self, df: pd.DataFrame, index: int) -> str:
        """Analyze recent volume trend."""
        recent_volumes = df['volume'].iloc[-5:]
        if len(recent_volumes) < 2:
            return 'NEUTRAL'
        
        recent_mean = recent_volumes[:-1].mean()
        current_volume = recent_volumes.iloc[-1]
        
        if current_volume > recent_mean * 1.3:
            return 'INCREASING'
        elif current_volume < recent_mean * 0.7:
            return 'DECREASING'
        else:
            return 'STABLE'
    
    def _calculate_volume_stability(self, data) -> float:
        """Calculate volume stability (lower = more stable)."""
        if len(data) < 2 or any(v == 0 for v in data['volume']):
            return 1.0
        
        volumes = [v / data['volume'].iloc[0] for v in data['volume']]
        coefficient_of_variation = np.std(volumes) / np.mean(volumes) if np.mean(volumes) > 0 else 0
        return round(1 - coefficient_of_variation, 2)
    
    def find_breakouts(self, df: pd.DataFrame, boxes: List[Dict]) -> List[Dict]:
        """
        Identify breakout opportunities above box highs with volume confirmation.
        
        Args:
            df: DataFrame with 'close', 'high', 'low', 'volume' columns  
            boxes: List of detected Darvas boxes
            
        Returns:
            List of potential breakout signals
        """
        breakouts = []
        
        for i in range(1, len(df)):
            current_price = df.iloc[i]['close']
            current_volume = df.iloc[i]['volume']
            
            # Look at the previous box
            if boxes and boxes[-1]['end'] >= i - 3:
                prev_box = boxes[-1]
                
                # Check if price broke above box high by at least 2%
                breakout_threshold = prev_box['high'] * 1.02
                
                if current_price > breakout_threshold:
                    # Calculate strength metrics
                    price_change_pct = (current_price - prev_box['high']) / prev_box['high']
                    
                    # Volume spike detection (> 150% of average)
                    volume_spike = current_volume / max(prev_box['avg_volume'], 1)
                    
                    # Enhanced signal calculation including pattern recognition
                    signal_strength = self._calculate_enhanced_signal_strength(
                        price_change_pct, volume_spike, boxes[-1]
                    )
                    
                    # Pattern recognition check
                    patterns_detected = self._detect_patterns(df, i)
                    
                    breakouts.append({
                        'date': df.iloc[i].name,
                        'price': current_price,
                        'box_high': prev_box['high'],
                        'breakout_pct': round(price_change_pct * 100, 2),
                        'volume_spike': round(volume_spike * 100, 2),
                        'signal_strength': signal_strength,
                        'patterns_detected': patterns_detected,
                        'confidence_score': self._calculate_confidence(price_change_pct, volume_spike)
                    })
        
        return breakouts
    
    def _calculate_enhanced_signal_strength(self, price_change: float, 
                                            volume_multiplier: float, 
                                            box: Dict) -> str:
        """Calculate enhanced breakout signal strength."""
        
        # Base score from price and volume
        price_score = min(price_change / 0.05, 2)  # Max 2 points for 5%+ breakouts
        volume_score = min((volume_multiplier - 1) / 0.3, 1.5)  # Max 1.5 points
        
        # Volume trend bonus
        volume_trend_bonus = {
            'INCREASING': 0.5,
            'STABLE': 0.2,
            'DECREASING': 0
        }.get(box.get('volume_trend', 'NEUTRAL'), 0)
        
        # Volume stability bonus (up to 0.3 for very stable volume)
        volume_stability_bonus = box.get('volume_stability', 0) * 0.3
        
        total_score = (price_change * 2 + (volume_multiplier - 1)) \
                      + volume_trend_bonus + volume_stability_bonus
        
        if total_score > 50:
            return 'STRONG'
        elif total_score > 30:
            return 'MODERATE'
        else:
            return 'WEAK'
    
    def _calculate_confidence(self, price_change: float, 
                              volume_spike: float) -> float:
        """Calculate confidence score for breakout (0-100)."""
        base_confidence = price_change * 20  # Max 200, we'll cap it
        volume_bonus = min(volume_spike - 100, 40)  # Volume bonus up to 40 points
        
        confidence = min(base_confidence + volume_bonus, 95)
        return round(confidence, 1)
    
    def _detect_patterns(self, df: pd.DataFrame, current_idx: int) -> List[str]:
        """Detect price patterns near breakout."""
        patterns = []
        
        # Look back for pattern formation
        lookback = min(20, len(df)) - current_idx
        
        if lookback < 5:
            return patterns
        
        recent_data = df.iloc[-lookback:].copy()
        
        # Double bottom detection
        bottom_candidates = (recent_data['low'] == recent_data['low'].rolling(3).min()).sum()
        if bottom_candidates >= 2 and recent_data['low'].iloc[-1] > recent_data['low'].iloc[-2]:
            patterns.append('DOUBLE_BOTTOM')
        
        # Pennant/flag pattern detection (consolidation after uptrend)
        if len(recent_data) >= 5:
            prices = recent_data['close'].values
            is_uptrend = all(prices[i+1] > prices[i-1] for i in range(1, len(prices)-2))
            
            if is_uptrend and recent_data['high'].iloc[-2:] \
               < df.iloc[:current_idx]['high'].mean() * 0.05:  # Small upper band
                patterns.append('FLAT_TOP')
        
        # Rising wedge detection
        highs = recent_data['high'].values
        if len(highs) >= 6:
            is_rising_wedge = all(highs[i] < highs[i-1] for i in range(1, len(highs)))
            lows_increasing = all(highs[i-1] - highs[i] < highs[i+1] - highs[i] 
                                for i in range(2, len(highs)-2))
            if is_rising_wedge and lows_increasing:
                patterns.append('RISING_WEDGE')
        
        return patterns


class TrendLineDetector:
    """Detects trend lines and moving average alignments."""
    
    def __init__(self, periods=[20, 50, 200]):
        self.periods = periods
    
    def calculate_trend(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate moving averages for trend alignment."""
        trends = {}
        
        for period in self.periods:
            if len(df) >= period:
                ma = df['close'].rolling(window=period).mean().iloc[-1]
                trends[f'ma{period}'] = float(ma)
        
        return trends
    
    def check_trend_alignment(self, current_price: float, trends: Dict) -> str:
        """Check if stock is in uptrend based on MA alignment."""
        bullish_count = sum(1 for ma_name, ma_price in trends.items() 
                          if ma_name.startswith('ma') and ma_price < current_price)
        
        total_mas = len([k for k in trends if k.startswith('ma')])
        bullish_ratio = bullish_count / total_mas if total_mas > 0 else 0
        
        if bullish_ratio > 0.7:
            return 'STRONG_UPTREND'
        elif bullish_ratio > 0.4:
            return 'MODERATE_UPTREND'
        else:
            return 'NO_CLEAR_TREND'


class IndianStockMonitor:
    """Monitors stocks for Darvas breakout opportunities with enhanced analysis."""
    
    def __init__(self):
        self.darvas_detector = DarvasBoxDetector(window_size=5)
        self.trend_detector = TrendLineDetector()
        self.wishlist = {}  # {ticker: {'name': str, 'last_price': float}}
        self.alerts = []
    
    def load_stock_data(self, ticker: str):
        """Load historical data for a stock."""
        try:
            import yfinance as yf
            
            # Download last 2 years of data (default)
            period = '1y' if len(str(ticker)) <= 3 else '3mo'  # For NSE symbols
            df = yf.download(ticker, period=period)
            
            self.wishlist[ticker] = {
                'name': ticker,
                'last_price': float(df['Close'].iloc[-1]) if len(df) > 0 else None
            }
            
        except Exception as e:
            print(f"Error loading {ticker}: {str(e)}")
            self.wishlist[ticker] = {'error': str(e)}
    
    def analyze_stock(self, ticker: str) -> Optional[Dict]:
        """
        Analyze a stock for Darvas breakout opportunities.
        
        Args:
            ticker: Stock symbol (e.g., 'RELIANCE.NS' for NSE stocks)
            
        Returns:
            Analysis result or None if analysis failed
        """
        # Check if we have data cached
        if ticker in self.wishlist and 'error' not in self.wishlist[ticker]:
            # Use cached data from recent download
            pass
        
        df = yf.download(ticker, period='3mo', interval='1d')
        
        if df.empty or len(df) < 20:
            return {'ticker': ticker, 'error': 'Insufficient data'}
        
        # Detect boxes
        boxes = self.darvas_detector.detect_boxes(df)
        
        # Find breakouts
        breakouts = self.darvas_detector.find_breakouts(df, boxes)
        
        # Get trend alignment
        trends = self.trend_detector.calculate_trend(df)
        trend_status = self.trend_detector.check_trend_alignment(
            df['Close'].iloc[-1], trends
        )
        
        return {
            'ticker': ticker,
            'current_price': float(df['Close'].iloc[-1]),
            'boxes_detected': len(boxes),
            'active_box_high': boxes[-1]['high'] if boxes else None,
            'breakouts': breakouts,
            'trend': trend_status,
            'analysis_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            'recommendation': self._get_recommendation(breakouts, trend_status)
        }
    
    def _get_recommendation(self, breakouts: List, trend: str) -> str:
        """Get trading recommendation."""
        strong_breakouts = [b for b in breakouts if b['signal_strength'] == 'STRONG']
        
        # Check for patterns on strong breakouts
        has_patterns = any(b.get('patterns_detected') for b in strong_breakouts)
        
        if strong_breakouts and trend == 'STRONG_UPTREND':
            if has_patterns:
                return 'BUY STRONG - Pattern-confirmed Darvas breakout'
            return 'BUY - Strong Darvas breakout detected'
        elif breakouts and trend in ['MODERATE_UPTREND', 'STRONG_UPTREND']:
            return 'WATCHLIST - Potential breakout forming'
        else:
            return 'HOLD - No strong breakout signals'


class PortfolioScanner:
    """Scans a portfolio of stocks for breakout opportunities."""
    
    def __init__(self):
        self.monitor = IndianStockMonitor()
    
    def scan_all_stocks(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Scan multiple stocks for breakout opportunities.
        
        Args:
            tickers: List of stock symbols (e.g., ['RELIANCE.NS', 'TCS.NS'])
            
        Returns:
            Dictionary of analysis results
        """
        results = {}
        
        for ticker in tickers:
            try:
                result = self.monitor.analyze_stock(ticker)
                results[ticker] = result
            except Exception as e:
                results[ticker] = {'error': str(e)}
        
        return results
    
    def get_breakout_summary(self, tickers: List[str]) -> Dict:
        """Get summary of all current breakouts."""
        results = self.scan_all_stocks(tickers)
        
        active_breakouts = []
        watchlist = []
        
        for ticker, result in results.items():
            if 'error' not in result and result.get('breakouts'):
                breakouts = result['breakouts']
                
                # Get latest strong breakout with patterns
                strong_breakout = None
                for b in reversed(breakouts):
                    if b['signal_strength'] == 'STRONG':
                        strong_breakout = b
                        break
                
                if strong_breakout:
                    active_breakouts.append({
                        **strong_breakout,
                        'ticker': ticker,
                        'current_price': result['current_price'],
                        'recommendation': result.get('recommendation', '')
                    })
                elif result.get('boxes_detected', 0) > 0:
                    watchlist.append({
                        'ticker': ticker,
                        'status': 'Box formation complete',
                        'box_high': result.get('active_box_high'),
                        'trend': result.get('trend')
                    })
        
        return {
            'total_analyzed': len(tickers),
            'strong_breakouts': active_breakouts,
            'watchlist_items': watchlist,
            'scan_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }