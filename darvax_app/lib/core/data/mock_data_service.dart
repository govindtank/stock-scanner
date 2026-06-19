import '../models/real_holding.dart';
import '../models/full_portfolio.dart';
import '../models/mutual_fund.dart';
import '../models/bond_holding.dart';
import '../models/dv_pattern.dart';
import '../models/wishlist_stock.dart';

/// Provides rich mock data so the app runs without a backend.
/// Swap for a real API client later.
class MockDataService {

  // ── Your real portfolio (15 holdings, ₹1,53,824, +14.43%) ──
  static List<RealHolding> get holdings => [
    RealHolding(stock: 'HINDCOPPER.NS', stockName: 'Hindustan Copper', quantity: 85, avgPrice: 215.50, currentPrice: 440.80, investedValue: 18317.50, currentValue: 37468.00, unrealizedPnl: 19150.50, unrealizedPnlPct: 104.55, dayChange: 3.20, dayChangePct: 0.73),
    RealHolding(stock: 'BEL.NS', stockName: 'Bharat Electronics', quantity: 120, avgPrice: 148.20, currentPrice: 245.60, investedValue: 17784.00, currentValue: 29472.00, unrealizedPnl: 11688.00, unrealizedPnlPct: 65.72, dayChange: 1.80, dayChangePct: 0.74),
    RealHolding(stock: 'TATATECH.NS', stockName: 'Tata Technologies', quantity: 30, avgPrice: 445.00, currentPrice: 666.80, investedValue: 13350.00, currentValue: 20004.00, unrealizedPnl: 6654.00, unrealizedPnlPct: 49.84, dayChange: -2.10, dayChangePct: -0.31),
    RealHolding(stock: 'NTPC.NS', stockName: 'NTPC Ltd', quantity: 200, avgPrice: 245.30, currentPrice: 362.40, investedValue: 49060.00, currentValue: 72480.00, unrealizedPnl: 23420.00, unrealizedPnlPct: 47.74, dayChange: 4.50, dayChangePct: 1.26),
    RealHolding(stock: 'IRFC.NS', stockName: 'Indian Railway Finance', quantity: 300, avgPrice: 98.50, currentPrice: 138.20, investedValue: 29550.00, currentValue: 41460.00, unrealizedPnl: 11910.00, unrealizedPnlPct: 40.30, dayChange: 1.10, dayChangePct: 0.80),
    RealHolding(stock: 'RITES.NS', stockName: 'RITES Ltd', quantity: 50, avgPrice: 285.00, currentPrice: 390.40, investedValue: 14250.00, currentValue: 19520.00, unrealizedPnl: 5270.00, unrealizedPnlPct: 36.98, dayChange: 0.80, dayChangePct: 0.21),
    RealHolding(stock: 'PFC.NS', stockName: 'Power Finance Corp', quantity: 100, avgPrice: 235.00, currentPrice: 310.20, investedValue: 23500.00, currentValue: 31020.00, unrealizedPnl: 7520.00, unrealizedPnlPct: 32.00, dayChange: 2.30, dayChangePct: 0.75),
    RealHolding(stock: 'IREDA.NS', stockName: 'IREDA', quantity: 150, avgPrice: 112.80, currentPrice: 146.50, investedValue: 16920.00, currentValue: 21975.00, unrealizedPnl: 5055.00, unrealizedPnlPct: 29.88, dayChange: 1.60, dayChangePct: 1.10),
    RealHolding(stock: 'TCS.NS', stockName: 'Tata Consultancy', quantity: 15, avgPrice: 3850.00, currentPrice: 4175.50, investedValue: 57750.00, currentValue: 62632.50, unrealizedPnl: 4882.50, unrealizedPnlPct: 8.45, dayChange: -12.00, dayChangePct: -0.29),
    RealHolding(stock: 'HDFCBANK.NS', stockName: 'HDFC Bank', quantity: 35, avgPrice: 1620.00, currentPrice: 1725.80, investedValue: 56700.00, currentValue: 60403.00, unrealizedPnl: 3703.00, unrealizedPnlPct: 6.53, dayChange: 5.20, dayChangePct: 0.30),
    RealHolding(stock: 'NEPHROPLUS.NS', stockName: 'Nephroplus', quantity: 52, avgPrice: 690.00, currentPrice: 743.65, investedValue: 35880.00, currentValue: 38669.80, unrealizedPnl: 2789.80, unrealizedPnlPct: 7.78, dayChange: 3.45, dayChangePct: 0.47),
    RealHolding(stock: 'RELIANCE.NS', stockName: 'Reliance Industries', quantity: 20, avgPrice: 2850.00, currentPrice: 2960.30, investedValue: 57000.00, currentValue: 59206.00, unrealizedPnl: 2206.00, unrealizedPnlPct: 3.87, dayChange: -8.50, dayChangePct: -0.29),
    RealHolding(stock: 'SBIN.NS', stockName: 'SBI', quantity: 80, avgPrice: 680.00, currentPrice: 715.20, investedValue: 54400.00, currentValue: 57216.00, unrealizedPnl: 2816.00, unrealizedPnlPct: 5.18, dayChange: 2.80, dayChangePct: 0.39),
    RealHolding(stock: 'TMPV.NS', stockName: 'Tata Motors Passenger Vehicles', quantity: 60, avgPrice: 520.00, currentPrice: 485.30, investedValue: 31200.00, currentValue: 29118.00, unrealizedPnl: -2082.00, unrealizedPnlPct: -6.67, dayChange: -3.10, dayChangePct: -0.63),
    RealHolding(stock: 'PINELABS.NS', stockName: 'Piramal Pharma', quantity: 100, avgPrice: 128.00, currentPrice: 87.60, investedValue: 12800.00, currentValue: 8760.00, unrealizedPnl: -4040.00, unrealizedPnlPct: -31.55, dayChange: -1.20, dayChangePct: -1.35),
  ];

