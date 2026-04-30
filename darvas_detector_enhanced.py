"""
Enhanced Darvas Box Detector - Multi-Level Support Implementation
Implements advanced box detection with extended resistance zones and support levels
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class DarvasBox:
    """Represents a detected Darvas box with full metadata"""
    
    start_date: datetime
    end_date: datetime
    high: float
    low: float
    volume_avg: float
    days: int
    
    # Additional levels
    extended_resistance: float = None
    support_zones: dict = field(default_factory=dict)  # {price: {'volume': float, 'touches': int}}
    
    @property
    def box_height(self) -> float:
        """Calculate box height percentage"""
        return ((self.high - self.low) / self.high) * 100
    
    @property
    def is_valid(self) -> bool:
        """Check if box meets minimum validity criteria"""
        return self.box_height >= 8.0 and self.days >= 5


@dataclass  
class BoxDetectionResult:
    """Complete detection result with multiple levels"""
    
    detected: bool
    boxes: list = field(default_factory=list)
    current_box: DarvasBox = None
    primary_level: str = 'none'  # 'primary', 'extended', 'support'
    
    # Analysis metrics
    box_count: int = 0
    total_volume: float = 0.0
    avg_true_range: float = 0.0
    
    def add_box(self, box: DarvasBox):
        """Add a detected box to results"""
        self.boxes.append(box)
        if self.current_box is None or self.boxes[-1].end_date > self.current_box.end_date:
            self.current_box = box
        self.box_count += 1


class AdvancedDarvasDetector:
    """
    Enhanced Darvas Box Detector with multi-level support and advanced features
    
    Detects:
    - Primary ascending boxes (classic Darvas)
    - Extended resistance levels above primary box
    - Support zones below primary box
    - Volume-weighted breakout confirmation
    """
    
    def __init__(self, 
                 min_volume_ratio=1.5,
                 breakout_threshold_pct=0.8,
                 min_box_size_pct=8.0,
                 min_days_in_box=3,
                 max_pullback_pct=3.0):
        """
        Initialize detector with configurable parameters
        
        Args:
            min_volume_ratio: Minimum volume multiplier for breakout confirmation
            breakout_threshold_pct: Breakout must exceed box high by this percentage
            min_box_size_pct: Minimum box height as percentage of entry price
            min_days_in_box: Minimum days to establish a valid box
            max_pullback_pct: Maximum acceptable pullback percentage to maintain box
        """
        self.min_volume_ratio = min_volume_ratio
        self.breakout_threshold_pct = breakout_threshold_pct
        self.min_box_size_pct = min_box_size_pct
        self.min_days_in_box = min_days_in_box
        self.max_pullback_pct = max_pullback_pct
        
        # Performance tracking
        self.total_boxes_detected = 0
        self.successful_breakouts = 0
    
    def detect_boxes(self, historical_data: pd.DataFrame) -> dict | None:
        """
        Detect Darvas boxes in historical data with multi-level analysis
        
        Args:
            historical_data: DataFrame with OHLCV columns (Open, High, Low, Close, Volume)
                             Must be sorted by date ascending
            
        Returns:
            Dictionary with detected box information and signals, or None if insufficient data
        """
        # Validate input
        if len(historical_data) < self.min_days_in_box + 5:
            logger.warning(f"Insufficient data points: {len(historical_data)} < {self.min_days_in_box + 5}")
            return None
        
        required_cols = ['High', 'Low', 'Volume']
        if not all(col in historical_data.columns for col in required_cols):
            missing = [col for col in required_cols if col not in historical_data.columns]
            logger.error(f"Missing required columns: {missing}")
            return None
        
        # Add date column if not present
        if 'Date' not in historical_data.columns:
            historical_data['Date'] = pd.to_datetime(historical_data.index)
        
        # Ensure data is sorted by date
        historical_data = historical_data.sort_values('Date')
        
        # Detect boxes
        result = self._detect_boxes_core(historical_data)
        
        if result is None:
            return None
        
        # Add extended levels for primary box
        result.with_extended_levels = self._find_extended_levels(result.current_box, historical_data)
        
        self.total_boxes_detected += 1
        
        logger.info(f"Detected {len(result.boxes)} boxes. Primary: {result.primary_level}")
        
        return result.to_dict() if not isinstance(result, dict) else result
    
    def _detect_boxes_core(self, historical_data: pd.DataFrame) -> BoxDetectionResult | None:
        """
        Core box detection algorithm - identifies ascending box patterns
        
        Uses the following logic:
        1. Track consecutive higher highs and higher lows (no pullbacks)
        2. Calculate box boundaries (high = max high, low = min low in sequence)
        3. Identify breakout when price exceeds current box high by threshold
        """
        
        result = BoxDetectionResult(detected=False)
        
        # Track box state
        box_stack = []  # Stack of active box levels
        current_high = historical_data.iloc[0]['High']
        current_low = historical_data.iloc[0]['Low']
        volume_sum = historical_data.iloc[0]['Volume']
        box_start_idx = 0
        
        for i in range(1, len(historical_data)):
            row = historical_data.iloc[i]
            
            # Update box boundaries (expand as needed)
            current_high = max(current_high, row['High'])
            current_low = min(current_low, row['Low'])
            volume_sum += row['Volume']
            days_since_start = i - box_start_idx + 1
            
            # Check for breakout
            high_price_pct_change = (row['High'] - current_high) / current_high * 100 if current_high > 0 else 0
            
            # Volume check for this day
            avg_volume = historical_data['Volume'].rolling(window=20, min_periods=5).mean().iloc[i]
            volume_ratio = row['Volume'] / avg_volume if pd.notna(avg_volume) and avg_volume > 0 else 1.0
            
            # Check breakout condition (price exceeded box high by threshold)
            is_breakout = (
                high_price_pct_change >= self.breakout_threshold_pct * 100 or
                row['Close'] > current_high * (1 + self.breakout_threshold_pct / 100)
            )
            
            if is_breakout:
                # Create box before breakout
                box_end_date = historical_data.iloc[i - 1]['Date']
                
                box_volume_avg = volume_sum / days_since_start
                
                # Check volume requirement
                if volume_ratio < self.min_volume_ratio:
                    logger.debug(f"Volume too low at {row['High']}: ratio={volume_ratio:.2f} < {self.min_volume_ratio}")
                    box_end_date = historical_data.iloc[i - 1]['Date']
                else:
                    # Create valid box
                    box = DarvasBox(
                        start_date=historical_data.iloc[box_start_idx]['Date'],
                        end_date=box_end_date,
                        high=current_high,
                        low=current_low,
                        volume_avg=round(box_volume_avg, 2),
                        days=days_since_start
                    )
                    
                    # Check minimum box size
                    if box.box_height >= self.min_box_size_pct:
                        result.add_box(box)
                        box_end_date = historical_data.iloc[i - 1]['Date']
                        current_high = row['High']
                        current_low = row['Low']
                        volume_sum = row['Volume']
                        days_since_start = 1
                        box_start_idx = i
                    
                    # Track successful breakout
                    self.successful_breakouts += 1
            
            # Check for pullback that breaks ascending pattern
            if (box_stack and 
                box_stack[-1].low > historical_data.iloc[i - 1]['Low']):
                # Still in uptrend
                pass
            elif len(box_stack) >= 2:
                prev_box = box_stack[-2]
                if row['Low'] < prev_box.low * (1 - self.max_pullback_pct / 100):
                    # Major pullback, end current box
                    logger.debug(f"Pullback detected ending box")
                    pass
        
        return result
    
    def _find_extended_levels(self, box: DarvasBox, historical_data: pd.DataFrame) -> dict | None:
        """
        Find extended resistance levels above primary box
        
        Looks for price levels where previous breakouts occurred with high volume
        Creates multi-tier breakout targets
        """
        
        if not isinstance(box, DarvasBox):
            return None
        
        current_resistance = box.high
        extended_levels = []
        
        # Look for significant highs above current resistance
        mask = historical_data['High'] > current_resistance * 1.02  # 2% above resistance
        
        level_candidates = []
        
        for idx, row in historical_data[mask].iterrows():
            # Check if this high has significant volume
            avg_volume_window = historical_data['Volume'].rolling(10).mean().iloc[idx]
            
            if pd.notna(avg_volume_window) and avg_volume_window > 0:
                volume_ratio = row['Volume'] / avg_volume_window
                
                # High volume breakout level
                if volume_ratio >= self.min_volume_ratio:
                    level_candidates.append({
                        'price': round(row['High'], 2),
                        'date': row['Date'].isoformat(),
                        'volume': round(row['Volume'], 0),
                        'volume_ratio': round(volume_ratio, 2)
                    })
        
        if level_candidates:
            # Sort by price descending and take top candidates
            level_candidates.sort(key=lambda x: x['price'], reverse=True)
            
            # Take top 3 extended levels
            for i, level in enumerate(level_candidates[:3], 1):
                level['level'] = f'extended_{i}'
                extended_levels.append(level)
        
        if extended_levels:
            # Create extended resistance object
            extended_resistance = {
                'resistance': [level['price'] for level in extended_levels],
                'avg_volume_at_level': np.mean([level['volume'] for level in extended_levels]),
                'levels': extended_levels,
                'primary_box_low': round(box.low, 2)
            }
            
            return {
                'detected': True,
                'primary_resistance': round(current_resistance, 2),
                **extended_resistance
            }
        
        return None
    
    def validate_breakout(self, current_price: float, box_high: float, 
                          volume_ratio: float = 1.0) -> dict:
        """
        Validate if price has broken out of Darvas box with proper confirmation
        
        Args:
            current_price: Current stock price
            box_high: Previous box high (resistance level)
            volume_ratio: Current volume vs average volume
            
        Returns:
            Dictionary with breakout validation results
        """
        
        price_broken_out = current_price > box_high * (1 + self.breakout_threshold_pct / 100)
        
        result = {
            'price_above_resistance': current_price >= box_high,
            'breakout_confirmed': price_broken_out and volume_ratio >= self.min_volume_ratio,
            'current_price': round(current_price, 2),
            'box_high': round(box_high, 2),
            'volume_ratio': round(volume_ratio, 2),
            'confidence': float(price_broken_out) * float(volume_ratio >= self.min_volume_ratio)
        }
        
        if result['breakout_confirmed']:
            logger.info(f"Breakout confirmed: ${result['current_price']} > ${box_high}")
        
        return result
    
    def check_box_continuity(self, historical_data: pd.DataFrame, 
                             target_low: float) -> dict:
        """
        Check if stock is maintaining box continuity (no significant pullbacks)
        
        Args:
            historical_data: Historical OHLCV data
            target_low: Current or previous box low to check against
            
        Returns:
            Dictionary with continuity analysis results
        """
        
        if len(historical_data) < 5:
            return {'is_continuous': False, 'reason': 'Insufficient data'}
        
        # Count days where price stayed above target_low
        days_above_target = (historical_data['Low'] >= target_low).sum()
        total_days = len(historical_data)
        
        continuity_ratio = days_above_target / total_days
        
        # Check for significant pullbacks (>5% from recent high)
        highs = historical_data['High'].rolling(10, min_periods=2).mean()
        significant_pullback_count = ((historical_data['Low'] < highs * 0.95)).sum()
        
        return {
            'is_continuous': continuity_ratio >= 0.8 and significant_pullback_count <= 2,
            'continuity_ratio': round(continuity_ratio, 3),
            'significant_pullbacks': int(significant_pullback_count),
            'days_above_target': int(days_above_target),
            'total_days': int(total_days)
        }
    
    def identify_support_zones(self, historical_data: pd.DataFrame, 
                               box_low: float, window_size=20) -> list:
        """
        Identify key support zones below primary box
        
        Looks for significant lows with high volume that could act as support levels
        
        Args:
            historical_data: Historical data
            box_low: Current box low to search below
            window_size: Rolling window for volume analysis
            
        Returns:
            List of support zone dictionaries sorted by price ascending
        """
        
        support_zones = []
        
        # Search for lows above 95% of box low (significant support zones)
        mask = (historical_data['Low'] > box_low * 0.95) & \
                (historical_data['Low'] < box_low)
        
        if not mask.any():
            return []
        
        # Find significant volume nodes
        historical_data_with_volume_avg = historical_data.copy()
        historical_data_with_volume_avg['volume_avg_10d'] = \
            historical_data['Volume'].rolling(window=10, min_periods=3).mean()
        
        for idx, row in historical_data_with_volume_avg[mask].iterrows():
            avg_volume = historical_data_with_volume_avg.loc[idx, 'volume_avg_10d']
            
            if pd.notna(avg_volume) and avg_volume > 0:
                volume_ratio = row['Volume'] / avg_volume
                
                # High volume node (potential support zone)
                if volume_ratio >= self.min_volume_ratio:
                    support_zones.append({
                        'price': round(row['Low'], 2),
                        'date': row['Date'].isoformat(),
                        'volume': int(row['Volume']),
                        'volume_avg': round(avg_volume, 0),
                        'volume_ratio': round(volume_ratio, 2)
                    })
        
        # Sort by price ascending
        support_zones.sort(key=lambda x: x['price'])
        
        return support_zones
    
    def calculate_atr(self, historical_data: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average True Range for volatility context
        
        Args:
            historical_data: Historical OHLCV data
            period: ATR period
            
        Returns:
            Average True Range value
        """
        
        if len(historical_data) < period + 1:
            return 0.0
        
        high = historical_data['High'].values
        low = historical_data['Low'].values
        close = historical_data['Close'].values
        
        # Calculate true range
        tr_high_low = np.abs(high - low)
        tr_prev_close = np.abs(high[1:] - close[:-1])
        tr_prev_open = np.abs(low[1:] - close[:-1])  # Assuming open ≈ previous close
        
        true_range = np.maximum(tr_high_low, np.maximum(tr_prev_close, tr_prev_open))
        
        return float(np.mean(true_range[-period:])) if len(true_range) >= period else 0.0


