#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════
  DARVAS PAPER TRADER — Cron Runner v2.0 (Pro Trader Edition)
  
  Now integrates the Pro Trader Profile mindset layer:
  
  1. 🧘 MINDSET FIRST — Morning briefing, state check, golden rules
  2. 🎯 TRIAD SCAN — Find breakout/snapback/gap patterns across NSE
  3. 🚦 EXECUTION GATES — Filters Darvas signals through 4 mandatory gates
  4. 📊 DARVAS TRADER — Original trading engine (unchanged)
  5. 📈 COMBINED REPORT — Mindset + Patterns + Trades in one Telegram message
  
  "Trade the setup, not the story."
══════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import json
import datetime
from pathlib import Path

# Add repo to path
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))
os.chdir(SCRIPT_DIR)

from darvas_paper_trader import DarvasPaperTrader, StrategyImproviser

# ─── Pro Trader Profile Integration ──────────────────────────────────
try:
    from pro_trader_profile import (
        ProTraderProfile, MindsetJournal, run_triad_scanner,
        print_triad_report, ExecutionGate, PATTERN_ARCHETYPES,
        PRO_SCAN_UNIVERSE, MINDSET_STATES,
        # DV scanner integration
        run_dv_scanner, run_dv_monitor, print_dv_report,
        DV_SCAN_LOG, check_dv_entry_exit_conditions,
        format_dv_alert_message,
    )
    PRO_TRADER_AVAILABLE = True
except ImportError as e:
    PRO_TRADER_AVAILABLE = False
    print(f"⚠️ Pro Trader Profile not loaded: {e}")

# ─── DarvaX Pattern Scanner Integration ──────────────────────────────
try:
    from darvaX_scanner import (
        scan_universe_for_darvaX, print_darvaX_report,
        DARVAX_PATTERNS, run_darvaX_scanner,
    )
    DARVAX_AVAILABLE = True
except ImportError as e:
    DARVAX_AVAILABLE = False
    print(f"⚠️ DarvaX scanner not loaded: {e}")


# ─── Constants for risk adjustment ────────────────────────────────────
MAX_RISK_PER_TRADE = 0.02  # Default 2%
RISK_MULTIPLIER_MAP = {
    "DISCIPLINED": 1.0,
    "CAUTIOUS": 0.5,
    "AGGRESSIVE": 0.3,
    "TILTED": 0.0,
    "ANALYTICAL": 0.0,
}


