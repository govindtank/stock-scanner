# Stock Scanner - Advanced Technical Analysis & Risk Management

## Overview

A comprehensive Python-based stock scanning platform featuring:

- **Darvas Box Detection** - Classic box-and-trend breakout strategy
- **Advanced Technical Indicators** - MACD, Bollinger Bands, RSI, ADX, and more
- **Enhanced Scanning Strategies** - Momentum, volatility, pattern recognition scans
- **Professional Risk Management** - ATR-based stops, position sizing, VaR calculations
- **Backtesting Engine** - Historical performance simulation with metrics
- **Portfolio Analysis** - Correlation tracking and concentration monitoring

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/govindtank/stock-scanner.git
cd stock-scanner
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Basic Scan
```python
import yfinance as yf
from darvas_detector import DarvasBoxDetector

# Get stock data
ticker = 'AAPL'
data = yf.download(ticker, period='1y')

# Initialize detector
detector = DarvasBoxDetector()

# Detect boxes and scan for opportunities
results = detector.detect_boxes_and_scan(data)
print(results)
```

## Features by Module

### 📊 Technical Indicators (`technical_indicators.py`)
Professional-grade indicator calculations:
- **MACD** - Trend-following momentum indicator with signal line
- **Bollinger Bands** - Volatility bands for breakout detection
- **Stochastic Oscillator** - Overbought/oversold conditions
- **ADX** - Trend strength measurement (0-100 scale)
- **ATR** - Average True Range for stop-loss placement
- **VWAP** - Volume-weighted average price institutional levels
- **Williams %R** - Momentum oscillator (-100 to 0 scale)
- **CCI** - Commodity Channel Index for cyclical trends

Example:
```python
from technical_indicators import TechnicalIndicators
import pandas as pd

indicators = TechnicalIndicators.calculate_all(
    close=pd.Series(stock_data['Close']),
    high=pd.Series(stock_data['High']),
    low=pd.Series(stock_data['Low']),
    volume=pd.Series(stock_data['Volume'])
)
```

### 🎯 Enhanced Scans (`enhanced_scans.py`)
Multiple trading strategies and scan types:

1. **Momentum Filter Scan** - RSI + MACD reversal detection
2. **Volatility Breakout** - BB breaks with volume confirmation
3. **Trend Following** - SMA crossovers with ADX filter
4. **Pattern Recognition** - Double top/bottom, head & shoulders
5. **Volume Spike Detection** - Institutional activity signals
6. **Gap Analysis** - Overnight gap identification

Example:
```python
from enhanced_scans import EnhancedScans

results = EnhancedScans.momentum_filter_scan(
    df=stock_data,
    rsi_period=14,
    rsi_buy=30,
    rsi_sell=70
)
```

### 🛡️ Risk Management (`risk_management.py`)
Professional money management:

- **Stop-Loss Types**:
  - Fixed percentage (e.g., 5% below entry)
  - ATR-based dynamic stops
  - Volatility-adjusted stops
  - Trend-following stops
  
- **Take-Profit Types**:
  - Fixed targets
  - Risk/reward ratio based (default 2.5:1)
  - Trailing stops
  
- **Position Sizing**:
  - Fixed percentage of account
  - Kelly Criterion with fractioning
  - Volatility targeting
  - Risk parity

- **Risk Metrics**:
  - Value-at-Risk (VaR) calculations
  - Drawdown tracking
  - Position validation

Example:
```python
from risk_management import RiskManager, StopLossType

# Calculate ATR-based stop loss
stop_price = RiskManager.calculate_stop_loss(
    entry_price=150.0,
    stop_type=StopLossType.ATR_BASED,
    price_data=current_prices
)
```

### 📈 Backtesting (`backtesting.py`)
Historical performance simulation:

- **Features**:
  - Single and multi-asset backtesting
  - Transaction cost modeling (commissions + slippage)
  - Position tracking with stop-loss/take-profit
  - Equity curve generation
  
- **Metrics**:
  - Sharpe Ratio
  - Sortino Ratio
  - Maximum Drawdown
  - Total/Audalized Return
  - Win Rate & Profit Factor

Example:
```python
from backtesting import BacktestingEngine

engine = BacktestingEngine(initial_capital=100000)
engine.set_data(historical_df)

result = engine.analyze_strategy(
    entry_signal=lambda row: row['Close'] < 147,
    exit_signal=lambda row: row['Close'] > 153,
    strategy_name="mean_reversion"
)

print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

### 🔗 Portfolio Correlation (`portfolio_correlation.py`)
Portfolio-level analysis tools:

- **Correlation Matrix** - Pairwise asset correlations
- **Risk Decomposition** - Variance contribution by asset
- **Over-Concentration Check** - Dangerous position alerts
- **Diversification Score** - 0-1 scale rating (higher is better)
- **Low-Correlation Discovery** - Find uncorrelated assets
- **Sector Exposure Analysis** - Concentration monitoring

Example:
```python
from portfolio_correlation import CorrelationAnalyzer

