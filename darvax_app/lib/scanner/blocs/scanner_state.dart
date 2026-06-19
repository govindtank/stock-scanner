part of 'scanner_cubit.dart';

sealed class ScannerState {
  const ScannerState();
}

class ScannerInitial extends ScannerState {
  const ScannerInitial();
}

class ScannerScanning extends ScannerState {
  final String currentTicker;
  final int progress;
  final int total;

  const ScannerScanning({
    required this.currentTicker,
    required this.progress,
    required this.total,
  });
}

class ScannerLoaded extends ScannerState {
  final List<ScanResult> results;
  final DateTime scannedAt;

  const ScannerLoaded({
    required this.results,
    required this.scannedAt,
  });
}

class ScannerError extends ScannerState {
  final String message;

  const ScannerError(this.message);
}
