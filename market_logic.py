from database import *
import matplotlib.pyplot as plt
import yfinance as yf
import requests
import pandas as pd
import logging
import time

logging.getLogger('yfinance').setLevel(logging.CRITICAL)

PRICE_CACHE = {}
CACHE_EXPIRY = 60  # seconds

def get_live_quote(symbol):
    current_time = time.time()
    
    # Check if we have a valid cached quote
    if symbol in PRICE_CACHE:
        cached_quote, timestamp = PRICE_CACHE[symbol]
        if current_time - timestamp < CACHE_EXPIRY:
            return cached_quote

    try:
        stock = yf.Ticker(symbol)
        # Use history instead of fast_info to avoid 'exchangeTimezoneName' and other API errors
        hist = stock.history(period="5d")
        if hist.empty:
            return None
        
        current_price = float(hist["Close"].iloc[-1])
        if len(hist) >= 2:
            prev_close = float(hist["Close"].iloc[-2])
        else:
            prev_close = current_price
            
        change_percent = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
        result = {"c": current_price, "dp": change_percent}
        
        # Save to cache
        PRICE_CACHE[symbol] = (result, current_time)
        return result
    except Exception as e:
        print(f"Error fetching quote for {symbol}: {e}")
        # If the API fails, fallback to the expired cache if available so prices don't suddenly turn to 0
        if symbol in PRICE_CACHE:
            return PRICE_CACHE[symbol][0]
        return None

def search_tickers(query):
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=6&newsCount=0"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        results = []
        for q in data.get("quotes", []):
            symbol = q.get("symbol")
            name = q.get("shortname", "")
            if symbol:
                results.append(f"{symbol} - {name}" if name else symbol)
        return results
    except Exception:
        return []

def calculate_portfolio_summary():
    holdings = get_all_holdings()
    total_investment = 0
    total_current_value = 0
    portfolio_rows = []

    for holding in holdings:
        holding_id, ticker, quantity, buy_price = holding
        investment_value = quantity * buy_price
        quote = get_live_quote(ticker)
        current_price = quote.get("c", 0) if quote else 0
        current_value = quantity * current_price
        profit_loss = current_value - investment_value
        
        total_investment += investment_value
        total_current_value += current_value
        portfolio_rows.append(
            (holding_id, ticker, quantity, buy_price, current_price, investment_value, current_value, profit_loss)
        )

    total_profit_loss = total_current_value - total_investment
    roi = (total_profit_loss / total_investment * 100) if total_investment else 0

    return {
        "investment": total_investment,
        "current_value": total_current_value,
        "profit_loss": total_profit_loss,
        "roi": roi,
        "rows": portfolio_rows,
    }

def get_top_holdings():
    holdings = get_all_holdings()
    results = []
    for row in holdings:
        ticker, quantity, buy_price = row[1], row[2], row[3]
        results.append((ticker, quantity * buy_price))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:3]

def get_allocation():
    holdings = get_all_holdings()
    total = sum(row[2] * row[3] for row in holdings)
    if total == 0: return []
    
    allocation = []
    for row in holdings:
        value = row[2] * row[3]
        percent = (value / total) * 100
        allocation.append((row[1], round(percent, 2)))
    return allocation

def get_diversification_suggestion():
    allocation = get_allocation()
    if not allocation: return "No holdings."
    biggest = max(allocation, key=lambda x: x[1])
    if biggest[1] > 50:
        return f"{biggest[0]} forms {biggest[1]}% of portfolio. Diversification recommended."
    return "Portfolio allocation appears balanced."

SECTOR_CACHE = {}

def get_sector_allocation():
    holdings = get_all_holdings()
    sectors = {}
    for row in holdings:
        ticker, quantity, buy_price = row[1], row[2], row[3]
        value = quantity * buy_price
        
        if ticker not in SECTOR_CACHE:
            try:
                profile = yf.Ticker(ticker).info
                sector = profile.get("industry", "Unknown")
            except Exception:
                sector = "Unknown"
            SECTOR_CACHE[ticker] = sector
            
        sector = SECTOR_CACHE[ticker]
        sectors[sector] = sectors.get(sector, 0) + value
        
    total = sum(sectors.values())
    if total == 0: return []
    return [(sector, round((val / total) * 100, 2)) for sector, val in sectors.items()]

def show_allocation_chart(allocation):
    if not allocation: return
    labels = [a[0] for a in allocation]
    sizes = [a[1] for a in allocation]
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%")
    plt.title("Portfolio Allocation")
    plt.show()

def show_sector_chart(sectors):
    if not sectors: return
    labels = [s[0] for s in sectors]
    sizes = [s[1] for s in sectors]
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%")
    plt.title("Sector Allocation")
    plt.show()

def show_historical_growth():
    holdings = get_all_holdings()
    if not holdings: 
        return
        
    portfolio_history = None
    
    for row in holdings:
        ticker, quantity = row[1], row[2]
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            if hist.empty: continue
            
            value_series = hist["Close"] * quantity
            if hasattr(value_series.index, 'tz_localize') and value_series.index.tz is not None:
                value_series.index = value_series.index.tz_localize(None)
            
            if portfolio_history is None:
                portfolio_history = value_series
            else:
                portfolio_history, value_series = portfolio_history.align(value_series, join='outer')
                # use standard fillna instead of ffill() directly for wider pandas compatibility
                if hasattr(portfolio_history, 'ffill'):
                    portfolio_history = portfolio_history.ffill().fillna(0)
                    value_series = value_series.ffill().fillna(0)
                else:
                    portfolio_history = portfolio_history.fillna(method='ffill').fillna(0)
                    value_series = value_series.fillna(method='ffill').fillna(0)
                portfolio_history = portfolio_history + value_series
        except Exception as e:
            print(f"Error fetching history for {ticker}: {e}")
            continue
            
    if portfolio_history is not None and not portfolio_history.empty:
        plt.figure(figsize=(10, 5))
        portfolio_history.plot(title="Historical Portfolio Growth (Last 3 Months)", color="blue", linewidth=2)
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value")
        plt.grid(True)
        plt.tight_layout()
        plt.show()