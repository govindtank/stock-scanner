import 'dart:math';
import '../network/yahoo_finance_service.dart';
import '../models/nifty200.dart';

// ══════════════════════════════════════════════════════════════════════════
//  DARVAX PATTERN SCANNER — Pure Dart Port
//  ══════════════════════════════════════════════════════════════════════════
//  All 9 DarvaX patterns from the PDF, ported from the Python scanner.
//  No numpy/pandas — pure Dart with list operations.
// ══════════════════════════════════════════════════════════════════════════

// ─── Pattern Metadata ──────────────────────────────────────────────────

class DarvaXPattern {
  final String id;
  final String name;
  final String emoji;
  final String description;

  const DarvaXPattern({
    required this.id,
    required this.name,
    required this.emoji,
    required this.description,
  });
}

const Map<String, DarvaXPattern> PATTERN_META = {
  'HIGH_DRY_FRY': DarvaXPattern(
    id: 'HIGH_DRY_FRY',
    name: 'High Dry Fry',
    emoji: '🍟',
    description:
        'Stock surges 20-50% on huge volume → corrects 10-20% → baby candle base → blast 65%+',
  ),
  'BULLISH_TASUKI': DarvaXPattern(
    id: 'BULLISH_TASUKI',
    name: 'Bullish Tasuki Line',
    emoji: '🌅',
    description:
        'Long bearish candle → gap-up bullish closing above bear\'s high',
  ),
  'INSIDE_BAR_BREAK': DarvaXPattern(
    id: 'INSIDE_BAR_BREAK',
    name: 'Inside Bar Breakout',
    emoji: '📦',
    description:
        'Inside bar consolidation → volume breakout above mother bar',
  ),
  'MORNING_STAR': DarvaXPattern(
    id: 'MORNING_STAR',
    name: 'Morning Star',
    emoji: '⭐',
    description:
        '3-candle reversal: long bear → doji → long bull closing above midpoint',
  ),
  'DOUBLE_BOTTOM': DarvaXPattern(
    id: 'DOUBLE_BOTTOM',
    name: 'Double Bottom',
    emoji: '🔵',
    description:
        'W-bottom with two swing lows at same level — breakout above neckline',
  ),
  'BABY_CRADLE': DarvaXPattern(
    id: 'BABY_CRADLE',
    name: 'Baby Cradle',
    emoji: '👶',
    description:
        'Multiple tiny candlesticks clustering in tight range — coiled spring',
  ),
  'DARVAX_JALWA': DarvaXPattern(
    id: 'DARVAX_JALWA',
    name: 'DarvaX Jalwa',
    emoji: '🔥',
    description:
        'Tight Darvas box with multiple touches → explosive juice breakout',
  ),
  'LAL_DABANGG': DarvaXPattern(
    id: 'LAL_DABANGG',
    name: 'Lal Dabangg',
    emoji: '🌶️',
    description:
        'Tall green candle (3x+ avg body) with huge volume — institutional buying',
  ),
  'ZIGZAG_FIB': DarvaXPattern(
    id: 'ZIGZAG_FIB',
    name: 'ZigZag Fibonacci',
    emoji: '📐',
    description:
        'Swing low + 61.8% fib retracement + buy above 10 EMA',
  ),
};

// ─── Detection Result ──────────────────────────────────────────────────

class PatternDetection {
  final bool matched;
  final int score;
  final List<String> evidence;
  final Map<String, dynamic> details;

  const PatternDetection({
    this.matched = false,
    this.score = 0,
    this.evidence = const [],
    this.details = const {},
  });

  factory PatternDetection.empty() => const PatternDetection();
}

class ScanResult {
  final String ticker;
  final String? bestPattern;
  final int bestScore;
  final double price;
  final Map<String, PatternDetection> results;
  final DarvaXPattern? patternMeta;

  ScanResult({
    required this.ticker,
    this.bestPattern,
    this.bestScore = 0,
    this.price = 0,
    this.results = const {},
    this.patternMeta,
  });

  List<String> get evidence {
    if (bestPattern == null) return [];
    return results[bestPattern]?.evidence ?? [];
  }
}

// ─── Math Helpers ──────────────────────────────────────────────────────

double _mean(List<double> values) {
  if (values.isEmpty) return 0;
  return values.reduce((a, b) => a + b) / values.length;
}

double _min(List<double> values) => values.reduce(min);
double _max(List<double> values) => values.reduce(max);

int _argmin(List<double> values) {
  double minVal = values[0];
  int minIdx = 0;
  for (int i = 1; i < values.length; i++) {
    if (values[i] < minVal) {
      minVal = values[i];
      minIdx = i;
    }
  }
  return minIdx;
}

List<double> _ema(List<double> values, int period) {
  if (values.isEmpty) return [];
  final result = List<double>.filled(values.length, 0);
  final k = 2.0 / (period + 1);
  result[0] = values[0];
  for (int i = 1; i < values.length; i++) {
    result[i] = values[i] * k + result[i - 1] * (1 - k);
  }
  return result;
}