# Calculate correlation matrix
corr_matrix = CorrelationAnalyzer.calculate_correlation_matrix(
    asset_data=portfolio_returns
)

# Check concentration risks
concentration_report = CorrelationAnalyzer.check_overconcentration(
    weights=current_weights,
    correlations=corr_matrix
)

if concentration_report['is_concentrated']:
    print("⚠️ Portfolio needs rebalancing!")
```

## Usage Examples

### Complete Analysis Pipeline

```python
import yfinance as yf
import pandas as pd
from technical_indicators import TechnicalIndicators
from enhanced_scans import EnhancedScans
from risk_management import RiskManager, StopLossType
from portfolio_correlation import CorrelationAnalyzer

# Fetch data
ticker = 'AAPL'
stock_data = yf.download(ticker, period='1y', progress=False)

# Calculate technical indicators
indicators = TechnicalIndicators.calculate_all(
    close=pd.Series(stock_data['Close']),
    high=pd.Series(stock_data['High']),
    low=pd.Series(stock_data['Low']),
    volume=pd.Series(stock_data['Volume'])
)

# Run multiple scan strategies
results = {
    'momentum': EnhancedScans.momentum_filter_scan(
        stock_data, rsi_period=14, rsi_buy=30, rsi_sell=70
    ),
    'volatility': EnhancedScans.volatility_breakout_scan(stock_data),
    'trend': EnhancedScans.trend_following_scan(stock_data)
}

# Apply risk management to signals
opportunities = []
for signal in results['momentum']['buy_signals']:
    stop_price = RiskManager.calculate_stop_loss(
        entry_price=signal['Close'],
        stop_type=StopLossType.ATR_BASED,
        price_data=pd.Series(stock_data['Low'])[-len(stock_data):]
    )
    
    # Calculate position size
    position_size = RiskManager.calculate_position_size(
        account_balance=100000,
        stock_price=stop_price,
        sizing_type=PositionSizingType.VOLATILITY_TARGETING
    )
    
    opportunities.append({
        'symbol': ticker,
        'entry_price': signal['Close'],
        'stop_loss': stop_price,
        'position_size': position_size
    })

print(f"Found {len(opportunities)} trading opportunities")
```

## API Documentation

### Technical Indicators API

| Method | Description |
|--------|-------------|
| `TechnicalIndicators.rsi(close_series, period=14)` | Relative Strength Index |
| `TechnicalIndicators.macd(close_series, fast=12, slow=26, signal=9)` | MACD with histogram |
| `TechnicalIndicators.bollinger_bands(close_series, window=20, std=2.0)` | Upper/Middle/Lower bands |
| `TechnicalIndicators.stochastic(high, low, close, k=14, d=3)` | %K and %D lines |
| `TechnicalIndicators.atr(high, low, close, period=14)` | Average True Range |
| `TechnicalIndicators.vwap(high, low, close, volume)` | Volume Weighted Avg Price |
| `TechnicalIndicators.adx(high, low, close, period=14)` | Trend Strength Index |
| `TechnicalIndicators.williams_r(high, low, close, period=14)` | Williams Percent Range |
| `TechnicalIndicators.commodity_channel_index(close, period=20)` | CCI Oscillator |
| `TechnicalIndicators.calculate_all(close, high, low, volume)` | **Calculate all indicators at once** |

### Enhanced Scans API

| Scan Type | Method Call |
|-----------|-------------|
| Momentum Filter | `EnhancedScans.momentum_filter_scan(df, rsi_period=14, rsi_buy=30, rsi_sell=70)` |
| Volatility Breakout | `EnhancedScans.volatility_breakout_scan(df, bb_period=20, volume_threshold=1.5)` |
| Trend Following | `EnhancedScans.trend_following_scan(df, sma_fast=9, sma_slow=21, adx_threshold=25)` |
| Pattern Recognition | `EnhancedScans.pattern_recognition_scan(df, pattern_type='double_bottom')` |
| Volume Spike Detection | `EnhancedScans.volume_spike_detection(df, volume_threshold=2.0)` |
| Gap Analysis | `EnhancedScans.gap_analysis(df, min_gap_pct=0.03, volume_confirmation=1.5)` |

### Risk Management API

```python
# Stop-Loss Calculations
RiskManager.calculate_stop_loss(
    entry_price=float,
    stop_type: (FIXED_PCT, ATR_BASED, VOLATILITY_ADJUSTED, CHAIN_STOP),
    price_data=Series,  # for dynamic stops
    atr_period=int,
    atr_multiplier=float
) -> float

