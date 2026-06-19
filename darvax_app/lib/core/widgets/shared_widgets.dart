import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

/// ─── PnL Coloured Text ──────────────────────────────────────────────────
class PnlText extends StatelessWidget {
  final double value;
  final bool isPercentage;
  final TextStyle? style;
  final bool showSign;

  const PnlText(
    this.value, {
    super.key,
    this.isPercentage = false,
    this.style,
    this.showSign = true,
  });

  @override
  Widget build(BuildContext context) {
    final color = value >= 0 ? AppColors.green : AppColors.red;
    final sign = value >= 0 ? '+' : '';
    final suffix = isPercentage ? '%' : '';
    final formatted = value >= 0
        ? '${showSign ? sign : ''}₹${value.toStringAsFixed(2)}$suffix'
        : '${showSign ? sign : ''}-₹${value.abs().toStringAsFixed(2)}$suffix';
    return Text(
      formatted,
      style: (style ?? const TextStyle()).copyWith(color: color, fontWeight: FontWeight.w600),
    );
  }
}

/// ─── Currency Text ──────────────────────────────────────────────────────
class CurrencyText extends StatelessWidget {
  final double amount;
  final TextStyle? style;
  final bool compact;

  const CurrencyText(this.amount, {super.key, this.style, this.compact = false});

  String _format(double n) {
    if (compact && n >= 10000000) return '₹${(n / 10000000).toStringAsFixed(2)}Cr';
    if (compact && n >= 100000) return '₹${(n / 100000).toStringAsFixed(2)}L';
    if (n >= 1000) {
      final str = n.toStringAsFixed(0);
      final buffer = StringBuffer();
      int count = 0;
      for (int i = str.length - 1; i >= 0; i--) {
        count++;
        buffer.write(str[i]);
        if (count == 3 && i > 0) { buffer.write(','); count = 0; }
      }
      return '₹${buffer.toString().split('').reversed.join()}';
    }
    return '₹${n.toStringAsFixed(2)}';
  }

  @override
  Widget build(BuildContext context) => Text(_format(amount), style: style);
}

/// ─── KPI Card ───────────────────────────────────────────────────────────
class KpiCard extends StatelessWidget {
  final String label;
  final Widget value;
  final IconData? icon;
  final Color? accentColor;
  final VoidCallback? onTap;

  const KpiCard({
    super.key,
    required this.label,
    required this.value,
    this.icon,
    this.accentColor,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: accentColor?.withOpacity(0.3) ?? AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                if (icon != null) ...[
                  Icon(icon, size: 14, color: accentColor ?? AppColors.textMuted),
                  const SizedBox(width: 6),
                ],
                Text(label, style: const TextStyle(
                  color: AppColors.textMuted, fontSize: 11, fontWeight: FontWeight.w500,
                )),
              ],
            ),
            const SizedBox(height: 8),
            DefaultTextStyle(
              style: const TextStyle(color: AppColors.textPrimary, fontSize: 18, fontWeight: FontWeight.w600),
              child: value,
            ),
          ],
        ),
      ),
    );
  }
}

/// ─── Section Header ─────────────────────────────────────────────────────
class SectionHeader extends StatelessWidget {
  final String title;
  final String? trailing;
  final VoidCallback? onTrailingTap;
  final Widget? action;

  const SectionHeader({
    super.key,
    required this.title,
    this.trailing,
    this.onTrailingTap,
    this.action,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 10),
      child: Row(
        children: [
          Text(title, style: const TextStyle(
            color: AppColors.textPrimary, fontSize: 17, fontWeight: FontWeight.w600,
          )),
          const Spacer(),
          if (action != null) action!,
          if (trailing != null)
            GestureDetector(
              onTap: onTrailingTap,
              child: Text(trailing!, style: const TextStyle(
                color: AppColors.accentBright, fontSize: 12, fontWeight: FontWeight.w500,
              )),
            ),
        ],
      ),
    );
  }
}

/// ─── Status Badge ───────────────────────────────────────────────────────
class StatusBadge extends StatelessWidget {
  final String label;
  final Color backgroundColor;
  final Color textColor;

  StatusBadge({
    super.key,
    required this.label,
    this.backgroundColor = AppColors.panel,
    this.textColor = AppColors.accent,
  });

  StatusBadge.green(this.label, {super.key})
      : backgroundColor = const Color(0x2910B981),
        textColor = const Color(0xFF10B981);

  StatusBadge.red(this.label, {super.key})
      : backgroundColor = const Color(0x29EF4444),
        textColor = const Color(0xFFE54545);

  StatusBadge.yellow(this.label, {super.key})
      : backgroundColor = const Color(0x29F59E0B),
        textColor = const Color(0xFFF59E0B);

  StatusBadge.neutral(this.label, {super.key})
      : backgroundColor = const Color(0x1A8A8F98),
        textColor = const Color(0xFF8A8F98);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(label, style: TextStyle(
        color: textColor, fontSize: 11, fontWeight: FontWeight.w600,
      )),
    );
  }
}

/// ─── Loading Shimmer ────────────────────────────────────────────────────
class ShimmerCard extends StatefulWidget {
  final double height;
  final double width;
  final double borderRadius;

