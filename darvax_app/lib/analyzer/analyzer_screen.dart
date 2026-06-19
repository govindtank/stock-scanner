import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/shared_widgets.dart';
import '../../core/analytics/darvax_scanner.dart';
import 'blocs/analyzer_cubit.dart';

/// ─── Analyzer Screen ────────────────────────────────────────────────────
/// Stock deep-dive: search, run 9 patterns, see Entry/Exit verdict.
///
class AnalyzerScreen extends StatefulWidget {
  const AnalyzerScreen({super.key});

  @override
  State<AnalyzerScreen> createState() => _AnalyzerScreenState();
}

class _AnalyzerScreenState extends State<AnalyzerScreen> {
  final _tickerController = TextEditingController();

  @override
  void dispose() {
    _tickerController.dispose();
    super.dispose();
  }

  void _analyze() {
    final ticker = _tickerController.text.trim().toUpperCase();
    if (ticker.isEmpty) return;
    context.read<AnalyzerCubit>().analyze(ticker);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Analyzer')),
      body: Column(
        children: [
          // ── Search Bar ──
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _tickerController,
                    decoration: InputDecoration(
                      hintText: 'Enter NSE ticker...',
                      prefixIcon: const Icon(Icons.search_rounded, size: 18, color: AppColors.textMuted),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                    ),
                    style: const TextStyle(fontSize: 14, letterSpacing: 1),
                    textCapitalization: TextCapitalization.characters,
                    textInputAction: TextInputAction.search,
                    onSubmitted: (_) => _analyze(),
                  ),
                ),
                const SizedBox(width: 8),
                SizedBox(
                  height: 42,
                  child: ElevatedButton.icon(
                    onPressed: _analyze,
                    icon: const Icon(Icons.analytics_rounded, size: 16),
                    label: const Text('Analyze'),
                  ),
                ),
              ],
            ),
          ),

          // ── Quick ticker chips ──
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Wrap(
              spacing: 6,
              runSpacing: 4,
              children: ['RELIANCE', 'HDFCBANK', 'TCS', 'INFY', 'ICICIBANK', 'SBIN', 'BAJFINANCE', 'TRENT']
                  .map((t) => ActionChip(
                        label: Text(t, style: const TextStyle(fontSize: 11)),
                        onPressed: () {
                          _tickerController.text = t;
                          _analyze();
                        },
                        backgroundColor: AppColors.panel,
                        side: const BorderSide(color: AppColors.border),
                        labelStyle: const TextStyle(color: AppColors.textSecondary),
                      ))
                  .toList(),
            ),
          ),

          const SizedBox(height: 8),

          // ── Results ──
          Expanded(
            child: BlocBuilder<AnalyzerCubit, AnalyzerState>(
              builder: (context, state) {
                return switch (state) {
                  AnalyzerInitial() => const EmptyState(
                    icon: Icons.analytics_rounded,
                    title: 'Enter a ticker',
                    subtitle: 'Analyze any NSE stock for DarvaX pattern signals',
                  ),
                  AnalyzerLoading s => _AnalyzerLoading(ticker: s.ticker),
                  AnalyzerResult s => _AnalyzerResultView(state: s),
                  AnalyzerError s => ErrorView(
                    message: s.message,
                    onRetry: () => context.read<AnalyzerCubit>().analyze(_tickerController.text.trim().toUpperCase()),
                  ),
                };
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _AnalyzerLoading extends StatelessWidget {
  final String ticker;
  const _AnalyzerLoading({required this.ticker});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const CircularProgressIndicator(color: AppColors.accent),
        const SizedBox(height: 16),
        Text('Analyzing $ticker...', style: const TextStyle(color: AppColors.textSecondary, fontSize: 14)),
        const SizedBox(height: 8),
        const Text('Running 9 DarvaX patterns', style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
      ],
    );
  }
}

class _AnalyzerResultView extends StatelessWidget {
  final AnalyzerResult state;
  const _AnalyzerResultView({required this.state});

  @override
  Widget build(BuildContext context) {
    final sr = state.scanResult;
    final isEntry = sr.bestScore >= 55;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // ── Verdict Card ──
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: isEntry
                  ? [AppColors.green.withOpacity(0.15), AppColors.green.withOpacity(0.05)]
                  : [AppColors.red.withOpacity(0.15), AppColors.red.withOpacity(0.05)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isEntry ? AppColors.green.withOpacity(0.3) : AppColors.red.withOpacity(0.3),
            ),
          ),
          child: Column(
            children: [
              Icon(
                isEntry ? Icons.check_circle_rounded : Icons.cancel_rounded,
                size: 40,
                color: isEntry ? AppColors.greenBright : AppColors.redBright,
              ),
              const SizedBox(height: 8),
              Text(isEntry ? 'ENTRY SIGNAL' : 'AVOID / EXIT',
                style: TextStyle(
                  color: isEntry ? AppColors.greenBright : AppColors.redBright,
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.5,
                )),
              const SizedBox(height: 4),
              Text(state.ticker.replaceAll('.NS', ''),
                style: const TextStyle(color: AppColors.textPrimary, fontSize: 14)),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _VerdictStat(label: 'Score', value: '${sr.bestScore}/100'),
                  const SizedBox(width: 24),
                  _VerdictStat(label: 'Price', value: '₹${sr.price.toStringAsFixed(2)}'),
                  if (sr.bestPattern != null) ...[
                    const SizedBox(width: 24),
                    _VerdictStat(label: 'Pattern', value: sr.bestPattern!),
                  ],
                ],
              ),
            ],
          ),
        ),

        const SizedBox(height: 20),

        // ── Individual Pattern Scores ──
        const SectionHeader(title: 'Pattern Analysis'),
        if (sr.results.isEmpty)
          const Padding(
            padding: EdgeInsets.all(16),
            child: Text('No pattern data available', style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
          )
        else
          ...sr.results.entries.map((entry) {
            final pattern = entry.key;
            final detection = entry.value;
            return _PatternRow(
              name: pattern,
              matched: detection.matched,
              score: detection.score,
              evidence: detection.evidence,
            );
          }),
      ],
    );
  }
}

class _VerdictStat extends StatelessWidget {
  final String label;
  final String value;

  const _VerdictStat({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value, style: const TextStyle(color: AppColors.textPrimary, fontSize: 15, fontWeight: FontWeight.w600)),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
      ],
    );
  }
}

class _PatternRow extends StatelessWidget {
  final String name;
  final bool matched;
  final int score;
  final List<String> evidence;

  const _PatternRow({
    required this.name,
    required this.matched,
    required this.score,
    required this.evidence,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8, left: 16, right: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: const TextStyle(
                  color: AppColors.textPrimary, fontSize: 13, fontWeight: FontWeight.w500,
                )),
                if (evidence.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(evidence.join(', '), maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(
                    color: AppColors.textTertiary, fontSize: 11,
                  )),
                ],
              ],
            ),
          ),
          const SizedBox(width: 12),
          StatusBadge(
            label: matched ? '${score}/100' : '—',
            backgroundColor: matched
                ? (score >= 70 ? AppColors.green.withOpacity(0.15) : AppColors.yellow.withOpacity(0.15))
                : AppColors.textMuted.withOpacity(0.1),
            textColor: matched
                ? (score >= 70 ? AppColors.greenBright : AppColors.yellow)
                : AppColors.textMuted,
          ),
        ],
      ),
    );
  }
}