// ─── Indicator Helpers ─────────────────────────────────────────────────

class _Indicators {
  final List<double> close;
  final List<double> open;
  final List<double> high;
  final List<double> low;
  final List<double> volume;
  final int n;

  _Indicators(List<StockCandle> candles)
      : close = candles.map((c) => c.close).toList(),
        open = candles.map((c) => c.open).toList(),
        high = candles.map((c) => c.high).toList(),
        low = candles.map((c) => c.low).toList(),
        volume = candles.map((c) => c.volume).toList(),
        n = candles.length;

  double avgBody([int? lookback]) {
    final len = lookback ?? n;
    final start = max(0, n - len);
    final bodies =
        List.generate(n - start, (i) => (close[start + i] - open[start + i]).abs());
    if (bodies.isEmpty) return 0;
    return _mean(bodies);
  }

  double avgRange([int? lookback]) {
    final len = lookback ?? n;
    final start = max(0, n - len);
    final ranges =
        List.generate(n - start, (i) => high[start + i] - low[start + i]);
    if (ranges.isEmpty) return 0;
    return _mean(ranges);
  }

  double avgVol([int? lookback]) {
    final len = lookback ?? n;
    final start = max(0, n - len);
    final vols = volume.sublist(start, n);
    if (vols.isEmpty) return 0;
    return _mean(vols);
  }
}

// ══════════════════════════════════════════════════════════════════════════
//  PATTERN DETECTORS
// ══════════════════════════════════════════════════════════════════════════

// ─── 1. HIGH DRY FRY ──────────────────────────────────────────────────

PatternDetection detectHighDryFry(_Indicators ind) {
  if (ind.n < 45) return PatternDetection.empty();

  // 1. Find surge phase (20-50% move with high volume)
  final lookback = min(ind.n, 125);
  final avgVol20 = ind.avgVol(lookback);
  final surgeCandidates = <Map<String, dynamic>>[];

  for (int i = max(3, ind.n - lookback); i < ind.n; i++) {
    final lookFwd = min(15, ind.n - i);
    if (lookFwd < 3) break;

    final priceChange =
        (ind.close[i + lookFwd - 1] / ind.close[i] - 1) * 100;
    final volSlice = ind.volume.sublist(i, i + lookFwd);
    final volRatio = _mean(volSlice) / max(avgVol20, 1);

    if (priceChange >= 15 && priceChange <= 60 && volRatio >= 1.3) {
      surgeCandidates.add({
        'start_idx': i,
        'end_idx': i + lookFwd - 1,
        'surge_pct': priceChange,
        'vol_ratio': volRatio,
        'peak_price': _max(ind.close.sublist(i, i + lookFwd)),
      });
    }
  }

  if (surgeCandidates.isEmpty) return PatternDetection.empty();

  surgeCandidates.sort((a, b) =>
      (b['surge_pct'] * b['vol_ratio']).compareTo(a['surge_pct'] * a['vol_ratio']));
  final bestSurge = surgeCandidates.first;
  final surgeEnd = bestSurge['end_idx'] as int;
  final peakPrice = bestSurge['peak_price'] as double;

  if (surgeEnd >= ind.n - 5) return PatternDetection.empty();

  // 2. Correction phase
  final postSurge = ind.close.sublist(surgeEnd);
  final minPostIdx = _argmin(postSurge) + surgeEnd;

  if (minPostIdx >= ind.n) return PatternDetection.empty();

  final correctionPct = (peakPrice - ind.close[minPostIdx]) / peakPrice * 100;
  if (correctionPct < 8 || correctionPct > 35) return PatternDetection.empty();

  final correctionEnd = minPostIdx;
  if (correctionEnd >= ind.n - 3) return PatternDetection.empty();

  // 3. Baby candle base
  final baseCandles = ind.close.sublist(correctionEnd);
  if (baseCandles.length < 5) return PatternDetection.empty();

  final baseVolAvg =
      _mean(ind.volume.sublist(correctionEnd)) / max(avgVol20, 1);
  final baseDays = baseCandles.length;

  final avgBodyBase = ind.avgBody(ind.n - correctionEnd);
  final avgBodyOverall = ind.avgBody(ind.n);
  final bodyRatio = avgBodyBase / max(avgBodyOverall, 0.01);
  final baseCompression = bodyRatio < 0.8;

  // 4. Check breakout
  bool recentBreakout = false;
  double recentMove = 0, recentVol = 0;
  if (ind.close.sublist(correctionEnd).length >= 3) {
    recentMove = (ind.close.last / ind.close[correctionEnd] - 1) * 100;
    recentVol = ind.volume.last / max(avgVol20, 1);
    if (recentMove > 5 && recentVol > 1.3) recentBreakout = true;
  }

  // Score
  int score = 0;
  final evidence = <String>[];

  if (bestSurge['surge_pct'] >= 20) {
    score += 25;
    evidence.add(
        '✅ Surge phase: +${(bestSurge['surge_pct'] as double).toStringAsFixed(1)}% on ${(bestSurge['vol_ratio'] as double).toStringAsFixed(1)}x volume');
  } else {
    score += 15;
    evidence.add(
        '🟡 Surge phase: +${(bestSurge['surge_pct'] as double).toStringAsFixed(1)}% (moderate)');
  }

  if (correctionPct >= 10 && correctionPct <= 25) {
    score += 25;
    evidence.add(
        '✅ Correction: -${correctionPct.toStringAsFixed(1)}% from peak (ideal pullback)');
  } else if (correctionPct > 25) {
    score += 10;
    evidence.add(
        '🟡 Correction: -${correctionPct.toStringAsFixed(1)}% (deep pullback)');
  } else {
    score += 15;
    evidence.add(
        '🟡 Correction: -${correctionPct.toStringAsFixed(1)}% (shallow pullback)');
  }

  if (baseDays >= 8) {
    score += 20;
    evidence.add('✅ Base formation: $baseDays days — well-developed base');
  } else if (baseDays >= 5) {
    score += 10;
    evidence.add('🟡 Base formation: $baseDays days — early base');
  }

  if (baseVolAvg < 0.8 && baseDays >= 5) {
    score += 15;
    evidence.add(
        '✅ Volume drying: ${baseVolAvg.toStringAsFixed(1)}x — selling exhaustion');
  }

  if (baseCompression) {
    score += 10;
    evidence.add(
        '✅ Baby candle compression (ratio ${bodyRatio.toStringAsFixed(2)})');
  }

  if (recentBreakout) {
    score += 15;
    evidence.add(
        '🚀 Breaking out! +${recentMove.toStringAsFixed(1)}% on ${recentVol.toStringAsFixed(1)}x volume');
  }

  if (score >= 50) {
    return PatternDetection(
      matched: true,
      score: score,
      evidence: evidence,
      details: {
        'surge_pct': bestSurge['surge_pct'],
        'correction_pct': correctionPct,
        'base_days': baseDays,
      },
    );
  }
  return PatternDetection.empty();
}

