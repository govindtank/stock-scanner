import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/shared_widgets.dart';
import '../../core/blocs/dashboard/dashboard_cubit.dart';
import '../../core/blocs/dashboard/dashboard_state.dart';
import '../../core/blocs/portfolio/portfolio_cubit.dart';
import '../../core/blocs/portfolio/portfolio_state.dart';

/// ─── Dashboard Screen ───────────────────────────────────────────────────
/// Market overview: watchlist table + portfolio snapshot + quick actions.
///
class DashboardScreen extends StatefulWidget {
  final void Function(int tab)? onNavigateToTab;

  const DashboardScreen({super.key, this.onNavigateToTab});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DashboardCubit>().load();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('DarvaX'),
        actions: [
          BlocBuilder<DashboardCubit, DashboardState>(
            builder: (_, state) {
              final synced = state is DashboardLoaded && state.lastSync != null;
              return Padding(
                padding: const EdgeInsets.only(right: 8),
                child: IconButton(
                  icon: Icon(
                    Icons.refresh_rounded,
                    size: 20,
                    color: synced ? AppColors.accent : AppColors.textMuted,
                  ),
                  onPressed: () => context.read<DashboardCubit>().refresh(),
                ),
              );
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        color: AppColors.accent,
        backgroundColor: AppColors.bg,
        onRefresh: () async => context.read<DashboardCubit>().load(),
        child: BlocBuilder<DashboardCubit, DashboardState>(
          builder: (context, state) {
            return switch (state) {
              DashboardInitial() => const SizedBox.shrink(),
              DashboardLoading() => _buildLoading(),
              DashboardLoaded s => _buildLoaded(context, s),
              DashboardError s => ErrorView(
                message: s.message,
                onRetry: () => context.read<DashboardCubit>().load(),
              ),
            };
          },
        ),
      ),
    );
  }

