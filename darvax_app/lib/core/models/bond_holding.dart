class BondHolding {
  final String name;
  final String issuer;
  final String rating;
  final double faceValue;
  final double couponRate;
  final double currentPrice;
  final DateTime maturityDate;
  final double ytm;
  final double quantity;

  BondHolding({
    required this.name,
    required this.issuer,
    this.rating = 'AAA',
    required this.faceValue,
    required this.couponRate,
    required this.currentPrice,
    required this.maturityDate,
    this.ytm = 0,
    this.quantity = 1,
  });

  double get investedValue => currentPrice * quantity;
  double get annualIncome => faceValue * couponRate / 100 * quantity;

  factory BondHolding.fromJson(Map<String, dynamic> json) => BondHolding(
        name: json['name'] ?? '',
        issuer: json['issuer'] ?? '',
        rating: json['rating'] ?? 'AAA',
        faceValue: (json['face_value'] ?? 0).toDouble(),
        couponRate: (json['coupon_rate'] ?? 0).toDouble(),
        currentPrice: (json['current_price'] ?? 0).toDouble(),
        maturityDate: json['maturity_date'] != null
            ? DateTime.parse(json['maturity_date'])
            : DateTime.now(),
        ytm: (json['ytm'] ?? 0).toDouble(),
        quantity: (json['quantity'] ?? 1).toDouble(),
      );

  Map<String, dynamic> toJson() => {
        'name': name,
        'issuer': issuer,
        'rating': rating,
        'face_value': faceValue,
        'coupon_rate': couponRate,
        'current_price': currentPrice,
        'maturity_date': maturityDate.toIso8601String(),
        'ytm': ytm,
        'quantity': quantity,
      };
}