// ─── 2. BULLISH TASUKI ────────────────────────────────────────────────

PatternDetection detectBullishTasuki(_Indicators ind) {
  if (ind.n < 3) return PatternDetection.empty();

  final i = ind.n - 1; // bullish candle
  final j = i - 1; // bearish candle
  final k = i - 2;

  if (k < 0) return PatternDetection.empty();

  // Candle j must be bearish
  if (!(ind.close[j] < ind.open[j])) return PatternDetection.empty();

  final avgBody = ind.avgBody();
  final bearBody = (ind.close[j] - ind.open[j]).abs();
  if (bearBody < avgBody * 1.2) return PatternDetection.empty();

  // Candle i must be bullish
  if (!(ind.close[i] > ind.open[i])) return PatternDetection.empty();

  // Gap up
  if (ind.open[i] <= ind.close[j]) return PatternDetection.empty();

  // Close above bear's high
  if (ind.close[i] <= ind.high[j]) {
    if (ind.close[i] < ind.high[j] * 0.98) return PatternDetection.empty();
  }

  int score = 0;
  final evidence = <String>[];
  final gapPct = (ind.open[i] / ind.close[j] - 1) * 100;

  if (gapPct >= 2) {
    score += 30;
    evidence.add('✅ Strong gap up: +${gapPct.toStringAsFixed(1)}%');
  } else {
    score += 15;
    evidence.add('🟡 Gap up: +${gapPct.toStringAsFixed(1)}%');
  }

  final bullBody = (ind.close[i] - ind.open[i]).abs();
  if (bullBody >= avgBody * 1.5) {
    score += 20;
    evidence.add(
        '✅ Large bullish body: ${bullBody.toStringAsFixed(1)} vs avg ${avgBody.toStringAsFixed(1)}');
  }

  final avgVol = ind.avgVol(20);
  final volRatio = ind.volume[i] / max(avgVol, 1);
  if (volRatio >= 2.0) {
    score += 25;
    evidence.add('✅ Massive volume: ${volRatio.toStringAsFixed(1)}x');
  } else if (volRatio >= 1.5) {
    score += 15;
    evidence.add('🟡 Good volume: ${volRatio.toStringAsFixed(1)}x');
  }

  if (ind.close[i] > ind.high[j]) {
    score += 25;
    evidence.add(
        '✅ Closed above bear high (${ind.high[j].toStringAsFixed(1)})');
  }

  if (score >= 50) {
    return PatternDetection(matched: true, score: score, evidence: evidence);
  }
  return PatternDetection.empty();
}

// ─── 3. INSIDE BAR BREAKOUT ──────────────────────────────────────────

