import 'dart:convert';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:hive_flutter/hive_flutter.dart';
import '../../network/yahoo_finance_service.dart';
import 'portfolio_state.dart';

class PortfolioCubit extends Cubit<PortfolioState> {
  final YahooFinanceService _yahoo;
  static const _boxName = 'portfolio_holdings';

  PortfolioCubit({YahooFinanceService? yahoo})
      : _yahoo = yahoo ?? YahooFinanceService(),
        super(const PortfolioInitial()) {
    _init();
  }

  Future<void> _init() async {
    emit(const PortfolioLoading());
    try {
      final holdings = _loadHoldings();
      if (holdings.isEmpty) {
        // Pre-fill with user's real holdings from memory
        await _seedDefaultHoldings();
        emit(PortfolioLoaded(holdings: _loadHoldings()));
      } else {
        emit(PortfolioLoaded(holdings: holdings));
      }
      // Auto-refresh prices
      await refreshPrices();
    } catch (e) {
      if (!isClosed) {
        emit(PortfolioError('Failed to load: $e'));
      }
    }
  }

  List<PortfolioHolding> _loadHoldings() {
    final box = Hive.box<String>(_boxName);
    final data = box.get('holdings');
    if (data == null || data.isEmpty) return [];
    try {
      final list = jsonDecode(data) as List;
      return list
          .map((e) => PortfolioHolding.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> _saveHoldings(List<PortfolioHolding> holdings) async {
    final box = Hive.box<String>(_boxName);
    await box.put(
      'holdings',
      jsonEncode(holdings.map((h) => h.toJson()).toList()),
    );
  }

  Future<void> _seedDefaultHoldings() async {
    final defaults = [
      PortfolioHolding(ticker: 'HINDCOPPER.NS', name: 'Hindustan Copper', quantity: 50, avgPrice: 320),
      PortfolioHolding(ticker: 'BEL.NS', name: 'Bharat Electronics', quantity: 100, avgPrice: 350),
      PortfolioHolding(ticker: 'TATATECH.NS', name: 'Tata Technologies', quantity: 30, avgPrice: 1200),
      PortfolioHolding(ticker: 'PINELABS.NS', name: 'Pine Labs', quantity: 20, avgPrice: 850),
      PortfolioHolding(ticker: 'NEPHROPLUS.NS', name: 'Nephro Plus', quantity: 62, avgPrice: 640),
      PortfolioHolding(ticker: 'TRENT.NS', name: 'Trent', quantity: 15, avgPrice: 4500),
      PortfolioHolding(ticker: 'RELIANCE.NS', name: 'Reliance Industries', quantity: 10, avgPrice: 2900),
      PortfolioHolding(ticker: 'HDFCBANK.NS', name: 'HDFC Bank', quantity: 25, avgPrice: 1650),
      PortfolioHolding(ticker: 'ICICIBANK.NS', name: 'ICICI Bank', quantity: 40, avgPrice: 1100),
      PortfolioHolding(ticker: 'SBIN.NS', name: 'SBI', quantity: 30, avgPrice: 750),
      PortfolioHolding(ticker: 'INFY.NS', name: 'Infosys', quantity: 20, avgPrice: 1550),
      PortfolioHolding(ticker: 'BAJFINANCE.NS', name: 'Bajaj Finance', quantity: 10, avgPrice: 7200),
      PortfolioHolding(ticker: 'M&M.NS', name: 'Mahindra & Mahindra', quantity: 25, avgPrice: 2600),
      PortfolioHolding(ticker: 'BELRISE.NS', name: 'BEL Rise', quantity: 50, avgPrice: 180),
      PortfolioHolding(ticker: 'LALPATHLAB.NS', name: 'Dr. Lal Path Labs', quantity: 10, avgPrice: 2800),
    ];
    await _saveHoldings(defaults);
  }

  /// Refresh all live prices from Yahoo Finance
  Future<void> refreshPrices() async {
    final current = state;
    if (current is! PortfolioLoaded) return;
    emit(current.copyWith(pricesUpdating: true));

    try {
      final updated = <PortfolioHolding>[];
      for (final h in current.holdings) {
        try {
          final quote = await _yahoo.fetchQuote(h.ticker);
          updated.add(h.copyWith(
            currentPrice: quote.currentPrice,
            dayChange: quote.dayChange,
          ));
        } catch (e) {
          // Keep old price if fetch fails
          updated.add(h);
        }
      }
      if (!isClosed) {
        emit(PortfolioLoaded(holdings: updated, pricesUpdating: false));
      }
    } catch (e) {
      if (!isClosed) {
        emit(PortfolioLoaded(
          holdings: current.holdings,
          pricesUpdating: false,
        ));
      }
    }
  }

  /// Add a new holding
  Future<void> addHolding(
    String ticker, {
    String name = '',
    required double quantity,
    required double avgPrice,
  }) async {
    final current = state;
    if (current is! PortfolioLoaded) return;
    final cleanTicker = ticker.endsWith('.NS') ? ticker : '$ticker.NS';
    final updated = [
      ...current.holdings,
      PortfolioHolding(
        ticker: cleanTicker,
        name: name,
        quantity: quantity,
        avgPrice: avgPrice,
      ),
    ];
    await _saveHoldings(updated);
    emit(PortfolioLoaded(holdings: updated));
  }

  /// Remove a holding
  Future<void> removeHolding(String ticker) async {
    final current = state;
    if (current is! PortfolioLoaded) return;
    final updated = current.holdings.where((h) => h.ticker != ticker).toList();
    await _saveHoldings(updated);
    emit(PortfolioLoaded(holdings: updated));
  }

  /// Update a holding (edit quantity/avg price)
  Future<void> updateHolding(
    String ticker, {
    double? quantity,
    double? avgPrice,
  }) async {
    final current = state;
    if (current is! PortfolioLoaded) return;
    final updated = current.holdings.map((h) {
      if (h.ticker == ticker) {
        return h.copyWith(quantity: quantity, avgPrice: avgPrice);
      }
      return h;
    }).toList();
    await _saveHoldings(updated);
    emit(PortfolioLoaded(holdings: updated));
  }
}
