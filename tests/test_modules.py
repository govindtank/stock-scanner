#!/usr/bin/env python3
"""
Comprehensive Test Suite for Stock Scanner Enhanced Modules
Tests all new modules: technical_indicators, enhanced_scans, risk_management, backtesting, portfolio_correlation
"""

import sys
sys.path.insert(0, '/Users/govind/stock-scanner')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================================================
# Test Data Generator
# ============================================================================

def generate_mock_market_data(n_days: int = 252, tickers: list = None) -> dict:
    """Generate realistic mock market data for testing."""
    if tickers is None:
        tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'TSLA', 'NVDA']
    
    np.random.seed(42)  # Reproducible results
    
    data_dict = {}
    
    for ticker in tickers:
        # Generate random walk with drift
        driftrate = np.random.normal(0.0003, 0.015, n_days)  # Daily return
        volatility = np.random.lognormal(0.6, 0.3, n_days) - 1  # Daily return
        
        daily_returns = driftrate + volatility * 0.01
        
        # Cumulative returns with initial price of $100
        cumulative_returns = (1 + daily_returns).cumprod()
        close_prices = 100 * cumulative_returns
        
        # Generate OHLC data
        price_range = np.random.uniform(0.01, 0.03, n_days)
        
        high = close_prices * (1 + price_range / 2)
        low = close_prices * (1 - price_range / 2)
        
        # Random walk for volume
        avg_volume = int(np.random.uniform(5e6, 3e7))
        volume = avg_volume * np.random.lognormal(0, 0.5, n_days).clip(0.5, 5)
        
        # Add date column
        start_date = datetime.now() - timedelta(days=n_days - 1)
        dates = [start_date + timedelta(days=i) for i in range(n_days)]
        
        data_dict[ticker] = pd.DataFrame({
            'Date': dates,
            'Open': high * 0.98,
            'High': high,
            'Low': low,
            'Close': close_prices,
            'Volume': volume
        })
    
    return {ticker: data for ticker, data in data_dict.items()}


# ============================================================================
# Test Technical Indicators Module
# ============================================================================

