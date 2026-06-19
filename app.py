"""
Enhanced Stock Scanner Web Application
======================================

Flask-based web interface with Plotly interactive charts.
Provides dashboard, API endpoints, and visualization capabilities.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import datetime
import os
import math
import requests as http_requests

from scanner import DarvasScanner, DEFAULT_STOCKS, load_watchlist, save_watchlist
from darvas_detector import IndianStockMonitor, DarvasBoxDetector
import technical_indicators as indicators_module
from technical_indicators import TechnicalIndicators


app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter web and cross-origin requests
scanner = DarvasScanner(interval_minutes=15)
monitor = IndianStockMonitor()

# ── Safe JSON encoder: convert NaN/Infinity → null for strict JSON compliance ──
def _clean_nan(obj):
    """Recursively replace NaN/Infinity with None in JSON-serializable objects."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: _clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_clean_nan(v) for v in obj]
    return obj

class SafeJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs['allow_nan'] = False  # prevent bare NaN/Inf tokens
        super().__init__(*args, **kwargs)

    def encode(self, o):
        # Clean NaN/Inf BEFORE serialization
        return super().encode(_clean_nan(o))

    def default(self, o):
        return super().default(o)

# Flask 3.x uses json_provider_class instead of json_encoder
from flask.json.provider import DefaultJSONProvider
class SafeJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        kwargs.setdefault("default", self.default)
        kwargs.setdefault("ensure_ascii", self.ensure_ascii)
        kwargs.setdefault("sort_keys", self.sort_keys)
        return json.dumps(_clean_nan(obj), **kwargs)

app.json_provider_class = SafeJSONProvider
app.json = SafeJSONProvider(app)


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


@app.route('/api/portfolio/real')
def get_real_portfolio():
    """Get user's real portfolio data."""
    try:
        with open('darvax_trade_tracker.json') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/portfolio/system')
