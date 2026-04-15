import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from datetime import timedelta

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import re
from datetime import datetime
from datetime import date
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np


class MouseActivityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mouse Activity Dashboard")

        self.file_path = None
        self.output_path = tk.StringVar()
        self.rev_var = tk.BooleanVar(value=True)
        self.km_var = tk.BooleanVar(value=True)
        self.df = None
        self.mouse_ids = []
        self.plots = []
        self.current_index = 0
        self.build_dashboard()
        self.date = 0
        self.date_number = 0
        self.dayrange = 0
        #self.reference_date = date(2026, 2, 23)
        self.reference_date = None
        self.cohort = None

        self.available_mice = []
        self.selected_mice = []
        self.mouse_select_vars = {}

        self.available_days = []
        self.selected_days = []

        self.time_ranges = [
            (pd.to_datetime('8/15/2025 10:54:00 AM'), pd.to_datetime('8/15/2025 1:03:00 PM')),
            (pd.to_datetime('8/17/2025 1:24:00 PM'), pd.to_datetime('8/17/2025 2:25:00 PM')),
            (pd.to_datetime('8/18/2025 9:24:00 AM'), pd.to_datetime('8/18/2025 11:49:00 AM')),
            (pd.to_datetime('8/19/2025 11:51:00 AM'), pd.to_datetime('8/19/2025 1:23:00 PM')),
            (pd.to_datetime('8/17/2025 1:24:00 PM'), pd.to_datetime('8/18/2025 11:49:00 AM'))
        ]



    def build_dashboard(self):
        self.main_frame = tk.Frame(self.root, padx=10, pady=10)
        self.main_frame.pack(fill="x")

        tk.Label(self.main_frame, text="Input File (.csv or .xls):").grid(row=0, column=0, sticky="w")
        self.file_entry = tk.Entry(self.main_frame, width=50)
        self.file_entry.grid(row=0, column=1, padx=5)
        tk.Button(self.main_frame, text="Browse", command=self.load_file).grid(row=0, column=2)

        tk.Label(self.main_frame, text="Output Filename:").grid(row=1, column=0, sticky="w")
        self.output_entry = tk.Entry(self.main_frame, width=50, textvariable=self.output_path)
        self.output_entry.grid(row=1, column=1, padx=5)
        tk.Button(self.main_frame, text="Save As", command=self.select_output_path).grid(row=1, column=2)

        tk.Checkbutton(self.main_frame, text="Show Revolutions", variable=self.rev_var, command=self.update_plots).grid(row=2, column=0, sticky="w")
        tk.Checkbutton(self.main_frame, text="Show Distance (km)", variable=self.km_var, command=self.update_plots).grid(row=2, column=1, sticky="w")

        # button row 1
        tk.Button(self.main_frame, text="24h distance monitor per Mouse", command=self.Daily_Data_per_Mouse).grid(row=3, column=0, pady=10)
        tk.Button(self.main_frame, text="24h bout monitor per Mouse", command=self.Bout_averaged_Rev_per_day).grid(row=3, column=1, pady=10)
        tk.Button(self.main_frame, text="Save Plots", command=self.save_plots).grid(row=3, column=2, pady=10)

        tk.Label(self.main_frame, text="output: multiple pdfs, each showing\nrunning distance of one mouse spanning a 24-hr cycle").grid(row=4, column=0)
        tk.Label(self.main_frame, text="output: multiple pdfs, each showing\nbout activity (in rev) of one mouse spanning a 24-hr cycle\n").grid(row=4, column=1)
        tk.Label(self.main_frame, text="+++++++++++++++++++++++++++++++++++++\n").grid(row=4, column=2)

        # button row 2
        tk.Button(self.main_frame, text="Day1-X Totally distance comparison", command=self.compare_activity_sum_across_days).grid(row=5, column=0, pady=10)
        tk.Button(self.main_frame, text="24h distance monitor per day", command=self.distance_comparison_each_day).grid(row=5, column=1, pady=10)
        tk.Button(self.main_frame, text="Bunch Save", command=self.bunch_save).grid(row=5, column=2, pady=10)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: one plot summarizing total distance that each mouse run on each day\n").grid(row=6, column=0)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: pdf, one fig per day, distance of all mice on y axis, 24h time series on x\n").grid(row=6, column=1)
        tk.Label(self.main_frame, text="+++++++++++++++++++++++++++++++++++++\n").grid(row=6, column=2)

        # button row 3
        tk.Button(self.main_frame, text="Hist Bout Rev Count", command=self.hist_bouts_ct_per_min).grid(row=7, column=0, pady=10)
        tk.Button(self.main_frame, text="Hist Bout Rev Count - Daytime Only", command=self.daytime_hist_bouts_ct_per_min).grid(row=7, column=1, pady=10)
        tk.Button(self.main_frame, text="Hist Bout Rev Count - Nighttime Only", command=self.nighttime_hist_bouts_ct_per_min).grid(row=7, column=2, pady=10)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: histograms_bout_count_each_day.pdf, one page per day\n each page contains hist subplots of individual mice's bout counts\n").grid(row=8, column=0)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: histograms_bout_count_each_day_(daytime).pdf\n").grid(row=8, column=1)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: histograms_bout_count_each_day_(nighttime).pdf\n").grid(row=8, column=2)

        # button row 4
        tk.Button(self.main_frame, text="Hist Bout Duration/Day", command=self.hist_bouts_duration).grid(row=9, column=0, pady=10)
        tk.Button(self.main_frame, text="Hist Bout Duration/Day - Daytime Only", command=self.daytime_hist_bouts_duration).grid(row=9, column=1, pady=10)
        tk.Button(self.main_frame, text="Hist Bout Duration/Day - Nighttime Only", command=self.nighttime_hist_bouts_duration).grid(row=9, column=2, pady=10)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: histograms_bout_duration_each_day.pdf, one page per day\n each page contains hist subplots of individual mice's bout durations\n").grid(row=10, column=0)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: histograms_bout_duration_each_day_(daytime).pdf").grid(row=10, column=1)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: histograms_bout_duration_each_day_(nighttime).pdf").grid(row=10, column=2)

        # button row 5
        tk.Button(self.main_frame, text="Hist Bout Duration/Mouse", command=self.hist_bouts_duration_p_mouse).grid(row=11, column=0, pady=10)
        tk.Button(self.main_frame, text="Hist Bout Duration/Mouse - Daytime Only", command=self.daytime_hist_bouts_duration_p_mouse).grid(row=11, column=1, pady=10)
        tk.Button(self.main_frame, text="Hist Bout Duration/Mouse - Nighttime Only", command=self.nighttime_hist_bouts_duration_p_mouse).grid(row=11, column=2, pady=10)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: histograms_bout_duration_each_mouse.pdf, one page per mouse\n each page "
                                       "contains hist subplots of its bout durations across days\n").grid(row=12, column=0)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: histograms_bout_duration_each_mouse_(daytime).pdf").grid(row=12, column=1)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: histograms_bout_duration_each_mouse_(nighttime).pdf").grid(row=12, column=2)

        # button row 6
        tk.Button(self.main_frame, text="Bar Plot - Bout Duration on/not on Wheel", command=self.plot_time_on_wheel_summary).grid(row=13, column=0, pady=10)
        tk.Button(self.main_frame, text="Weekly report", command=self.plot_temporal_two_week_splits).grid(row=13, column=1, pady=10)
        tk.Button(self.main_frame, text="Actogram", command=self.plot_double_plotted_actogram).grid(row=13, column=2, pady=10)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: 2 Bar Plots (l:ctr vs SNr vs GPi; r: ctr vs ctr vs SNc)\n").grid(row=14, column=0)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: \n").grid(row=14, column=1)
        tk.Label(self.main_frame, text="---\n").grid(row=14, column=2)

        # In build_dashboard(), add this button:
        tk.Button(self.main_frame, text="Bout Statistics Summary (4 Figs)",
                  command=self.generate_bout_statistics_summary_multi_cohort).grid(row=14, column=1, pady=10)

        #select mouse
        tk.Label(self.main_frame, text="Select mice to display:").grid(row=15, column=1, sticky="w")

        self.mouse_listbox = tk.Listbox(self.main_frame, selectmode="multiple", height=6, exportselection=False)
        self.mouse_listbox.grid(row=16, column=1, rowspan=2, sticky="nsew", padx=5)

        tk.Button(self.main_frame, text="Apply Mouse Selection", command=self.apply_mouse_selection) \
            .grid(row=18, column=1, pady=5, sticky="ew")

        tk.Label(self.main_frame, text="Select DayIndex to display:").grid(
            row=15, column=2, sticky="w"
        )

        self.day_listbox = tk.Listbox(
            self.main_frame,
            selectmode="multiple",
            height=8,
            exportselection=False
        )
        self.day_listbox.grid(row=16, column=2, rowspan=2, sticky="nsew", padx=5)

        tk.Button(
            self.main_frame,
            text="Apply Day Selection",
            command=self.apply_day_selection
        ).grid(row=18, column=2, pady=5, sticky="ew")

        #canvas
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill="both", expand=True)
        self.canvas_area = tk.Canvas(self.canvas_frame)
        self.canvas_area.pack(fill="both", expand=True)

        self.nav_frame = tk.Frame(self.root)
        self.nav_frame.pack(pady=5)
        self.prev_button = tk.Button(self.nav_frame, text="<< Prev", command=self.show_prev_plot)
        self.prev_button.pack(side="left", padx=5)
        self.next_button = tk.Button(self.nav_frame, text="Next >>", command=self.show_next_plot)
        self.next_button.pack(side="left", padx=5)

    def load_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Data Files", "*.csv *.xls *.xlsx")])
        if self.file_path:
            if self.file_path.endswith(".xls") | self.file_path.endswith(".csv"):
                self.cohort = int(self.file_path[-5:-4])
            else:
                self.cohort = int(self.file_path[-6:-5])
            if self.cohort == 1:
                self.mouse_label = ["SC01(Control)", "LM45(SNr-DTA)", "SC02(GPi-DTA)"]
            elif self.cohort == 2:
                self.mouse_label = ["SC04(SNr-DTA)", "SC05(SNr-DTA)", "SC06(SNr-DTA)", "SC07(Control)", "SC08(Control)"]
            elif self.cohort == 3:
                self.mouse_label = ["SC09(SNr-DTA)", "SC10(SNr-DTA)", "SC11(SNr-DTA)", "SC12(SNr-DTA)", "SC13(Control)",
                                    "SC14(Control)", "SC15(Control)"]
            elif self.cohort == 4:
                self.mouse_label = ["SC29(SNr-DTA)", "SC30(SNr-DTA)", "SC31(SNr-DTA)", "SC32(SNr-DTA)", "SC33(Control)",
                                    "SC34(Control)", "SC35(Control)"]

            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, self.file_path)
            self.load_dataframe()



    def select_output_path(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")])
        if path:
            self.output_path.set(path)


    def customized_modifications_on_df(self):
        cols_to_zero = ["1 8 3 rev", "1 8 3 km"]

        mask = self.df["DayIndex"] >= 18
        self.df.loc[mask, cols_to_zero] = 0

    def load_dataframe(self):
        try:
            if self.file_path.endswith(".xls") | self.file_path.endswith(".xlsx"):
                try:
                    df = pd.read_csv(self.file_path, skiprows=10, sep="\t")
                except Exception:
                    df = pd.read_csv(self.file_path, skiprows=10)
            elif self.file_path.endswith(".csv"):
                df = pd.read_csv(self.file_path, skiprows=10)
            else:
                raise ValueError("Unsupported file format")

            df = df.dropna(how='all')
            df = df.dropna(axis=1, how='all')
            df.columns = [col.strip() for col in df.columns]
            if 'Bin' not in df.columns:
                raise ValueError("Missing 'Bin' column")

            mouse_ids = sorted(set(col.split()[2] for col in df.columns if col.startswith('1 8')))
            mouse_ids = [int(m) for m in mouse_ids if str(m).isdigit()]
            self.available_mice = mouse_ids
            # default: select all
            self.selected_mice = mouse_ids.copy()

            self.mouse_listbox.delete(0, tk.END)
            for mid in self.available_mice:
                self.mouse_listbox.insert(tk.END, str(mid))

            # select all by default
            for i in range(len(self.available_mice)):
                self.mouse_listbox.selection_set(i)

            self.mouse_ids = mouse_ids
            self.num_mice = len(mouse_ids)


            df['Bin'] = pd.to_datetime(df['Bin'], format="mixed", errors='coerce')
            df = df.dropna(subset=['Bin'])  # need clean Bins before taking min
            self.reference_date = df['Bin'].dt.normalize().min().date()
            if self.cohort == 3:
                self.reference_date = df['Bin'].dt.normalize().min().date() - timedelta(days=8)


            ref_ts = pd.Timestamp(self.reference_date)
            df['DateIndex'] = (df['Bin'].dt.normalize() - ref_ts).dt.days
            df['Date'] = df['Bin'].dt.date
            for col in df.columns:
                if col != 'Bin':
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna(subset=['Bin'])
            df = df.dropna(axis=1, how='all')

            #what days are gonna to be used
            days = sorted(df["DateIndex"].dropna().unique().astype(int))
            self.available_days = days
            self.selected_days = days.copy()
            self.day_listbox.delete(0, tk.END)
            for d in days:
                self.day_listbox.insert(tk.END, f"D{d}")

            # select all by default
            for i in range(len(days)):
                self.day_listbox.selection_set(i)

            self.df = df

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def Daily_Data_per_Mouse(self):
        if self.df is None or self.df.empty:
            messagebox.showinfo("No Data", "No dataframe loaded.")
            return
        if "DateIndex" not in self.df.columns:
            messagebox.showerror("Missing Column", "Your dataframe has no 'DateIndex' column.")
            return\

        bar_width = 1 / (24 * 60)  # 1 minute in days
        df = self.df.sort_values(["DateIndex", "Bin"]).copy()

        # --- collect figures per mouse ---
        plots_by_mouse = {mid: [] for mid in self.get_selected_mice()}

        for day_idx, day_df in df.groupby("DateIndex", sort=True):
            for mid in self.get_selected_mice():
                km_col = f"1 8 {mid} km"
                if not (self.km_var.get() and km_col in day_df.columns):
                    continue

                fig, ax = plt.subplots(figsize=(8, 4))

                ax.bar(
                    day_df["Bin"],
                    day_df[km_col] * 1000,
                    color="tab:orange",
                    width=bar_width,
                    align="center"
                )

                ax.set_ylabel("Distance (m)")
                ax.set_xlabel("Time")

                ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
                ax.set_xlim(day_df["Bin"].min(), day_df["Bin"].max())

                try:
                    mouse_name = self.mouse_label[int(mid) - 1]
                except Exception:
                    mouse_name = f"Mouse {mid}"

                ax.set_title(f"Cohort {self.cohort} - D{int(day_idx)} – Daily Activity – {mouse_name}")
                ax.grid(True, axis="y", linestyle="--", alpha=0.35)
                fig.autofmt_xdate()
                fig.tight_layout()

                plots_by_mouse[mid].append(fig)


        for mid, figs in plots_by_mouse.items():
            if not figs:
                continue
            pdf_path = f"./p1c{self.cohort}/Mouse_{mid}_Daily_Activity.pdf"
            with PdfPages(pdf_path) as pdf:
                for fig in figs:
                    pdf.savefig(fig)
                    plt.close(fig)

    def plot_bout_statistics(self):
        """
        Generate plots for bout statistics from the CSV file created by Bout_averaged_Rev_per_day.
        Creates one PDF per mouse with 4 plots per day:
          1. Total Bout Time (bar chart)
          2. Most Frequent Bout Duration (bar chart)
          3. Total Bout Revolutions (bar chart)
          4. Number of Bouts (bar chart)
        """
        import os

        # Load the CSV file
        csv_path = f"./p1c{self.cohort}/Cohort{self.cohort}_Bout_Statistics.csv"

        if not os.path.exists(csv_path):
            messagebox.showerror("File Not Found",
                                 f"Bout statistics CSV not found at: {csv_path}\n"
                                 "Please run 'Bout_averaged_Rev_per_day' first.")
            return

        try:
            bout_df = pd.read_csv(csv_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")
            return

        # Validate required columns
        required_cols = ['MouseID', 'MouseLabel', 'DayIndex', 'TotalBoutTime_min',
                         'MostFrequentBoutDuration_min', 'TotalBoutRevs', 'NumberOfBouts']
        missing = [c for c in required_cols if c not in bout_df.columns]
        if missing:
            messagebox.showerror("Missing Columns",
                                 f"CSV is missing required columns: {missing}")
            return

        # Get unique mice from CSV
        selected_mice = self.get_selected_mice()

        if not selected_mice:
            messagebox.showinfo("No Data", "No selected mice found in the CSV file.")
            return

        # --- Collect figures per mouse ---
        plots_by_mouse = {mid: [] for mid in selected_mice}

        for mid in selected_mice:
            mouse_data = bout_df[bout_df['MouseID'] == mid].sort_values('DayIndex')

            if mouse_data.empty:
                continue

            mouse_name = mouse_data['MouseLabel'].iloc[0] if 'MouseLabel' in mouse_data.columns else f"Mouse {mid}"

            # Group by day to create one page per day
            for day_idx, day_data in mouse_data.groupby('DayIndex'):
                # Create a figure with 2x2 subplots
                fig, axes = plt.subplots(2, 2, figsize=(12, 10))
                fig.suptitle(f"Cohort {self.cohort} - D{int(day_idx)} - Bout Statistics - {mouse_name}",
                             fontsize=14, fontweight='bold')

                # Extract values (should be single row per day)
                total_bout_time = day_data['TotalBoutTime_min'].iloc[0]
                most_freq_duration = day_data['MostFrequentBoutDuration_min'].iloc[0]
                total_bout_revs = day_data['TotalBoutRevs'].iloc[0]
                num_bouts = day_data['NumberOfBouts'].iloc[0]

                # Plot 1: Total Bout Time
                ax1 = axes[0, 0]
                ax1.bar(['Total Bout Time'], [total_bout_time], color='tab:blue', width=0.5)
                ax1.set_ylabel('Time (minutes)', fontsize=11)
                ax1.set_title('Total Time Spent in Bouts', fontsize=12, fontweight='bold')
                ax1.grid(True, axis='y', linestyle='--', alpha=0.35)
                ax1.set_ylim(0, max(total_bout_time * 1.2, 1))

                # Plot 2: Most Frequent Bout Duration
                ax2 = axes[0, 1]
                ax2.bar(['Most Frequent Duration'], [most_freq_duration], color='tab:green', width=0.5)
                ax2.set_ylabel('Duration (minutes)', fontsize=11)
                ax2.set_title('Most Frequent Bout Duration', fontsize=12, fontweight='bold')
                ax2.grid(True, axis='y', linestyle='--', alpha=0.35)
                ax2.set_ylim(0, max(most_freq_duration * 1.2, 1))

                # Plot 3: Total Bout Revolutions
                ax3 = axes[1, 0]
                ax3.bar(['Total Bout Revs'], [total_bout_revs], color='tab:orange', width=0.5)
                ax3.set_ylabel('Revolutions', fontsize=11)
                ax3.set_title('Total Revolutions During Bouts', fontsize=12, fontweight='bold')
                ax3.grid(True, axis='y', linestyle='--', alpha=0.35)
                ax3.set_ylim(0, max(total_bout_revs * 1.2, 1))

                # Plot 4: Number of Bouts
                ax4 = axes[1, 1]
                ax4.bar(['Number of Bouts'], [num_bouts], color='tab:red', width=0.5)
                ax4.set_ylabel('Count', fontsize=11)
                ax4.set_title('Number of Bouts', fontsize=12, fontweight='bold')
                ax4.grid(True, axis='y', linestyle='--', alpha=0.35)
                ax4.set_ylim(0, max(num_bouts * 1.2, 1))

                # Add text annotations with values
                ax1.text(0, total_bout_time, f'{total_bout_time:.1f} min',
                         ha='center', va='bottom', fontsize=10, fontweight='bold')
                ax2.text(0, most_freq_duration, f'{most_freq_duration:.0f} min',
                         ha='center', va='bottom', fontsize=10, fontweight='bold')
                ax3.text(0, total_bout_revs, f'{total_bout_revs:.1f}',
                         ha='center', va='bottom', fontsize=10, fontweight='bold')
                ax4.text(0, num_bouts, f'{num_bouts:.0f}',
                         ha='center', va='bottom', fontsize=10, fontweight='bold')

                # Remove x-tick labels for cleaner look
                for ax in axes.flatten():
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
                    ax.tick_params(axis='x', which='both', bottom=False, labelbottom=False)

                fig.tight_layout(rect=[0, 0, 1, 0.97])
                plots_by_mouse[mid].append(fig)

        # --- Save one PDF per mouse ---
        for mid, figs in plots_by_mouse.items():
            if not figs:
                continue

            pdf_path = f"./p1c{self.cohort}/Mouse_{mid}_Bout_Statistics.pdf"
            with PdfPages(pdf_path) as pdf:
                for fig in figs:
                    pdf.savefig(fig)
                    plt.close(fig)

    def generate_bout_statistics_summary_multi_cohort(self):
        """
        Generate a 3-figure PDF summarizing bout statistics across multiple cohorts:
        Figure 1: Bout speed distribution (revs/min)
        Figure 2: Bout duration distribution (minutes)
        Figure 3: Inter-bout interval distribution (minutes)

        Each figure has 2×2 subfigures showing individual cohorts.
        Histogram style matches MATLAB code (outline/stairs style).

        FILTERS:
        - Only uses days 8-21
        - Skips mouse 3 in cohort 1
        - Skips mouse 4 in cohort 2
        - Skips mouse 7 in cohort 4
        """
        from matplotlib.backends.backend_pdf import PdfPages
        from tkinter import filedialog

        # --- Load multiple cohort files ---
        file_paths = filedialog.askopenfilenames(
            title="Select cohort data files (multiple cohorts)",
            filetypes=[("Data Files", "*.csv *.xls *.xlsx")]
        )

        if not file_paths:
            messagebox.showinfo("No Files", "No files selected.")
            return

        print(f"Loading {len(file_paths)} cohort file(s)...")

        # Storage for all cohorts
        cohort_data_dict = {}  # {cohort_num: {'df': df, 'labels': labels, 'snr_mice': [], 'ctrl_mice': []}}

        # Define day range filter
        DAY_MIN = 8
        DAY_MAX = 21

        # Load each cohort file
        for file_path in file_paths:
            try:
                # Determine cohort number from filename
                if file_path.endswith(".xls") or file_path.endswith(".csv"):
                    cohort_num = int(file_path[-5:-4])
                else:
                    cohort_num = int(file_path[-6:-5])

                # Set mouse labels for this cohort
                if cohort_num == 1:
                    mouse_labels = ["SC01(Control)", "LM45(SNr-DTA)", "SC02(GPi-DTA)"]
                elif cohort_num == 2:
                    mouse_labels = ["SC04(SNr-DTA)", "SC05(SNr-DTA)", "SC06(SNr-DTA)",
                                    "SC07(Control)", "SC08(Control)"]
                elif cohort_num == 3:
                    mouse_labels = ["SC09(SNr-DTA)", "SC10(SNr-DTA)", "SC11(SNr-DTA)",
                                    "SC12(SNr-DTA)", "SC13(Control)", "SC14(Control)", "SC15(Control)"]
                elif cohort_num == 4:
                    mouse_labels = ["SC29(SNr-DTA)", "SC30(SNr-DTA)", "SC31(SNr-DTA)",
                                    "SC32(SNr-DTA)", "SC33(Control)", "SC34(Control)", "SC35(Control)"]
                else:
                    mouse_labels = []

                # Load dataframe
                if file_path.endswith(".xls") or file_path.endswith(".xlsx"):
                    try:
                        df = pd.read_csv(file_path, skiprows=10, sep="\t")
                    except Exception:
                        df = pd.read_csv(file_path, skiprows=10)
                elif file_path.endswith(".csv"):
                    df = pd.read_csv(file_path, skiprows=10)
                else:
                    continue

                # Clean dataframe
                df = df.dropna(how='all').dropna(axis=1, how='all')
                df.columns = [col.strip() for col in df.columns]

                if 'Bin' not in df.columns:
                    print(f"Warning: No 'Bin' column in cohort {cohort_num}, skipping")
                    continue

                # Process timestamps
                df['Bin'] = pd.to_datetime(df['Bin'], format="mixed", errors='coerce')
                df = df.dropna(subset=['Bin'])

                # Create DateIndex
                reference_date = df['Bin'].dt.normalize().min().date()
                if cohort_num == 3:
                    from datetime import timedelta
                    reference_date = reference_date - timedelta(days=8)

                ref_ts = pd.Timestamp(reference_date)
                df['DateIndex'] = (df['Bin'].dt.normalize() - ref_ts).dt.days

                # Filter: Only keep days 8-21
                df = df[(df['DateIndex'] >= DAY_MIN) & (df['DateIndex'] <= DAY_MAX)]

                if df.empty:
                    print(f"Warning: No data in day range {DAY_MIN}-{DAY_MAX} for cohort {cohort_num}")
                    continue

                # Get mouse IDs
                mouse_ids = sorted(set(col.split()[2] for col in df.columns if col.startswith('1 8')))
                mouse_ids = [int(m) for m in mouse_ids if str(m).isdigit()]

                # Filter: Skip specific mice per cohort
                excluded_mice = []
                if cohort_num == 1 and 3 in mouse_ids:
                    mouse_ids.remove(3)
                    excluded_mice.append(3)
                if cohort_num == 2 and 4 in mouse_ids:
                    mouse_ids.remove(4)
                    excluded_mice.append(4)
                if cohort_num == 4 and 7 in mouse_ids:
                    mouse_ids.remove(7)
                    excluded_mice.append(7)

                # Separate by group
                snr_mice = []
                ctrl_mice = []

                for mid in mouse_ids:
                    if mid - 1 < len(mouse_labels):
                        label = mouse_labels[mid - 1]
                        if "SNr" in label or "DTA" in label:
                            snr_mice.append(mid)
                        elif "Control" in label:
                            ctrl_mice.append(mid)

                # Store cohort data
                cohort_data_dict[cohort_num] = {
                    'df': df,
                    'labels': mouse_labels,
                    'snr_mice': snr_mice,
                    'ctrl_mice': ctrl_mice
                }

                print(f"  Loaded Cohort {cohort_num}: SNr-DTA={len(snr_mice)}, Control={len(ctrl_mice)}")
                if excluded_mice:
                    print(f"    Excluded mice: {excluded_mice}")

            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                continue

        if not cohort_data_dict:
            messagebox.showerror("Error", "No cohort files loaded successfully.")
            return

        cohort_numbers = sorted(cohort_data_dict.keys())
        print(f"\nSuccessfully loaded {len(cohort_numbers)} cohort(s): {cohort_numbers}")

        # --- Helper function: Analyze bouts for one mouse ---
        def analyze_mouse_bouts(mouse_df, rev_col, threshold=10):
            """Analyze bout statistics for a single mouse across all days."""
            bout_speeds = []
            bout_durations = []
            inter_bout_intervals = []

            for day, day_df in mouse_df.groupby('DateIndex'):
                day_df = day_df.sort_values('Bin').copy()

                if rev_col not in day_df.columns:
                    continue

                revs = pd.to_numeric(day_df[rev_col], errors='coerce').fillna(0.0)
                revs = revs.where(revs >= threshold, 0.0)

                active = revs > 0
                if not active.any():
                    continue

                run_id = (active != active.shift(fill_value=False)).cumsum()

                bout_end_indices = []

                for run, group in revs.groupby(run_id):
                    if not active.loc[group.index].iloc[0]:
                        continue

                    duration = len(group)
                    bout_durations.append(duration)

                    speed = group.mean()
                    bout_speeds.append(speed)

                    bout_end_indices.append(group.index[-1])

                # Inter-bout intervals
                if len(bout_end_indices) > 1:
                    for i in range(len(bout_end_indices) - 1):
                        current_end_idx = bout_end_indices[i]
                        next_start_idx = None

                        for run, group in revs.groupby(run_id):
                            if active.loc[group.index].iloc[0] and group.index[0] > current_end_idx:
                                next_start_idx = group.index[0]
                                break

                        if next_start_idx is not None:
                            interval = day_df.loc[next_start_idx, 'Bin'] - day_df.loc[current_end_idx, 'Bin']
                            interval_minutes = interval.total_seconds() / 60
                            inter_bout_intervals.append(interval_minutes)

            return bout_speeds, bout_durations, inter_bout_intervals

        # --- Collect data for each cohort ---
        threshold = 10
        cohort_bout_data = {}  # {cohort_num: {'snr_speeds': [], ...}}

        for cohort_num in cohort_numbers:
            cohort_info = cohort_data_dict[cohort_num]
            df = cohort_info['df']
            snr_mice = cohort_info['snr_mice']
            ctrl_mice = cohort_info['ctrl_mice']

            snr_bout_speeds = []
            snr_bout_durations = []
            snr_inter_bout_intervals = []

            ctrl_bout_speeds = []
            ctrl_bout_durations = []
            ctrl_inter_bout_intervals = []

            # Process SNr-DTA mice
            for mid in snr_mice:
                rev_col = f"1 8 {mid} rev"
                if rev_col not in df.columns:
                    continue

                mouse_df = df[['Bin', 'DateIndex', rev_col]].copy()
                speeds, durations, intervals = analyze_mouse_bouts(mouse_df, rev_col, threshold)

                snr_bout_speeds.extend(speeds)
                snr_bout_durations.extend(durations)
                snr_inter_bout_intervals.extend(intervals)

            # Process Control mice
            for mid in ctrl_mice:
                rev_col = f"1 8 {mid} rev"
                if rev_col not in df.columns:
                    continue

                mouse_df = df[['Bin', 'DateIndex', rev_col]].copy()
                speeds, durations, intervals = analyze_mouse_bouts(mouse_df, rev_col, threshold)

                ctrl_bout_speeds.extend(speeds)
                ctrl_bout_durations.extend(durations)
                ctrl_inter_bout_intervals.extend(intervals)

            cohort_bout_data[cohort_num] = {
                'snr_speeds': snr_bout_speeds,
                'snr_durations': snr_bout_durations,
                'snr_intervals': snr_inter_bout_intervals,
                'ctrl_speeds': ctrl_bout_speeds,
                'ctrl_durations': ctrl_bout_durations,
                'ctrl_intervals': ctrl_inter_bout_intervals,
                'n_snr': len(snr_mice),
                'n_ctrl': len(ctrl_mice)
            }

            print(f"Cohort {cohort_num}: SNr {len(snr_bout_speeds)} bouts, Ctrl {len(ctrl_bout_speeds)} bouts")

        # --- Create 3-figure PDF with 2×2 subplots per figure ---
        cohort_str = "_".join([f"C{c}" for c in cohort_numbers])
        pdf_path = f"./Multi_Cohort_{cohort_str}_Bout_Statistics_D{DAY_MIN}-{DAY_MAX}.pdf"

        # Colors matching MATLAB
        snr_color = (0.4, 0.7, 0.4)  # Green for SNr-DTA
        ctrl_color = (0.3, 0.3, 0.3)  # Gray for Control

        with PdfPages(pdf_path) as pdf:

            # ==================== FIGURE 1: BOUT SPEED DISTRIBUTION ====================
            fig1, axes1 = plt.subplots(2, 2, figsize=(14, 12))
            axes1 = axes1.flatten()

            speed_bins = np.arange(10, 160, 5)

            for idx, cohort_num in enumerate(cohort_numbers):
                if idx >= 4:
                    break

                ax = axes1[idx]
                data = cohort_bout_data[cohort_num]

                if data['snr_speeds']:
                    ax.hist(data['snr_speeds'], bins=speed_bins,
                            histtype='step', edgecolor=snr_color, linewidth=2,
                            label=f"SNr-DTA (n={len(data['snr_speeds'])} bouts)")
                    snr_mean = np.mean(data['snr_speeds'])
                    ax.axvline(snr_mean, color=snr_color, linewidth=2,
                               linestyle='--', alpha=0.7)
                    ax.text(snr_mean, 1.0, f'{snr_mean:.1f}',
                            transform=ax.get_xaxis_transform(),
                            color=snr_color, fontsize=8, fontweight='bold',
                            ha='left', va='bottom', rotation=90)

                if data['ctrl_speeds']:
                    ax.hist(data['ctrl_speeds'], bins=speed_bins,
                            histtype='step', edgecolor=ctrl_color, linewidth=2,
                            label=f"Control (n={len(data['ctrl_speeds'])} bouts)")
                    ctrl_mean = np.mean(data['ctrl_speeds'])
                    ax.axvline(ctrl_mean, color=ctrl_color, linewidth=2,
                               linestyle='--', alpha=0.7)
                    ax.text(ctrl_mean, 1.0, f'{ctrl_mean:.1f}',
                            transform=ax.get_xaxis_transform(),
                            color=ctrl_color, fontsize=8, fontweight='bold',
                            ha='left', va='bottom', rotation=90)

                ax.set_xlabel('Bout Speed (revs/min)', fontsize=11, fontweight='bold')
                ax.set_ylabel('Counts', fontsize=11, fontweight='bold')
                ax.set_title(f'Cohort {cohort_num}', fontsize=12, fontweight='bold')
                ax.legend(loc='best', fontsize=9, frameon=False)
                ax.grid(True, alpha=0.3, linestyle='--')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)

            for idx in range(len(cohort_numbers), 4):
                axes1[idx].axis('off')

            fig1.suptitle(f'Bout Speed Distribution (Days {DAY_MIN}-{DAY_MAX})',
                          fontsize=15, fontweight='bold')
            fig1.tight_layout(rect=[0, 0, 1, 0.96])
            pdf.savefig(fig1, bbox_inches='tight')
            plt.close(fig1)

            # ==================== FIGURE 2: BOUT DURATION DISTRIBUTION ====================
            fig2, axes2 = plt.subplots(2, 2, figsize=(14, 12))
            axes2 = axes2.flatten()

            duration_bins = np.arange(1, 51, 1)

            for idx, cohort_num in enumerate(cohort_numbers):
                if idx >= 4:
                    break

                ax = axes2[idx]
                data = cohort_bout_data[cohort_num]

                if data['snr_durations']:
                    ax.hist(data['snr_durations'], bins=duration_bins,
                            histtype='step', edgecolor=snr_color, linewidth=2,
                            label=f"SNr-DTA (n={len(data['snr_durations'])} bouts)")
                    snr_mean = np.mean(data['snr_durations'])
                    ax.axvline(snr_mean, color=snr_color, linewidth=2,
                               linestyle='--', alpha=0.7)
                    ax.text(snr_mean, 1.0, f'{snr_mean:.1f}',
                            transform=ax.get_xaxis_transform(),
                            color=snr_color, fontsize=8, fontweight='bold',
                            ha='left', va='bottom', rotation=90)

                if data['ctrl_durations']:
                    ax.hist(data['ctrl_durations'], bins=duration_bins,
                            histtype='step', edgecolor=ctrl_color, linewidth=2,
                            label=f"Control (n={len(data['ctrl_durations'])} bouts)")
                    ctrl_mean = np.mean(data['ctrl_durations'])
                    ax.axvline(ctrl_mean, color=ctrl_color, linewidth=2,
                               linestyle='--', alpha=0.7)
                    ax.text(ctrl_mean, 1.0, f'{ctrl_mean:.1f}',
                            transform=ax.get_xaxis_transform(),
                            color=ctrl_color, fontsize=8, fontweight='bold',
                            ha='left', va='bottom', rotation=90)

                ax.set_xlabel('Bout Duration (minutes)', fontsize=11, fontweight='bold')
                ax.set_ylabel('Counts', fontsize=11, fontweight='bold')
                ax.set_title(f'Cohort {cohort_num}', fontsize=12, fontweight='bold')
                ax.set_xlim(1, 50)
                ax.legend(loc='best', fontsize=9, frameon=False)
                ax.grid(True, alpha=0.3, linestyle='--')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)

            for idx in range(len(cohort_numbers), 4):
                axes2[idx].axis('off')

            fig2.suptitle(f'Bout Duration Distribution (Days {DAY_MIN}-{DAY_MAX})',
                          fontsize=15, fontweight='bold')
            fig2.tight_layout(rect=[0, 0, 1, 0.96])
            pdf.savefig(fig2, bbox_inches='tight')
            plt.close(fig2)

            # ==================== FIGURE 3: INTER-BOUT INTERVAL DISTRIBUTION ====================
            fig3, axes3 = plt.subplots(2, 2, figsize=(14, 12))
            axes3 = axes3.flatten()

            for idx, cohort_num in enumerate(cohort_numbers):
                if idx >= 4:
                    break

                ax = axes3[idx]
                data = cohort_bout_data[cohort_num]

                # Filter intervals to start from 1 minute
                snr_intervals_filtered = [x for x in data['snr_intervals'] if x >= 1]
                ctrl_intervals_filtered = [x for x in data['ctrl_intervals'] if x >= 1]

                max_interval = max(max(snr_intervals_filtered) if snr_intervals_filtered else 1,
                                   max(ctrl_intervals_filtered) if ctrl_intervals_filtered else 1)

                # Bins starting from 1 minute
                interval_bins = np.concatenate([
                    np.arange(1, 10, 0.5),  # 1-10 min: 0.5 min bins
                    np.arange(10, 60, 5),  # 10-60 min: 5 min bins
                    np.logspace(np.log10(60), np.log10(min(max_interval + 1, 1440)), 20)  # >60 min: log scale
                ])

                if snr_intervals_filtered:
                    ax.hist(snr_intervals_filtered, bins=interval_bins,
                            histtype='step', edgecolor=snr_color, linewidth=2,
                            label=f"SNr-DTA (n={len(snr_intervals_filtered)} intervals)")
                    snr_median = np.median(snr_intervals_filtered)
                    ax.axvline(snr_median, color=snr_color, linewidth=2,
                               linestyle='--', alpha=0.7)
                    ax.text(snr_median, 1.0, f'{snr_median:.1f}',
                            transform=ax.get_xaxis_transform(),
                            color=snr_color, fontsize=8, fontweight='bold',
                            ha='left', va='bottom', rotation=90)

                if ctrl_intervals_filtered:
                    ax.hist(ctrl_intervals_filtered, bins=interval_bins,
                            histtype='step', edgecolor=ctrl_color, linewidth=2,
                            label=f"Control (n={len(ctrl_intervals_filtered)} intervals)")
                    ctrl_median = np.median(ctrl_intervals_filtered)
                    ax.axvline(ctrl_median, color=ctrl_color, linewidth=2,
                               linestyle='--', alpha=0.7)
                    ax.text(ctrl_median, 1.0, f'{ctrl_median:.1f}',
                            transform=ax.get_xaxis_transform(),
                            color=ctrl_color, fontsize=8, fontweight='bold',
                            ha='left', va='bottom', rotation=90)

                ax.set_xlabel('Inter-Bout Interval (minutes)', fontsize=11, fontweight='bold')
                ax.set_ylabel('Counts', fontsize=11, fontweight='bold')
                ax.set_title(f'Cohort {cohort_num}', fontsize=12, fontweight='bold')
                ax.set_xscale('log')
                ax.set_xlim(1, None)  # Start x-axis at 1
                ax.legend(loc='best', fontsize=9, frameon=False)
                ax.grid(True, alpha=0.3, linestyle='--')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)

            for idx in range(len(cohort_numbers), 4):
                axes3[idx].axis('off')

            fig3.suptitle(f'Inter-Bout Interval Distribution (Days {DAY_MIN}-{DAY_MAX})',
                          fontsize=15, fontweight='bold')
            fig3.tight_layout(rect=[0, 0, 1, 0.96])
            pdf.savefig(fig3, bbox_inches='tight')
            plt.close(fig3)

            # ==================== FIGURE 4: WITHIN-BOUT ACCELERATION DISTRIBUTION ====================
            # For each pair of consecutive active 1-min bins within a bout, compute
            # delta_speed = speed[t] - speed[t-1]  (revs/min per minute).
            # Negative = deceleration, positive = acceleration.

            # Collect per-cohort acceleration values
            cohort_accel_data = {}

            for cohort_num in cohort_numbers:
                cohort_info = cohort_data_dict[cohort_num]
                df_c = cohort_info['df']
                snr_mice_c = cohort_info['snr_mice']
                ctrl_mice_c = cohort_info['ctrl_mice']

                def collect_accelerations(mouse_list, df_src, threshold=10):
                    accels = []
                    for mid in mouse_list:
                        rev_col = f"1 8 {mid} rev"
                        if rev_col not in df_src.columns:
                            continue
                        for day, day_df in df_src.groupby('DateIndex'):
                            day_df = day_df.sort_values('Bin').copy()
                            revs = pd.to_numeric(day_df[rev_col], errors='coerce').fillna(0.0)
                            revs = revs.where(revs >= threshold, 0.0).values
                            active = revs > 0
                            # Walk through consecutive active pairs
                            for i in range(1, len(revs)):
                                if active[i] and active[i - 1]:
                                    accels.append(revs[i] - revs[i - 1])
                    return accels

                cohort_accel_data[cohort_num] = {
                    'snr': collect_accelerations(snr_mice_c, df_c),
                    'ctrl': collect_accelerations(ctrl_mice_c, df_c),
                }

            fig4, axes4 = plt.subplots(2, 2, figsize=(14, 12))
            axes4 = axes4.flatten()

            # Symmetric bins centred on 0, in steps of 2 rev/min
            accel_bins = np.arange(-80, 82, 2)

            for idx, cohort_num in enumerate(cohort_numbers):
                if idx >= 4:
                    break

                ax = axes4[idx]
                adata = cohort_accel_data[cohort_num]

                if adata['snr']:
                    ax.hist(adata['snr'], bins=accel_bins,
                            histtype='step', edgecolor=snr_color, linewidth=2,
                            label=f"SNr-DTA (n={len(adata['snr'])} transitions)")
                    snr_mean_a = np.mean(adata['snr'])
                    ax.axvline(snr_mean_a, color=snr_color, linewidth=2, linestyle='--', alpha=0.7)
                    ax.text(snr_mean_a, 1.0, f'{snr_mean_a:.2f}',
                            transform=ax.get_xaxis_transform(),
                            color=snr_color, fontsize=8, fontweight='bold',
                            ha='left', va='bottom', rotation=90)

                if adata['ctrl']:
                    ax.hist(adata['ctrl'], bins=accel_bins,
                            histtype='step', edgecolor=ctrl_color, linewidth=2,
                            label=f"Control (n={len(adata['ctrl'])} transitions)")
                    ctrl_mean_a = np.mean(adata['ctrl'])
                    ax.axvline(ctrl_mean_a, color=ctrl_color, linewidth=2, linestyle='--', alpha=0.7)
                    ax.text(ctrl_mean_a, 1.0, f'{ctrl_mean_a:.2f}',
                            transform=ax.get_xaxis_transform(),
                            color=ctrl_color, fontsize=8, fontweight='bold',
                            ha='left', va='bottom', rotation=90)

                ax.axvline(0, color='black', linewidth=1.0, linestyle='-', alpha=0.4)
                ax.set_xlabel('Δ Speed between consecutive active bins (revs/min)', fontsize=11, fontweight='bold')
                ax.set_ylabel('Counts', fontsize=11, fontweight='bold')
                ax.set_title(f'Cohort {cohort_num}', fontsize=12, fontweight='bold')
                ax.legend(loc='best', fontsize=9, frameon=False)
                ax.grid(True, alpha=0.3, linestyle='--')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)

            for idx in range(len(cohort_numbers), 4):
                axes4[idx].axis('off')

            fig4.suptitle(f'Within-Bout Acceleration Distribution (Days {DAY_MIN}-{DAY_MAX})\n'
                          f'Δ speed between consecutive 1-min active bins; negative = deceleration',
                          fontsize=14, fontweight='bold')
            fig4.tight_layout(rect=[0, 0, 1, 0.96])
            pdf.savefig(fig4, bbox_inches='tight')
            plt.close(fig4)

        print(f"\nSaved multi-cohort summary: {pdf_path}")

        # ==================== SUMMARY CSV: per-mouse light/dark ratios + Lomb-Scargle ====================
        from scipy import signal as scipy_signal

        def lomb_scargle_period(times, values, min_period=20, max_period=28):
            """Reused from plot_double_plotted_actogram. Returns (tau, power, amplitude, false_alarm_prob)."""
            mask = ~np.isnan(np.array(values, dtype=float))
            times_clean = np.array(times, dtype=float)[mask]
            values_clean = np.array(values, dtype=float)[mask]
            if len(times_clean) < 24:
                return np.nan, np.nan, np.nan, np.nan
            frequencies = np.linspace(1 / max_period, 1 / min_period, 1000)
            try:
                ls_power = scipy_signal.lombscargle(
                    times_clean, values_clean - np.mean(values_clean),
                    frequencies * 2 * np.pi, normalize=True)
                peak_idx = np.argmax(ls_power)
                tau = 1.0 / frequencies[peak_idx]
                power = ls_power[peak_idx]
                amplitude = np.sqrt(2 * power) * np.std(values_clean)
                M = len(frequencies)
                false_alarm_prob = 1 - (1 - np.exp(-power)) ** M
                return tau, power, amplitude, false_alarm_prob
            except Exception as e:
                print(f"Lomb-Scargle error: {e}")
                return np.nan, np.nan, np.nan, np.nan

        # Light = 06:00–18:00  (hours 6..17),  Dark = 18:00–06:00
        LIGHT_HOURS = set(range(6, 18))   # 6,7,...,17
        threshold = 10
        summary_rows = []

        for cohort_num in cohort_numbers:
            cohort_info = cohort_data_dict[cohort_num]
            df_c = cohort_info['df'].copy()
            all_mice = cohort_info['snr_mice'] + cohort_info['ctrl_mice']

            for mid in all_mice:
                rev_col = f"1 8 {mid} rev"
                if rev_col not in df_c.columns:
                    continue

                label = cohort_info['labels'][int(mid) - 1] if int(mid) - 1 < len(cohort_info['labels']) else f"Mouse {mid}"

                # Split rows into light / dark based on hour of Bin timestamp
                mouse_df = df_c[['Bin', 'DateIndex', rev_col]].copy()
                mouse_df[rev_col] = pd.to_numeric(mouse_df[rev_col], errors='coerce').fillna(0.0)
                mouse_df['hour'] = mouse_df['Bin'].dt.hour

                light_df = mouse_df[mouse_df['hour'].isin(LIGHT_HOURS)]
                dark_df  = mouse_df[~mouse_df['hour'].isin(LIGHT_HOURS)]

                def bout_stats_from_df(sub_df, rc, thr):
                    """Return (n_bouts, mean_speed) pooled across all days in sub_df."""
                    n_bouts = 0
                    speeds = []
                    for day, day_data in sub_df.groupby('DateIndex'):
                        day_data = day_data.sort_values('Bin')
                        revs = day_data[rc].where(day_data[rc] >= thr, 0.0)
                        active = revs > 0
                        if not active.any():
                            continue
                        run_id = (active != active.shift(fill_value=False)).cumsum()
                        for _, grp in revs.groupby(run_id):
                            if active.loc[grp.index].iloc[0]:
                                n_bouts += 1
                                speeds.append(grp.mean())
                    mean_speed = float(np.mean(speeds)) if speeds else np.nan
                    return n_bouts, mean_speed

                n_light, spd_light = bout_stats_from_df(light_df,  rev_col, threshold)
                n_dark,  spd_dark  = bout_stats_from_df(dark_df,   rev_col, threshold)

                count_ratio = (n_dark  / n_light)  if n_light  > 0 else np.nan
                speed_ratio = (spd_dark / spd_light) if (spd_light and not np.isnan(spd_light) and spd_light > 0) else np.nan

                # --- Lomb-Scargle on the full minute-resolution rev series (days 8-21) ---
                mouse_full = df_c[['Bin', rev_col]].copy()
                mouse_full[rev_col] = pd.to_numeric(mouse_full[rev_col], errors='coerce').fillna(0.0)
                mouse_full = mouse_full.sort_values('Bin')
                start_time = mouse_full['Bin'].min()
                mouse_full['HoursFromStart'] = (mouse_full['Bin'] - start_time).dt.total_seconds() / 3600.0

                tau, ls_power, ls_amplitude, ls_fap = lomb_scargle_period(
                    mouse_full['HoursFromStart'].values,
                    mouse_full[rev_col].values
                )

                summary_rows.append({
                    'Cohort':                   cohort_num,
                    'MouseID':                  mid,
                    'MouseLabel':               label,
                    'BoutCount_Light':          n_light,
                    'BoutCount_Dark':           n_dark,
                    'BoutCount_DarkLightRatio': round(count_ratio, 3) if not np.isnan(count_ratio) else np.nan,
                    'BoutSpeed_Light_revPerMin':  round(spd_light, 2) if not np.isnan(spd_light) else np.nan,
                    'BoutSpeed_Dark_revPerMin':   round(spd_dark,  2) if not np.isnan(spd_dark)  else np.nan,
                    'BoutSpeed_DarkLightRatio':  round(speed_ratio, 3) if not np.isnan(speed_ratio) else np.nan,
                    'Tau_hours':                round(tau,        2) if not np.isnan(tau)        else np.nan,
                    'LS_Power':                 round(ls_power,   4) if not np.isnan(ls_power)   else np.nan,
                    'LS_Amplitude':             round(ls_amplitude, 2) if not np.isnan(ls_amplitude) else np.nan,
                    'LS_FalseAlarmProb':        round(ls_fap,     4) if not np.isnan(ls_fap)     else np.nan,
                })

        if summary_rows:
            summary_df = pd.DataFrame(summary_rows).sort_values(['Cohort', 'MouseID'])
            csv_dir = os.path.dirname(os.path.abspath(pdf_path))
            csv_filename = f"Multi_Cohort_{cohort_str}_LightDark_Circadian_Summary_D{DAY_MIN}-{DAY_MAX}.csv"
            csv_path = os.path.join(csv_dir, csv_filename)
            summary_df.to_csv(csv_path, index=False)
            print(f"Saved per-mouse summary CSV: {csv_path}")
        else:
            csv_path = "N/A"
            print("Warning: No summary rows generated for CSV.")

        # Print summary statistics
        print("\n" + "=" * 60)
        print(f"MULTI-COHORT BOUT STATISTICS SUMMARY (Days {DAY_MIN}-{DAY_MAX})")
        print("=" * 60)

        for cohort_num in cohort_numbers:
            data = cohort_bout_data[cohort_num]
            print(f"\nCohort {cohort_num}:")
            if data['snr_speeds']:
                snr_intervals_filtered = [x for x in data['snr_intervals'] if x >= 1]
                print(f"  SNr-DTA (n={data['n_snr']} mice, {len(data['snr_speeds'])} bouts):")
                print(f"    Speed: {np.mean(data['snr_speeds']):.1f} ± {np.std(data['snr_speeds']):.1f} revs/min")
                print(f"    Duration: {np.mean(data['snr_durations']):.1f} ± {np.std(data['snr_durations']):.1f} min")
                if snr_intervals_filtered:
                    print(f"    Inter-bout interval (median): {np.median(snr_intervals_filtered):.1f} min")

            if data['ctrl_speeds']:
                ctrl_intervals_filtered = [x for x in data['ctrl_intervals'] if x >= 1]
                print(f"  Control (n={data['n_ctrl']} mice, {len(data['ctrl_speeds'])} bouts):")
                print(f"    Speed: {np.mean(data['ctrl_speeds']):.1f} ± {np.std(data['ctrl_speeds']):.1f} revs/min")
                print(f"    Duration: {np.mean(data['ctrl_durations']):.1f} ± {np.std(data['ctrl_durations']):.1f} min")
                if ctrl_intervals_filtered:
                    print(f"    Inter-bout interval (median): {np.median(ctrl_intervals_filtered):.1f} min")

        print("=" * 60 + "\n")

        # ======================================================================
        # COMBINED SINGLE-PANEL PDF
        # One figure per metric (Speed / Duration / IBI / Acceleration), each
        # showing ALL cohorts overlaid on the same axes.
        # SNr-DTA: solid green shades per cohort; Control: solid gray shades.
        # ======================================================================

        # One shade of green per cohort (SNr) and one shade of gray per cohort (Ctrl)
        snr_cohort_colors  = [(0.25, 0.65, 0.25), (0.10, 0.45, 0.10),
                              (0.55, 0.80, 0.30), (0.15, 0.55, 0.45)]
        ctrl_cohort_colors = [(0.30, 0.30, 0.30), (0.55, 0.55, 0.55),
                              (0.15, 0.15, 0.15), (0.65, 0.60, 0.50)]

        combined_pdf_path = pdf_path.replace(
            f"_Bout_Statistics_D{DAY_MIN}-{DAY_MAX}.pdf",
            f"_AllCohorts_Combined_D{DAY_MIN}-{DAY_MAX}.pdf")

        def _draw_combined_panel(ax, cohort_numbers, cohort_bout_data,
                                 snr_key, ctrl_key, bins_arr,
                                 xlabel, use_log_x=False,
                                 use_median_line=False):
            """
            Draw overlaid histograms for all cohorts onto ax.
            snr_key / ctrl_key  : key into cohort_bout_data[c] for the data list.
            bins_arr            : bin edges.
            use_median_line     : use median instead of mean for the vline label.
            """
            for c_idx, c_num in enumerate(cohort_numbers):
                data = cohort_bout_data[c_num]
                sc   = snr_cohort_colors[c_idx % len(snr_cohort_colors)]
                cc   = ctrl_cohort_colors[c_idx % len(ctrl_cohort_colors)]

                snr_vals = data[snr_key]
                ctrl_vals = data[ctrl_key]

                if snr_key == 'snr_intervals':
                    snr_vals  = [x for x in snr_vals  if x >= 1]
                if ctrl_key == 'ctrl_intervals':
                    ctrl_vals = [x for x in ctrl_vals if x >= 1]

                if snr_vals:
                    ax.hist(snr_vals, bins=bins_arr, histtype='step',
                            edgecolor=sc, linewidth=1.8,
                            label=f"C{c_num} SNr-DTA (n={len(snr_vals)})")
                    stat = np.median(snr_vals) if use_median_line else np.mean(snr_vals)
                    ax.axvline(stat, color=sc, linewidth=1.5, linestyle='--', alpha=0.8)
                    ax.text(stat, 1.0, f'{stat:.1f}',
                            transform=ax.get_xaxis_transform(),
                            color=sc, fontsize=7, fontweight='bold',
                            ha='left', va='bottom', rotation=90)

                if ctrl_vals:
                    ax.hist(ctrl_vals, bins=bins_arr, histtype='step',
                            edgecolor=cc, linewidth=1.8, linestyle='--',
                            label=f"C{c_num} Control (n={len(ctrl_vals)})")
                    stat = np.median(ctrl_vals) if use_median_line else np.mean(ctrl_vals)
                    ax.axvline(stat, color=cc, linewidth=1.5, linestyle=':', alpha=0.8)
                    ax.text(stat, 1.0, f'{stat:.1f}',
                            transform=ax.get_xaxis_transform(),
                            color=cc, fontsize=7, fontweight='bold',
                            ha='left', va='bottom', rotation=90)

            if use_log_x:
                ax.set_xscale('log')
                ax.set_xlim(1, None)
            ax.set_xlabel(xlabel, fontsize=11, fontweight='bold')
            ax.set_ylabel('Counts', fontsize=11, fontweight='bold')
            ax.legend(loc='best', fontsize=7, frameon=False, ncol=2)
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

        # Build IBI bins dynamically (need max across all cohorts)
        all_intervals = []
        for c_num in cohort_numbers:
            all_intervals += [x for x in cohort_bout_data[c_num]['snr_intervals'] if x >= 1]
            all_intervals += [x for x in cohort_bout_data[c_num]['ctrl_intervals'] if x >= 1]
        max_ibi = max(all_intervals) if all_intervals else 1440
        ibi_bins = np.concatenate([
            np.arange(1, 10, 0.5),
            np.arange(10, 60, 5),
            np.logspace(np.log10(60), np.log10(min(max_ibi + 1, 1440)), 20)
        ])

        with PdfPages(combined_pdf_path) as cpdf:

            # Figure 1: Bout Speed – all cohorts combined
            fig_cs, ax_cs = plt.subplots(figsize=(10, 6))
            _draw_combined_panel(ax_cs, cohort_numbers, cohort_bout_data,
                                 'snr_speeds', 'ctrl_speeds',
                                 np.arange(10, 160, 5),
                                 'Bout Speed (revs/min)')
            fig_cs.suptitle(f'Bout Speed – All Cohorts (Days {DAY_MIN}-{DAY_MAX})',
                            fontsize=13, fontweight='bold')
            fig_cs.tight_layout(rect=[0, 0, 1, 0.96])
            cpdf.savefig(fig_cs, bbox_inches='tight')
            plt.close(fig_cs)

            # Figure 2: Bout Duration – all cohorts combined
            fig_cd, ax_cd = plt.subplots(figsize=(10, 6))
            _draw_combined_panel(ax_cd, cohort_numbers, cohort_bout_data,
                                 'snr_durations', 'ctrl_durations',
                                 np.arange(1, 51, 1),
                                 'Bout Duration (minutes)')
            ax_cd.set_xlim(1, 50)
            fig_cd.suptitle(f'Bout Duration – All Cohorts (Days {DAY_MIN}-{DAY_MAX})',
                            fontsize=13, fontweight='bold')
            fig_cd.tight_layout(rect=[0, 0, 1, 0.96])
            cpdf.savefig(fig_cd, bbox_inches='tight')
            plt.close(fig_cd)

            # Figure 3: Inter-Bout Interval – all cohorts combined (log x, median line)
            fig_ci, ax_ci = plt.subplots(figsize=(10, 6))
            _draw_combined_panel(ax_ci, cohort_numbers, cohort_bout_data,
                                 'snr_intervals', 'ctrl_intervals',
                                 ibi_bins,
                                 'Inter-Bout Interval (minutes)',
                                 use_log_x=True, use_median_line=True)
            fig_ci.suptitle(f'Inter-Bout Interval – All Cohorts (Days {DAY_MIN}-{DAY_MAX})',
                            fontsize=13, fontweight='bold')
            fig_ci.tight_layout(rect=[0, 0, 1, 0.96])
            cpdf.savefig(fig_ci, bbox_inches='tight')
            plt.close(fig_ci)

            # Figure 4: Within-Bout Acceleration – all cohorts combined
            # Re-collect acceleration data using cohort_data_dict (already in scope)
            accel_data_combined = {}
            for c_num in cohort_numbers:
                df_c2 = cohort_data_dict[c_num]['df']

                def _collect_acc(mouse_list, df_src, thr=10):
                    acc = []
                    for mid2 in mouse_list:
                        rc2 = f"1 8 {mid2} rev"
                        if rc2 not in df_src.columns:
                            continue
                        for _, d_df in df_src.groupby('DateIndex'):
                            d_df = d_df.sort_values('Bin')
                            rv = pd.to_numeric(d_df[rc2], errors='coerce').fillna(0.0)
                            rv = rv.where(rv >= thr, 0.0).values
                            act = rv > 0
                            for ii in range(1, len(rv)):
                                if act[ii] and act[ii - 1]:
                                    acc.append(rv[ii] - rv[ii - 1])
                    return acc

                accel_data_combined[c_num] = {
                    'snr':  _collect_acc(cohort_data_dict[c_num]['snr_mice'],  df_c2),
                    'ctrl': _collect_acc(cohort_data_dict[c_num]['ctrl_mice'], df_c2),
                }

            fig_ca, ax_ca = plt.subplots(figsize=(10, 6))
            accel_bins_c = np.arange(-80, 82, 2)
            for c_idx, c_num in enumerate(cohort_numbers):
                sc = snr_cohort_colors[c_idx % len(snr_cohort_colors)]
                cc = ctrl_cohort_colors[c_idx % len(ctrl_cohort_colors)]
                snr_a = accel_data_combined[c_num]['snr']
                ctrl_a = accel_data_combined[c_num]['ctrl']
                if snr_a:
                    ax_ca.hist(snr_a, bins=accel_bins_c, histtype='step',
                               edgecolor=sc, linewidth=1.8,
                               label=f"C{c_num} SNr-DTA (n={len(snr_a)})")
                    sm = np.mean(snr_a)
                    ax_ca.axvline(sm, color=sc, linewidth=1.5, linestyle='--', alpha=0.8)
                    ax_ca.text(sm, 1.0, f'{sm:.2f}',
                               transform=ax_ca.get_xaxis_transform(),
                               color=sc, fontsize=7, fontweight='bold',
                               ha='left', va='bottom', rotation=90)
                if ctrl_a:
                    ax_ca.hist(ctrl_a, bins=accel_bins_c, histtype='step',
                               edgecolor=cc, linewidth=1.8, linestyle='--',
                               label=f"C{c_num} Control (n={len(ctrl_a)})")
                    cm = np.mean(ctrl_a)
                    ax_ca.axvline(cm, color=cc, linewidth=1.5, linestyle=':', alpha=0.8)
                    ax_ca.text(cm, 1.0, f'{cm:.2f}',
                               transform=ax_ca.get_xaxis_transform(),
                               color=cc, fontsize=7, fontweight='bold',
                               ha='left', va='bottom', rotation=90)

            ax_ca.axvline(0, color='black', linewidth=1.0, linestyle='-', alpha=0.4)
            ax_ca.set_xlabel('Δ Speed between consecutive active bins (revs/min)',
                             fontsize=11, fontweight='bold')
            ax_ca.set_ylabel('Counts', fontsize=11, fontweight='bold')
            ax_ca.legend(loc='best', fontsize=7, frameon=False, ncol=2)
            ax_ca.grid(True, alpha=0.3, linestyle='--')
            ax_ca.spines['top'].set_visible(False)
            ax_ca.spines['right'].set_visible(False)
            fig_ca.suptitle(f'Within-Bout Acceleration – All Cohorts (Days {DAY_MIN}-{DAY_MAX})',
                            fontsize=13, fontweight='bold')
            fig_ca.tight_layout(rect=[0, 0, 1, 0.96])
            cpdf.savefig(fig_ca, bbox_inches='tight')
            plt.close(fig_ca)

        print(f"Saved combined single-panel PDF: {combined_pdf_path}")

        messagebox.showinfo("Complete",
                            f"Generated multi-cohort bout statistics summary\n"
                            f"Cohorts: {', '.join([str(c) for c in cohort_numbers])}\n"
                            f"Days: {DAY_MIN}-{DAY_MAX}\n"
                            f"PDF (4 figures, 2×2): {pdf_path}\n"
                            f"PDF (4 figures, combined): {combined_pdf_path}\n"
                            f"CSV (light/dark + circadian): {csv_path}")


    def Bout_averaged_Rev_per_day(self):
        """
        Bout-averaged rev time series:
          - rev < threshold -> 0
          - consecutive nonzero runs (within each day) replaced by run mean
        Output:
          - one PDF per mouse
          - each PDF: one page per day (DateIndex)
          - x-axis: time-of-day
          - one CSV file with bout statistics per mouse per day
        """
        if self.df is None or self.df.empty:
            self.load_dataframe()
        if self.df is None or self.df.empty:
            messagebox.showinfo("No Data", "No dataframe loaded.")
            return
        if "DateIndex" not in self.df.columns:
            messagebox.showerror("Missing Column", "Your dataframe has no 'DateIndex' column.")
            return
        if "Bin" not in self.df.columns:
            messagebox.showerror("Missing Column", "Your dataframe has no 'Bin' timestamp column.")
            return

        # defines "bout" as the minimum rev counts within 1-min
        threshold = 10
        df = self.df.sort_values(["DateIndex", "Bin"]).copy()

        # --- helper: compute bout-averaged series WITHIN one day ---
        def bout_average_series(s: pd.Series, threshold: float) -> pd.Series:
            s = pd.to_numeric(s, errors="coerce").fillna(0.0)
            s = s.where(s >= threshold, 0.0)

            active = s > 0
            if active.empty:
                return s, 0, 0, []

            # consecutive run id
            run_id = (active != active.shift(fill_value=False)).cumsum()

            out = s.astype(float).copy()
            for _, idx in out.groupby(run_id).groups.items():
                # idx is index labels of this run
                if active.loc[idx].iloc[0]:  # only active runs
                    out.loc[idx] = out.loc[idx].mean()

            bout_durations = []
            bout_total_revs = []

            for _, idx in out.groupby(run_id).groups.items():
                if active.loc[idx].iloc[0]:
                    dur = len(idx)  # minutes
                    mean_rev = out.loc[idx].iloc[0]  # already bout-averaged
                    total_rev = mean_rev * dur
                    bout_durations.append(dur)
                    bout_total_revs.append(total_rev)

            total_bout_time = sum(bout_durations)
            total_bout_revs = sum(bout_total_revs)

            return out, total_bout_time, total_bout_revs, bout_durations

        # ---------------------------------------------------------------------

        figs_by_mouse = {mid: [] for mid in self.get_selected_mice()}
        bout_records = {}  # mid -> list of (day_idx, total_bout_revs)

        # NEW: Storage for CSV data
        csv_records = []  # List of dictionaries for CSV output

        # Group by day first (prevents bouts from spanning midnight across days)
        for day_idx, day_df in df.groupby("DateIndex", sort=True):
            day_df = day_df.sort_values("Bin").copy()

            for mid in self.get_selected_mice():
                rev_col = f"1 8 {mid} rev"
                if not (self.rev_var.get() and rev_col in day_df.columns):
                    continue

                # compute bout-averaged rev within this day
                y, total_bout_time, total_bout_revs, bout_durations = bout_average_series(day_df[rev_col],
                                                                                          threshold=threshold)
                bout_records.setdefault(mid, []).append((int(day_idx), float(total_bout_revs)))

                # NEW: Calculate most frequent bout duration
                if bout_durations:
                    from collections import Counter
                    duration_counts = Counter(bout_durations)
                    most_frequent_duration = duration_counts.most_common(1)[0][0]  # Get the most common duration
                else:
                    most_frequent_duration = 0

                # NEW: Store data for CSV
                if total_bout_time != 0:
                    v= total_bout_revs / total_bout_time
                else:
                    v=0
                csv_records.append({
                    'MouseID': mid,
                    'MouseLabel': self.mouse_label[int(mid) - 1],
                    'DayIndex': int(day_idx),
                    'TotalBoutTime_min': total_bout_time,
                    'MostFrequentBoutDuration_min': most_frequent_duration,
                    'NumberOfBouts': len(bout_durations),
                    'MeanRevsIngBoutWindow': v
                })

                fig, ax = plt.subplots(figsize=(8, 4.6))
                ax.plot(day_df["Bin"], y, linewidth=1.4, color="tab:orange", label="Bout-avg rev")

                ax.set_ylabel("Revolutions (bout-averaged)")
                ax.set_xlabel("Time")
                ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
                ax.set_xlim(day_df["Bin"].min(), day_df["Bin"].max())

                mouse_name = self.mouse_label[int(mid) - 1]
                ax.set_title(
                    f"Cohort {self.cohort} - D{int(day_idx)} - Bout Activity - {mouse_name}  ( ≥ {threshold} revs/min)")
                ax.grid(True, axis="y", linestyle="--", alpha=0.35)
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)

                if total_bout_time == 0:
                    print(str(mid) + " at " + str(day_idx))
                    continue

                notation = (
                    f"Definition of running bouts: a bout is defined as one or more consecutive "
                    f"1-min intervals with wheel revolutions ≥ {threshold} rev·min⁻¹.\n"
                    f"Total bout duration = {total_bout_time:d} min; "
                    f"avg speed during bouts = {total_bout_revs / total_bout_time:.1f} rev(s)/min."
                )
                fig.tight_layout(rect=[0.0, 0.1, 1.0, 1.0])
                fig.text(
                    0.5,  # centered horizontally
                    0.0,  # bottom margin
                    notation,
                    ha="center",
                    va="bottom",
                    fontsize=9
                )
                fig.autofmt_xdate()
                figs_by_mouse.setdefault(mid, []).append(fig)

        # --- save one PDF per mouse ---
        saved_any = False
        for mid, figs in figs_by_mouse.items():
            if not figs:
                continue

            pdf_path = f"./p1c{self.cohort}/Mouse_{mid}_Bout_Averaged_Rev_byDay.pdf"
            with PdfPages(pdf_path) as pdf:
                for fig in figs:
                    pdf.savefig(fig)
                    plt.close(fig)

            saved_any = True


        # NEW: Save CSV file with bout statistics
        if csv_records:
            csv_df = pd.DataFrame(csv_records)
            self.plot_bout_statistics(csv_df)
            # Sort by MouseID then DayIndex for readability
            csv_df = csv_df.sort_values(['MouseID', 'DayIndex'])
            csv_path = f"./p1c{self.cohort}/Cohort{self.cohort}_Bout_Statistics.csv"
            csv_df.to_csv(csv_path, index=False)
            print(f"Saved bout statistics CSV: {csv_path}")


        # ---- plot total_bout_revs across days (like total distance) ----
        if bout_records:
            fig2, ax2 = plt.subplots(figsize=(13, 6))

            for mid, records in bout_records.items():
                records = sorted(records, key=lambda x: x[0])
                days = [f"D{d}" for d, _ in records]
                vals = [v for _, v in records]

                try:
                    label = self.mouse_label[int(mid) - 1]
                except Exception:
                    label = f"Mouse {mid}"

                ax2.plot(days, vals, marker="o", label=label)

            ax2.set_xlabel("Date")
            ax2.set_ylabel(f"Total revolutions during bouts (rev/day; threshold ≥ {threshold} rev·min⁻¹)")
            ax2.set_title(f"Cohort {self.cohort} - Daily Running Output (Bout-based)")
            ax2.grid(True, linestyle="--", alpha=0.4)
            ax2.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
            ax2.legend(frameon=False)

            fig2.tight_layout()
            fig2.savefig(f"./p1c{self.cohort}/[summary]bout_speed_over_days_thr_{threshold}revpermin.pdf", dpi=300)
            # Optionally display this summary figure in the GUI:
            for widget in self.canvas_area.winfo_children():
                widget.destroy()
            canvas = FigureCanvasTkAgg(fig2, master=self.canvas_area)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

    def plot_activities_for_dayindex(self, day, df):
        fig, ax = plt.subplots(figsize=(10, 5))
        for mid in self.get_selected_mice():
            km_col = f'1 8 {mid} km'
            if km_col in df.columns:
                smoothed = df[km_col].interpolate().rolling(window=15, min_periods=1, center=True).mean()
                df['Smoothed'] = smoothed  # keep the smoothed values with the df
                df = df.sort_values(by='Bin')  # ensure proper x order
                ax.plot(df['Bin'], df['Smoothed'], label=self.mouse_label[int(mid) - 1])

        ax.set_xlabel("Time")
        ax.set_ylabel("Distance (km)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.title(f"Cohort {self.cohort} - Day {day} - Activity Comparison across Mice")
        plt.xticks(rotation=45)
        plt.grid(True)
        ax.legend()

        for widget in self.canvas_area.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        return fig


    def distance_comparison_each_day(self):
        with PdfPages(f"./p1c{self.cohort}/Allmice_Daily_Activity.pdf") as pdf:
            # Loop through each day
            for day, day_df in self.df.groupby('DateIndex'):
                fig = self.plot_activities_for_dayindex(day, day_df)
                pdf.savefig(fig)
                plt.close(fig)

    def compare_activity_sum_across_days(self):
        import matplotlib.pyplot as plt
        import numpy as np
        import re

        activity_records = {}

        if self.df is None or self.df.empty:
            messagebox.showinfo("No Data", "No dataframe loaded.")
            return

        for day, df in self.df.groupby('DateIndex'):
            df.columns = [col.strip() for col in df.columns]
            if 'Bin' not in df.columns:
                continue
            df['Bin'] = pd.to_datetime(df['Bin'], errors='coerce')
            df = df.dropna(subset=['Bin'])
            df = df.dropna(axis=1, how='all')

            mouse_ids = sorted(set(col.split()[2] for col in df.columns if col.startswith('1 8')))
            for mid in self.get_selected_mice():
                km_col = f'1 8 {mid} km'
                if km_col in df.columns:
                    km = pd.to_numeric(df[km_col], errors='coerce')
                    total_km = km.sum()
                    activity_records.setdefault(mid, []).append((day, total_km))

        # Helper function to generate color gradients
        def make_gradient_colors(base_color, n):
            """Generate n colors as gradient from base_color to white"""
            gradients = []
            for i in range(n):
                # Mix base color with white, varying the proportion
                ratio = 0.1 + (0.55 * i / max(n - 1, 1))  # From 10% to 65% mix with white
                color = tuple(base_color[j] * (1 - ratio) + ratio for j in range(3))
                gradients.append(color)
            return gradients

        # Helper function to extract SC number from label
        def extract_sc_number(label):
            """Extract the SC number from label like 'SC12(SNr-DTA)'"""
            match = re.search(r'SC(\d+)', label)
            return int(match.group(1)) if match else 999

        # Define base colors
        base_red = (0.80, 0.20, 0.20)  # Red for SNr-DTA
        base_blue = (0.20, 0.35, 0.75)  # Blue for Control

        # Sort mice by group (SNr-DTA first, then Control), then by SC number
        snr_mice = []
        ctrl_mice = []

        for mid in activity_records.keys():
            label = self.mouse_label[int(mid) - 1]
            sc_number = extract_sc_number(label)

            if "SNr-DTA" in label:
                snr_mice.append((mid, sc_number))
            elif "Control" in label or "GPi-DTA" in label:
                ctrl_mice.append((mid, sc_number))

        # Sort each group by SC number
        snr_mice.sort(key=lambda x: x[1])  # Sort by SC number
        ctrl_mice.sort(key=lambda x: x[1])  # Sort by SC number

        # Extract just the mouse IDs after sorting
        snr_mice_ids = [mid for mid, _ in snr_mice]
        ctrl_mice_ids = [mid for mid, _ in ctrl_mice]

        # Generate colors
        snr_colors = make_gradient_colors(base_red, len(snr_mice_ids)) if snr_mice_ids else []
        ctrl_colors = make_gradient_colors(base_blue, len(ctrl_mice_ids)) if ctrl_mice_ids else []

        # Create color mapping for each mouse
        mouse_colors = {}
        for i, mid in enumerate(snr_mice_ids):
            mouse_colors[mid] = snr_colors[i]
        for i, mid in enumerate(ctrl_mice_ids):
            mouse_colors[mid] = ctrl_colors[i]

        # Sort mice: SNr-DTA first (by SC number), then Control (by SC number)
        sorted_mice = snr_mice_ids + ctrl_mice_ids

        # Create figure
        filenames = [f"./p1c{self.cohort}/[summary]total_distance_over_days.png"]
        fig, ax = plt.subplots(figsize=(13, 6))

        # Plot in sorted order
        for mid in sorted_mice:
            if mid in activity_records:
                records = sorted(activity_records[mid], key=lambda x: x[0])
                days = ["D" + str(r[0]) for r in records]
                values = [r[1] for r in records]

                ax.plot(days, values,
                        label=self.mouse_label[int(mid) - 1],
                        marker='o',
                        color=mouse_colors[mid],
                        linewidth=2,
                        markersize=6,
                        markeredgecolor='k',
                        markeredgewidth=0.5)

        ax.set_xlabel("Date", fontsize=12, fontweight='bold')
        ax.set_ylabel("Distance run from 00:00 to 24:00 (km)", fontsize=12, fontweight='bold')
        plt.title(f"Cohort {self.cohort} - Activity Level Over Time", fontsize=14, fontweight='bold')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        ax.legend(loc='best', fontsize=10)
        plt.tight_layout()

        fig.savefig(filenames[0], dpi=300, bbox_inches='tight')

        # Display in canvas
        for widget in self.canvas_area.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)



    def assemble_files(self):
        file_paths = filedialog.askopenfilenames(title="Select multiple day files", filetypes=[("Data Files", "*.csv *.xls *.xlsx")])
        if not file_paths:
            return

        map_dates_activities = {}
        df_assembled = []

        for file_path in file_paths:
            try:
                if file_path.endswith(".xls") | file_path.endswith(".xlsx"):
                    try:
                        df = pd.read_csv(file_path, skiprows=10, sep="\t")
                    except Exception:
                        df = pd.read_csv(file_path, skiprows=10)
                elif file_path.endswith(".csv"):
                    df = pd.read_csv(file_path, skiprows=10)
                else:
                    continue

                df = df.dropna(how="any").dropna(axis=1, how='all')
                df.columns = [col.strip() for col in df.columns]

                if 'Bin' not in df.columns:
                    continue
                df['Bin'] = pd.to_datetime(df['Bin'],format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
                df = df.fillna(0)

                ref_ts = pd.Timestamp(self.reference_date)
                df['DateIndex'] = (df['Bin'].dt.normalize() - ref_ts).dt.days
                df['Date'] = df['Bin'].dt.date

                if df['Bin'].iloc[0] == df['Bin'].iloc[-1]:
                    df = df.iloc[:-1]
                df = df.sort_values(by='Bin')

                #mask = pd.Series(False, index=df.index)
                #for start, end in self.time_ranges:
                #    mask |= df['Bin'].between(start, end)

                # Set all columns (except 'Bin') to 0 where the mask is True
                #cols_to_zero = [col for col in df.columns if col != 'Bin' and col != 'DateIndex']
                #df.loc[mask, cols_to_zero] = 0

                df_assembled.append(df)
            except Exception as e:
                print(e)



        # merge files
        merged_df = pd.concat(df_assembled, ignore_index=True)

        rev_cols = [col for col in merged_df.columns if col.endswith("rev")]
        max_rev_value = merged_df[rev_cols].max().max()
        self.dayrange = max(merged_df['DateIndex'])

        merged_df = merged_df.drop_duplicates(subset='Bin', keep='first')

        selected = set(self.get_selected_mice())
        keep_cols = ["Bin", "DateIndex", "Date"]
        for mid in selected:
            keep_cols += [f"1 8 {mid} rev", f"1 8 {mid} km"]

        keep_cols = [c for c in keep_cols if c in merged_df.columns]
        merged_df = merged_df[keep_cols]

        print("Max rev across all mice:", max_rev_value)
        return merged_df

    def hist_bouts_ct_per_min(self, circadian = "NA"):
        filename = f"./p1c{self.cohort}/histograms_bout_count_each_day.pdf"
        sufix = ""
        if circadian == "day":
            merged_df = pd.DataFrame([x for i, x in self.df.iterrows() if x['Bin'].hour >= 6 and x['Bin'].hour < 18])
            filename = f"./p1c{self.cohort}/histograms_bout_count_each_day_(daytime).pdf"
            sufix = " - Daytime (6:00 - 18:00)"
        elif circadian == "night":
            merged_df = pd.DataFrame([x for i, x in self.df.iterrows() if x['Bin'].hour >= 18 or x['Bin'].hour < 6])
            filename = f"./p1c{self.cohort}/histograms_bout_count_each_day_(nighttime).pdf"
            sufix = " - Nighttime (18:00 - 06:00)"

        # Loop through each day
        with PdfPages(filename) as pdf:
            # Loop through each day
            mouse_ids = self.get_selected_mice()
            for day, day_df in self.df.groupby('DateIndex'):
                fig, axes = plt.subplots(len(mouse_ids), 1, figsize=(8, 3 * len(mouse_ids)), sharex=True)
                fig.suptitle(f"Cohort {self.cohort} - Revolution counts/min Histogram - D{day}" + sufix)
                if len(mouse_ids) == 1:  # Handle case of 1 mouse
                    axes = [axes]

                # Loop through each mouse column
                for ax, mid in zip(axes, mouse_ids):
                    rev_col = f'1 8 {mid} rev'
                    if rev_col in day_df.columns:
                        counts, bins, patches = ax.hist(day_df[rev_col][(day_df[rev_col] != 0) & day_df[rev_col].notna()], range=(0, 160), bins=20, alpha=0.7, edgecolor='black')
                        ax.set_title(self.mouse_label[int(mid) - 1])
                        # Label axes
                        ax.set_ylabel("Count")
                        ax.set_xlabel("Revolution counts/min")

                        # Set x-axis ticks to bin centers
                        ax.set_xticks([(bins[i] + bins[i + 1]) / 2 for i in range(len(bins) - 1)])
                        ax.set_xticklabels([f"{(bins[i] + bins[i + 1]) / 2:.1f}" for i in range(len(bins) - 1)],
                                           rotation=45)

                        # Add grid for readability
                        ax.grid(axis='y', linestyle='--', alpha=0.6)

                plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust for suptitle
                #plt.show()
                pdf.savefig(fig)
                plt.close(fig)

    def daytime_hist_bouts_ct_per_min(self):
        self.hist_bouts_ct_per_min(circadian="day")

    def nighttime_hist_bouts_ct_per_min(self):
        self.hist_bouts_ct_per_min(circadian="night")

    def get_rev_columns(df):
        """Return the list of revolution columns, e.g. '1 8 {mid} rev'."""
        return [c for c in df.columns if c.strip().endswith(' rev')]

    def bout_lengths_from_series(self, sub_df, threshold_rev=0, threshold_duration = 0, minutes_per_row=1, status="on"):
        sub_df = sub_df.mask(sub_df < threshold_rev, 0)
        if status == "on":
            active = sub_df > 0  # return a boolean
        else:
            active = sub_df == 0
        if active.empty:
            return []

        # identify consecutive runs
        groups = (active != active.shift(fill_value=False)).cumsum()
        bout_lengths = []
        for _, g in active.groupby(groups):
            if g.iloc[0]:  # only active (True) runs
                bout_lengths.append(int(g.sum()) * minutes_per_row)

        bout_lengths = [x for x in bout_lengths if x > threshold_duration]
        return bout_lengths

    def hist_bouts_duration(self, circadian = "NA"):
        filename = f"./p1c{self.cohort}/histograms_bout_duration_each_day.pdf"
        sufix = ""
        if circadian == "day":
            merged_df = pd.DataFrame([x for i, x in self.df.iterrows() if x['Bin'].hour >= 6 and x['Bin'].hour < 18])
            filename = f"./p1c{self.cohort}/histograms_bout_duration_each_day_(daytime).pdf"
            sufix = "\nDaytime (6:00 - 18:00)"
        elif circadian == "night":
            merged_df = pd.DataFrame([x for i, x in self.df.iterrows() if x['Bin'].hour >= 18 or x['Bin'].hour < 6])
            filename = f"./p1c{self.cohort}/histograms_bout_duration_each_day_(nighttime).pdf"
            sufix = "\nNighttime (18:00 - 06:00)"

        # each day
        with PdfPages(filename) as pdf:
            # Loop through each day
            mouse_ids = self.get_selected_mice()
            for day, day_df in self.df.groupby('DateIndex'):
                print(f"Day{day} start")

                fig, axes = plt.subplots(len(mouse_ids), 1, figsize=(8, 3 * len(mouse_ids)), sharex=True)
                fig.suptitle(f"Cohort {self.cohort} - Bout Duration Histograms - D{day}" + sufix)

                if len(mouse_ids) == 1:  # Handle case of 1 mouse
                    axes = [axes]

                # Loop through each mouse column
                max_rev = []
                for ax, mid in zip(axes, mouse_ids):
                    rev_col = f'1 8 {mid} rev'
                    all_lengths = []
                    per_mouse_lengths = []

                    if rev_col in day_df.columns:
                        bl = self.bout_lengths_from_series(day_df[rev_col], minutes_per_row=1)
                        per_mouse_lengths.append(bl)
                        all_lengths.extend(bl)

                        if len(bl) == 0:
                            ax.text(0.5, 0.5, "No data", ha='center', va='center', transform=ax.transAxes)
                        else:
                            counts, bins, patches = ax.hist(bl, range=(0, 50), bins=50, alpha=0.7, edgecolor='black')
                            max_rev.append(max(counts))

                        ax.grid(axis='y', linestyle='--', alpha=1)
                        # Title for each mouse
                        ax.set_title(self.mouse_label[int(mid) - 1])

                        # Label axes
                        ax.set_ylabel("Count")
                        ax.set_xlabel("Bout Duration(min)")
                        ax.set_xlim(1, 50)
                        ax.set_xticks(np.arange(1, 51, 2))
                        fig.tight_layout()

                        # Add grid for readability
                        ax.grid(axis='y', linestyle='--', alpha=0.6)
                if max_rev:
                    print(max(max_rev))
                    for i in axes:
                        i.set_ylim(1, max(max_rev))

                plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust for suptitle
                #plt.show()
                pdf.savefig(fig)
                plt.close(fig)
                print(f'day{day} is done')

    def daytime_hist_bouts_duration(self):
        self.hist_bouts_duration(circadian="day")

    def nighttime_hist_bouts_duration(self):
        self.hist_bouts_duration(circadian="night")

    def hist_bouts_duration_p_mouse(self, circadian = "NA"):
        self.mouse_ids = self.get_selected_mice()

        sufix = ""
        filename = f"p1c{self.cohort}/histograms_bout_duration_each_mouse.pdf"
        if circadian == "day":
            merged_df = pd.DataFrame([x for i, x in self.df.iterrows() if x['Bin'].hour >= 6 and x['Bin'].hour < 18])
            filename = f"p1c{self.cohort}/histograms_bout_duration_each_mouse_(daytime).pdf"
            sufix = f"\nDaytime (6:00 - 18:00)"
        elif circadian == "night":
            merged_df = pd.DataFrame([x for i, x in self.df.iterrows() if x['Bin'].hour >= 18 or x['Bin'].hour < 6])
            filename = f"p1c{self.cohort}/histograms_bout_duration_each_mouse_(nighttime).pdf"
            sufix = "\nNighttime (18:00 - 06:00)"

        # clean up
        merged_df = self.df.dropna(how='all').dropna(axis=1, how='all')

        # gather/lock the list of days (sorted)
        if 'DateIndex' not in self.df.columns:
            raise ValueError("Expected 'DateIndex' in merged_df. Make sure assemble_files() creates it.")
        days = sorted(merged_df['DateIndex'].dropna().unique())
        if len(days) == 0:
            messagebox.showinfo("No Data", "No days found in the merged data.")
            return

        # fixed bins & ticks for consistency
        bins_edges = np.arange(1, 51, 1)  # 1..50 inclusive edges
        xticks = np.arange(1, 51, 2)  # label every 2 for readability

        with PdfPages(filename) as pdf:
            # ----- iterate over MICE (one figure per mouse) -----
            for mid in self.get_selected_mice():
                # count how many subplots we will actually show (some days may be skipped)
                valid_days = []
                rev_max = []
                for day in days:
                    # Apply your rule: on Day <=7, skip mice >4 (i.e., DTAs)
                    if day <= 7 and int(mid) > 4:
                        continue
                    # Only include if the column exists for this mouse on this day
                    rev_col = f'1 8 {mid} rev'
                    day_df = merged_df.loc[self.df['DateIndex'] == day]
                    if rev_col in day_df.columns and not day_df.empty:
                        valid_days.append(day)

                # If nothing to plot for this mouse, still put a note page
                if not valid_days:
                    fig, ax = plt.subplots(figsize=(8, 3))
                    if int(mid) < 4:
                        mtitle = self.mouse_label[int(mid) - 1]
                    else:
                        mtitle = self.mouse_label[int(mid) - 2]
                    ax.text(0.5, 0.5, f"No bouts to plot for {mtitle}", ha='center', va='center',
                            transform=ax.transAxes)
                    ax.axis('off')
                    fig.suptitle(f"Cohort {self.cohort} - Bout Duration Histograms — {mtitle}"+ sufix)
                    pdf.savefig(fig)
                    plt.close(fig)
                    continue

                # Make one figure with a row per day
                n_rows = len(valid_days)
                fig, axes = plt.subplots(n_rows, 1, figsize=(8, 2.5 * n_rows), sharex=True)
                if n_rows == 1:
                    axes = [axes]

                # Figure title: mouse name
                mtitle = self.mouse_label[int(mid) - 1]
                fig.suptitle(f"Cohort {self.cohort} - Bout Duration Histogram — {mtitle}" + sufix)

                # ----- iterate over DAYS (one subplot per day) -----
                for ax, day in zip(axes, valid_days):
                    day_df = merged_df.loc[self.df['DateIndex'] == day]
                    rev_col = f'1 8 {mid} rev'
                    # compute bout lengths (minutes_per_row=1 by your definition)
                    bl = self.bout_lengths_from_series(day_df[rev_col], minutes_per_row=1)

                    # histogram: fixed 1–50, 50 bins
                    counts, bins, patches = ax.hist(bl, bins=bins_edges, range=(1, 50), alpha=0.7, edgecolor='black')
                    rev_max.append(max(counts))

                    ax.set_xlim(1, 50)
                    ax.set_ylabel("Count")
                    ax.grid(axis='y', linestyle='--', alpha=0.6)
                    # title per subplot: Day label
                    ax.set_title(f"D{day}")

                # shared x-label & ticks
                axes[-1].set_xlabel("Bout Duration (min)")
                axes[-1].set_xticks(xticks)
                axes[-1].set_xticklabels([str(x) for x in xticks], rotation=45, ha='right')

                for i in axes:
                    i.set_ylim(1, max(rev_max))

                fig.tight_layout(rect=[0, 0, 1, 0.97])
                pdf.savefig(fig)
                plt.close(fig)

    def daytime_hist_bouts_duration_p_mouse(self):
        self.hist_bouts_duration_p_mouse(circadian = "day")

    def nighttime_hist_bouts_duration_p_mouse(self):
        self.hist_bouts_duration_p_mouse(circadian = "night")

    def _compute_time_on_or_not_on_wheel(self, merged_df, threshold=0, status = "on"):
        if 'DateIndex' not in merged_df.columns:
            raise ValueError("Expected 'DateIndex' in merged_df. Make sure assemble_files() creates it.")
        merged_df = merged_df.dropna(how='all').dropna(axis=1, how='all')

        # Discover mice from columns if not set
        if not getattr(self, 'mouse_ids', None):
            # columns like '1 8 {mid} rev'
            mids = []
            for c in merged_df.columns:
                parts = c.strip().split()
                if len(parts) == 4 and parts[-1] == 'rev' and parts[0] == '1' and parts[1] == '8':
                    try:
                        mids.append(int(parts[2]))
                    except Exception:
                        pass
            self.mouse_ids = sorted(set(mids))

        records = []
        # Group by day
        for day, day_df in merged_df.groupby('DateIndex'):
            for mid in self.get_selected_mice():
                rev_col = f'1 8 {mid} rev'
                if rev_col not in day_df.columns:
                    continue
                # Minutes “on wheel” = count of rows with rev >= threshold
                df_daytime = pd.DataFrame([x for i,x in day_df.iterrows() if x['Bin'].hour >=6 and x['Bin'].hour <18])
                df_nighttime = pd.DataFrame([x for i,x in day_df.iterrows() if x['Bin'].hour >= 18 or x['Bin'].hour <6])

                if status == "on":
                    intervals = self.bout_lengths_from_series(day_df[rev_col], minutes_per_row=1, threshold_duration=1)
                    intervals_day = self.bout_lengths_from_series(df_daytime[rev_col], minutes_per_row=1, threshold_duration=1)
                    intervals_night = self.bout_lengths_from_series(df_nighttime[rev_col], minutes_per_row=1, threshold_duration=1)
                else:
                    intervals = self.bout_lengths_from_series(day_df[rev_col], minutes_per_row=1, status = "off")
                    intervals_day = self.bout_lengths_from_series(df_daytime[rev_col], minutes_per_row=1, status = "off")
                    intervals_night = self.bout_lengths_from_series(df_nighttime[rev_col], minutes_per_row=1,status = "off")
                minutes_on = sum(intervals)
                records.append({
                    'MouseID': mid,
                    'MouseLabel': self.mouse_label[mid-1],
                    'Day': int(day),
                    'MinutesOnWheel': minutes_on,
                    'MinutesOnWheel_day': sum(intervals_day),
                    'MinutesOnWheel_night': sum(intervals_night)
                })

        if not records:
            raise ValueError("No time-on-wheel data computed. Check columns and threshold.")
        return pd.DataFrame(records)


    def plot_time_on_or_not_on_wheel(self, df, threshold = 0, state = "on", notes = "", circadian=False):
        if circadian:
            fig, axes = plt.subplots(3, 2, figsize=(10, 15), sharey=True)
            start_axes = axes[0][0]
            axes[1][0].set_title("Daytime (06:00 - 18:00)", loc="right")
            axes[2][0].set_title("Nighttime (18:00 - 06:00 +1)", loc="right")
        else:
            fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), sharey=True)
            start_axes = axes[0]

        if state=="on":
            df = self._compute_time_on_or_not_on_wheel(df, threshold=threshold)
            fig.suptitle(f"Time on Wheel (mean ± SEM) (*on-wheel threshold > {threshold} min)", y=0.98, fontsize=16)
            start_axes.set_ylabel("Minutes on wheel per day")
        else:
            df = self._compute_time_on_or_not_on_wheel(df, threshold=threshold, status = "off")
            if notes==" *1st week removed":
                df = df[df["Day"] > 7]
            fig.suptitle(f"Time NOT on Wheel (mean ± SEM)" + notes, y=0.98, fontsize=16)
            start_axes.set_ylabel("Minutes not on wheel per day")

        groupA = [mid for mid in self.get_selected_mice() if "SNr" in self.mouse_label[mid-1]]
        groupB = [mid for mid in self.get_selected_mice() if "Control" in self.mouse_label[mid-1]]


        def agg_group(data, mice, columnname='MinutesOnWheel'):
            rows = []
            for m in mice:
                if m <= 3:
                    sub = data[data['MouseID'] == m][columnname]
                else:
                    sub = data[(data['MouseID'] == m) & (data['Day'] > 7)][columnname]
                arr = [x for x in sub if x != 0]
                n = len(arr)
                mean = float(np.nanmean(arr))
                sem = float(np.nanstd(arr, ddof=1) / np.sqrt(n)) if n > 1 else 0.0
                label = data.loc[data['MouseID'] == m, 'MouseLabel'].iloc[0] if (
                            data['MouseID'] == m).any() else f"Mouse {m}"
                rows.append((m, label, mean, sem, n))
            return rows

        GA = agg_group(df, groupA, columnname = "MinutesOnWheel")
        GB = agg_group(df, groupB, columnname = "MinutesOnWheel")
        GC= agg_group(df, groupA, columnname="MinutesOnWheel_day")
        GD = agg_group(df, groupB, columnname="MinutesOnWheel_day")
        GE = agg_group(df, groupA, columnname="MinutesOnWheel_night")
        GF = agg_group(df, groupB, columnname="MinutesOnWheel_night")

        # Aesthetic tuning (Nature/Science vibe)
        plt.rcParams.update({
            "font.size": 12,
            "axes.linewidth": 1.2,
            "axes.labelsize": 13,
            "axes.titlesize": 14,
            "xtick.direction": "out",
            "ytick.direction": "out"
        })
        if circadian:
            groups = [(axes[0][0], GA, "SNr-DTA"), (axes[0][1], GB, "Ctrl"), (axes[1][0], GC, "SNr-DTA"), (axes[1][1], GD, "Ctrl"), (axes[2][0], GE, "SNr-DTA"), (axes[2][1], GF, "Ctrl")]
        else:
            groups = [(axes[0], GA, "SNr-DTA"), (axes[1], GB, "Ctrl")]

        # Neutral palette
        bar_face = "#D9D9D9"  # light gray bars
        bar_edge = "#111111"  # black edge
        point_col = "#333333"  # dark points

        # Helper: draw one panel
        rng = np.random.default_rng(1234)
        stop_ct = 0
        for ax, rows, title in groups:
            # x positions
            x = np.arange(len(rows))
            means = [r[2] for r in rows]
            sems = [r[3] for r in rows]
            labels = [r[1] for r in rows]
            # bars
            MAX_BARS = max(len(GA), len(GB))
            BAR_WIDTH = 0.6

            ax.bar(x, means, yerr=sems, capsize=4, lw=1.2, edgecolor=bar_edge,
                   color=bar_face, width=0.6, error_kw=dict(lw=1.2))
            # overlay individual points (jittered)
            for i, (mid, label, _, _, _) in enumerate(rows):
                temp_df = df
                if stop_ct <2:
                    pts = temp_df[temp_df['MouseID'] == mid]['MinutesOnWheel'].to_numpy(dtype=float)
                elif 2 <= stop_ct < 4:
                    pts = temp_df[temp_df['MouseID'] == mid]['MinutesOnWheel_day'].to_numpy(dtype=float)
                else:
                    pts = temp_df[temp_df['MouseID'] == mid]['MinutesOnWheel_night'].to_numpy(dtype=float)
                pts = pts[pts > 0]

                if pts.size == 0:
                    continue
                jitter = rng.normal(0, 0.06, size=pts.size)
                ax.scatter(np.full_like(pts, i, dtype=float) + jitter,
                           pts, s=24, color=point_col, alpha=0.85, zorder=3, linewidths=0.2, edgecolors="#000000")

            ax.set_xticks(x)
            ax.set_xlim(-0.5, MAX_BARS - 0.5)
            ax.set_xticklabels(labels, rotation=20, ha='right')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(axis='y', linestyle='--', alpha=0.35)
            ax.set_axisbelow(True)

            stop_ct+=1
            if not circadian:
                break

        fig.tight_layout(rect=[0, 0, 1, 0.96])

        # Show in your Tk canvas
        for w in self.canvas_area.winfo_children():
            w.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Optional: save to a publication-ready PDF/PNG by extension in save_path
        with PdfPages(f"./p1c{self.cohort}/time_on_wheel_summary.pdf") as pdf:
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)

    def plot_time_on_wheel_summary(self, save_path="time_on_wheel_summary.pdf"):
        self.plot_time_on_or_not_on_wheel(self.df, threshold=2, state = "off", notes = " *1st week removed",circadian=True)
        self.plot_time_on_or_not_on_wheel(self.df, threshold=2, state = "on", notes = " *1st week removed", circadian=True)



    def video_saving(self):
        # pip install pdf2image imageio imageio-ffmpeg
        from pdf2image import convert_from_path
        import imageio.v2 as imageio

        pdf_path = "/Users/chen/Desktop/running_wheel_plotting/histograms.pdf"
        out_mp4 = "figures.mp4"
        fps_a = 2  # pages per second (duration per page = 1/fps)

        # Convert PDF pages to images
        pages = convert_from_path(pdf_path, dpi=200)

        # Create video writer
        writer = imageio.get_writer(out_mp4)  # fps goes here, not in write()

        for page in pages:
            writer.append_data(np.array(pages))  # convert PIL Image to numpy array

        writer.close()
        print(f"Saved video")

    def plot_temporal_two_week_splits(self):
        """
        Build one PDF with two figures:
          - Page 1: Raw data (m/min)
          - Page 2: Normalized data (%)

        Each figure has 2 subplots side-by-side:
           • Left  = Week 2 (Days 8–14)
           • Right = Week 3 (Days 15–21)

        Curves are mean ± SEM across days, aligned to minute of day (0..1439).
        """
        from tkinter import filedialog, messagebox
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.backends.backend_pdf import PdfPages

        # --- local smoother (tweakable) ---
        def smooth_1d_local(x, window=31, polyorder=2):
            x = np.asarray(x, dtype=float)
            if x.size == 0:
                return x
            isnan = np.isnan(x)
            if np.all(isnan):
                return x
            idx = np.where(~isnan)[0]
            xf = x.copy()
            xf[isnan] = np.interp(np.where(isnan)[0], idx, x[idx])
            try:
                from scipy.signal import savgol_filter
                w = int(window) + (int(window) % 2 == 0)  # ensure odd
                if w <= polyorder:
                    w = polyorder + 3 if (polyorder + 3) % 2 == 1 else polyorder + 4
                ys = savgol_filter(xf, window_length=w, polyorder=int(polyorder), mode="interp")
            except Exception:
                ys = xf
            ys[isnan] = np.nan
            return ys

        # --- groups & labels ---
        group1 = self.get_selected_mice()
        label_map = self.mouse_label

        # storage: per mouse -> arrays + corresponding day indices
        per_mouse_arrays = {m: [] for m in group1}
        per_mouse_days = {m: [] for m in group1}
        # reference date (must be set earlier in your app)
        ref = self.reference_date
        if ref is None:
            messagebox.showerror("Error", "self.reference_date (datetime.date) is not set.")
            return

        minute_index = pd.Index(np.arange(1440), name="MinuteOfDay")

        df = self.df.copy()
        df.columns = [str(c).strip() for c in df.columns]

        if "Bin" not in df.columns:
            cand = [c for c in df.columns if str(c).lower() == "bin"]
            if not cand:
                messagebox.showerror("Missing Column", "No 'Bin' column found.")
                return
            df = df.rename(columns={cand[0]: "Bin"})

        df["Bin"] = pd.to_datetime(df["Bin"], errors="coerce")
        df = df.dropna(subset=["Bin"])

        if "DateIndex" not in df.columns:
            # recompute DateIndex robustly if missing
            ref_ts = pd.Timestamp(self.reference_date)
            df["DateIndex"] = (df["Bin"].dt.normalize() - ref_ts).dt.days

        # Ensure mouse IDs are ints (important for f-strings and dict keys)
        group1 = [int(m) for m in self.get_selected_mice()]

        # Use a proper label dict
        label_map = {int(mid): self.mouse_label[int(mid) - 1] for mid in group1}

        per_mouse_arrays = {m: [] for m in group1}
        per_mouse_days = {m: [] for m in group1}

        df = df.sort_values(["DateIndex", "Bin"])

        # ----- Build one vector PER DAY PER MOUSE -----
        for day_idx, day_df in df.groupby("DateIndex", sort=True):
            mod = day_df["Bin"].dt.hour * 60 + day_df["Bin"].dt.minute

            for mid in group1:
                km_col = f"1 8 {mid} km"
                if km_col not in day_df.columns:
                    continue

                vals = pd.to_numeric(day_df[km_col], errors="coerce")
                day_series = pd.Series(vals.values, index=mod.values, dtype="float64")
                day_series = day_series.groupby(day_series.index).mean()  # collapse duplicates
                day_series = day_series.reindex(minute_index, fill_value=np.nan)

                y = (day_series * 1000.0).to_numpy()  # meters/min
                y_s = smooth_1d_local(y, window=31, polyorder=2)

                per_mouse_arrays[mid].append(y_s)
                per_mouse_days[mid].append(int(day_idx))

        # --- mean & sem helper ---
        def mean_sem(stack):
            if len(stack) == 0:
                return None, None
            arr = np.vstack(stack)
            mean = np.nanmean(arr, axis=0)
            if arr.shape[0] > 1:
                n = np.sum(~np.isnan(arr), axis=0)
                sem = np.nanstd(arr, axis=0, ddof=1) / np.sqrt(np.maximum(n, 1))
            else:
                sem = np.zeros_like(mean)
            return np.clip(mean, 0, None), sem

        # --- plotting helper (one figure, two subplots) ---
        def plot_group_two_weeks(group, week1, week2, title, ylabel, normalize=False):
            """
            group: list of mouse IDs
            week1: (lo, hi)
            week2: (lo, hi)
            ylabel: label for y-axis
            normalize: if True, normalize each mouse's data to percentage of max
            """
            x = np.arange(1440)
            tick_minutes = np.arange(0, 24 * 60 + 1, 120)
            tick_labels = [f"{tm // 60:02d}:{tm % 60:02d}" for tm in tick_minutes]

            plt.rcParams.update({
                "font.size": 12,
                "axes.linewidth": 1.2,
                "axes.labelsize": 13,
                "axes.titlesize": 14,
                "xtick.direction": "out",
                "ytick.direction": "out"
            })

            fig, axes = plt.subplots(1, 2, figsize=(18, 5), sharey=True)

            for ax, (lo, hi), subtitle in zip(axes, [week1, week2], ["Week 2", "Week 3"]):
                snr_mice = [mid for mid in group if "SNr" in label_map.get(mid, "") or "DTA" in label_map.get(mid, "")]
                ctrl_mice = [mid for mid in group if "Control" in label_map.get(mid, "")]

                def make_gradient(base_rgb, n):
                    """Darker to lighter shades of base_rgb."""
                    return [tuple(base_rgb[j] + (1 - base_rgb[j]) * (0.15 + 0.55 * i / max(n - 1, 1))
                                  for j in range(3))
                            for i in range(n)]

                snr_colors = make_gradient((0.75, 0.10, 0.10), len(snr_mice))
                ctrl_colors = make_gradient((0.10, 0.25, 0.75), len(ctrl_mice))
                color_map = {mid: c for mid, c in zip(snr_mice, snr_colors)}
                color_map.update({mid: c for mid, c in zip(ctrl_mice, ctrl_colors)})

                for mid in group:
                    stacks = [arr for arr, di in zip(per_mouse_arrays[mid], per_mouse_days[mid]) if lo <= di <= hi]
                    if not stacks:
                        continue
                    m, s = mean_sem(stacks)
                    if m is None:
                        continue

                    # Normalize if requested
                    if normalize:
                        max_val = np.nanmax(m)
                        if max_val > 0:
                            m = (m / max_val) * 100
                            s = (s / max_val) * 100

                    col = color_map.get(mid, "gray")
                    ax.plot(x, m, linewidth=1.8, label=label_map.get(mid, f"Mouse {mid}"), color=col)
                    ax.fill_between(x, m - s, m + s, alpha=0.20, linewidth=0, color=col)

                ax.set_title(f"{subtitle}", pad=8)
                ax.set_xlim(0, 1440)
                ax.set_xticks(tick_minutes)
                ax.set_xticklabels(tick_labels)
                ax.grid(axis="y", linestyle="--", alpha=0.35)
                ax.set_axisbelow(True)
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)

            axes[0].set_ylabel(ylabel)

            # Sort legend
            inv_label_map = {v: k for k, v in label_map.items()}
            for ax in axes:
                handles, labels = ax.get_legend_handles_labels()
                sorted_pairs = sorted(
                    zip(handles, labels),
                    key=lambda pair: inv_label_map.get(pair[1], 9999)
                )
                sorted_handles, sorted_labels = zip(*sorted_pairs) if sorted_pairs else ([], [])
                ax.legend(sorted_handles, sorted_labels, loc="upper center", frameon=False)

            fig.suptitle(title, fontsize=15, y=0.99)
            fig.tight_layout(rect=[0, 0, 1, 0.96])
            return fig

        # --- Build both figures ---
        # Figure 1: Raw data
        figRaw = plot_group_two_weeks(
            group1,
            week1=(8, 14),
            week2=(15, 21),
            title=f"Cohort {self.cohort} - Temporal Activity (Raw Data)",
            ylabel="Speed (m/min)",
            normalize=False
        )
        figNorm = plot_group_two_weeks(
            group1,
            week1=(8, 14),
            week2=(15, 21),
            title=f"Cohort {self.cohort} - Temporal Activity (Normalized)",
            ylabel="Normalized Speed (%)",
            normalize=True
        )

        # --- Save both figures to one PDF ---
        pdf_path = f"./p1c{self.cohort}/Cohort{self.cohort}_24h_activity_w2vs3.pdf"
        with PdfPages(pdf_path) as pdf:
            pdf.savefig(figRaw, bbox_inches="tight")
            pdf.savefig(figNorm, bbox_inches="tight")

        print(f"Saved PDF with 2 pages: {pdf_path}")

        # --- Show raw data figure in Tk canvas ---
        for w in self.canvas_area.winfo_children():
            w.destroy()
        canvas = FigureCanvasTkAgg(figRaw, master=self.canvas_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Close figures to free memory
        plt.close(figNorm)
        # Keep figRaw open since it's displayed in canvas

    def plot_double_plotted_actogram(self):
        """
        Generate cohort-wide actogram showing mean wheel activity across 24-hour cycles.
        Separate traces for SNr-DTA vs Control groups with gradient coloring.
        Includes circadian period analysis using Lomb-Scargle periodogram.

        Output:
        - One cohort actogram PDF showing all mice
        - Summary figure comparing tau (period) across groups
        - CSV with circadian parameters (tau, amplitude, power)
        """
        from scipy import signal
        from matplotlib.backends.backend_pdf import PdfPages

        if self.df is None or self.df.empty:
            self.load_dataframe()
        if self.df is None or self.df.empty:
            messagebox.showinfo("No Data", "No dataframe loaded.")
            return
        if "DateIndex" not in self.df.columns:
            messagebox.showerror("Missing Column", "Your dataframe has no 'DateIndex' column.")
            return
        if "Bin" not in self.df.columns:
            messagebox.showerror("Missing Column", "Your dataframe has no 'Bin' timestamp column.")
            return

        df = self.df.sort_values(["DateIndex", "Bin"]).copy()

        # Storage for circadian analysis results
        circadian_results = []

        # Color gradient helper
        def make_gradient_colors(base_color, n):
            gradients = []
            for i in range(n):
                ratio = 0.1 + (0.55 * i / max(n - 1, 1))
                color = tuple(base_color[j] * (1 - ratio) + ratio for j in range(3))
                gradients.append(color)
            return gradients

        base_red = (0.80, 0.20, 0.20)
        base_blue = (0.20, 0.35, 0.75)

        # Separate mice by group
        selected_mice = self.get_selected_mice()
        snr_mice = []
        ctrl_mice = []

        for mid in selected_mice:
            label = self.mouse_label[int(mid) - 1]
            if "SNr" in label or "DTA" in label:
                snr_mice.append(mid)
            elif "Control" in label:
                ctrl_mice.append(mid)

        snr_colors = make_gradient_colors(base_red, len(snr_mice)) if snr_mice else []
        ctrl_colors = make_gradient_colors(base_blue, len(ctrl_mice)) if ctrl_mice else []

        mouse_colors = {}
        for i, mid in enumerate(snr_mice):
            mouse_colors[mid] = snr_colors[i]
        for i, mid in enumerate(ctrl_mice):
            mouse_colors[mid] = ctrl_colors[i]

        # --- Lomb-Scargle periodogram analysis ---
        def lomb_scargle_period(times, values, min_period=20, max_period=28):
            """
            Compute dominant circadian period using Lomb-Scargle periodogram.

            Parameters:
            -----------
            times : array-like
                Time in hours
            values : array-like
                Activity values
            min_period : float
                Minimum period to search (hours)
            max_period : float
                Maximum period to search (hours)

            Returns:
            --------
            tau : float
                Dominant period in hours
            power : float
                Power at dominant period
            amplitude : float
                Amplitude of the dominant rhythm
            significance : float
                Statistical significance (p-value)
            """
            # Remove NaN values
            mask = ~np.isnan(values)
            times_clean = np.array(times)[mask]
            values_clean = np.array(values)[mask]

            if len(times_clean) < 24:  # Need at least 1 day of data
                return np.nan, np.nan, np.nan, np.nan

            # Define frequency range (1/period)
            frequencies = np.linspace(1 / max_period, 1 / min_period, 1000)

            # Compute Lomb-Scargle periodogram
            try:
                ls_power = signal.lombscargle(times_clean, values_clean - np.mean(values_clean),
                                              frequencies * 2 * np.pi, normalize=True)

                # Find peak
                peak_idx = np.argmax(ls_power)
                peak_freq = frequencies[peak_idx]
                tau = 1 / peak_freq  # Period in hours
                power = ls_power[peak_idx]

                # Estimate amplitude (half peak-to-peak of fitted sinusoid)
                amplitude = np.sqrt(2 * power) * np.std(values_clean)

                # Significance testing (false alarm probability)
                M = len(frequencies)
                false_alarm_prob = 1 - (1 - np.exp(-power)) ** M

                return tau, power, amplitude, false_alarm_prob

            except Exception as e:
                print(f"Error in Lomb-Scargle analysis: {e}")
                return np.nan, np.nan, np.nan, np.nan

        # --- Prepare data organized by mouse and day ---
        mouse_day_data = {}  # {mouse_id: {day: hourly_array}}

        for mid in selected_mice:
            rev_col = f"1 8 {mid} rev"

            if rev_col not in df.columns:
                print(f"Warning: Column {rev_col} not found for mouse {mid}")
                continue

            mouse_name = self.mouse_label[int(mid) - 1]
            mouse_df = df[[rev_col, 'Bin', 'DateIndex']].copy()
            mouse_df = mouse_df.dropna(subset=[rev_col])
            mouse_df[rev_col] = pd.to_numeric(mouse_df[rev_col], errors='coerce')

            if len(mouse_df) < 24 * 60:  # Need at least 1 day
                print(f"Insufficient data for mouse {mid}")
                continue

            # Organize by day and hour
            mouse_df['HourOfDay'] = mouse_df['Bin'].dt.hour + mouse_df['Bin'].dt.minute / 60

            mouse_day_data[mid] = {}

            # Get data for each day
            for day in sorted(mouse_df['DateIndex'].unique()):
                day_data = mouse_df[mouse_df['DateIndex'] == day].copy()

                # Bin into 24 hourly bins
                hourly_bins = np.arange(0, 24.5, 1)  # 0, 1, 2, ..., 24
                hourly_activity = np.zeros(24)

                for i in range(24):
                    hour_mask = (day_data['HourOfDay'] >= i) & (day_data['HourOfDay'] < i + 1)
                    if hour_mask.any():
                        hourly_activity[i] = day_data.loc[hour_mask, rev_col].mean()

                mouse_day_data[mid][int(day)] = hourly_activity

            # --- Circadian analysis for this mouse ---
            # Concatenate all days for long-term analysis
            start_time = mouse_df['Bin'].min()
            mouse_df['HoursFromStart'] = (mouse_df['Bin'] - start_time).dt.total_seconds() / 3600

            times_hours = mouse_df['HoursFromStart'].values
            activity_values = mouse_df[rev_col].values

            tau, power, amplitude, p_value = lomb_scargle_period(
                times_hours, activity_values, min_period=20, max_period=28
            )

            circadian_results.append({
                'MouseID': mid,
                'MouseLabel': mouse_name,
                'Tau_hours': tau,
                'Power': power,
                'Amplitude': amplitude,
                'P_value': p_value,
                'Significant': 'Yes' if p_value < 0.05 else 'No'
            })

        # --- Create cohort-wide actogram (24 hours only) ---
        # Get all days across all mice
        all_days = set()
        for mid_data in mouse_day_data.values():
            all_days.update(mid_data.keys())
        all_days = sorted(all_days)

        if not all_days:
            messagebox.showerror("No Data", "No daily data available for actogram.")
            return

        # Create figure with 3 panels
        fig = plt.figure(figsize=(14, 12))
        gs = fig.add_gridspec(3, 1, height_ratios=[2.5, 1, 1], hspace=0.35)

        # --- Panel 1: Actogram (24 hours) ---
        ax_actogram = fig.add_subplot(gs[0])

        # Plot each mouse's data
        y_offset = 0
        ytick_positions = []
        ytick_labels = []

        # Plot SNr-DTA mice first
        for i, mid in enumerate(snr_mice):
            if mid not in mouse_day_data:
                continue

            mouse_name = self.mouse_label[int(mid) - 1]
            color = mouse_colors[mid]

            for day in all_days:
                if day not in mouse_day_data[mid]:
                    continue

                hourly_activity = mouse_day_data[mid][day]
                hours = np.arange(24)

                # Normalize activity for visualization (0-1 scale per mouse for bar height)
                max_activity = max([np.max(mouse_day_data[mid][d])
                                    for d in mouse_day_data[mid].keys() if len(mouse_day_data[mid][d]) > 0])
                if max_activity > 0:
                    normalized_activity = hourly_activity / max_activity * 0.8  # Scale to 0.8 for spacing
                else:
                    normalized_activity = hourly_activity * 0

                # Plot 24 hours
                for h in range(24):
                    if normalized_activity[h] > 0:
                        ax_actogram.bar(h, normalized_activity[h], bottom=y_offset,
                                        width=1, color=color, alpha=0.7, edgecolor='none')

                y_offset += 1

            # Add mouse label
            ytick_positions.append(y_offset - len(all_days) / 2)
            ytick_labels.append(mouse_name)

        # Add separator
        if snr_mice and ctrl_mice:
            ax_actogram.axhline(y_offset, color='black', linewidth=2, linestyle='-')
            y_offset += 0.5

        # Plot Control mice
        for i, mid in enumerate(ctrl_mice):
            if mid not in mouse_day_data:
                continue

            mouse_name = self.mouse_label[int(mid) - 1]
            color = mouse_colors[mid]

            for day in all_days:
                if day not in mouse_day_data[mid]:
                    continue

                hourly_activity = mouse_day_data[mid][day]
                hours = np.arange(24)

                max_activity = max([np.max(mouse_day_data[mid][d])
                                    for d in mouse_day_data[mid].keys() if len(mouse_day_data[mid][d]) > 0])
                if max_activity > 0:
                    normalized_activity = hourly_activity / max_activity * 0.8
                else:
                    normalized_activity = hourly_activity * 0

                # Plot 24 hours
                for h in range(24):
                    if normalized_activity[h] > 0:
                        ax_actogram.bar(h, normalized_activity[h], bottom=y_offset,
                                        width=1, color=color, alpha=0.7, edgecolor='none')

                y_offset += 1

            ytick_positions.append(y_offset - len(all_days) / 2)
            ytick_labels.append(mouse_name)

        # Format actogram
        ax_actogram.set_xlim(-0.5, 24.5)
        ax_actogram.set_ylim(0, y_offset + 0.5)
        ax_actogram.set_xlabel('Time (hours)', fontsize=13, fontweight='bold')
        ax_actogram.set_ylabel('Mouse', fontsize=13, fontweight='bold')
        ax_actogram.set_xticks(np.arange(0, 25, 3))
        ax_actogram.set_yticks(ytick_positions)
        ax_actogram.set_yticklabels(ytick_labels, fontsize=9)
        ax_actogram.grid(True, axis='x', alpha=0.3, linestyle='--')

        # Shade nighttime (assuming lights off 18:00-06:00)
        ax_actogram.axvspan(18, 24, alpha=0.15, color='gray', zorder=0, label='Dark phase')
        ax_actogram.axvspan(0, 6, alpha=0.15, color='gray', zorder=0)

        # Add zeitgeber time reference
        ax_actogram.set_title(f'Cohort {self.cohort} - Actogram\n'
                              f'Days {min(all_days)} to {max(all_days)}',
                              fontsize=14, fontweight='bold', pad=15)

        # --- Panel 2: Average daily profiles by group ---
        ax_profile = fig.add_subplot(gs[1])

        # Calculate group averages
        def calc_group_average(mouse_list):
            """Calculate mean hourly activity across all mice and days in group"""
            all_hourly = []
            for mid in mouse_list:
                if mid not in mouse_day_data:
                    continue
                for day_data in mouse_day_data[mid].values():
                    all_hourly.append(day_data)

            if not all_hourly:
                return None, None

            hourly_array = np.array(all_hourly)
            mean_activity = np.nanmean(hourly_array, axis=0)
            sem_activity = np.nanstd(hourly_array, axis=0) / np.sqrt(len(all_hourly))

            return mean_activity, sem_activity

        hours = np.arange(24)

        if snr_mice:
            snr_mean, snr_sem = calc_group_average(snr_mice)
            if snr_mean is not None:
                ax_profile.plot(hours, snr_mean, color=base_red, linewidth=3,
                                label=f'SNr-DTA (n={len(snr_mice)})', marker='o', markersize=4)
                ax_profile.fill_between(hours, snr_mean - snr_sem, snr_mean + snr_sem,
                                        alpha=0.25, color=base_red)

        if ctrl_mice:
            ctrl_mean, ctrl_sem = calc_group_average(ctrl_mice)
            if ctrl_mean is not None:
                ax_profile.plot(hours, ctrl_mean, color=base_blue, linewidth=3,
                                label=f'Control (n={len(ctrl_mice)})', marker='s', markersize=4)
                ax_profile.fill_between(hours, ctrl_mean - ctrl_sem, ctrl_mean + ctrl_sem,
                                        alpha=0.25, color=base_blue)

        ax_profile.set_xlim(0, 24)
        ax_profile.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
        ax_profile.set_ylabel('Wheel Revs/hour\n(mean ± SEM)', fontsize=12, fontweight='bold')
        ax_profile.set_title('Average Daily Activity Profile', fontsize=13, fontweight='bold')
        ax_profile.set_xticks(np.arange(0, 25, 3))
        ax_profile.grid(True, alpha=0.3, linestyle='--')
        ax_profile.legend(loc='best', fontsize=11, frameon=False)
        ax_profile.spines['top'].set_visible(False)
        ax_profile.spines['right'].set_visible(False)

        # Shade nighttime
        ax_profile.axvspan(18, 24, alpha=0.15, color='gray', zorder=0)
        ax_profile.axvspan(0, 6, alpha=0.15, color='gray', zorder=0)

        # --- Panel 3: Group periodograms (IMPROVED VERSION) ---
        # Calculate group-averaged periodograms
        if circadian_results:
            results_df = pd.DataFrame(circadian_results)

            snr_results = results_df[results_df['MouseLabel'].str.contains('SNr|DTA', na=False)]
            ctrl_results = results_df[results_df['MouseLabel'].str.contains('Control', na=False)]

        if len(snr_results) > 0 and len(ctrl_results) > 0:
            snr_power_mean = snr_results['Power'].mean()
            ctrl_power_mean = ctrl_results['Power'].mean()
            power_diff_pct = ((snr_power_mean - ctrl_power_mean) / ctrl_power_mean) * 100

        # Save cohort figure
        fig.tight_layout()
        pdf_path = f"./p1c{self.cohort}/Cohort{self.cohort}_Actogram.pdf"
        fig.savefig(pdf_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved cohort actogram: {pdf_path}")

        # --- Save circadian parameters to CSV ---
        if circadian_results:
            results_df = pd.DataFrame(circadian_results)
            results_df = results_df.sort_values('MouseID')
            csv_path = f"./p1c{self.cohort}/Cohort{self.cohort}_Circadian_Parameters.csv"
            results_df.to_csv(csv_path, index=False)
            print(f"Saved circadian parameters: {csv_path}")

        # ======================================================================
        # MULTI-COHORT COMBINED ACTOGRAM
        # Ask user to select additional cohort files; pool all cohorts into one
        # figure with the same 3-panel layout (actogram / profile / LS tau bar).
        # SNr-DTA mice → red family; Control → blue family across all cohorts.
        # ======================================================================
        from tkinter import filedialog as _fd

        extra_paths = _fd.askopenfilenames(
            title="Select ALL cohort files for combined actogram (cancel to skip)",
            filetypes=[("Data Files", "*.csv *.xls *.xlsx")]
        )

        if extra_paths:
            # cohort label colours: one shade of red / blue per cohort
            cohort_red_shades  = [(0.80, 0.10, 0.10), (0.90, 0.35, 0.15),
                                  (0.75, 0.20, 0.40), (0.95, 0.50, 0.30)]
            cohort_blue_shades = [(0.10, 0.25, 0.75), (0.20, 0.50, 0.85),
                                  (0.10, 0.60, 0.70), (0.30, 0.40, 0.90)]

            # Storage across all cohorts
            all_snr_hourly   = []   # each element: 24-element hourly array (one mouse×day)
            all_ctrl_hourly  = []
            all_snr_tau      = []   # Lomb-Scargle tau per SNr mouse
            all_ctrl_tau     = []
            combined_mouse_day_data  = {}  # (cohort, mid) -> {day: hourly_array}
            combined_mouse_colors    = {}
            combined_mouse_labels    = {}
            combined_snr_keys        = []
            combined_ctrl_keys       = []

            cohort_order = []  # track loading order for colour assignment

            for fpath in sorted(extra_paths):
                try:
                    # ---- infer cohort number ----
                    if fpath.endswith(".xls") or fpath.endswith(".csv"):
                        c_num = int(fpath[-5:-4])
                    else:
                        c_num = int(fpath[-6:-5])

                    if c_num == 1:
                        c_labels = ["SC01(Control)", "LM45(SNr-DTA)", "SC02(GPi-DTA)"]
                    elif c_num == 2:
                        c_labels = ["SC04(SNr-DTA)", "SC05(SNr-DTA)", "SC06(SNr-DTA)",
                                    "SC07(Control)", "SC08(Control)"]
                    elif c_num == 3:
                        c_labels = ["SC09(SNr-DTA)", "SC10(SNr-DTA)", "SC11(SNr-DTA)",
                                    "SC12(SNr-DTA)", "SC13(Control)", "SC14(Control)", "SC15(Control)"]
                    elif c_num == 4:
                        c_labels = ["SC29(SNr-DTA)", "SC30(SNr-DTA)", "SC31(SNr-DTA)",
                                    "SC32(SNr-DTA)", "SC33(Control)", "SC34(Control)", "SC35(Control)"]
                    else:
                        c_labels = []

                    # ---- load df ----
                    if fpath.endswith(".xls") or fpath.endswith(".xlsx"):
                        try:
                            c_df = pd.read_csv(fpath, skiprows=10, sep="\t")
                        except Exception:
                            c_df = pd.read_csv(fpath, skiprows=10)
                    else:
                        c_df = pd.read_csv(fpath, skiprows=10)

                    c_df = c_df.dropna(how='all').dropna(axis=1, how='all')
                    c_df.columns = [col.strip() for col in c_df.columns]
                    if 'Bin' not in c_df.columns:
                        continue
                    c_df['Bin'] = pd.to_datetime(c_df['Bin'], format="mixed", errors='coerce')
                    c_df = c_df.dropna(subset=['Bin'])

                    ref_d = c_df['Bin'].dt.normalize().min().date()
                    if c_num == 3:
                        from datetime import timedelta as _td
                        ref_d = ref_d - _td(days=8)
                    c_df['DateIndex'] = (c_df['Bin'].dt.normalize() - pd.Timestamp(ref_d)).dt.days

                    c_mids = sorted(set(col.split()[2] for col in c_df.columns if col.startswith('1 8')))
                    c_mids = [int(m) for m in c_mids if str(m).isdigit()]

                    # excluded mice same rules as generate_bout_statistics_summary_multi_cohort
                    for skip in ([3, 5, 6, 7] if c_num == 1 else
                                 [4]           if c_num == 2 else
                                 [7]           if c_num == 4 else []):
                        if skip in c_mids:
                            c_mids.remove(skip)

                    c_idx = len(cohort_order)
                    cohort_order.append(c_num)
                    snr_col = cohort_red_shades[c_idx % len(cohort_red_shades)]
                    ctrl_col = cohort_blue_shades[c_idx % len(cohort_blue_shades)]

                    for mid in c_mids:
                        rev_col = f"1 8 {mid} rev"
                        if rev_col not in c_df.columns:
                            continue
                        lbl = c_labels[mid - 1] if mid - 1 < len(c_labels) else f"C{c_num}M{mid}"
                        is_snr = "SNr" in lbl or "DTA" in lbl
                        key = (c_num, mid)

                        m_df = c_df[['Bin', 'DateIndex', rev_col]].copy()
                        m_df[rev_col] = pd.to_numeric(m_df[rev_col], errors='coerce').fillna(0.0)
                        m_df['HourOfDay'] = m_df['Bin'].dt.hour + m_df['Bin'].dt.minute / 60

                        combined_mouse_day_data[key] = {}
                        for day in sorted(m_df['DateIndex'].unique()):
                            d_df = m_df[m_df['DateIndex'] == day]
                            h_arr = np.zeros(24)
                            for h in range(24):
                                mask_h = (d_df['HourOfDay'] >= h) & (d_df['HourOfDay'] < h + 1)
                                if mask_h.any():
                                    h_arr[h] = d_df.loc[mask_h, rev_col].mean()
                            combined_mouse_day_data[key][int(day)] = h_arr
                            if is_snr:
                                all_snr_hourly.append(h_arr)
                            else:
                                all_ctrl_hourly.append(h_arr)

                        combined_mouse_colors[key] = snr_col if is_snr else ctrl_col
                        combined_mouse_labels[key] = lbl

                        if is_snr:
                            combined_snr_keys.append(key)
                        else:
                            combined_ctrl_keys.append(key)

                        # Lomb-Scargle tau
                        m_df2 = m_df.sort_values('Bin')
                        m_df2['HoursFromStart'] = (m_df2['Bin'] - m_df2['Bin'].min()).dt.total_seconds() / 3600.0
                        tau_c, _, _, _ = lomb_scargle_period(
                            m_df2['HoursFromStart'].values, m_df2[rev_col].values)
                        if not np.isnan(tau_c):
                            if is_snr:
                                all_snr_tau.append(tau_c)
                            else:
                                all_ctrl_tau.append(tau_c)

                    print(f"  Combined actogram: loaded cohort {c_num}")
                except Exception as e_c:
                    print(f"  Combined actogram: skipped {fpath} ({e_c})")
                    continue

            if combined_mouse_day_data:
                all_c_days = sorted(set(
                    day for data in combined_mouse_day_data.values() for day in data.keys()))

                fig_all = plt.figure(figsize=(16, 14))
                gs_all  = fig_all.add_gridspec(3, 1, height_ratios=[3, 1, 1], hspace=0.38)

                # ---- Panel 1: stacked actogram (all cohorts, SNr first then Ctrl) ----
                ax_act = fig_all.add_subplot(gs_all[0])
                y_off, ytick_pos, ytick_lbl = 0, [], []

                for group_keys, sep_label in [(combined_snr_keys, "SNr-DTA"),
                                              (combined_ctrl_keys, "Control")]:
                    group_start = y_off
                    for key in group_keys:
                        if key not in combined_mouse_day_data:
                            continue
                        color = combined_mouse_colors[key]
                        lbl   = combined_mouse_labels[key]
                        n_days_plotted = 0
                        max_act = max(
                            (np.max(combined_mouse_day_data[key][d])
                             for d in combined_mouse_day_data[key] if len(combined_mouse_day_data[key][d]) > 0),
                            default=1.0)
                        for day in all_c_days:
                            if day not in combined_mouse_day_data[key]:
                                continue
                            h_arr = combined_mouse_day_data[key][day]
                            norm  = h_arr / max_act * 0.8 if max_act > 0 else h_arr * 0
                            for h in range(24):
                                if norm[h] > 0:
                                    ax_act.bar(h, norm[h], bottom=y_off,
                                               width=1, color=color, alpha=0.65, edgecolor='none')
                            y_off += 1
                            n_days_plotted += 1
                        if n_days_plotted:
                            ytick_pos.append(y_off - n_days_plotted / 2)
                            ytick_lbl.append(lbl)

                    if group_keys and sep_label == "SNr-DTA" and combined_ctrl_keys:
                        ax_act.axhline(y_off, color='black', linewidth=1.5, linestyle='--', alpha=0.6)
                        y_off += 0.5

                ax_act.set_xlim(-0.5, 24.5)
                ax_act.set_ylim(0, y_off + 0.5)
                ax_act.set_xticks(np.arange(0, 25, 3))
                ax_act.set_yticks(ytick_pos)
                ax_act.set_yticklabels(ytick_lbl, fontsize=7)
                ax_act.set_xlabel('Time (hours)', fontsize=12, fontweight='bold')
                ax_act.set_ylabel('Mouse', fontsize=12, fontweight='bold')
                ax_act.axvspan(18, 24, alpha=0.12, color='gray', zorder=0)
                ax_act.axvspan(0,  6,  alpha=0.12, color='gray', zorder=0)
                ax_act.grid(True, axis='x', alpha=0.3, linestyle='--')
                ax_act.set_title(
                    f'All Cohorts Combined – Actogram  '
                    f'(Days {min(all_c_days)}–{max(all_c_days)})',
                    fontsize=13, fontweight='bold', pad=12)

                # ---- Panel 2: pooled group mean ± SEM hourly profile ----
                ax_prof = fig_all.add_subplot(gs_all[1])
                hours_x = np.arange(24)

                for hourly_list, col, grp_label in [
                        (all_snr_hourly,  (0.80, 0.10, 0.10), f'SNr-DTA (n={len(combined_snr_keys)} mice)'),
                        (all_ctrl_hourly, (0.10, 0.25, 0.75), f'Control (n={len(combined_ctrl_keys)} mice)')]:
                    if not hourly_list:
                        continue
                    arr = np.array(hourly_list)
                    mn  = np.nanmean(arr, axis=0)
                    sem = np.nanstd(arr, axis=0) / np.sqrt(len(hourly_list))
                    ax_prof.plot(hours_x, mn, color=col, linewidth=2.5,
                                 label=grp_label, marker='o', markersize=3)
                    ax_prof.fill_between(hours_x, mn - sem, mn + sem,
                                         alpha=0.22, color=col, linewidth=0)

                ax_prof.set_xlim(0, 23)
                ax_prof.set_xticks(np.arange(0, 25, 3))
                ax_prof.set_xlabel('Hour of Day', fontsize=11, fontweight='bold')
                ax_prof.set_ylabel('Revs/hour\n(mean±SEM)', fontsize=11, fontweight='bold')
                ax_prof.set_title('Pooled Average Daily Activity Profile', fontsize=12, fontweight='bold')
                ax_prof.axvspan(18, 24, alpha=0.12, color='gray', zorder=0)
                ax_prof.axvspan(0,  6,  alpha=0.12, color='gray', zorder=0)
                ax_prof.grid(True, alpha=0.3, linestyle='--')
                ax_prof.legend(loc='best', fontsize=10, frameon=False)
                ax_prof.spines['top'].set_visible(False)
                ax_prof.spines['right'].set_visible(False)

                # ---- Panel 3: tau bar plot (mean ± SEM per group) ----
                ax_tau = fig_all.add_subplot(gs_all[2])
                rng2 = np.random.default_rng(42)
                bar_groups = []
                if all_snr_tau:
                    bar_groups.append((all_snr_tau,  (0.80, 0.10, 0.10), 'SNr-DTA'))
                if all_ctrl_tau:
                    bar_groups.append((all_ctrl_tau, (0.10, 0.25, 0.75), 'Control'))

                for bx, (tau_vals, bcol, blbl) in enumerate(bar_groups):
                    bm  = np.mean(tau_vals)
                    bse = np.std(tau_vals, ddof=1) / np.sqrt(len(tau_vals)) if len(tau_vals) > 1 else 0
                    ax_tau.bar(bx, bm, yerr=bse, color=bcol, alpha=0.75, capsize=5,
                               edgecolor='black', linewidth=1.0, width=0.5)
                    jit = rng2.normal(0, 0.07, size=len(tau_vals))
                    ax_tau.scatter(np.full(len(tau_vals), bx) + jit, tau_vals,
                                   s=28, color='black', alpha=0.7, zorder=3)

                ax_tau.set_xticks(range(len(bar_groups)))
                ax_tau.set_xticklabels([g[2] for g in bar_groups], fontsize=11)
                ax_tau.set_ylabel('Circadian Period τ (hours)', fontsize=11, fontweight='bold')
                ax_tau.set_title('Lomb-Scargle Dominant Period (All Cohorts)', fontsize=12, fontweight='bold')
                ax_tau.axhline(24, color='gray', linewidth=1.2, linestyle='--', alpha=0.6, label='24 h')
                ax_tau.legend(fontsize=9, frameon=False)
                ax_tau.spines['top'].set_visible(False)
                ax_tau.spines['right'].set_visible(False)
                ax_tau.grid(axis='y', alpha=0.3, linestyle='--')

                fig_all.tight_layout()
                combined_pdf = "./AllCohorts_Combined_Actogram.pdf"
                fig_all.savefig(combined_pdf, dpi=300, bbox_inches='tight')
                plt.close(fig_all)
                print(f"Saved combined actogram: {combined_pdf}")
            else:
                print("Combined actogram: no data loaded, skipping.")

        if circadian_results:
            messagebox.showinfo("Complete",
                                f"Generated cohort actogram with {len(selected_mice)} mice\n"
                                f"Saved to: {pdf_path}")
        else:
            messagebox.showinfo("No Results", "No circadian analysis results generated.")

    def bunch_save(self):
        self.Daily_Data_per_Mouse()
        self.Bout_averaged_Rev_per_day()
        self.compare_activity_sum_across_days()
        self.distance_comparison_each_day()
        self.hist_bouts_ct_per_min()
        self.daytime_hist_bouts_ct_per_min()
        self.nighttime_hist_bouts_ct_per_min()
        self.hist_bouts_duration()
        self.daytime_hist_bouts_duration()
        self.nighttime_hist_bouts_duration()
        self.hist_bouts_duration_p_mouse()
        self.daytime_hist_bouts_duration_p_mouse()
        self.nighttime_hist_bouts_duration_p_mouse()
        self.plot_time_on_wheel_summary()
        self.plot_temporal_two_week_splits()

    def show_plot(self, index):
        for widget in self.canvas_area.winfo_children():
            widget.destroy()
        if 0 <= int(index) < len(self.plots):
            fig, _ = self.plots[int(index)]
            canvas = FigureCanvasTkAgg(fig, master=self.canvas_area)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            self.current_index = int(index)

    def show_page(self, page_index):
        for widget in self.canvas_area.winfo_children():
            widget.destroy()

        start = page_index * self.page_size
        end = min(start + self.page_size, len(self.plots))
        figs = self.plots[start:end]

        if not figs:
            return

        # create ONE composite figure
        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        axes = axes.flatten()

        for ax, (src_fig, _) in zip(axes, figs):
            self._copy_axes(src_fig.axes[0], ax)

        # hide unused subplots
        for ax in axes[len(figs):]:
            ax.axis("off")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        self.current_page = page_index

    def show_next_plot(self):
        if self.current_index + 1 < len(self.plots):
            self.show_plot(self.current_index + 1)

    def show_prev_plot(self):
        if self.current_index - 1 >= 0:
            self.show_plot(self.current_index - 1)

    def update_plots(self):
        if self.df is not None:
            self.Daily_Data_per_Mouse()
            if self.plots:
                self.show_plot(self.current_index)

    def save_plots(self):
        if not self.output_path.get():
            messagebox.showerror("Missing Output Path", "Please specify an output file name.")
            return
        #for fig, mid in self.plots:
            #fig.savefig(f"{os.path.splitext(self.output_path.get())[0]}_mouse_{mid}.png")

        with PdfPages(f"{os.path.splitext(self.output_path.get())[0]}{self.date}_Day{self.date_number}.pdf") as pdf:
            for fig, _ in self.plots:
                pdf.savefig(fig)

    def apply_mouse_selection(self):
        sel = [int(self.mouse_listbox.get(i)) for i in self.mouse_listbox.curselection()]
        if not sel:
            messagebox.showwarning("No mice selected", "Please select at least one mouse.")
            return
        self.selected_mice = sel
        #self.update_plots()

    def get_selected_mice(self):
        # fallback if not set
        if getattr(self, "selected_mice", None):
            return self.selected_mice
        return getattr(self, "mouse_ids", [])

    def get_selected_days(self):
        if getattr(self, "selected_days", None):
            return self.selected_days
        return getattr(self, "available_days", [])

    def apply_day_selection(self):
        sel = [self.available_days[i] for i in self.day_listbox.curselection()]
        if not sel:
            messagebox.showwarning(
                "No days selected",
                "Please select at least one DayIndex."
            )
            return
        self.selected_days = sel
        self.df = self.df[self.df["DateIndex"].isin(self.get_selected_days())]
        # self.update_plots()  # optional auto-refresh


if __name__ == "__main__":
    root = tk.Tk()
    app = MouseActivityApp(root)
    root.mainloop()