import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

/// ─── OHLCV Data Model ──────────────────────────────────────────────────
class StockCandle {
  final DateTime timestamp;
  final double open;
  final double high;
  final double low;
  final double close;
  final double volume;

  StockCandle({
    required this.timestamp,
    required this.open,
    required this.high,
    required this.low,
    required this.close,
    required this.volume,
  });

  bool get isBullish => close >= open;
  bool get isBearish => close < open;
  double get body => (close - open).abs();
  double get range => high - low;
  bool get isDoji => body / (range == 0 ? 1 : range) < 0.1;

  @override
  String toString() =>
      '${timestamp.toIso8601String().substring(0, 10)} O:$open H:$high L:$low C:$close V:$volume';
}

/// ─── Yahoo Finance Service ─────────────────────────────────────────────
///
/// Fetches historical OHLCV data directly from Yahoo Finance API.
/// No Flask backend required — the app works standalone.
///
class YahooFinanceService {
  final Dio _dio;
  static const String _baseUrl = 'https://query1.finance.yahoo.com/v8/finance/chart';

  YahooFinanceService({Dio? dio})
      : _dio = dio ??
            Dio(BaseOptions(
              connectTimeout: const Duration(seconds: 15),
              receiveTimeout: const Duration(seconds: 30),
              headers: {
                'User-Agent':
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
              },
            ));

  /// Fetch 6 months of daily OHLCV data for a NSE stock ticker.
  /// Ticker format: "EMMVEE.NS" (with .NS suffix).
  Future<List<StockCandle>> fetchDailyData(
    String ticker, {
    String range = '6mo',
    String interval = '1d',
  }) async {
    try {
      final response = await _dio.get(
        '$_baseUrl/$ticker',
        queryParameters: {
          'range': range,
          'interval': interval,
          'includePrePost': false,
        },
      );

      final data = response.data as Map<String, dynamic>;
      final result = data['chart']['result'] as List?;
      if (result == null || result.isEmpty) {
        debugPrint('[YahooFinance] No data for $ticker');
        return [];
      }

      final timestamps = result[0]['timestamp'] as List? ?? [];
      final quotes = result[0]['indicators']['quote'] as List? ?? [];
      if (quotes.isEmpty) return [];

      final quote = quotes[0] as Map<String, dynamic>;
      final opens = (quote['open'] as List?)?.cast<double?>() ?? [];
      final highs = (quote['high'] as List?)?.cast<double?>() ?? [];
      final lows = (quote['low'] as List?)?.cast<double?>() ?? [];
      final closes = (quote['close'] as List?)?.cast<double?>() ?? [];
      final volumes = (quote['volume'] as List?)?.cast<int?>() ?? [];

      final candles = <StockCandle>[];
      for (int i = 0; i < timestamps.length; i++) {
        final ts = timestamps[i];
        final o = opens.length > i ? opens[i] : null;
        final h = highs.length > i ? highs[i] : null;
        final l = lows.length > i ? lows[i] : null;
        final c = closes.length > i ? closes[i] : null;
        final v = volumes.length > i ? volumes[i] : null;

        // Skip null/incomplete bars
        if (o == null || h == null || l == null || c == null || v == null) {
          continue;
        }
        if (o == 0 && h == 0 && l == 0 && c == 0) continue;

        candles.add(StockCandle(
          timestamp: DateTime.fromMillisecondsSinceEpoch((ts as int) * 1000),
          open: o,
          high: h,
          low: l,
          close: c,
          volume: v.toDouble(),
        ));
      }

      // Debug timestamps
      if (candles.isNotEmpty) {
        debugPrint(
            '[YahooFinance] $ticker: ${candles.length} bars '
            '${candles.first.timestamp.toIso8601String().substring(0, 10)} → '
            '${candles.last.timestamp.toIso8601String().substring(0, 10)}');
      }

      return candles;
    } on DioException catch (e) {
      debugPrint('[YahooFinance] Error fetching $ticker: ${e.message}');
      return [];
    }
  }

  /// Fetch current price for a ticker
  Future<double> fetchCurrentPrice(String ticker) async {
    const url = 'https://query1.finance.yahoo.com/v8/finance/chart';
    try {
      final response = await _dio.get(
        '$url/$ticker',
        queryParameters: {
          'range': '1d',
          'interval': '1d',
          'includePrePost': false,
        },
      );

      final data = response.data as Map<String, dynamic>;
      final result = data['chart']['result'] as List?;
      if (result == null || result.isEmpty) return 0;

      final quote = (result[0]['indicators']['quote'] as List).first
          as Map<String, dynamic>;
      final closes = (quote['close'] as List?)?.cast<double?>() ?? [];
      return closes.where((c) => c != null).lastOrNull ?? 0;
    } catch (e) {
      return 0;
    }
  }