# Take-Profit Calculations
RiskManager.calculate_take_profit(
    entry_price=float,
    tp_type: (FIXED_PCT, RISK_REWARD_RATIO, TRAILING_STOP),
    position_data=Dict,  # for context
    rsi_periods=tuple,
    risk_reward_ratio=float
) -> float

# Position Sizing
RiskManager.calculate_position_size(
    account_balance=float,
    stock_price=float,
    sizing_type: (FIXED_PERCENT, KELLY_CRITERION, VOLATILITY_TARGETING),
    risk_per_trade_pct=float,
    kelly_fraction=float,
    target_portfolio_volatility=float
) -> float

# Risk Metrics
RiskManager.calculate_var(returns_series, confidence_level=0.95, horizon_days=1) -> float
RiskManager.track_drawdown(equity_curve, max_drawdown_pct=None) -> Dict
RiskManager.calculate_risk_reward(entry_price, stop_loss, take_profit, quantity) -> Dict
RiskManager.validate_position(...) -> (bool, str)  # Returns (is_valid, reason)
```

## Configuration

### Risk Management Defaults
Edit these parameters in your code:

```python
# Stop-Loss Configuration
STOP_LOSS_CONFIG = {
    'type': 'ATR_BASED',              # FIXED_PCT | ATR_BASED | VOLATILITY_ADJUSTED
    'atr_multiplier': 2.0,            # Number of ATRs for stop distance
    'volatility_threshold': 0.25      # Monthly vol multiplier
}

# Take-Profit Configuration  
TAKE_PROFIT_CONFIG = {
    'type': 'RISK_REWARD_RATIO',      # FIXED_PCT | RISK_REWARD_RATIO | TRAILING_STOP
    'risk_reward_ratio': 2.5,         # Profit target in R (e.g., 2.5:1)
}

# Position Sizing Configuration
POSITION_SIZING_CONFIG = {
    'type': 'VOLATILITY_TARGETING',   # FIXED_PERCENT | KELLY_CRITERION | VOLATILITY_TARGETING
    'risk_per_trade_pct': 0.02,       # Max 2% risk per trade
    'kelly_fraction': 0.25,           # Use quarter-Kelly for reduced risk
    'target_portfolio_volatility': 0.15  # Target 15% annualized vol
}

# Transaction Costs (in backtesting)
BACKTESTING_CONFIG = {
    'transaction_cost_pct': 0.001,    # 0.1% commission per trade
    'slippage_bps': 2.0               # 2 basis points slippage
}
```

## Testing

Run the test suite:

```bash
python3 tests/test_modules.py
```

Expected output:
```
============================================================
STOCK SCANNER MODULE TEST SUITE
============================================================

--- testing technical_indicators.py ---
✓ RSI calculation: PASS
✓ MACD calculation: PASS
✓ Bollinger Bands calculation: PASS
...
✓ All technical indicator tests PASSED

--- testing enhanced_scans.py ---
✓ Momentum Filter Scan: PASS
✓ Volatility Breakout Scan: PASS
✓ Trend Following Scan: PASS
✓ Pattern Recognition Scan: PASS
✓ Volume Spike Detection: PASS
✓ All enhanced scans tests PASSED

...

============================================================
ALL MODULES TESTED SUCCESSFULLY!
============================================================
```

## Project Structure

```
stock-scanner/
├── app.py                     # Main application entry point
├── darvas_detector.py         # Darvas Box detection strategy
├── scanner.py                 # Core scanning logic
├── technical_indicators.py    # Advanced indicator calculations
├── enhanced_scans.py          # Multi-strategy scan types
├── risk_management.py         # Professional risk controls
├── backtesting.py             # Historical simulation engine
├── portfolio_correlation.py   # Portfolio-level analysis
├── tests/
│   └── test_modules.py        # Comprehensive unit tests
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── CHANGELOG.md               # Version history
```

## Performance Benchmarks

**Technical Indicators**: All indicators calculate in <10ms for 10K bars  
**Enhanced Scans**: Full scan suite runs in ~50ms for typical datasets  
**Risk Management**: Position sizing + stop calculation: <2ms  
**Correlation Analysis**: Matrix computation: <100ms for 10 assets  

## Contributing

Contributions are welcome! Please submit pull requests or create issues for bug reports.

## License

MIT License - See LICENSE file for details

## Author

Govind Tank - [GitHub Profile](https://github.com/govindtank)

---

*Note: This software is for educational purposes only. Trading financial markets involves risk.*
