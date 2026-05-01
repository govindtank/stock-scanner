# Stock Scanner - Enhanced Features & Improvements

## Overview
This stock scanner project has been enhanced with advanced technical analysis capabilities, multiple detection strategies, risk management tools, and comprehensive testing.

## New Modules Added

### 1. `technical_indicators.py`
**Purpose**: Advanced technical indicator calculations beyond basic SMA/RSI

**Features Implemented**:
- **MACD**: Moving Average Convergence Divergence with customizable periods (fast: 12, slow: 26, signal: 9)
- **Bollinger Bands**: Volatility bands with upper/middle/lower bounds
- **Stochastic Oscillator**: %K and %D for momentum detection
- **ADX**: Average Directional Index for trend strength
- **ATR**: Average True Range for volatility measurement
- **VWAP**: Volume Weighted Average Price
- **Williams %R**: Momentum oscillator (-100 to 0 scale)
- **CCI**: Commodity Channel Index (cyclical momentum)

**Key Benefits**:
- More accurate entry/exit signals
- Better risk adjustment based on volatility
- Comprehensive market regime detection

### 2. `enhanced_scans.py`
**Purpose**: Advanced scanning strategies combining multiple indicators

**Scan Types Implemented**:
1. **Momentum Filter Scan**
   - Combines RSI oversold/overbought with MACD momentum reversal
   - Trend filter using price vs VWAP relationship

2. **Volatility Breakout Detection**
   - Detects breakouts beyond Bollinger Bands with volume confirmation
   - Calculates breakout strength and distance from bands

3. **Trend Following Strategy**
   - Moving average crossover (9/21 period)
   - ADX trend strength filter (>25 for strong trends)
   - Stop-loss based on ATR

4. **Pattern Recognition**
   - Double Top (M-pattern) detection
   - Double Bottom (W-pattern) detection
   - Head and Shoulders (simplified)

5. **Volume Spike Detection**
   - Identifies 2x+ average volume days
   - Price confirmation (minimum 3% move)

6. **Gap Analysis**
   - Overnight opening gap detection (>3%)
   - Volume confirmation for institutional activity
   - Tracks gap fill patterns

**Key Benefits**:
- Multiple trading strategies in one framework
- Pattern-based opportunity identification
- Institutional activity signals via volume analysis

### 3. `risk_management.py`
**Purpose**: Professional risk controls and position sizing

**Features Implemented**:

**Stop-Loss Strategies**:
- Fixed percentage (e.g., 5% below entry)
- ATR-based (dynamic volatility adjustment)
- Volatility-adjusted (monthly vol targeting)
- Chain stop (tightening over time)
- Trend-following (below short-term SMA)

**Take-Profit Strategies**:
- Fixed percentage targets
- Risk/reward ratio based (default 2.5:1)
- Trailing stops with configurable distance
- RSI-based reversal detection

**Position Sizing**:
- Fixed percentage of account (e.g., 10%)
- Kelly Criterion (with fractioning for reduced risk)
- Volatility targeting (achieve target portfolio vol)
- Risk parity (equal risk contribution)

**Risk Metrics**:
- Value-at-Risk (VaR) calculations
- Drawdown tracking with recovery monitoring
- Position validation before entry

**Key Benefits**:
- Prevents catastrophic losses
- Consistent risk-adjusted returns
- Professional money management practices

### 4. `backtesting.py`
**Purpose**: Historical performance simulation

**Features Implemented**:
- Single and multi-asset backtesting engines
- Position tracking with entry/exit management
- Transaction cost modeling (commissions + slippage)
- Performance metrics:
  - Sharpe Ratio
  - Sortino Ratio
  - Maximum Drawdown
  - Total/Audalized Return
  - Win Rate & Profit Factor
- Equity curve generation

**Key Benefits**:
- Test strategies on historical data
- Validate risk-adjusted returns
- Optimize strategy parameters before live trading

### 5. `portfolio_correlation.py`
**Purpose**: Portfolio-level analysis and concentration monitoring

**Features Implemented**:
- Pairwise correlation matrix calculation
- Rolling correlation windows
- Risk decomposition by asset (variance contribution)
- Over-concentration detection:
  - Single position >50% alerts
  - Correlated cluster warnings
- Diversification scoring (0-1 scale)
- Low-correlation asset discovery
- Sector exposure analysis

**Key Benefits**:
- Identify dangerous concentration risks
- Optimize asset allocation
- True diversification measurement
- Prevent sector over-exposure

## Improvements to Existing Files

### `scanner.py` - Updated for New Modules
- Now imports from new technical indicator modules
- Supports multiple scan types via enhanced_scans
- Risk management integration for position sizing

### `darvas_detector.py` - Enhanced with Technical Filters
- Added optional RSI and volume filters
- Can combine Darvas box with trend detection
- Improved breakout confirmation

### `app.py` - Streamlined Interface
- Cleaner API for calling new modules independently
- Batch indicator calculation support
- Risk-adjusted returns reporting

## Usage Examples

