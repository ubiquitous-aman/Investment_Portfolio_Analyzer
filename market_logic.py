from database import *
import matplotlib.pyplot as plt
import yfinance as yf
import requests
import pandas as pd
import numpy as np
import logging
import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.getLogger('yfinance').setLevel(logging.CRITICAL)

PRICE_CACHE = {}
CACHE_EXPIRY = 60  # seconds

# Common sector mapping for instant, offline/zero-latency lookup of popular tickers
COMMON_SECTORS = {
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology", "GOOG": "Technology",
    "AMZN": "Consumer Cyclical", "TSLA": "Automotive", "META": "Communication",
    "NVDA": "Semiconductors", "NFLX": "Entertainment", "AMD": "Semiconductors",
    "INTC": "Semiconductors", "BABA": "Consumer Cyclical", "DIS": "Entertainment",
    "RELIANCE.NS": "Energy", "TCS.NS": "Technology", "INFY.NS": "Technology",
    "HDFCBANK.NS": "Financial Services", "ICICIBANK.NS": "Financial Services",
    "WIPRO.NS": "Technology", "TATAMOTORS.NS": "Automotive", "SBIN.NS": "Financial Services",
    "ITC.NS": "Consumer Defensive", "BHARTIARTL.NS": "Telecom", "LT.NS": "Engineering",
}

SECTOR_CACHE = {}
PROFILE_CACHE = {}


def get_live_quote(symbol):
    """
    Fetch the live price and percentage change for a symbol.
    Uses Yahoo Finance v8 direct chart JSON endpoint for near-instant (<200ms) responses,
    falling back to yfinance fast_info / history if needed.
    """
    symbol = symbol.strip().upper()
    current_time = time.time()

    # Check if we have a valid cached quote
    if symbol in PRICE_CACHE:
        cached_quote, timestamp = PRICE_CACHE[symbol]
        if current_time - timestamp < CACHE_EXPIRY:
            return cached_quote

    # 1. Fast path: Direct lightweight Yahoo chart endpoint
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
    try:
        r = requests.get(url, headers=headers, timeout=4)
        if r.status_code == 200:
            data = r.json()
            meta = data["chart"]["result"][0]["meta"]
            current_price = meta.get("regularMarketPrice")
            prev_close = meta.get("chartPreviousClose") or meta.get("previousClose") or current_price

            if current_price is not None:
                current_price = float(current_price)
                prev_close = float(prev_close) if prev_close else current_price
                change_percent = ((current_price - prev_close) / prev_close * 100) if prev_close else 0.0
                result = {"c": round(current_price, 2), "dp": round(change_percent, 2)}
                PRICE_CACHE[symbol] = (result, current_time)
                return result
    except Exception:
        pass

    # 2. Fallback path: yfinance
    try:
        stock = yf.Ticker(symbol)
        try:
            current_price = stock.fast_info.last_price
            prev_close = stock.fast_info.previous_close or current_price
            if current_price is not None:
                current_price = float(current_price)
                prev_close = float(prev_close) if prev_close else current_price
                change_percent = ((current_price - prev_close) / prev_close * 100) if prev_close else 0.0
                result = {"c": round(current_price, 2), "dp": round(change_percent, 2)}
                PRICE_CACHE[symbol] = (result, current_time)
                return result
        except Exception:
            pass

        hist = stock.history(period="5d")
        if not hist.empty and "Close" in hist.columns:
            close_prices = hist["Close"].dropna()
            if not close_prices.empty:
                current_price = float(close_prices.iloc[-1])
                prev_close = float(close_prices.iloc[-2]) if len(close_prices) >= 2 else current_price
                change_percent = ((current_price - prev_close) / prev_close * 100) if prev_close else 0.0
                result = {"c": round(current_price, 2), "dp": round(change_percent, 2)}
                PRICE_CACHE[symbol] = (result, current_time)
                return result
    except Exception as e:
        print(f"Error fetching quote for {symbol}: {e}")

    # 3. If all network fetches fail, return expired cache if present
    if symbol in PRICE_CACHE:
        return PRICE_CACHE[symbol][0]

    return None


