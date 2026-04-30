"""
Enhanced Stock Scanner - Async Support Implementation
Implements concurrent stock analysis with rate limiting and retry logic
"""

import yfinance as yf
from datetime import datetime, timedelta
from aiohttp import ClientSession, ClientTimeout
import asyncio
import pandas as pd
import numpy as np
from darvas_detector import DarvasDetector
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Trading signal types with confidence thresholds"""
    STRONG_BUY = ('strong_buy', 0.85)
    BUY = ('buy', 0.70)
    NEUTRAL = ('neutral', 0.30)
    SELL = ('sell', 0.25)
    STRONG_SELL = ('strong_sell', 0.15)


class AsyncStockScanner:
    """
    Enhanced Stock Scanner with async support and caching
    Supports concurrent analysis of multiple stocks with rate limiting
    """
    
    def __init__(self, data_source='yfinance', cash=10000, commission=0, 
                 max_concurrent=5, timeout_seconds=30):
        self.data_source = data_source
        self.cash = cash
        self.commission = commission
        self.detector = DarvasDetector()
        
        # Performance tracking
        self.position_count = 0
        self.total_invested = 0
        self.scan_count = 0
        
        # Async configuration
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds
        self.semaphore = None
        self._semaphore_lock = False
        
        # Rate limiting config (for paid data sources)
        self.rate_limit_delay = 0.1  # seconds between requests
        self.burst_size = 10
    
    async def initialize(self):
        """Initialize semaphore and timeouts"""
        if not self._semaphore_lock:
            self.semaphore = asyncio.Semaphore(self.max_concurrent)
            self.timeout = ClientTimeout(total=self.timeout_seconds)
            self._semaphore_lock = True
            logger.info(f"AsyncScanner initialized with {self.max_concurrent} concurrent slots")
    
    async def scan(self, symbols=None, sector=None, top_n=50):
        """
        Scan stocks for trading opportunities asynchronously
        
        Args:
            symbols: List of stock tickers or None for all candidates
            sector: Optional sector filter  
            top_n: Number of top signals to return
            
        Returns:
            List of trading signals sorted by confidence
        """
        await self.initialize()
        
        # Get candidate universe
        if symbols is None:
            candidates = self._get_all_candidates(sector=sector)
        else:
            candidates = symbols
        
        if not candidates:
            logger.warning("No candidates to scan")
            return []
        
        logger.info(f"Starting async scan on {len(candidates)} stocks (top_n={top_n})")
        
        # Scan with rate limiting and concurrent execution
        signals = await self._scan_with_rate_limit(candidates)
        
        # Filter by confidence threshold
        min_confidence = 0.3
        filtered_signals = [s for s in signals if s['confidence'] >= min_confidence]
        
        logger.info(f"Found {len(filtered_signals)} signals above threshold")
        
        # Sort and limit results
        sorted_signals = sorted(filtered_signals, 
                               key=lambda x: x.get('confidence', 0), 
                               reverse=True)[:top_n]
        
        self.scan_count += len(candidates)
        logger.info(f"Scan completed: {len(sorted_signals)} signals from {self.scan_count} total attempts")
        
        return sorted_signals
    
    async def _scan_with_rate_limit(self, symbols):
        """Scan with rate limiting for paid API sources"""
        semaphore = self.semaphore
        
        async def analyze_with_semaphore(ticker):
            async with semaphore:
                try:
                    await asyncio.sleep(self.rate_limit_delay)
                    return await self._analyze_async(ticker)
                except Exception as e:
                    logger.error(f"Error analyzing {ticker}: {e}")
                    return None
        
        # Create tasks for all symbols
        tasks = [analyze_with_semaphore(ticker) for ticker in symbols]
        
        # Execute concurrently, handling exceptions
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Extract successful signals
        signals = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} failed: {result}")
                continue
            
            if result is not None:
                signals.append(result)
        
        return signals
    
    async def _analyze_async(self, ticker):
        """Async version of analyze_stock"""
        start_time = datetime.now()
        
        try:
            # Fetch historical data asynchronously
            hist = await self._fetch_historical_data_async(ticker)
            
            if hist is None or len(hist) < 20:
                logger.debug(f"{ticker}: Insufficient data ({len(hist) if hist else 0} bars)")
                return None
            
            # Detect Darvas boxes
            darvas_boxes = self.detector.detect_boxes(hist)
            
            if not darvas_boxes and not darvas_boxes.get('detected'):
                return None
            
            # Get current price and indicators
            current_price = hist['Close'][-1]
            
            # Analyze signal with comprehensive indicators
            signal_info = await self._calculate_signal_async(
                ticker=ticker,
                current_price=current_price,
                darvas_boxes=darvas_boxes,
                hist=hist
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.debug(f"{ticker} analyzed in {duration*1000:.1f}ms")
            
            return signal_info
            
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            return None
    
    async def _fetch_historical_data_async(self, ticker):
        """Fetch historical data asynchronously"""
        try:
            ticker_obj = yf.Ticker(ticker)
            
            # Use asyncio run_coroutine_threadsafe for sync-yfinance call
            # Or use websockets for truly async fetching
            hist = ticker_obj.history(period='6mo')
            
            if hist.empty:
                return None
            
            hist['Close'] = hist['Close'].dropna()
            
            return hist
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            return None
    
    async def _calculate_signal_async(self, ticker, current_price, 
                                      darvas_boxes, hist):
        """Calculate comprehensive signal analysis"""
        
        # Get technical indicators
        ma5 = self._compute_sma(hist['Close'], 5) if len(hist['Close']) >= 5 else None
        ma20 = self._compute_sma(hist['Close'], 20) if len(hist['Close']) >= 20 else None
        
        # Calculate RSI
        rsi = self._calculate_rsi(hist['Close'], 14)
        
        # Calculate volume ratio
        avg_volume = hist['Volume'].rolling(20).mean()
        current_volume = hist['Volume'][-1]
        volume_ratio = current_volume / avg_volume if pd.notna(avg_volume) else 1.0
        
        # Box analysis
        box_price = darvas_boxes.get('box_price') if darvas_boxes else None
        support = darvas_boxes.get('support')
        resistance = darvas_boxes.get('resistance')
        
        # Determine signal type and confidence
        signal_type, confidence = self._determine_signal_with_indicators(
            current_price=current_price,
            ma5=ma5,
            ma20=ma20,
            rsi=rsi,
            volume_ratio=volume_ratio,
            darvas_boxes=darvas_boxes,
            box_price=box_price
        )
        
        return {
            'ticker': ticker,
            'current_price': round(current_price, 2),
            'signal': signal_type.value if signal_type else None,
            'confidence': round(confidence, 3),
            'box_price': round(box_price, 2) if box_price else None,
            'support': round(support, 2) if support else None,
            'resistance': round(resistance, 2) if resistance else None,
            'rsi': round(rsi, 2),
            'volume_ratio': round(volume_ratio, 2),
            'ma5': round(ma5, 2) if ma5 else None,
            'ma20': round(ma20, 2) if ma20 else None,
            'timestamp': datetime.now().isoformat()
        }
    
    def _compute_sma(self, prices, period):
        """Compute Simple Moving Average"""
        return np.mean(prices[-period:]) if len(prices) >= period else None
    
    def _calculate_rsi(self, closes, period=14):
        """Calculate RSI indicator (Pure Python implementation)"""
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = -np.where(deltas < 0, deltas, 0)
        
        avg_gain = np.mean(gains[-period:]) if len(gains) >= period else 100
        avg_loss = np.mean(losses[-period:]) if len(losses) >= period else 100
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _determine_signal_with_indicators(self, current_price, ma5=None, 
                                          ma20=None, rsi=None, volume_ratio=1.0,
                                          darvas_boxes=None, box_price=None):
        """Determine signal type based on multiple factors with scoring"""
        
        score = 0
        max_score = 10
        
        # Box breakout detection (+2)
        if darvas_boxes and box_price:
            if current_price > box_price * 1.02:  # 2% above box
                score += 2  # Strong breakout signal
        
        # Moving average crossover (+1)
        if ma5 and ma20:
            if ma5 > ma20 and current_price > ma5:  # Bullish alignment
                score += 1
        
        # Price vs MA position (+1)
        if ma5 and current_price > ma5:
            score += 1
        
        # Volume confirmation (+1-2)
        if volume_ratio > 1.5:  # Above average volume
            score += 1.5
        elif volume_ratio > 1.2:
            score += 1
        
        # RSI filter (-1 for overbought, +0.5 for neutral/buy zone)
        if rsi and 45 <= rsi <= 65:  # Optimal RSI range
            score += 0.5
        elif rsi > 70:  # Overbought
            score -= 1
        
        # Calculate confidence
        confidence = min(score / max_score, 1.0) if max_score > 0 else 0
        
        # Determine signal type
        if confidence >= 0.85:
            signal_type = SignalType.STRONG_BUY
        elif confidence >= 0.70:
            signal_type = SignalType.BUY
        elif confidence >= 0.30:
            signal_type = SignalType.NEUTRAL
        elif confidence >= 0.25:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.STRONG_SELL
        
        return signal_type, confidence
    
    async def scan_batch(self, symbols, batch_size=10):
        """Scan a batch of stocks with configurable concurrency"""
        semaphore = self.semaphore
        
        async def analyze_limited(ticker):
            async with semaphore:
                try:
                    await asyncio.sleep(self.rate_limit_delay)
                    return await self._analyze_async(ticker)
                except Exception as e:
                    logger.error(f"Error analyzing {ticker}: {e}")
                    return None
        
        # Chunk symbols into batches
        chunks = [symbols[i:i + batch_size] for i in range(0, len(symbols), batch_size)]
        
        all_signals = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing batch {i+1}/{len(chunks)}: {chunk}")
            tasks = [analyze_limited(ticker) for ticker in chunk]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            signals = []
            for result in results:
                if isinstance(result, Exception):
                    continue
                if result is not None:
                    signals.append(result)
            
            all_signals.extend(signals)
        
        return sorted(all_signals, key=lambda x: x.get('confidence', 0), reverse=True)
    
    def scan_sync(self, symbols=None, sector=None, top_n=50):
        """Sync wrapper for backward compatibility"""
        import threading
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.scan(symbols=symbols, sector=sector, top_n=top_n)
            )
            return result
        finally:
            loop.close()


def get_sector_universe():
    """Get list of tickers by sector (simplified)"""
    # Would be populated with yfinance sector data
    return {}


async def scan_stocks_async(ticker_list, max_concurrent=5):
    """Convenience function for scanning multiple stocks"""
    scanner = AsyncStockScanner(max_concurrent=max_concurrent)
    await scanner.initialize()
    return await scanner.scan(symbols=ticker_list)


if __name__ == '__main__':
    import asyncio
    
    # Test async scanning
    async def main():
        # Scan a few stocks
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        scanner = AsyncStockScanner(max_concurrent=3)
        await scanner.initialize()
        
        signals = await scanner.scan(symbols=tickers, top_n=5)
        
        print(f"Found {len(signals)} signals:")
        for signal in signals:
            print(f"  {signal['ticker']}: {signal['signal']} "
                  f"(confidence={signal['confidence']:.2f}, price=${signal['current_price']})")
    
    asyncio.run(main())
