# Investment Portfolio Analyzer

A lightweight, standalone desktop application built with Python and Tkinter to track investments, pull live market prices, and visualize portfolio health in real-time.

## Features

- **Instant Live Market Data:** Integrates fast parallel Yahoo Finance quote fetching with background threading for instant, zero-freeze updates.
- **Ticker Autocomplete:** Built-in live ticker search suggests correct symbols with debounced typing.
- **Interactive Dashboard:** View your entire portfolio at a glance, including total investment, current value, profit/loss (P/L), and return on investment (ROI).
- **Embedded Real-time Visualizations:**
  - **Portfolio Allocation Chart:** Dynamically updates to show the weight of each asset.
  - **Sector Diversification Chart:** Categorizes stocks by industry/sector for clear diversification insights.
- **Stock Explorer & Fundamentals:** Look up any stock (e.g., `AAPL`, `NVDA`, `RELIANCE.NS`) to view live pricing, day change %, market cap, sector, and an interactive 1-year performance chart with volume.
- **Market Watch:** Instant popup widget tracking live benchmark and blue-chip stocks.
- **Comprehensive Risk & Performance Analytics:**
  - Annualized Volatility and Maximum Drawdown per holding.
  - 3-Month Historical Growth curve.
  - Risk Comparison Bar Chart.
  - 6-Month Asset Correlation Heatmap.
  - Best and worst performing assets.
- **CSV Import & Export:** One-click backup and restore of your portfolio data.
- **Local Storage:** Secure, local SQLite database (`portfolio.db`) with automatic validation.

## Prerequisites

Before running the application, ensure you have the following installed on your system:
- **Python 3.8+**
- `pip` (Python package manager)

## Installation & Setup

1. **Clone or Download the Repository:**
   ```bash
   # Clone using git or download the ZIP from GitHub and extract it
   git clone https://github.com/ubiquitous-aman/Investment_Portfolio_Analyzer.git
   cd Investment_Portfolio_Analyzer
   ```

2. **Create a Virtual Environment (Recommended):**
   ```bash
   python -m venv venv
   
   # Activate on Linux/macOS
   source venv/bin/activate  
   
   # Activate on Windows
   venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *Required packages include: `pandas`, `matplotlib`, `numpy`, `requests`, `yfinance`, and `Pillow`.*

## How to Run

1. Open your terminal or command prompt.
2. Navigate to the project directory.
3. Make sure your virtual environment is activated (if you created one).
4. Run the main application file:
   ```bash
   python main.py
   ```

## Project Structure

- `main.py`: The entry point of the application. Contains the Tkinter GUI setup and dashboard logic.
- `market_logic.py`: Handles all API interactions with Yahoo Finance (`yfinance` and `requests`), data caching, and portfolio calculations.
- `database.py`: Manages the local SQLite database schema and handles CRUD operations for stock holdings.
- `requirements.txt`: Lists all the necessary Python packages to run the project.
- `portfolio.db`: SQLite database file (created automatically upon first run).

## Technologies Used

- **Python**: Core programming language.
- **Tkinter**: Built-in GUI library for building the desktop application.
- **SQLite3**: Lightweight database for storing user holdings locally without setup.
- **Matplotlib**: For plotting interactive pie charts and historical line charts.
- **yfinance**: For fetching reliable live and historical stock data from Yahoo Finance.
