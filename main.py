from database import *
from market_logic import *
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class AddHoldingWindow:
    def __init__(self, parent, refresh_callback):
        self.refresh_callback = refresh_callback
        self.window = tk.Toplevel(parent)
        self.window.title("Add Holding")
        self.window.geometry("360x360")
        self.window.resizable(False, False)

        ticker_frame = tk.Frame(self.window)
        ticker_frame.pack(fill=tk.X, pady=10, padx=20)

        tk.Label(ticker_frame, text="Stock Ticker Symbol (e.g. AAPL, TCS.NS):", font=("Arial", 10)).pack(anchor="w")
        self.ticker_entry = tk.Entry(ticker_frame, font=("Arial", 10))
        self.ticker_entry.pack(fill=tk.X, pady=3)
        self.ticker_entry.bind('<KeyRelease>', self.on_key_release)

        self.listbox = tk.Listbox(ticker_frame, height=4, font=("Arial", 9))
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        self.listbox_packed = False
        self.search_timer = None

        input_frame = tk.Frame(self.window)
        input_frame.pack(fill=tk.X, pady=5, padx=20)

        tk.Label(input_frame, text="Quantity (Shares):", font=("Arial", 10)).pack(anchor="w")
        self.quantity_entry = tk.Entry(input_frame, font=("Arial", 10))
        self.quantity_entry.pack(fill=tk.X, pady=3)

        tk.Label(input_frame, text="Buy Price Per Share (₹):", font=("Arial", 10)).pack(anchor="w", pady=(8, 0))
        self.price_entry = tk.Entry(input_frame, font=("Arial", 10))
        self.price_entry.pack(fill=tk.X, pady=3)

        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Save Holding", width=14, bg="#1f77b4", fg="white", font=("Arial", 10, "bold"), command=self.save_holding).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", width=10, font=("Arial", 10), command=self.window.destroy).pack(side="left", padx=5)

    def on_key_release(self, event):
        if event.keysym in ['Up', 'Down', 'Return', 'Left', 'Right', 'Tab']:
            return
        if self.search_timer:
            self.window.after_cancel(self.search_timer)
        query = self.ticker_entry.get().strip()
        if len(query) < 1:
            if self.listbox_packed:
                self.listbox.pack_forget()
                self.listbox_packed = False
            return
        self.search_timer = self.window.after(300, lambda: self.perform_search(query))

    def perform_search(self, query):
        def fetch():
            results = search_tickers(query)
            if self.ticker_entry.get().strip().upper() != query.upper() and self.ticker_entry.get().strip() != query:
                return
            self.window.after(0, lambda: self.update_listbox(results))
        threading.Thread(target=fetch, daemon=True).start()

    def update_listbox(self, results):
        self.listbox.delete(0, tk.END)
        if not results:
            if self.listbox_packed:
                self.listbox.pack_forget()
                self.listbox_packed = False
            return
        for r in results:
            self.listbox.insert(tk.END, r)
        if not self.listbox_packed:
            self.listbox.pack(fill=tk.X, pady=2)
            self.listbox_packed = True

    def on_select(self, event):
        selection = self.listbox.curselection()
        if selection:
            item = self.listbox.get(selection[0])
            ticker = item.split(' - ')[0]
            self.ticker_entry.delete(0, tk.END)
            self.ticker_entry.insert(0, ticker)
            self.listbox.pack_forget()
            self.listbox_packed = False

    def save_holding(self):
        ticker = self.ticker_entry.get().strip().upper()
        qty_str = self.quantity_entry.get().strip()
        price_str = self.price_entry.get().strip()

        if not ticker:
            messagebox.showerror("Validation Error", "Please enter a valid stock ticker symbol.", parent=self.window)
            return

        try:
            quantity = int(qty_str)
            buy_price = float(price_str)
            if quantity <= 0 or buy_price <= 0:
                messagebox.showerror("Validation Error", "Quantity and buy price must be positive numbers greater than 0.", parent=self.window)
                return
        except ValueError:
            messagebox.showerror("Validation Error", "Quantity must be a whole number and buy price must be a valid number.", parent=self.window)
            return

        try:
            add_holding(ticker, quantity, buy_price)
            self.refresh_callback()
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save holding: {e}", parent=self.window)