PatternDetection detectInsideBarBreakout(_Indicators ind) {
  if (ind.n < 5) return PatternDetection.empty();

  final avgVol = ind.avgVol(20);

  for (int lb = 1; lb < min(11, ind.n - 1); lb++) {
    final ibIdx = ind.n - 1 - lb;
    final motherIdx = ibIdx - 1;
    if (motherIdx < 0) break;

    // Inside bar check
    if (!(ind.high[ibIdx] <= ind.high[motherIdx] &&
        ind.low[ibIdx] >= ind.low[motherIdx])) continue;

    if (ibIdx + 1 >= ind.n) continue;

    final breakoutIdx = ibIdx + 1;
    final breakoutHigh = ind.close[breakoutIdx] > ind.open[breakoutIdx]
        ? ind.close[breakoutIdx]
        : ind.high[breakoutIdx];

    if (!(breakoutHigh > ind.high[motherIdx])) continue;

    int score = 0;
    final evidence = <String>[];

    final volRatio = ind.volume[breakoutIdx] / max(avgVol, 1);
    if (volRatio >= 2.0) {
      score += 30;
      evidence.add('✅ Breakout on ${volRatio.toStringAsFixed(1)}x volume');
    } else if (volRatio >= 1.5) {
      score += 20;
      evidence.add('🟡 Breakout on ${volRatio.toStringAsFixed(1)}x volume');
    } else {
      score += 10;
    }

    final brPct = (ind.close[breakoutIdx] / ind.high[motherIdx] - 1) * 100;
    if (brPct > 3) {
      score += 25;
      evidence.add('✅ Strong breakout: +${brPct.toStringAsFixed(1)}%');
    } else if (brPct > 1) {
      score += 15;
      evidence.add('🟡 Breakout: +${brPct.toStringAsFixed(1)}%');
    }

    final ibRange = ind.high[ibIdx] - ind.low[ibIdx];
    final motherRange = ind.high[motherIdx] - ind.low[motherIdx];
    if (motherRange > 0) {
      final tightness = ibRange / motherRange;
      if (tightness < 0.3) {
        score += 20;
        evidence.add('✅ Very tight inside bar — coiled');
      } else if (tightness < 0.5) {
        score += 10;
        evidence.add('🟡 Moderate inside bar');
      }
    }

    if (ind.n - breakoutIdx <= 3) {
      score += 15;
      evidence.add('🆕 Fresh breakout signal');
    }

    if (score >= 50) {
      return PatternDetection(matched: true, score: score, evidence: evidence);
    }
    return PatternDetection.empty();
  }
  return PatternDetection.empty();
}

// ─── 4. MORNING STAR ─────────────────────────────────────────────────

PatternDetection detectMorningStar(_Indicators ind) {
  if (ind.n < 4) return PatternDetection.empty();

  final i = ind.n - 1; // bullish
  final j = i - 1; // indecision
  final k = i - 2; // bearish
  if (k < 0) return PatternDetection.empty();

  // Day 1: bearish
  if (!(ind.close[k] < ind.open[k])) return PatternDetection.empty();
  final avgBody = ind.avgBody();
  final bearBody = (ind.close[k] - ind.open[k]).abs();
  if (bearBody < avgBody * 1.3) return PatternDetection.empty();

  // Day 2: small body
  final body2 = (ind.close[j] - ind.open[j]).abs();
  if (body2 > avgBody * 0.8) return PatternDetection.empty();

  // Day 3: bullish
  if (!(ind.close[i] > ind.open[i])) return PatternDetection.empty();
  final bullBody = (ind.close[i] - ind.open[i]).abs();
  if (bullBody < avgBody * 1.2) return PatternDetection.empty();

  // Close above bear midpoint
  final bearMid = (ind.high[k] + ind.low[k]) / 2;
  if (ind.close[i] <= bearMid) return PatternDetection.empty();

  int score = 0;
  final evidence = <String>[];

  if (bearBody >= avgBody * 2) {
    score += 15;
    evidence.add('✅ Strong bearish candle — capitulation');
  }

  final dojiThreshold = (ind.close[j] - ind.open[j]).abs() /
      max(ind.high[j] - ind.low[j], 0.001);
  if (dojiThreshold < 0.1) {
    score += 20;
    evidence.add('✅ Doji indecision — perfect reversal pause');
  } else {
    score += 10;
    evidence.add('🟡 Small candle indecision');
  }

  if (bullBody >= avgBody * 2) {
    score += 25;
    evidence.add('✅ Strong bullish candle — conviction');
  } else if (bullBody >= avgBody * 1.5) {
    score += 15;
  }

  final pctAbove = (ind.close[i] / bearMid - 1) * 100;
  if (ind.close[i] > ind.high[k]) {
    score += 25;
    evidence.add(
        '✅ Closed above bearish high (${ind.high[k].toStringAsFixed(1)})');
  } else {
    score += 15;
    evidence.add('🟡 Closed ${pctAbove.toStringAsFixed(1)}% above bear midpoint');
  }

  final avgVol = ind.avgVol(20);
  final volRatio = ind.volume[i] / max(avgVol, 1);
  if (volRatio >= 1.5) {
    score += 15;
    evidence.add('✅ Volume confirmation: ${volRatio.toStringAsFixed(1)}x');
  }

  if (score >= 50) {
    return PatternDetection(matched: true, score: score, evidence: evidence);
  }
  return PatternDetection.empty();
}

