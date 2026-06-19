class RealHolding {
  final String stock;
  final String stockName;
  final double quantity;
  final double avgPrice;
  final double currentPrice;
  final double investedValue;
  final double currentValue;
  final double unrealizedPnl;
  final double unrealizedPnlPct;
  final double dayChange;
  final double dayChangePct;

  RealHolding({
    required this.stock,
    required this.stockName,
    required this.quantity,
    required this.avgPrice,
    required this.currentPrice,
    required this.investedValue,
    required this.currentValue,
    required this.unrealizedPnl,
    required this.unrealizedPnlPct,
    this.dayChange = 0,
    this.dayChangePct = 0,
  });

  factory RealHolding.fromJson(Map<String, dynamic> json) {
    return RealHolding(
      stock: json['stock'] ?? '',
      stockName: json['stock_name'] ?? json['stock'] ?? '',
      quantity: (json['quantity'] ?? 0).toDouble(),
      avgPrice: (json['avg_price'] ?? 0).toDouble(),
      currentPrice: (json['current_price'] ?? 0).toDouble(),
      investedValue: (json['invested_value'] ?? 0).toDouble(),
      currentValue: (json['current_value'] ?? 0).toDouble(),
      unrealizedPnl: (json['unrealized_pnl'] ?? 0).toDouble(),
      unrealizedPnlPct: (json['unrealized_pnl_pct'] ?? 0).toDouble(),
      dayChange: (json['day_change'] ?? 0).toDouble(),
      dayChangePct: (json['day_change_pct'] ?? 0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
    'stock': stock,
    'stock_name': stockName,
    'quantity': quantity,
    'avg_price': avgPrice,
    'current_price': currentPrice,
    'invested_value': investedValue,
    'current_value': currentValue,
    'unrealized_pnl': unrealizedPnl,
    'unrealized_pnl_pct': unrealizedPnlPct,
    'day_change': dayChange,
    'day_change_pct': dayChangePct,
  };
}
