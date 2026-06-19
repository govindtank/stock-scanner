import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/shared_widgets.dart';
import '../../core/blocs/portfolio/portfolio_cubit.dart';
import '../../core/blocs/portfolio/portfolio_state.dart';

/// ─── Portfolio Screen ───────────────────────────────────────────────────
/// Holdings list with live P&L, allocation preview, add/edit/delete.
///
class PortfolioScreen extends StatefulWidget {
  final void Function(int tab)? onNavigateToTab;

  const PortfolioScreen({super.key, this.onNavigateToTab});

  @override
  State<PortfolioScreen> createState() => _PortfolioScreenState();
}

class _PortfolioScreenState extends State<PortfolioScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Portfolio'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, size: 20),
            tooltip: 'Refresh Prices',
            onPressed: () => context.read<PortfolioCubit>().refreshPrices(),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => context.read<PortfolioCubit>().refreshPrices(),
        child: BlocBuilder<PortfolioCubit, PortfolioState>(
          builder: (context, state) {
            return switch (state) {
              PortfolioInitial() || PortfolioLoading() => const ShimmerList(itemCount: 6),
              PortfolioLoaded s => _PortfolioContent(state: s),
              PortfolioError s => ErrorView(
                message: s.message,
                onRetry: () => context.read<PortfolioCubit>().refreshPrices(),
              ),
            };
          },
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showAddDialog(context),
        backgroundColor: AppColors.accent,
        icon: const Icon(Icons.add_rounded, size: 18),
        label: const Text('Add Holding'),
      ),
    );
  }

  void _showAddDialog(BuildContext context) {
    final tickerCtrl = TextEditingController();
    final nameCtrl = TextEditingController();
    final qtyCtrl = TextEditingController();
    final priceCtrl = TextEditingController();
    final formKey = GlobalKey<FormState>();

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Add Holding'),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: tickerCtrl,
                decoration: const InputDecoration(labelText: 'Ticker', hintText: 'RELIANCE'),
                textCapitalization: TextCapitalization.characters,
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: nameCtrl,
                decoration: const InputDecoration(labelText: 'Name (optional)', hintText: 'Reliance Industries'),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: qtyCtrl,
                decoration: const InputDecoration(labelText: 'Quantity'),
                keyboardType: TextInputType.number,
                validator: (v) => (v == null || double.tryParse(v) == null) ? 'Enter a number' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: priceCtrl,
                decoration: const InputDecoration(labelText: 'Avg. Price'),
                keyboardType: TextInputType.number,
                validator: (v) => (v == null || double.tryParse(v) == null) ? 'Enter a number' : null,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              if (!formKey.currentState!.validate()) return;
              context.read<PortfolioCubit>().addHolding(
                tickerCtrl.text.trim().toUpperCase(),
                name: nameCtrl.text.trim(),
                quantity: double.parse(qtyCtrl.text.trim()),
                avgPrice: double.parse(priceCtrl.text.trim()),
              );
              Navigator.pop(ctx);
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }
}

class _PortfolioContent extends StatelessWidget {
  final PortfolioLoaded state;

  const _PortfolioContent({required this.state});

