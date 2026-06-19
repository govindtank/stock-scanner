import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/shared_widgets.dart';
import '../../core/analytics/darvax_scanner.dart';
import 'blocs/scanner_cubit.dart';

/// ─── Scanner Screen ─────────────────────────────────────────────────────
/// NIFTY 200 universe scan with progress, filterable results, single scan.
///
class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final _searchCtrl = TextEditingController();
  String _selectedFilter = 'All';
  static const _filters = ['All', '≥70', '≥55', '<55'];

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  List<ScanResult> _filtered(List<ScanResult> results) {
    var r = results;
    final q = _searchCtrl.text.trim().toUpperCase();
    if (q.isNotEmpty) {
      r = r.where((s) => s.ticker.contains(q)).toList();
    }
    return switch (_selectedFilter) {
      '≥70' => r.where((s) => s.bestScore >= 70).toList(),
      '≥55' => r.where((s) => s.bestScore >= 55).toList(),
      '<55' => r.where((s) => s.bestScore < 55).toList(),
      _ => r,
    };
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scanner'),
        actions: [
          BlocBuilder<ScannerCubit, ScannerState>(
            builder: (_, state) {
              if (state is ScannerLoaded && state.results.isNotEmpty) {
                return Padding(
                  padding: const EdgeInsets.only(right: 12),
                  child: StatusBadge.neutral('${state.results.length} found'),
                );
              }
              return const SizedBox.shrink();
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // ── Search + Scan Button ──
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchCtrl,
                    decoration: InputDecoration(
                      hintText: 'Search ticker...',
                      prefixIcon: const Icon(Icons.search_rounded, size: 18, color: AppColors.textMuted),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      suffixIcon: _searchCtrl.text.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear_rounded, size: 16),
                              onPressed: () { _searchCtrl.clear(); setState(() {}); },
                            )
                          : null,
                    ),
                    style: const TextStyle(fontSize: 14),
                    onChanged: (_) => setState(() {}),
                    textInputAction: TextInputAction.search,
                    onSubmitted: (v) {
                      if (v.trim().isNotEmpty) {
                        context.read<ScannerCubit>().scanSingle(v.trim().toUpperCase());
                      }
                    },
                  ),
                ),
                const SizedBox(width: 8),
                BlocBuilder<ScannerCubit, ScannerState>(
                  builder: (_, state) {
                    final isScanning = state is ScannerScanning;
                    return SizedBox(
                      height: 42,
                      child: ElevatedButton.icon(
                        onPressed: isScanning
                            ? null
                            : () => context.read<ScannerCubit>().scan(),
                        icon: Icon(isScanning ? Icons.hourglass_top_rounded : Icons.radar_rounded, size: 16),
                        label: Text(isScanning ? 'Scanning...' : 'Scan All'),
                      ),
                    );
                  },
                ),
              ],
            ),
          ),

          // ── Filter Chips ──
          BlocBuilder<ScannerCubit, ScannerState>(
            builder: (_, state) {
              if (state is! ScannerLoaded) return const SizedBox.shrink();
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                child: Row(
                  children: _filters.map((f) {
                    final selected = _selectedFilter == f;
                    return Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: ChoiceChip(
                        label: Text(f, style: const TextStyle(fontSize: 12)),
                        selected: selected,
                        onSelected: (_) => setState(() => _selectedFilter = f),
                        selectedColor: AppColors.accent.withOpacity(0.2),
                        labelStyle: TextStyle(
                          color: selected ? AppColors.accentBright : AppColors.textMuted,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    );
                  }).toList(),
                ),
              );
            },
          ),

          // ── Progress Indicator ──
          BlocBuilder<ScannerCubit, ScannerState>(
            builder: (_, state) {
              if (state is! ScannerScanning) return const SizedBox.shrink();
              final s = state;  // Already confirmed ScannerScanning above
              final pct = s.total > 0 ? (s.progress / s.total) : 0.0;
              return Padding(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    LinearProgressIndicator(
                      value: pct,
                      backgroundColor: AppColors.border,
                      color: AppColors.accent,
                      minHeight: 3,
                    ),
                    const SizedBox(height: 6),
                    Text('${s.progress} / ${s.total} — ${s.currentTicker}',
                      style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                  ],
                ),
              );
            },
          ),

          // ── Results / States ──
          Expanded(
            child: BlocBuilder<ScannerCubit, ScannerState>(
              builder: (context, state) {
                return switch (state) {
                  ScannerInitial() => const EmptyState(
                    icon: Icons.radar_rounded,
                    title: 'Ready to scan',
                    subtitle: 'Scan the NIFTY 200 universe for DarvaX patterns',
                  ),
                  ScannerScanning s => s.progress > 0
                      ? const SizedBox.shrink()
                      : const Center(child: CircularProgressIndicator(color: AppColors.accent)),
                  ScannerLoaded s => _ResultsList(results: _filtered(s.results), scannedAt: s.scannedAt),
                  ScannerError s => ErrorView(
                    message: s.message,
                    onRetry: () => context.read<ScannerCubit>().scan(),
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

class _ResultsList extends StatelessWidget {
  final List<ScanResult> results;
  final DateTime scannedAt;

  const _ResultsList({required this.results, required this.scannedAt});

  @override
  Widget build(BuildContext context) {
    if (results.isEmpty) {
      return const EmptyState(
        icon: Icons.search_off_rounded,
        title: 'No matches',
        subtitle: 'Try a different filter or search term',
      );
    }

    final sorted = List<ScanResult>.from(results)
      ..sort((a, b) => b.bestScore.compareTo(a.bestScore));

    return ListView.separated(
      padding: const EdgeInsets.only(bottom: 24),
      itemCount: sorted.length,
      separatorBuilder: (_, __) => const Divider(height: 1, indent: 16, endIndent: 16),
      itemBuilder: (_, i) {
        final r = sorted[i];
        return StockTile(
          ticker: r.ticker,
          name: r.bestPattern != null ? 'Pattern: ${r.bestPattern}' : null,
          price: r.price,
          score: r.bestScore.toDouble(),
        );
      },
    );
  }
}
