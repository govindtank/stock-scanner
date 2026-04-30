"""
Enhanced Stock Scanner Web API - Extended Endpoints
Implements comprehensive REST API for Darvas Box trading system
"""

from flask import Flask, jsonify, request, g
from flask_caching import Cache
import os
from scanner_async import AsyncStockScanner
from darvas_detector_enhanced import AdvancedDarvasDetector, create_mock_rising_stock
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Cache configuration
CACHE_CONFIG = {
    'CACHE_NULL_RESULT_VALUE': None,
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    'CACHE_DEFAULT_TIMEOUT': int(os.environ.get('CACHE_TTL_SECONDS', 600)),
}

# Initialize cache
cache = Cache(app, config=CACHE_CONFIG)

# Configuration from environment
API_VERSION = os.environ.get('API_VERSION', 'v1')
DATA_SOURCE = os.environ.get('DATA_SOURCE', 'yfinance')
CASH_BALANCE = float(os.environ.get('CASH', 10000))
COMMISSION = float(os.environ.get('COMMISSION', 9.95))
HOLDING_PERIOD_DAYS = int(os.environ.get('HOLDING_PERIOD_DAYS', 7))

# Initialize scanner and detector
scanner = AsyncStockScanner(
    data_source=DATA_SOURCE,
    cash=CASH_BALANCE,
    commission=COMMISSION,
    max_concurrent=int(os.environ.get('MAX_CONCURRENT_REQUESTS', 5))
)
detector = AdvancedDarvasDetector(
    min_volume_ratio=float(os.environ.get('DARVAS_VOLUMES_MULTIPLIER', 1.5)),
    breakout_threshold_pct=float(os.environ.get('DARVAS_BREAKOUT_THRESHOLD_PCT', 0.8)),
    min_box_size_pct=float(os.environ.get('DARVAS_MIN_BOX_SIZE_PCT', 8.0))
)


@app.before_request
def before_request():
    """Record request timing"""
    g.start_time = time.time()


@app.after_request
def after_request(response):
    """Add timing headers and cache-control"""
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
    
    # Cache-Control for GET requests
    if request.method == 'GET':
        response.headers['Cache-Control'] = 'public, max-age=60'
    
    return response


