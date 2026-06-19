import 'real_holding.dart';
import 'mutual_fund.dart';
import 'bond_holding.dart';

class FullPortfolio {
  final double totalValue;
  final double stocksValue;
  final double mfValue;
  final double bondsValue;
  final double cashValue;
  final List<RealHolding> holdings;
  final List<MutualFund> mutualFunds;
  final List<BondHolding> bonds;
  final double overallReturns;
  final double overallReturnsPct;
  final double riskScore;
  final String riskLevel;

  FullPortfolio({
    this.totalValue = 0,
    this.stocksValue = 0,
    this.mfValue = 0,
    this.bondsValue = 0,
    this.cashValue = 0,
    this.holdings = const [],
    this.mutualFunds = const [],
    this.bonds = const [],
    this.overallReturns = 0,
    this.overallReturnsPct = 0,
    this.riskScore = 50,
    this.riskLevel = 'moderate',
  });

  double get stocksPct => totalValue > 0 ? (stocksValue / totalValue) * 100 : 0;
  double get mfPct => totalValue > 0 ? (mfValue / totalValue) * 100 : 0;
  double get bondsPct => totalValue > 0 ? (bondsValue / totalValue) * 100 : 0;
  double get cashPct => totalValue > 0 ? (cashValue / totalValue) * 100 : 0;

  factory FullPortfolio.empty() => FullPortfolio();

  factory FullPortfolio.fromJustHoldings(List<RealHolding> holdings) {
    final stocksValue = holdings.fold<double>(0, (s, h) => s + h.currentValue);
    final invested = holdings.fold<double>(0, (s, h) => s + h.investedValue);
    final returns = stocksValue - invested;
    return FullPortfolio(
      totalValue: stocksValue,
      stocksValue: stocksValue,
      holdings: holdings,
      overallReturns: returns,
      overallReturnsPct: invested > 0 ? (returns / invested) * 100 : 0,
    );
  }

  factory FullPortfolio.fromJson(Map<String, dynamic> json) => FullPortfolio(
        totalValue: (json['total_value'] ?? 0).toDouble(),
        stocksValue: (json['stocks_value'] ?? 0).toDouble(),
        mfValue: (json['mf_value'] ?? 0).toDouble(),
        bondsValue: (json['bonds_value'] ?? 0).toDouble(),
        cashValue: (json['cash_value'] ?? 0).toDouble(),
        holdings: (json['holdings'] as List? ?? [])
            .map((h) => RealHolding.fromJson(h))
            .toList(),
        mutualFunds: (json['mutual_funds'] as List? ?? [])
            .map((m) => MutualFund.fromJson(m))
            .toList(),
        bonds: (json['bonds'] as List? ?? [])
            .map((b) => BondHolding.fromJson(b))
            .toList(),
        overallReturns: (json['overall_returns'] ?? 0).toDouble(),
        overallReturnsPct: (json['overall_returns_pct'] ?? 0).toDouble(),
        riskScore: (json['risk_score'] ?? 50).toDouble(),
        riskLevel: json['risk_level'] ?? 'moderate',
      );
}