def test_technical_indicators():
    """Test all technical indicator calculations."""
    print("\n" + "="*60)
    print("TESTING: technical_indicators.py")
    print("="*60)
    
    from technical_indicators import TechnicalIndicators
    
    # Generate test data
    mock_data = generate_mock_market_data(n_days=30, tickers=['AAPL'])
    df = mock_data['AAPL']
    
    try:
        # Test RSI
        rsi_series = TechnicalIndicators.rsi(pd.Series(df['Close']), period=14)
        assert len(rsi_series) == len(df) - 13, "RSI length mismatch"
        assert rsi_series.min() >= 0 and rsi_series.max() <= 100, "RSI out of bounds"
        print("✓ RSI calculation: PASS")
        
        # Test MACD
        macd_line, signal, histogram = TechnicalIndicators.macd(
            pd.Series(df['Close']), fast_period=12, slow_period=26, signal_period=9
        )
        assert len(macd_line) == len(df) - 34, "MACD length mismatch"
        assert len(signal) == len(df) - 35, "Signal line length mismatch"
        print("✓ MACD calculation: PASS")
        
        # Test Bollinger Bands
        upper, middle, lower = TechnicalIndicators.bollinger_bands(
            pd.Series(df['Close']), window=20, num_std=2.0
        )
        assert len(upper) == len(df) - 19, "Upper band length mismatch"
        assert upper > middle for all values in valid range, "Bollinger Bands invalid"
        print("✓ Bollinger Bands calculation: PASS")
        
        # Test Stochastic
        stoch_k, stoch_d = TechnicalIndicators.stochastic(
            pd.Series(df['High']),
            pd.Series(df['Low']),
            pd.Series(df['Close']),
            k_period=14, d_period=3
        )
        assert len(stoch_k) == len(df) - 13, "Stochastic K length mismatch"
        assert stoch_k.min() >= 0 and stoch_k.max() <= 100, "Stochastic out of bounds"
        print("✓ Stochastic calculation: PASS")
        
        # Test ATR
        atr_series = TechnicalIndicators.atr(
            pd.Series(df['High']),
            pd.Series(df['Low']),
            pd.Series(df['Close']),
            period=14
        )
        assert len(atr_series) == len(df) - 13, "ATR length mismatch"
        assert atr_series > 0 for all values, "ATR should be positive"
        print("✓ ATR calculation: PASS")
        
        # Test VWAP
        vwap = TechnicalIndicators.vwap(
            pd.Series(df['High']),
            pd.Series(df['Low']),
            pd.Series(df['Close']),
            pd.Series(df['Volume'])
        )
        assert len(vwap) == len(df), "VWAP length mismatch"
        print("✓ VWAP calculation: PASS")
        
        # Test ADX
        adx = TechnicalIndicators.adx(
            pd.Series(df['High']),
            pd.Series(df['Low']),
            pd.Series(df['Close']),
            period=14
        )
        assert len(adx) == len(df) - 13, "ADX length mismatch"
        assert adx >= 0 and adx <= 100 for all values, "ADX out of bounds"
        print("✓ ADX calculation: PASS")
        
        # Test Williams %R
        wr = TechnicalIndicators.williams_r(
            pd.Series(df['High']),
            pd.Series(df['Low']),
            pd.Series(df['Close']),
            period=14
        )
        assert len(wr) == len(df) - 13, "Williams R length mismatch"
        assert wr >= -100 and wr <= 0 for all values, "Williams R out of bounds"
        print("✓ Williams %R calculation: PASS")
        
        # Test CCI
        cci = TechnicalIndicators.commodity_channel_index(
            pd.Series(df['Close']), period=20
        )
        assert len(cci) == len(df) - 19, "CCI length mismatch"
        print("✓ CCI calculation: PASS")
        
        # Test all-in-one method
        result = TechnicalIndicators.calculate_all(
            pd.Series(df['Close']),
            pd.Series(df['High']),
            pd.Series(df['Low']),
            pd.Series(df['Volume'])
        )
        assert 'rsi' in result and 'macd_line' in result and 'bollinger_upper' in result, \
               "calculate_all missing indicators"
        print("✓ Batch indicator calculation: PASS")
        
        return True
        
    except Exception as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Test Enhanced Scans Module
# ============================================================================