// ─── 5. DOUBLE BOTTOM ─────────────────────────────────────────────────

PatternDetection detectDoubleBottom(_Indicators ind) {
  if (ind.n < 30) return PatternDetection.empty();

  final lookback = min(ind.n, 60);
  final searchStart = max(0, ind.n - lookback);

  // Find swing lows
  final swingLows = <MapEntry<int, double>>[];
  for (int i = searchStart + 3; i < ind.n - 3; i++) {
    if (ind.low[i] < ind.low[i - 1] &&
        ind.low[i] < ind.low[i - 2] &&
        ind.low[i] < ind.low[i - 3] &&
        ind.low[i] < ind.low[i + 1] &&
        ind.low[i] < ind.low[i + 2] &&
        ind.low[i] < ind.low[i + 3]) {
      swingLows.add(MapEntry(i, ind.low[i]));
    }
  }

  if (swingLows.length < 2) return PatternDetection.empty();

  for (int p1 = 0; p1 < swingLows.length - 1; p1++) {
    for (int p2 = p1 + 1; p2 < swingLows.length; p2++) {
      final idx1 = swingLows[p1].key, val1 = swingLows[p1].value;
      final idx2 = swingLows[p2].key, val2 = swingLows[p2].value;

      if ((idx2 - idx1).abs() < 10) continue;
      if ((val2 - val1) / min(val1, val2) > 0.05) continue;

      final peaksBetween = ind.high.sublist(idx1, idx2 + 1);
      final neckline = _max(peaksBetween);

      if (ind.close.last <= neckline * 0.99) continue;

      final patternDepth = neckline - min(val1, val2);
      final targetPrice = neckline + patternDepth;

      int score = 0;
      final evidence = <String>[];
      final lowDiffPct = (val2 - val1).abs() / val1 * 100;

      if (lowDiffPct < 2) {
        score += 25;
        evidence.add('✅ Near-perfect low alignment (diff ${lowDiffPct.toStringAsFixed(1)}%)');
      } else {
        score += 15;
        evidence.add('🟡 Good low alignment (diff ${lowDiffPct.toStringAsFixed(1)}%)');
      }

      final brPct = (ind.close.last / neckline - 1) * 100;
      if (brPct > 2) {
        score += 25;
        evidence.add('✅ Strong neckline breakout: +${brPct.toStringAsFixed(1)}%');
      } else if (brPct > 1) {
        score += 15;
        evidence.add('🟡 Breakout above neckline: +${brPct.toStringAsFixed(1)}%');
      }

      final avgVol = ind.avgVol(20);
      final volRatio = ind.volume.last / max(avgVol, 1);
      if (volRatio >= 1.5) {
        score += 20;
        evidence.add('✅ Volume on breakout: ${volRatio.toStringAsFixed(1)}x');
      }

      score += 15;
      evidence.add(
          '🎯 Target ₹${targetPrice.toStringAsFixed(0)} (+${((targetPrice / neckline - 1) * 100).toStringAsFixed(0)}%)');

      if (score >= 50) {
        return PatternDetection(
          matched: true,
          score: score,
          evidence: evidence,
          details: {'neckline': neckline, 'target': targetPrice},
        );
      }
    }
  }
  return PatternDetection.empty();
}

// ─── 6. BABY CRADLE ──────────────────────────────────────────────────