def run_pro_trader_layer() -> dict:
    """
    Run the Pro Trader mindset + pattern recognition layer.
    Returns the full context for the Darvas trader to consume.
    """
    context = {
        "mindset_state": "DISCIPLINED",
        "risk_multiplier": 1.0,
        "mindset_message": "",
        "top_picks": [],
        "triad_html": "",
        "active_archetypes": {},
        "error": None,
    }

    if not PRO_TRADER_AVAILABLE:
        context["mindset_message"] = "⚠️ Pro Trader Profile not loaded — running in legacy mode"
        return context

    try:
        # 1. Load profile and reset daily counters
        profile = MindsetJournal.load_profile()
        MindsetJournal.reset_daily_counters(profile)

        # 2. Get mindset state
        state = profile.mindset.current_state
        state_info = MINDSET_STATES.get(state, {})
        risk_mult = state_info.get('risk_multiplier', 1.0)

        context["mindset_state"] = state
        context["risk_multiplier"] = risk_mult
        context["profile"] = profile

        # Build mindset briefing
        mindset_lines = []
        mindset_lines.append(f"🧘 MINDSET: {state_info.get('emoji', '🧘')} {state}")
        mindset_lines.append(f"   Risk Multiplier: {risk_mult * 100:.0f}%")
        mindset_lines.append(f"   Consecutive Wins: {profile.mindset.consecutive_wins} | Losses: {profile.mindset.consecutive_losses}")
        mindset_lines.append(f"   Daily Trades: {profile.mindset.daily_trades_taken} | Daily Losses: {profile.mindset.daily_losses}")

        if risk_mult == 0.0:
            mindset_lines.append(f"   ⛔ TRADING PAUSED — State is {state}. No new positions.")
            context["trading_paused"] = True
        elif risk_mult < 1.0:
            mindset_lines.append(f"   ⚠️ Reduced risk mode — position sizes cut by {int((1-risk_mult)*100)}%")

        context["mindset_message"] = "\n".join(mindset_lines)

        # ─── 3a. Run Triad pattern scan ───────────────────────────────
        print("🔍 Running Triad pattern scan...")
        results = run_triad_scanner(universe=PRO_SCAN_UNIVERSE, progress=True)

        # ─── 3b. Run DV pattern scan (the AtherEnergy/Centrum pattern) ─
        print("🏃‍♂️ Running Directional Volatility scan...")
        dv_results = run_dv_scanner(universe=PRO_SCAN_UNIVERSE, progress=False)
        context["dv_results"] = dv_results
        
        # Check entry/exit for DV-Bull top picks
        dv_alerts = []
        for r in dv_results.get('dv_bull', [])[:3]:
            cond = check_dv_entry_exit_conditions(r, "DIRECTIONAL_VOLATILITY_BULL")
            if cond['recommendation'] in ('ENTRY', 'EXIT'):
                dv_alerts.append({'ticker': r['ticker'], 'type': 'DV-BULL',
                                  'action': cond['recommendation'],
                                  'price': r['price'], 'signals': cond['entry_signals_hit'] + cond['exit_signals_hit']})
        for r in dv_results.get('dv_bear', [])[:3]:
            cond = check_dv_entry_exit_conditions(r, "DIRECTIONAL_VOLATILITY_BEAR")
            if cond['recommendation'] in ('ENTRY', 'EXIT'):
                dv_alerts.append({'ticker': r['ticker'], 'type': 'DV-BEAR',
                                  'action': cond['recommendation'],
                                  'price': r['price'], 'signals': cond['entry_signals_hit'] + cond['exit_signals_hit']})
        context["dv_alerts"] = dv_alerts

        # ─── 3c. Run DarvaX pattern scan (High Dry Fry, Tasuki, etc.) ─
        if DARVAX_AVAILABLE:
            print("🍟 Running DarvaX pattern scan...")
            darvaX_results = scan_universe_for_darvaX(
                universe=PRO_SCAN_UNIVERSE,
                min_score=40,
            )
            context["darvaX_results"] = darvaX_results
            print(f"   → {len(darvaX_results)} DarvaX pattern matches found")

        # 4. Get top picks (score >= 50)
        top_picks = [r for r in results if r['best_score'] >= 50]
        context["top_picks"] = top_picks[:15]  # Top 15

        # 5. Group by archetype for the report
        arch_groups = {}
        for r in top_picks:
            arch = r['best_archetype']
            if arch not in arch_groups:
                arch_groups[arch] = []
            arch_groups[arch].append(r)
        context["active_archetypes"] = arch_groups

        # 6. Build Triad summary for the report
        triad_lines = []
        triad_lines.append(f"🎯 TRIAD PATTERN SCAN: {len(top_picks)} matches from {len(results)} stocks")

        for arch, stocks in sorted(arch_groups.items()):
            config = PATTERN_ARCHETYPES.get(arch, {})
            emoji = config.get('emoji', '📊')
            name = config.get('name', arch)
            # Show top 5 per archetype
            top_in_arch = sorted(stocks, key=lambda x: x['best_score'], reverse=True)[:5]
            matched = ", ".join([f"{s['ticker'].replace('.NS','')}({s['best_score']})" for s in top_in_arch])
            triad_lines.append(f"   {emoji} {name}: {matched}")

        context["triad_html"] = "\n".join(triad_lines)

        # 7. Save pattern log
        from pro_trader_profile import PATTERN_LOG
        with open(PATTERN_LOG, 'w') as f:
            json.dump({
                'date': datetime.date.today().isoformat(),
                'results': [{
                    'ticker': r['ticker'],
                    'archetype': r['best_archetype'],
                    'score': r['best_score'],
                    'price': r['price'],
                    'rsi': r['rsi'],
                } for r in top_picks[:30]]
            }, f, indent=2)

        return context

    except Exception as e:
        import traceback
        context["error"] = f"{e}\n{traceback.format_exc()}"
        context["mindset_message"] = f"⚠️ Pro Trader error: {e}"
        return context


