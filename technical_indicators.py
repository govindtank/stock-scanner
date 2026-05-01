"""
Technical Indicators Module for Stock Scanner
==============================================

This module provides comprehensive technical indicators for stock analysis:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- ATR (Average True Range)
- ADX (Average Directional Index)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional


class TechnicalIndicators:
    """Computes and analyzes various technical indicators."""
    
    @staticmethod
    def rsi(prices: pd.Series, window: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI).
        
        Args:
            prices: Series of closing prices
            window: RSI calculation period (default 14 days)
            
        Returns:
            Current RSI value
        """
        if len(prices) < window + 1:
            return None
            
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not rsi.empty else None
    
    @staticmethod
    def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Series of closing prices
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line EMA period (default 9)
            
        Returns:
            Dictionary with MACD, signal line, and histogram values
        """
        if len(prices) < max(slow, signal) + 1:
            return {'macd': None, 'signal': None, 'histogram': None}
        
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': float(macd_line.iloc[-1]),
            'signal': float(signal_line.iloc[-1]),
            'histogram': float(histogram.iloc[-1])
        }
    
    @staticmethod
    def bollinger_bands(prices: pd.Series, window: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Series of closing prices
            window: Number of periods for rolling mean (default 20)
            std_dev: Number of standard deviations for upper/lower bands (default 2.0)
            
        Returns:
            Dictionary with middle band, upper band, lower band, and bandwidth
        """
        if len(prices) < window + 1:
            return {'middle': None, 'upper': None, 'lower': None, 'bandwidth': None}
        
        sma = prices.rolling(window=window).mean()
        rolling_std = prices.rolling(window=window).std()
        
        upper_band = sma + (std_dev * rolling_std)
        lower_band = sma - (std_dev * rolling_std)
        
        # Bandwidth = 2 * std_dev / SMA
        bandwidth = 2 * (upper_band - lower_band) / sma
        
        return {
            'middle': float(sma.iloc[-1]),
            'upper': float(upper_band.iloc[-1]),
            'lower': float(lower_band.iloc[-1]),
            'bandwidth': float(bandwidth.iloc[-1] * 100)  # As percentage
        }
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> float:
        """
        Calculate Average True Range (ATR).
        
        Args:
            high: Series of high prices
            low: Series of low prices
            close: Series of closing prices
            window: Number of periods for averaging (default 14)
            
        Returns:
            Current ATR value
        """
        if len(close) < window + 1:
            return None
        
        true_range = pd.concat([
            high - low,
            abs(high - close.shift(1)),
            abs(low - close.shift(1))
        ], axis=1).max(axis=1)
        
        atr = true_range.rolling(window=window).mean()
        
        return float(atr.iloc[-1]) if not atr.empty else None
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> Dict[str, float]:
        """
        Calculate Average Directional Index (ADX).
        
        Args:
            high: Series of high prices
            low: Series of low prices
            close: Series of closing prices
            window: Number of periods for averaging (default 14)
            
        Returns:
            Dictionary with ADX and +DI, -DI values
        """
        if len(close) < window + 2:
            return {'adx': None, 'plus_di': None, 'minus_di': None}
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Average True Range
        atr = true_range.rolling(window=window).mean()
        
        # Directional Movement
        plus_dm = high.diff().where((high.diff() > low.diff()) & (high.diff() > 0), 0)
        minus_dm = -low.diff().where((low.diff() < high.diff()) & (-low.diff() > 0), 0)
        
        # Average Directional Movement
        avg_plus_dm = plus_dm.rolling(window=window).mean()
        avg_minus_dm = minus_dm.rolling(window=window).mean()
        
        # DI values
        tr_smooth = true_range.rolling(window=window + 1).mean().shift(1)
        plus_di = 100 * (avg_plus_dm / tr_smooth).fillna(0)
        minus_di = 100 * (avg_minus_dm / tr_smooth).fillna(0)
        
        # ADX calculation
        dx = 100 * abs(avg_plus_dm - avg_minus_dm) / ((tr_smooth + 1e-10))
        adx = dx.rolling(window=window).mean()
        
        return {
            'adx': float(adx.iloc[-1]) if not adx.empty else None,
            'plus_di': float(plus_di.iloc[-1]),
            'minus_di': float(minus_di.iloc[-1])
        }
    
    @staticmethod
    def exponential_moving_average(prices: pd.Series, span: int = 12) -> float:
        """
        Calculate Exponential Moving Average (EMA).
        
        Args:
            prices: Series of closing prices
            span: Number of periods for EMA (default 12)
            
        Returns:
            Current EMA value
        """
        if len(prices) < span + 1:
            return None
        
        ema = prices.ewm(span=span, adjust=False).mean()
        
        return float(ema.iloc[-1]) if not ema.empty else None
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                   k_period: int = 14, d_period: int = 3) -> Dict[str, float]:
        """
        Calculate Stochastic Oscillator.
        
        Args:
            high: Series of high prices
            low: Series of low prices
            close: Series of closing prices
            k_period: %K period (default 14)
            d_period: %D smoothing period (default 3)
            
        Returns:
            Dictionary with %K and %D values
        """
        if len(close) < max(k_period, d_period) + 2:
            return {'k': None, 'd': None}
        
        highest_high = high.rolling(window=k_period).max()
        lowest_low = low.rolling(window=k_period).min()
        
        stoch_k = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-10)
        stoch_d = stoch_k.rolling(window=d_period).mean()
        
        return {
            'k': float(stoch_k.iloc[-1]),
            'd': float(stoch_d.iloc[-1])
        }
    
    @staticmethod
    def momentum(prices: pd.Series, period: int = 10) -> Optional[float]:
        """
        Calculate Price Momentum.
        
        Args:
            prices: Series of closing prices
            period: Number of periods to look back (default 10)
            
        Returns:
            Percentage change over the period
        """
        if len(prices) < period + 1:
            return None
        
        momentum = prices.pct_change(period=period) * 100
        return float(momentum.iloc[-1])
    
    def calculate_all(self, df: pd.DataFrame) -> Dict[str, object]:
        """
        Calculate all technical indicators for a DataFrame.
        
        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            
        Returns:
            Dictionary containing all indicator values
        """
        return {
            'rsi': self.rsi(df['close']),
            'macd': self.macd(df['close']),
            'bollinger': self.bollinger_bands(df['close']),
            'atr': self.atr(df['high'], df['low'], df['close']),
            'adx': self.adx(df['high'], df['low'], df['close']),
            'ema_12': self.exponential_moving_average(df['close'], 12),
            'stochastic': self.stochastic(df['high'], df['low'], df['close']),
            'momentum_10d': self.momentum(df['close'], 10)
        }