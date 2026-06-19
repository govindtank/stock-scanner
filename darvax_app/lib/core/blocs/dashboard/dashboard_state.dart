import 'package:equatable/equatable.dart';

sealed class DashboardState extends Equatable {
  const DashboardState();

  @override
  List<Object?> get props => [];
}

class DashboardInitial extends DashboardState {
  const DashboardInitial();
}

class DashboardLoading extends DashboardState {
  const DashboardLoading();
}

/// Market overview with live quotes from Yahoo Finance
class DashboardLoaded extends DashboardState {
  final List<LiveQuote> marketQuotes;
  final String? lastSync;
  final double portfolioValue;
  final double portfolioPnl;

  const DashboardLoaded({
    required this.marketQuotes,
    this.lastSync,
    this.portfolioValue = 0,
    this.portfolioPnl = 0,
  });

  @override
  List<Object?> get props => [marketQuotes, lastSync, portfolioValue, portfolioPnl];
}

class DashboardError extends DashboardState {
  final String message;

  const DashboardError(this.message);

  @override
  List<Object?> get props => [message];
}

/// Simple live quote model
class LiveQuote extends Equatable {
  final String ticker;
  final String displayName;
  final double price;
  final double change;
  final double changePercent;

  const LiveQuote({
    required this.ticker,
    required this.displayName,
    required this.price,
    required this.change,
    required this.changePercent,
  });

  bool get isUp => changePercent >= 0;
  bool get isDown => changePercent < 0;

  @override
  List<Object?> get props => [ticker, price, change, changePercent];
}