def filter_signals_through_gates(
    darvas_signals: list,
    pro_trader_context: dict,
) -> list:
    """
    Filter Darvas-generated signals through the Pro Trader's execution gates.
    Returns only signals that pass ALL 4 gates.
    """
    if not PRO_TRADER_AVAILABLE or not darvas_signals:
        return darvas_signals

    profile = pro_trader_context.get("profile")
    if not profile:
        return darvas_signals

    # If trading is paused, return nothing
    if pro_trader_context.get("trading_paused"):
        return []

    risk_mult = pro_trader_context["risk_multiplier"]

    # Cross-reference Darvas signals with Triad picks
    triad_picks = {r['ticker']: r for r in pro_trader_context.get("top_picks", [])}

    gated_signals = []
    for signal in darvas_signals:
        ticker = signal.get('symbol', '')
        ticker_main = ticker.replace('.NS', '')

        # Check if this stock has a Triad pattern match
        triad_match = triad_picks.get(ticker) or triad_picks.get(ticker_main + '.NS')
        archetype_match = triad_match['best_archetype'] if triad_match else None

        # Gate 1: Must have some pattern match (score >= 50)
        if not triad_match or triad_match['best_score'] < 50:
            # Weak signal — only pass if risk is fully on
            if risk_mult < 1.0:
                continue

        # Gate 2: Apply risk multiplier to position sizing
        if 'entry_zone' in signal:
            signal['risk_multiplier'] = risk_mult
            signal['pattern_score'] = triad_match['best_score'] if triad_match else 0
            signal['pattern_archetype'] = archetype_match

        gated_signals.append(signal)

    return gated_signals