PatternDetection detectBabyCradle(_Indicators ind) {
  if (ind.n < 15) return PatternDetection.empty();

  final avgBody = ind.avgBody();
  final avgVol = ind.avgVol(20);
  final lookback = min(15, ind.n - 1);

  final recentHigh = _max(ind.high.sublist(ind.n - lookback, ind.n));
  final recentLow = _min(ind.low.sublist(ind.n - lookback, ind.n));
  final rangePct = (recentHigh - recentLow) / recentLow * 100;

  if (rangePct > 10) return PatternDetection.empty();

  final recentBodies = <double>[];
  for (int i = 1; i <= lookback; i++) {
    recentBodies.add((ind.close[ind.n - i] - ind.open[ind.n - i]).abs());
  }
  final avgRecentBody = _mean(recentBodies);
  if (avgRecentBody > avgBody * 0.8) return PatternDetection.empty();

  final recentVolRatio =
      _mean(ind.volume.sublist(ind.n - lookback, ind.n)) / max(avgVol, 1);

  int score = 0;
  final evidence = <String>[];

  if (rangePct < 5) {
    score += 30;
    evidence.add('✅ Very tight range: ${rangePct.toStringAsFixed(1)}% over $lookback days');
  } else {
    score += 20;
    evidence.add('🟡 Moderate range: ${rangePct.toStringAsFixed(1)}%');
  }

  final bodyRatio = avgRecentBody / max(avgBody, 0.01);
  if (bodyRatio < 0.4) {
    score += 25;
    evidence.add('✅ Tiny baby candles (ratio ${bodyRatio.toStringAsFixed(2)})');
  } else if (bodyRatio < 0.6) {
    score += 15;
    evidence.add('🟡 Small candles (ratio ${bodyRatio.toStringAsFixed(2)})');
  }

  if (recentVolRatio < 0.7) {
    score += 20;
    evidence.add('✅ Volume drying (${recentVolRatio.toStringAsFixed(1)}x) — accumulation');
  } else if (recentVolRatio < 1.0) {
    score += 10;
    evidence.add('🟡 Normal volume (${recentVolRatio.toStringAsFixed(1)}x)');
  }

  if (ind.n >= 3) {
    final recentMove = (ind.close.last / ind.close[ind.n - 3] - 1) * 100;
    if (recentMove > 3) {
      score += 15;
      evidence.add('🚀 Breaking out of cradle! +${recentMove.toStringAsFixed(1)}% in 3 days');
    } else if (recentMove > 0) {
      score += 10;
      evidence.add('🟡 Edge of cradle (+${recentMove.toStringAsFixed(1)}%)');
    }
  }

  if (lookback >= 12) {
    score += 10;
    evidence.add('✅ Extended cradle ($lookback days)');
  }

  if (score >= 50) {
    return PatternDetection(matched: true, score: score, evidence: evidence);
  }
  return PatternDetection.empty();
}

// ─── 7. DARVAX JALWA ─────────────────────────────────────────────────

PatternDetection detectDarvaXJalwa(_Indicators ind) {
  if (ind.n < 30) return PatternDetection.empty();

  final lookback = min(ind.n, 60);
  final avgVol = ind.avgVol(30);
  const boxSize = 10;

  Map<String, dynamic>? bestBox;
  int bestTouches = 0;

  for (int boxStart = max(0, ind.n - lookback);
      boxStart <= ind.n - boxSize - 5;
      boxStart++) {
    final boxHigh = _max(ind.high.sublist(boxStart, boxStart + boxSize));
    final boxLow = _min(ind.low.sublist(boxStart, boxStart + boxSize));
    final boxRangePct = (boxHigh - boxLow) / boxLow * 100;

    if (boxRangePct > 12 || boxRangePct < 2) continue;

    int touches = 0;
    for (int t = boxStart; t < boxStart + boxSize; t++) {
      if (ind.high[t] >= boxHigh * 0.97) touches++;
    }

    if (touches > bestTouches) {
      bestTouches = touches;
      bestBox = {
        'start': boxStart,
        'end': boxStart + boxSize - 1,
        'high': boxHigh,
        'low': boxLow,
        'range_pct': boxRangePct,
        'touches': touches,
      };
    }
  }

  if (bestBox == null || bestTouches < 2) return PatternDetection.empty();

  final box = bestBox;
  final breakoutStart = (box['end'] as int) + 1;
  if (breakoutStart >= ind.n) return PatternDetection.empty();

  final postBox = ind.close.sublist(breakoutStart);
  if (postBox.length < 2) return PatternDetection.empty();

  final aboveBox = postBox.where((x) => x > (box['high'] as double)).toList();
  if (aboveBox.isEmpty) return PatternDetection.empty();

  int score = 0;
  final evidence = <String>[];

  if ((box['range_pct'] as double) < 6) {
    score += 20;
    evidence.add('✅ Tight Darvas box: ${(box['range_pct'] as double).toStringAsFixed(1)}% range');
  }

  if (bestTouches >= 4) {
    score += 25;
    evidence.add('✅ $bestTouches touches on box top');
  } else if (bestTouches >= 2) {
    score += 15;
    evidence.add('🟡 $bestTouches touches on box top');
  }

  final breakHigh = _max(postBox);
  final brPct = (breakHigh / (box['high'] as double) - 1) * 100;
  if (brPct > 5) {
    score += 20;
    evidence.add('✅ Strong breakout: +${brPct.toStringAsFixed(1)}% above box');
  } else if (brPct > 2) {
    score += 10;
  }

  final breakoutVolIdx = breakoutStart + postBox.indexOf(breakHigh);
  if (breakoutVolIdx < ind.volume.length) {
    final volRatio = ind.volume[breakoutVolIdx] / max(avgVol, 1);
    if (volRatio >= 2) {
      score += 20;
      evidence.add('✅ Explosive volume: ${volRatio.toStringAsFixed(1)}x');
    } else if (volRatio >= 1.5) {
      score += 10;
      evidence.add('🟡 Volume: ${volRatio.toStringAsFixed(1)}x');
    }
  }

  final recentAbove = postBox.sublist(max(0, postBox.length - 5))
      .where((x) => x > (box['high'] as double))
      .length;
  if (recentAbove >= 3) {
    score += 15;
    evidence.add('✅ Holding above box: $recentAbove/5 days');
  }

  if (score >= 50) {
    return PatternDetection(
      matched: true,
      score: score,
      evidence: evidence,
      details: {
        'box_high': box['high'],
        'box_low': box['low'],
        'breakout_pct': brPct,
      },
    );
  }
  return PatternDetection.empty();
}