def test_enhanced_scans():
    """Test all enhanced scan strategies."""
    print("\n" + "="*60)
    print("TESTING: enhanced_scans.py")
    print("="*60)
    
    from enhanced_scans import EnhancedScans, ScanType
    
    # Generate test data for multiple tickers
    mock_data = generate_mock_market_data(n_days=100, tickers=['AAPL', 'GOOGL'])
    
    try:
        # Test Momentum Filter Scan
        momentum_result = EnhancedScans.momentum_filter_scan(
            pd.DataFrame(mock_data['AAPL']),
            rsi_period=14,
            rsi_buy=30,
            rsi_sell=70
        )
        assert 'scan_type' in momentum_result and momentum_result['scan_type'] == ScanType.MOMENTUM_FILTER.value, \
               "Momentum filter scan type incorrect"
        print("✓ Momentum Filter Scan: PASS")
        
        # Test Volatility Breakout Scan
        bb_data = pd.DataFrame(mock_data['AAPL'])
        from technical_indicators import TechnicalIndicators
        upper, middle, lower = TechnicalIndicators.bollinger_bands(
            pd.Series(bb_data['Close']), 20, 2.0
        )
        bb_data['bb_upper'] = upper.values
        bb_data['bb_lower'] = lower.values
        bb_data['avg_vol_20d'] = bb_data['Volume'].rolling(window=20).mean().values
        
        vol_breakout_result = EnhancedScans.volatility_breakout_scan(bb_data)
        assert 'scan_type' in vol_breakout_result, "Volatility breakout scan missing type"
        print("✓ Volatility Breakout Scan: PASS")
        
        # Test Trend Following Scan
        trend_data = pd.DataFrame(mock_data['AAPL'])
        from technical_indicators import TechnicalIndicators
        adx_series = TechnicalIndicators.adx(
            pd.Series(trend_data['High']),
            pd.Series(trend_data['Low']),
            pd.Series(trend_data['Close']),
            14
        )
        trend_data['adx'] = adx_series.values
        
        trend_result = EnhancedScans.trend_following_scan(trend_data)
        assert 'scan_type' in trend_result and trend_result['scan_type'] == ScanType.TREND_FOLLOWING.value, \
               "Trend following scan type incorrect"
        print("✓ Trend Following Scan: PASS")
        
        # Test Pattern Recognition (Double Bottom)
        pattern_data = pd.DataFrame(mock_data['AAPL'])
        pattern_result = EnhancedScans.pattern_recognition_scan(
            pattern_data,
            pattern_type='double_bottom'
        )
        assert 'scan_type' in pattern_result and pattern_result['scan_type'] == ScanType.PATTERN_RECOGNITION.value, \
               "Pattern recognition scan type incorrect"
        print("✓ Pattern Recognition Scan: PASS")
        
        # Test Volume Spike Detection
        vol_spike_result = EnhancedScans.volume_spike_detection(
            pd.DataFrame(mock_data['AAPL']),
            volume_threshold=2.0
        )
        assert 'scan_type' in vol_spike_result, "Volume spike detection missing type"
        print("✓ Volume Spike Detection: PASS")
        
        return True
        
    except Exception as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Test Risk Management Module
# ============================================================================

def test_risk_management():
    """Test all risk management calculations."""
    print("\n" + "="*60)
    print("TESTING: risk_management.py")
    print("="*60)
    
    from risk_management import RiskManager, StopLossType, TakeProfitType, PositionSizingType
    
    try:
        # Test Fixed % Stop Loss
        stop_price = RiskManager.calculate_stop_loss(
            entry_price=150.0,
            stop_type=StopLossType.FIXED_PCT
        )
        assert stop_price < 150.0, "Fixed % stop should be below entry"
        print("✓ Fixed % Stop Loss: PASS")
        
        # Test ATR-based Stop Loss
        price_data = pd.Series([148, 149, 150, 151, 152, 153, 154, 155, 156, 157] +
                               [148, 149, 150, 151, 152, 153, 154, 155, 156, 157] * 10)
        atr_stop = RiskManager.calculate_stop_loss(
            entry_price=150.0,
            stop_type=StopLossType.ATR_BASED,
            price_data=price_data
        )
        assert atr_stop < 150.0 and atr_stop > 130.0, "ATR stop out of reasonable range"
        print("✓ ATR-based Stop Loss: PASS")
        
        # Test Take-Profit (Fixed %)
        tp_price = RiskManager.calculate_take_profit(
            entry_price=150.0,
            tp_type=TakeProfitType.FIXED_PCT
        )
        assert tp_price > 150.0, "Fixed % TP should be above entry"
        print("✓ Fixed % Take-Profit: PASS")
        
        # Test Position Sizing (Fixed %)
        size = RiskManager.calculate_position_size(
            account_balance=100000,
            stock_price=150.0,
            sizing_type=PositionSizingType.FIXED_PERCENT
        )
        assert 0 < size <= 25000, "Fixed % position size out of range"
        print("✓ Fixed % Position Sizing: PASS")
        
        # Test VaR Calculation
        returns = pd.Series(np.random.normal(0.0003, 0.015, 500))
        var = RiskManager.calculate_var(returns, confidence_level=0.95, horizon_days=1)
        assert -0.1 < var < 0, "VaR should be negative (loss estimate)"
        print("✓ Value-at-Risk Calculation: PASS")
        
        # Test Drawdown Tracking
        equity_curve = pd.Series([100000] + [100500, 102000, 98000, 100000, 102500] * 10)
        dd_info = RiskManager.track_drawdown(equity_curve)
        assert 'current_drawdown' in dd_info and 'max_drawdown' in dd_info
        print("✓ Drawdown Tracking: PASS")
        
        # Test Risk/Reward Calculation
        rr_info = RiskManager.calculate_risk_reward(
            entry_price=150.0,
            stop_loss=145.0,
            take_profit=170.0,
            position_quantity=100
        )
        assert 'risk_reward_ratio' in rr_info and rr_info['risk_reward_ratio'] > 0
        assert abs(rr_info['risk_reward_ratio'] - 4.0) < 0.1, "R:R ratio incorrect"
        print("✓ Risk/Reward Calculation: PASS")
        
        # Test Position Validation
        is_valid, reason = RiskManager.validate_position(
            entry_price=150.0,
            stop_loss=145.0,
            take_profit=170.0,
            account_balance=100000,
            stock_price=150.0
        )
        assert is_valid == True, "Valid position should pass validation"
        print("✓ Position Validation: PASS")
        
        return True
        
    except Exception as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Test Portfolio Correlation Module
