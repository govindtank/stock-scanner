import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/shared_widgets.dart';
import 'blocs/alerts_cubit.dart';
import 'blocs/alerts_state.dart';

/// ─── Alerts Screen ──────────────────────────────────────────────────────
/// Active alerts + triggered alerts tabs, create/delete/check.
///
class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabCtrl;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Alerts'),
        bottom: TabBar(
          controller: _tabCtrl,
          indicatorColor: AppColors.accent,
          labelColor: AppColors.textPrimary,
          unselectedLabelColor: AppColors.textMuted,
          labelStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
          tabs: [
            Tab(
              child: BlocBuilder<AlertsCubit, AlertsState>(
                builder: (_, state) {
                  final count = state is AlertsLoaded ? state.alerts.length : 0;
                  return Text('Active${count > 0 ? ' ($count)' : ''}');
                },
              ),
            ),
            Tab(
              child: BlocBuilder<AlertsCubit, AlertsState>(
                builder: (_, state) {
                  final count = state is AlertsLoaded ? state.triggeredAlerts.length : 0;
                  return Text('Triggered${count > 0 ? ' ($count)' : ''}');
                },
              ),
            ),
          ],
        ),
      ),
      body: BlocBuilder<AlertsCubit, AlertsState>(
        builder: (context, state) {
          return switch (state) {
            AlertsInitial() => const Center(child: CircularProgressIndicator(color: AppColors.accent)),
            AlertsLoaded s => TabBarView(
              controller: _tabCtrl,
              children: [
                _ActiveAlertsTab(alerts: s.alerts, onCheck: () => context.read<AlertsCubit>().checkAlerts()),
                _TriggeredAlertsTab(triggered: s.triggeredAlerts, onClear: () => context.read<AlertsCubit>().clearTriggered()),
              ],
            ),
            AlertsError s => ErrorView(
              message: s.message,
              onRetry: () => context.read<AlertsCubit>().checkAlerts(),
            ),
          };
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showAddDialog(context),
        backgroundColor: AppColors.accent,
        icon: const Icon(Icons.add_alert_rounded, size: 18),
        label: const Text('New Alert'),
      ),
    );
  }

  void _showAddDialog(BuildContext context) {
    final tickerCtrl = TextEditingController();
    final priceCtrl = TextEditingController();
    final formKey = GlobalKey<FormState>();

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Set Price Alert'),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: tickerCtrl,
                decoration: const InputDecoration(
                  labelText: 'Ticker',
                  hintText: 'RELIANCE.NS',
                ),
                textCapitalization: TextCapitalization.characters,
                validator: (v) => (v == null || v.trim().isEmpty) ? 'Required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: priceCtrl,
                decoration: const InputDecoration(
                  labelText: 'Target Price (₹)',
                  hintText: '3000',
                ),
                keyboardType: TextInputType.number,
                validator: (v) => (v == null || double.tryParse(v) == null)
                    ? 'Enter a valid price'
                    : null,
              ),
              const SizedBox(height: 12),
              const Text(
                'You will be notified when the stock price crosses this target.',
                style: TextStyle(color: AppColors.textTertiary, fontSize: 12),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              if (!formKey.currentState!.validate()) return;
              final ticker = tickerCtrl.text.trim().toUpperCase();
              final cleanTicker = ticker.endsWith('.NS') ? ticker : '$ticker.NS';
              final price = double.parse(priceCtrl.text.trim());
              context.read<AlertsCubit>().addPriceAlert(
                ticker: cleanTicker,
                targetPrice: price,
                title: '$cleanTicker @ ₹${price.toStringAsFixed(0)}',
                description: 'Price alert when $cleanTicker reaches ₹${price.toStringAsFixed(0)}',
              );
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Alert set for $cleanTicker at ₹${price.toStringAsFixed(0)}'),
                ),
              );
            },
            child: const Text('Set Alert'),
          ),
        ],
      ),
    );
  }
}

/// ─── Active Alerts Tab ──────────────────────────────────────────────────
class _ActiveAlertsTab extends StatelessWidget {
  final List<DarvaAlert> alerts;
  final VoidCallback onCheck;

  const _ActiveAlertsTab({required this.alerts, required this.onCheck});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // ── Check button ──
        if (alerts.isNotEmpty)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: onCheck,
                icon: const Icon(Icons.refresh_rounded, size: 16),
                label: const Text('Check Prices Against Alerts'),
              ),
            ),
          ),

        // ── List or Empty ──
        Expanded(
          child: alerts.isEmpty
              ? const EmptyState(
                  icon: Icons.notifications_off_rounded,
                  title: 'No active alerts',
                  subtitle: 'Tap + to create your first price alert',
                )
              : ListView.separated(
                  padding: const EdgeInsets.only(top: 8, bottom: 80),
                  itemCount: alerts.length,
                  separatorBuilder: (_, __) => const Divider(height: 1, indent: 16, endIndent: 16),
                  itemBuilder: (_, i) => _AlertTile(
                    alert: alerts[i],
                    onDelete: () => context.read<AlertsCubit>().removeAlert(alerts[i].id),
                  ),
                ),
        ),
      ],
    );
  }
}

/// ─── Triggered Alerts Tab ───────────────────────────────────────────────
class _TriggeredAlertsTab extends StatelessWidget {
  final List<DarvaAlert> triggered;
  final VoidCallback onClear;

  const _TriggeredAlertsTab({required this.triggered, required this.onClear});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        if (triggered.isNotEmpty)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: onClear,
                icon: const Icon(Icons.clear_all_rounded, size: 16),
                label: const Text('Clear All'),
              ),
            ),
          ),
        Expanded(
          child: triggered.isEmpty
              ? const EmptyState(
                  icon: Icons.check_circle_rounded,
                  title: 'No triggered alerts',
                  subtitle: 'Your price alerts will appear here when triggered',
                )
              : ListView.separated(
                  padding: const EdgeInsets.only(top: 8, bottom: 80),
                  itemCount: triggered.length,
                  separatorBuilder: (_, __) => const Divider(height: 1, indent: 16, endIndent: 16),
                  itemBuilder: (_, i) => _TriggeredTile(alert: triggered[i]),
                ),
        ),
      ],
    );
  }
}

/// ─── Alert Tile ─────────────────────────────────────────────────────────
class _AlertTile extends StatelessWidget {
  final DarvaAlert alert;
  final VoidCallback onDelete;

  const _AlertTile({required this.alert, required this.onDelete});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          const Icon(Icons.notifications_active_rounded, size: 20, color: AppColors.accent),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(alert.title, style: const TextStyle(
                  color: AppColors.textPrimary, fontSize: 14, fontWeight: FontWeight.w500,
                )),
                const SizedBox(height: 2),
                Text(alert.description, style: const TextStyle(
                  color: AppColors.textTertiary, fontSize: 12,
                )),
              ],
            ),
          ),
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

/// ─── Triggered Tile ─────────────────────────────────────────────────────
class _TriggeredTile extends StatelessWidget {
  final DarvaAlert alert;

  const _TriggeredTile({required this.alert});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          const Icon(Icons.check_circle_rounded, size: 20, color: AppColors.green),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(alert.title, style: const TextStyle(
                  color: AppColors.textPrimary, fontSize: 14, fontWeight: FontWeight.w500,
                )),
                const SizedBox(height: 2),
                Text('Triggered', style: const TextStyle(
                  color: AppColors.green, fontSize: 12, fontWeight: FontWeight.w500,
                )),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
