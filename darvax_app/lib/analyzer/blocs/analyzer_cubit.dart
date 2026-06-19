import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/analytics/darvax_scanner.dart';

// ─── States ────────────────────────────────────────────────────────────

sealed class AnalyzerState {
  const AnalyzerState();
}

class AnalyzerInitial extends AnalyzerState {
  const AnalyzerInitial();
}

class AnalyzerLoading extends AnalyzerState {
  final String ticker;
  const AnalyzerLoading(this.ticker);
}

class AnalyzerResult extends AnalyzerState {
  final String ticker;
  final ScanResult scanResult;
  const AnalyzerResult({
    required this.ticker,
    required this.scanResult,
  });

  bool get isEntrySignal => scanResult.bestScore >= 55;
}

class AnalyzerError extends AnalyzerState {
  final String ticker;
  final String message;
  const AnalyzerError(this.ticker, this.message);
}

// ─── Cubit ─────────────────────────────────────────────────────────────

class AnalyzerCubit extends Cubit<AnalyzerState> {
  final DarvaXScannerEngine _scanner;

  AnalyzerCubit({DarvaXScannerEngine? scanner})
      : _scanner = scanner ?? DarvaXScannerEngine(),
        super(const AnalyzerInitial());

  /// Reset to initial state
  void reset() => emit(const AnalyzerInitial());

  /// Analyze a single ticker and return Entry/Exit verdict
  Future<void> analyze(String ticker) async {
    final cleanTicker = ticker.endsWith('.NS') ? ticker : '$ticker.NS';
    emit(AnalyzerLoading(cleanTicker));

    try {
      final result = await _scanner.scanTicker(cleanTicker);

      if (result.bestScore == 0) {
        emit(AnalyzerError(cleanTicker, 'No data available for $ticker'));
        return;
      }

      emit(AnalyzerResult(
        ticker: cleanTicker,
        scanResult: result,
      ));
    } catch (e) {
      emit(AnalyzerError(cleanTicker, 'Analysis failed: $e'));
    }
  }
}