// ─── 8. LAL DABANGG ───────────────────────────────────────────────────

PatternDetection detectLalDabangg(_Indicators ind) {
  if (ind.n < 5) return PatternDetection.empty();

  final avgBody = ind.avgBody();
  final avgVol = ind.avgVol(20);
  final i = ind.n - 1;

  // Must be bullish
  if (!(ind.close[i] > ind.open[i])) return PatternDetection.empty();

  final body = (ind.close[i] - ind.open[i]).abs();
  if (body < avgBody * 2.0) return PatternDetection.empty();

  int score = 0;
  final evidence = <String>[];
  final bodyRatio = body / max(avgBody, 0.01);

  if (bodyRatio >= 3.0) {
    score += 30;
    evidence.add('✅ Massive candle: ${bodyRatio.toStringAsFixed(1)}x avg body');
  } else if (bodyRatio >= 2.5) {
    score += 20;
    evidence.add('🟡 Big candle: ${bodyRatio.toStringAsFixed(1)}x avg body');
  } else {
    score += 15;
  }

  final volRatio = ind.volume[i] / max(avgVol, 1);
  if (volRatio >= 3.0) {
    score += 30;
    evidence.add('✅ Huge volume: ${volRatio.toStringAsFixed(1)}x');
  } else if (volRatio >= 2.0) {
    score += 20;
    evidence.add('🟡 Strong volume: ${volRatio.toStringAsFixed(1)}x');
  } else if (volRatio >= 1.5) {
    score += 10;
  }

  final gainPct = (ind.close[i] / ind.open[i] - 1) * 100;
  if (gainPct > 5) {
    score += 25;
    evidence.add('✅ Big gain: +${gainPct.toStringAsFixed(1)}%');
  } else if (gainPct > 3) {
    score += 15;
    evidence.add('🟡 Good gain: +${gainPct.toStringAsFixed(1)}%');
  }

  if (i > 5) {
    final prevHigh = _max(ind.high.sublist(0, i));
    if (prevHigh > 0 && ind.close[i] > prevHigh * 0.98) {
      score += 15;
      evidence.add('✅ Breaking out from range high');
    }
  }

  if (score >= 50) {
    return PatternDetection(matched: true, score: score, evidence: evidence);
  }
  return PatternDetection.empty();
}

// ─── 9. ZIGZAG FIB ────────────────────────────────────────────────────

PatternDetection detectZigzagFib(_Indicators ind) {
  if (ind.n < 40) return PatternDetection.empty();

  final ema10 = _ema(ind.close, 10);

  // Find swing lows/highs
  final swingLows = <MapEntry<int, double>>[];
  final swingHighs = <MapEntry<int, double>>[];

  for (int i = 3; i < ind.n - 3; i++) {
    if (ind.low[i] < _min(ind.low.sublist(i - 3, i)) &&
        ind.low[i] <= _min(ind.low.sublist(i + 1, min(i + 4, ind.n)))) {
      swingLows.add(MapEntry(i, ind.low[i]));
    }
    if (ind.high[i] > _max(ind.high.sublist(i - 3, i)) &&
        ind.high[i] >= _max(ind.high.sublist(i + 1, min(i + 4, ind.n)))) {
      swingHighs.add(MapEntry(i, ind.high[i]));
    }
  }

  if (swingLows.isEmpty || swingHighs.isEmpty) return PatternDetection.empty();

  final recentHigh = swingHighs.last;
  final recentLow = swingLows.last;

  if (recentLow.key <= recentHigh.key) return PatternDetection.empty();

  final swingRange = recentHigh.value - recentLow.value;
  final fib618 = recentHigh.value - swingRange * 0.618;
  final fib50 = recentHigh.value - swingRange * 0.5;

  final currentPrice = ind.close.last;
  final near618 =
      (currentPrice - fib618).abs() / fib618 * 100 < 3;
  final near50 =
      (currentPrice - fib50).abs() / fib50 * 100 < 3;

  if (!near618 && !near50) return PatternDetection.empty();

  final aboveEma10 = currentPrice > ema10.last;
  final ema10Slope = ind.n >= 3
      ? (ema10.last - ema10[ind.n - 3]) / ema10[ind.n - 3] * 100
      : 0.0;

  int score = 0;
  final evidence = <String>[];

  if (near618) {
    score += 30;
    final fibPct = (currentPrice / fib618 - 1) * 100;
    evidence.add(
        '✅ At 61.8% golden ratio (dev ${fibPct.abs().toStringAsFixed(1)}%)');
  } else {
    score += 20;
    final fibPct = (currentPrice / fib50 - 1) * 100;
    evidence.add(
        '🟡 At 50% fib level (dev ${fibPct.abs().toStringAsFixed(1)}%)');
  }

  if (aboveEma10) {
    score += 25;
    evidence.add(
        '✅ Above 10 EMA (${currentPrice.toStringAsFixed(1)} > ${ema10.last.toStringAsFixed(1)})');
  } else {
    score += 10;
    evidence.add('🟡 Below 10 EMA — wait');
  }

  if (ema10Slope > 0) {
    score += 20;
    evidence.add('✅ 10 EMA rising (${ema10Slope.toStringAsFixed(2)}%)');
  } else {
    score += 5;
  }

  final swingPct = (recentHigh.value / recentLow.value - 1) * 100;
  if (swingPct > 20) {
    score += 15;
    evidence.add('✅ Strong swing: ${swingPct.toStringAsFixed(1)}%');
  } else if (swingPct > 10) {
    score += 10;
  }

  final avgVol = ind.avgVol(20);
  final volRatio = ind.volume.last / max(avgVol, 1);
  if (volRatio > 1.3) {
    score += 10;
    evidence.add('🟡 Volume on bounce: ${volRatio.toStringAsFixed(1)}x');
  }

  if (score >= 50) {
    return PatternDetection(
      matched: true,
      score: score,
      evidence: evidence,
      details: {
        'fib_618': fib618,
        'swing_high': recentHigh.value,
        'swing_low': recentLow.value,
        'above_ema10': aboveEma10,
      },
    );
  }
  return PatternDetection.empty();
}

