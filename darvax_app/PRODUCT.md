# Product

## Register

product

## Users

Active individual traders and retail investors in Indian markets (NSE/BSE). Primary user is a confident, hands-on trader who runs their own portfolio, actively monitors DV (Directional Volatility) patterns, Darvas Box breakouts, and options strategies. They use this app as a companion to their trading desk — checking portfolio health, paper-trading against system bots, and getting AI-assisted analysis. The user is tech-literate, comfortable with data, and values precision over simplification.

## Product Purpose

DarvaX is an AI-powered trading copilot that helps individual investors analyze their portfolio, practice paper trading against automated system strategies, and get intelligent market insights. It exists to bridge the gap between having data and making informed trading decisions — by combining portfolio tracking, paper trading arena, multi-LLM assistant, and pattern detection in one unified dark-themed dashboard. Success means the user trades more confidently, learns from system bot comparisons, and has instant access to analytical insights.

## Brand Personality

**Sharp, Confident, Analytical.**

DarvaX is the precision instrument of trading tools — not a game, not a brokerage account statement. It speaks in data, benchmarks, and clear signals. The tone is authoritative but never arrogant; technical but never opaque. Think of it as a trading desk co-pilot that respects the user's intelligence and rewards attention to detail.

## Anti-references

- **Robinhood / Zerodha Kite** — Gamified, too playful, treats trading as casual entertainment. Avoid bright colors, confetti, "congratulations" popups, and broker-branded UI patterns.
- **SaaS fintech templating** — The generic "SaaS cream" dark theme: gradient text headings, glassmorphism cards, ghost-card borders+shadows, side-stripe accents on every card, the "hero metric" template (big number + small label + supporting stat). This is the saturated AI scaffold of 2026; DarvaX should feel purpose-built, not template-generated.
- **TradingView clutter** — Professional but overwhelming. Too many indicators, widgets, and panels competing for attention. DarvaX is focused — one screen, one purpose.
- **"AI-generated" tells** — No gradient text (`background-clip: text`), no repeating-linear-gradient stripe backgrounds, no sketchy SVG illustrations, no rounded-everything (32px+ border radius on cards), no tiny uppercase tracked eyebrow above every section.

## Design Principles

1. **Data first, chrome second** — Every pixel earns its place. Remove anything that doesn't carry information or aid navigation. Numbers and charts lead; decoration follows.
2. **Precision in every detail** — Spacing, typography, alignment, and color all signal trustworthiness. A P&L number that's misaligned or poorly contrasted erodes confidence in the trading data it represents.
3. **Calm authority** — The interface stays composed even when the market is volatile. Motion is purposeful and restrained (ease-out, no bounce). Alerts and errors are clear but not alarming.
4. **Consistent hierarchy** — Information density varies by screen, but the visual language (spacing scale, type ramp, color roles) remains consistent. The user always knows where to look and what something means.
5. **Learning through comparison** — The Arena (user vs system) is the core feedback loop. Every comparison — P&L side-by-side, win rates, trade history — should make the user's strengths and gaps immediately visible.

## Accessibility & Inclusion

- WCAG AA minimum (4.5:1 body text contrast, 3:1 large text)
- Semantic color coding: green for profit, red for loss, with icon or text labels as secondary signals for color vision deficiency
- Reduced motion support: all animations have `prefers-reduced-motion` alternative (crossfade or instant)
- Platform-native dark mode as default; no jarring color shifts