  /// Fetch live quotes (price + change%) for multiple tickers in parallel
  Future<Map<String, Map<String, double>>> fetchLiveQuotes(
    List<String> tickers,
  ) async {
    final results = <String, Map<String, double>>{};
    final batch = <Future<void>>[];

    for (final ticker in tickers) {
      batch.add(() async {
        const url = 'https://query1.finance.yahoo.com/v8/finance/chart';
        try {
          final response = await _dio.get(
            '$url/$ticker',
            queryParameters: {
              'range': '5d',
              'interval': '1d',
              'includePrePost': false,
            },
          );

          final data = response.data as Map<String, dynamic>;
          final result = data['chart']['result'] as List?;
          if (result == null || result.isEmpty) return;

          final quote = (result[0]['indicators']['quote'] as List).first
              as Map<String, dynamic>;
          final closes = (quote['close'] as List?)?.cast<double?>() ?? [];
          final prices =
              closes.where((c) => c != null).map((c) => c!).toList();

          if (prices.length >= 2) {
            final current = prices.last;
            final prevClose = prices[prices.length - 2];
            final change = current - prevClose;
            final changePct = prevClose > 0 ? (change / prevClose) * 100 : 0.0;
            results[ticker] = {
              'price': current,
              'change': change,
              'changePercent': changePct,
            };
          } else if (prices.length == 1) {
            results[ticker] = {
              'price': prices.last,
              'change': 0,
              'changePercent': 0,
            };
          }
        } catch (e) {
          debugPrint('[YahooFinance] Quote error $ticker: $e');
        }
      }());

      // Small stagger to avoid rate limits
      if (batch.length % 5 == 0) {
        await Future.delayed(const Duration(milliseconds: 200));
      }
    }

    await Future.wait(batch);
    return results;
  }

  /// Fetch multiple stocks in parallel
  Future<Map<String, List<StockCandle>>> fetchMultiple(
    List<String> tickers, {
    void Function(String ticker, int index, int total)? onProgress,
  }) async {
    final results = <String, List<StockCandle>>{};
    final total = tickers.length;

    for (int i = 0; i < total; i++) {
      final ticker = tickers[i];
      onProgress?.call(ticker, i, total);
      results[ticker] = await fetchDailyData(ticker);
      // Small delay to avoid rate limiting
      if (i < total - 1) {
        await Future.delayed(const Duration(milliseconds: 300));
      }
    }

    return results;
  }

  /// Fetch structured quote (price + change) for a ticker
  Future<QuoteData> fetchQuote(String ticker) async {
    final price = await fetchCurrentPrice(ticker);
    if (price == 0) return const QuoteData(currentPrice: 0);

    // Get previous close for day change
    const url = 'https://query1.finance.yahoo.com/v8/finance/chart';
    try {
      final response = await _dio.get(
        '$url/$ticker',
        queryParameters: {
          'range': '5d',
          'interval': '1d',
          'includePrePost': false,
        },
      );
      final data = response.data as Map<String, dynamic>;
      final result = data['chart']['result'] as List?;
      if (result == null || result.isEmpty) {
        return QuoteData(currentPrice: price);
      }
      final quote = (result[0]['indicators']['quote'] as List).first
          as Map<String, dynamic>;
      final closes = (quote['close'] as List?)?.cast<double?>() ?? [];
      final prices = closes.where((c) => c != null).map((c) => c!).toList();
      if (prices.length >= 2) {
        final prevClose = prices[prices.length - 2];
        final change = price - prevClose;
        final changePct = prevClose > 0 ? (change / prevClose) * 100 : 0.0;
        return QuoteData(
          currentPrice: price,
          dayChange: change,
          dayChangePct: changePct,
        );
      }
      return QuoteData(currentPrice: price);
    } catch (e) {
      return QuoteData(currentPrice: price);
    }
  }
}

/// ─── Quote Data Model ──────────────────────────────────────────────────
class QuoteData {
  final double currentPrice;
  final double dayChange;
  final double dayChangePct;

  const QuoteData({
    required this.currentPrice,
    this.dayChange = 0,
    this.dayChangePct = 0,
  });
}
