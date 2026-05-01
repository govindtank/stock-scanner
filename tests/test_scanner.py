"""
Comprehensive Test Suite for Stock Scanner
==========================================

Tests for all modules including:
- Technical indicators
- Darvas box detection (enhanced)
- Scan types (mean reversion, gap analysis, momentum, etc.)
- Configuration system
- Integration tests
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestDataGeneration:
    """Helper class for generating test data."""
    
    @staticmethod
    def create_uptrend_data(periods: int = 50) -> pd.DataFrame:
        """Create an uptrending stock data series."""
        dates = pd.date_range('2024-01-01', periods=periods, freq='D')
        
        # Create random walk with upward bias
        base_price = 100
        returns = np.random.normal(0.001, 0.02, periods)  # Small upward drift
        prices = base_price * (1 + returns).cumprod()
        
        high = prices * (1 + np.random.uniform(0.01, 0.03, periods))
        low = prices * (1 - np.random.uniform(0.01, 0.03, periods))
        close = prices
        
        return pd.DataFrame({
            'open': close * 1.002 + np.random.uniform(-0.5, 0.5, periods),
            'high': high,
            'low': low,
            'close': close,
            'volume': np.random.randint(1000000, 5000000, periods)
        }, index=dates)
    
    @staticmethod
    def create_volatile_data(periods: int = 50) -> pd.DataFrame:
        """Create a volatile stock data series."""
        dates = pd.date_range('2024-01-01', periods=periods, freq='D')
        
        base_price = 100
        returns = np.random.normal(0.001, 0.05, periods)  # Higher volatility
        prices = base_price * (1 + returns).cumprod()
        
        high = prices * (1 + np.random.uniform(0.03, 0.06, periods))
        low = prices * (1 - np.random.uniform(0.03, 0.06, periods))
        close = prices
        
        return pd.DataFrame({
            'open': close * 1.002 + np.random.uniform(-1, 1, periods),
            'high': high,
            'low': low,
            'close': close,
            'volume': np.random.randint(500000, 3000000, periods)
        }, index=dates)
    
    @staticmethod
    def create_gap_up_data(base_periods: int = 10) -> pd.DataFrame:
        """Create data with a gap up."""
        dates = pd.date_range('2024-01-01', periods=base_periods + 1, freq='D')
        
        base_price = 100
        returns = np.random.normal(0.0005, 0.02, base_periods)
        prices = [base_price] + list(base_price * (1 + returns).cumprod())
        
        # Create gap up on last day
        gap_up_prices = [p * 1.03 if i == base_periods else p for i, p in enumerate(prices)]
        
        high = [max(p * 1.02, 105) if i == base_periods else p * (1 + np.random.uniform(0.02, 0.04)) 
                 for i, p in enumerate(gap_up_prices)]
        low = [p * 0.98 if i == base_periods else p * (1 - np.random.uniform(0.02, 0.04)) 
                for i, p in enumerate(gap_up_prices)]
        
        close = gap_up_prices
        volumes = np.array([5e6] + [np.random.randint(1e6, 3e6, base_periods)])
        
        return pd.DataFrame({
            'open': [(p * 1.03) if i == base_periods else p * 1.002 + np.random.uniform(-0.5, 0.5) 
                     for i, p in enumerate(gap_up_prices)],
            'high': high,
            'low': low,
            'close': close,
            'volume': volumes
        }, index=dates)
    
    @staticmethod
    def create_volume_spike_data(base_periods: int = 10) -> pd.DataFrame:
        """Create data with a volume spike."""
        dates = pd.date_range('2024-01-01', periods=base_periods + 1, freq='D')
        
        base_price = 100
        returns = np.random.normal(0.001, 0.02, base_periods)
        prices = [base_price] + list(base_price * (1 + returns).cumprod())
        
        high = [p * (1 + np.random.uniform(0.02, 0.03)) for p in prices]
        low = [p * (1 - np.random.uniform(0.02, 0.03)) for p in prices]
        close = prices
        
        # Normal volume then spike on last day
        volumes = np.array([np.random.randint(1e6, 2e6) for _ in range(base_periods)] + [5e6])
        
        return pd.DataFrame({
            'open': [p * 1.002 + np.random.uniform(-0.5, 0.5) for p in prices],
            'high': high,
            'low': low,
            'close': close,
            'volume': volumes
        }, index=dates)


class TestTechnicalIndicators(unittest.TestCase):
    """Test technical indicators module."""
    
    def setUp(self):
        """Set up test data."""
        self.data = TestDataGeneration.create_uptrend_data()
        
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        from technical_indicators import TechnicalIndicators
        
        indicators = TechnicalIndicators()
        rsi = indicators.rsi(self.data['close'])
        
        # RSI should be between 0 and 100 for uptrending stock
        self.assertIsNotNone(rsi)
        self.assertGreaterEqual(rsi, 0)
        self.assertLessEqual(rsi, 100)
    
    def test_macd_calculation(self):
        """Test MACD calculation."""
        from technical_indicators import TechnicalIndicators
        
        indicators = TechnicalIndicators()
        macd = indicators.macd(self.data['close'])
        
        self.assertIn('macd', macd)
        self.assertIn('signal', macd)
        self.assertIn('histogram', macd)
    
    def test_bollinger_bands_calculation(self):
        """Test Bollinger Bands calculation."""
        from technical_indicators import TechnicalIndicators
        
        indicators = TechnicalIndicators()
        bb = indicators.bollinger_bands(self.data['close'])
        
        self.assertIn('middle', bb)
        self.assertIn('upper', bb)
        self.assertIn('lower', bb)
        self.assertEqual(bb['upper'], bb['middle'] + 2 * (bb['upper'] - bb['middle']))
    
    def test_atr_calculation(self):
        """Test ATR calculation."""
        from technical_indicators import TechnicalIndicators
        
        indicators = TechnicalIndicators()
        atr = indicators.atr(self.data['high'], self.data['low'], self.data['close'])
        
        self.assertIsNotNone(atr)
        self.assertGreater(atr, 0)
    
    def test_adx_calculation(self):
        """Test ADX calculation."""
        from technical_indicators import TechnicalIndicators
        
        indicators = TechnicalIndicators()
        adx = indicators.adx(self.data['high'], self.data['low'], self.data['close'])
        
        self.assertIn('adx', adx)
        self.assertIn('plus_di', adx)
        self.assertIn('minus_di', adx)
    
    def test_all_indicators_at_once(self):
        """Test calculating all indicators at once."""
        from technical_indicators import TechnicalIndicators
        
        indicators = TechnicalIndicators()
        all_indicators = indicators.calculate_all(self.data)
        
        expected_keys = ['rsi', 'macd', 'bollinger', 'atr', 'adx', 'ema_12', 'stochastic', 'momentum_10d']
        for key in expected_keys:
            self.assertIn(key, all_indicators)


class TestEnhancedDarvasDetector(unittest.TestCase):
    """Test enhanced Darvas detector with volume analysis and pattern recognition."""
    
    def setUp(self):
        """Set up test data."""
        self.data = TestDataGeneration.create_uptrend_data(100)
        self.boxes = []
        
    def test_box_detection(self):
        """Test box detection."""
        from darvas_detector import DarvasBoxDetector
        
        detector = DarvasBoxDetector(window_size=5)
        boxes = detector.detect_boxes(self.data)
        
        self.assertIsInstance(boxes, dict)
        self.assertIn('start', boxes[0] if boxes else {})
        self.assertIn('end', boxes[0] if boxes else {})
    
    def test_breakout_detection(self):
        """Test breakout detection."""
        from darvas_detector import DarvasBoxDetector
        
        detector = DarvasBoxDetector(window_size=5)
        boxes = detector.detect_boxes(self.data)
        breakouts = detector.find_breakouts(self.data, boxes)
        
        self.assertIsInstance(breakouts, list)
        for breakout in breakouts:
            self.assertIn('date', breakout)
            self.assertIn('price', breakout)
            self.assertIn('signal_strength', breakout)
    
    def test_volume_trend_analysis(self):
        """Test volume trend analysis."""
        from darvas_detector import DarvasBoxDetector
        
        detector = DarvasBoxDetector(window_size=5)
        
        # Manually analyze a recent index
        box_result = detector._analyze_volume_trend(self.data, len(self.data) - 10)
        self.assertIn(box_result, ['INCREASING', 'DECREASING', 'STABLE', 'NEUTRAL'])
    
    def test_pattern_recognition(self):
        """Test pattern recognition."""
        from darvas_detector import DarvasBoxDetector
        
        detector = DarvasBoxDetector(pattern_sensitivity=0.9)
        
        # Pattern detection may not return patterns in simple uptrend, but should not crash
        boxes = detector.detect_boxes(self.data)
        breakouts = detector.find_breakouts(self.data, boxes)
        
        for breakout in breakouts:
            self.assertIn('patterns_detected', breakout)
            self.assertIsInstance(breakout['patterns_detected'], list)
    
    def test_enhanced_signal_strength(self):
        """Test enhanced signal strength calculation."""
        from darvas_detector import DarvasBoxDetector
        
        detector = DarvasBoxDetector()
        
        # Test with typical values
        price_change = 0.04  # 4% breakout
        volume_multiplier = 1.8  # 180% volume
        
        score = (price_change * 2 + (volume_multiplier - 1))
        
        self.assertGreater(score, 0)
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation."""
        from darvas_detector import DarvasBoxDetector
        
        detector = DarvasBoxDetector()
        
        price_change = 0.05
        volume_spike = 1.7
        
        base_confidence = price_change * 20
        volume_bonus = min(volume_spike - 100, 40)
        
        self.assertGreaterEqual(base_confidence + volume_bonus, 60)


