import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/analytics/darvax_scanner.dart';

part 'scanner_state.dart';

class ScannerCubit extends Cubit<ScannerState> {
  final DarvaXScannerEngine _scanner;
  List<ScanResult> _lastResults = [];

  ScannerCubit({DarvaXScannerEngine? scanner})
      : _scanner = scanner ?? DarvaXScannerEngine(),
        super(const ScannerInitial());

  /// Run a full universe scan
  Future<void> scan() async {
    emit(const ScannerScanning(
      currentTicker: '',
      progress: 0,
      total: 0,
    ));

    try {
      int progressCount = 0;

      final results = await _scanner.scanUniverse(
        onProgress: (ticker, index, total) {
          progressCount++;
          emit(ScannerScanning(
            currentTicker: ticker,
            progress: progressCount,
            total: total,
          ));
        },
      );

      _lastResults = results;
      emit(ScannerLoaded(
        results: results,
        scannedAt: DateTime.now(),
      ));
    } catch (e) {
      emit(ScannerError('Scan failed: $e'));
    }
  }

  /// Scan a single custom ticker
  Future<void> scanSingle(String ticker) async {
    emit(const ScannerScanning(
      currentTicker: '',
      progress: 0,
      total: 1,
    ));

    try {
      final result = await _scanner.scanTicker(ticker);
      _lastResults = result.bestScore > 0 ? [result] : [];
      emit(ScannerLoaded(
        results: _lastResults,
        scannedAt: DateTime.now(),
      ));
    } catch (e) {
      emit(ScannerError('Scan failed for $ticker: $e'));
    }
  }

  List<ScanResult> get lastResults => _lastResults;
}
