import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as mpatches
from data_fetcher import analyze_ticker
from database import get_earnings_history, get_watchlist, add_to_watchlist, remove_from_watchlist
import threading

# --- Color Scheme ---
BG_DARK = "#1e1e2e"
BG_MID = "#2a2a3e"
BG_LIGHT = "#313145"
ACCENT = "#4f8ef7"
GREEN = "#4caf82"
RED = "#e05c5c"
TEXT = "#e0e0e0"
TEXT_DIM = "#888888"
WHITE = "#ffffff"

class EarningsAnalyzer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Earnings Analyzer — Time Spread Tool")
        self.geometry("1100x750")
        self.configure(bg=BG_DARK)
        self.resizable(True, True)
        self.current_summary = None
        self._build_ui()

    def _build_ui(self):
        # --- Header ---
        header = tk.Frame(self, bg=ACCENT, height=50)
        header.pack(fill="x")
        tk.Label(header, text="EARNINGS ANALYZER", font=("Calibri", 18, "bold"),
                 bg=ACCENT, fg=WHITE).pack(side="left", padx=20, pady=10)
        tk.Label(header, text="Time Spread Candidate Tool",
                 font=("Calibri", 11), bg=ACCENT, fg=WHITE).pack(side="left", padx=5, pady=10)

        # --- Main Layout ---
        main = tk.Frame(self, bg=BG_DARK)
        main.pack(fill="both", expand=True, padx=15, pady=15)

        # Left panel
        left = tk.Frame(main, bg=BG_MID, width=280)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        # Right panel
        right = tk.Frame(main, bg=BG_DARK)
        right.pack(side="left", fill="both", expand=True)

        self._build_left_panel(left)
        self._build_right_panel(right)

    def _build_left_panel(self, parent):
        # Search section
        tk.Label(parent, text="ANALYZE TICKER", font=("Calibri", 11, "bold"),
                 bg=BG_MID, fg=ACCENT).pack(pady=(15, 5), padx=15, anchor="w")

        search_frame = tk.Frame(parent, bg=BG_MID)
        search_frame.pack(fill="x", padx=15, pady=5)

        self.ticker_entry = tk.Entry(search_frame, font=("Calibri", 13, "bold"),
                                      bg=BG_LIGHT, fg=WHITE, insertbackground=WHITE,
                                      relief="flat", width=10)
        self.ticker_entry.pack(side="left", ipady=6, padx=(0, 5))
        self.ticker_entry.bind("<Return>", lambda e: self._run_analysis())

        tk.Button(search_frame, text="GO", font=("Calibri", 11, "bold"),
                  bg=ACCENT, fg=WHITE, relief="flat", cursor="hand2",
                  command=self._run_analysis, width=4).pack(side="left", ipady=6)

        # Lookback
        tk.Label(parent, text="Earnings to analyze:",
                 font=("Calibri", 9), bg=BG_MID, fg=TEXT_DIM).pack(padx=15, anchor="w")
        self.lookback_var = tk.IntVar(value=8)
        lookback_frame = tk.Frame(parent, bg=BG_MID)
        lookback_frame.pack(fill="x", padx=15, pady=(2, 10))
        for val in [4, 8, 12]:
            tk.Radiobutton(lookback_frame, text=str(val), variable=self.lookback_var,
                           value=val, bg=BG_MID, fg=TEXT, selectcolor=BG_LIGHT,
                           activebackground=BG_MID, font=("Calibri", 9)).pack(side="left")

        # Status
        self.status_var = tk.StringVar(value="Enter a ticker to begin")
        tk.Label(parent, textvariable=self.status_var, font=("Calibri", 9),
                 bg=BG_MID, fg=TEXT_DIM, wraplength=240).pack(padx=15, pady=5, anchor="w")

        # Divider
        tk.Frame(parent, bg=BG_LIGHT, height=1).pack(fill="x", padx=15, pady=10)

        # Watchlist
        tk.Label(parent, text="WATCHLIST", font=("Calibri", 11, "bold"),
                 bg=BG_MID, fg=ACCENT).pack(pady=(5, 5), padx=15, anchor="w")

        wl_btn_frame = tk.Frame(parent, bg=BG_MID)
        wl_btn_frame.pack(fill="x", padx=15, pady=(0, 5))
        tk.Button(wl_btn_frame, text="+ Add", font=("Calibri", 9),
                  bg=GREEN, fg=WHITE, relief="flat", cursor="hand2",
                  command=self._add_to_watchlist).pack(side="left", padx=(0, 5), ipady=3, ipadx=5)
        tk.Button(wl_btn_frame, text="− Remove", font=("Calibri", 9),
                  bg=RED, fg=WHITE, relief="flat", cursor="hand2",
                  command=self._remove_from_watchlist).pack(side="left", ipady=3, ipadx=5)

        # Watchlist listbox
        wl_frame = tk.Frame(parent, bg=BG_MID)
        wl_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.watchlist_box = tk.Listbox(wl_frame, bg=BG_LIGHT, fg=TEXT,
                                         font=("Calibri", 10), relief="flat",
                                         selectbackground=ACCENT, selectforeground=WHITE,
                                         activestyle="none", cursor="hand2")
        self.watchlist_box.pack(fill="both", expand=True)
        self.watchlist_box.bind("<Double-Button-1>", self._load_from_watchlist)
        self._refresh_watchlist()

    def _build_right_panel(self, parent):
        # Summary cards row
        self.cards_frame = tk.Frame(parent, bg=BG_DARK)
        self.cards_frame.pack(fill="x", pady=(0, 10))

        self.card_vars = {}
        card_defs = [
            ("TICKER", "ticker"),
            ("AVG ABS MOVE", "avg_abs_move"),
            ("AVG MOVE", "avg_move"),
            ("LARGEST", "max_move"),
            ("SMALLEST", "min_move"),
            ("ANALYZED", "earnings_analyzed"),
        ]

        for label, key in card_defs:
            card = tk.Frame(self.cards_frame, bg=BG_MID, padx=12, pady=8)
            card.pack(side="left", fill="y", padx=(0, 8))
            tk.Label(card, text=label, font=("Calibri", 8),
                     bg=BG_MID, fg=TEXT_DIM).pack(anchor="w")
            var = tk.StringVar(value="--")
            self.card_vars[key] = var
            tk.Label(card, textvariable=var, font=("Calibri", 14, "bold"),
                     bg=BG_MID, fg=WHITE).pack(anchor="w")

        # Chart
        chart_frame = tk.Frame(parent, bg=BG_MID)
        chart_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.fig, self.ax = plt.subplots(figsize=(8, 3.5))
        self.fig.patch.set_facecolor(BG_MID)
        self.ax.set_facecolor(BG_LIGHT)
        self.ax.set_title("Post-Earnings Price Moves", color=TEXT, fontsize=11)
        self.ax.tick_params(colors=TEXT)
        for spine in self.ax.spines.values():
            spine.set_edgecolor(BG_LIGHT)

        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # History table
        table_frame = tk.Frame(parent, bg=BG_MID)
        table_frame.pack(fill="x")

        tk.Label(table_frame, text="EARNINGS HISTORY", font=("Calibri", 10, "bold"),
                 bg=BG_MID, fg=ACCENT).pack(anchor="w", padx=10, pady=(8, 4))

        cols = ("Date", "Move %", "EPS Estimate", "EPS Actual", "Beat EPS")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=5)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=BG_LIGHT, foreground=TEXT,
                         rowheight=22, fieldbackground=BG_LIGHT, borderwidth=0)
        style.configure("Treeview.Heading", background=BG_MID, foreground=ACCENT,
                         font=("Calibri", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", ACCENT)])

        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        self.tree.pack(fill="x", padx=10, pady=(0, 10))

    def _run_analysis(self):
        ticker = self.ticker_entry.get().strip().upper()
        if not ticker:
            messagebox.showwarning("Input Required", "Please enter a ticker symbol.")
            return

        self.status_var.set(f"Fetching data for {ticker}...")
        self._clear_display()

        def fetch():
            summary = analyze_ticker(ticker, lookback=self.lookback_var.get())
            self.after(0, lambda: self._display_results(ticker, summary))

        threading.Thread(target=fetch, daemon=True).start()

    def _display_results(self, ticker, summary):
        if summary is None:
            self.status_var.set(f"No data found for {ticker}")
            return

        self.current_summary = summary
        self.status_var.set(f"Analysis complete for {ticker}")

        # Update cards
        self.card_vars["ticker"].set(summary["ticker"])
        self.card_vars["avg_abs_move"].set(f"{summary['avg_abs_move']:.2f}%")
        avg = summary["avg_move"]
        self.card_vars["avg_move"].set(f"{avg:+.2f}%")
        self.card_vars["max_move"].set(f"{summary['max_move']:+.2f}%")
        self.card_vars["min_move"].set(f"{summary['min_move']:+.2f}%")
        self.card_vars["earnings_analyzed"].set(str(summary["earnings_analyzed"]))

        # Update chart
        self.ax.clear()
        self.ax.set_facecolor(BG_LIGHT)
        results = summary["results"]
        dates = [r["date"] for r in results]
        moves = [r["move_pct"] for r in results]
        colors = [GREEN if m >= 0 else RED for m in moves]

        bars = self.ax.bar(range(len(moves)), moves, color=colors, width=0.6, zorder=3)
        self.ax.axhline(y=0, color=TEXT_DIM, linewidth=0.8, zorder=2)
        self.ax.set_xticks(range(len(dates)))
        self.ax.set_xticklabels(dates, rotation=35, ha="right", fontsize=8, color=TEXT)
        self.ax.set_ylabel("Move %", color=TEXT, fontsize=9)
        self.ax.set_title(f"{ticker} — Post-Earnings Price Moves", color=TEXT, fontsize=11)
        self.ax.tick_params(colors=TEXT)
        self.ax.yaxis.grid(True, color=BG_DARK, linewidth=0.5, zorder=1)
        for spine in self.ax.spines.values():
            spine.set_edgecolor(BG_MID)

        # Value labels on bars
        for bar, move in zip(bars, moves):
            self.ax.text(bar.get_x() + bar.get_width() / 2,
                         bar.get_height() + (0.1 if move >= 0 else -0.3),
                         f"{move:+.1f}%", ha="center", va="bottom" if move >= 0 else "top",
                         fontsize=7, color=TEXT)

        self.fig.tight_layout()
        self.canvas.draw()

        # Update table
        for row in self.tree.get_children():
            self.tree.delete(row)

        history = get_earnings_history(ticker)
        for row in history:
            _, date, exp_move, act_move, beat_exp, eps_est, eps_act, beat_eps, notes = row
            beat_str = "✓" if beat_eps == 1 else ("✗" if beat_eps == 0 else "--")
            eps_est_str = f"{eps_est:.2f}" if eps_est else "--"
            eps_act_str = f"{eps_act:.2f}" if eps_act else "--"
            move_str = f"{act_move:+.2f}%" if act_move else "--"
            self.tree.insert("", "end", values=(date, move_str, eps_est_str, eps_act_str, beat_str))

    def _clear_display(self):
        for key in self.card_vars:
            self.card_vars[key].set("--")
        self.ax.clear()
        self.ax.set_facecolor(BG_LIGHT)
        self.ax.set_title("Post-Earnings Price Moves", color=TEXT, fontsize=11)
        self.canvas.draw()
        for row in self.tree.get_children():
            self.tree.delete(row)

    def _refresh_watchlist(self):
        self.watchlist_box.delete(0, tk.END)
        for row in get_watchlist():
            self.watchlist_box.insert(tk.END, f"  {row[0]}")

    def _add_to_watchlist(self):
        ticker = self.ticker_entry.get().strip().upper()
        if not ticker:
            messagebox.showwarning("Input Required", "Enter a ticker first.")
            return
        add_to_watchlist(ticker)
        self._refresh_watchlist()

    def _remove_from_watchlist(self):
        selection = self.watchlist_box.curselection()
        if not selection:
            messagebox.showwarning("Select Ticker", "Select a ticker from the watchlist first.")
            return
        ticker = self.watchlist_box.get(selection[0]).strip()
        remove_from_watchlist(ticker)
        self._refresh_watchlist()

    def _load_from_watchlist(self, event):
        selection = self.watchlist_box.curselection()
        if selection:
            ticker = self.watchlist_box.get(selection[0]).strip()
            self.ticker_entry.delete(0, tk.END)
            self.ticker_entry.insert(0, ticker)
            self._run_analysis()


if __name__ == "__main__":
    app = EarningsAnalyzer()
    app.mainloop()