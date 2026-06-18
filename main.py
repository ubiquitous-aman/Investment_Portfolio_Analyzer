from database import *
from market_logic import *
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AddHoldingWindow:
    def __init__(self, parent, refresh_callback):
        self.refresh_callback = refresh_callback
        self.window = tk.Toplevel(parent)
        self.window.title("Add Holding")
        self.window.geometry("350x350")

        ticker_frame = tk.Frame(self.window)
        ticker_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(ticker_frame, text="Ticker").pack()
        self.ticker_entry = tk.Entry(ticker_frame)
        self.ticker_entry.pack()
        self.ticker_entry.bind('<KeyRelease>', self.on_key_release)
        
        self.listbox = tk.Listbox(ticker_frame, height=4)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        self.listbox_packed = False
        self.search_timer = None

        tk.Label(self.window, text="Quantity").pack(pady=5)
        self.quantity_entry = tk.Entry(self.window)
        self.quantity_entry.pack()

        tk.Label(self.window, text="Buy Price").pack(pady=5)
        self.price_entry = tk.Entry(self.window)
        self.price_entry.pack()

        tk.Button(self.window, text="Save", command=self.save_holding).pack(pady=15)

    def on_key_release(self, event):
        if event.keysym in ['Up', 'Down', 'Return', 'Left', 'Right']:
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
            self.listbox.pack(pady=2)
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
        quantity = self.quantity_entry.get().strip()
        buy_price = self.price_entry.get().strip()

        if not ticker:
            messagebox.showerror("Error", "Ticker required")
            return
        try:
            quantity = int(quantity)
            buy_price = float(buy_price)
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity or price")
            return

        add_holding(ticker, quantity, buy_price)
        self.refresh_callback()
        self.window.destroy()

