# Investment Portfolio Analyzer

A lightweight, standalone desktop application built with Python and Tkinter to track investments, pull live market prices, and visualize portfolio health in real-time.

## Features

- **Live Market Data:** Integrates with Yahoo Finance API (`yfinance`) to fetch real-time stock prices and daily changes.
- **Ticker Search:** Built-in ticker search functionality prevents errors by suggesting correct ticker symbols when adding holdings.
- **Interactive Dashboard:** View your entire portfolio at a glance, including total investment, current value, profit/loss (P/L), and return on investment (ROI).
- **Real-time Visualizations:**
  - **Portfolio Allocation Chart:** Dynamically updates to show the weight of each asset in your portfolio.
  - **Sector Analysis Chart:** Automatically fetches industry data for each stock to visualize your portfolio's sector diversification.
- **Market Watch:** A quick popup tool to check live prices for major predefined stock symbols.
- **Comprehensive Analytics:** Detailed reports including best/worst performers, diversification warnings, and an aggregated 3-month historical growth line chart.
- **Local Storage:** All data is securely stored locally on your machine using an SQLite database (`portfolio.db`).

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
