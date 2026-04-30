# Stock Scanner - Darvas Box Trading System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Automated stock scanner based on Richard Darvas's box trading methodology**. Identifies breakout opportunities in real-time using advanced technical analysis and provides actionable trading signals.

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/govindtank/stock-scanner.git
cd stock-scanner

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file with your settings:

```bash
# Core settings
DATA_SOURCE=yfinance
CASH=10000
COMMISSION=9.95
HOLDING_PERIOD_DAYS=7

# Darvas detector parameters
DARVAS_MIN_BOX_SIZE_PCT=8.0
DARVAS_VOLUMES_MULTIPLIER=1.5
DARVAS_BREAKOUT_THRESHOLD_PCT=0.8

# Cache configuration
CACHE_TTL_SECONDS=600
MAX_CONCURRENT_REQUESTS=5

# API settings
API_VERSION=v1
HOST=0.0.0.0
PORT=5000
```

### Running the Server

```bash
python app_enhanced.py
```

The API will be available at `http://localhost:5000`

## 📊 Features

### Core Capabilities

- ✅ **Darvas Box Detection** - Identify ascending box breakout patterns
- ✅ **Multi-Level Analysis** - Extended resistance zones and support levels
- ✅ **Async Scanning** - Concurrent analysis of multiple stocks
- ✅ **Caching Layer** - Redis-based caching for improved performance
- ✅ **Comprehensive API** - RESTful endpoints for all operations
- ✅ **Signal Scoring** - Confidence-based signal ranking
- ✅ **Portfolio Tracking** - Position management and P&L calculation

### Technical Indicators

- Simple Moving Averages (SMA5, SMA20)
- Relative Strength Index (RSI)
- Volume Ratio Analysis
- Average True Range (ATR)
- Box Height/Volume metrics

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/health` | GET | Health check |
| `/v1/health/metrics` | GET | Extended health with metrics |
| `/v1/box/<ticker>` | GET | Darvas box analysis for ticker |
| `/v1/scan` | GET | Batch scan for trading signals |
| `/v1/scan/batch` | POST | Custom batch scan with parameters |
| `/v1/validate/<ticker>` | GET | Validate ticker availability |
| `/v1/simulation` | POST | Backtest simulation |

### Python Usage

```python
from darvas_detector_enhanced import AdvancedDarvasDetector
from scanner_async import AsyncStockScanner
import asyncio

# Initialize detector
detector = AdvancedDarvasDetector(
    min_volume_ratio=1.5,
    breakout_threshold_pct=0.8,
    min_box_size_pct=8.0
)

# Initialize async scanner
scanner = AsyncStockScanner(
    max_concurrent=5,
    timeout_seconds=30
)

async def main():
    # Scan stocks asynchronously
    signals = await scanner.scan(symbols=['AAPL', 'MSFT', 'GOOGL'], top_n=10)
    
    # Get box analysis for single stock
    hist = get_historical_data('AAPL')
    result = detector.detect_boxes(hist)
    
    print(f"Found {len(signals)} signals")
    for signal in signals:
        print(f"  {signal['ticker']}: {signal['signal']} "
              f"(confidence={signal['confidence']:.2f})")

asyncio.run(main())
```

## 🔧 Trading Rules (Darvas Methodology)

1. **Buy** when price breaks above previous box high with volume confirmation
2. **Sell** when price breaks below previous box low
3. **Trade in rising markets only** - higher lows, no pullbacks
4. **Minimum box size**: 8% of entry price
5. **Volume confirmation**: 100%+ above average volume

### Signal Types

| Signal | Confidence Range | Description |
|--------|-----------------|-------------|
| `strong_buy` | ≥ 85% | High probability breakout with strong indicators |
| `buy` | 70-84% | Good setup, enter on confirmation |
| `neutral` | 30-69% | Monitor for development |
| `sell` | 25-29% | Consider taking profits or reducing position |
| `strong_sell` | < 25% | Breakdown below support |

## 📈 Advanced Features

### Multi-Level Box Detection

The enhanced detector identifies:
- **Primary Level**: Current ascending box
- **Extended Resistance**: Higher breakout targets with historical volume
- **Support Zones**: Key support levels for stop-loss placement

```python
result = detector.detect_boxes(historical_data)
if result and result.get('with_extended_levels'):
    levels = result['with_extended_levels']['resistance']
    for level in levels:
        print(f"Extended resistance: ${level['price']} ({level['level']})")
