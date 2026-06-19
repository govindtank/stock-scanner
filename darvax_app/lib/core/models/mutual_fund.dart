class MutualFund {
  final String name;
  final String amc;
  final String category;
  final double invested;
  final double currentValue;
  final double returns;
  final double expenseRatio;
  final double nav;
  final String riskLevel;

  MutualFund({
    required this.name,
    required this.amc,
    required this.category,
    required this.invested,
    required this.currentValue,
    required this.returns,
    this.expenseRatio = 0,
    this.nav = 0,
    this.riskLevel = 'moderate',
  });

  double get returnsPct => invested > 0 ? ((returns / invested) * 100) : 0;

  factory MutualFund.fromJson(Map<String, dynamic> json) => MutualFund(
        name: json['name'] ?? '',
        amc: json['amc'] ?? '',
        category: json['category'] ?? 'Unknown',
        invested: (json['invested'] ?? 0).toDouble(),
        currentValue: (json['current_value'] ?? 0).toDouble(),
        returns: (json['returns'] ?? 0).toDouble(),
        expenseRatio: (json['expense_ratio'] ?? 0).toDouble(),
        nav: (json['nav'] ?? 0).toDouble(),
        riskLevel: json['risk_level'] ?? 'moderate',
      );

  Map<String, dynamic> toJson() => {
        'name': name,
        'amc': amc,
        'category': category,
        'invested': invested,
        'current_value': currentValue,
        'returns': returns,
        'expense_ratio': expenseRatio,
        'nav': nav,
        'risk_level': riskLevel,
      };
}
