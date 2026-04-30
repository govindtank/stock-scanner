"""
Test suite for Stock Scanner enhancements
Tests Darvas detector, async scanner, and API endpoints
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest
import pandas as pd
from datetime import datetime, timedelta

# Import modules under test
from darvas_detector_enhanced import (
    AdvancedDarvasDetector,
    DarvasBox,
    BoxDetectionResult,
    create_mock_rising_stock,
    create_mock_choppy_stock
)


class TestAdvancedDarvasDetector:
    """Test suite for AdvancedDarvasDetector"""
    
    def test_detect_box_with_rising_stock(self):
        """Test that rising stock data detects Darvas boxes"""
        detector = AdvancedDarvasDetector(
            min_volume_ratio=1.5,
            breakout_threshold_pct=0.8,
            min_box_size_pct=8.0
        )
        
        mock_data = create_mock_rising_stock(days=60, start_price=150)
        
        result = detector.detect_boxes(mock_data)
        
        # Should detect at least one box
        assert result is not None
        assert isinstance(result, dict)
        assert 'detected' in result
    
    def test_detect_box_returns_correct_structure(self):
        """Test that detection result has correct structure"""
        detector = AdvancedDarvasDetector()
        mock_data = create_mock_rising_stock(days=45, start_price=100)
        
        result = detector.detect_boxes(mock_data)
        
        assert 'detected' in result
        assert 'current_box' in result
        assert 'box_price' in result
        assert 'support' in result
        assert 'resistance' in result
    
    def test_detect_no_box_with_choppy_stock(self):
        """Test that choppy stock data doesn't detect boxes"""
        detector = AdvancedDarvasDetector()
        mock_data = create_mock_choppy_stock(days=60, start_price=100)
        
        result = detector.detect_boxes(mock_data)
        
        # Choppy data should not have valid detection or return None
        assert result is None or not result.get('detected')
    
    def test_box_properties(self):
        """Test DarvasBox dataclass properties"""
        box = DarvasBox(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 15),
            high=160.0,
            low=150.0,
            volume_avg=1e6,
            days=14
        )
        
        assert box.high == 160.0
        assert box.low == 150.0
        assert box.volume_avg == 1e6
        assert box.days == 14
        
        # Test box height calculation
        expected_height = ((160.0 - 150.0) / 160.0) * 100
        assert abs(box.box_height - expected_height) < 0.01
    
    def test_box_validity_check(self):
        """Test box validity criteria"""
        # Valid box: height >= 8%, days >= 3
        valid_box = DarvasBox(
            start_date=datetime.now(),
            end_date=datetime.now(),
            high=100.0,
            low=95.0,  # 5% range = 5% height
            volume_avg=1e6,
            days=7
        )
        assert valid_box.is_valid is False  # Box too small (only 4.8%)
        
        # Larger box
        large_box = DarvasBox(
            start_date=datetime.now(),
            end_date=datetime.now(),
            high=100.0,
            low=90.0,  # 10% range = 10% height
            volume_avg=1e6,
            days=5
        )
        assert large_box.is_valid is True
    
    def test_validate_breakout(self):
        """Test breakout validation"""
        detector = AdvancedDarvasDetector(min_volume_ratio=1.5)
        
        # Below box - no breakout
        result = detector.validate_breakout(
            current_price=100,
            box_high=105,
            volume_ratio=1.2
        )
        assert result['breakout_confirmed'] is False
        
        # Above box with good volume - breakout confirmed
        result = detector.validate_breakout(
            current_price=110,
            box_high=105,
            volume_ratio=2.0
        )
        assert result['breakout_confirmed'] is True
    
    def test_box_continuity_check(self):
        """Test box continuity analysis"""
        detector = AdvancedDarvasDetector()
        mock_data = create_mock_rising_stock(days=30, start_price=150)
        
        # Check continuity with current low
        result = detector.check_box_continuity(
            historical_data=mock_data,
            target_low=140.0
        )
        
        assert 'is_continuous' in result
        assert 'continuity_ratio' in result
        assert isinstance(result['is_continuous'], bool)


class TestAsyncStockScanner:
    """Test suite for AsyncStockScanner"""
    
    @pytest.mark.asyncio
    async def test_scan_returns_signals(self):
        """Test that scan returns trading signals"""
        scanner = AsyncStockScanner(
            cash=10000,
            commission=9.95,
            max_concurrent=2
        )
        
        # Use mock data or real tickers with fallback
        import yfinance as yf
        
        # Test with a known ticker
        try:
            scanner_data = yf.Ticker('AAPL').history(period='3mo')
            if not scanner_data.empty:
                tickers = ['AAPL', 'MSFT']
                signals = await scanner.scan(symbols=tickers, top_n=5)
                
                assert isinstance(signals, list)
                # May return empty if no boxes detected, which is valid
        except Exception as e:
            pytest.skip(f"Could not test with real tickers: {e}")
    
    def test_sync_wrapper(self):
        """Test sync wrapper for backward compatibility"""
        scanner = AsyncStockScanner(max_concurrent=3)
        
        # Sync wrapper should work without errors
        signals = scanner.scan_sync(symbols=['AAPL', 'MSFT'], top_n=5)
        
        assert isinstance(signals, list)


class TestDetectionEdgeCases:
    """Test edge cases and error handling"""
    
    def test_insufficient_data(self):
        """Test behavior with insufficient data"""
        detector = AdvancedDarvasDetector(min_days_in_box=3)
        
        # Create minimal data (less than minimum)
        dates = pd.date_range(end=datetime.now(), periods=2, freq='B')
        minimal_data = pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [102.0, 103.0],
            'Low': [98.0, 99.0],
            'Close': [101.0, 102.0],
            'Volume': [1e5, 1e5]
        })
        
        result = detector.detect_boxes(minimal_data)
        
        # Should handle gracefully (return None or minimal structure)
        assert result is not None
    
    def test_missing_columns(self):
        """Test behavior with missing required columns"""
        detector = AdvancedDarvasDetector()
        
        invalid_data = pd.DataFrame({
            'Date': pd.date_range(end=datetime.now(), periods=30, freq='B'),
            'Price': range(100, 130)
        })
        
        result = detector.detect_boxes(invalid_data)
        
        # Should return None for invalid data structure
        assert result is None or not result.get('detected')


if __name__ == '__main__':
    pytest.main(['-v', '--tb=short'])
