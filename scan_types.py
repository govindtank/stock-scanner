"""
Stock Scanner Types Module
==========================

This module provides various scanning strategies beyond Darvas breakouts:
- Mean Reversion Scanner (RSI, Bollinger Bands, Stochastic)
- Gap Analysis Scanner (gap up/down detection)
- Momentum Scanner (price momentum analysis)
- Relative Strength Scanner (RS comparison across market)
- Volume Pattern Scanner (volume spikes and patterns)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from enum import Enum


class ScanType(Enum):
    """Enumeration of available scan types."""
    MEAN_REVERSION = "mean_reversion"
    GAP_ANALYSIS = "gap_analysis"
    MOMENTUM = "momentum"
    RELATIVE_STRENGTH = "relative_strength"
    VOLUME_PATTERN = "volume_pattern"


class ScanEngine:
    """Base class for all scanner types."""
    
    @staticmethod
    def analyze(data: pd.DataFrame) -> Dict[str, object]:
        raise NotImplementedError("Subclasses must implement analyze()")
    
    @staticmethod
    def calculate_score(results: List[Dict]) -> float:
        """Calculate overall scan score."""
        if not results:
            return 0.0
        
        scores = [r.get('score', 0) for r in results]
        return sum(scores) / len(scores)


class MeanReversionScanner(ScanEngine):
    """
    Mean Reversion Scanner based on RSI, Bollinger Bands, and Stochastic.
    
    Identifies stocks trading away from their mean (overbought/oversold conditions).
    """
    
    def __init__(self, 
                 rsi_period: int = 14,
                 rsi_overbought: float = 70,
                 rsi_oversold: float = 30,
                 bb_period: int = 20,
                 bb_std: float = 2.0):
        """
        Initialize mean reversion scanner.
        
        Args:
            rsi_period: RSI calculation period (default 14)
            rsi_overbought: Overbought threshold (default 70)
            rsi_oversold: Oversold threshold (default 30)
            bb_period: Bollinger Band period (default 20)
            bb_std: Bollinger Band standard deviations (default 2.0)
        """
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.bb_period = bb_period
        self.bb_std = bb_std
    
    def analyze(self, data: pd.DataFrame) -> List[Dict]:
        """
        Analyze data for mean reversion signals.
        
        Args:
            data: DataFrame with 'open', 'high', 'low', 'close', 'volume'
            
        Returns:
            List of signal dictionaries
        """
        from technical_indicators import TechnicalIndicators
        
        indicators = TechnicalIndicators()
        rsi_value = indicators.rsi(data['close'])
        bb = indicators.bollinger_bands(data['close'])
        
        if not all(v is not None for v in [rsi_value, bb.get('middle')]):
            return []
        
        signals = []
        
        # Check for oversold conditions (buy opportunity)
        if rsi_value and rsi_value < self.rsi_oversold:
            below_band_lower = data['close'].iloc[-1] < bb.get('lower', float('inf'))
            
            signal = {
                'type': ScanType.MEAN_REVERSION.value,
                'signal': 'OVERSOLD_BUY' if below_band_lower else 'OVERSOLD_WATCH',
                'rsi': rsi_value,
                'price': float(data['close'].iloc[-1]),
                'band_position': round(
                    (data['close'].iloc[-1] - bb.get('middle', 0)) / 
                    (bb.get('upper', 1) - bb.get('middle', 0)) * 100, 2
                ),
                'score': max((self.rsi_oversold - rsi_value) * 2, 
                            abs(data['close'].iloc[-1] - bb.get('lower', float('inf'))) / 5),
                'timestamp': str(data.index[-1]) if hasattr(data, 'index') else None
            }
            signals.append(signal)
        
        # Check for overbought conditions (sell/short opportunity)
        elif rsi_value and rsi_value > self.rsi_overbought:
            above_band_upper = data['close'].iloc[-1] > bb.get('upper', float('-inf'))
            
            signal = {
                'type': ScanType.MEAN_REVERSION.value,
                'signal': 'OVERBOUGHT_SELL' if above_band_upper else 'OVERBOUGHT_WATCH',
                'rsi': rsi_value,
                'price': float(data['close'].iloc[-1]),
                'band_position': round(
                    (data['close'].iloc[-1] - bb.get('middle', 0)) / 
                    (bb.get('upper', 1) - bb.get('middle', 0)) * 100, 2
                ),
                'score': min((rsi_value - self.rsi_overbought) * 2, 50),
                'timestamp': str(data.index[-1]) if hasattr(data, 'index') else None
            }
            signals.append(signal)
        
        return signals
    
    def is_oversold(self, data: pd.DataFrame) -> Optional[Dict]:
        """Check if stock is oversold."""
        from technical_indicators import TechnicalIndicators
        
        rsi_value = TechnicalIndicators.rsi(data['close'])
        bb = TechnicalIndicators.bollinger_bands(data['close'])
        
        if not all(v is not None for v in [rsi_value, bb.get('lower')]):
            return None
        
        if rsi_value < self.rsi_oversold and data['close'].iloc[-1] < bb.get('lower', float('inf')):
            return {
                'condition': 'OVERSOLD',
                'rsi': rsi_value,
                'price_to_lower_band_pct': round(
                    (bb.get('lower') - data['close'].iloc[-1]) / bb.get('middle', 0) * 100, 2
                )
            }
        return None
    
    def is_overbought(self, data: pd.DataFrame) -> Optional[Dict]:
        """Check if stock is overbought."""
        from technical_indicators import TechnicalIndicators
        
        rsi_value = TechnicalIndicators.rsi(data['close'])
        bb = TechnicalIndicators.bollinger_bands(data['close'])
        
        if not all(v is not None for v in [rsi_value, bb.get('upper')]):
            return None
        
        if rsi_value > self.rsi_overbought and data['close'].iloc[-1] > bb.get('upper', float('-inf')):
            return {
                'condition': 'OVERBOUGHT',
                'rsi': rsi_value,
                'price_to_upper_band_pct': round(
                    (data['close'].iloc[-1] - bb.get('upper')) / bb.get('middle', 0) * 100, 2
                )
            }
        return None


class GapAnalysisScanner(ScanEngine):
    """
    Gap Analysis Scanner for detecting gap up/down patterns.
    
    Identifies stocks with significant opening gaps that may indicate
    strong sentiment or news-driven moves.
    """
    
    def __init__(self, 
                 gap_threshold: float = 0.025,
                 min_gap_volume_multiplier: float = 1.5):
        """
        Initialize gap analysis scanner.
        
        Args:
            gap_threshold: Minimum gap size as percentage of previous close (default 2.5%)
            min_gap_volume_multiplier: Minimum volume for significant gaps (default 1.5x average)
        """
        self.gap_threshold = gap_threshold
        self.min_gap_volume_multiplier = min_gap_volume_multiplier
    
    def analyze(self, data: pd.DataFrame) -> List[Dict]:
        """
        Analyze for gap patterns.
        
        Args:
            data: DataFrame with 'open', 'high', 'low', 'close', 'volume'
            
        Returns:
            List of gap signal dictionaries
        """
        signals = []
        
        if len(data) < 2:
            return signals
        
        prev_close = data['close'].iloc[-2]
        current_open = data['open'].iloc[-1]
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].mean()
        
        # Calculate gap percentage
        gap_pct = abs(current_open - prev_close) / prev_close
        
        if gap_pct >= self.gap_threshold:
            is_gap_up = current_open > prev_close
            
            volume_ratio = current_volume / max(avg_volume, 0.1)
            significant_volume = volume_ratio >= self.min_gap_volume_multiplier
            
            gap_type = 'GAP_UP_BUY' if is_gap_up else 'GAP_DOWN_SELL'
            
            signal = {
                'type': ScanType.GAP_ANALYSIS.value,
                'signal': gap_type,
                'gap_direction': 'UP' if is_gap_up else 'DOWN',
                'gap_pct': round(gap_pct * 100, 2),
                'volume_ratio': round(volume_ratio * 100, 2),
                'price': float(data['close'].iloc[-1]),
                'timestamp': str(data.index[-1]) if hasattr(data, 'index') else None,
                'score': min(gap_pct * 50 + (volume_ratio - self.min_gap_volume_multiplier) * 10 if significant_volume else gap_pct * 30, 90)
            }
            signals.append(signal)
        
        return signals
    
    def is_significant_gap_up(self, data: pd.DataFrame) -> Optional[Dict]:
        """Check for significant upward gap."""
        prev_close = data['close'].iloc[-2]
        current_open = data['open'].iloc[-1]
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].mean()
        
        if len(data) < 2:
            return None
        
        gap_pct = (current_open - prev_close) / prev_close
        
        if gap_pct >= self.gap_threshold and current_volume >= self.min_gap_volume_multiplier * avg_volume:
            return {
                'condition': 'SIGNIFICANT_GAP_UP',
                'gap_pct': round(gap_pct * 100, 2),
                'volume_ratio': round((current_volume / max(avg_volume, 0.1)) * 100, 2)
            }
        return None


class MomentumScanner(ScanEngine):
    """
    Momentum Scanner for identifying strong trending stocks.
    
    Uses multiple momentum indicators including:
    - Price momentum over various periods
    - Rate of Change (ROC)
    - Relative Volume
    """
    
    def __init__(self, 
                 momentum_period: int = 5,
                 min_momentum_pct: float = 0.02):
        """
        Initialize momentum scanner.
        
        Args:
            momentum_period: Momentum lookback period (default 5 days)
            min_momentum_pct: Minimum momentum threshold as percentage (default 2%)
        """
        self.momentum_period = momentum_period
        self.min_momentum_pct = min_momentum_pct
    
    def analyze(self, data: pd.DataFrame) -> List[Dict]:
        """
        Analyze for momentum signals.
        
        Args:
            data: DataFrame with 'open', 'high', 'low', 'close', 'volume'
            
        Returns:
            List of momentum signal dictionaries
        """
        from technical_indicators import TechnicalIndicators
        
        indicators = TechnicalIndicators()
        momentum_5d = indicators.momentum(data['close'], self.momentum_period)
        
        signals = []
        
        if momentum_5d is not None:
            # Strong bullish momentum
            if momentum_5d > self.min_momentum_pct:
                relative_volume = data['volume'].iloc[-1] / max(data['volume'].mean(), 0.1)
                
                signal = {
                    'type': ScanType.MOMENTUM.value,
                    'signal': 'BULLISH_MOMENTUM',
                    'momentum_5d_pct': round(momentum_5d, 2),
                    'relative_volume': round(relative_volume * 100, 2),
                    'price': float(data['close'].iloc[-1]),
                    'timestamp': str(data.index[-1]) if hasattr(data, 'index') else None,
                    'score': min(momentum_5d * 50 + (relative_volume - 1) * 10, 90)
                }
                signals.append(signal)
            
            # Strong bearish momentum
            elif momentum_5d < -self.min_momentum_pct:
                relative_volume = data['volume'].iloc[-1] / max(data['volume'].mean(), 0.1)
                
                signal = {
                    'type': ScanType.MOMENTUM.value,
                    'signal': 'BEARISH_MOMENTUM',
                    'momentum_5d_pct': round(momentum_5d, 2),
                    'relative_volume': round(relative_volume * 100, 2),
                    'price': float(data['close'].iloc[-1]),
                    'timestamp': str(data.index[-1]) if hasattr(data, 'index') else None,
                    'score': min(abs(momentum_5d) * 50 + (relative_volume - 1) * 10, 90)
                }
                signals.append(signal)
        
        return signals
    
    def is_strong_momentum(self, data: pd.DataFrame) -> Optional[Dict]:
        """Check for strong bullish momentum."""
        from technical_indicators import TechnicalIndicators
        
        momentum_5d = TechnicalIndicators.momentum(data['close'], self.momentum_period)
        
        if momentum_5d is not None and momentum_5d > self.min_momentum_pct:
            return {
                'condition': 'STRONG_BULLISH_MOMENTUM',
                'momentum_5d_pct': round(momentum_5d, 2)
            }
        return None


class RelativeStrengthScanner(ScanEngine):
    """
    Relative Strength Scanner for comparing stock performance.
    
    Compares a stock's recent performance against:
    - Its own previous period performance
    - Market average (if benchmark data available)
    """
    
    def __init__(self, 
                 comparison_period: int = 5):
        """
        Initialize relative strength scanner.
        
        Args:
            comparison_period: Number of periods to compare against (default 5)
        """
        self.comparison_period = comparison_period
    
    def analyze(self, data: pd.DataFrame) -> List[Dict]:
        """
        Analyze for relative strength signals.
        
        Args:
            data: DataFrame with 'open', 'high', 'low', 'close', 'volume'
            
        Returns:
            List of relative strength signal dictionaries
        """
        from technical_indicators import TechnicalIndicators
        
        indicators = TechnicalIndicators()
        
        signals = []
        
        if len(data) <= self.comparison_period:
            return signals
        
        # Get current close and price n periods ago
        current_close = data['close'].iloc[-1]
        past_close = data['close'].iloc[-(self.comparison_period + 1)]
        
        # Calculate relative performance
        current_return = (current_close - past_close) / max(past_close, 0.01) * 100
        
        # Check for strong relative strength
        if current_return > 3:  # More than 3% better than period ago
            signals.append({
                'type': ScanType.RELATIVE_STRENGTH.value,
                'signal': 'STRONG_RELATIVE_STRENGTH',
                'relative_performance_pct': round(current_return, 2),
                'price': float(current_close),
                'timestamp': str(data.index[-1]) if hasattr(data, 'index') else None,
                'score': min(current_return * 2, 50)
            })
        
        # Check for weakness relative to period ago
        elif current_return < -3:
            signals.append({
                'type': ScanType.RELATIVE_STRENGTH.value,
                'signal': 'WEAK_RELATIVE_STRENGTH',
                'relative_performance_pct': round(current_return, 2),
                'price': float(current_close),
                'timestamp': str(data.index[-1]) if hasattr(data, 'index') else None,
                'score': min(abs(current_return) * 2, 50)
            })
        
        return signals


class VolumePatternScanner(ScanEngine):
    """
    Volume Pattern Scanner for identifying volume-based signals.
    
    Detects:
    - Volume spikes (significant above average)
    - High-volume days with price action
    - Volume trend changes
    """
    
    def __init__(self, 
                 spike_threshold: float = 2.0,
                 sustained_volume_periods: int = 3):
        """
        Initialize volume pattern scanner.
        
        Args:
            spike_threshold: Volume multiplier for spike detection (default 2.0x average)
            sustained_volume_periods: Minimum periods of high volume to qualify (default 3)
        """
        self.spike_threshold = spike_threshold
        self.sustained_volume_periods = sustained_volume_periods
    
    def analyze(self, data: pd.DataFrame) -> List[Dict]:
        """
        Analyze for volume patterns.
        
        Args:
            data: DataFrame with 'open', 'high', 'low', 'close', 'volume'
            
        Returns:
            List of volume pattern signal dictionaries
        """
        signals = []
        
        if len(data) < self.sustained_volume_periods:
            return signals
        
        avg_volume = data['volume'].mean()
        recent_high_volume_day = -1
        
        # Find most significant recent volume spike
        for i in range(len(data)):
            current_volume = data['volume'].iloc[i]
            if current_volume >= self.spike_threshold * avg_volume and current_volume > 0:
                if current_volume / max(avg_volume, 0.1) > \
                   data.iloc[-(recent_high_volume_day + 1):]['volume'].max() / max(avg_volume, 0.1):
                    recent_high_volume_day = i
        
        if recent_high_volume_day < 0 or len(data) - recent_high_volume_day <= self.sustained_volume_periods:
            return signals
        
        current_volume = data['volume'].iloc[-1]
        volume_ratio = current_volume / max(avg_volume, 0.1)
        
        # Price movement on high volume day
        spike_price_change_pct = abs(
            data['close'].iloc[-recent_high_volume_day - 1] - 
            data['close'].iloc[-recent_high_volume_day]
        ) / data['close'].iloc[-recent_high_volume_day] * 100
        
        signals.append({
            'type': ScanType.VOLUME_PATTERN.value,
            'signal': 'VOLUME_SPIKE_CONFIRMED' if volume_ratio >= self.spike_threshold else 'VOLUME_INCREASING',
            'volume_spike_pct': round((volume_ratio - 1) * 100, 2),
            'price_change_on_spike_pct': round(spike_price_change_pct, 2),
            'days_since_spike': len(data) - recent_high_volume_day - 1,
            'price': float(data['close'].iloc[-1]),
            'timestamp': str(data.index[-1]) if hasattr(data, 'index') else None,
            'score': min(volume_ratio * 5, 30) + spike_price_change_pct * 0.5
        })
        
        return signals


def run_scanner(scan_type: ScanType, data: pd.DataFrame, **kwargs) -> List[Dict]:
    """
    Run the appropriate scanner based on type.
    
    Args:
        scan_type: Type of scanner to use (ScanType enum)
        data: DataFrame with stock price/volume data
        **kwargs: Additional arguments passed to scanner constructor
        
    Returns:
        List of signal dictionaries
    """
    scanners = {
        ScanType.MEAN_REVERSION: MeanReversionScanner,
        ScanType.GAP_ANALYSIS: GapAnalysisScanner,
        ScanType.MOMENTUM: MomentumScanner,
        ScanType.RELATIVE_STRENGTH: RelativeStrengthScanner,
        ScanType.VOLUME_PATTERN: VolumePatternScanner
    }
    
    scanner_class = scanners.get(scan_type)
    if not scanner_class:
        raise ValueError(f"Unknown scan type: {scan_type}")
    
    # Create scanner instance with provided kwargs or defaults
    scanner_kwargs = {'comparison_period': 5} if scan_type == ScanType.RELATIVE_STRENGTH else {}
    
    try:
        scanner = scanner_class(**kwargs)
    except TypeError:
        scanner = scanner_class()
    
    return scanner.analyze(data)


def get_all_signals(
    data: pd.DataFrame,
    scanners: Optional[List[ScanType]] = None
) -> List[Dict]:
    """
    Run multiple scanners and aggregate signals.
    
    Args:
        data: DataFrame with stock price/volume data
        scanners: List of scan types to run (default: all available)
        
    Returns:
        Combined list of all signals
    """
    if scanners is None:
        scanners = [ScanType(s) for s in ScanType]
    
    all_signals = []
    for scan_type in scanners:
        try:
            signals = run_scanner(scan_type, data)
            all_signals.extend(signals)
        except Exception as e:
            print(f"Error running {scan_type.value} scanner: {e}")
    
    return all_signals


if __name__ == '__main__':
    # Example usage
    import pandas as pd
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=30, freq='D')
    close_prices = np.random.randn(30).cumsum() + 100
    high_prices = close_prices + np.random.uniform(0.5, 2, 30)
    low_prices = close_prices - np.random.uniform(0.5, 2, 30)
    volumes = np.random.randint(1000000, 5000000, 30)
    
    data = pd.DataFrame({
        'open': close_prices * 1.005,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    }, index=dates)
    
    print("Sample Data Created")
    print(f"Data shape: {data.shape}")
    print(f"\nFirst few rows:\n{data.head()}")
    
    # Run mean reversion scan
    mr = MeanReversionScanner()
    mr_signals = mr.analyze(data)
    print(f"\nMean Reversion Signals ({len(mr_signals)}): {mr_signals}")
    
    # Run gap analysis
    ga = GapAnalysisScanner()
    ga_signals = ga.analyze(data)
    print(f"Gap Analysis Signals ({len(ga_signals)}): {ga_signals}")
    
    # Run all scans
    scanners = [
        ScanType.MEAN_REVERSION,
        ScanType.GAP_ANALYSIS,
        ScanType.MOMENTUM,
        ScanType.RELATIVE_STRENGTH,
        ScanType.VOLUME_PATTERN
    ]
    
    all_signals = get_all_signals(data, scanners)
    print(f"\nAll Signals ({len(all_signals)}): {all_signals}")