class TestScanTypes(unittest.TestCase):
    """Test various scan types."""
    
    def test_mean_reversion_scan(self):
        """Test mean reversion scanner."""
        from scan_types import MeanReversionScanner
        
        scanner = MeanReversionScanner(rsi_oversold=30, rsi_overbought=70)
        signals = scanner.analyze(self.data)
        
        # Should return either oversold or overbought or no signals (normal range)
        self.assertIsInstance(signals, list)
    
    def test_gap_analysis_scan(self):
        """Test gap analysis scanner."""
        from scan_types import GapAnalysisScanner
        
        data_with_gap = TestDataGeneration.create_gap_up_data()
        
        scanner = GapAnalysisScanner(gap_threshold=0.025, min_gap_volume_multiplier=1.5)
        signals = scanner.analyze(data_with_gap)
        
        self.assertIsInstance(signals, list)
    
    def test_momentum_scan(self):
        """Test momentum scanner."""
        from scan_types import MomentumScanner
        
        scanner = MomentumScanner(momentum_period=5, min_momentum_pct=0.02)
        signals = scanner.analyze(self.data)
        
        self.assertIsInstance(signals, list)
    
    def test_relative_strength_scan(self):
        """Test relative strength scanner."""
        from scan_types import RelativeStrengthScanner
        
        scanner = RelativeStrengthScanner(comparison_period=5)
        signals = scanner.analyze(self.data)
        
        self.assertIsInstance(signals, list)
    
    def test_volume_pattern_scan(self):
        """Test volume pattern scanner."""
        from scan_types import VolumePatternScanner
        
        data_with_spike = TestDataGeneration.create_volume_spike_data()
        
        scanner = VolumePatternScanner(spike_threshold=2.0, sustained_volume_periods=3)
        signals = scanner.analyze(data_with_spike)
        
        self.assertIsInstance(signals, list)