def get_system_portfolio():
    """Get system paper trading portfolios (Darvas + Options)."""
    try:
        darvas = {}
        options = {}
        
        # Load Darvas paper trader state
        if os.path.exists('darvas_state.json'):
            with open('darvas_state.json') as f:
                darvas = json.load(f)
        
        # Load Options paper trader state
        if os.path.exists('options_state.json'):
            with open('options_state.json') as f:
                options = json.load(f)
        
        return jsonify({
            'darvas': darvas,
            'options': options,
            'combined': {
                'darvas_capital': 100000,
                'options_capital': 100000,
                'darvas_equity': darvas.get('total_value', 0) if darvas else 0,
                'options_equity': (options.get('cash', 0) if options else 0),
                'darvas_pnl': darvas.get('total_pnl', 0) if darvas else 0,
                'options_pnl': options.get('total_pnl', 0) if options else 0,
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patterns/recommended')
def get_recommended_patterns():
    """Get the latest recommended patterns from the DarvaX DV scanner."""
    try:
        # Try the pattern log first
        patterns_file = 'pro_trader_patterns.json'
        dv_log = 'dv_scan_results.json'
        
        if os.path.exists(dv_log):
            with open(dv_log) as f:
                data = json.load(f)
            return jsonify(data)
        elif os.path.exists(patterns_file):
            with open(patterns_file) as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({
                'error': 'No pattern data available. Run a DV scan first.',
                'patterns': []
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/wishlist/scan')
def get_wishlist_scan():
    """Scan wishlist stocks and return entry/exit advice."""
    try:
        from wishlist_scanner import scan_wishlist, load_cached_scan
        
        force = request.args.get('force', '0') == '1'
        
        if not force:
            # Try cache first (less than 30 min old)
            cached = load_cached_scan()
            if cached and 'results' in cached and cached.get('results'):
                ts = cached.get('timestamp', '')
                if ts:
                    try:
                        cached_time = datetime.datetime.fromisoformat(ts)
                        now = datetime.datetime.now()
                        age = (now - cached_time).total_seconds()
                        if age < 1800:  # 30 minutes
                            return jsonify(cached)
                    except:
                        pass
        
        # Run fresh scan
        result = scan_wishlist()
        return jsonify(result)
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


@app.route('/api/history')
def get_history():
    """Get combined trade history across all systems (closed trades)."""
    try:
        history = {
            'real': [],
            'darvas': [],
            'options': [],
            'generated_at': datetime.datetime.now().isoformat()
        }
        
        # Real portfolio closed trades (from trade tracker if available)
        try:
            with open('darvax_trade_tracker.json') as f:
                rt = json.load(f)
            history['real'] = rt.get('trades', [])
            history['real_summary'] = {
                'total_invested': rt.get('summary', {}).get('total_invested', 0),
                'current_value': rt.get('summary', {}).get('current_value', 0),
                'total_pnl': rt.get('summary', {}).get('total_returns_abs', 0),
                'total_pnl_pct': rt.get('summary', {}).get('total_returns_pct', 0),
                'win_rate': rt.get('performance', {}).get('win_rate', 0),
                'total_trades': rt.get('performance', {}).get('total_trades', 0),
            }
        except:
            pass
        
        # Darvas system closed trades
        try:
            with open('darvas_state.json') as f:
                ds = json.load(f)
            history['darvas'] = ds.get('closed_trades', [])
            history['darvas_summary'] = {
                'total_value': ds.get('total_value', 0),
                'total_pnl': ds.get('total_pnl', 0),
                'cash': ds.get('cash', 0),
                'win_rate': (ds.get('winning_trades', 0) / max(ds.get('total_trades', 0), 1)) * 100,
                'total_trades': ds.get('total_trades', 0),
                'open_positions': len(ds.get('positions', [])),
            }
        except:
            pass
        
        # Options system closed trades
        try:
            with open('options_state.json') as f:
                os_ = json.load(f)
            history['options'] = os_.get('closed_trades', [])
            history['options_summary'] = {
                'cash': os_.get('cash', 0),
                'total_pnl': os_.get('total_pnl', 0),
                'total_trades': os_.get('total_trades', 0),
                'win_rate': (os_.get('winning_trades', 0) / max(os_.get('total_trades', 0), 1)) * 100,
                'drawdown': os_.get('current_drawdown', 0),
                'open_positions': len(os_.get('positions', [])),
            }
        except:
            pass
        
        # Combined radar data
        def safe_pnl(val):
            return val if val else 0
        
        radar = {
            'dx': {
                'win_rate': history.get('darvas_summary', {}).get('win_rate', 0),
                'total_pnl': safe_pnl(history.get('darvas_summary', {}).get('total_pnl', 0)),
                'total_trades': history.get('darvas_summary', {}).get('total_trades', 0),
            },
            'options': {
                'win_rate': history.get('options_summary', {}).get('win_rate', 0),
                'total_pnl': safe_pnl(history.get('options_summary', {}).get('total_pnl', 0)),
                'total_trades': history.get('options_summary', {}).get('total_trades', 0),
            },
            'real': {
                'win_rate': history.get('real_summary', {}).get('win_rate', 0),
                'total_pnl': safe_pnl(history.get('real_summary', {}).get('total_pnl', 0)),
                'total_trades': history.get('real_summary', {}).get('total_trades', 0),
            }
        }
        history['radar'] = radar
        
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/performance')
def get_performance():
    """Get performance chart data (equity curve, monthly returns)."""
    try:
        # Build performance data from available sources
        performance = {
            'equity_curve': [],
            'monthly_returns': [],
            'generated_at': datetime.datetime.now().isoformat()
        }

        # Extract equity history from Darvas state if available
        if os.path.exists('darvas_state.json'):
            with open('darvas_state.json') as f:
                ds = json.load(f)
            equity = ds.get('equity_history', [])
            if equity:
                performance['equity_curve'] = equity
            else:
                # Synthetic equity curve from peak_value
                peak = ds.get('peak_value', 100000)
                current = ds.get('total_value', 100000)
                performance['equity_curve'] = [
                    {'date': (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat(), 'value': 100000},
                    {'date': (datetime.datetime.now() - datetime.timedelta(days=15)).isoformat(), 'value': (100000 + peak) / 2},
                    {'date': datetime.datetime.now().isoformat(), 'value': current},
                ]
        else:
            performance['equity_curve'] = [
                {'date': (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat(), 'value': 100000},
                {'date': datetime.datetime.now().isoformat(), 'value': 100000},
            ]

        # Monthly returns from options state if available
        if os.path.exists('options_state.json'):
            with open('options_state.json') as f:
                os_ = json.load(f)
            performance['monthly_returns'] = os_.get('monthly_returns', [])

        return jsonify(performance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stock/<symbol>')
def get_stock_detail(symbol):
    """Get detailed data for a single stock across all systems."""
    try:
        result = {
            'symbol': symbol,
            'real': None,
            'darvas': None,
            'options': None,
            'patterns': None,
            'wishlist': None,
        }

        # Check in real portfolio
        try:
            with open('darvax_trade_tracker.json') as f:
                rt = json.load(f)
            for trade in rt.get('trades', []):
                if trade.get('stock', '').upper() == symbol.upper():
                    result['real'] = trade
                    break
        except:
            pass

        # Check in Darvas portfolio
        try:
            with open('darvas_state.json') as f:
                ds = json.load(f)
            for pos in ds.get('positions', []):
                if pos.get('symbol', '').upper() == symbol.upper():
                    result['darvas'] = pos
                    break
        except:
            pass

        # Check in Options positions
        try:
            with open('options_state.json') as f:
                os_ = json.load(f)
            for pos in os_.get('positions', []):
                if pos.get('symbol', '').upper() == symbol.upper():
                    result['options'] = pos
                    break
        except:
            pass

        # Check in patterns
        try:
            pat_file = 'dv_scan_results.json'
            if os.path.exists(pat_file):
                with open(pat_file) as f:
                    pd = json.load(f)
                for cat in ['dv_bull', 'dv_bear', 'dv_accel']:
                    for p in pd.get(cat, []):
                        if p.get('ticker', '').upper() == symbol.upper():
                            result['patterns'] = p
                            break
        except:
            pass

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── AI Stock Q&A (Qwen 3.5 via LM Studio) ────────────────────────────
@app.route('/api/ai/query', methods=['POST'])
def ai_stock_query():
    """Answer a stock-related question using the local Qwen 3.5 model."""
    data = request.get_json()
    question = data.get('question', '').strip()
    stock_context = data.get('stock_context', '')

    if not question:
        return jsonify({'error': 'Question is required'}), 400

    # Gather market context
    context_parts = []

    # Real portfolio summary
    try:
        with open('darvax_trade_tracker.json') as f:
            rt = json.load(f)
        s = rt.get('summary', {})
        perf = rt.get('performance', {})
        context_parts.append(
            f"USER'S PORTFOLIO: ₹{s.get('current_value', 0):,.0f} invested across "
            f"{s.get('total_holdings', 0)} holdings, {perf.get('win_rate', 0)}% win rate, "
            f"P&L: {s.get('total_returns_abs', 0):+,.0f} ({s.get('total_returns_pct', 0):+.2f}%). "
            f"Nifty: {s.get('nifty_50', 'N/A')}. "
            f"Best: {perf.get('best_performer', 'N/A')}. Worst: {perf.get('worst_performer', 'N/A')}."
        )
    except:
        pass

    # Tracked stocks context
    try:
        with open('tracked_stocks.json') as f:
            ts = json.load(f)
        prices = ts.get('prices', {})
        stock_list = []
        for s in ts.get('stocks', []):
            t = s['ticker']
            p = prices.get(t, {})
            if p.get('price', 0) > 0:
                stock_list.append(f"{s['name']} ({t}): ₹{p['price']} ({p.get('daily_change_pct', 0):+.2f}%)")
        if stock_list:
            context_parts.append("TRACKED STOCKS: " + " | ".join(stock_list))
    except:
        pass

    # Stock-specific data if a ticker is mentioned
    if stock_context:
        try:
            df = monitor.load_stock_data(stock_context)
            if 'error' not in df and not df.empty:
                close = df['Close']
                rsi_val = TechnicalIndicators().rsi(close)
                context_parts.append(
                    f"{stock_context} DATA: Last close ₹{float(close.iloc[-1]):.2f}, "
                    f"20d avg ₹{float(close.iloc[-20:].mean()):.2f}, "
                    f"RSI(14) = {rsi_val:.1f}, "
                    f"52w high ₹{float(close.max()):.2f}, "
                    f"52w low ₹{float(close.min()):.2f}"
                )
        except:
            pass

    system_prompt = (
        "You are DX, an expert Indian stock market analyst assistant. "
        "You have deep knowledge of NSE stocks, technical analysis, Darvas box theory, "
        "fundamental analysis, and Indian market dynamics. "
        "Give clear, concise, actionable answers. Use Indian rupee (₹) notation. "
        "Be direct — no filler. If you don't know something, say so."
    )

    full_context = "\n\n".join(context_parts) if context_parts else "No market data available."
    user_prompt = f"CONTEXT:\n{full_context}\n\nUSER QUESTION: {question}\n\nAnswer concisely as DX:"

    try:
        resp = http_requests.post(
            "http://localhost:1234/v1/chat/completions",
            json={
                "model": "qwen/qwen3.5-9b",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 1024,
                "temperature": 0.3,
            },
            timeout=120
        )
        result = resp.json()
        answer = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        reasoning = result.get('choices', [{}])[0].get('message', {}).get('reasoning_content', '')
        return jsonify({
            'answer': answer,
            'reasoning': reasoning,
            'model': result.get('model', 'qwen/qwen3.5-9b'),
            'usage': result.get('usage', {}),
        })
    except Exception as e:
        return jsonify({'error': f'AI query failed: {str(e)}'}), 500


@app.route('/api/ai/tracked')
def ai_tracked_stocks():
    """Return tracked stocks with live prices and analysis."""
    try:
        with open('tracked_stocks.json') as f:
            data = json.load(f)
        # Also append wishlist scan results for these stocks
        try:
            wislist = json.loads(open('wishlist_scan_cache.json').read())
            if wislist.get('results'):
                # Match tracked stocks in wishlist results
                tracked_tickers = {s['ticker'].replace('.NS','') for s in data.get('stocks', [])}
                matched = [r for r in wislist['results'] if r.get('ticker','') in tracked_tickers or (r.get('ticker','')+'.NS') in tracked_tickers]
                data['wishlist_matches'] = matched
        except:
            data['wishlist_matches'] = []
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Route Aliases for Dashboard frontend ────────────────────
@app.route('/api/ai/ask', methods=['POST'])
def ai_ask():
    """Alias for /api/ai/query used by dashboard frontend."""
    return ai_stock_query()

@app.route('/api/tracked-stocks')
def tracked_stocks():
    """Alias for /api/ai/tracked used by dashboard frontend."""
    return ai_tracked_stocks()

@app.route('/api/refresh-tracked-prices', methods=['POST'])
def refresh_tracked_prices():
    """Fetch fresh prices for all tracked stocks via NSE."""
    import subprocess
    try:
        script = os.path.join(os.path.dirname(__file__), 'update_trade_tracker_prices.py')
        if os.path.exists(script):
            result = subprocess.run(['python3', script], capture_output=True, text=True, timeout=120)
            out = result.stdout.strip()
            err = result.stderr.strip()
            if result.returncode == 0:
                return jsonify({'success': True, 'message': out[-200:] if out else 'Prices refreshed'})
            else:
                return jsonify({'success': False, 'error': err[-200:] if err else 'Script failed'})
        else:
            # Fallback: use NSE fetch directly
            from scanner import fetch_stock_data_nse
            try:
                with open('tracked_stocks.json') as f:
                    data = json.load(f)
            except:
                return jsonify({'success': False, 'error': 'tracked_stocks.json not found'})
            import datetime
            now = datetime.datetime.now().isoformat()
            for s in data.get('stocks', []):
                t = s['ticker']
                try:
                    res = fetch_stock_data_nse(t)
                    if res and 'price' in res:
                        data.setdefault('prices', {})[t] = {
                            'price': res['price'],
                            'daily_change_pct': res.get('daily_change_pct', 0),
                            'updated_at': now
                        }
                except:
                    pass
            data['last_updated'] = now
            with open('tracked_stocks.json', 'w') as f:
                json.dump(data, f, indent=2)
            return jsonify({'success': True, 'message': f'Updated {len(data.get("stocks", []))} stocks'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Add CORS headers for local development
    port = int(os.environ.get('PORT', 8085))
    app.run(debug=True, host='0.0.0.0', port=port)