  @override
  Widget build(BuildContext context) {
    final holdings = state.holdings;

    return Column(
      children: [
        // ── Summary Bar ──
        Container(
          margin: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                AppColors.accent.withOpacity(0.15),
                AppColors.accent.withOpacity(0.05),
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.accent.withOpacity(0.2)),
          ),
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: _SummaryItem(
                      label: 'Invested',
                      value: '₹${state.totalInvested.toStringAsFixed(0)}',
                    ),
                  ),
                  Expanded(
                    child: _SummaryItem(
                      label: 'Current',
                      value: '₹${state.totalValue.toStringAsFixed(0)}',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: _SummaryItem(
                      label: 'Total P&L',
                      value: '${state.totalPnl >= 0 ? '+' : ''}₹${state.totalPnl.toStringAsFixed(0)}',
                      color: state.totalPnl >= 0 ? AppColors.green : AppColors.red,
                    ),
                  ),
                  Expanded(
                    child: _SummaryItem(
                      label: 'Return',
                      value: '${state.totalPnlPct >= 0 ? '+' : ''}${state.totalPnlPct.toStringAsFixed(2)}%',
                      color: state.totalPnlPct >= 0 ? AppColors.green : AppColors.red,
                    ),
                  ),
                ],
              ),
              if (state.pricesUpdating) ...[
                const SizedBox(height: 10),
                const LinearProgressIndicator(
                  backgroundColor: AppColors.border,
                  color: AppColors.accent,
                  minHeight: 2,
                ),
              ],
            ],
          ),
        ),

        // ── Holdings Count ──
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
          child: Row(
            children: [
              Text('${holdings.length} Holding${holdings.length != 1 ? 's' : ''}',
                style: const TextStyle(color: AppColors.textMuted, fontSize: 13)),
            ],
          ),
        ),

        // ── Holdings List ──
        if (holdings.isEmpty)
          const Expanded(
            child: EmptyState(
              icon: Icons.account_balance_wallet_rounded,
              title: 'No holdings yet',
              subtitle: 'Tap the + button to add your first holding',
            ),
          )
        else
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.only(bottom: 80),
              itemCount: holdings.length,
              separatorBuilder: (_, __) => const Divider(height: 1, indent: 16, endIndent: 16),
              itemBuilder: (context, i) {
                final h = holdings[i];
                final investVal = h.investedValue;
                final curVal = h.currentValue;
                final pnl = curVal - investVal;
                return _HoldingTile(
                  holding: h,
                  pnl: pnl,
                  onDelete: () => context.read<PortfolioCubit>().removeHolding(h.ticker),
                );
              },
            ),
          ),
      ],
    );
  }
}

class _SummaryItem extends StatelessWidget {
  final String label;
  final String value;
  final Color? color;

  const _SummaryItem({required this.label, required this.value, this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: AppColors.textMuted, fontSize: 11, fontWeight: FontWeight.w500)),
        const SizedBox(height: 4),
        Text(value, style: TextStyle(
          color: color ?? AppColors.textPrimary,
          fontSize: 16,
          fontWeight: FontWeight.w600,
        )),
      ],
    );
  }
}

class _HoldingTile extends StatelessWidget {
  final PortfolioHolding holding;
  final double pnl;
  final VoidCallback onDelete;

  const _HoldingTile({
    required this.holding,
    required this.pnl,
    required this.onDelete,
  });

  String _displayTicker(String t) => t.endsWith('.NS') ? t.substring(0, t.length - 3) : t;

  @override
  Widget build(BuildContext context) {
    final pnlColor = pnl >= 0 ? AppColors.green : AppColors.red;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          // Ticker + quantity
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_displayTicker(holding.ticker),
                  style: const TextStyle(color: AppColors.textPrimary, fontSize: 15, fontWeight: FontWeight.w500)),
                const SizedBox(height: 2),
                if (holding.name.isNotEmpty)
                  Text(holding.name, style: const TextStyle(color: AppColors.textTertiary, fontSize: 12)),
                const SizedBox(height: 4),
                Text('${holding.quantity.toInt()} × ₹${holding.avgPrice.toStringAsFixed(0)}',
                  style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
              ],
            ),
          ),
          // P&L
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('₹${holding.currentPrice.toStringAsFixed(2)}',
                style: const TextStyle(color: AppColors.textPrimary, fontSize: 14, fontWeight: FontWeight.w500)),
              const SizedBox(height: 2),
              Text('${pnl >= 0 ? '+' : ''}₹${pnl.toStringAsFixed(0)}',
                style: TextStyle(color: pnlColor, fontSize: 12, fontWeight: FontWeight.w600)),
              Text('${holding.unrealizedPnlPct >= 0 ? '+' : ''}${holding.unrealizedPnlPct.toStringAsFixed(2)}%',
                style: TextStyle(color: pnlColor, fontSize: 11, fontWeight: FontWeight.w500)),
            ],
          ),
          const SizedBox(width: 8),
          // Delete
          InkWell(
            onTap: onDelete,
            borderRadius: BorderRadius.circular(6),
            child: Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: AppColors.red.withOpacity(0.1),
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Icon(Icons.delete_rounded, size: 16, color: AppColors.red),
            ),
          ),
        ],
      ),
    );
  }
}
