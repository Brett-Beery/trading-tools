import sqlite3
import os

DB_PATH = "trading_data.db"

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Earnings history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS earnings_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            earnings_date TEXT NOT NULL,
            expected_move_pct REAL,
            actual_move_pct REAL,
            beat_expected INTEGER,
            eps_estimate REAL,
            eps_actual REAL,
            beat_eps INTEGER,
            notes TEXT,
            date_logged TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, earnings_date)
        )
    ''')

    # Ticker watchlist table
    c.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE NOT NULL,
            date_added TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


def save_earnings(ticker, earnings_date, actual_move_pct, 
                  expected_move_pct=None, eps_estimate=None, 
                  eps_actual=None, notes=None):
    """Save or update an earnings record."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    beat_expected = None
    if expected_move_pct and actual_move_pct:
        beat_expected = 1 if abs(actual_move_pct) <= abs(expected_move_pct) else 0

    beat_eps = None
    if eps_estimate and eps_actual:
        beat_eps = 1 if eps_actual >= eps_estimate else 0

    c.execute('''
        INSERT OR REPLACE INTO earnings_history 
        (ticker, earnings_date, expected_move_pct, actual_move_pct, 
         beat_expected, eps_estimate, eps_actual, beat_eps, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (ticker.upper(), earnings_date, expected_move_pct, actual_move_pct,
          beat_expected, eps_estimate, eps_actual, beat_eps, notes))

    conn.commit()
    conn.close()


def get_earnings_history(ticker):
    """Retrieve all earnings records for a ticker."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT ticker, earnings_date, expected_move_pct, actual_move_pct,
               beat_expected, eps_estimate, eps_actual, beat_eps, notes
        FROM earnings_history
        WHERE ticker = ?
        ORDER BY earnings_date DESC
    ''', (ticker.upper(),))

    rows = c.fetchall()
    conn.close()
    return rows


def get_watchlist():
    """Retrieve all tickers on the watchlist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT ticker, date_added, notes FROM watchlist ORDER BY ticker')
    rows = c.fetchall()
    conn.close()
    return rows


def add_to_watchlist(ticker, notes=None):
    """Add a ticker to the watchlist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO watchlist (ticker, notes) VALUES (?, ?)',
                  (ticker.upper(), notes))
        conn.commit()
        print(f"{ticker.upper()} added to watchlist.")
    except sqlite3.IntegrityError:
        print(f"{ticker.upper()} is already on the watchlist.")
    conn.close()


def remove_from_watchlist(ticker):
    """Remove a ticker from the watchlist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM watchlist WHERE ticker = ?', (ticker.upper(),))
    conn.commit()
    conn.close()
    print(f"{ticker.upper()} removed from watchlist.")


if __name__ == "__main__":
    init_db()
    
    # Quick test
    add_to_watchlist("AAPL", "Classic time spread candidate")
    add_to_watchlist("NVDA")
    
    print("\nWatchlist:")
    for row in get_watchlist():
        print(f"  {row[0]} - Added: {row[1]} - Notes: {row[2]}")