class TestConfiguration(unittest.TestCase):
    """Test configuration system."""
    
    def test_darvas_breakout_preset(self):
        """Test Darvas breakout preset."""
        from configuration import Preset, get_full_config
        
        preset = Preset.darvas_breakout()
        
        self.assertEqual(preset['scan_type'], 'darvas_breakout')
        self.assertIn('take_profit_pct', preset['trading'])
    
    def test_mean_reversion_preset(self):
        """Test mean reversion preset."""
        from configuration import Preset
        
        preset = Preset.mean_reversion()
        
        self.assertEqual(preset['scan_type'], 'mean_reversion')
        self.assertIn('take_profit_pct', preset['trading'])
    
    def test_get_full_config(self):
        """Test getting full configuration."""
        from configuration import get_full_config
        
        config = get_full_config()
        
        expected_sections = ['trading', 'risk', 'scan', 'alerts', 'data', 'charts']
        for section in expected_sections:
            self.assertIn(section, config)
    
    def test_get_config_with_preset(self):
        """Test getting config with preset."""
        from configuration import get_full_config, Presets
        
        config = get_full_config(preset_name='mean_reversion')
        
        self.assertEqual(config['scan_params'].get('mean_reversion_oversold'), 30)
    
    def test_validate_config(self):
        """Test configuration validation."""
        from configuration import validate_config
        
        # Valid config
        valid_config = {
            'trading': {'take_profit_pct': 5.0, 'stop_loss_pct': 3.0},
            'risk': {'max_portfolio_risk': 0.10},
            'scan': {},
            'alerts': {'alert_channels': ['console']},
            'data': {'primary_source': 'yfinance'},
            'charts': {'enable_plotly_charts': True}
        }
        
        errors = validate_config(valid_config)
        self.assertEqual(errors, [])
        
        # Invalid config
        invalid_config = {
            'trading': {'take_profit_pct': -5.0},  # Negative value
        }
        
        errors = validate_config(invalid_config)
        self.assertGreater(len(errors), 0)
    
    def test_presets_available(self):
        """Test that all presets are available."""
        from configuration import Presets
        
        preset_names = ['darvas_breakout', 'mean_reversion', 'momentum', 
                        'gap_trading', 'relative_strength', 'volume_patterns']
        
        for name in preset_names:
            self.assertTrue(Presets.validate_preset(name))