// ══════════════════════════════════════════════════════════════════════════
//  MASTER SCANNER
// ══════════════════════════════════════════════════════════════════════════

class DarvaXScannerEngine {
  final YahooFinanceService _yahoo;
  final int _minScore;

  /// Stock universe to scan — NIFTY 200
  static List<String> get UNIVERSE => Nifty200.uniqueTickers;

  DarvaXScannerEngine({
    YahooFinanceService? yahoo,
    int minScore = 40,
  })  : _yahoo = yahoo ?? YahooFinanceService(),
        _minScore = minScore;

  /// Run all pattern detectors on one stock's data
  Map<String, PatternDetection> _runDetectors(List<StockCandle> candles) {
    final ind = _Indicators(candles);
    return {
      'HIGH_DRY_FRY': detectHighDryFry(ind),
      'BULLISH_TASUKI': detectBullishTasuki(ind),
      'INSIDE_BAR_BREAK': detectInsideBarBreakout(ind),
      'MORNING_STAR': detectMorningStar(ind),
      'DOUBLE_BOTTOM': detectDoubleBottom(ind),
      'BABY_CRADLE': detectBabyCradle(ind),
      'DARVAX_JALWA': detectDarvaXJalwa(ind),
      'LAL_DABANGG': detectLalDabangg(ind),
      'ZIGZAG_FIB': detectZigzagFib(ind),
    };
  }

  /// Scan a single ticker for DarvaX patterns
  Future<ScanResult> scanTicker(String ticker,
      {List<StockCandle>? preloaded}) async {
    final candles = preloaded ?? await _yahoo.fetchDailyData(ticker);
    if (candles.length < 20) {
      return ScanResult(ticker: ticker);
    }

    final results = _runDetectors(candles);
    String? bestPattern;
    int bestScore = 0;

    results.forEach((name, detection) {
      if (detection.matched && detection.score > bestScore) {
        bestPattern = name;
        bestScore = detection.score;
      }
    });

    final price = candles.last.close;
    final patternMeta =
        bestPattern != null ? PATTERN_META[bestPattern] : null;

    return ScanResult(
      ticker: ticker,
      bestPattern: bestPattern,
      bestScore: bestScore,
      price: price,
      results: results,
      patternMeta: patternMeta,
    );
  }

  /// Scan the full universe of stocks
  Future<List<ScanResult>> scanUniverse({
    void Function(String ticker, int index, int total)? onProgress,
  }) async {
    final data = await _yahoo.fetchMultiple(UNIVERSE, onProgress: onProgress);

    final results = <ScanResult>[];
    for (int i = 0; i < UNIVERSE.length; i++) {
      final ticker = UNIVERSE[i];
      onProgress?.call(ticker, i, UNIVERSE.length);
      final candles = data[ticker] ?? [];
      if (candles.length < 20) continue;

      final result = await scanTicker(ticker, preloaded: candles);
      if (result.bestScore >= _minScore) {
        results.add(result);
      }
    }

    // Sort by score descending
    results.sort((a, b) => b.bestScore.compareTo(a.bestScore));
    return results;
  }
}