# ============================================================================

def test_portfolio_correlation():
    """Test all correlation analysis functions."""
    print("\n" + "="*60)
    print("TESTING: portfolio_correlation.py")
    print("="*60)
    
    from portfolio_correlation import CorrelationAnalyzer
    
    # Generate correlated returns data
    n_days = 252
    np.random.seed(123)
    
    # Create covariance matrix for correlation structure
    assets = ['AAPL', 'MSFT', 'AMZN']
    cov_matrix = np.array([
        [0.02, 0.008, 0.007],
        [0.008, 0.02, 0.01],
        [0.007, 0.01, 0.02]
    ])
    
    # Generate correlated random returns
    from numpy.linalg import cholesky
    L = cholesky(cov_matrix)
    correlated_returns = np.random.normal(0, 1, (n_days, 3)) @ L.T
    
    # Convert to DataFrame
    portfolio_returns = pd.DataFrame(
        correlated_returns,
        columns=assets,
        index=pd.date_range('2023-01-01', periods=n_days)
    )
    
    try:
        # Test correlation matrix calculation
        corr_matrix = CorrelationAnalyzer.calculate_correlation_matrix({
            'AAPL': portfolio_returns['AAPL'],
            'MSFT': portfolio_returns['MSFT'],
            'AMZN': portfolio_returns['AMZN']
        })
        assert corr_matrix.shape == (3, 3), "Correlation matrix wrong shape"
        print("✓ Correlation Matrix: PASS")
        
        # Test risk decomposition
        weights = {'AAPL': 0.4, 'MSFT': 0.35, 'AMZN': 0.25}
        individual_vols = {asset: returns.std() * np.sqrt(252) for asset, returns in portfolio_returns.items()}
        
        risk_contributions = CorrelationAnalyzer.decompose_portfolio_risk(
            corr_matrix, weights, individual_vols
        )
        assert len(risk_contributions) == 3, "Risk decomposition wrong length"
        print("✓ Risk Decomposition: PASS")
        
        # Test overconcentration check
        concentration_result = CorrelationAnalyzer.check_overconcentration(
            weights, corr_matrix
        )
        assert 'alerts' in concentration_result and 'effective_number_of_assets' in concentration_result
        print("✓ Over-concentration Check: PASS")
        
        # Test diversification score
        diversity_score = CorrelationAnalyzer.calculate_diversification_score(corr_matrix, weights)
        assert 0 <= diversity_score <= 1, "Diversification score out of range"
        print("✓ Diversification Score: PASS")
        
        # Test low correlation asset finding
        # Add uncorrelated asset (simulate with random data)
        uncorr_returns = np.random.normal(0, 1, n_days)
        corr_matrix_expanded = pd.DataFrame({
            'AAPL': portfolio_returns['AAPL'],
            'MSFT': portfolio_returns['MSFT'],
            'AMZN': portfolio_returns['AMZN'],
            'BOND': uncorr_returns
        })
        
        low_corr_assets = CorrelationAnalyzer.find_low_correlation_assets(
            corr_matrix_expanded, exclude_assets=['AAPL', 'MSFT']
        )
        assert isinstance(low_corr_assets, list), "Low correlation assets should be list"
        print("✓ Low Correlation Asset Finding: PASS")
        
        # Test sector exposure analysis
        portfolio_data = {asset: pd.Series(returns) for asset, returns in portfolio_returns.items()}
        sector_exposure = CorrelationAnalyzer.analyze_sector_exposure(portfolio_data)
        assert 'sector_exposure' in sector_exposure, "Sector exposure missing"
        print("✓ Sector Exposure Analysis: PASS")
        
        return True
        
    except Exception as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Test Backtesting Engine