  static FullPortfolio get fullPortfolio {
    final h = holdings;
    final stocksValue = h.fold<double>(0, (s, e) => s + e.currentValue);
    final invested = h.fold<double>(0, (s, e) => s + e.investedValue);
    final returns = stocksValue - invested;
    return FullPortfolio(
      totalValue: stocksValue + 25000, // + cash
      stocksValue: stocksValue,
      mfValue: 45000,
      bondsValue: 30000,
      cashValue: 25000,
      holdings: h,
      mutualFunds: _mutualFunds,
      bonds: _bonds,
      overallReturns: returns,
      overallReturnsPct: invested > 0 ? (returns / invested) * 100 : 0,
      riskScore: 62.5,
      riskLevel: 'moderate',
    );
  }

  static List<MutualFund> get _mutualFunds => [
    MutualFund(name: 'Parag Parikh Flexi Cap', amc: 'PPFAS', category: 'flexi-cap', invested: 15000, currentValue: 18240, returns: 3240, expenseRatio: 0.89, nav: 62.45, riskLevel: 'moderate'),
    MutualFund(name: 'Quant Small Cap', amc: 'Quant AMC', category: 'small-cap', invested: 10000, currentValue: 13450, returns: 3450, expenseRatio: 1.25, nav: 185.30, riskLevel: 'high'),
    MutualFund(name: 'SBI Bluechip', amc: 'SBI MF', category: 'large-cap', invested: 20000, currentValue: 22310, returns: 2310, expenseRatio: 0.65, nav: 72.80, riskLevel: 'low'),
  ];

  static List<BondHolding> get _bonds => [
    BondHolding(name: '7.10% GOI 2030', issuer: 'Government of India', rating: 'AAA', faceValue: 1000, couponRate: 7.10, currentPrice: 985, maturityDate: DateTime(2030, 6, 15), ytm: 7.32, quantity: 10),
    BondHolding(name: '8.25% NHAI 2029', issuer: 'NHAI', rating: 'AAA', faceValue: 1000, couponRate: 8.25, currentPrice: 1012, maturityDate: DateTime(2029, 3, 20), ytm: 8.05, quantity: 15),
    BondHolding(name: '9.50% REC 2028', issuer: 'REC Ltd', rating: 'AAA', faceValue: 1000, couponRate: 9.50, currentPrice: 1040, maturityDate: DateTime(2028, 11, 30), ytm: 8.85, quantity: 5),
  ];