class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Investment Portfolio Analyzer")
        self.root.geometry("1120x840")
        self.create_widgets()
        self.load_holdings()

    def create_widgets(self):
        title = tk.Label(self.root, text="Investment Portfolio Analyzer", font=("Arial", 18, "bold"))
        title.pack(pady=10)

        # Primary actions button frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Add Holding", font=("Arial", 10), command=self.open_add_window).pack(side="left", padx=6)
        tk.Button(button_frame, text="Delete Selected", font=("Arial", 10), command=self.delete_selected).pack(side="left", padx=6)
        tk.Button(button_frame, text="Refresh Live Prices", font=("Arial", 10), command=self.refresh_dashboard).pack(side="left", padx=6)
        tk.Button(button_frame, text="Import CSV", font=("Arial", 10), command=self.import_csv).pack(side="left", padx=6)
        tk.Button(button_frame, text="Export CSV", font=("Arial", 10), command=self.export_csv).pack(side="left", padx=6)

        # Tools & Analytics section
        tools_frame = ttk.LabelFrame(self.root, text="Tools & Analytics")
        tools_frame.pack(fill="x", padx=15, pady=8)

        tk.Button(tools_frame, text="Market Watch", font=("Arial", 10), command=self.open_market_watch).pack(side="left", padx=8, pady=8)
        tk.Button(tools_frame, text="Stock Explorer", font=("Arial", 10), command=self.open_stock_explorer).pack(side="left", padx=8, pady=8)
        tk.Button(tools_frame, text="Full Analytics Report", font=("Arial", 10), command=self.open_analytics_report).pack(side="left", padx=8, pady=8)

        # Portfolio Summary Banner
        summary_frame = ttk.LabelFrame(self.root, text="Portfolio Summary")
        summary_frame.pack(fill="x", padx=15, pady=8)
        self.summary_label = tk.Label(summary_frame, text="No Portfolio Data", font=("Arial", 11))
        self.summary_label.pack(padx=10, pady=10)

        # Treeview Table for Holdings
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=8)

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Ticker", "Quantity", "Buy Price", "Current Price", "Investment", "Current Value", "P/L"),
            show="headings",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.config(command=self.tree.yview)

        col_widths = {
            "ID": 50, "Ticker": 100, "Quantity": 80, "Buy Price": 110,
            "Current Price": 110, "Investment": 130, "Current Value": 130, "P/L": 120
        }

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            width = col_widths.get(col, 100)
            self.tree.column(col, width=width, anchor="center")

        self.tree.pack(side="left", fill="both", expand=True)

        # Embedded Matplotlib Visualizations
        self.charts_frame = tk.Frame(self.root)
        self.charts_frame.pack(fill="both", expand=True, padx=15, pady=8)

        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 3.8))
        self.fig.patch.set_facecolor('#f7f7f7')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.charts_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def refresh_dashboard(self):
        self.load_holdings()

    def open_add_window(self):
        AddHoldingWindow(self.root, self.refresh_dashboard)

    def load_holdings(self):
        """Fetch holdings and populate UI immediately, updating live quotes in background."""
        holdings = get_all_holdings()

        for row in self.tree.get_children():
            self.tree.delete(row)

        if not holdings:
            self.summary_label.config(text="No Portfolio Data. Click 'Add Holding' or 'Import CSV' to start tracking your stocks.")
            self.update_charts()
            return

        self.summary_label.config(text="Fetching live market data...")

        def worker():
            summary = calculate_portfolio_summary()
            self.root.after(0, lambda: self._apply_summary(summary))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_summary(self, summary):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for row in summary["rows"]:
            formatted_row = (
                row[0],
                row[1],
                row[2],
                f"₹{row[3]:.2f}",
                f"₹{row[4]:.2f}",
                f"₹{row[5]:.2f}",
                f"₹{row[6]:.2f}",
                f"₹{row[7]:.2f}"
            )
            self.tree.insert("", "end", values=formatted_row)

        self.summary_label.config(
            text=f"Investment: ₹{summary['investment']:,.2f}   |   "
                 f"Current Value: ₹{summary['current_value']:,.2f}   |   "
                 f"P/L: ₹{summary['profit_loss']:,.2f}   |   "
                 f"ROI: {summary['roi']:.2f}%"
        )
        self.update_charts()

    def update_charts(self):
        self.ax1.clear()
        self.ax2.clear()

        self.ax1.axis('off')
        self.ax2.axis('off')

        allocation = get_allocation()
        if allocation:
            labels = [a[0] for a in allocation]
            sizes = [a[1] for a in allocation]
            self.ax1.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
            self.ax1.set_title("Portfolio Allocation", fontsize=11, fontweight="bold")
        else:
            self.ax1.text(0.5, 0.5, "No Allocation Data", ha='center', va='center', color='gray')

        sectors = get_sector_allocation()
        if sectors:
            labels = [s[0] for s in sectors]
            sizes = [s[1] for s in sectors]
            self.ax2.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140)
            self.ax2.set_title("Sector Diversification", fontsize=11, fontweight="bold")
        else:
            self.ax2.text(0.5, 0.5, "No Sector Data", ha='center', va='center', color='gray')

        self.canvas.draw()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a holding from the table to delete.", parent=self.root)
            return

        item = self.tree.item(selected[0])
        holding_id = item["values"][0]
        ticker = item["values"][1]

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete holding #{holding_id} ({ticker})?", parent=self.root)
        if confirm:
            delete_holding(holding_id)
            self.load_holdings()

    def import_csv(self):
        filepath = filedialog.askopenfilename(
            title="Select Portfolio CSV to Import",
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")),
            parent=self.root
        )
        if filepath:
            try:
                count = import_portfolio_from_csv(filepath)
                if count > 0:
                    messagebox.showinfo("Import Complete", f"Successfully imported {count} holding(s) from CSV.", parent=self.root)
                    self.load_holdings()
                else:
                    messagebox.showwarning("Import Notice", "No valid holdings were found in the selected CSV file.", parent=self.root)
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import CSV: {e}", parent=self.root)

    def export_csv(self):
        holdings = get_all_holdings()
        if not holdings:
            messagebox.showwarning("Export Notice", "Your portfolio is currently empty. Add holdings before exporting.", parent=self.root)
            return

        filepath = filedialog.asksaveasfilename(
            title="Export Portfolio to CSV",
            defaultextension=".csv",
            filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")),
            parent=self.root
        )
        if filepath:
            try:
                export_portfolio_to_csv(filepath)
                messagebox.showinfo("Export Successful", f"Portfolio successfully exported to:\n{filepath}", parent=self.root)
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export CSV: {e}", parent=self.root)

    def open_market_watch(self):
        top = tk.Toplevel(self.root)
        top.title("Live Market Watch")
        top.geometry("520x360")

        btn_frame = tk.Frame(top)
        btn_frame.pack(fill="x", padx=10, pady=8)

        text_widget = tk.Text(top, wrap="word", font=("Courier", 10))
        scroll = ttk.Scrollbar(top, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text_widget.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        def fetch_data():
            text_widget.config(state="normal")
            text_widget.delete("1.0", tk.END)
            text_widget.insert(tk.END, "Fetching live market prices...\n")
            text_widget.config(state="disabled")

            def worker():
                symbols = ["AAPL", "MSFT", "GOOGL", "RELIANCE.NS", "TCS.NS", "INFY.NS"]
                quotes = get_quotes_batch(symbols)
                lines = []
                for symbol in symbols:
                    quote = quotes.get(symbol)
                    if quote:
                        current_price = quote.get("c", 0.0)
                        change_percent = quote.get("dp", 0.0)
                        lines.append(f"{symbol:<12} | Price: ₹{current_price:<8.2f} | Change: {change_percent:+.2f}%\n")
                    else:
                        lines.append(f"{symbol:<12} | Data Unavailable\n")

                def update_ui():
                    text_widget.config(state="normal")
                    text_widget.delete("1.0", tk.END)
                    for line in lines:
                        text_widget.insert(tk.END, line)
                    text_widget.config(state="disabled")

                top.after(0, update_ui)

            threading.Thread(target=worker, daemon=True).start()

        tk.Button(btn_frame, text="Refresh Live Prices", font=("Arial", 9), command=fetch_data).pack(side="left", padx=5)
        fetch_data()

    def open_stock_explorer(self):
        top = tk.Toplevel(self.root)
        top.title("Stock Explorer & Fundamentals")
        top.geometry("560x420")
        top.resizable(False, False)

        header_frame = tk.Frame(top, padx=15, pady=10)
        header_frame.pack(fill="x")

        tk.Label(header_frame, text="Search Ticker (e.g. AAPL, NVDA, RELIANCE.NS):", font=("Arial", 10)).pack(anchor="w")

        search_frame = tk.Frame(header_frame)
        search_frame.pack(fill="x", pady=5)

        stock_entry = tk.Entry(search_frame, font=("Arial", 11))
        stock_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        result_box = tk.Frame(top, padx=15, pady=10, relief="groove", borderwidth=1)
        result_box.pack(fill="both", expand=True, padx=15, pady=5)

        status_label = tk.Label(result_box, text="Enter a ticker symbol and click 'Analyze Stock'.", font=("Arial", 10), fg="gray")
        status_label.pack(pady=25)

        name_lbl = tk.Label(result_box, text="", font=("Arial", 13, "bold"), fg="#1f77b4")
        price_lbl = tk.Label(result_box, text="", font=("Arial", 12))
        sector_lbl = tk.Label(result_box, text="", font=("Arial", 10))
        mcap_lbl = tk.Label(result_box, text="", font=("Arial", 10))

        def do_analyze():
            symbol = stock_entry.get().strip().upper()
            if not symbol:
                messagebox.showwarning("Input Required", "Please enter a stock ticker symbol.", parent=top)
                return

            status_label.config(text="Fetching company profile and market quote...", fg="black")
            status_label.pack(pady=25)
            for widget in [name_lbl, price_lbl, sector_lbl, mcap_lbl]:
                widget.pack_forget()

            def worker():
                quote = get_live_quote(symbol)
                profile = get_company_profile(symbol)

                def update_ui():
                    if not quote and not profile:
                        status_label.config(text=f"Could not find data for ticker '{symbol}'.", fg="red")
                        return

                    status_label.pack_forget()
                    c_price = quote.get("c", 0.0) if quote else 0.0
                    dp = quote.get("dp", 0.0) if quote else 0.0
                    curr = profile.get("currency", "USD")
                    curr_symbol = "₹" if "NS" in symbol or curr == "INR" else "$"

                    dp_color = "green" if dp >= 0 else "red"
                    dp_sign = "+" if dp >= 0 else ""

                    mcap_val = profile.get("marketCap", 0)
                    if mcap_val >= 1e12:
                        mcap_str = f"{curr_symbol}{mcap_val/1e12:.2f} Trillion"
                    elif mcap_val >= 1e9:
                        mcap_str = f"{curr_symbol}{mcap_val/1e9:.2f} Billion"
                    elif mcap_val > 0:
                        mcap_str = f"{curr_symbol}{mcap_val/1e6:.2f} Million"
                    else:
                        mcap_str = "N/A"

                    name_lbl.config(text=f"{profile.get('name', symbol)} ({symbol})")
                    name_lbl.pack(anchor="w", pady=(10, 4))

                    price_lbl.config(text=f"Live Price: {curr_symbol}{c_price:,.2f}  ({dp_sign}{dp:.2f}%)", fg=dp_color)
                    price_lbl.pack(anchor="w", pady=4)

                    sector_lbl.config(text=f"Sector / Industry: {profile.get('industry', 'General')}")
                    sector_lbl.pack(anchor="w", pady=4)

                    mcap_lbl.config(text=f"Market Capitalization: {mcap_str}")
                    mcap_lbl.pack(anchor="w", pady=4)

                top.after(0, update_ui)

            threading.Thread(target=worker, daemon=True).start()

        def do_chart():
            symbol = stock_entry.get().strip().upper()
            if not symbol:
                messagebox.showwarning("Input Required", "Please enter a stock ticker symbol.", parent=top)
                return
            ok, msg = show_stock_performance(symbol)
            if not ok:
                messagebox.showinfo("Chart Notice", msg, parent=top)

        analyze_btn = tk.Button(search_frame, text="Analyze Stock", font=("Arial", 10, "bold"), bg="#1f77b4", fg="white", command=do_analyze)
        analyze_btn.pack(side="left", padx=4)

        chart_btn = tk.Button(search_frame, text="View 1Y Chart", font=("Arial", 10), command=do_chart)
        chart_btn.pack(side="left", padx=4)

    def open_analytics_report(self):
        top = tk.Toplevel(self.root)
        top.title("Full Analytics & Risk Report")
        top.geometry("740x580")

        summary = calculate_portfolio_summary()
        current_value = summary['current_value']
        profit_loss = summary['profit_loss']
        roi = summary['roi']

        rows = summary["rows"]
        if rows:
            best = max(rows, key=lambda x: x[7])
            worst = min(rows, key=lambda x: x[7])
            best_str = f"{best[1]} (+₹{best[7]:.2f})" if best[7] >= 0 else f"{best[1]} (₹{best[7]:.2f})"
            worst_str = f"{worst[1]} (+₹{worst[7]:.2f})" if worst[7] >= 0 else f"{worst[1]} (₹{worst[7]:.2f})"
        else:
            best_str = "N/A"
            worst_str = "N/A"

        diversification_msg = get_diversification_suggestion()

        report_frame = tk.Frame(top, padx=20, pady=15)
        report_frame.pack(fill="both", expand=True)

        metrics = [
            ("Total Current Value", f"₹{current_value:,.2f}"),
            ("Total Profit / Loss", f"₹{profit_loss:,.2f}"),
            ("Return on Investment (ROI)", f"{roi:.2f}%"),
            ("Best Performer", best_str),
            ("Worst Performer", worst_str),
            ("Asset Allocation", "View Live Chart on Main Dashboard"),
            ("Diversification Analysis", diversification_msg),
        ]

        for i, (metric, answer) in enumerate(metrics):
            tk.Label(report_frame, text=metric, font=("Arial", 10, "bold"), anchor="w").grid(row=i, column=0, sticky="w", pady=4, padx=10)
            tk.Label(report_frame, text=answer, font=("Arial", 10), anchor="w").grid(row=i, column=1, sticky="w", pady=4, padx=10)

        # Risk metrics section
        risk_frame = ttk.LabelFrame(top, text="Asset Risk Metrics (Annualized)")
        risk_frame.pack(fill="x", padx=20, pady=10)

        risk_label = tk.Label(risk_frame, text="Calculating risk metrics...", font=("Arial", 10), justify="left")
        risk_label.pack(padx=10, pady=8, anchor="w")

        def load_risk():
            risk_metrics = get_risk_metrics()
            if risk_metrics:
                lines = []
                for item in risk_metrics:
                    lines.append(f"• {item['ticker']:<10} => Volatility: {item['volatility']:.2f}%   |   Max Drawdown: {item['drawdown']:.2f}%")
                text = "\n".join(lines)
            else:
                text = "No risk metrics available for current holdings."

            def update_risk_ui():
                risk_label.config(text=text)

            top.after(0, update_risk_ui)

        threading.Thread(target=load_risk, daemon=True).start()

        # Chart launcher buttons
        btn_frame = tk.Frame(top, pady=15)
        btn_frame.pack(fill="x", padx=20)

        def launch_growth():
            ok, msg = show_historical_growth()
            if not ok:
                messagebox.showinfo("Notice", msg, parent=top)

        def launch_volatility():
            ok, msg = show_volatility_chart()
            if not ok:
                messagebox.showinfo("Notice", msg, parent=top)

        def launch_heatmap():
            ok, msg = show_correlation_heatmap()
            if not ok:
                messagebox.showinfo("Notice", msg, parent=top)

        tk.Button(btn_frame, text="Historical Growth (3M)", font=("Arial", 9, "bold"), command=launch_growth).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Volatility Bar Chart", font=("Arial", 9, "bold"), command=launch_volatility).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Correlation Heatmap", font=("Arial", 9, "bold"), command=launch_heatmap).pack(side="left", padx=5)


def main():
    initialize_database()
    root = tk.Tk()
    Dashboard(root)
    root.mainloop()


if __name__ == "__main__":
    import signal
    import sys

    def signal_handler(sig, frame):
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)