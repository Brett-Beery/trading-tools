# Earnings Analyzer — Time Spread Tool

A Python desktop application for analyzing historical post-earnings price 
behavior to identify time spread (calendar spread) candidates. Built for 
traders who want data-driven stock selection for earnings volatility strategies.

---

## The Problem This Solves

Time spreads around earnings profit from implied volatility crush — but only 
when the underlying stock stays within the market maker's expected move. 
Identifying which stocks historically behave this way requires pulling and 
analyzing years of earnings data manually.

This tool automates that research. Enter a ticker, get an instant visual 
breakdown of every post-earnings move over the last 4, 8, or 12 earnings 
cycles — with EPS beat/miss data, summary statistics, and everything saved 
to a local database that grows more valuable over time.

---

## Features

- **Live data** via Yahoo Finance API — no API key required
- **Interactive GUI** built with Tkinter and Matplotlib
- **Post-earnings move chart** with color-coded bars and value labels
- **Summary stat cards** — avg move, avg absolute move, largest, smallest
- **EPS history table** — estimate vs actual with beat/miss indicators
- **Persistent watchlist** — save tickers for quick access
- **Local SQLite database** — every analysis is saved, building a 
  proprietary historical dataset over time
- **Adjustable lookback** — analyze 4, 8, or 12 earnings cycles

---

## Strategy Context

This tool was built around the **time spread (calendar spread)** strategy 
taught by RDT/1OP. The goal is to identify stocks that consistently stay 
within market maker expectations post-earnings, making them strong candidates 
for volatility crush plays.

Ideal candidates show:
- Low average absolute move (< 4-5%)
- Consistent, predictable reactions
- No extreme outlier moves

---

## Tech Stack

- Python 3.x
- yfinance
- pandas
- tkinter
- matplotlib
- sqlite3 (built-in)

---

## Setup
```bash
# Clone the repository
git clone https://github.com/Brett-Beery/trading-tools.git
cd trading-tools

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install yfinance pandas matplotlib lxml
```

---

## Usage
```bash
python app.py
```

1. Enter a ticker symbol and hit GO or press Enter
2. Select how many earnings cycles to analyze (4, 8, or 12)
3. Review the chart, stat cards, and earnings history table
4. Add promising candidates to your watchlist for quick access
5. Double-click any watchlist ticker to instantly re-analyze

---

## Database

Every analysis automatically saves to a local SQLite database 
(`trading_data.db`). Over time this builds a proprietary dataset of 
earnings behavior across your watched tickers — more valuable the 
longer you use it.

---

## Roadmap

- Expected move overlay (IV-derived)
- Export analysis to PDF/Excel report
- Broker API integration for trade logging
- Multi-ticker comparison view
- Consistency scoring algorithm

---

## Author

Brett Beery — Python developer specializing in automation and data 
manipulation. Aspiring quantitative trader.
[GitHub](https://github.com/Brett-Beery) | 
[LinkedIn](https://www.linkedin.com/in/brett-beery/)