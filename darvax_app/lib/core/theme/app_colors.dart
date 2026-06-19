import 'package:flutter/material.dart';

/// ─── Linear-Inspired Dark Theme Palette ─────────────────────────────────
/// Canonical source of all colors in the DarvaX design system.
/// Use ONLY these colors — never hardcode values in widgets.
///
class AppColors {
  AppColors._();

  // ── Background Surfaces ──────────────────────────────────────────────
  /// Deepest canvas — main app background
  static const Color bg = Color(0xFF08090A);
  /// Elevated panels, cards, sheets
  static const Color surface = Color(0xFF0F1011);
  /// Level 3 surface — dropdowns, popovers
  static const Color panel = Color(0xFF191A1B);
  /// Hover / subtle elevation
  static const Color elevated = Color(0xFF28282C);

  // ── Text ──────────────────────────────────────────────────────────────
  /// Near-white primary text (not pure white — prevents eye strain)
  static const Color textPrimary = Color(0xFFF7F8F8);
  /// Body text, secondary content
  static const Color textSecondary = Color(0xFFD0D6E0);
  /// Placeholders, metadata, muted content
  static const Color textTertiary = Color(0xFF8A8F98);
  /// Timestamps, disabled states, subtle labels
  static const Color textMuted = Color(0xFF62666D);

  // ── Brand & Accent ────────────────────────────────────────────────────
  /// DarvaX signature purple (brand accent)
  static const Color accent = Color(0xFF7132F5);
  /// Brighter variant for interactive elements
  static const Color accentBright = Color(0xFF7170FF);
  /// Hover state for accent elements
  static const Color accentHover = Color(0xFF828FFF);
  /// Subtle accent background (16% opacity)
  static Color get accentSubtle => accent.withOpacity(0.16);

  // ── Semantic ──────────────────────────────────────────────────────────
  /// Positive / gain
  static const Color green = Color(0xFF27A644);
  /// Positive bright
  static const Color greenBright = Color(0xFF10B981);
  /// Negative / loss
  static const Color red = Color(0xFFE54545);
  /// Negative bright
  static const Color redBright = Color(0xFFEF4444);
  /// Warning / yellow
  static const Color yellow = Color(0xFFF59E0B);
  /// Info / blue
  static const Color blue = Color(0xFF3B82F6);

  // ── Borders ──────────────────────────────────────────────────────────
  /// Standard semi-transparent border
  static const Color border = Color(0xFF23252A);
  /// Lighter variant
  static const Color borderLight = Color(0xFF34343A);
  /// Subtle separator
  static Color get borderSubtle => const Color(0xFFFFFFFF).withOpacity(0.05);

  // ── Chart Colors ─────────────────────────────────────────────────────
  static const List<Color> chartPalette = [
    Color(0xFF7132F5),
    Color(0xFF3B82F6),
    Color(0xFF10B981),
    Color(0xFFF59E0B),
    Color(0xFFEF4444),
    Color(0xFF8B5CF6),
    Color(0xFF06B6D4),
    Color(0xFFEC4899),
  ];

  // ── Helpers ──────────────────────────────────────────────────────────
  static Color pnlColor(double pnl) => pnl >= 0 ? green : red;
  static Color pnlBright(double pnl) => pnl >= 0 ? greenBright : redBright;
}