# ============================================================================

def test_backtesting():
    """Test backtesting engine."""
    print("\n" + "="*60)
    print("TESTING: backtesting.py")
    print("="*60)
    
    from backtesting import BacktestingEngine, TradeSide
    
    # Generate mock data with clear trend signals for testing
    np.random.seed(456)
    n_days = 100
    start_date = datetime.now() - timedelta(days=n_days - 1)
    dates = [start_date + timedelta(days=i) for i in range(n_days)]
    
    # Create data with clear buy signals (e.g., mean reversion around $150)
    close_prices = 150 + np.random.normal(0, 3, n_days)
    
    data = pd.DataFrame({
        'Date': dates,
        'Open': close_prices * 0.98,
        'High': close_prices * 1.02,
        'Low': close_prices * 0.96,
        'Close': close_prices,
        'Volume': np.random.randint(1e6, 5e6, n_days)
    })
    
    try:
        # Create backtesting engine
        engine = BacktestingEngine(
            initial_capital=100000,
            transaction_cost_pct=0.001
        )
        
        # Set data
        engine.set_data(data)
        print("✓ Backtesting Engine initialization: PASS")
        
        # Define simple entry signal (buy when price below $147)
        def entry_signal(df_row):
            return df_row['Close'] < 147
        
        # Define exit signal (sell when price above $153)
        def exit_signal(df_row):
            return df_row['Close'] > 153
        
        # Run backtest
        result = engine.analyze_strategy(
            entry_signal=entry_signal,
            exit_signal=exit_signal,
            strategy_name="mean_reversion",
            use_stop_loss=True,
            stop_loss_pct=0.05
        )
        
        assert 'sharpe_ratio' in result._asdict() if hasattr(result, '_asdict') else hasattr(result, 'sharpe_ratio'), \
               "Backtest result missing metrics"
        print("✓ Strategy Analysis: PASS")
        
        # Check that equity curve exists
        assert len(result.equity_curve) > 0, "Equity curve empty"
        print("✓ Equity Curve Generation: PASS")
        
        return True
        
    except Exception as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# Main Test Runner
# ============================================================================

def main():
    """Run all tests and generate summary."""
    
    print("="*60)
    print("STOCK SCANNER MODULE TEST SUITE")
    print("="*60)
    
    results = {
        'technical_indicators': test_technical_indicators(),
        'enhanced_scans': test_enhanced_scans(),
        'risk_management': test_risk_management(),
        'portfolio_correlation': test_portfolio_correlation(),
        'backtesting': test_backtesting()
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\n  Total: {passed}/{total} modules passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Ready to push to GitHub.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} module(s) failed. Please review before pushing.")
        return 1


if __name__ == "__main__":
    exit(main())