class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Investment Portfolio Analyzer")
        self.root.geometry("1100x850")
        self.create_widgets()
        self.load_holdings()

    def create_widgets(self):
        title = tk.Label(self.root, text="Investment Portfolio Analyzer", font=("Arial", 18, "bold"))
        title.pack(pady=10)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Add Holding", command=self.open_add_window).pack(side="left", padx=10)
        tk.Button(button_frame, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=10)

        tools_frame = ttk.LabelFrame(self.root, text="Tools & Analytics")
        tools_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(tools_frame, text="Market Watch", command=self.open_market_watch).pack(side="left", padx=10, pady=10)
        tk.Button(tools_frame, text="Full Analytics Report", command=self.open_analytics_report).pack(side="left", padx=10, pady=10)

        summary_frame = ttk.LabelFrame(self.root, text="Portfolio Summary")
        summary_frame.pack(fill="x", padx=10, pady=10)
        self.summary_label = tk.Label(summary_frame, text="No Portfolio Data", font=("Arial", 11))
        self.summary_label.pack(padx=10, pady=10)

        tree_frame = tk.Frame(self.root)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Ticker", "Quantity", "Buy Price", "Current Price", "Investment", "Current Value", "P/L"),
            show="headings",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.config(command=self.tree.yview)

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Ticker", width=100, anchor="center")
        self.tree.column("Quantity", width=80, anchor="center")
        
        self.tree.pack(side="left", fill="both", expand=True)

        self.charts_frame = tk.Frame(self.root)
        self.charts_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 4))
        self.fig.patch.set_facecolor('#f0f0f0')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.charts_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def refresh_dashboard(self):
        self.load_holdings()

    def open_add_window(self):
        AddHoldingWindow(self.root, self.refresh_dashboard)

    def load_holdings(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        summary = calculate_portfolio_summary()
        for row in summary["rows"]:
            formatted_row = (row[0], row[1], row[2], f"{row[3]:.4f}", f"{row[4]:.4f}", f"{row[5]:.4f}", f"{row[6]:.4f}", f"{row[7]:.4f}")
            self.tree.insert("", "end", values=formatted_row)

        self.summary_label.config(
            text=f"Investment: ₹{summary['investment']:.2f}   |   Current Value: ₹{summary['current_value']:.2f}   |   P/L: ₹{summary['profit_loss']:.2f}   |   ROI: {summary['roi']:.2f}%"
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
            self.ax1.pie(sizes, labels=labels, autopct="%1.1f%%")
            self.ax1.set_title("Portfolio Allocation")
        else:
            self.ax1.text(0.5, 0.5, "No Allocation Data", ha='center', va='center')
            
        sectors = get_sector_allocation()
        if sectors:
            labels = [s[0] for s in sectors]
            sizes = [s[1] for s in sectors]
            self.ax2.pie(sizes, labels=labels, autopct="%1.1f%%")
            self.ax2.set_title("Sector Analysis")
        else:
            self.ax2.text(0.5, 0.5, "No Sector Data", ha='center', va='center')
            
        self.canvas.draw()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a row")
            return
        item = self.tree.item(selected[0])
        holding_id = item["values"][0]
        delete_holding(holding_id)
        self.load_holdings()

    def open_market_watch(self):
        top = tk.Toplevel(self.root)
        top.title("Market Watch")
        top.geometry("500x350")
        
        btn_frame = tk.Frame(top)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        text_widget = tk.Text(top, wrap="word", font=("Courier", 10))
        scroll = ttk.Scrollbar(top, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text_widget.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        def fetch_data():
            text_widget.config(state="normal")
            text_widget.delete("1.0", tk.END)
            text_widget.insert(tk.END, "Fetching data...\n")
            top.update()
            text_widget.delete("1.0", tk.END)
            
            symbols = ["AAPL", "MSFT", "RELIANCE.NS", "TCS.NS", "INFY.NS"]
            for symbol in symbols:
                quote = get_live_quote(symbol)
                if quote:
                    current_price = quote.get("c", 0)
                    change_percent = quote.get("dp", 0)
                    line = f"{symbol:<12} | Price: ₹{current_price:<8.2f} | Change: {change_percent:+.2f}%\n"
                else:
                    line = f"{symbol:<12} | Data Unavailable\n"
                text_widget.insert(tk.END, line)
            text_widget.config(state="disabled")

        tk.Button(btn_frame, text="Refresh Market Data", command=fetch_data).pack(side="left", padx=5)
        fetch_data()



    def open_analytics_report(self):
        top = tk.Toplevel(self.root)
        top.title("Full Analytics Report")
        top.geometry("700x450")

        summary = calculate_portfolio_summary()
        current_value = summary['current_value']
        profit_loss = summary['profit_loss']
        
        rows = summary["rows"]
        if rows:
            # rows format: (holding_id, ticker, quantity, buy_price, current_price, investment_value, current_value, profit_loss)
            best = max(rows, key=lambda x: x[7])
            worst = min(rows, key=lambda x: x[7])
            best_str = f"{best[1]} (+₹{best[7]:.2f})" if best[7] >= 0 else f"{best[1]} (₹{best[7]:.2f})"
            worst_str = f"{worst[1]} (+₹{worst[7]:.2f})" if worst[7] >= 0 else f"{worst[1]} (₹{worst[7]:.2f})"
        else:
            best_str = "N/A"
            worst_str = "N/A"
            
        diversification_msg = get_diversification_suggestion()
        
        report_frame = tk.Frame(top, padx=20, pady=20)
        report_frame.pack(fill="both", expand=True)
        
        metrics = [
            ("Current Value", f"₹{current_value:.2f}"),
            ("Profit/Loss", f"₹{profit_loss:.2f}"),
            ("Best Performer", best_str),
            ("Worst Performer", worst_str),
            ("Asset Allocation", "View Live Chart on Main Dashboard"),
            ("Diversification", diversification_msg),
            ("Historical Growth", "View Chart Below"),
        ]
        
        for i, (metric, answer) in enumerate(metrics):
            tk.Label(report_frame, text=metric, font=("Arial", 11, "bold"), anchor="w").grid(row=i, column=0, sticky="w", pady=8, padx=10)
            tk.Label(report_frame, text=answer, font=("Arial", 11), anchor="w").grid(row=i, column=1, sticky="w", pady=8, padx=10)
            
        btn_frame = tk.Frame(top)
        btn_frame.pack(pady=15)
        

        tk.Button(btn_frame, text="View Historical Growth", command=show_historical_growth, width=20).pack(side="left", padx=10)

def main():
    initialize_database()
    root = tk.Tk()
    Dashboard(root)
    root.mainloop()

if __name__ == "__main__":
    import signal
    import sys
    
    # Catch Ctrl+C and exit silently to prevent cffi/tkinter stack traces
    def signal_handler(sig, frame):
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)