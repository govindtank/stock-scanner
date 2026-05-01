"""
Enhanced Scan Types for Stock Scanner
Implements advanced detection strategies beyond Darvas Box:
- Momentum Filter Scans
- Volatility Breakout Detection
- Trend Following Strategies
- Pattern Recognition (Head & Shoulders, Double Top/Bottom)
- Volume Spike Detection
- Gap Analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum


class ScanType(Enum):
    """Enumeration of available scan types."""
    MOMENTUM_FILTER = "momentum_filter"
    VOLATILITY_BREAKOUT = "volatility_breakout"
    TREND_FOLLOWING = "trend_following"
    PATTERN_RECOGNITION = "pattern_recognition"
    VOLUME_SPIKE = "volume_spike"
    GAP_ANALYSIS = "gap_analysis"
    COMBINED_STRATEGY = "combined_strategy"


class EnhancedScans:
    """
    Advanced scanning strategies combining multiple indicators.
    
    Each scan type represents a different trading strategy or market condition.
    """
    
    @staticmethod
    def momentum_filter_scan(
        df: pd.DataFrame,
        rsi_period: int = 14,
        rsi_buy: float = 30,
        rsi_sell: float = 70,
        macd_signal: str = 'macd_line',
        price_threshold_pct: float = 0.05
    ) -> Dict[str, any]:
        """
        Momentum-based scan combining RSI and MACD signals with trend filter.
        
        Strategy:
        - Buy when RSI < 30 (oversold) AND MACD histogram turning positive
        - Hold until RSI > 70 (overbought) OR trend breaks
        
        Args:
            df: DataFrame with OHLCV and technical indicators
            rsi_period: RSI calculation period
            rsi_buy: RSI threshold for buy signal
            rsi_sell: RSI threshold for sell signal  
            macd_signal: Column name for MACD line
            price_threshold_pct: Minimum move percentage to hold position
            
        Returns:
            Dict with scan results and signals
        """
        if 'Close' not in df.columns:
            raise ValueError("DataFrame must have 'Close' column")
            
        if macd_signal is None or macd_signal not in df.columns:
            # Calculate MACD if not present
            from technical_indicators import TechnicalIndicators
            macd_line, signal, histogram = TechnicalIndicators.macd(
                pd.Series(df['Close'])
            )
            df[macd_signal] = macd_line.values
            df['macd_signal'] = signal.values
            df['macd_histogram'] = histogram.values
        
        # Calculate RSI if not present
        from technical_indicators import TechnicalIndicators
        rsi_series = TechnicalIndicators.rsi(pd.Series(df['Close']), rsi_period)
        df['rsi'] = rsi_series.values
        
        signals = []
        positions = ['HOLD', 'HOLD', 'HOLD']  # Initialize
        
        for i in range(2, len(df)):  # Skip first two rows due to rolling calculations
            rsi = df['rsi'].iloc[i]
            macd_hist = df.get('macd_histogram', pd.Series()).iloc[i]
            prev_macd_hist = df.get('macd_histogram', pd.Series()).iloc[i-1] if i > 2 else 0
            
            # Trend filter: require uptrend (price above VWAP)
            trend_up = df['Close'].iloc[i] > df.get('vwap', pd.Series()).iloc[i] if 'vwap' in df.columns else True
            
            if rsi < rsi_buy and macd_hist > prev_macd_hist and trend_up:
                positions.append('BUY')
                signals.append('Oversold with momentum reversal')
            elif rsi > rsi_sell:
                positions.append('SELL')
                signals.append('Overbought - taking profits')
            else:
                positions.append('HOLD')
                signals.append('Current position active' if positions[-2] in ['BUY', 'BUY'] else None)
        
        # Create results DataFrame
        results = pd.DataFrame({
            'position': positions,
            'signal': signals,
            'rsi': df['rsi'].tolist()[-len(positions):],
            'trend': [True if i < len(df) and (df.get('vwap', pd.Series()).isna() or df['Close'].iloc[i] > df.get('vwap', pd.Series()).iloc[i]) else False 
                     for i in range(len(positions))]
        })
        
        return {
            'scan_type': ScanType.MOMENTUM_FILTER.value,
            'results': results,
            'buy_signals': results[results['position'] == 'BUY'],
            'sell_signals': results[results['position'] == 'SELL'],
            'hold_signals': results[results['position'] == 'HOLD']
        }
    
    @staticmethod
    def volatility_breakout_scan(
        df: pd.DataFrame,
        bb_period: int = 20,
        bb_std: float = 2.0,
        volume_threshold: float = 1.5,
        min_price_range: float = 0.02
    ) -> Dict[str, any]:
        """
        Volatility breakout detection using Bollinger Bands and volume.
        
        Strategy:
        - Detect when price breaks out of Bollinger Bands with above-average volume
        - Measure breakouts relative to recent volatility
        
        Args:
            df: DataFrame with OHLCV and Bollinger Bands
            bb_period: Bollinger Band period
            bb_std: Number of standard deviations for bands
            volume_threshold: Volume multiplier for breakout confirmation
            min_price_range: Minimum price movement for valid breakout
            
        Returns:
            Dict with scan results and breakout signals
        """
        if 'Close' not in df.columns or 'High' not in df.columns or 'Low' not in df.columns:
            raise ValueError("DataFrame must have OHLC columns")
            
        from technical_indicators import TechnicalIndicators
        upper, middle, lower = TechnicalIndicators.bollinger_bands(
            pd.Series(df['Close']), bb_period, bb_std
        )
        
        df['bb_upper'] = upper.values
        df['bb_lower'] = lower.values
        
        # Calculate average volume for breakout detection
        avg_volume = df['Volume'].rolling(window=20).mean()
        df['avg_vol_20d'] = avg_volume.values
        
        # Price range for breakout calculation
        price_range = df['High'] - df['Low']
        df['price_range'] = price_range.values
        
        signals = []
        positions = ['HOLD', 'HOLD', 'HOLD']
        
        breakouts = pd.DataFrame(columns=['date', 'type', 'strength'])
        
        for i in range(2, len(df)):
            current_price = df['Close'].iloc[i]
            high = df['High'].iloc[i]
            low = df['Low'].iloc[i]
            volume = df['Volume'].iloc[i]
            
            upper_band = df['bb_upper'].iloc[i]
            lower_band = df['bb_lower'].iloc[i]
            avg_vol = df['avg_vol_20d'].iloc[i]
            
            # Calculate breakout strength
            if current_price > upper_band and volume >= volume_threshold * avg_vol:
                distance_to_band = (current_price - upper_band) / upper_band
                breakouts = pd.concat([breakouts, pd.DataFrame({
                    'date': df.index.iloc[i],
                    'type': 'BULLISH',
                    'strength': distance_to_band
                })])
                signals.append('VOLATILITY_BREAKOUT_BULLISH')
                positions.append('BUY')
            elif current_price < lower_band and volume >= volume_threshold * avg_vol:
                distance_to_band = (lower_band - current_price) / lower_band
                breakouts = pd.concat([breakouts, pd.DataFrame({
                    'date': df.index.iloc[i],
                    'type': 'BEARISH', 
                    'strength': distance_to_band
                })])
                signals.append('VOLATILITY_BREAKOUT_BEARISH')
                positions.append('SELL')
            else:
                signals.append('NO_BREAKOUT')
                positions.append('HOLD')
        
        # Add breakouts to results
        results = pd.DataFrame({
            'date': df.index.tolist()[-len(positions):],
            'position': positions,
            'signal': signals,
            'close': df['Close'].tolist()[-len(positions):],
            'bb_upper': df['bb_upper'].tolist()[-len(positions):],
            'bb_lower': df['bb_lower'].tolist()[-len(positions):]
        })
        
        if len(breakouts) > 0:
            results = pd.concat([results, breakouts])
        
        return {
            'scan_type': ScanType.VOLATILITY_BREAKOUT.value,
            'results': results,
            'breakouts': breakouts,
            'last_signal': signals[-1] if signals else None
        }
    
    @staticmethod
    def trend_following_scan(
        df: pd.DataFrame,
        sma_fast: int = 9,
        sma_slow: int = 21,
        adx_period: int = 14,
        adx_threshold: float = 25.0,
        atr_stop_pct: float = 2.0
    ) -> Dict[str, any]:
        """
        Trend following strategy using moving average crossovers and ADX filter.
        
        Strategy:
        - Long when fast SMA crosses above slow SMA with ADX > threshold
        - Short when fast SMA crosses below slow SMA  
        - Stop losses based on ATR
        
        Args:
            df: DataFrame with OHLCV, SMAs, and ATR
            sma_fast: Fast moving average period
            sma_slow: Slow moving average period
            adx_period: ADX calculation period
            adx_threshold: Minimum ADX for trend confirmation
            atr_stop_pct: Stop loss as % of ATR
            
        Returns:
            Dict with scan results and trend signals
        """
        if 'Close' not in df.columns or 'Volume' not in df.columns:
            raise ValueError("DataFrame must have Close and Volume columns")
            
        from technical_indicators import TechnicalIndicators
        
        # Calculate SMAs
        sma_fast = pd.Series(df['Close']).rolling(window=sma_fast).mean()
        sma_slow = pd.Series(df['Close']).rolling(window=sma_slow).mean()
        
        # Calculate ADX
        adx_series = TechnicalIndicators.adx(
            pd.Series(df['High']),
            pd.Series(df['Low']),
            pd.Series(df['Close']),
            adx_period
        )
        
        # Calculate ATR
        atr_series = TechnicalIndicators.atr(
            pd.Series(df['High']),
            pd.Series(df['Low']),
            pd.Series(df['Close']),
            adx_period
        )
        
        df['sma_fast'] = sma_fast.values
        df['sma_slow'] = sma_slow.values
        df['adx'] = adx_series.values
        df['atr'] = atr_series.values
        
        signals = []
        positions = ['HOLD', 'HOLD', 'HOLD']
        
        buy_points = []
        sell_points = []
        
        for i in range(sma_slow, len(df)):  # Skip SMA calculation lag
            sma_fast_val = df['sma_fast'].iloc[i]
            sma_slow_val = df['sma_slow'].iloc[i]
            adx_val = df['adx'].iloc[i]
            atr_val = df['atr'].iloc[i]
            
            if pd.isna(sma_fast_val) or pd.isna(sma_slow_val):
                continue
                
            # Calculate stop loss
            stop_loss_pct = 2.0 * atr_val / df['Close'].iloc[i]
            
            if adx_val > adx_threshold:
                if sma_fast_val < sma_slow_val and positions[-1] != 'SHORT':
                    positions.append('SELL')
                    signals.append('Short entry - Fast SMA crosses below Slow SMA')
                elif sma_fast_val > sma_slow_val and positions[-1] != 'LONG':
                    positions.append('BUY')
                    signals.append(f'Long entry with trend confirmation. Stop: {stop_loss_pct:.2%}')
                    buy_points.append({
                        'date': df.index.iloc[i],
                        'price': df['Close'].iloc[i],
                        'stop_loss': stop_loss_pct
                    })
                else:
                    positions.append('HOLD')
                    signals.append('Trend following - maintain position' if positions[-2] in ['BUY', 'SELL'] else None)
            else:
                positions.append('NO_TRADE')
                signals.append('No trend - ADX below threshold' if positions[-2] in ['BUY', 'SELL'] else None)
        
        # Create results DataFrame
        results_data = pd.DataFrame({
            'date': df.index.tolist()[-len(positions):],
            'position': positions,
            'signal': signals,
            'close': df['Close'].tolist()[-len(positions):],
            'sma_fast': df['sma_fast'].tolist()[-len(positions):],
            'sma_slow': df['sma_slow'].tolist()[-len(positions):],
            'adx': df['adx'].tolist()[-len(positions):]
        })
        
        return {
            'scan_type': ScanType.TREND_FOLLOWING.value,
            'results': results_data,
            'buy_points': pd.DataFrame(buy_points) if buy_points else pd.DataFrame(columns=['date', 'price', 'stop_loss']),
            'sell_points': pd.DataFrame(sell_points) if sell_points else pd.DataFrame(columns=[]),
            'last_signal': signals[-1] if signals else None,
            'adx_threshold': adx_threshold
        }
    
    @staticmethod
    def pattern_recognition_scan(
        df: pd.DataFrame,
        pattern_type: str = 'double_top',
        pattern_confidence: float = 0.7
    ) -> Dict[str, any]:
        """
        Pattern recognition for classic chart patterns.
        
        Supported patterns:
        - Double Top (M-pattern)
        - Double Bottom (W-pattern)  
        - Head and Shoulders (simplified)
        - Ascending Triangle
        
        Args:
            df: DataFrame with OHLCV
            pattern_type: Type of pattern to detect
            pattern_confidence: Minimum confidence threshold for pattern
            
        Returns:
            Dict with detected patterns and signals
        """
        
        def find_double_top(df: pd.DataFrame, min_pattern_pct: float = 0.7) -> List[Dict]:
            """Detect double top patterns."""
            patterns = []
            
            if len(df) < 30:
                return patterns
            
            # Find local peaks (tops)
            for i in range(15, len(df) - 15):
                window = df['High'].iloc[i-20:i+20]
                
                # Check if this point is a local maximum
                is_peak = all(window.iloc[-20:] <= df['High'].iloc[i]) and \
                          all(window.iloc[:-20] <= df['High'].iloc[i])
                
                if not is_peak:
                    continue
                
                peak1_price = df['High'].iloc[i]
                peak_date = df.index[i]
                
                # Look for second top
                for j in range(i + 1, min(len(df), i + 30)):
                    window2 = df['High'].iloc[i:j+1]
                    
                    is_second_peak = all(window2.iloc[:-1] <= df['High'].iloc[j])
                    
                    if is_second_peak:
                        # Check for breakdown below middle point
                        low_range = df['Low'].iloc[(i + j) // 2]
                        current_price = df['Close'].iloc[j]
                        
                        # Pattern confirmed if price breaks below the lows between peaks
                        if current_price < (df['High'].iloc[i] + df['High'].iloc[j]) / 2:
                            patterns.append({
                                'pattern': 'DOUBLE_TOP',
                                'peak1_date': peak_date,
                                'peak1_price': peak1_price,
                                'peak2_price': df['High'].iloc[j],
                                'breakdown_price': current_price,
                                'confidence': min_pattern_pct,
                                'signal_type': 'SELL'
                            })
                            break
            
            return patterns
        
        def find_double_bottom(df: pd.DataFrame, min_pattern_pct: float = 0.7) -> List[Dict]:
            """Detect double bottom patterns."""
            patterns = []
            
            if len(df) < 30:
                return patterns
            
            # Find local troughs (bottoms)
            for i in range(15, len(df) - 15):
                window = df['Low'].iloc[i-20:i+20]
                
                is_trough = all(window.iloc[-20:] >= df['Low'].iloc[i]) and \
                          all(window.iloc[:-20] >= df['Low'].iloc[i])
                
                if not is_trough:
                    continue
                
                trough1_price = df['Low'].iloc[i]
                trough_date = df.index[i]
                
                # Look for second bottom
                for j in range(i + 1, min(len(df), i + 30)):
                    window2 = df['Low'].iloc[i:j+1]
                    
                    is_second_trough = all(window2.iloc[:-1] >= df['Low'].iloc[j])
                    
                    if is_second_trough:
                        high_range = df['High'].iloc[(i + j) // 2]
                        current_price = df['Close'].iloc[j]
                        
                        if current_price > (df['Low'].iloc[i] + df['Low'].iloc[j]) / 2:
                            patterns.append({
                                'pattern': 'DOUBLE_BOTTOM',
                                'trough1_date': trough_date,
                                'trough1_price': trough1_price,
                                'trough2_price': df['Low'].iloc[j],
                                'breakout_price': current_price,
                                'confidence': min_pattern_pct,
                                'signal_type': 'BUY'
                            })
                            break
            
            return patterns
        
        def find_head_and_shoulders(df: pd.DataFrame) -> List[Dict]:
            """Simplified head and shoulders detection."""
            patterns = []
            
            if len(df) < 40:
                return patterns
            
            # Look for three peaks with middle being highest
            for i in range(20, len(df) - 20):
                h1 = df['High'].iloc[i-5:i]
                h2 = df['High'].iloc[i:i+5]
                
                if len(h1) < 3 or len(h2) < 3:
                    continue
                
                left_peak_price = max(h1.iloc[1:-1])
                right_peak_price = max(h2.iloc[1:-1])
                head_price = max(h2)
                
                # Check pattern shape
                if left_peak_price < head_price > right_peak_price:
                    # Find neckline (roughly average of lows around shoulders)
                    low_shoulder1 = df['Low'].iloc[i-4]
                    low_shoulder2 = df['Low'].iloc[i+4]
                    neckline = (low_shoulder1 + low_shoulder2) / 2
                    
                    if current_close := df['Close'].iloc[-1]:
                        # Check for breakdown
                        if current_close < neckline * 0.98:  # 2% tolerance
                            patterns.append({
                                'pattern': 'HEAD_AND_SHOULDERS',
                                'head_price': head_price,
                                'shoulder1_price': left_peak_price,
                                'shoulder2_price': right_peak_price,
                                'neckline': neckline,
                                'breakdown_price': current_close,
                                'signal_type': 'SELL'
                            })
            
            return patterns
        
        # Detect patterns based on type
        if pattern_type == 'double_top':
            patterns = find_double_top(df)
        elif pattern_type == 'double_bottom':
            patterns = find_double_bottom(df)
        elif pattern_type == 'head_shoulders':
            patterns = find_head_and_shoulders(df)
        else:
            return {
                'scan_type': ScanType.PATTERN_RECOGNITION.value,
                'pattern_type': pattern_type,
                'patterns': [],
                'signals': []
            }
        
        # Convert to DataFrame with proper datetime index if available
        results = pd.DataFrame(patterns) if patterns else pd.DataFrame(columns=[
            'pattern', 'signal_type', 'price'
        ])
        
        return {
            'scan_type': ScanType.PATTERN_RECOGNITION.value,
            'pattern_type': pattern_type,
            'patterns': results,
            'signals': [p['signal_type'] for p in patterns] if patterns else [],
            'last_signal': patterns[0]['signal_type'] if patterns else None
        }
    
    @staticmethod
    def volume_spike_detection(
        df: pd.DataFrame,
        volume_threshold: float = 2.0,
        min_price_change: float = 0.03
    ) -> Dict[str, any]:
        """
        Detect abnormal volume spikes indicating institutional activity.
        
        Strategy:
        - Identify days with 2x+ normal volume
        - Check for price confirmation (at least 3% move)
        - Signal potential trend changes
        
        Args:
            df: DataFrame with OHLCV
            volume_threshold: Volume multiplier above average
            min_price_change: Minimum price movement to consider significant
            
        Returns:
            Dict with volume spike signals and analysis
        """
        if 'Volume' not in df.columns or 'Close' not in df.columns:
            raise ValueError("DataFrame must have Volume and Close columns")
            
        # Calculate average volume (20-day rolling)
        avg_volume = df['Volume'].rolling(window=20).mean()
        df['avg_vol_20d'] = avg_volume.values
        
        # Calculate volume ratio
        df['vol_ratio'] = df['Volume'] / (df['avg_vol_20d'] + 1e-10)
        
        # Volume spikes
        spikes = []
        for i, row in df.iterrows():
            if row['vol_ratio'] >= volume_threshold:
                price_change = abs(row['Close'].iloc[i] - row['Close'].iloc[i-1]) / row['Close'].iloc[i-1] if row['Close'].iloc[i-1] > 0 else 0
                
                if price_change >= min_price_change:
                    spikes.append({
                        'date': row['Date'],
                        'volume': int(row['Volume']),
                        'avg_volume': int(df['avg_vol_20d'].iloc[i]),
                        'vol_ratio': float(row['vol_ratio']),
                        'price_change_pct': price_change,
                        'close': float(row['Close'].iloc[i])
                    })
        
        results = pd.DataFrame(spikes) if spikes else pd.DataFrame(columns=[
            'date', 'volume', 'avg_volume', 'vol_ratio', 'price_change_pct'
        ])
        
        return {
            'scan_type': ScanType.VOLUME_SPIKE.value,
            'results': results,
            'total_spikes': len(spikes),
            'last_spike': spikes[-1] if spikes else None
        }
    
    @staticmethod
    def gap_analysis(
        df: pd.DataFrame,
        min_gap_pct: float = 0.03,
        volume_confirmation: float = 1.5
    ) -> Dict[str, any]:
        """
        Detect stock price gaps (overnight opening moves).
        
        Strategy:
        - Identify gap up/down at open (>3% from previous close)
        - Confirm with above-average volume
        - Track gap fill patterns
        
        Args:
            df: DataFrame with Date, Open, Close, Volume columns
            min_gap_pct: Minimum percentage for valid gap
            volume_confirmation: Volume multiplier for confirmation
            
        Returns:
            Dict with gap signals and analysis
        """
        if 'Date' not in df.columns or 'Open' not in df.columns:
            raise ValueError("DataFrame must have Date and Open columns")
            
        # Calculate previous day's close (for each date)
        sorted_df = df.sort_values('Date').reset_index(drop=True)
        
        gaps = []
        for i, row in sorted_df.iterrows():
            prev_close = df['Close'].iloc[df['Date'] < row['Date']].iloc[-1] if len(df['Date'][df['Date'] < row['Date']]) > 0 else row['Close'].iloc[i-2] if i >= 2 else None
            
            if prev_close is None:
                continue
                
            gap_pct = abs(row['Open'] - prev_close) / prev_close
            
            if gap_pct >= min_gap_pct:
                volume_ratio = row['Volume'] / (df['Volume'].rolling(window=20).mean().iloc[i] + 1e-10)
                
                is_bullish_gap = row['Open'] > prev_close
                signal_type = 'GAP_UP' if is_bullish_gap else 'GAP_DOWN'
                
                gaps.append({
                    'date': str(row['Date']),
                    'gap_type': signal_type,
                    'gap_pct': gap_pct,
                    'open': row['Open'],
                    'prev_close': prev_close,
                    'volume': int(row['Volume']),
                    'vol_ratio': float(volume_ratio),
                    'confirmed': volume_ratio >= volume_confirmation
                })
        
        results = pd.DataFrame(gaps) if gaps else pd.DataFrame(columns=[
            'date', 'gap_type', 'gap_pct', 'open', 'prev_close', 'volume', 'vol_ratio', 'confirmed'
        ])
        
        return {
            'scan_type': ScanType.GAP_ANALYSIS.value,
            'results': results,
            'gaps_detected': len(gaps),
            'bullish_gaps': sum(1 for g in gaps if g['gap_type'] == 'GAP_UP'),
            'bearish_gaps': sum(1 for g in gaps if g['gap_type'] == 'GAP_DOWN')
        }


def run_combined_strategy_scan(
    df: pd.DataFrame,
    scan_config: Dict[str, any] = None
) -> Dict[str, any]:
    """
    Run multiple scans and combine results into a comprehensive strategy.
    
    Args:
        df: DataFrame with all technical indicators
        scan_config: Configuration for each scan type
        
    Returns:
        Combined analysis with prioritized signals
    """
    if scan_config is None:
        scan_config = {
            'momentum': {
                'scan_type': ScanType.MOMENTUM_FILTER,
                'config': {}
            },
            'volatility': {
                'scan_type': ScanType.VOLATILITY_BREAKOUT,
                'config': {}
            }
        }
    
    results = {}
    signals = []
    
    # Run each scan
    for scan_name, config in scan_config.items():
        scan_type_str = config.get('scan_type', 'momentum_filter')
        
        if scan_type_str == ScanType.MOMENTUM_FILTER.value:
            results[scan_name] = EnhancedScans.momentum_filter_scan(df, **config.get('config', {}))
        elif scan_type_str == ScanType.VOLATILITY_BREAKOUT.value:
            results[scan_name] = EnhancedScans.volatility_breakout_scan(df, **config.get('config', {}))
        elif scan_type_str == ScanType.TREND_FOLLOWING.value:
            results[scan_name] = EnhancedScans.trend_following_scan(df, **config.get('config', {}))
        elif scan_type_str == ScanType.PATTERN_RECOGNITION.value:
            results[scan_name] = EnhancedScans.pattern_recognition_scan(
                df, 
                pattern_type=config.get('pattern_type', 'double_top'),
                pattern_confidence=config.get('confidence', 0.7)
            )
        elif scan_type_str == ScanType.VOLUME_SPIKE.value:
            results[scan_name] = EnhancedScans.volume_spike_detection(df, **config.get('config', {}))
    
    return {
        'combined_scan': 'multi_strategy_analysis',
        'individual_results': results,
        'timestamp': pd.Timestamp.now().isoformat() if hasattr(pd, 'Timestamp') else None
    }
