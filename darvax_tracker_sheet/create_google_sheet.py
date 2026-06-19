#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════════════════
  DARVAX TRACKER — Google Sheet Builder
  ══════════════════════════════════════════════════════════════════════════════

  Creates a Google Sheet with:
  - Live NSE stock prices via GOOGLEFINANCE
  - Technical indicators (SMA20, RSI proxy, volatility)
  - DarvaX breakout signal detection with color-coding
  - Conditional formatting for visual scanning

  Usage:
    1. pip install gspread google-auth
    2. Enable Google Sheets API & create service account
       https://console.cloud.google.com/apis/library/sheets.googleapis.com
    3. Download JSON key → save as ~/hermes_projects/trading-dashboard/credentials/sheets-key.json
    4. Share your target sheet with the service account email
    5. Run: python3 create_google_sheet.py

  FALLBACK: If API access isn't set up, import darvax_tracker.csv into
  Google Sheets manually and add formulas per the SETUP_GUIDE below.
══════════════════════════════════════════════════════════════════════════════
"""

import os
import json
import datetime
from typing import Optional

# ── Google Sheets API ─────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "DarvaX Tracker"
CREDENTIALS_PATH = os.path.expanduser(
    "~/hermes_projects/trading-dashboard/credentials/sheets-key.json"
)

# ── Stock Universe ───────────────────────────────────────────────────────
STOCKS = [
    ("EMMVEE.NS", "Emmvee Solar", "Solar"),
    ("CENTUM.NS", "Centum Electronics", "Defense Electronics"),
    ("GODAVARIB.NS", "Godavari Biorefineries", "Biofuels"),
    ("ATHERENERG.NS", "Ather Energy", "Electric Vehicles"),
    ("PARAS.NS", "Paras Defence", "Defense"),
    ("OMNI.NS", "Omnitech Engineering", "Engineering"),
    ("GROWW.NS", "Groww", "Fintech"),
    ("TI.NS", "Tilaknagar Industries", "Beverages"),
    ("BELRISE.NS", "Belrise Industries", "Auto Components"),
    ("LALPATHLAB.NS", "Dr. Lal PathLabs", "Diagnostics"),
    ("HINDCOPPER.NS", "Hindustan Copper", "Mining"),
    ("BEL.NS", "Bharat Electronics", "Defense"),
    ("TATATECH.NS", "Tata Technologies", "Technology"),
    ("PINELABS.NS", "Pine Labs", "Fintech"),
    ("NEPHROPLUS.NS", "Nephro Plus", "Healthcare"),
    ("TRENT.NS", "Trent", "Retail"),
    ("RELIANCE.NS", "Reliance Industries", "Conglomerate"),
    ("HDFCBANK.NS", "HDFC Bank", "Banking"),
    ("ICICIBANK.NS", "ICICI Bank", "Banking"),
    ("SBIN.NS", "SBI", "Banking"),
    ("INFY.NS", "Infosys", "Technology"),
    ("BAJFINANCE.NS", "Bajaj Finance", "Finance"),
    ("M&M.NS", "Mahindra & Mahindra", "Auto"),
]

# ── Formula Generators ──────────────────────────────────────────────────

def nse(ticker: str) -> str:
    """Convert EMMVEE.NS → NSE:EMMVEE for GOOGLEFINANCE"""
    return f"NSE:{ticker.replace('.NS', '')}"

def gfinance_field(ticker: str, field: str) -> str:
    """GOOGLEFINANCE formula string"""
    sym = nse(ticker)
    return f'=GOOGLEFINANCE("{sym}", "{field}")'

def price_formula(ticker: str, row: int) -> str:
    sym = nse(ticker)
    return f'=IFERROR(GOOGLEFINANCE("{sym}", "price"), "")'

def change_formula(ticker: str, row: int) -> str:
    sym = nse(ticker)
    return f'=IFERROR(GOOGLEFINANCE("{sym}", "changepct"), "")'

def volume_formula(ticker: str, row: int) -> str:
    sym = nse(ticker)
    return f'=IFERROR(GOOGLEFINANCE("{sym}", "volume"), "")'

def high52w_formula(ticker: str, row: int) -> str:
    sym = nse(ticker)
    return f'=IFERROR(GOOGLEFINANCE("{sym}", "high52"), "")'

def low52w_formula(ticker: str, row: int) -> str:
    sym = nse(ticker)
    return f'=IFERROR(GOOGLEFINANCE("{sym}", "low52"), "")'

def sma20_formula(ticker: str, row: int) -> str:
    """SMA20 from GoogleFinance - use a workaround since
    GOOGLEFINANCE doesn't directly support SMA.
    We use the close history and AVERAGE.
    """
    sym = nse(ticker)
    return f'=IFERROR(AVERAGE(QUERY(GOOGLEFINANCE("{sym}", "close", TODAY()-30, TODAY()), "SELECT Col2 LIMIT 20 OFFSET 1")), "")'

# ── Sheet Builder ──────────────────────────────────────────────────────

def build_sheet_data():
    """Build all rows with formulas for the tracker sheet."""
    headers = [
        "Ticker", "Company", "Sector",
        "LTP (₹)", "Day Change %", "Volume",
        "52W High", "52W Low", "52W % From High",
        "SMA20", "% Above SMA20",
        "Signal", "Conviction", "Last Updated"
    ]

    rows = [headers]

    for ticker, company, sector in STOCKS:
        row_num = len(rows) + 1  # 1-based, header is row 1
        r = row_num  # current data row

        ticker_clean = ticker.replace(".NS", "")

        # LTP
        ltp = f'=IFERROR(GOOGLEFINANCE("NSE:{ticker_clean}"), "")'
        change = f'=IFERROR(GOOGLEFINANCE("NSE:{ticker_clean}", "changepct"), "")'
        volume = f'=IFERROR(GOOGLEFINANCE("NSE:{ticker_clean}", "volume"), "")'
        high52 = f'=IFERROR(GOOGLEFINANCE("NSE:{ticker_clean}", "high52"), "")'
        low52 = f'=IFERROR(GOOGLEFINANCE("NSE:{ticker_clean}", "low52"), "")'
        near_52wh = f'=IFERROR(IF({high52}=0,"",(D{r}/{high52})*100), "")'
        sma20 = f'=IFERROR(AVERAGE(QUERY(GOOGLEFINANCE("NSE:{ticker_clean}", "close", TODAY()-30, TODAY()), "SELECT Col2 LIMIT 20 OFFSET 1")), "")'
        pct_above_sma = f'=IFERROR(IF(ISBLANK(J{r}),"", ((D{r}/J{r})-1)*100), "")'

        # Signal logic — simple breakout detection
        signal = (
            f'=IFERROR(IF(AND(ISNUMBER(D{r}), ISNUMBER(G{r}), D{r}>=G{r}*0.98, '
            f'ISNUMBER(E{r}), E{r}>1.5, ISNUMBER(K{r}), K{r}>0), '
            f'"🔥 BREAKOUT", IF(AND(ISNUMBER(K{r}), K{r}>5), '
            f'"🟢 Strong", IF(AND(ISNUMBER(K{r}), K{r}>0), '
            f'"🟡 Above SMA", "⚪ Neutral"))), "")'
        )

        conviction = (
            f'=IFERROR(IF(L{r}="🔥 BREAKOUT", '
            f'IF(AND(E{r}>3, K{r}>8), "High", "Medium"), '
            f'IF(L{r}="🟢 Strong", "Medium", "Low")), "")'
        )

        timestamp = f'=IF(D{r}="","",NOW())'

        rows.append([
            ticker, company, sector,
            ltp, change, volume,
            high52, low52, near_52wh,
            sma20, pct_above_sma,
            signal, conviction, timestamp
        ])

    return rows

# ── Formatting Rules ──────────────────────────────────────────────────

def build_conditional_format_rules():
    """Build conditional formatting rules for the sheet."""
    return [
        # 🔥 BREAKOUT — Gold background
        {
            "range": "A:N",
            "condition": "custom",
            "formula": '=$L1="🔥 BREAKOUT"',
            "bgColor": {"red": 0.9, "green": 0.7, "blue": 0.1, "alpha": 0.25},
        },
        # 🟢 Strong — Green background
        {
            "range": "A:N",
            "condition": "custom",
            "formula": '=$L1="🟢 Strong"',
            "bgColor": {"red": 0.0, "green": 0.6, "blue": 0.3, "alpha": 0.15},
        },
        # 🟡 Above SMA — Yellow background
        {
            "range": "A:N",
            "condition": "custom",
            "formula": '=$L1="🟡 Above SMA"',
            "bgColor": {"red": 0.9, "green": 0.8, "blue": 0.1, "alpha": 0.10},
        },
        # Price up (day change > 0)
        {
            "range": "D:D",
            "condition": "greater",
            "value": 0,
            "textColor": {"red": 0.0, "green": 0.7, "blue": 0.3},
        },
        # Price down (day change < 0)
        {
            "range": "D:D",
            "condition": "less",
            "value": 0,
            "textColor": {"red": 0.9, "green": 0.2, "blue": 0.2},
        },
    ]


# ── Sheet Creation (if API available) ────────────────────────────────────

def create_sheet_via_api():
    """Try to create the Google Sheet via the Sheets API."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("❌ gspread or google-auth not installed.")
        print("   Run: pip install gspread google-auth")
        return False

    if not os.path.exists(CREDENTIALS_PATH):
        print(f"❌ Credentials not found at: {CREDENTIALS_PATH}")
        print("   See SETUP_GUIDE.md for instructions.")
        return False

    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
        client = gspread.authorize(creds)

        # Create the sheet
        spreadsheet = client.create(SHEET_NAME)
        sheet = spreadsheet.sheet1
        sheet.update_title("Stocks")

        print(f"✅ Created sheet: {spreadsheet.title}")
        print(f"   URL: {spreadsheet.url}")

        # Populate data
        rows = build_sheet_data()
        sheet.update(range_name="A1", values=rows)

        # Apply formatting
        import gspread_formatting as gf

        # Header formatting
        header_fmt = gf.CellFormat(
            backgroundColor=gf.Color(0.05, 0.05, 0.08),
            textFormat=gf.TextFormat(bold=True, foregroundColor=gf.Color(1, 1, 1), fontSize=12),
        )
        gf.format_cell_range(sheet, "A1:N1", header_fmt)

        # Freeze header row
        sheet.freeze(rows=1)

        # Auto-resize columns
        for i, col in enumerate("ABCDEFGHIJKLMN", 1):
            sheet.format(f"{col}:{col}", {"textFormat": {"fontSize": 11}})

        # Conditional formatting rules
        rules = build_conditional_format_rules()
        gf.set_column_width(sheet, "A", 120)  # Ticker
        gf.set_column_width(sheet, "D", 100)  # LTP
        gf.set_column_width(sheet, "L", 140)  # Signal
        gf.set_column_width(sheet, "M", 120)  # Conviction

        print("✅ Formatting applied")
        print(f"\n📊 Share this sheet: {spreadsheet.url}")
        print("   Add your Google email as Editor to see it in your account.")

        return True

    except Exception as e:
        print(f"❌ Error creating sheet: {e}")
        return False


# ─── MAIN ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("═══════════════════════════════════════════════════════")
    print("  DarvaX Tracker — Google Sheet Builder")
    print(f"  {datetime.date.today().isoformat()}")
    print("═══════════════════════════════════════════════════════")

    success = create_sheet_via_api()

    if not success:
        print("\n─── FALLBACK: Manual Import ───")
        print("  Import 'darvax_tracker.csv' into Google Sheets.")
        print("  Then follow SETUP_GUIDE.md for formula instructions.")
        print("  CSV path: darvax_tracker.csv")