  Widget _buildLoading() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: const [
        ShimmerCard(height: 100),
        SizedBox(height: 12),
        ShimmerCard(height: 72),
        SizedBox(height: 12),
        ShimmerCard(height: 72),
        SizedBox(height: 12),
        ShimmerCard(height: 72),
      ],
    );
  }

  Widget _buildLoaded(BuildContext context, DashboardLoaded state) {
    // Get portfolio holdings from portfolio cubit
    final portfolioState = context.watch<PortfolioCubit>().state;
    final holdings = portfolioState is PortfolioLoaded ? portfolioState.holdings : <PortfolioHolding>[];
    final holdingCount = holdings.length;
    final recentHoldings = holdings.take(3).toList();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // ── Portfolio Summary Card ──
        _buildPortfolioSumary(context, state, holdingCount, recentHoldings),
        const SizedBox(height: 16),

        // ── Quick Actions ──
        _buildQuickActions(context),
        const SizedBox(height: 20),

        // ── Market Watchlist ──
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('Market Watch', style: TextStyle(
              color: AppColors.textPrimary, fontSize: 16, fontWeight: FontWeight.w600,
            )),
            Text(state.lastSync != null ? _formatTime(state.lastSync!) : '', style: const TextStyle(
              color: AppColors.textMuted, fontSize: 11,
            )),
          ],
        ),
        const SizedBox(height: 8),
        ...state.marketQuotes.map((q) => _buildWatchlistRow(q)),
        if (state.marketQuotes.isEmpty)
          const Padding(
            padding: EdgeInsets.all(20),
            child: Text('No market data available', style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
          ),
      ],
    );
  }

  Widget _buildPortfolioSumary(BuildContext context, DashboardLoaded state, int holdingCount, List<PortfolioHolding> recentHoldings) {
    final totalValue = state.portfolioValue;
    final totalPnl = state.portfolioPnl;
    final totalInvested = totalValue - totalPnl;
    final pnlPct = totalInvested > 0 ? (totalPnl / totalInvested) * 100 : 0.0;
    final isPositive = totalPnl >= 0;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isPositive
              ? [AppColors.green.withOpacity(0.12), AppColors.surface.withOpacity(0.8)]
              : [AppColors.red.withOpacity(0.12), AppColors.surface.withOpacity(0.8)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isPositive ? AppColors.green.withOpacity(0.2) : AppColors.red.withOpacity(0.2),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.account_balance_wallet_rounded, size: 18, color: AppColors.textSecondary),
              const SizedBox(width: 8),
              const Text('Portfolio', style: TextStyle(color: AppColors.textSecondary, fontSize: 12, fontWeight: FontWeight.w500)),
              const Spacer(),
              if (holdingCount > 0)
                StatusBadge(label: '$holdingCount holdings', backgroundColor: AppColors.accentSubtle, textColor: AppColors.accent),
            ],
          ),
          const SizedBox(height: 12),
          Text('₹${totalValue.toStringAsFixed(2)}', style: const TextStyle(
            color: AppColors.textPrimary, fontSize: 28, fontWeight: FontWeight.w700,
          )),
          const SizedBox(height: 6),
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: (isPositive ? AppColors.green : AppColors.red).withOpacity(0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(isPositive ? Icons.trending_up_rounded : Icons.trending_down_rounded, size: 14,
                        color: isPositive ? AppColors.greenBright : AppColors.redBright),
                    const SizedBox(width: 4),
                    Text(
                      '${isPositive ? '+' : ''}${totalPnl.toStringAsFixed(2)} (${pnlPct.toStringAsFixed(1)}%)',
                      style: TextStyle(
                        color: isPositive ? AppColors.greenBright : AppColors.redBright,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Text('invested', style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
            ],
          ),

          // ── Recent holdings preview ──
          if (recentHoldings.isNotEmpty) ...[
            const SizedBox(height: 14),
            const Divider(height: 1),
            const SizedBox(height: 10),
            ...recentHoldings.map((h) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                children: [
                  Text(h.ticker.replaceAll('.NS', ''), style: const TextStyle(
                    color: AppColors.textPrimary, fontSize: 13, fontWeight: FontWeight.w500,
                  )),
                  const Spacer(),
                  Text('₹${h.currentPrice.toStringAsFixed(2)}', style: const TextStyle(
                    color: AppColors.textSecondary, fontSize: 13,
                  )),
                  const SizedBox(width: 12),
                  Text(
                    '${h.unrealizedPnl >= 0 ? '+' : ''}${h.unrealizedPnlPct.toStringAsFixed(1)}%',
                    style: TextStyle(
                      color: h.unrealizedPnl >= 0 ? AppColors.greenBright : AppColors.redBright,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            )),
          ],
        ],
      ),
    );
  }

  Widget _buildQuickActions(BuildContext context) {
    return Row(
      children: [
        _ActionChip(icon: Icons.search_rounded, label: 'Analyze', onTap: widget.onNavigateToTab != null ? () => widget.onNavigateToTab!(1) : null),
        const SizedBox(width: 10),
        _ActionChip(icon: Icons.radar_rounded, label: 'Scan', onTap: widget.onNavigateToTab != null ? () => widget.onNavigateToTab!(3) : null),
        const SizedBox(width: 10),
        _ActionChip(icon: Icons.add_alert_rounded, label: 'Alert', onTap: widget.onNavigateToTab != null ? () => widget.onNavigateToTab!(4) : null),
        const SizedBox(width: 10),
        _ActionChip(icon: Icons.refresh_rounded, label: 'Refresh', onTap: () => context.read<DashboardCubit>().refresh()),
      ],
    );
  }

  Widget _buildWatchlistRow(LiveQuote q) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surface,
        border: Border(bottom: BorderSide(color: AppColors.border.withOpacity(0.5))),
      ),
      child: Row(
        children: [
          Expanded(
            flex: 3,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(q.displayName, style: const TextStyle(
                  color: AppColors.textPrimary, fontSize: 13, fontWeight: FontWeight.w500,
                )),
                if (q.ticker != q.displayName)
                  Text(q.ticker, style: const TextStyle(
                    color: AppColors.textTertiary, fontSize: 11,
                  )),
              ],
            ),
          ),
          Expanded(
            flex: 2,
            child: Text('₹${q.price.toStringAsFixed(2)}', textAlign: TextAlign.right, style: const TextStyle(
              color: AppColors.textPrimary, fontSize: 13, fontWeight: FontWeight.w600,
            )),
          ),
          SizedBox(
            width: 80,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
              decoration: BoxDecoration(
                color: (q.isUp ? AppColors.green : AppColors.red).withOpacity(0.12),
                borderRadius: BorderRadius.circular(5),
              ),
              child: Text(
                '${q.isUp ? '+' : ''}${q.changePercent.toStringAsFixed(2)}%',
                textAlign: TextAlign.right,
                style: TextStyle(
                  color: q.isUp ? AppColors.greenBright : AppColors.redBright,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _formatTime(String iso) {
    try {
      final dt = DateTime.parse(iso);
      final now = DateTime.now();
      final diff = now.difference(dt);
      if (diff.inSeconds < 60) return '${diff.inSeconds}s ago';
      if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
      return '${diff.inHours}h ago';
    } catch (_) {
      return '';
    }
  }
}

class _ActionChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback? onTap;

  const _ActionChip({required this.icon, required this.label, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: AppColors.panel,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: AppColors.accent),
            const SizedBox(width: 6),
            Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12, fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}