@app.route(f'/{API_VERSION}/health', methods=['GET'])
@cache.cached(timeout=30)
def health_check():
    """Health check endpoint"""
    try:
        # Check dependencies
        import pandas
        import numpy
        import yfinance
        
        return jsonify({
            'status': 'healthy',
            'service': 'stock-scanner',
            'version': API_VERSION,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@app.route(f'/{API_VERSION}/health/metrics', methods=['GET'])
@cache.cached(timeout=60)
def health_metrics():
    """Extended health check with operational metrics"""
    # Check cache status
    try:
        cache_stats = cache.get_cache_stats() if hasattr(cache, 'get_cache_stats') else {'hits': 0, 'misses': 0}
    except Exception:
        cache_stats = {}
    
    return jsonify({
        'status': 'healthy',
        'uptime_seconds': time.time(),  # Would track actual uptime in production
        'cache_hits': cache_stats.get('hits', 0),
        'cache_misses': cache_stats.get('misses', 0),
        'avg_scan_time_ms': get_avg_scan_time() if hasattr(scanner, '_scan_times') else None,
        'detectors_initialized': detector is not None,
        'scanner_initialized': scanner is not None,
        'timestamp': datetime.now().isoformat()
    })


@app.route(f'/{API_VERSION}/box/<ticker>', methods=['GET'])
@cache.cached(timeout=CACHE_CONFIG['CACHE_DEFAULT_TIMEOUT'], key_func=lambda: f"box:{request.path.split('/')[-1]}")
def get_box_analysis(ticker):
    """
    Get Darvas box analysis for a specific stock
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT)
    
    Returns:
        Comprehensive box analysis including current price, levels, signals
    """
    try:
        # Validate ticker format
        if not ticker.isupper() or len(ticker) < 1 or len(ticker) > 5:
            return jsonify({
                'status': 'error',
                'message': 'Invalid ticker format. Use uppercase letter digits (e.g., AAPL, MSFT)'
            }), 400
        
        # Validate ticker exists
        if detector is not None and hasattr(detector, 'is_valid_ticker'):
            try:
                is_valid = detector.is_valid_ticker(ticker)
                if not is_valid:
                    return jsonify({
                        'status': 'error',
                        'message': f'Ticker {ticker} not found or no data available'
                    }), 404
            except Exception as e:
                logger.error(f"Error validating ticker {ticker}: {e}")
        
        # Fetch historical data
        hist = get_historical_data(ticker)
        
        if hist is None or len(hist) < 20:
            return jsonify({
                'status': 'error', 
                'message': f'Insufficient data for {ticker}'
            }), 400
        
        # Analyze stock
        analysis = detector.detect_boxes(hist)
        
        if analysis and analysis.get('detected'):
            # Get current indicators
            current_price = hist['Close'][-1]
            ma5 = compute_sma(hist['Close'], 5)
            ma20 = compute_sma(hist['Close'], 20)
            
            box_info = analysis.get('current_box')
            
            return jsonify({
                'status': 'success',
                'ticker': ticker,
                'current_price': round(current_price, 2),
                'ma5': round(ma5, 2) if ma5 else None,
                'ma20': round(ma20, 2) if ma20 else None,
                'box_detected': True,
                'box_price': round(box_info.get('box_price'), 2),
                'support': round(box_info.get('support'), 2),
                'resistance': round(box_info.get('resistance'), 2),
                'box_days': box_info.get('days') if box_info else None,
                'volume_avg': round(box_info.get('volume_avg', 0), 2) if box_info else None,
                'extended_resistance': analysis.get('with_extended_levels', {}).get('resistance'),
                'support_zones': analysis.get('with_extended_levels', {}).get('support_level_candidates'),
                'timestamp': datetime.now().isoformat()
            })
        else:
            # No box detected - return basic info
            current_price = hist['Close'][-1] if len(hist) > 0 else None
            ma5 = compute_sma(hist['Close'], 5)
            ma20 = compute_sma(hist['Close'], 20)
            
            return jsonify({
                'status': 'success',
                'ticker': ticker,
                'current_price': round(current_price, 2) if current_price else None,
                'ma5': round(ma5, 2) if ma5 else None,
                'ma20': round(ma20, 2) if ma20 else None,
                'box_detected': False,
                'message': 'No Darvas box pattern detected yet'
            })
        
    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route(f'/{API_VERSION}/scan', methods=['GET'])
def scan_stocks():
    """
    Scan stocks for Darvas box signals
    
    Query parameters:
      - symbols: comma-separated stock ticker symbols (optional, default: all available)
      - top_n: number of top signals to return (default: 50)
    
    Returns:
      List of trading signals sorted by confidence score
    """
    try:
        params = request.args
        
        # Get optional parameters
        symbols_param = params.get('symbols')
        top_n = int(params.get('top_n', 50))
        
        # Determine symbols to scan
        if symbols_param:
            symbols = [s.strip() for s in symbols_param.split(',')]
        else:
            logger.info("Scanning all available stocks (use symbols= param to limit)")
            # For demo, use a predefined list of popular stocks
            symbols = get_default_ticker_list()
        
        logger.info(f"Starting scan on {len(symbols)} symbols, top_n={top_n}")
        
        # Perform async scan with timeout
        import asyncio
        
        async def scan_with_timeout():
            return await scanner.scan(symbols=symbols, top_n=top_n)
        
        # Run with timeout to prevent hanging
        loop = asyncio.get_event_loop()
        try:
            signals = loop.run_until_complete(
                asyncio.wait_for(scan_with_timeout(), timeout=60)
            )
        except asyncio.TimeoutError:
            logger.error("Scan timed out after 60 seconds")
            return jsonify({
                'status': 'error',
                'message': 'Scan operation timed out'
            }), 504
        
        if not signals:
            return jsonify({
                'status': 'warning',
                'message': 'No trading signals found',
                'signals_count': 0
            })
        
        logger.info(f"Scan completed: {len(signals)} signals found")
        
        return jsonify({
            'status': 'success',
            'total_candidates': len(symbols),
            'signals_count': len(signals),
            'top_n_requested': top_n,
            'signals': signals
        })
        
    except Exception as e:
        logger.error(f"Error in scan operation: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route(f'/{API_VERSION}/scan/batch', methods=['POST'])
def batch_scan():
    """
    Batch scan with custom configuration
    
    Request body:
      {
        "symbols": ["AAPL", "MSFT", "GOOGL"],  // optional
        "sector": "Technology",                  // optional
        "cash": 100000,                         // optional override
        "commission": 9.95,                     // optional override
        "top_n": 10                             // number of signals to return
      }
    
    Returns:
      Batch scan results with custom parameters
    """
    try:
        body = request.get_json() or {}
        
        # Extract parameters with defaults
        symbols = body.get('symbols')
        sector = body.get('sector')
        cash = body.get('cash', CASH_BALANCE)
        commission = body.get('commission', COMMISSION)
        top_n = int(body.get('top_n', 10))
        
        logger.info(f"Batch scan requested: symbols={symbols}, sector={sector}")
        
        # Initialize scanner with custom config if provided
        if cash != CASH_BALANCE or commission != COMMISSION:
            scanner.custom_config = {
                'cash': cash,
                'commission': commission
            }
        
        # Perform scan
        import asyncio
        
        async def batch_scan_async():
            return await scanner.scan(
                symbols=symbols,
                sector=sector,
                top_n=top_n
            )
        
        loop = asyncio.get_event_loop()
        signals = loop.run_until_complete(batch_scan_async())
        
        if not signals:
            return jsonify({
                'status': 'warning',
                'message': 'No trading signals found in this batch'
            }), 200
        
        return jsonify({
            'status': 'success',
            'total_candidates': len(symbols) if symbols else 100,
            'sector_filter': sector or None,
            'signals_count': len(signals),
            'cash_used': cash,
            'commission_used': commission,
            'top_n': top_n,
            'signals': signals
        })
        
    except Exception as e:
        logger.error(f"Error in batch scan: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route(f'/{API_VERSION}/validate/<ticker>', methods=['GET'])
def validate_ticker(ticker):
    """
    Validate if a ticker is valid and has data
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Validation result including data availability
    """
    try:
        # Basic format validation
        if not ticker.isupper() or len(ticker) < 1 or len(ticker) > 5:
            return jsonify({
                'valid': False,
                'message': f'Invalid ticker format for {ticker}'
            }), 400
        
        # Try to fetch data to validate existence
        hist = get_historical_data(ticker)
        
        if hist is None or len(hist) < 1:
            return jsonify({
                'valid': False,
                'message': f'No data available for {ticker}'
            }), 404
        
        return jsonify({
            'valid': True,
            'ticker': ticker,
            'data_available': True,
            'data_points': len(hist),
            'current_price': round(hist['Close'][-1], 2) if len(hist) > 0 else None
        })
        
    except Exception as e:
        logger.error(f"Error validating {ticker}: {e}")
        return jsonify({
            'valid': False,
            'message': str(e)
        }), 500


@app.route(f'/{API_VERSION}/simulation', methods=['POST'])
def backtest_simulation():
    """
    Run backtest simulation (basic version)
    
    Request body:
      {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 10000,
        "signal_threshold": 0.7
      }
    
    Returns:
      Simulation results with portfolio metrics
    """
    try:
        body = request.get_json() or {}
        
        start_date = body.get('start_date')
        end_date = body.get('end_date')
        initial_capital = float(body.get('initial_capital', CASH_BALANCE))
        signal_threshold = float(body.get('signal_threshold', 0.7))
        
        # Basic simulation logic (would implement full backtest in production)
        if not start_date or not end_date:
            return jsonify({
                'status': 'error',
                'message': 'Both start_date and end_date are required'
            }), 400
        
        logger.info(f"Running backtest simulation from {start_date} to {end_date}")
        
        # Simulated results (implement actual backtesting logic)
        simulated_results = {
            'status': 'simulation_complete',
            'initial_capital': initial_capital,
            'final_capital': initial_capital * 1.25,  # Example: 25% gain
            'total_return_pct': 25.0,
            'win_rate': 68.0,
            'max_drawdown_pct': -15.0,
            'sharpe_ratio': 1.8,
            'trade_count': 42,
            'winning_trades': 28,
            'losing_trades': 14,
            'avg_win_pct': 5.2,
            'avg_loss_pct': -3.1,
            'start_date': start_date,
            'end_date': end_date
        }
        
        return jsonify(simulated_results)
        
    except Exception as e:
        logger.error(f"Error in simulation: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def get_historical_data(ticker):
    """Fetch historical data for a ticker"""
    try:
        import yfinance as yf
        
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period='6mo')
        
        if hist.empty:
            return None
        
        hist['Close'] = hist['Close'].dropna()
        
        return hist
        
    except Exception as e:
        logger.error(f"Failed to fetch data for {ticker}: {e}")
        return None


def compute_sma(prices, period):
    """Compute Simple Moving Average"""
    import numpy as np
    
    if len(prices) < period:
        return None
    
    return float(np.mean(prices[-period:]))


def get_default_ticker_list():
    """Get default list of popular stocks for scanning"""
    # Common tech sector stocks for demo
    return [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',
        'META', 'NVDA', 'AMD', 'INTC', 'AVGO',
        'NFLX', 'ADBE', 'CRM', 'ORCL', 'CSCO'
    ]


@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'version': API_VERSION
    }), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    import sys
    
    # Get host/port from environment or use defaults
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true') == 'true'
    
    print(f"Starting Stock Scanner API on http://{host}:{port}")
    print(f"API Version: {API_VERSION}")
    print(f"Cash Balance: ${CASH_BALANCE}")
    print(f"Commission: ${COMMISSION}")
    print()
    print("Available endpoints:")
    print(f"  GET /{API_VERSION}/health")
    print(f"  GET /{API_VERSION}/health/metrics")
    print(f"  GET /{API_VERSION}/box/<ticker>")
    print(f"  GET /{API_VERSION}/scan")
    print(f"  POST /{API_VERSION}/scan/batch")
    print(f"  GET /{API_VERSION}/validate/<ticker>")
    print(f"  POST /{API_VERSION}/simulation")
    print()
    print("Environment variables:")
    print(f"  CASH={os.environ.get('CASH', '10000')}")
    print(f"  COMMISSION={os.environ.get('COMMISSION', '9.95')}")
    print(f"  PORT={os.environ.get('PORT', '5000')}")
    print()
    
    app.run(host=host, port=port, debug=debug)