def get_quotes_batch(symbols):
    """
    Fetch live quotes for multiple symbols concurrently using ThreadPoolExecutor.
    Fetches 5-10 symbols in ~0.3-0.5s total instead of several seconds.
    """
    unique_symbols = list(set(s.strip().upper() for s in symbols if s))
    if not unique_symbols:
        return {}

    quotes = {}
    to_fetch = []
    current_time = time.time()

    for sym in unique_symbols:
        if sym in PRICE_CACHE:
            cached_quote, ts = PRICE_CACHE[sym]
            if current_time - ts < CACHE_EXPIRY:
                quotes[sym] = cached_quote
                continue
        to_fetch.append(sym)

    if to_fetch:
        with ThreadPoolExecutor(max_workers=min(len(to_fetch), 8)) as executor:
            future_to_sym = {executor.submit(get_live_quote, sym): sym for sym in to_fetch}
            for future in as_completed(future_to_sym):
                sym = future_to_sym[future]
                try:
                    q = future.result()
                    if q:
                        quotes[sym] = q
                except Exception:
                    pass

    return quotes


def search_tickers(query):
    """Search for matching ticker symbols using Yahoo Finance search API."""
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


def get_company_profile(symbol):
    """Fetch company fundamentals: name, sector/industry, market cap, and currency."""
    symbol = symbol.strip().upper()
    if symbol in PROFILE_CACHE:
        return PROFILE_CACHE[symbol]

    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        name = info.get("shortName") or info.get("longName") or symbol
        industry = info.get("industry") or info.get("sector") or COMMON_SECTORS.get(symbol, "General")
        mcap = info.get("marketCap", 0)
        currency = info.get("currency", "USD")

        profile = {
            "symbol": symbol,
            "name": name,
            "industry": industry,
            "marketCap": mcap,
            "currency": currency,
        }
        PROFILE_CACHE[symbol] = profile
        return profile
    except Exception as e:
        print(f"Error fetching profile for {symbol}: {e}")
        return {
            "symbol": symbol,
            "name": symbol,
            "industry": COMMON_SECTORS.get(symbol, "General"),
            "marketCap": 0,
            "currency": "USD",
        }


def calculate_portfolio_summary():
    """
    Calculate full summary of holdings using parallel quote fetching.
    Returns investment total, current value, profit/loss, ROI, and individual row tuples.
    """
    holdings = get_all_holdings()
    total_investment = 0.0
    total_current_value = 0.0
    portfolio_rows = []

    # Batch fetch all quotes in parallel
    symbols = [h[1] for h in holdings]
    quotes = get_quotes_batch(symbols)

    for holding in holdings:
        holding_id, ticker, quantity, buy_price = holding
        ticker = ticker.upper()
        investment_value = quantity * buy_price

        quote = quotes.get(ticker)
        current_price = quote.get("c", buy_price) if quote else buy_price
        current_value = quantity * current_price
        profit_loss = current_value - investment_value

        total_investment += investment_value
        total_current_value += current_value
        portfolio_rows.append(
            (holding_id, ticker, quantity, buy_price, current_price, investment_value, current_value, profit_loss)
        )

    total_profit_loss = total_current_value - total_investment
    roi = (total_profit_loss / total_investment * 100) if total_investment else 0.0

    return {
        "investment": total_investment,
        "current_value": total_current_value,
        "profit_loss": total_profit_loss,
        "roi": roi,
        "rows": portfolio_rows,
    }


def get_top_holdings():
    """Get top 3 holdings by investment value, properly aggregating duplicate tickers."""
    holdings = get_all_holdings()
    ticker_values = {}
    for row in holdings:
        ticker, quantity, buy_price = row[1].upper(), row[2], row[3]
        ticker_values[ticker] = ticker_values.get(ticker, 0) + (quantity * buy_price)
    results = sorted(ticker_values.items(), key=lambda x: x[1], reverse=True)
    return results[:3]


def get_allocation():
    """Get portfolio percentage allocation by ticker, consolidating duplicate tickers."""
    holdings = get_all_holdings()
    if not holdings:
        return []

    ticker_values = {}
    for row in holdings:
        ticker, quantity, buy_price = row[1].upper(), row[2], row[3]
        ticker_values[ticker] = ticker_values.get(ticker, 0) + (quantity * buy_price)

    total = sum(ticker_values.values())
    if total == 0:
        return []

    return [(ticker, round((val / total) * 100, 2)) for ticker, val in ticker_values.items()]


def get_diversification_suggestion():
    """Return a plain-English diversification suggestion based on portfolio weights."""
    allocation = get_allocation()
    if not allocation:
        return "No holdings in portfolio."
    biggest = max(allocation, key=lambda x: x[1])
    if biggest[1] > 50:
        return f"{biggest[0]} forms {biggest[1]}% of your portfolio. Consider diversifying across other assets."
    return "Portfolio allocation appears balanced."


