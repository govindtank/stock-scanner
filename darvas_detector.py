"""
Darvas Box Breakout Detection Module for Indian Stocks
=======================================================

This module implements the Darvas box method for identifying breakout opportunities
in Indian stock market using yfinance (free, no API key required).

The Darvas theory is based on:
1. Price consolidation in "boxes" (ranges)
2. Breakouts above box highs with strong volume
3. Quick profit-taking after breakouts
4. Trend following with moving averages
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import datetime


class DarvasBoxDetector:
    """Implements Darvas Box Method for breakout detection."""
    
    def __init__(self, window_size=5, min_box_volatility=0.02):
        """
        Initialize the Darvas box detector.
        
        Args:
            window_size: Number of days to look back for box formation (default 5)
            min_box_volatility: Minimum volatility required within a box (%)
        """
        self.window_size = window_size
        self.min_box_volatility = min_box_volatility
    
    def detect_boxes(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """
        Detect Darvas boxes in price data.
        
        Args:
            df: DataFrame with 'close' and 'volume' columns
            
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
                
                boxes.append({
                    'start': i - self.window_size + 1,
                    'end': i,
                    'high': recent_high,
                    'low': recent_low,
                    'close': current_price,
                    'avg_volume': avg_volume,
                    'range': recent_high - recent_low
                })
        
        return boxes
    
    def find_breakouts(self, df: pd.DataFrame, boxes: List[Dict]) -> List[Dict]:
        """
        Identify breakout opportunities above box highs.
        
        Args:
            df: DataFrame with 'close' and 'volume' columns  
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
                    
                    breakouts.append({
                        'date': df.iloc[i].name,
                        'price': current_price,
                        'box_high': prev_box['high'],
                        'breakout_pct': round(price_change_pct * 100, 2),
                        'volume_spike': round(volume_spike * 100, 2),
                        'signal_strength': self._calculate_signal_strength(
                            price_change_pct, volume_spike
                        )
                    })
        
        return breakouts
    
    def _calculate_signal_strength(self, price_change: float, volume_multiplier: float) -> str:
        """Calculate breakout signal strength."""
        score = (price_change * 2 + (volume_multiplier - 1) / 3) * 10
        
        if score > 50:
            return 'STRONG'
        elif score > 30:
            return 'MODERATE'
        else:
            return 'WEAK'


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
    """Monitors Indian stocks for Darvas breakout opportunities."""
    
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
        if ticker not in self.wishlist:
            self.load_stock_data(ticker)
            
            if ticker not in self.wishlist or self.wishlist[ticker].get('error'):
                return None
        
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
        
        if strong_breakouts and trend == 'STRONG_UPTREND':
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
                
                # Get latest strong breakout
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
