"""
Technical Indicators Module for Stock Scanner
Implements advanced indicators beyond basic SMA/RSI:
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Stochastic Oscillator
- Ichimoku Cloud (simplified)
- ADX (Average Directional Index)
- Volume Weighted Average Price (VWAP)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List


class TechnicalIndicators:
    """
    Collection of technical indicators for stock analysis.
    
    All methods support both Pandas Series and NumPy arrays.
    """
    
    @staticmethod
    def macd(
        close_prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Moving Average Convergence Divergence (MACD).
        
        Args:
            close_prices: Close price series
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line period (default: 9)
            
        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        if len(close_prices) < max(fast_period, slow_period, signal_period):
            return pd.Series(index=close_prices.index), pd.Series(index=close_prices.index), pd.Series(index=close_prices.index)
        
        # Calculate EMAs
        ema_fast = close_prices.ewm(com=fast_period - 1, adjust=False).mean()
        ema_slow = close_prices.ewm(com=slow_period - 1, adjust=False).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line (EMA of MACD)
        signal_line = macd_line.ewm(com=signal_period - 1, adjust=False).mean()
        
        # Histogram
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(
        close_prices: pd.Series,
        window: int = 20,
        num_std: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands (upper, middle, lower).
        
        Args:
            close_prices: Close price series
            window: Rolling window for SMA (default: 20)
            num_std: Number of standard deviations (default: 2.0)
            
        Returns:
            Tuple of (Upper Band, Middle Band/SMA, Lower Band)
        """
        if len(close_prices) < window:
            upper = pd.Series(index=close_prices.index)
            middle = close_prices.ewm(com=window - 1, adjust=False).mean()
            lower = pd.Series(index=close_prices.index)
            return upper, middle, lower
        
        # Middle band (SMA)
        middle = close_prices.rolling(window=window).mean()
        
        # Rolling standard deviation
        rolling_std = close_prices.rolling(window=window).std()
        
        # Upper and Lower bands
        upper = middle + (num_std * rolling_std)
        lower = middle - (num_std * rolling_std)
        
        return upper, middle, lower
    
    @staticmethod
    def stochastic(
        high_prices: pd.Series,
        low_prices: pd.Series,
        close_prices: pd.Series,
        k_period: int = 14,
        d_period: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator.
        
        Args:
            high_prices: High price series
            low_prices: Low price series
            close_prices: Close price series
            k_period: %K period (default: 14)
            d_period: %D smoothing period (default: 3)
            
        Returns:
            Tuple of (%K, %D)
        """
        if len(close_prices) < k_period:
            return pd.Series(index=close_prices.index), pd.Series(index=close_prices.index)
        
        # True range for denominator
        low_range = low_prices.rolling(window=k_period).min()
        high_range = high_prices.rolling(window=k_period).max()
        
        # %K calculation
        rk = 100 * (close_prices - low_range) / (high_range - low_range + 1e-10)
        
        # Apply smoothing to get %K
        k_smoothed = rk.ewm(com=k_period - 1, adjust=False).mean()
        
        # %D is moving average of %K
        d_line = k_smoothed.rolling(window=d_period).mean()
        
        return k_smoothed, d_line
    
    @staticmethod
    def rsi(
        close_prices: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Relative Strength Index (enhanced version with zones).
        
        Args:
            close_prices: Close price series
            period: RSI period (default: 14)
            
        Returns:
            RSI values (0-100 scale)
        """
        if len(close_prices) < period + 1:
            return pd.Series(index=close_prices.index, dtype=float)
        
        # Calculate price changes
        delta = close_prices.diff()
        
        # Separate gains and losses
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        # Rolling average of gains and losses
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Avoid division by zero
        rs_series = avg_gain / (avg_loss + 1e-10)
        
        # RSI calculation
        rsi = 100 - (100 / (1 + rs_series))
        
        return rsi
    
    @staticmethod
    def atr(
        high_prices: pd.Series,
        low_prices: pd.Series,
        close_prices: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range (volatility measure).
        
        Args:
            high_prices: High price series
            low_prices: Low price series  
            close_prices: Close price series
            period: ATR period (default: 14)
            
        Returns:
            ATR values
        """
        if len(close_prices) < period + 1:
            return pd.Series(index=close_prices.index, dtype=float)
        
        # True Range: max of three values
        tr1 = high_prices - low_prices
        tr2 = abs(high_prices - close_prices.shift(1))
        tr3 = abs(low_prices - close_prices.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Smoothed ATR using EWMA for better responsiveness
        atr = true_range.ewm(com=period - 1, adjust=False).mean()
        
        return atr
    
    @staticmethod
    def vwap(
        high_prices: pd.Series,
        low_prices: pd.Series,
        close_prices: pd.Series,
        volume: pd.Series
    ) -> pd.Series:
        """
        Calculate Volume Weighted Average Price.
        
        Args:
            high_prices: High price series
            low_prices: Low price series
            close_prices: Close price series
            volume: Volume series
            
        Returns:
            VWAP values
        """
        if len(close_prices) != len(volume):
            raise ValueError("High/Low/Close and Volume must have same length")
        
        # Typical price
        typical_price = (high_prices + low_prices + close_prices) / 3
        
        # Price * volume
        tpv = typical_price * volume
        
        # Cumulative sum
        cum_tpv = tpv.cumsum()
        cum_vol = volume.cumsum()
        
        # VWAP
        vwap = cum_tpv / (cum_vol + 1e-10)
        
        return vwap
    
    @staticmethod
    def adx(
        high_prices: pd.Series,
        low_prices: pd.Series,
        close_prices: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average Directional Index (trend strength).
        
        Args:
            high_prices: High price series
            low_prices: Low price series
            close_prices: Close price series
            period: ADX period (default: 14)
            
        Returns:
            ADX values (0-100, >25 indicates strong trend)
        """
        if len(close_prices) < period + 1:
            return pd.Series(index=close_prices.index, dtype=float)
        
        # Directional movement
        plus_dm = np.zeros(len(close_prices))
        minus_dm = np.zeros(len(close_prices))
        
        for i in range(1, len(close_prices)):
            up_move = close_prices.iloc[i] - close_prices.iloc[i - 1]
            down_move = close_prices.iloc[i - 1] - close_prices.iloc[i]
            
            if up_move > 0 and up_move > abs(down_move):
                plus_dm[i] = high_prices.iloc[i] - low_prices.iloc[i]
            elif down_move > 0 and down_move > abs(up_move):
                minus_dm[i] = high_prices.iloc[i] - low_prices.iloc[i]
        
        # Smoothed +DI and -DI
        plus_di = 100 * pd.Series(plus_dm).ewm(com=period - 1, adjust=False).mean() / \
                   (pd.Series(abs(minus_dm)).ewm(com=period - 1, adjust=False).mean() + 1e-10)
        
        minus_di = 100 * pd.Series(minus_dm).ewm(com=period - 1, adjust=False).mean() / \
                   (pd.Series(abs(plus_dm)).ewm(com=period - 1, adjust=False).mean() + 1e-10)
        
        # DX (Directional Index)
        dx = 100 * pd.abs(plus_di - minus_di) / (pd.abs(plus_di) + pd.abs(minus_di) + 1e-10)
        
        # ADX (smoothed DX)
        adx = dx.ewm(com=period - 1, adjust=False).mean()
        
        return adx
    
    @staticmethod
    def williams_r(
        high_prices: pd.Series,
        low_prices: pd.Series,
        close_prices: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Williams %R (momentum oscillator).
        
        Args:
            high_prices: High price series
            low_prices: Low price series
            close_prices: Close price series
            period: %R period (default: 14)
            
        Returns:
            Williams %R values (-100 to 0, < -80 indicates overbought)
        """
        if len(close_prices) < period:
            return pd.Series(index=close_prices.index, dtype=float)
        
        # Highest high and lowest low over period
        highest_high = high_prices.rolling(window=period).max()
        lowest_low = low_prices.rolling(window=period).min()
        
        # Williams %R
        wr = -100 * (highest_high - close_prices) / (highest_high - lowest_low + 1e-10)
        
        return wr
    
    @staticmethod
    def commodity_channel_index(
        close_prices: pd.Series,
        period: int = 20
    ) -> pd.Series:
        """
        Calculate Commodity Channel Index (CCI).
        
        Args:
            close_prices: Close price series
            period: CCI period (default: 20)
            
        Returns:
            CCI values (cyclically interpreted momentum oscillator)
        """
        if len(close_prices) < period + 1:
            return pd.Series(index=close_prices.index, dtype=float)
        
        # Typical price
        typical_price = (close_prices + close_prices.shift(1) + close_prices.shift(2)) / 3
        
        # SMA of typical price
        sma = typical_price.rolling(window=period).mean()
        
        # Mean deviation
        md = pd.Series(index=typical_price.index, dtype=float)
        for i in range(period, len(typical_price)):
            window = typical_price.iloc[i-period:i+1]
            md_val = (np.abs(typical_price.iloc[i] - window).sum()) / period
            md.iloc[i] = md_val
        
        # CCI
        cci = 0.015 * (typical_price - sma) / (md + 1e-10)
        
        return cci
    
    @classmethod
    def calculate_all(cls, close: pd.Series, high: pd.Series, low: pd.Series, volume: pd.Series) -> Dict[str, any]:
        """
        Calculate all available indicators at once for efficiency.
        
        Args:
            close: Close price series
            high: High price series
            low: Low price series
            volume: Volume series
            
        Returns:
            Dictionary with all calculated indicators
        """
        result = {
            'rsi': cls.rsi(close),
            'macd_line': None,
            'macd_signal': None, 
            'macd_histogram': None,
            'bollinger_upper': None,
            'bollinger_middle': None,
            'bollinger_lower': None,
            'stoch_k': None,
            'stoch_d': None,
            'atr': cls.atr(high, low, close),
            'vwap': cls.vwap(high, low, close, volume),
            'adx': cls.adx(high, low, close),
            'williams_r': cls.williams_r(high, low, close),
            'cci': cls.commodity_channel_index(close)
        }
        
        # Calculate MACD only if we have enough data
        if len(close) >= max(12, 26, 9):
            result['macd_line'], result['macd_signal'], result['macd_histogram'] = \
                cls.macd(close, fast_period=12, slow_period=26, signal_period=9)
        
        # Calculate Bollinger Bands only if we have enough data
        if len(close) >= 20:
            result['bollinger_upper'], result['bollinger_middle'], result['bollinger_lower'] = \
                cls.bollinger_bands(close, window=20, num_std=2.0)
        
        # Calculate Stochastic only if we have enough data
        if len(close) >= 14:
            result['stoch_k'], result['stoch_d'] = \
                cls.stochastic(high, low, close, k_period=14, d_period=3)
        
        return result


def add_indicator_to_dataframe(df: pd.DataFrame, indicator_name: str) -> pd.DataFrame:
    """
    Convenience function to add calculated indicators to a DataFrame.
    
    Args:
        df: Input DataFrame with OHLCV data
        indicator_name: Name of indicator (e.g., 'rsi', 'macd_line')
        
    Returns:
        DataFrame with new indicator column(s)
    """
    indicators = TechnicalIndicators()
    
    if indicator_name in ['rsi']:
        df['rsi'] = indicators.rsi(df['Close'])
    elif indicator_name in ['macd_line', 'macd_signal', 'macd_histogram']:
        macd_line, signal, hist = indicators.macd(df['Close'])
        df['macd_line'] = macd_line.values
        df['macd_signal'] = signal.values
        df['macd_histogram'] = hist.values
    elif indicator_name in ['bollinger_upper', 'bollinger_middle', 'bollinger_lower']:
        upper, middle, lower = indicators.bollinger_bands(df['Close'])
        df['bollinger_upper'] = upper.values
        df['bollinger_middle'] = middle.values
        df['bollinger_lower'] = lower.values
    elif indicator_name in ['stoch_k', 'stoch_d']:
        stoch_k, stoch_d = indicators.stochastic(df['High'], df['Low'], df['Close'])
        df['stoch_k'] = stoch_k.values
        df['stoch_d'] = stoch_d.values
    
    return df