def create_mock_rising_stock(days=30, start_price=150, trend='up'):
    """Create mock historical data for testing"""
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='B')  # Business days
    
    if trend == 'up':
        # Rising stock with consolidation (typical Darvas setup)
        prices = start_price + np.cumsum(np.random.normal(0.8, 1, days))
        highs = prices * np.array([1 + np.random.uniform(0, 0.02) for _ in range(days)])
        lows = prices * np.array([1 - np.random.uniform(0, 0.03) for _ in range(days)])
    else:
        # Choppy stock (no box formation)
        prices = start_price + np.cumsum(np.random.normal(0, 1.5, days))
        highs = prices * np.array([1 + np.random.uniform(-0.02, 0.02) for _ in range(days)])
        lows = prices * np.array([1 + np.random.uniform(-0.03, -0.01) for _ in range(days)])
    
    # Add volume (higher during breakouts)
    volumes = np.random.poisson(1e6, days)
    
    return pd.DataFrame({
        'Date': dates,
        'Open': prices * 0.98 + np.random.normal(0, 0.5, days),
        'High': highs,
        'Low': lows,
        'Close': prices + np.random.normal(0, 1, days),
        'Volume': volumes
    })


def create_mock_choppy_stock(days=30, start_price=100):
    """Create mock choppy stock data (no breakout pattern)"""
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='B')
    
    # Sideways movement with no clear trend
    prices = start_price + np.cumsum(np.random.normal(0, 1.2, days))
    highs = prices * np.array([1 + np.random.uniform(-0.03, 0.03) for _ in range(days)])
    lows = prices * np.array([1 + np.random.uniform(-0.04, 0.03) for _ in range(days)])
    
    volumes = np.random.poisson(5e5, days)
    
    return pd.DataFrame({
        'Date': dates,
        'Open': prices * 0.97 + np.random.normal(0, 0.3, days),
        'High': highs,
        'Low': lows,
        'Close': prices + np.random.normal(0, 1, days),
        'Volume': volumes
    })


if __name__ == '__main__':
    import asyncio
    
    # Test with mock data
    detector = AdvancedDarvasDetector(
        min_volume_ratio=1.5,
        breakout_threshold_pct=0.8,
        min_box_size_pct=8.0
    )
    
    # Create test data
    rising_stock = create_mock_rising_stock(days=60, start_price=150)
    choppy_stock = create_mock_choppy_stock(days=60, start_price=100)
    
    print("=" * 60)
    print("Testing Darvas Box Detection")
    print("=" * 60)
    
    # Test rising stock (should detect boxes)
    print("\nRising Stock Analysis:")
    result = detector.detect_boxes(rising_stock)
    if result and result.get('detected'):
        box_info = result.get('current_box')
        if box_info:
            print(f"  Detected {len(result.get('boxes', []))} boxes")
            print(f"  Primary level: {result.get('primary_level')}")
            print(f"  Box price: ${round(box_info.get('box_price'), 2)}")
    
    # Test choppy stock (should not detect boxes)
    print("\nChoppy Stock Analysis:")
    result = detector.detect_boxes(choppy_stock)
    if result:
        print(f"  Detected: {result.get('detected', False)}")