### Basic Technical Indicator Calculation
```python
from technical_indicators import TechnicalIndicators
import pandas as pd

# Calculate all indicators at once
result = TechnicalIndicators.calculate_all(
    close=pd.Series(data['Close']),
    high=pd.Series(data['High']),
    low=pd.Series(data['Low']),
    volume=pd.Series(data['Volume'])
)

# Access specific indicator
print(result['rsi'].iloc[-1])
print(result['macd_line'].iloc[-1])
```

### Momentum Filter Strategy
```python
from enhanced_scans import EnhancedScans

# Run momentum filter scan
result = EnhancedScans.momentum_filter_scan(
    df,
    rsi_period=14,
    rsi_buy=30,
    rsi_sell=70
)

# Get buy signals
buy_signals = result['buy_signals']
print(f"Found {len(buy_signals)} buy opportunities")
```

### Risk-Aware Position Sizing
```python
from risk_management import RiskManager, StopLossType

# Calculate stop-loss based on ATR
stop_loss = RiskManager.calculate_stop_loss(
    entry_price=150.0,
    stop_type=StopLossType.ATR_BASED,
    price_data=current_prices
)

# Calculate appropriate position size
position_size = RiskManager.calculate_position_size(
    account_balance=100000,
    stock_price=stop_loss,
    sizing_type=PositionSizingType.VOLATILITY_TARGETING
)
```

### Backtest a Strategy
```python
from backtesting import BacktestingEngine

engine = BacktestingEngine(initial_capital=100000)
engine.set_data(historical_df)

result = engine.analyze_strategy(
    entry_signal=lambda row: row['Close'] < 147,  # Example signal
    exit_signal=lambda row: row['Close'] > 153,
    strategy_name="mean_reversion"
)

print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown*100:.1f}%")
```

### Portfolio Correlation Analysis
```python
from portfolio_correlation import CorrelationAnalyzer

# Calculate correlation matrix
corr_matrix = CorrelationAnalyzer.calculate_correlation_matrix(
    asset_data=portfolio_returns
)

# Check for concentration issues
concentration_report = CorrelationAnalyzer.check_overconcentration(
    weights=current_portfolio_weights,
    correlations=corr_matrix
)

if concentration_report['is_concentrated']:
    print("⚠️ Portfolio is over-concentrated!")
```

## Testing

### Running Tests
```bash
python3 tests/test_modules.py
```

Tests cover:
- All technical indicator calculations
- Each enhanced scan type
- Risk management strategies
- Portfolio correlation analysis
- Backtesting engine functionality

## Installation

```bash
pip install -r requirements.txt
```

### Dependencies
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical operations
- `yfinance>=0.2.27` - Optional: Stock data fetching (for demo)
- `scikit-learn>=1.3.0` - Statistical functions
- `matplotlib>=3.7.0` - Visualization
- `seaborn>=0.12.0` - Enhanced plotting

## Git Commits Made

### Initial Setup
```bash
git add darvas_detector.py scanner.py app.py requirements.txt README.md
git commit -m "feat: Add Darvas Box detection and basic scanning framework"
git push -u origin main
```

### Phase 1: Technical Indicators & Enhanced Scans
```bash
git add technical_indicators.py enhanced_scans.py tests/test_modules.py
git commit -m "feat: Add comprehensive technical indicators and enhanced scan strategies

- technical_indicators.py implements MACD, Bollinger Bands, Stochastic,
  ADX, ATR, VWAP, Williams %R, and CCI for professional-level analysis
  
- enhanced_scans.py provides 6 scan types: momentum filter, volatility breakout,
  trend following, pattern recognition (double top/bottom, head & shoulders),
  volume spike detection, and gap analysis

- Full test suite added with unit tests for all new functionality"
git push -u origin main
```

### Phase 2: Risk Management & Backtesting
```bash
git add risk_management.py backtesting.py portfolio_correlation.py tests/test_modules.py README.md
git commit -m "feat: Add professional risk management and backtesting capabilities

- risk_management.py implements ATR-based stop-loss, risk/reward ratios,
  Kelly criterion position sizing, VaR calculations, and drawdown monitoring
  
- backtesting.py provides historical performance simulation with Sharpe/Sortino
  ratios, equity curves, and transaction cost modeling
  
- portfolio_correlation.py adds concentration analysis, diversification scoring,
  and over-concentration detection to prevent dangerous portfolio exposures

- All modules include comprehensive docstrings and example usage"
git push -u origin main
```

## Future Enhancement Opportunities

1. **Machine Learning Integration**
   - Add LSTM/Transformer models for price prediction
   - Neural network-based signal generation
   - Automated strategy optimization via reinforcement learning

2. **Advanced Chart Patterns**
   - Wyckoff methods analysis
   - Elliott Wave pattern detection
   - Candlestick pattern recognition (doji, hammer, engulfing)

3. **Options Integration**
   - Greeks calculation (Delta, Gamma, Theta, Vega)
   - Option chain scanning for hedging opportunities
   - Implied volatility surface analysis

4. **News Sentiment Analysis**
   - Real-time news aggregation
   - NLP-based sentiment scoring
   - Event-driven trading triggers

5. **Multi-Timeframe Analysis**
   - Cross-timeframe confirmation (daily + hourly signals)
   - Fibonacci level integration
   - Supply/demand zone mapping

## License

MIT License - See LICENSE file for details
