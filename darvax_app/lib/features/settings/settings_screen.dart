import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/shared_widgets.dart';

/// ─── Settings Screen ────────────────────────────────────────────────────
/// App info, data source config, about DarvaX.
///
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.only(top: 8, bottom: 40),
        children: [
          // ── Data Source ──
          const _SectionTitle('Data Source'),
          _SettingTile(
            icon: Icons.analytics_rounded,
            title: 'Yahoo Finance',
            subtitle: 'Live market data for NSE stocks',
            trailing: StatusBadge.green('Active'),
          ),
          const Divider(indent: 56, endIndent: 16),
          _SettingTile(
            icon: Icons.radar_rounded,
            title: 'DarvaX Scanner',
            subtitle: '9 pattern detection algorithms',
            trailing: StatusBadge.green('9/9'),
          ),
          const Divider(indent: 56, endIndent: 16),
          _SettingTile(
            icon: Icons.storage_rounded,
            title: 'Local Storage',
            subtitle: 'Portfolio & alerts saved on device',
            trailing: StatusBadge.neutral('Hive'),
          ),

          const SizedBox(height: 16),
          const _SectionTitle('Universe'),
          _SettingTile(
            icon: Icons.apartment_rounded,
            title: 'NIFTY 200',
            subtitle: '248 stocks scanned for patterns',
            trailing: StatusBadge.neutral('NS'),
          ),

          const SizedBox(height: 16),
          const _SectionTitle('About'),
          _SettingTile(
            icon: Icons.info_outline_rounded,
            title: 'DarvaX v2.0',
            subtitle: 'Standalone Flutter trading analysis app',
          ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;
  const _SectionTitle(this.title);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Text(title, style: const TextStyle(
        color: AppColors.accentBright,
        fontSize: 12,
        fontWeight: FontWeight.w600,
        letterSpacing: 0.5,
      )),
    );
  }
}

class _SettingTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Widget? trailing;

  const _SettingTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: AppColors.panel,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.border),
            ),
            child: Icon(icon, size: 18, color: AppColors.accent),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(
                  color: AppColors.textPrimary, fontSize: 15, fontWeight: FontWeight.w500,
                )),
                const SizedBox(height: 2),
                Text(subtitle, style: const TextStyle(
                  color: AppColors.textTertiary, fontSize: 12,
                )),
              ],
            ),
          ),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}
