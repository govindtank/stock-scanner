enum TradeSide { user, system }
enum TradeAction { buy, sell }
enum TradeStatus { open, closed }
enum TradeDirection { long, short }

class ArenaTrade {
  final String id;
  final String stock;
  final TradeSide side;
  final TradeAction action;
  final TradeDirection direction;
  final int quantity;
  final double entryPrice;
  final double? exitPrice;
  final DateTime entryTime;
  final DateTime? exitTime;
  final TradeStatus status;
  final double pnl;
  final double pnlPercent;
  final String strategyNotes;

  ArenaTrade({
    required this.id,
    required this.stock,
    required this.side,
    required this.action,
    this.direction = TradeDirection.long,
    required this.quantity,
    required this.entryPrice,
    this.exitPrice,
    required this.entryTime,
    this.exitTime,
    required this.status,
    this.pnl = 0,
    this.pnlPercent = 0,
    this.strategyNotes = '',
  });

  ArenaTrade copyWith({
    String? id,
    String? stock,
    TradeSide? side,
    TradeAction? action,
    TradeDirection? direction,
    int? quantity,
    double? entryPrice,
    double? exitPrice,
    DateTime? entryTime,
    DateTime? exitTime,
    TradeStatus? status,
    double? pnl,
    double? pnlPercent,
    String? strategyNotes,
  }) {
    return ArenaTrade(
      id: id ?? this.id,
      stock: stock ?? this.stock,
      side: side ?? this.side,
      action: action ?? this.action,
      direction: direction ?? this.direction,
      quantity: quantity ?? this.quantity,
      entryPrice: entryPrice ?? this.entryPrice,
      exitPrice: exitPrice ?? this.exitPrice,
      entryTime: entryTime ?? this.entryTime,
      exitTime: exitTime ?? this.exitTime,
      status: status ?? this.status,
      pnl: pnl ?? this.pnl,
      pnlPercent: pnlPercent ?? this.pnlPercent,
      strategyNotes: strategyNotes ?? this.strategyNotes,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'stock': stock,
        'side': side.name,
        'action': action.name,
        'direction': direction.name,
        'quantity': quantity,
        'entry_price': entryPrice,
        'exit_price': exitPrice,
        'entry_time': entryTime.toIso8601String(),
        'exit_time': exitTime?.toIso8601String(),
        'status': status.name,
        'pnl': pnl,
        'pnl_percent': pnlPercent,
        'strategy_notes': strategyNotes,
      };

  factory ArenaTrade.fromJson(Map<String, dynamic> json) => ArenaTrade(
        id: json['id'] ?? '',
        stock: json['stock'] ?? '',
        side: TradeSide.values.firstWhere(
          (e) => e.name == json['side'],
          orElse: () => TradeSide.user,
        ),
        action: TradeAction.values.firstWhere(
          (e) => e.name == json['action'],
          orElse: () => TradeAction.buy,
        ),
        direction: TradeDirection.values.firstWhere(
          (e) => e.name == json['direction'],
          orElse: () => TradeDirection.long,
        ),
        quantity: json['quantity'] ?? 0,
        entryPrice: (json['entry_price'] ?? 0).toDouble(),
        exitPrice: (json['exit_price'] as num?)?.toDouble(),
        entryTime: json['entry_time'] != null
            ? DateTime.parse(json['entry_time'])
            : DateTime.now(),
        exitTime: json['exit_time'] != null
            ? DateTime.parse(json['exit_time'])
            : null,
        status: TradeStatus.values.firstWhere(
          (e) => e.name == json['status'],
          orElse: () => TradeStatus.open,
        ),
        pnl: (json['pnl'] ?? 0).toDouble(),
        pnlPercent: (json['pnl_percent'] ?? 0).toDouble(),
        strategyNotes: json['strategy_notes'] ?? '',
      );
}