def get_sector_allocation():
    """
    Get sector allocation percentage.
    Uses common sector lookup and cached profiles to avoid blocking network calls.
    """
    holdings = get_all_holdings()
    if not holdings:
        return []

    sectors = {}
    for row in holdings:
        ticker, quantity, buy_price = row[1].upper(), row[2], row[3]
        value = quantity * buy_price

        if ticker in COMMON_SECTORS:
            sector = COMMON_SECTORS[ticker]
        elif ticker in SECTOR_CACHE:
            sector = SECTOR_CACHE[ticker]
        else:
            try:
                info = yf.Ticker(ticker).info
                sector = info.get("sector") or info.get("industry") or "General"
            except Exception:
                sector = "General"
            SECTOR_CACHE[ticker] = sector

        sectors[sector] = sectors.get(sector, 0) + value

    total = sum(sectors.values())
    if total == 0:
        return []
    return [(sector, round((val / total) * 100, 2)) for sector, val in sectors.items()]


def get_risk_metrics():
    """
    Calculate annualized volatility and max drawdown for all holdings.
    Returns a list of dicts with ticker, volatility %, and drawdown %.
    """
    holdings = get_all_holdings()
    if not holdings:
        return []

    unique_tickers = list(set(h[1].upper() for h in holdings))
    results = []

    def fetch_risk(ticker):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            if hist.empty or "Close" not in hist.columns:
                return None
            closes = hist["Close"].dropna()
            if len(closes) < 10:
                return None

            returns = closes.pct_change().dropna()
            volatility = round(float(returns.std() * np.sqrt(252) * 100), 2)

            cummax = closes.cummax()
            drawdown = (closes - cummax) / cummax
            max_drawdown = round(float(drawdown.min() * 100), 2)

            return {
                "ticker": ticker,
                "volatility": volatility,
                "drawdown": max_drawdown,
            }
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=min(len(unique_tickers), 6)) as executor:
        for res in executor.map(fetch_risk, unique_tickers):
            if res:
                results.append(res)

    return results


def export_portfolio_to_csv(filepath):
    """Export current portfolio summary and holdings to a CSV file."""
    summary = calculate_portfolio_summary()
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Ticker", "Quantity", "Buy Price", "Current Price", "Investment", "Current Value", "Profit/Loss"])
        for row in summary["rows"]:
            writer.writerow(row)


def import_portfolio_from_csv(filepath):
    """
    Import stock holdings from a CSV file.
    Supports exported CSV format or simple Ticker, Quantity, Buy Price columns.
    Returns the number of successfully imported rows.
    """
    imported_count = 0
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return 0

        header_lower = [h.strip().lower() for h in header]
        ticker_idx, qty_idx, price_idx = None, None, None

        for idx, col in enumerate(header_lower):
            if "ticker" in col or "symbol" in col:
                ticker_idx = idx
            elif "quant" in col or "qty" in col or "shares" in col:
                qty_idx = idx
            elif "buy" in col or "price" in col or "cost" in col:
                if price_idx is None:
                    price_idx = idx

        # Check if first row was actually raw data without headers
        if ticker_idx is None or qty_idx is None or price_idx is None:
            if len(header) >= 3:
                try:
                    q = int(header[1].strip())
                    p = float(header[2].strip())
                    if q > 0 and p > 0:
                        add_holding(header[0].strip().upper(), q, p)
                        imported_count += 1
                except ValueError:
                    pass
            ticker_idx, qty_idx, price_idx = 0, 1, 2

        for row in reader:
            if len(row) > max(ticker_idx, qty_idx, price_idx):
                sym = row[ticker_idx].strip().upper()
                try:
                    q = int(row[qty_idx].strip())
                    p = float(row[price_idx].strip())
                    if sym and q > 0 and p > 0:
                        add_holding(sym, q, p)
                        imported_count += 1
                except ValueError:
                    continue

    return imported_count


def show_allocation_chart(allocation):
    """Display standalone allocation pie chart."""
    if not allocation:
        return
    labels = [a[0] for a in allocation]
    sizes = [a[1] for a in allocation]
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
    plt.title("Portfolio Allocation")
    plt.show()


def show_sector_chart(sectors):
    """Display standalone sector pie chart."""
    if not sectors:
        return
    labels = [s[0] for s in sectors]
    sizes = [s[1] for s in sectors]
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
    plt.title("Sector Allocation")
    plt.show()


