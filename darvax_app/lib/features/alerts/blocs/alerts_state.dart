import 'package:equatable/equatable.dart';

enum AlertType { priceTarget, priceCross, patternDetected, portfolioAlert }

class DarvaAlert {
  final String id;
  final AlertType type;
  final String ticker;
  final String title;
  final String description;
  final double? targetPrice;
  final bool isTriggered;
  final DateTime createdAt;

  const DarvaAlert({
    required this.id,
    required this.type,
    required this.ticker,
    required this.title,
    required this.description,
    this.targetPrice,
    this.isTriggered = false,
    required this.createdAt,
  });

  DarvaAlert copyWith({bool? isTriggered}) {
    return DarvaAlert(
      id: id,
      type: type,
      ticker: ticker,
      title: title,
      description: description,
      targetPrice: targetPrice,
      isTriggered: isTriggered ?? this.isTriggered,
      createdAt: createdAt,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'type': type.name,
    'ticker': ticker,
    'title': title,
    'description': description,
    'targetPrice': targetPrice,
    'isTriggered': isTriggered,
    'createdAt': createdAt.toIso8601String(),
  };

  factory DarvaAlert.fromJson(Map<String, dynamic> json) => DarvaAlert(
    id: json['id'] as String,
    type: AlertType.values.firstWhere((t) => t.name == json['type']),
    ticker: json['ticker'] as String,
    title: json['title'] as String,
    description: json['description'] as String,
    targetPrice: (json['targetPrice'] as num?)?.toDouble(),
    isTriggered: json['isTriggered'] as bool? ?? false,
    createdAt: DateTime.parse(json['createdAt'] as String),
  );
}

// ─── States ───

sealed class AlertsState extends Equatable {
  const AlertsState();
  @override
  List<Object?> get props => [];
}

class AlertsInitial extends AlertsState {
  const AlertsInitial();
}

class AlertsLoaded extends AlertsState {
  final List<DarvaAlert> alerts;
  final List<DarvaAlert> triggeredAlerts;

  const AlertsLoaded({
    required this.alerts,
    required this.triggeredAlerts,
  });

  bool get hasUnread => triggeredAlerts.isNotEmpty;

  AlertsLoaded copyWith({
    List<DarvaAlert>? alerts,
    List<DarvaAlert>? triggeredAlerts,
  }) {
    return AlertsLoaded(
      alerts: alerts ?? this.alerts,
      triggeredAlerts: triggeredAlerts ?? this.triggeredAlerts,
    );
  }

  @override
  List<Object?> get props => [alerts, triggeredAlerts];
}

class AlertsError extends AlertsState {
  final String message;
  const AlertsError(this.message);
  @override
  List<Object?> get props => [message];
}
