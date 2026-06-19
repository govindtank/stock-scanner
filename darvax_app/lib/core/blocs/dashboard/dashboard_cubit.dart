import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import '../../network/yahoo_finance_service.dart';
import '../portfolio/portfolio_cubit.dart';
import '../portfolio/portfolio_state.dart';
import 'dashboard_state.dart';

class DashboardCubit extends Cubit<DashboardState> {
  final YahooFinanceService _yahoo;
  final PortfolioCubit? _portfolioCubit;

  static const List<String> _watchlist = [
    'RELIANCE.NS',
    'TCS.NS',
    'HDFCBANK.NS',
    'INFY.NS',
    'ICICIBANK.NS',
    'SBIN.NS',
    'BHARTIARTL.NS',
    'KOTAKBANK.NS',
    'BAJFINANCE.NS',
    'TATAMOTORS.NS',
    'M&M.NS',
    'AXISBANK.NS',
    'MARUTI.NS',
    'TITAN.NS',
    'SUNPHARMA.NS',
    'WIPRO.NS',
    'NTPC.NS',
    'POWERGRID.NS',
    'TRENT.NS',
    'HINDUNILVR.NS',
    'ITC.NS',
    'HCLTECH.NS',
    'LT.NS',
    'ASIANPAINT.NS',
  ];

  static const Map<String, String> _nameMap = {
    'RELIANCE.NS': 'Reliance',
    'TCS.NS': 'TCS',
    'HDFCBANK.NS': 'HDFC Bank',
    'INFY.NS': 'Infosys',
    'ICICIBANK.NS': 'ICICI Bank',
    'SBIN.NS': 'SBI',
    'BHARTIARTL.NS': 'Bharti Airtel',
    'KOTAKBANK.NS': 'Kotak Bank',
    'BAJFINANCE.NS': 'Bajaj Finance',
    'TATAMOTORS.NS': 'Tata Motors',
    'M&M.NS': 'M&M',
    'AXISBANK.NS': 'Axis Bank',
    'MARUTI.NS': 'Maruti',
    'TITAN.NS': 'Titan',
    'SUNPHARMA.NS': 'Sun Pharma',
    'WIPRO.NS': 'Wipro',
    'NTPC.NS': 'NTPC',
    'POWERGRID.NS': 'Power Grid',
    'TRENT.NS': 'Trent',
    'HINDUNILVR.NS': 'HUL',
    'ITC.NS': 'ITC',
    'HCLTECH.NS': 'HCL Tech',
    'LT.NS': 'L&T',
    'ASIANPAINT.NS': 'Asian Paints',
  };

  DashboardCubit({
    YahooFinanceService? yahooService,
    PortfolioCubit? portfolioCubit,
  })  : _yahoo = yahooService ?? YahooFinanceService(),
        _portfolioCubit = portfolioCubit,
        super(const DashboardInitial()) {
    load();
  }

  void load() {
    emit(const DashboardLoading());
    _fetchMarketData();
  }

  Future<void> _fetchMarketData() async {
    try {
      final quotes = await _yahoo.fetchLiveQuotes(_watchlist);

      final marketQuotes = <LiveQuote>[];
      for (final ticker in _watchlist) {
        final q = quotes[ticker];
        if (q != null) {
          marketQuotes.add(LiveQuote(
            ticker: ticker.replaceAll('.NS', ''),
            displayName: _nameMap[ticker] ?? ticker.replaceAll('.NS', ''),
            price: q['price'] ?? 0,
            change: q['change'] ?? 0,
            changePercent: q['changePercent'] ?? 0,
          ));
        }
      }

      // Get portfolio value from PortfolioCubit if available
      double portfolioValue = 0;
      double portfolioPnl = 0;
      if (_portfolioCubit != null) {
        final pState = _portfolioCubit.state;
        if (pState is PortfolioLoaded) {
          portfolioValue = pState.totalValue;
          portfolioPnl = pState.totalPnl;
        }
      }

      if (isClosed) return;
      emit(DashboardLoaded(
        marketQuotes: marketQuotes,
        lastSync: DateTime.now().toIso8601String(),
        portfolioValue: portfolioValue,
        portfolioPnl: portfolioPnl,
      ));
    } catch (e) {
      if (isClosed) return;
      emit(DashboardError('Failed to load market data: $e'));
    }
  }

  void refresh() => load();
}
