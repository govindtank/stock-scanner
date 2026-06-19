# 📊 DarvaX Tracker — Google Sheet Setup Guide

## Option A: API Auto-Create (Recommended)

### Prerequisites
```bash
pip install gspread google-auth gspread-formatting
```

### Steps
1. Go to https://console.cloud.google.com/apis/library/sheets.googleapis.com
2. Enable the **Google Sheets API** for a project
3. Create a **Service Account** → Download JSON key
4. Rename the key → `~/hermes_projects/trading-dashboard/credentials/sheets-key.json`
5. Note the **service account email** (e.g., `darvax-tracker@xxx.iam.gserviceaccount.com`)
6. Run:
```bash
cd ~/workspace/stock-scanner-repo/darvax_tracker_sheet
python3 create_google_sheet.py
```
7. The script outputs a URL — open it
8. Click **Share → Add your personal Google email as Editor**
9. The sheet now lives in **your** Google Drive

---

## Option B: Manual Import (No API)

### Step 1: Create a new sheet
1. Go to [sheets.google.com](https://sheets.google.com) → **Blank spreadsheet**
2. Rename the sheet to **DarvaX Tracker**

### Step 2: Import the CSV
1. File → Import → Upload → `darvax_tracker.csv`
2. Import location: **Replace current sheet**
3. Separator: **Comma**

### Step 3: Add GOOGLEFINANCE Formulas

Set up the formula columns. Row 1 = headers. Data starts at row 2.

| Column | Header | Formula for Row 2 (drag down) |
|--------|--------|-------------------------------|
| A | Ticker | (imported from CSV) |
| B | Company | (imported from CSV) |
| C | Sector | (imported from CSV) |
| **D** | **LTP (₹)** | `=IFERROR(GOOGLEFINANCE("NSE:"&LEFT(A2,LEN(A2)-3)), "")` |
| **E** | **Day Change %** | `=IFERROR(GOOGLEFINANCE("NSE:"&LEFT(A2,LEN(A2)-3), "changepct"), "")` |
| **F** | **Volume** | `=IFERROR(GOOGLEFINANCE("NSE:"&LEFT(A2,LEN(A2)-3), "volume"), "")` |
| **G** | **52W High** | `=IFERROR(GOOGLEFINANCE("NSE:"&LEFT(A2,LEN(A2)-3), "high52"), "")` |
| **H** | **52W Low** | `=IFERROR(GOOGLEFINANCE("NSE:"&LEFT(A2,LEN(A2)-3), "low52"), "")` |
| **I** | **52W % From High** | `=IFERROR(IF(G2=0,"",(D2/G2)*100), "")` |
| **J** | **SMA20** | `=IFERROR(AVERAGE(QUERY(GOOGLEFINANCE("NSE:"&LEFT(A2,LEN(A2)-3), "close", TODAY()-30, TODAY()), "SELECT Col2 LIMIT 20 OFFSET 1")), "")` |
| **K** | **% Above SMA20** | `=IFERROR(IF(ISBLANK(J2),"",((D2/J2)-1)*100), "")` |
| **L** | **Signal** | `=IFERROR(IF(AND(ISNUMBER(D2),ISNUMBER(G2),D2>=G2*0.98,ISNUMBER(E2),E2>1.5,ISNUMBER(K2),K2>0),"🔥 BREAKOUT",IF(AND(ISNUMBER(K2),K2>5),"🟢 Strong",IF(AND(ISNUMBER(K2),K2>0),"🟡 Above SMA","⚪ Neutral"))), "")` |
| **M** | **Conviction** | `=IFERROR(IF(L2="🔥 BREAKOUT",IF(AND(E2>3,K2>8),"High","Medium"),IF(L2="🟢 Strong","Medium","Low")), "")` |
| **N** | **Last Updated** | `=IF(D2="","",NOW())` |

### Step 4: Conditional Formatting

Select the **entire data range** (A2:N) and add these rules:

| Rule | Format cells if... | Custom formula | Format style |
|------|-------------------|----------------|--------------|
| 🔥 Breakout | Custom formula is | `=$L1="🔥 BREAKOUT"` | Gold bg (#F2C94C) |
| 🟢 Strong | Custom formula is | `=$L1="🟢 Strong"` | Green bg (#27AE60, 15% opacity) |
| 🟡 Above SMA | Custom formula is | `=$L1="🟡 Above SMA"` | Yellow bg (#F2C94C, 10% opacity) |
| Green price | Greater than | 0 (apply to D column) | Green text |
| Red price | Less than | 0 (apply to D column) | Red text |

### Step 5: Lock It Down
- **Freeze Row 1**: View → Freeze → 1 row
- **Pin to top**: Drag the sheet tab to the leftmost position
- **Add a chart**: Select D column → Insert → Chart → Line chart for portfolio view

---

## Column Reference

| Signal | Meaning |
|--------|---------|
| 🔥 BREAKOUT | Price near 52W high + strong volume + above SMA20 |
| 🟢 Strong | Above SMA20 by >5% — in uptrend |
| 🟡 Above SMA | Modestly above SMA20 — watch for momentum |
| ⚪ Neutral | Below SMA20 or data unavailable |

Add new stocks at the bottom and drag formulas down.
