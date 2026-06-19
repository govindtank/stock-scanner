# DarvaX Agent — Flutter AI Trading Assistant

## Comprehensive Development Plan

---

## 🎯 Vision

A **Flutter-based Android app** that extends the web dashboard into a full-featured **AI-native mobile trading copilot**. It displays all portfolio data, runs a **User vs System paper trading arena** with teaching guidance, and has a **multi-provider AI assistant** (OpenRouter, Gemini, OpenCode Zen, OpenAI, Anthropic, Custom) for natural-language queries.

**"Your trading copilot that lives in your pocket."**

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flutter App (Android)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────────┐  │
│  │ Data Layer│  │Domain Lyr│  │       Presentation           │  │
│  │ (Repo)   │→│ (Models) │→│ (Riverpod + 5 Tab Pages)      │  │
│  └────┬─────┘  └──────────┘  └──────────────────────────────┘  │
│       │                    ┌────────────────────┐    │          │
│       ▼                    │  AI Agent (LLM)     │    │          │
│  ┌──────────┐              │  • OpenAI-compatible │    │          │
│  │ Dio API   │              │  • Anthropic format  │    │          │
│  │ (Flask)  │              │  • Gemini format     │    │          │
│  └──────────┘              │  • OpenRouter        │    │          │
│       │                    │  • OpenCode Zen      │    │          │
│       │                    └────────────────────┘    │          │
│  ┌──────────┐                                        │          │
│  │ Hive DB  │  ← local cache + user paper trades     │          │
│  │ (offline)│    (arena trades, chat history)         │          │
│  └──────────┘                                         │          │
└──────────────────────────┬──────────────────────────────┘
                           │
                   ┌───────▼────────┐
                   │ Flask Backend   │
                   │ (localhost:8085)│
                   └────────────────┘
```

---

## 📱 Screen Map & Navigation (5 Bottom Tabs)

```
Tab 1: 📊 Dashboard     → KPI overview, market context
Tab 2: 💼 Portfolio     → Holdings, Mutual Funds, Bonds, Allocation
Tab 3: ⚔️ Arena         → User vs System Paper Trading + Teaching
Tab 4: 🤖 AI Assistant  → Chat, Context-aware trading advisor
Tab 5: ⚙️ Settings      → LLM config, server URL, theme
```

---

## 🧩 Data Models (Domain Layer)

```dart
// ── Real Portfolio ──
class RealHolding {
  String stock, stockName;
  double quantity, avgPrice, currentPrice, investedValue, currentValue;
  double unrealizedPnl, unrealizedPnlPct, dayChange, dayChangePct;
}

// ── Mutual Funds & Bonds ──
class MutualFund {
  String name, amc, category;   // large-cap, mid-cap, debt, etc.
  double invested, currentValue, returns, expenseRatio, nav;
  String riskLevel;              // low, moderate, high
}

class BondHolding {
  String name, issuer, rating;
  double faceValue, couponRate, currentPrice;
  DateTime maturityDate;
  double ytm;                    // yield to maturity
}

class FullPortfolio {
  double totalValue;
  double stocksValue, mfValue, bondsValue, cashValue;
  List<RealHolding> holdings;
  List<MutualFund> mutualFunds;
  List<BondHolding> bonds;
  double overallReturns, riskScore;
  String riskLevel;
}

// ── Arena: User vs System Paper Trading ──
enum TradeSide { user, system }
enum TradeAction { buy, sell }
enum TradeStatus { open, closed }
enum TradeDirection { long, short }

class ArenaTrade {
  String id, stock;
  TradeSide side;
  TradeAction action;
  TradeDirection direction;
  int quantity;
  double entryPrice, exitPrice;
  DateTime entryTime, exitTime;
  TradeStatus status;
  double pnl, pnlPercent;
  String strategyNotes;        // why this trade was made
}

class ArenaMatchup {
  double userPnl, systemPnl;
  double userWinRate, systemWinRate;
  int userWins, systemWins, userLosses, systemLosses;
  double bestTrade, worstTrade;
  List<ArenaTrade> trades;
  DateTime startedAt;
}