  const ShimmerCard({
    super.key,
    this.height = 80,
    this.width = double.infinity,
    this.borderRadius = 10,
  });

  @override
  State<ShimmerCard> createState() => _ShimmerCardState();
}

class _ShimmerCardState extends State<ShimmerCard> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 1500))..repeat();
    _animation = Tween(begin: -1.0, end: 2.0).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOutSine));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, _) {
        return Container(
          height: widget.height,
          width: widget.width,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(widget.borderRadius),
            gradient: LinearGradient(
              colors: const [AppColors.panel, AppColors.surface, AppColors.panel],
              stops: [0.0, _animation.value.toDouble().clamp(0.0, 1.0), 1.0],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
        );
      },
    );
  }
}

/// ─── Shimmer List ───────────────────────────────────────────────────────
class ShimmerList extends StatelessWidget {
  final int itemCount;
  final double itemHeight;

  const ShimmerList({super.key, this.itemCount = 5, this.itemHeight = 72});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: List.generate(
        itemCount,
        (i) => Padding(
          padding: EdgeInsets.only(top: i == 0 ? 0 : 8, left: 16, right: 16),
          child: ShimmerCard(height: itemHeight),
        ),
      ),
    );
  }
}

/// ─── Empty State ────────────────────────────────────────────────────────
class EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final String? actionLabel;
  final VoidCallback? onAction;

  const EmptyState({
    super.key,
    this.icon = Icons.inbox_rounded,
    required this.title,
    this.subtitle = '',
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 48, color: AppColors.textMuted),
            const SizedBox(height: 16),
            Text(title, textAlign: TextAlign.center, style: const TextStyle(
              color: AppColors.textPrimary, fontSize: 17, fontWeight: FontWeight.w500,
            )),
            if (subtitle.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(subtitle, textAlign: TextAlign.center, style: const TextStyle(
                color: AppColors.textTertiary, fontSize: 13,
              )),
            ],
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: onAction,
                icon: const Icon(Icons.refresh_rounded, size: 16),
                label: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// ─── Error View ─────────────────────────────────────────────────────────
class ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback? onRetry;

  const ErrorView({super.key, required this.message, this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline_rounded, size: 48, color: AppColors.red),
            const SizedBox(height: 16),
            Text(message, textAlign: TextAlign.center, style: const TextStyle(
              color: AppColors.textSecondary, fontSize: 14,
            )),
            if (onRetry != null) ...[
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh_rounded, size: 16),
                label: const Text('Try Again'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// ─── Stock Tile ─────────────────────────────────────────────────────────
/// Reusable row used in Dashboard, Portfolio, Scanner, and Alerts screens.
class StockTile extends StatelessWidget {
  final String ticker;
  final String? name;
  final double price;
  final double? change;
  final double? changePct;
  final double? score;
  final Widget? trailing;
  final VoidCallback? onTap;

  const StockTile({
    super.key,
    required this.ticker,
    this.name,
    required this.price,
    this.change,
    this.changePct,
    this.score,
    this.trailing,
    this.onTap,
  });

  String _displayTicker(String t) => t.endsWith('.NS') ? t.substring(0, t.length - 3) : t;

  @override
  Widget build(BuildContext context) {
    final hasChange = change != null;
    final color = hasChange ? (change! >= 0 ? AppColors.green : AppColors.red) : AppColors.textPrimary;

    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            // Ticker info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(_displayTicker(ticker), style: const TextStyle(
                    color: AppColors.textPrimary, fontSize: 15, fontWeight: FontWeight.w500,
                  )),
                  if (name != null && name!.isNotEmpty) const SizedBox(height: 2),
                  if (name != null && name!.isNotEmpty) Text(name!, style: const TextStyle(
                    color: AppColors.textTertiary, fontSize: 12,
                  )),
                ],
              ),
            ),
            // Score badge (if provided)
            if (score != null) ...[
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: score! >= 70 ? AppColors.green.withOpacity(0.15) : score! >= 50 ? AppColors.yellow.withOpacity(0.15) : Colors.transparent,
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: AppColors.border),
                ),
                child: Text('${score!.toInt()}', style: TextStyle(
                  color: score! >= 70 ? AppColors.greenBright : score! >= 50 ? AppColors.yellow : AppColors.textMuted,
                  fontSize: 12, fontWeight: FontWeight.w600,
                )),
              ),
              const SizedBox(width: 12),
            ],
            // Price + change
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text('₹${price.toStringAsFixed(2)}', style: TextStyle(
                  color: AppColors.textPrimary, fontSize: 15, fontWeight: FontWeight.w500,
                )),
                if (hasChange) ...[
                  const SizedBox(height: 2),
                  Text(
                    '${change! >= 0 ? '+' : ''}${change!.toStringAsFixed(2)} (${changePct?.toStringAsFixed(2) ?? '0.00'}%)',
                    style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w500),
                  ),
                ],
              ],
            ),
            if (trailing != null) ...[
              const SizedBox(width: 8),
              trailing!,
            ],
          ],
        ),
      ),
    );
  }
}