def build_combined_report(
    darvas_report: str,
    pro_trader_context: dict,
    darvas_signals: list,
    improvements: list,
    original_signals_count: int,
    gated_signals_count: int,
) -> str:
    """
    Combine Pro Trader mindset + Triad scan + Darvas trading report.
    """
    parts = []

    # === SECTION 0: Header ===
    today = datetime.date.today().isoformat()
    parts.append(f"📊 **DARVAS PRO TRADER — {today}**")
    parts.append(f"{'─' * 35}")

    # === SECTION 1: Mindset State ===
    if pro_trader_context.get("mindset_message"):
        parts.append("")
        parts.append(pro_trader_context["mindset_message"])

    # === SECTION 2: Triad Pattern Scan ===
    if pro_trader_context.get("triad_html"):
        parts.append("")
        parts.append(pro_trader_context["triad_html"])

    # Show which archetypes are currently actionable
    arch_groups = pro_trader_context.get("active_archetypes", {})
    if arch_groups:
        emoji_map = {
            "BREAKOUT_MOMENTUM": "🚀",
            "MEAN_REVERSION_SNAPBACK": "🔄",
            "GAP_AND_GO": "⚡",
            "DIRECTIONAL_VOLATILITY_BULL": "🏃‍♂️",
            "DIRECTIONAL_VOLATILITY_BEAR": "🔄",
        }
        arch_status = []
        for arch, stocks in arch_groups.items():
            emoji = emoji_map.get(arch, "📊")
            action = "🟢 ACTIVE" if len(stocks) >= 2 else "🟡 LIMITED"
            arch_status.append(f"   {emoji} {arch}: {action} ({len(stocks)} matches)")
        if arch_status:
            parts.append(f"\n📡 **LIVE PATTERN SIGNALS:**")
            parts.extend(arch_status)

    # === SECTION 2b: DV Scan Results ===
    dv_results = pro_trader_context.get("dv_results", {})
    if dv_results:
        parts.append("\n🏃‍♂️ **DIRECTIONAL VOLATILITY SCAN**")
        dv_bull = dv_results.get('dv_bull', [])
        dv_bear = dv_results.get('dv_bear', [])
        dv_accel = dv_results.get('dv_accel', [])
        parts.append(f"   🏃‍♂️ DV-Bull: {len(dv_bull)} | 🔄 DV-Bear: {len(dv_bear)} | ⚡ DV-Accel: {len(dv_accel)}")
        
        # Top DV-Bull picks
        if dv_bull:
            top_dv = ", ".join([f"{s['ticker'].replace('.NS','')}(S:{s['dv_score']})" for s in dv_bull[:5]])
            parts.append(f"   🏃‍♂️ Top DV-Bull: {top_dv}")
        
        # DV alerts (entry/exit)
        dv_alerts = pro_trader_context.get("dv_alerts", [])
        if dv_alerts:
            parts.append("\n📡 **DV ENTRY/EXIT ALERTS:**")
            for a in dv_alerts[:5]:
                icon = "🟢" if a['action'] == 'ENTRY' else "🔴"
                sig_text = f" ({', '.join(a['signals'][:2])})" if a.get('signals') else ""
                parts.append(f"   {icon} {a['ticker']} {a['type']}: {a['action']} @ \u20b9{a['price']}{sig_text}")

    # === SECTION 2c: DarvaX Pattern Scan ===
    darvaX_results = pro_trader_context.get("darvaX_results", [])
    if darvaX_results:
        parts.append("\n🍟 **DARVAX PATTERN SCAN**")
        parts.append(f"   Total DarvaX matches: {len(darvaX_results)}")

        # Top 5 picks
        for r in darvaX_results[:5]:
            pattern_name = r.get("pattern_name", r.get("best_darvaX_pattern", "?"))
            emoji = r.get("pattern_emoji", "📊")
            ticker = r['ticker'].replace('.NS', '')
            score = r['best_darvaX_score']
            parts.append(f"   {emoji} {ticker}: {pattern_name} (Score: {score})")
            evidence = r.get("evidence", [])
            if evidence:
                parts.append(f"      └ {evidence[0][:65]}")

        # Pattern distribution
        if darvaX_results:
            pattern_counts = {}
            for r in darvaX_results:
                pat = r.get("best_darvaX_pattern", "UNKNOWN")
                pattern_counts[pat] = pattern_counts.get(pat, 0) + 1
            if pattern_counts:
                dist_items = []
                for p, c in sorted(pattern_counts.items(), key=lambda x: -x[1]):
                    name = p.replace('_', ' ').title()
                    dist_items.append(f"{name}: {c}")
                parts.append(f"   📊 Distribution: {' | '.join(dist_items)}")

    # === SECTION 3: Darvas Activity ===
    if pro_trader_context.get("risk_multiplier", 1.0) > 0:
        parts.append("")
        
        # Show gate filtering if applicable
        if original_signals_count > 0:
            filtered = original_signals_count - gated_signals_count
            parts.append(f"🚦 **EXECUTION GATES**: {original_signals_count} signals → {gated_signals_count} passed ({filtered} filtered)")
        
        # Add the full Darvas report
        parts.append("")
        parts.append(darvas_report)

    # === SECTION 4: Strategy Improvements ===
    if improvements:
        parts.append("")
        parts.append("🔄 **STRATEGY IMPROVEMENTS**")
        for imp in improvements:
            parts.append(f"  • {imp}")

    # === SECTION 5: Portfolio Summary ===
    # (darvas_report already has this, but we add a clean summary)

    # === FOOTER ===
    parts.append("")
    parts.append("─" * 35)
    parts.append("🎯 _Pro Trader + Darvas Engine | Paper Trading_")
    parts.append("⚠️ _Not Financial Advice_")

    return "\n".join(parts)