def show_historical_growth():
    """Plot aggregated historical growth of current holdings over the past 3 months."""
    holdings = get_all_holdings()
    if not holdings:
        return False, "No holdings in portfolio to generate growth chart."

    portfolio_history = None

    for row in holdings:
        ticker, quantity = row[1].upper(), row[2]
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            if hist.empty or "Close" not in hist.columns:
                continue

            value_series = hist["Close"] * quantity
            if hasattr(value_series.index, 'tz_localize') and value_series.index.tz is not None:
                value_series.index = value_series.index.tz_localize(None)

            if portfolio_history is None:
                portfolio_history = value_series
            else:
                portfolio_history, value_series = portfolio_history.align(value_series, join='outer')
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
        plt.figure(figsize=(9, 4.5))
        portfolio_history.plot(title="Historical Portfolio Growth (Last 3 Months)", color="#1f77b4", linewidth=2)
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()
        plt.show()
        return True, "Success"

    return False, "Could not fetch historical data for portfolio assets."


def show_volatility_chart():
    """Display a bar chart comparing annualized volatility across current holdings."""
    risk_data = get_risk_metrics()
    if not risk_data:
        return False, "No risk data available for your current holdings."

    tickers = [item["ticker"] for item in risk_data]
    volatilities = [item["volatility"] for item in risk_data]

    plt.figure(figsize=(8, 4.5))
    bars = plt.bar(tickers, volatilities, color="#ff7f0e", width=0.45, edgecolor="#c96005", alpha=0.9)
    plt.title("Annualized Risk Comparison (Volatility %)", fontsize=12, fontweight="bold")
    plt.ylabel("Annualized Volatility (%)", fontsize=10)
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    for bar, val in zip(bars, volatilities):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, f"{val:.1f}%", ha='center', va='bottom', fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.show()
    return True, "Success"


def show_correlation_heatmap():
    """Calculate and display a correlation heatmap across portfolio holdings."""
    holdings = get_all_holdings()
    unique_tickers = list(set(h[1].upper() for h in holdings))
    if len(unique_tickers) < 2:
        return False, "You need at least 2 different stocks in your portfolio to calculate correlation."

    histories = {}

    def fetch_hist(ticker):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")
            if not hist.empty and "Close" in hist.columns:
                s = hist["Close"].dropna()
                if hasattr(s.index, 'tz_localize') and s.index.tz is not None:
                    s.index = s.index.tz_localize(None)
                return ticker, s
        except Exception:
            pass
        return ticker, None

    with ThreadPoolExecutor(max_workers=min(len(unique_tickers), 6)) as executor:
        for ticker, s in executor.map(fetch_hist, unique_tickers):
            if s is not None and len(s) > 10:
                histories[ticker] = s

    if len(histories) < 2:
        return False, "Could not fetch enough price history to generate a correlation heatmap."

    df = pd.DataFrame(histories).dropna()
    if df.empty or len(df.columns) < 2:
        return False, "Not enough overlapping trading days between the selected assets."

    corr = df.corr()

    fig, ax = plt.subplots(figsize=(7, 6))
    cax = ax.matshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    fig.colorbar(cax, shrink=0.8)

    ticks = range(len(corr.columns))
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels(corr.columns, rotation=45, ha="left", fontsize=10)
    ax.set_yticklabels(corr.columns, fontsize=10)

    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            val = corr.iloc[i, j]
            color = "white" if abs(val) > 0.5 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", color=color, fontweight="bold")

    plt.title("Asset Correlation Matrix (6-Month)", pad=20, fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.show()
    return True, "Success"


def show_stock_performance(symbol):
    """Display 1-year historical trend chart with closing price and trading volume."""
    symbol = symbol.strip().upper()
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1y")
        if hist.empty or "Close" not in hist.columns:
            return False, f"Could not retrieve historical data for {symbol}."

        closes = hist["Close"].dropna()
        volumes = hist["Volume"].dropna()
        dates = closes.index
        if hasattr(dates, 'tz_localize') and dates.tz is not None:
            dates = dates.tz_localize(None)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        fig.suptitle(f"{symbol} – 1-Year Performance & Volume", fontsize=13, fontweight="bold")

        ax1.plot(dates, closes.values, label="Closing Price", color="#1f77b4", linewidth=1.8)
        if len(closes) >= 50:
            ma50 = closes.rolling(window=50).mean()
            ax1.plot(dates, ma50.values, label="50-Day Moving Avg", color="#ff7f0e", linestyle="--", linewidth=1.4)
        ax1.set_ylabel("Price")
        ax1.legend(loc="upper left")
        ax1.grid(True, linestyle="--", alpha=0.6)

        ax2.bar(dates, volumes.values, color="gray", alpha=0.6, width=1.0)
        ax2.set_ylabel("Volume")
        ax2.set_xlabel("Date")
        ax2.grid(True, linestyle="--", alpha=0.6)

        plt.tight_layout()
        plt.show()
        return True, "Success"
    except Exception as e:
        return False, f"Error charting {symbol}: {e}"