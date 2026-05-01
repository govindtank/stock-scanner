# Changelog

## [1.5.0] - 2026-05-01 (Enhanced Release)

### 🎉 Major Enhancements

This release adds comprehensive technical analysis capabilities, multiple trading strategies, risk management tools, and backtesting functionality.

#### New Modules Added

##### 1. Technical Indicators (`technical_indicators.py`)
- **MACD**: Moving Average Convergence Divergence (12/26/9 periods)
- **Bollinger Bands**: Volatility bands with upper/middle/lower bounds
- **Stochastic Oscillator**: %K and %D lines for momentum detection
- **ADX**: Average Directional Index for trend strength (0-100 scale)
- **ATR**: Average True Range for volatility measurement and stop-loss placement
- **VWAP**: Volume Weighted Average Price for institutional level identification
- **Williams %R**: Momentum oscillator (-100 to 0 scale)
- **CCI**: Commodity Channel Index for cyclical trend analysis

All indicators support both Pandas Series and NumPy arrays. Batch calculation method available.

##### 2. Enhanced Scans (`enhanced_scans.py`)
Six advanced scanning strategies:

1. **Momentum Filter Scan**
   - RSI oversold/overbought detection
   - MACD momentum reversal confirmation
   - VWAP trend filter

2. **Volatility Breakout Detection**
   - Bollinger Band breakout identification
   - Volume-based breakout confirmation (1.5x average)
   - Breakout strength calculation

3. **Trend Following Strategy**
   - 9/21 period moving average crossover
   - ADX trend filter (>25 threshold)
   - ATR-based stop-loss integration

4. **Pattern Recognition**
   - Double Top (M-pattern) detection
   - Double Bottom (W-pattern) detection  
   - Head and Shoulders identification (simplified)
   - Signal generation with confidence levels

5. **Volume Spike Detection**
   - 2x average volume threshold
   - Minimum 3% price move requirement
   - Institutional activity signaling

6. **Gap Analysis**
   - >3% overnight opening gaps
   - Volume confirmation (1.5x multiplier)
   - Gap fill tracking patterns

##### 3. Risk Management (`risk_management.py`)
Professional money management implementation:

**Stop-Loss Strategies:**
- Fixed percentage (e.g., 5% below entry)
- ATR-based dynamic stops
- Volatility-adjusted stops (monthly vol targeting)
- Chain stop (tightening over time)
- Trend-following stops (below SMA20)

**Take-Profit Strategies:**
- Fixed percentage targets
- Risk/reward ratio based (default 2.5:1)
- Trailing stops with configurable distance
- RSI-based reversal detection

**Position Sizing:**
- Fixed percentage of account
- Kelly Criterion with fractioning (0.25 = quarter-Kelly)
- Volatility targeting for risk parity
- Risk parity equal contribution

**Risk Metrics:**
- Value-at-Risk (VaR) calculations at 95% confidence
- Drawdown tracking with recovery monitoring
- Position validation before entry

##### 4. Backtesting Engine (`backtesting.py`)
Historical performance simulation:

**Features:**
- Single and multi-asset backtesting
- Transaction cost modeling (commissions + slippage)
- Position tracking with stop-loss/take-profit integration
- Equity curve generation

**Performance Metrics:**
- Sharpe Ratio (annualized)
- Sortino Ratio (downside deviation)
- Maximum Drawdown
- Total and Annualized Return
- Win Rate & Profit Factor

##### 5. Portfolio Correlation (`portfolio_correlation.py`)
Portfolio-level risk analysis:

- Pairwise correlation matrix calculation
- Rolling correlation windows
- Risk decomposition by asset (variance contribution)
- Over-concentration detection alerts
- Diversification scoring (0-1 scale)
- Low-correlation asset discovery
- Sector exposure analysis

#### Documentation Updates

- **README.md**: Complete API documentation with examples for all modules
- **IMPROVEMENTS.md**: Detailed feature summaries and use cases
- **Requirements.txt**: Updated with scikit-learn, matplotlib, seaborn dependencies

#### Testing Infrastructure

Added comprehensive test suite (`tests/test_modules.py`) with unit tests:
- All technical indicator calculations
- Each enhanced scan strategy
- Risk management strategies
- Portfolio correlation analysis
- Backtesting engine functionality

### Migration Notes

This is an additive release - all existing code remains compatible. The original Darvas Box detector continues to work unchanged. New modules can be integrated selectively or used together for comprehensive analysis.

### Example Integration

```python
from technical_indicators import TechnicalIndicators
from enhanced_scans import EnhancedScans
from risk_management import RiskManager, StopLossType

# Calculate indicators
indicators = TechnicalIndicators.calculate_all(close_prices, high_prices, low_prices, volume)

# Run multiple scans
results = {
    'momentum': EnhancedScans.momentum_filter_scan(df),
    'breakout': EnhancedScans.volatility_breakout_scan(df)
}

# Apply risk management to signals
for signal in results['momentum']['buy_signals']:
    stop_price = RiskManager.calculate_stop_loss(
        entry_price=signal['Close'],
        stop_type=StopLossType.ATR_BASED,
        price_data=current_prices
    )
```

### Breaking Changes

None - this release is fully backward compatible with existing code and the original Darvas Box detector functionality.

---

## [1.4.0] - 2026-04-XX (Previous Version)

- Async scanning support
- Enhanced detection algorithms
- Caching layer implementation

### See CHANGELOG.md for full version history
