class WishlistStock {
  final String ticker;
  final String name;
  final double price;
  final double rsi;
  final double dailyVolPct;
  final double volumeRatio;
  final double drawdownPct;
  final double near52whPct;
  final double pctAboveSma20;
  final String smaTrend;
  final String recommendation;
  final String conviction;
  final String reason;
  final bool dataUnavailable;
  final List<String> signals;

  WishlistStock({
    required this.ticker,
    this.name = '',
    this.price = 0,
    this.rsi = 50,
    this.dailyVolPct = 0,
    this.volumeRatio = 0,
    this.drawdownPct = 0,
    this.near52whPct = 0,
    this.pctAboveSma20 = 0,
    this.smaTrend = 'neutral',
    this.recommendation = 'hold',
    this.conviction = 'low',
    this.reason = '',
    this.dataUnavailable = false,
    this.signals = const [],
  });

  factory WishlistStock.fromJson(Map<String, dynamic> json) => WishlistStock(
        ticker: json['ticker'] ?? json['symbol'] ?? '',
        name: json['name'] ?? '',
        price: (json['price'] ?? json['ltp'] ?? 0).toDouble(),
        rsi: (json['rsi'] ?? 50).toDouble(),
        dailyVolPct: (json['daily_vol_pct'] ?? 0).toDouble(),
        volumeRatio: (json['volume_ratio'] ?? 0).toDouble(),
        drawdownPct: (json['drawdown_pct'] ?? 0).toDouble(),
        near52whPct: (json['near_52wh_pct'] ?? 0).toDouble(),
        pctAboveSma20: (json['pct_above_sma20'] ?? 0).toDouble(),
        smaTrend: json['sma_trend'] ?? 'neutral',
        recommendation: json['recommendation'] ?? 'hold',
        conviction: json['conviction'] ?? 'low',
        reason: json['reason'] ?? '',
        dataUnavailable: json['data_unavailable'] ?? false,
        signals: (json['signals'] as List? ?? []).cast<String>(),
      );
}
