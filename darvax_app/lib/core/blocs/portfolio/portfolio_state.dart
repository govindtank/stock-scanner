import 'package:equatable/equatable.dart';

/// A single holding in the user's portfolio
class PortfolioHolding {
  final String ticker;
  final String name;
  final double quantity;
  final double avgPrice;
  final double currentPrice;
  final double dayChange;

  const PortfolioHolding({
    required this.ticker,
    this.name = '',
    required this.quantity,
    required this.avgPrice,
    this.currentPrice = 0,
    this.dayChange = 0,
  });

  double get investedValue => quantity * avgPrice;
  double get currentValue => quantity * currentPrice;
  double get unrealizedPnl => currentValue - investedValue;
  double get unrealizedPnlPct =>
      investedValue > 0 ? ((currentPrice - avgPrice) / avgPrice) * 100 : 0;

  PortfolioHolding copyWith({
    String? ticker,
    String? name,
    double? quantity,
    double? avgPrice,
    double? currentPrice,
    double? dayChange,
  }) {
    return PortfolioHolding(
      ticker: ticker ?? this.ticker,
      name: name ?? this.name,
      quantity: quantity ?? this.quantity,
      avgPrice: avgPrice ?? this.avgPrice,
      currentPrice: currentPrice ?? this.currentPrice,
      dayChange: dayChange ?? this.dayChange,
    );
  }

  Map<String, dynamic> toJson() => {
    'ticker': ticker,
    'name': name,
    'quantity': quantity,
    'avgPrice': avgPrice,
  };

  factory PortfolioHolding.fromJson(Map<String, dynamic> json) =>
      PortfolioHolding(
        ticker: json['ticker'] as String,
        name: json['name'] as String? ?? '',
        quantity: (json['quantity'] as num).toDouble(),
        avgPrice: (json['avgPrice'] as num).toDouble(),
      );
}

// ─── States ───

sealed class PortfolioState extends Equatable {
  const PortfolioState();
  @override
  List<Object?> get props => [];
}

class PortfolioInitial extends PortfolioState {
  const PortfolioInitial();
}

class PortfolioLoading extends PortfolioState {
  const PortfolioLoading();
}

class PortfolioLoaded extends PortfolioState {
  final List<PortfolioHolding> holdings;
  final bool pricesUpdating;

  const PortfolioLoaded({required this.holdings, this.pricesUpdating = false});

  double get totalValue =>
      holdings.fold<double>(0, (s, h) => s + h.currentValue);
  double get totalInvested =>
      holdings.fold<double>(0, (s, h) => s + h.investedValue);
  double get totalPnl => totalValue - totalInvested;
  double get totalPnlPct =>
      totalInvested > 0 ? (totalPnl / totalInvested) * 100 : 0;

  PortfolioLoaded copyWith({
    List<PortfolioHolding>? holdings,
    bool? pricesUpdating,
  }) {
    return PortfolioLoaded(
      holdings: holdings ?? this.holdings,
      pricesUpdating: pricesUpdating ?? this.pricesUpdating,
    );
  }

  @override
  List<Object?> get props => [holdings, pricesUpdating];
}

class PortfolioError extends PortfolioState {
  final String message;
  const PortfolioError(this.message);
  @override
  List<Object?> get props => [message];
}