  // ── DV Patterns ──
  static List<DVPattern> get dvPatterns => [
    DVPattern(ticker: 'ATHERENERGY.NS', price: 1270.50, dvScore: 9.2, dailyVol: 2.8, pctAboveSma20: 8.4, near52whPct: 94.2, volTrend: 2.1, rsi: 67.3, drawdown: 5.8, currentBreakout: true, rsiTrend: 'rising', category: 'bull'),
    DVPattern(ticker: 'CENTUM.NS', price: 38.50, dvScore: 8.7, dailyVol: 4.2, pctAboveSma20: 12.6, near52whPct: 88.5, volTrend: 3.4, rsi: 71.2, drawdown: 12.4, currentBreakout: true, rsiTrend: 'rising', category: 'bull'),
    DVPattern(ticker: 'NEPHROPLUS.NS', price: 743.65, dvScore: 7.8, dailyVol: 1.9, pctAboveSma20: 5.2, near52whPct: 76.8, volTrend: 1.5, rsi: 59.8, drawdown: 15.2, currentBreakout: false, rsiTrend: 'neutral', category: 'bull'),
    DVPattern(ticker: 'RELIANCE.NS', price: 2960.30, dvScore: 6.5, dailyVol: 1.2, pctAboveSma20: 2.1, near52whPct: 68.4, volTrend: 0.8, rsi: 54.6, drawdown: 8.2, currentBreakout: false, rsiTrend: 'neutral', category: 'accel'),
    DVPattern(ticker: 'HINDCOPPER.NS', price: 440.80, dvScore: 8.1, dailyVol: 3.5, pctAboveSma20: 10.8, near52whPct: 91.5, volTrend: 2.8, rsi: 65.2, drawdown: 4.5, currentBreakout: true, rsiTrend: 'rising', category: 'bull'),
    DVPattern(ticker: 'TMPV.NS', price: 485.30, dvScore: 3.2, dailyVol: 1.8, pctAboveSma20: -4.5, near52whPct: 52.3, volTrend: -0.5, rsi: 42.1, drawdown: 22.8, currentBreakout: false, rsiTrend: 'falling', category: 'bear'),
  ];

