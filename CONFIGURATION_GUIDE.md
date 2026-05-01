# Stock Scanner Configuration Guide
=====================================

This guide provides comprehensive instructions for configuring and using the enhanced stock scanner with all available features.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Trading Strategy Presets](#trading-strategy-presets)
4. [Configuration System](#configuration-system)
5. [Technical Indicators](#technical-indicators)
6. [Scan Types](#scan-types)
7. [Risk Management](#risk-management)
8. [Alerts & Notifications](#alerts--notifications)
9. [Chart Settings](#chart-settings)
10. [Example Configurations](#example-configurations)

---

## Overview

The enhanced stock scanner provides multiple scanning strategies, technical indicators, and configuration options to suit different trading styles from conservative mean reversion to aggressive momentum trading.

### Available Features

- **6 Scan Types**: Darvas Breakouts, Mean Reversion, Gap Analysis, Momentum, Relative Strength, Volume Patterns
- **8 Technical Indicators**: RSI, MACD, Bollinger Bands, ATR, ADX, EMA, Stochastic, Price Momentum
- **3 Risk Levels**: Conservative, Moderate, Aggressive
- **Multiple Trading Presets**: Pre-configured strategies for each scan type
- **Custom Configurations**: Override any parameter to fine-tune your strategy

---

## Quick Start

### 1. Install Dependencies

```bash
pip install pandas numpy yfinance plotly
```

### 2. Run with Default Settings

```bash
python scanner.py
```

### 3. Use a Trading Strategy Preset

```python
from configuration import get_full_config, ScanType

# Get Darvas Breakout preset config
config = get_full_config(preset_name='darvas_breakout')
print(config)
```

---

## Trading Strategy Presets

Each scan type has an optimized trading strategy:

### 1. Darvas Breakout Preset

- **Strategy**: Box breakout trading
- **Take Profit**: 6%
- **Stop Loss**: 4%
- **Position Size**: Kelly criterion (2 units)

```python
from configuration import Preset, get_full_config

config = get_full_config(preset_name='darvas_breakout')
config['scan_params']['min_breakout_strength'] = 'STRONG'  # Only strong breakouts
```

### 2. Mean Reversion Preset

- **Strategy**: RSI + Bollinger Bands reversal
- **Take Profit**: 3.5%
- **Stop Loss**: 2%
- **Position Size**: Smaller (1 unit) for mean reversion

```python
config = get_full_config(preset_name='mean_reversion')
# Configure RSI levels
config['scan_params']['mean_reversion_oversold'] = 25  # More sensitive
config['scan_params']['mean_reversion_overbought'] = 75
```

### 3. Momentum Trading Preset

- **Strategy**: Follow strong trends
- **Take Profit**: 8%
- **Stop Loss**: 5%
- **Position Size**: Larger (3 units) for momentum

```python
config = get_full_config(preset_name='momentum')
# Minimum 5% gain over 5 days
config['scan_params']['min_momentum_pct'] = 0.05
```

### 4. Gap Trading Preset

- **Strategy**: Trade significant gaps
- **Take Profit**: 4%
- **Stop Loss**: 2.5%
- **Gap Size**: Minimum 3% gap

```python
config = get_full_config(preset_name='gap_trading')
config['scan_params']['min_gap_size'] = 0.03
```

### 5. Relative Strength Preset

- **Strategy**: Outperform previous period
- **Take Profit**: 5%
- **Stop Loss**: 3.5%

```python
config = get_full_config(preset_name='relative_strength')
# Minimum relative strength of 3% over comparison period
config['scan_params']['min_relative_strength_pct'] = 3.0
```

### 6. Volume Pattern Preset

- **Strategy**: Volume spike confirmation
- **Take Profit**: 4.5%
- **Stop Loss**: 3%

```python
config = get_full_config(preset_name='volume_patterns')
config['scan_params']['sustained_volume_periods'] = 3
```

---

## Configuration System

### Default Configuration Structure

```python
{
    'trading': {
        'max_positions': 10,
        'min_position_size': 100,
        'max_position_size': 1000,
        'take_profit_percentage': 5.0,
        'stop_loss_percentage': 3.0,
        'trailing_stop_enabled': True,
        'trailing_stop_distance': 2.0,
    },
    'risk': {
        'risk_level': 'moderate',  # conservative/moderate/aggressive
        'max_portfolio_risk': 0.10,
        'position_sizing_method': 'kelly',
        'daily_loss_limit_pct': 5.0,
        'drawdown_limit_pct': 10.0,
    },
    'scan': {
        'darvas_window_size': 5,
        'darvas_min_volatility': 0.02,
        'mean_reversion_rsi_period': 14,
        'volume_spike_threshold': 2.0,
    },
    'alerts': {
        'breakout_alerts': True,
        'pattern_alerts': False,
        'daily_summary': True,
        'email_notifications': False,
    },
    'data': {
        'primary_source': 'yfinance',
        'interval': '1d',
        'period': '3mo',
    },
}
```

### Getting Full Configuration

```python
from configuration import get_full_config

# Default config
config = get_full_config()

# With preset
config = get_full_config(preset_name='darvas_breakout')

# Custom overrides
config = get_full_config(
    preset_name='mean_reversion',
    custom_params={
        'scan.mean_reversion_oversold': 25,
        'trading.take_profit_pct': 4.0,
    }
)
```

---

## Technical Indicators

### Available Indicators

All indicators are accessible via the `technical_indicators` module:

#### RSI (Relative Strength Index)

- **Period**: Default 14 days
- **Overbought**: 70+
- **Oversold**: 30-
- **Usage**: Identify overbought/oversold conditions

```python
from technical_indicators import TechnicalIndicators
import pandas as pd

indicators = TechnicalIndicators()
rsi_value = indicators.rsi(df['close'])
print(f"Current RSI: {rsi_value}")
```

#### MACD (Moving Average Convergence Divergence)

- **Fast Period**: 12
- **Slow Period**: 26
- **Signal Period**: 9
- **Usage**: Trend momentum and crossover signals

```python
macd = indicators.macd(df['close'])
print(f"MACD: {macd['macd']}, Signal: {macd['signal']}, Histogram: {macd['histogram']}")
```

#### Bollinger Bands

- **Period**: 20 days
- **Standard Deviations**: 2.0
- **Usage**: Volatility bands and mean reversion

```python
bb = indicators.bollinger_bands(df['close'])
print(f"Upper: {bb['upper']}, Middle: {bb['middle']}, Lower: {bb['lower']}")
```

#### ATR (Average True Range)

- **Period**: 14 days
- **Usage**: Volatility measurement for position sizing

```python
atr = indicators.atr(df['high'], df['low'], df['close'])
print(f"ATR: {atr}")
```

#### ADX (Average Directional Index)

- **Period**: 14 days
- **Strong Trend**: ADX > 25
- **Usage**: Trend strength measurement

```python
adx = indicators.adx(df['high'], df['low'], df['close'])
print(f"ADX: {adx['adx']}, +DI: {adx['plus_di']}, -DI: {adx['minus_di']}")
```

#### EMA (Exponential Moving Average)

- **Default Span**: 12 days
- **Usage**: Trend following

```python
ema_12 = indicators.exponential_moving_average(df['close'], span=12)
```

#### Stochastic Oscillator

- **%K Period**: 14
- **%D Period**: 3
- **Usage**: Momentum oscillator

```python
stoch = indicators.stochastic(df['high'], df['low'], df['close'])
print(f"Stoch %K: {stoch['k']}, %D: {stoch['d']}")
```

#### Price Momentum

- **Default Period**: 10 days
- **Usage**: Percentage price change over period

```python
momentum = indicators.momentum(df['close'], period=10)
print(f"10-Day Momentum: {momentum}%")
```

---

## Scan Types

### 1. Mean Reversion Scanner

Analyzes stocks for overbought/oversold conditions.

**Parameters:**
- `rsi_period`: RSI calculation period (default 14)
- `rsi_overbought`: Overbought threshold (default 70)
- `rsi_oversold`: Oversold threshold (default 30)
- `bb_period`: Bollinger Band period (default 20)

```python
from scan_types import MeanReversionScanner, ScanType

scanner = MeanReversionScanner(
    rsi_overbought=75,      # More conservative
    rsi_oversold=25         # More sensitive to dips
)
signals = scanner.analyze(df)
```

### 2. Gap Analysis Scanner

Detects significant gap up/down patterns.

**Parameters:**
- `gap_threshold`: Minimum gap size (default 0.025 = 2.5%)
- `min_gap_volume_multiplier`: Volume requirement for gaps (default 1.5)

```python
from scan_types import GapAnalysisScanner

scanner = GapAnalysisScanner(
    gap_threshold=0.03,     # Only 3%+ gaps
    min_gap_volume_multiplier=2.0  # High volume confirmation
)
signals = scanner.analyze(df)
```

### 3. Momentum Scanner

Identifies strong trending stocks.

**Parameters:**
- `momentum_period`: Lookback period (default 5 days)
- `min_momentum_pct`: Minimum momentum threshold (default 2%)

```python
from scan_types import MomentumScanner

scanner = MomentumScanner(
    momentum_period=5,      # 5-day momentum
    min_momentum_pct=0.04   # Only stocks with >4% gain
)
signals = scanner.analyze(df)
```

### 4. Relative Strength Scanner

Compares stock performance against previous period.

**Parameters:**
- `comparison_period`: Comparison lookback (default 5)

```python
from scan_types import RelativeStrengthScanner

scanner = RelativeStrengthScanner(
    comparison_period=7,    # Compare to 7 days ago
)
signals = scanner.analyze(df)
```

### 5. Volume Pattern Scanner

Identifies volume spikes and patterns.

**Parameters:**
- `spike_threshold`: Volume multiplier for spike (default 2.0)
- `sustained_volume_periods`: Minimum high volume periods (default 3)

```python
from scan_types import VolumePatternScanner

scanner = VolumePatternScanner(
    spike_threshold=1.8,   # Lower threshold to catch earlier
    sustained_volume_periods=5  # More confirmation required
)
signals = scanner.analyze(df)
```

### Running Multiple Scanners

```python
from scan_types import get_all_signals, ScanType

# Run all scanners
all_scanners = [ScanType.MEAN_REVERSION, ScanType.GAP_ANALYSIS]
signals = get_all_signals(df, scanners=all_scanners)

# Check for any signals
if signals:
    print(f"Found {len(signals)} signals")
    for signal in signals:
        print(f"- {signal['signal']}: {signal.get('price', '')}")
```

---

## Risk Management

### Risk Levels

Configure your risk tolerance using the `RiskLevel` enum:

```python
from configuration import RiskLevel, get_full_config

# Conservative: Lower position sizes, wider stops
conservative = get_full_config(
    preset_name='darvas_breakout',
    custom_params={
        'risk.risk_level': RiskLevel.CONSERVATIVE,
        'trading.position_size_units': 1,
    }
)

# Aggressive: Higher position sizes, tighter stops
aggressive = get_full_config(
    preset_name='momentum',
    custom_params={
        'risk.risk_level': RiskLevel.AGGRESSIVE,
        'trading.position_size_units': 4,
    }
)
```

### Position Sizing Methods

Available methods: `kelly`, `fixed`, `volatility_adjusted`

```python
from configuration import Configuration

# Kelly Criterion (recommended for most traders)
config = get_full_config(preset_name='darvas_breakout')
config['risk']['position_sizing_method'] = 'kelly'

# Fixed dollar amount per trade
config['risk']['position_sizing_method'] = 'fixed'
config['trading']['min_position_size'] = 1000
```

### Daily Loss Limit

Stop trading when daily loss reaches threshold:

```python
from configuration import get_full_config

config = get_full_config(preset_name='darvas_breakout')
config['risk']['daily_loss_limit_pct'] = 3.0  # Stop after -3%
config['risk']['drawdown_limit_pct'] = 8.0   # Stop after 8% drawdown
```

---

## Alerts & Notifications

### Alert Configuration

Enable different types of alerts:

```python
from configuration import get_full_config

config = get_full_config(preset_name='darvas_breakout')

# Enable all alert types
config['alerts']['breakout_alerts'] = True
config['alerts']['pattern_alerts'] = True
config['alerts']['daily_summary'] = True

# Enable email notifications (requires SMTP configuration)
config['alerts']['email_notifications'] = True
```

### Alert Channels

Configure which channels receive alerts:

```python
from configuration import Configuration

config = get_full_config()
config['alerts']['alert_channels'] = ['console', 'email', 'webhook']
```

---

## Chart Settings

Enable Plotly charts for visualization:

```python
from configuration import get_full_config

config = get_full_config(preset_name='darvas_breakout')
config['charts']['enable_plotly_charts'] = True
config['charts']['chart_width'] = 1000
config['charts']['chart_height'] = 700
```

---

## Example Configurations

### Configuration 1: Conservative Darvas Breakout Trader

```python
from configuration import get_full_config, RiskLevel

conservative_darvas = get_full_config(
    preset_name='darvas_breakout',
    custom_params={
        'trading.take_profit_pct': 5.0,   # Tighter targets
        'trading.stop_loss_pct': 3.0,     # Faster exits
        'risk.risk_level': RiskLevel.CONSERVATIVE,
        'risk.position_size_units': 1,    # Conservative position sizing
        'alerts.daily_summary': True,     # Daily reviews
    }
)
```

### Configuration 2: Aggressive Momentum Trader

```python
from configuration import get_full_config, ScanType, RiskLevel

aggressive_momentum = get_full_config(
    preset_name='momentum',
    custom_params={
        'scan.momentum_period': 3,        # Shorter momentum window
        'trading.take_profit_pct': 10.0,  # Let winners run
        'trading.stop_loss_pct': 4.0,     # Quick stops
        'risk.risk_level': RiskLevel.AGGRESSIVE,
        'risk.position_size_units': 3,    # Bigger positions
        'scan.volume_spike_threshold': 2.5,  # Volume confirmation
    }
)
```

### Configuration 3: Mean Reversion Day Trader

```python
from configuration import get_full_config, ScanType

mean_reversion_day = get_full_config(
    preset_name='mean_reversion',
    custom_params={
        'scan_type': ScanType.MEAN_REVERSION.value,
        'trading.take_profit_pct': 3.0,   # Small targets for day trading
        'trading.stop_loss_pct': 1.5,     # Very tight stops
        'risk.daily_loss_limit_pct': 3.0, # Stop early if losing
        'risk.drawdown_limit_pct': 6.0,   # Protect capital
    }
)

# Adjust RSI levels for intraday trading
mean_reversion_day['scan_params']['mean_reversion_rsi_period'] = 10  # Faster response
mean_reversion_day['scan_params']['mean_reversion_oversold'] = 35
mean_reversion_day['scan_params']['mean_reversion_overbought'] = 65
```

---

## Advanced Usage

### Custom Scanner Pipeline

Combine multiple scanners for enhanced filtering:

```python
from scan_types import MeanReversionScanner, GapAnalysisScanner
import pandas as pd

def multi_stage_filter(df):
    """Apply multiple scanner stages with decreasing thresholds."""
    
    # Stage 1: Mean reversion signals (loose)
    mr_signals = MeanReversionScanner().analyze(df)
    
    # Stage 2: Gap analysis (medium)
    gap_signals = GapAnalysisScanner(gap_threshold=0.03).analyze(df)
    
    # Combine results
    all_signals = {**{s['signal']: s for s in mr_signals}, **{s['signal']: s for s in gap_signals}}
    
    return list(all_signals.values())

# Usage
signals = multi_stage_filter(df)
for signal in signals:
    print(f"{signal['signal']}: {signal.get('price', '')}")
```

### Batch Configuration Testing

Test multiple configurations on historical data:

```python
from configuration import get_full_config, Presets
import pandas as pd
import numpy as np

def test_configuration(config_name: str, data: pd.DataFrame):
    """Test a configuration on sample data."""
    
    config = get_full_config(preset_name=config_name)
    signals = []
    
    try:
        # Get scanner for this preset
        scan_type = config['scan_params'].get('scan_type', 'darvas')
        
        if 'mean_reversion' in str(config):
            signals = MeanReversionScanner().analyze(data)
        elif 'gap' in str(config):
            signals = GapAnalysisScanner().analyze(data)
        
        return {
            'name': config_name,
            'signals_found': len(signals),
            'valid': True,
        }
    except Exception as e:
        return {
            'name': config_name,
            'error': str(e),
            'valid': False,
        }

# Test all presets
test_configs = ['darvas_breakout', 'mean_reversion', 'momentum']
results = [test_configuration(c, data) for c in test_configs]
```

---

## Saving and Loading Configuration

### Save to JSON File

```python
from configuration import get_full_config, save_config

config = get_full_config(
    preset_name='darvas_breakout',
    custom_params={'scan.darvas_window_size': 7}
)

save_config(config, 'my_strategy.json')
# Saves config to my_strategy.json
```

### Load from JSON File

```python
from configuration import load_config

config = load_config('my_strategy.json')
print(f"Loaded strategy: Darvas {config['scan_params'].get('darvas_window_size')}-day")
```

---

## Summary of All Available Presets

| Preset Name | Scan Type | Best For | Risk Profile | Take Profit | Stop Loss |
|-------------|-----------|----------|--------------|-------------|-----------|
| `darvas_breakout` | Breakouts | Trend following | Moderate | 6% | 4% |
| `mean_reversion` | RSI/BB | Swing trading | Conservative | 3.5% | 2% |
| `momentum` | Momentum | Strong trends | Aggressive | 8% | 5% |
| `gap_trading` | Gaps | Intraday opportunities | Moderate-Aggressive | 4% | 2.5% |
| `relative_strength` | RSI | Outperformance strategy | Conservative-Moderate | 5% | 3.5% |
| `volume_patterns` | Volume | Volume confirmation | Moderate | 4.5% | 3% |

---

## Troubleshooting

### Common Issues

1. **No signals found**: Adjust threshold parameters or check data quality
2. **Yfinance errors**: Ensure internet connection and yfinance is installed
3. **Slow performance**: Reduce `period` in data config or use smaller dataset for testing

### Performance Tips

- Use shorter data periods for intraday strategies
- Run scanners on subsets of stocks first
- Cache technical indicator calculations when possible

---

## Getting Support

For issues or feature requests:
- Check the README.md for basic usage
- Review example configurations above
- Test with sample data using `tests/test_scanner.py`

---

## License

This configuration guide is part of the Stock Scanner project and is released under the same license as the project.
