import 'dart:convert';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:uuid/uuid.dart';
import '../../../core/network/yahoo_finance_service.dart';
import 'alerts_state.dart';

class AlertsCubit extends Cubit<AlertsState> {
  final YahooFinanceService _yahoo;
  static const _boxName = 'alerts_data';
  final _uuid = const Uuid();

  AlertsCubit({YahooFinanceService? yahoo})
      : _yahoo = yahoo ?? YahooFinanceService(),
        super(const AlertsInitial()) {
    _init();
  }

  Future<void> _init() async {
    try {
      final alerts = _loadAlerts();
      final triggered = _loadTriggered();
      emit(AlertsLoaded(alerts: alerts, triggeredAlerts: triggered));
    } catch (e) {
      emit(AlertsError('Failed to load alerts: $e'));
    }
  }

  List<DarvaAlert> _loadList(String key) {
    final box = Hive.box<String>(_boxName);
    final data = box.get(key);
    if (data == null || data.isEmpty) return [];
    try {
      final list = jsonDecode(data) as List;
      return list
          .map((e) => DarvaAlert.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> _saveList(String key, List<DarvaAlert> alerts) async {
    final box = Hive.box<String>(_boxName);
    await box.put(
      key,
      jsonEncode(alerts.map((a) => a.toJson()).toList()),
    );
  }

  List<DarvaAlert> _loadAlerts() => _loadList('alerts');
  List<DarvaAlert> _loadTriggered() => _loadList('triggered');

  /// Add a new price alert
  Future<void> addPriceAlert({
    required String ticker,
    required double targetPrice,
    required String title,
    String? description,
  }) async {
    final current = state;
    if (current is! AlertsLoaded) return;
    final alert = DarvaAlert(
      id: _uuid.v4(),
      type: AlertType.priceTarget,
      ticker: ticker,
      title: title,
      description: description ?? 'Alert when $ticker hits ₹${targetPrice.toStringAsFixed(0)}',
      targetPrice: targetPrice,
      createdAt: DateTime.now(),
    );
    final updated = [...current.alerts, alert];
    await _saveList('alerts', updated);
    emit(current.copyWith(alerts: updated));
  }

  /// Remove an alert
  Future<void> removeAlert(String id) async {
    final current = state;
    if (current is! AlertsLoaded) return;
    final updated = current.alerts.where((a) => a.id != id).toList();
    await _saveList('alerts', updated);
    emit(current.copyWith(alerts: updated));
  }

  /// Clear all triggered alerts
  Future<void> clearTriggered() async {
    final current = state;
    if (current is! AlertsLoaded) return;
    await _saveList('triggered', []);
    emit(current.copyWith(triggeredAlerts: []));
  }

  /// Check all active alerts against live prices
  Future<void> checkAlerts() async {
    final current = state;
    if (current is! AlertsLoaded) return;
    if (current.alerts.isEmpty) return;

    final triggered = <DarvaAlert>[];
    final remaining = <DarvaAlert>[];

    for (final alert in current.alerts) {
      try {
        final quote = await _yahoo.fetchQuote(alert.ticker);
        if (quote.currentPrice >= (alert.targetPrice ?? double.infinity)) {
          triggered.add(alert.copyWith(isTriggered: true));
        } else {
          remaining.add(alert);
        }
      } catch (e) {
        remaining.add(alert);
      }
    }

    if (triggered.isNotEmpty) {
      final allTriggered = [...current.triggeredAlerts, ...triggered];
      await _saveList('alerts', remaining);
      await _saveList('triggered', allTriggered);
      emit(current.copyWith(
        alerts: remaining,
        triggeredAlerts: allTriggered,
      ));
    }
  }
}
