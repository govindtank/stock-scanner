class DVPattern {
  final String ticker;
  final double price;
  final double dvScore;
  final double dailyVol;
  final double pctAboveSma20;
  final double near52whPct;
  final double volTrend;
  final double rsi;
  final double drawdown;
  final bool currentBreakout;
  final String rsiTrend;
  final String category;

  DVPattern({
    required this.ticker,
    required this.price,
    this.dvScore = 0,
    this.dailyVol = 0,
    this.pctAboveSma20 = 0,
    this.near52whPct = 0,
    this.volTrend = 0,
    this.rsi = 50,
    this.drawdown = 0,
    this.currentBreakout = false,
    this.rsiTrend = 'neutral',
    this.category = 'bull',
  });

  factory DVPattern.fromJson(Map<String, dynamic> json) => DVPattern(
        ticker: json['ticker'] ?? json['symbol'] ?? '',
        price: (json['price'] ?? json['ltp'] ?? 0).toDouble(),
        dvScore: (json['dv_score'] ?? json['score'] ?? 0).toDouble(),
        dailyVol: (json['daily_vol'] ?? json['daily_volatility'] ?? 0).toDouble(),
        pctAboveSma20: (json['pct_above_sma20'] ?? 0).toDouble(),
        near52whPct: (json['near_52wh_pct'] ?? json['near_52w_high_pct'] ?? 0).toDouble(),
        volTrend: (json['vol_trend'] ?? json['volume_trend'] ?? 0).toDouble(),
        rsi: (json['rsi'] ?? 50).toDouble(),
        drawdown: (json['drawdown'] ?? 0).toDouble(),
        currentBreakout: json['current_breakout'] ?? false,
        rsiTrend: json['rsi_trend'] ?? 'neutral',
        category: json['category'] ?? 'bull',
      );
}