```

### Volume Analysis

- Detects high-volume breakout days
- Identifies volume nodes at key price levels
- Filters low-volume false breakouts

### Box Continuity Check

Monitors for ascending pattern integrity:
```python
continuity = detector.check_box_continuity(historical_data, current_low)
print(f"Continuity ratio: {continuity['continuity_ratio']:.1%}")
```

## 🏗️ Architecture

### Modules

- **app_enhanced.py** - Flask API server with caching and error handling
- **scanner_async.py** - Async stock scanning with rate limiting
- **darvas_detector_enhanced.py** - Advanced Darvas box detection with multi-level support

### Data Flow

1. User requests scan → `/v1/scan`
2. Scanner fetches historical data (with caching)
3. Detector identifies Darvas boxes
4. Indicators calculated (RSI, SMA, volume ratio)
5. Signal scored and ranked by confidence
6. Results returned with extended levels

### Caching Strategy

- Stock data cached for TTL seconds (default: 600s)
- Box analysis cached per ticker
- Health metrics cached separately

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v --cov=.

# With coverage report
pytest tests/ --cov=. --cov-report=html
```

### Example Test

```python
# tests/test_darvas_detector.py
import pytest
from darvas_detector_enhanced import AdvancedDarvasDetector, create_mock_rising_stock

def test_detect_box():
    detector = AdvancedDarvasDetector(min_volume_ratio=1.5)
    mock_data = create_mock_rising_stock(days=60)
    
    result = detector.detect_boxes(mock_data)
    
    assert result['detected'] is True
    assert result['current_box']['days'] >= 3

def test_no_box_choppy():
    detector = AdvancedDarvasDetector()
    mock_data = create_mock_choppy_stock(days=60)
    
    result = detector.detect_boxes(mock_data)
    
    assert result is None or not result.get('detected')
```

## 🌐 API Examples

### Scan for Signals

```bash
# Scan popular tech stocks
curl "http://localhost:5000/v1/scan?top_n=10"

# Specific symbols
curl "http://localhost:5000/v1/scan?symbols=AAPL,MSFT,GOOGL,TSLA,top_n=5"
```

### Get Box Analysis

```bash
curl "http://localhost:5000/v1/box/AAPL"
```

### Batch Scan with Custom Config

```bash
curl -X POST http://localhost:5000/v1/scan/batch \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "cash": 100000,
    "commission": 10,
    "top_n": 5
  }'
```

### Backtest Simulation

```bash
curl -X POST http://localhost:5000/v1/simulation \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 10000,
    "signal_threshold": 0.7
  }'
```

## 🚀 Performance Optimizations

### Async Support

Scans multiple stocks concurrently with configurable concurrency:
```python
scanner = AsyncStockScanner(max_concurrent=5)
```

### Rate Limiting

For paid API sources, implements burst-based rate limiting:
```python
scanner.rate_limit_delay = 0.1  # seconds between requests
scanner.burst_size = 10         # requests per burst
```

### Caching

Uses Flask-Caching with Redis (or in-memory fallback):
```python
CACHE_TTL_SECONDS=600          # Cache TTL for box analysis
CACHE_DEFAULT_TIMEOUT=30        # Health check cache TTL
```

## 🔒 Error Handling

The API includes comprehensive error handling:

- **400 Bad Request** - Invalid parameters
- **404 Not Found** - Ticker not found or no data
- **500 Server Error** - Internal errors with logging
- **504 Gateway Timeout** - Scan operation exceeded timeout

### Error Response Format

```json
{
  "status": "error",
  "message": "Description of the error"
}
```

## 📊 Monitoring

Health endpoints provide operational metrics:

```bash
curl "http://localhost:5000/v1/health/metrics"
```

Response includes:
- Service status
- Cache hit/miss rates
- Average scan time
- Component health status

## 🛠️ Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt

# Run with debug mode
FLASK_DEBUG=true python app_enhanced.py
```

### Adding New Indicators

Edit `scanner_async.py` and add to `_calculate_signal_async`:
```python
def calculate_macd(self, hist):
    """Calculate MACD"""
    from talib import MACD_FULL历史 as macd  # or custom implementation
    ...
```

### Customizing Detector Parameters

Set in `.env`:
```bash
DARVAS_MIN_BOX_SIZE_PCT=10.0  # Larger boxes only
DARVAS_VOLUMES_MULTIPLIER=2.0  # Require higher volume
DARVAS_BREAKOUT_THRESHOLD_PCT=1.5  # 1.5% breakout minimum
```

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📚 References

- [Richard Darvas Trading System](https://en.wikipedia.org/wiki/Richard_Darvas)
- [Natenberg's Box Theory](https://www.natenberg.com/stock-market-insights/box-theory/)
- [TA-Lib Documentation](http://ta-lib.org/)

## 🔮 Roadmap

- [ ] WebSocket support for real-time price updates
- [ ] Machine learning signal enhancement
- [ ] Multi-exchange support (NYSE, NASDAQ, NAS)
- [ ] Paper trading integration
- [ ] Advanced backtesting engine with daily bars
- [ ] Portfolio risk management module
- [ ] Alert system for breakout events

---

**Built with ❤️ for active traders**
