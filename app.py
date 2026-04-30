from flask import Flask, render_template, jsonify
import json
from scanner import DarvasScanner, DEFAULT_STOCKS, load_watchlist
import datetime

app = Flask(__name__)
scanner = DarvasScanner()

@app.route('/')
def dashboard():
    """Render the main dashboard."""
    return render_template('index.html')

@app.route('/api/watchlist')
def get_watchlist():
    """Get current watchlist."""
    try:
        watchlist = load_watchlist()
        # Get quick prices for watchlist
        result = {}
        for stock in watchlist:
            try:
                import yfinance as yf
                data = yf.download(stock, period='3mo', interval='1d')
                if not data.empty:
                    last_price = float(data['Close'].iloc[-1])
                    result[stock] = {
                        'name': stock.split('.')[0],
                        'price': round(last_price, 2),
                        'change': None
                    }
            except:
                pass
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scan', methods=['POST'])
def scan_stocks():
    """Run a scan and return results."""
    try:
        results = scanner.run_once()
        
        # Format for frontend
        formatted = {}
        for stock, result in results.items():
            if 'error' not in result and result.get('breakouts'):
                latest_breakout = result['breakouts'][-1]
                formatted[stock] = {
                    'ticker': stock,
                    'price': round(result['current_price'], 2),
                    'last_box_high': round(result.get('active_box_high'), 2) if result.get('active_box_high') else None,
                    'breakout_pct': latest_breakout.get('breakout_pct'),
                    'volume_spike': latest_breakout.get('volume_spike'),
                    'signal_strength': latest_breakout.get('signal_strength'),
                    'recommendation': result.get('recommendation', ''),
                    'trend': result.get('trend')
                }
        
        return jsonify(formatted)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/watchlist', methods=['GET'])
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
            except:
                pass
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/<stock>')
def analyze_single(stock):
    """Analyze a single stock."""
    try:
        result = scanner.monitor.analyze_stock(stock)
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
        return jsonify({'success': True, 'count': len(stocks)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