// ── DV Patterns ──
class DVPattern {
  String ticker;
  double price, dvScore, dailyVol, pctAboveSma20;
  double near52whPct, volTrend, rsi, drawdown;
  bool currentBreakout;
  String rsiTrend;
  String category; // bull, bear, accel
}

// ── Wishlist ──
class WishlistStock {
  String ticker, name;
  double price, rsi, dailyVolPct, volumeRatio;
  double drawdownPct, near52whPct, pctAboveSma20;
  String smaTrend, recommendation, conviction, reason;
  bool dataUnavailable;
  List<String> signals;
}

// ── AI Chat ──
class ChatMessage {
  String role;       // user, assistant, system
  String content;
  DateTime timestamp;
}

// Kebab-case provider keys for URL auto-fill
enum LLMProvider {
  openai,            // https://api.openai.com/v1
  anthropic,         // https://api.anthropic.com
  openrouter,        // https://openrouter.ai/api/v1
  gemini,            // https://generativelanguage.googleapis.com/v1beta
  opencodeZen,       // https://api.opencode.ai/v1  (user-provided)
  custom             // user provides full base URL
}

class LLMConfig {
  LLMProvider provider;
  String apiKey;         // stored in FlutterSecureStorage
  String baseUrl;        // auto-filled or custom
  String model;
  String apiFormat;      // openai-compatible / anthropic / gemini
}
```

---

## 🤖 LLM Provider Configuration

| Provider | Base URL | API Format | Default Model |
|----------|----------|------------|---------------|
| **OpenAI** | `https://api.openai.com/v1` | OpenAI-compat | `gpt-4o` |
| **Anthropic** | `https://api.anthropic.com/v1` | Anthropic Messages | `claude-sonnet-4-20250514` |
| **OpenRouter** | `https://openrouter.ai/api/v1` | OpenAI-compat | `openrouter/auto` |
| **Google Gemini** | `https://generativelanguage.googleapis.com/v1beta` | Google Generative | `gemini-2.0-flash` |
| **OpenCode Zen** | User-provided | OpenAI-compat | User-provided |
| **Custom** | User-provided | User-selectable | User-provided |

**Configuration Screen:**
- Provider dropdown → auto-fills base URL + format + model
- API key field (masked, stored in FlutterSecureStorage)
- Model override text field
- "Test Connection" button → sends a simple chat request to validate
- Base URL override for custom deployments

---

## ⚔️ Arena: User vs System Paper Trading

This is a **teaching tool** where:
- **System side**: Automatically pulls trades from Darvas bot + Options bot positions (read-only display from Flask)
- **User side**: User manually enters paper trades (buy/sell stocks with virtual ₹1L capital)
- **Leaderboard**: Side-by-side P&L comparison over time

### Arena Screens:

1. **Arena Dashboard**: Side-by-side KPI cards
   - User P&L vs System P&L
   - User Win Rate vs System Win Rate
   - Active trades count
   - "Who's winning?" indicator

2. **User Trade Entry**: Quick-add trade form
   - Stock ticker input
   - Buy/Sell toggle
   - Quantity + price
   - Optional: strategy notes (what the user learned)

3. **Trade History**: Scrollable list of all trades with P&L color-coding
  
4. **Teaching Section**: Cards that explain
   - "Why the system entered that trade" (from Darvas strategy logic)
   - "What to look for" (pattern recognition lessons)
   - "Mistake tracker" (flags common user errors: buying without volume confirmation, chasing runners)

### Teaching Tips (built-in):
- Based on the user's trades vs system logic
- "You bought CENTRUM without volume confirmation — wait for 1.5x+ volume on breakout"
- "System entered ATHERENERG with RSI 67 in sweet spot — strong trend alignment"
- "Consider trailing stop at ₹X for this position"

---

## 📊 Portfolio Analysis (Stocks + Mutual Funds + Bonds)

Beyond basic holdings, the Portfolio Analysis section shows:

### Allocation Pie Chart
- Stocks vs Mutual Funds vs Bonds vs Cash
- Color-coded with risk levels

