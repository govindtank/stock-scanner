"""
Enhanced Stock Scanner Web Application
======================================

Flask-based web interface with Plotly interactive charts.
Provides dashboard, API endpoints, and visualization capabilities.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
import json
import datetime
import os

from scanner import DarvasScanner, DEFAULT_STOCKS, load_watchlist, save_watchlist
from darvas_detector import IndianStockMonitor, DarvasBoxDetector
import technical_indicators as indicators_module


app = Flask(__name__)
scanner = DarvasScanner(interval_minutes=15)
monitor = IndianStockMonitor()

# Ensure templates directory exists
os.makedirs('templates', exist_ok=True)


@app.route('/')
def dashboard():
    """Render the main dashboard."""
    return render_template('index.html')


@app.route('/api/technical-indicators/<stock>')
def get_technical_indicators(stock):
    """Get technical indicators for a stock."""
    try:
        df = monitor.load_stock_data(stock)
        
        if 'error' in df:
            return jsonify({'error': df['error']}), 400
        
        close_prices = df['Close']
        high_prices = df['High']
        low_prices = df['Low']
        
        # Calculate all indicators
        ind = indicators_module.TechnicalIndicators()
        
        technical_data = {
            'rsi': round(ind.rsi(close_prices), 2),
            'macd': ind.macd(close_prices),
            'bollinger_bands': ind.bollinger_bands(close_prices),
            'atr': round(ind.atr(high_prices, low_prices, close_prices), 2),
            'adx': ind.adx(high_prices, low_prices, close_prices),
            'ema_12': round(ind.exponential_moving_average(close_prices, 12), 2),
            'stochastic': ind.stochastic(high_prices, low_prices, close_prices)
        }
        
        return jsonify({'ticker': stock, **technical_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chart/<stock>')
def get_chart_data(stock):
    """Get chart data for Plotly visualization."""
    try:
        df = monitor.load_stock_data(stock)
        
        if 'error' in df:
            return jsonify({'error': df['error']}), 400
        
        # Get price and indicator data for chart
        close_prices = df['Close'].values.tolist()
        high_prices = df['High'].values.tolist()
        low_prices = df['Low'].values.tolist()
        
        # Technical indicators
        ind = indicators_module.TechnicalIndicators()
        macd_data = ind.macd(df['Close'])
        bb_data = ind.bollinger_bands(df['Close'])
        
        return jsonify({
            'close': close_prices,
            'high': high_prices,
            'low': low_prices,
            'current_close': float(close_prices[-1]),
            'macd': macd_data,
            'bollinger': bb_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scan')
def scan_stocks():
    """Run a scan and return results."""
    try:
        results = scanner.run_once()
        
        # Format for frontend
        formatted = {}
        for stock, result in results.items():
            if 'error' not in result:
                latest_breakout = None
                if result.get('breakouts'):
                    latest_breakout = result['breakouts'][-1]
                
                formatted[stock] = {
                    'ticker': stock,
                    'price': round(result['current_price'], 2),
                    'boxes_detected': result.get('boxes_detected', 0),
                    'trend': result.get('trend'),
                    'recommendation': result.get('recommendation', ''),
                }
                
                if latest_breakout:
                    formatted[stock].update({
                        'last_box_high': round(latest_breakout.get('box_high'), 2),
                        'breakout_pct': latest_breakout.get('breakout_pct'),
                        'volume_spike': latest_breakout.get('volume_spike'),
                        'signal_strength': latest_breakout.get('signal_strength'),
                        'patterns_detected': latest_breakout.get('patterns_detected', [])
                    })
        
        return jsonify(formatted)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist')
def get_watchlist():
    """Get current watchlist."""
    try:
        watchlist = load_watchlist()
        
        result = {}
        for stock in watchlist:
            try:
                import yfinance as yf
                data = yf.download(stock, period='3mo', interval='1d')
                if not data.empty:
                    last_price = float(data['Close'].iloc[-1])
                    prev_price = float(data['Close'].iloc[-2])
                    
                    result[stock] = {
                        'name': stock.split('.')[0],
                        'price': round(last_price, 2),
                        'change_pct': round((last_price - prev_price) / prev_price * 100, 2)
                    }
            except:
                pass
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/watchlist/full')
def get_all_watchlist():
    """Get full watchlist with ticker info."""
    try:
        watchlist = load_watchlist()
        result = {}
        
        for stock in watchlist:
            try:
                import yfinance as yf
                data = yf.download(stock, period='1mo')
                
                if not data.empty:
                    last = data.iloc[-1]
                    prev = data.iloc[-2]
                    
                    result[stock] = {
                        'ticker': stock,
                        'name': stock.split('.')[0],
                        'price': round(float(last['Close']), 2),
                        'change_pct': round((float(last['Close']) - float(prev['Close'])) / float(prev['Close']) * 100, 2)
                    }
            except Exception:
                pass
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analysis/<stock>')
def analyze_single(stock):
    """Analyze a single stock with full analysis."""
    try:
        result = monitor.analyze_stock(stock)
        if result and 'error' not in result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Analysis failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/set-watchlist', methods=['POST'])
def update_watchlist():
    """Update watchlist from JSON data."""
    try:
        data = request.get_json()
        stocks = [s['ticker'] for s in data]
        
        scanner.set_watchlist(stocks)
        save_watchlist(stocks)
        
        return jsonify({'success': True, 'count': len(stocks)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/get-config')
def get_config():
    """Get current configuration."""
    try:
        from configuration import Configuration
        
        config = {
            'trading': Configuration.TRADING_CONFIG.copy(),
            'risk': Configuration.RISK_CONFIG.copy(),
            'scan': Configuration.SCAN_CONFIG.copy(),
            'alerts': Configuration.ALERT_CONFIG.copy(),
        }
        
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/save-config', methods=['POST'])
def save_config():
    """Save configuration."""
    try:
        from configuration import get_full_config
        
        data = request.get_json()
        
        # Remove non-serializable items
        def serialize(obj):
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize(i) for i in obj]
            else:
                return str(obj) if isinstance(obj, datetime.datetime) else obj
        
        serialized_config = serialize(data)
        
        # Save to file
        config_path = 'config.json'
        with open(config_path, 'w') as f:
            json.dump(serialized_config, f, indent=2)
        
        return jsonify({'success': True, 'path': config_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/load-config')
def load_config():
    """Load configuration from file."""
    try:
        from configuration import load_config
        
        config = load_config('config.json')
        
        if 'scan_params' in config and not isinstance(config['scan_params'], dict):
            # Convert string to dict if needed
            scan_params = json.loads(config['scan_params'])
            config['scan_params'] = scan_params
        
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/indicators/calculate')
def calculate_indicators():
    """Calculate indicators for a ticker."""
    try:
        stock = request.args.get('ticker', '')
        
        if not stock:
            return jsonify({'error': 'Missing ticker parameter'}), 400
        
        df = monitor.load_stock_data(stock)
        
        if 'error' in df:
            return jsonify({'error': df['error']}), 400
        
        close_prices = df['Close']
        high_prices = df['High']
        low_prices = df['Low']
        
        ind = indicators_module.TechnicalIndicators()
        
        indicator_values = {
            'rsi': round(ind.rsi(close_prices), 2),
            'macd': ind.macd(close_prices),
            'bollinger_bands': ind.bollinger_bands(close_prices),
            'atr': round(ind.atr(high_prices, low_prices, close_prices), 2),
            'adx': ind.adx(high_prices, low_prices, close_prices)
        }
        
        return jsonify({'ticker': stock, **indicator_values})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scan-types', methods=['POST'])
def run_scan_type():
    """Run a specific scan type."""
    try:
        from scan_types import get_all_signals, ScanType
        
        data = request.get_json()
        ticker = data.get('ticker', '')
        scan_type_name = data.get('scan_type', 'darvas_breakout')
        
        if not ticker:
            return jsonify({'error': 'Missing ticker'}), 400
        
        # Load stock data
        df = monitor.load_stock_data(ticker)
        
        if 'error' in df:
            return jsonify({'error': df['error']}), 400
        
        # Map scan type names to ScanType enum
        type_mapping = {
            'mean_reversion': ScanType.MEAN_REVERSION,
            'gap_analysis': ScanType.GAP_ANALYSIS,
            'momentum': ScanType.MOMENTUM,
            'relative_strength': ScanType.RELATIVE_STRENGTH,
            'volume_pattern': ScanType.VOLUME_PATTERN,
        }
        
        scan_type = type_mapping.get(scan_type_name)
        if not scan_type:
            return jsonify({'error': f'Unknown scan type: {scan_type_name}'}), 400
        
        # Run scanner
        from scan_types import run_scanner
        signals = run_scanner(scan_type, df)
        
        # Convert ScanType to string for JSON
        formatted_signals = []
        for signal in signals:
            signal_copy = signal.copy()
            if 'type' in signal_copy:
                signal_copy['scan_type'] = signal_copy.pop('type')
            formatted_signals.append(signal_copy)
        
        return jsonify({'ticker': ticker, 'scan_type': scan_type_name, 'signals': formatted_signals})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Add CORS headers for local development
    app.run(debug=True, host='0.0.0.0', port=5000)
