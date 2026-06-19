import 'arena_trade.dart';

class ArenaMatchup {
  final double userPnl;
  final double systemPnl;
  final double userWinRate;
  final double systemWinRate;
  final int userWins;
  final int systemWins;
  final int userLosses;
  final int systemLosses;
  final int userTotalTrades;
  final int systemTotalTrades;
  final double bestTrade;
  final double worstTrade;
  final List<ArenaTrade> trades;
  final DateTime startedAt;

  ArenaMatchup({
    this.userPnl = 0,
    this.systemPnl = 0,
    this.userWinRate = 0,
    this.systemWinRate = 0,
    this.userWins = 0,
    this.systemWins = 0,
    this.userLosses = 0,
    this.systemLosses = 0,
    this.userTotalTrades = 0,
    this.systemTotalTrades = 0,
    this.bestTrade = 0,
    this.worstTrade = 0,
    this.trades = const [],
    DateTime? startedAt,
  }) : startedAt = startedAt ?? DateTime.now();

  String get winner {
    if (userPnl > systemPnl) return 'You 🏆';
    if (systemPnl > userPnl) return 'System 🤖';
    return 'Tied ⚖️';
  }

  ArenaMatchup copyWith({
    double? userPnl,
    double? systemPnl,
    double? userWinRate,
    double? systemWinRate,
    int? userWins,
    int? systemWins,
    int? userLosses,
    int? systemLosses,
    int? userTotalTrades,
    int? systemTotalTrades,
    double? bestTrade,
    double? worstTrade,
    List<ArenaTrade>? trades,
  }) {
    return ArenaMatchup(
      userPnl: userPnl ?? this.userPnl,
      systemPnl: systemPnl ?? this.systemPnl,
      userWinRate: userWinRate ?? this.userWinRate,
      systemWinRate: systemWinRate ?? this.systemWinRate,
      userWins: userWins ?? this.userWins,
      systemWins: systemWins ?? this.systemWins,
      userLosses: userLosses ?? this.userLosses,
      systemLosses: systemLosses ?? this.systemLosses,
      userTotalTrades: userTotalTrades ?? this.userTotalTrades,
      systemTotalTrades: systemTotalTrades ?? this.systemTotalTrades,
      bestTrade: bestTrade ?? this.bestTrade,
      worstTrade: worstTrade ?? this.worstTrade,
      trades: trades ?? this.trades,
      startedAt: startedAt,
    );
  }
}