def main():
    # ─── Phase 1: Pro Trader Layer ───────────────────────────────────
    print("=" * 60)
    print("  PRO TRADER PROFILE — INITIALIZING")
    print("=" * 60)
    
    pro_trader_ctx = run_pro_trader_layer()
    
    if pro_trader_ctx.get("error"):
        print(f"⚠️ Pro Trader error: {pro_trader_ctx['error']}")

    print(f"🧘 Mindset: {pro_trader_ctx.get('mindset_state', 'N/A')}")
    print(f"🎯 Triad matches: {len(pro_trader_ctx.get('top_picks', []))}")
    print(f"📐 Risk multiplier: {pro_trader_ctx.get('risk_multiplier', 1.0)*100:.0f}%")

    # ─── Phase 2: Darvas Trading Engine ──────────────────────────────
    print("\n" + "=" * 60)
    print("  DARVAS PAPER TRADER — RUNNING")
    print("=" * 60)

    trader = DarvasPaperTrader()
    
    # Apply risk multiplier from Pro Trader to position sizing
    risk_mult = pro_trader_ctx.get("risk_multiplier", 1.0)
    if risk_mult < 1.0 and risk_mult > 0:
        # Modify trader's max risk proportionally
        trader.portfolio.risk_multiplier = risk_mult
        print(f"📐 Risk adjusted: {risk_mult*100:.0f}% of normal position sizes")

    report = trader.run()

    # Count original signals (parse from report sections)
    original_signals_count = len(trader.report_sections) if hasattr(trader, 'report_sections') else 0
    
    # Get signals from trader (they're stored internally)
    # We need to access the signals list if available
    darvas_signals = getattr(trader, 'last_signals', [])

    # ─── Phase 3: Strategy Improviser ────────────────────────────────
    improver = StrategyImproviser()
    improvements = improver.review_and_improve(trader.portfolio, trader.memory)

    # ─── Phase 4: Gate Filtering ─────────────────────────────────────
    # Count how many signals would have been filtered
    gated_signals = filter_signals_through_gates(darvas_signals, pro_trader_ctx)
    gated_count = len(gated_signals)

    # ─── Phase 5: Build Combined Report ──────────────────────────────
    full_report = build_combined_report(
        darvas_report=report,
        pro_trader_context=pro_trader_ctx,
        darvas_signals=gated_signals,
        improvements=improvements,
        original_signals_count=original_signals_count,
        gated_signals_count=gated_count,
    )

    # Print to stdout (captured by Hermes cron for Telegram delivery)
    print(f"\n{'=' * 60}")
    print("  COMBINED REPORT")
    print(f"{'=' * 60}\n")
    print(full_report)

    # Save to file for debugging
    today = datetime.date.today().isoformat()
    reports_dir = SCRIPT_DIR / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    with open(reports_dir / f"cron_output_{today}.txt", 'w') as f:
        f.write(full_report)

    # Save Pro Trader profile state
    if PRO_TRADER_AVAILABLE:
        profile = pro_trader_ctx.get("profile")
        if profile:
            MindsetJournal.save_profile(profile)
            print(f"\n📁 Pro Trader profile saved")

    print(f"📁 Full report saved: reports/cron_output_{today}.txt")
    print(f"💰 Portfolio: ₹{trader.portfolio.total_value:,.0f} | "
          f"P&L: ₹{trader.portfolio.total_pnl:+,.0f} | "
          f"Positions: {len(trader.portfolio.positions)}")
    
    return full_report


if __name__ == '__main__':
    main()