### Per-Section Breakdown
- **Stocks**: Holdings table (existing)
- **Mutual Funds**: SIP/One-time, category breakdown, expense ratio analysis
- **Bonds**: Yield-to-maturity comparison, maturity ladder

### Risk Analysis
- Portfolio beta, concentration risk
- Diversification score
- "Your portfolio is X% concentrated in top 3 stocks"
- Recommendations: "Consider adding mid-cap MF for diversification"

### Data Sources
- **Mutual Funds**: User enters manually or scraped from backend
- **Bonds**: User-entered or external API
- For MVP: Manual entry + Hive storage + ability to sync with backend

---

## 🎨 Design System (Linear-inspired Dark UI)

```dart
class AppColors {
  static const bg = Color(0xFF08090A);
  static const panel = Color(0xFF0F1011);
  static const surface = Color(0xFF191A1B);
  static const surfaceHover = Color(0xFF28282C);
  static const textPrimary = Color(0xFFF7F8F8);
  static const textSecondary = Color(0xFFD0D6E0);
  static const textTertiary = Color(0xFF8A8F98);
  static const textMuted = Color(0xFF62666D);
  static const accent = Color(0xFF7170FF);
  static const accentHover = Color(0xFF828FFF);
  static const brandBg = Color(0xFF5E6AD2);
  static const green = Color(0xFF10B981);
  static const red = Color(0xFFE94560);
  static const yellow = Color(0xFFFFC107);
  static const border = Color(0x14FFFFFF);
  static const borderLight = Color(0x0DFFFFFF);
}
```

Typography: Inter (headings/body) + JetBrains Mono (numbers/prices)

---

## 👷 Implementation Phases

### Phase 1: Foundation + Core Screens (3-4 days)
| Day | What |
|-----|------|
| 1 | Project scaffold, deps, theme, core widgets, navigation |
| 2 | Data models + API client + repositories |
| 3 | Dashboard + Portfolio screens with real data |
| 4 | Arena screen (basic: paper trading entry + system comparison) |

### Phase 2: AI + Settings + Polish (3-4 days)
| Day | What |
|-----|------|
| 5 | Settings screen (all LLM providers + server config) |
| 6 | AI chat screen with streaming + context injection |
| 7 | Portfolio analysis (MF, bonds sections + allocation chart) |
| 8 | Arena teaching tips + comparison leaderboard |

### Phase 3: Polish + APK (2 days)
| Day | What |
|-----|------|
| 9 | Animations, error handling, offline cache |
| 10 | APK build, real device test, fixes |

**Total: ~10 days to fully functional APK**

---

## 📦 Dependencies

```yaml
dependencies:
  flutter_riverpod: ^2.5.0
  go_router: ^14.0.0
  dio: ^5.4.0
  hive_flutter: ^1.1.0
  flutter_secure_storage: ^9.2.0
  fl_chart: ^0.68.0
  flutter_markdown: ^0.7.0
  shimmer: ^3.0.0
  intl: ^0.19.0
  share_plus: ^9.0.0
  flutter_launcher_icons: ^0.13.0
```

---

## 🚀 Backend Endpoints Used

| Flask Endpoint | App Screen | Notes |
|----------------|-----------|-------|
| `/api/portfolio/real` | Portfolio | Holdings data |
| `/api/portfolio/system` | Arena | System bot trades for comparison |
| `/api/patterns/recommended` | Dashboard | DV Bull/Bear/Accel |
| `/api/wishlist/scan` | Dashboard | Wishlist signals |
| `/api/scan` | Dashboard | Breakout scanner |
| `/api/ai/context` (new) | AI Chat | Compact portfolio context |

**New backend endpoints needed for Arena:**
- `POST /api/arena/trade` — Submit a user paper trade
- `GET /api/arena/leaderboard` — Get comparison stats
- `GET /api/arena/trades` — Get trade history

These can be Hive-local for MVP, then synced to backend later.

---

**✅ Plan updated. Proceeding to Phase 1 — project scaffold + build.**