  // ── Wishlist ──
  static List<WishlistStock> get wishlist => [
    WishlistStock(ticker: 'HINDCOPPER.NS', name: 'Hindustan Copper', price: 440.80, rsi: 65.2, dailyVolPct: 3.5, volumeRatio: 1.8, drawdownPct: 4.5, near52whPct: 91.5, pctAboveSma20: 10.8, smaTrend: 'bullish', recommendation: 'buy', conviction: 'high', reason: 'Strong volume breakout with RSI in sweet spot', signals: ['Volume surge', 'RSI bullish', 'Above SMA20']),
    WishlistStock(ticker: 'BEL.NS', name: 'Bharat Electronics', price: 245.60, rsi: 62.8, dailyVolPct: 2.2, volumeRatio: 1.4, drawdownPct: 6.8, near52whPct: 85.2, pctAboveSma20: 7.5, smaTrend: 'bullish', recommendation: 'buy', conviction: 'high', reason: 'Defence sector momentum, strong trend', signals: ['Trend strength', 'Sector tailwind']),
    WishlistStock(ticker: 'TATATECH.NS', name: 'Tata Technologies', price: 666.80, rsi: 58.4, dailyVolPct: 1.6, volumeRatio: 0.9, drawdownPct: 12.5, near52whPct: 72.4, pctAboveSma20: 3.2, smaTrend: 'neutral', recommendation: 'hold', conviction: 'medium', reason: 'Consolidating after recent run-up', signals: ['Consolidation']),
    WishlistStock(ticker: 'NTPC.NS', name: 'NTPC Ltd', price: 362.40, rsi: 55.1, dailyVolPct: 1.2, volumeRatio: 1.1, drawdownPct: 8.2, near52whPct: 68.5, pctAboveSma20: 2.1, smaTrend: 'neutral', recommendation: 'hold', conviction: 'medium', reason: 'Stable utility with dividend yield', signals: []),
    WishlistStock(ticker: 'IRFC.NS', name: 'Indian Railway Finance', price: 138.20, rsi: 64.5, dailyVolPct: 4.8, volumeRatio: 2.2, drawdownPct: 10.5, near52whPct: 81.3, pctAboveSma20: 6.8, smaTrend: 'bullish', recommendation: 'buy', conviction: 'high', reason: 'Railway momentum with high volume', signals: ['High volume', 'Momentum']),
    WishlistStock(ticker: 'PGCIL.NS', name: 'Power Grid Corp', price: 298.50, rsi: 52.3, dailyVolPct: 1.1, volumeRatio: 0.7, drawdownPct: 5.2, near52whPct: 62.8, pctAboveSma20: 1.5, smaTrend: 'neutral', recommendation: 'hold', conviction: 'low', reason: 'Low volatility, awaiting breakout', signals: []),
    WishlistStock(ticker: 'TITAN.NS', name: 'Titan Company', price: 3450.00, rsi: 48.2, dailyVolPct: 1.5, volumeRatio: 0.8, drawdownPct: 14.2, near52whPct: 55.6, pctAboveSma20: -2.8, smaTrend: 'bearish', recommendation: 'watch', conviction: 'low', reason: 'Correcting from highs, wait for reversal', signals: ['Downtrend']),
    WishlistStock(ticker: 'HDFCBANK.NS', name: 'HDFC Bank', price: 1725.80, rsi: 56.8, dailyVolPct: 1.0, volumeRatio: 0.9, drawdownPct: 6.5, near52whPct: 72.8, pctAboveSma20: 3.5, smaTrend: 'neutral', recommendation: 'hold', conviction: 'medium', reason: 'Stable large-cap banking', signals: []),
  ];

  // ── System Trades (for Arena) ──
  static List<Map<String, dynamic>> get systemTradesData => [
    {'stock': 'ATHERENERGY.NS', 'action': 'buy', 'quantity': 25, 'entry_price': 1185.00, 'exit_price': 1270.50, 'pnl': 2137.50, 'pnl_percent': 7.22, 'status': 'closed'},
    {'stock': 'CENTUM.NS', 'action': 'buy', 'quantity': 500, 'entry_price': 34.20, 'exit_price': 38.50, 'pnl': 2150.00, 'pnl_percent': 12.57, 'status': 'closed'},
    {'stock': 'HINDCOPPER.NS', 'action': 'buy', 'quantity': 50, 'entry_price': 410.00, 'exit_price': 440.80, 'pnl': 1540.00, 'pnl_percent': 7.51, 'status': 'closed'},
    {'stock': 'TMPV.NS', 'action': 'sell', 'quantity': 100, 'entry_price': 510.00, 'exit_price': 540.50, 'pnl': 3050.00, 'pnl_percent': 5.98, 'status': 'closed'},
    {'stock': 'NTPC.NS', 'action': 'buy', 'quantity': 80, 'entry_price': 350.00, 'exit_price': 362.40, 'pnl': 992.00, 'pnl_percent': 3.54, 'status': 'closed'},
    {'stock': 'PINELABS.NS', 'action': 'buy', 'quantity': 200, 'entry_price': 95.00, 'exit_price': 87.60, 'pnl': -1480.00, 'pnl_percent': -7.79, 'status': 'closed'},
    {'stock': 'BEL.NS', 'action': 'buy', 'quantity': 40, 'entry_price': 232.00, 'exit_price': 280.50, 'pnl': 1940.00, 'pnl_percent': 20.91, 'status': 'closed'},
  ];
}
