import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from database import save_earnings, get_earnings_history

def get_earnings_dates(ticker):
    """Pull historical earnings dates for a ticker."""
    stock = yf.Ticker(ticker)
    
    try:
        earnings = stock.earnings_dates
        if earnings is None or earnings.empty:
            print(f"No earnings data found for {ticker}")
            return None
        return earnings
    except Exception as e:
        print(f"Error fetching earnings dates for {ticker}: {e}")
        return None


def calculate_post_earnings_move(ticker, earnings_date):
    """
    Calculate the actual price move after earnings.
    Compares closing price day before earnings to closing price day after.
    """
    stock = yf.Ticker(ticker)
    
    # Get a window of price data around earnings
    start = (earnings_date - timedelta(days=5)).strftime("%Y-%m-%d")
    end = (earnings_date + timedelta(days=5)).strftime("%Y-%m-%d")
    
    hist = stock.history(start=start, end=end)
    
    if hist.empty or len(hist) < 2:
        return None
    
    hist.index = hist.index.tz_localize(None) if hist.index.tz else hist.index
    earnings_date_naive = pd.Timestamp(earnings_date)
    
    # Find the closest trading days before and after earnings
    before = hist[hist.index <= earnings_date_naive]
    after = hist[hist.index > earnings_date_naive]
    
    if before.empty or after.empty:
        return None
    
    price_before = before.iloc[-1]["Close"]
    price_after = after.iloc[0]["Close"]
    
    move_pct = ((price_after - price_before) / price_before) * 100
    return round(move_pct, 2)


def analyze_ticker(ticker, lookback=8):
    """
    Full analysis of a ticker's earnings history.
    Pulls last `lookback` earnings, calculates moves, saves to database.
    """
    print(f"\nAnalyzing {ticker.upper()}...")
    
    stock = yf.Ticker(ticker)
    earnings = get_earnings_dates(ticker)
    
    if earnings is None:
        return None

    # Filter to past earnings only
    now = pd.Timestamp.now().tz_localize(None)
    
    if earnings.index.tz:
        earnings.index = earnings.index.tz_localize(None)
    
    past_earnings = earnings[earnings.index < now].head(lookback)
    
    if past_earnings.empty:
        print(f"No past earnings found for {ticker}")
        return None

    results = []
    
    for date, row in past_earnings.iterrows():
        earnings_date = date.to_pydatetime().replace(tzinfo=None)
        
        # Get EPS data if available
        eps_estimate = row.get("EPS Estimate", None)
        eps_actual = row.get("Reported EPS", None)
        
        # Calculate price move
        move = calculate_post_earnings_move(ticker, earnings_date)
        
        if move is not None:
            # Save to database
            save_earnings(
                ticker=ticker,
                earnings_date=earnings_date.strftime("%Y-%m-%d"),
                actual_move_pct=move,
                eps_estimate=float(eps_estimate) if pd.notna(eps_estimate) else None,
                eps_actual=float(eps_actual) if pd.notna(eps_actual) else None
            )
            
            results.append({
                "date": earnings_date.strftime("%Y-%m-%d"),
                "move_pct": move,
                "eps_estimate": eps_estimate,
                "eps_actual": eps_actual
            })
            
            print(f"  {earnings_date.strftime('%Y-%m-%d')}: {move:+.2f}%")

    if not results:
        print(f"Could not calculate moves for {ticker}")
        return None

    # Summary statistics
    moves = [r["move_pct"] for r in results]
    summary = {
        "ticker": ticker.upper(),
        "earnings_analyzed": len(moves),
        "avg_move": round(sum(moves) / len(moves), 2),
        "avg_abs_move": round(sum(abs(m) for m in moves) / len(moves), 2),
        "max_move": round(max(moves, key=abs), 2),
        "min_move": round(min(moves, key=abs), 2),
        "positive_reactions": sum(1 for m in moves if m > 0),
        "negative_reactions": sum(1 for m in moves if m < 0),
        "results": results
    }

    print(f"\n  Summary for {ticker.upper()}:")
    print(f"  Earnings analyzed: {summary['earnings_analyzed']}")
    print(f"  Average move: {summary['avg_move']:+.2f}%")
    print(f"  Average absolute move: {summary['avg_abs_move']:.2f}%")
    print(f"  Largest move: {summary['max_move']:+.2f}%")
    print(f"  Smallest move: {summary['min_move']:+.2f}%")
    print(f"  Positive reactions: {summary['positive_reactions']}")
    print(f"  Negative reactions: {summary['negative_reactions']}")

    return summary


if __name__ == "__main__":
    # Test with a couple of tickers
    analyze_ticker("AAPL")
    analyze_ticker("NVDA")