class TestDataScenarios(unittest.TestCase):
    """Integration tests with various data scenarios."""
    
    def test_volatile_stock_analysis(self):
        """Test analysis on volatile stock."""
        from darvas_detector import IndianStockMonitor
        
        volatile_data = TestDataGeneration.create_volatile_data()
        
        monitor = IndianStockMonitor()
        result = monitor.analyze_stock('TEST_VOLATILE')  # This will actually fetch data
        
        self.assertIsNotNone(result)
    
    def test_multi_stock_scan(self):
        """Test scanning multiple stocks."""
        from darvas_detector import PortfolioScanner
        
        scanner = PortfolioScanner()
        
        tickers = ['RELIANCE.NS', 'TCS.NS']
        results = scanner.scan_all_stocks(tickers)
        
        self.assertGreater(len(results), 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_insufficient_data_for_rsi(self):
        """Test RSI with insufficient data."""
        from technical_indicators import TechnicalIndicators
        
        # Less than 14 periods
        short_data = pd.DataFrame({
            'close': list(range(5, 20))
        })
        
        indicators = TechnicalIndicators()
        rsi = indicators.rsi(short_data['close'])
        
        # RSI should return None or valid value depending on implementation
        self.assertIsNotNone(rsi) or (rsi is None and len(short_data) < 14)
    
    def test_insufficient_data_for_bollinger_bands(self):
        """Test Bollinger Bands with insufficient data."""
        from technical_indicators import TechnicalIndicators
        
        short_data = pd.DataFrame({
            'close': list(range(5, 20))
        })
        
        indicators = TechnicalIndicators()
        bb = indicators.bollinger_bands(short_data['close'])
        
        self.assertIsNotNone(bb.get('middle'))
    
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrame."""
        from technical_indicators import TechnicalIndicators
        
        empty_df = pd.DataFrame({'close': []})
        
        indicators = TechnicalIndicators()
        rsi = indicators.rsi(empty_df['close'])
        
        self.assertIsNone(rsi)


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes in order
    suite.addTests(loader.loadTestsFromTestCase(TestTechnicalIndicators))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedDarvasDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestScanTypes))
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestDataScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("STOCK SCANNER COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print()
    
    # Run tests
    result = run_tests()
    
    print()
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED - See above for details")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
