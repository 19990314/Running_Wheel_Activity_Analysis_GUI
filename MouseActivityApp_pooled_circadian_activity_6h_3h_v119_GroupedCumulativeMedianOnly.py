import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['ps.fonttype'] = 42
plt.rcParams['pdf.fonttype'] = 42
import matplotlib.dates as mdates
import seaborn as sns
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from datetime import timedelta

from shapely.measurement import length

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
        tk.Button(self.main_frame, text="Pooled multi-cohort distance comparison", command=self.compare_activity_sum_across_days_multi_cohort).grid(row=5, column=3, pady=10)
        tk.Button(self.main_frame, text="Functional Trajectory UMAP", command=self.plot_functional_trajectory_umap_multi_cohort).grid(row=5, column=4, pady=10)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: one plot summarizing total distance that each mouse run on each day\n").grid(row=6, column=0)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: pdf, one fig per day, distance of all mice on y axis, 24h time series on x\n").grid(row=6, column=1)
        tk.Label(self.main_frame, text="+++++++++++++++++++++++++++++++++++++\n").grid(row=6, column=2)
        tk.Label(self.main_frame, text="Input: multiple cohort files\n Output: pooled total distance per mouse across days\n").grid(row=6, column=3)
        tk.Label(self.main_frame, text="Input: multiple cohort files\n Output: UMAP trajectory of each mouse across days 1–28\n").grid(row=6, column=4)

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
        tk.Button(self.main_frame, text="Pooled Actogram", command=self.plot_pooled_actogram).grid(row=15, column=2, pady=5)
        tk.Button(self.main_frame, text="Pooled Circadian Activity (6h + 3h)",
                  command=self.plot_pooled_circadian_activity_by_phase).grid(row=15, column=0, pady=5)
        tk.Button(self.main_frame, text="Bout Interval CSV + Plot",
                  command=self.bout_interval_csv_plot).grid(row=16, column=0, pady=5)
        tk.Button(self.main_frame, text="Custom Window Group Diff",
                  command=self.plot_custom_window_group_differences).grid(row=17, column=0, pady=5)
        tk.Button(self.main_frame, text="Discovery Scan Wheeling Phenotype",
                  command=self.plot_custom_window_group_differences).grid(row=18, column=0, pady=5)
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

    def _labels_for_cohort_global(self, cohort_num):
        """
        Central mouse-label mapping used across plots/analysis.
        For cohort 3, list index = wheel/mouse ID - 1:
            wheel 1 -> SC09
            wheel 2 -> SC10
            wheel 3 -> SC11
            wheel 4 -> SC12
            wheel 5 -> SC13
            wheel 6 -> SC14
            wheel 7 -> SC15
        """
        if cohort_num == 1:
            return ["SC01(Control)", "LM45(SNr-DTA)", "SC02(GPi-DTA)"]
        if cohort_num == 2:
            return ["SC04(SNr-DTA)", "SC05(SNr-DTA)", "SC06(SNr-DTA)",
                    "SC07(Control)", "SC08(Control)"]
        if cohort_num == 3:
            return ["SC09(SNr-DTA)", "SC10(SNr-DTA)", "SC11(SNr-DTA)",
                    "SC12(SNr-DTA)", "SC13(Control)", "SC14(Control)", "SC15(Control)"]
        if cohort_num == 4:
            return ["SC29(SNr-DTA)", "SC30(SNr-DTA)", "SC31(SNr-DTA)",
                    "SC32(SNr-DTA)", "SC33(Control)", "SC34(Control)", "SC35(Control)"]
        return []


    def load_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Data Files", "*.csv *.xls *.xlsx")])
        if self.file_path:
            if self.file_path.endswith(".xls") | self.file_path.endswith(".csv"):
                self.cohort = int(self.file_path[-5:-4])
            else:
                self.cohort = int(self.file_path[-6:-5])
            self.mouse_label = self._labels_for_cohort_global(self.cohort)

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

    def _per_mouse_bout_metric_csv_filename(self, day_min=8, day_max=21):
        """Shared output filename for per-mouse bout metric summaries."""
        return f'BoutStatistics_perMouse_boutCounts_lightdarkseparated_lowhighspeedseparated_meanANDmedianOf_1Revs_2Durations_3IBI_4Acceleration_day{day_min}-{day_max}.csv'

    def _build_per_mouse_bout_metric_df(self, cohort_data_dict, day_min=8, day_max=21,
                                        threshold=10, truncate_flag=0, acc_nozero=0):
        """
        Build the per-mouse metric table used by:
        - generate_bout_statistics_summary_multi_cohort()
        - bout_interval_csv_plot()

        This table now includes both:
        1. Whole selected-day-range metrics.
        2. Phase-split metrics using the same phase segmentation used in bout statistics:
           - Light phase: 06:00-18:00
           - Dark phase 1: 18:00-24:00
           - Dark phase 2: 00:00-06:00
           - Dark phase 3: 18:00-21:00
             Note: Dark phase 3 is an additional overlapping sub-window of Dark phase 1.

        Output columns:
            Cohort, ID, Group, MouseLabel, Day, BoutThreshold_revPerMin,
            whole-range mean/median for:
              1) BoutSpeed_revPerMin
              2) BoutDuration_minute
              3) InterBoutInterval_minute
              4) WithinBoutAcceleration_deltaRevPerMin
            phase-specific mean/median columns for the same four metrics.
        """
        phase_specs = [
            ('Light_06-18', 6, 18),
            ('Dark_18-24', 18, 24),
            ('Dark_00-06', 0, 6),
            # Additional focused early-dark sub-window.
            # This overlaps with Dark phase 1 rather than replacing it.
            ('Dark_18-21', 18, 21),
        ]

        def _phases_for_timestamp(ts):
            """
            Return all phase labels that should receive this timestamp.

            Dark phase 3 is intentionally overlapping:
            18:00-21:00 is counted in both Dark phase 1 and Dark phase 3.
            """
            hour = pd.Timestamp(ts).hour + pd.Timestamp(ts).minute / 60.0 + pd.Timestamp(ts).second / 3600.0
            phases = []
            if 6 <= hour < 18:
                phases.append('Light_06-18')
            elif 18 <= hour < 24:
                phases.append('Dark_18-24')
                if 18 <= hour < 21:
                    phases.append('Dark_18-21')
            else:
                phases.append('Dark_00-06')
            return phases

        def _safe_phase_prefix(phase_name):
            return (
                phase_name.replace(' ', '_')
                .replace('-', '_')
                .replace(':', '')
            )

        def _empty_phase_dict():
            return {phase_name: [] for phase_name, _, _ in phase_specs}

        def analyze_mouse_bouts(mouse_df, rev_col, threshold=10):
            bout_speeds = []
            bout_durations = []
            inter_bout_intervals = []

            speed_by_phase = _empty_phase_dict()
            duration_by_phase = _empty_phase_dict()
            ibi_by_phase = _empty_phase_dict()

            for _, day_df in mouse_df.groupby('DateIndex'):
                day_df = day_df.sort_values('Bin').copy()
                if rev_col not in day_df.columns:
                    continue

                revs = pd.to_numeric(day_df[rev_col], errors='coerce').fillna(0.0)
                revs = revs.where(revs >= threshold, 0.0)
                active = revs > 0
                if not active.any():
                    continue

                run_id = (active != active.shift(fill_value=False)).cumsum()
                active_runs = []

                for _, group in revs.groupby(run_id):
                    if not active.loc[group.index].iloc[0]:
                        continue

                    if truncate_flag and len(group) >= 3:
                        group_for_stats = group[1:-1]
                    else:
                        group_for_stats = group

                    if len(group_for_stats) == 0:
                        continue

                    start_idx = group.index[0]
                    end_idx = group.index[-1]
                    start_ts = pd.Timestamp(day_df.loc[start_idx, 'Bin'])
                    phase_names = _phases_for_timestamp(start_ts)

                    duration_val = float(len(group_for_stats))
                    speed_val = float(group_for_stats.mean())

                    bout_durations.append(duration_val)
                    bout_speeds.append(speed_val)
                    for phase_name in phase_names:
                        duration_by_phase[phase_name].append(duration_val)
                        speed_by_phase[phase_name].append(speed_val)

                    active_runs.append({
                        'start_idx': start_idx,
                        'end_idx': end_idx,
                        'start_ts': start_ts,
                        'end_ts': pd.Timestamp(day_df.loc[end_idx, 'Bin']),
                    })

                for i in range(len(active_runs) - 1):
                    current_end_idx = active_runs[i]['end_idx']
                    next_start_idx = active_runs[i + 1]['start_idx']
                    ibi_val = float(next_start_idx - current_end_idx - 1)
                    if ibi_val >= 1:
                        inter_bout_intervals.append(ibi_val)

                        # Match the interval timing convention used in the audit list:
                        # phase is assigned by the previous bout end timestamp.
                        phase_names = _phases_for_timestamp(active_runs[i]['end_ts'])
                        for phase_name in phase_names:
                            ibi_by_phase[phase_name].append(ibi_val)

            return {
                'speeds': bout_speeds,
                'durations': bout_durations,
                'intervals': inter_bout_intervals,
                'speed_by_phase': speed_by_phase,
                'duration_by_phase': duration_by_phase,
                'ibi_by_phase': ibi_by_phase,
            }

        def collect_accelerations(mouse_list, df_src, threshold=10):
            accels = []
            accels_by_phase = _empty_phase_dict()

            for mid in mouse_list:
                rev_col = f'1 8 {mid} rev'
                if rev_col not in df_src.columns:
                    continue

                for _, day_df in df_src.groupby('DateIndex'):
                    day_df = day_df.sort_values('Bin').copy()
                    revs_series = pd.to_numeric(day_df[rev_col], errors='coerce').fillna(0.0)
                    revs_series = revs_series.where(revs_series >= threshold, 0.0)
                    revs = revs_series.values
                    active = revs > 0

                    for i in range(1, len(revs)):
                        if active[i] and active[i - 1]:
                            delta = float(revs[i] - revs[i - 1])
                            if acc_nozero and delta == 0:
                                continue

                            accels.append(delta)

                            ts = pd.Timestamp(day_df.iloc[i]['Bin'])
                            phase_names = _phases_for_timestamp(ts)
                            for phase_name in phase_names:
                                accels_by_phase[phase_name].append(delta)

            return accels, accels_by_phase

        def value_stats(values):
            arr = np.asarray(values, dtype=float)
            arr = arr[~np.isnan(arr)]
            if len(arr) == 0:
                return {'mean': np.nan, 'median': np.nan}
            return {'mean': float(np.mean(arr)), 'median': float(np.median(arr))}

        def add_metric_stats_to_row(row, prefix, values):
            stats = value_stats(values)
            row[f'{prefix}_mean'] = round(stats['mean'], 4) if not np.isnan(stats['mean']) else np.nan
            row[f'{prefix}_median'] = round(stats['median'], 4) if not np.isnan(stats['median']) else np.nan

        def add_phase_metric_stats_to_row(row, phase_name, metric_prefix, values):
            phase_prefix = _safe_phase_prefix(phase_name)
            add_metric_stats_to_row(row, f'{phase_prefix}_{metric_prefix}', values)

        per_mouse_metric_rows = []
        for cohort_num in sorted(cohort_data_dict.keys()):
            cohort_info = cohort_data_dict[cohort_num]
            df_c = cohort_info['df']
            all_mice = cohort_info.get('snr_mice', []) + cohort_info.get('ctrl_mice', [])

            for mid in all_mice:
                rev_col = f'1 8 {mid} rev'
                if rev_col not in df_c.columns:
                    continue

                labels = cohort_info.get('labels', [])
                label = labels[int(mid) - 1] if int(mid) - 1 < len(labels) else f'Mouse {mid}'
                group = label.split('(')[1][:-1] if '(' in label and ')' in label else 'Unknown'

                mouse_df = df_c[['Bin', 'DateIndex', rev_col]].copy()

                # Average daily revolutions across the selected experimental days.
                # For each mouse, first sum total revolutions within each DateIndex,
                # then average those daily totals across days.
                rev_for_daily = pd.to_numeric(mouse_df[rev_col], errors='coerce').fillna(0.0)
                daily_revs = (
                    pd.DataFrame({
                        'DateIndex': mouse_df['DateIndex'].values,
                        'Revs': rev_for_daily.values
                    })
                    .groupby('DateIndex')['Revs']
                    .sum()
                    .reindex(range(day_min, day_max + 1), fill_value=0.0)
                )
                avg_daily_revs = float(daily_revs.mean()) if len(daily_revs) > 0 else np.nan
                median_daily_revs = float(daily_revs.median()) if len(daily_revs) > 0 else np.nan
                total_revs_selected_days = float(daily_revs.sum()) if len(daily_revs) > 0 else np.nan

                bout_stats = analyze_mouse_bouts(mouse_df, rev_col, threshold)

                speeds = bout_stats['speeds']
                durations = bout_stats['durations']
                intervals = [x for x in bout_stats['intervals'] if x >= 1]

                # Phase-specific intervals should use the same x >= 1 filter.
                ibi_by_phase = {
                    phase_name: [x for x in vals if x >= 1]
                    for phase_name, vals in bout_stats['ibi_by_phase'].items()
                }

                accels, accels_by_phase = collect_accelerations([mid], df_c, threshold)

                row = {
                    'Cohort': cohort_num,
                    'ID': label[0:4],
                    'Group': group,
                    'MouseLabel': label,
                    'Day': str(day_min) + ' - ' + str(day_max),
                    'BoutThreshold_revPerMin': threshold,
                    'Revolutions_avgDaily_mean': round(avg_daily_revs, 4) if not np.isnan(avg_daily_revs) else np.nan,
                    'Revolutions_avgDaily_median': round(median_daily_revs, 4) if not np.isnan(median_daily_revs) else np.nan,
                }

                # Whole selected-day-range metrics, preserving previous column names.
                add_metric_stats_to_row(row, 'BoutSpeed_revPerMin', speeds)
                add_metric_stats_to_row(row, 'BoutDuration_minute', durations)
                add_metric_stats_to_row(row, 'InterBoutInterval_minute', intervals)
                add_metric_stats_to_row(row, 'WithinBoutAcceleration_deltaRevPerMin', accels)

                # Phase-split metrics.
                for phase_name, _, _ in phase_specs:
                    add_phase_metric_stats_to_row(
                        row, phase_name, 'BoutSpeed_revPerMin',
                        bout_stats['speed_by_phase'].get(phase_name, [])
                    )
                    add_phase_metric_stats_to_row(
                        row, phase_name, 'BoutDuration_minute',
                        bout_stats['duration_by_phase'].get(phase_name, [])
                    )
                    add_phase_metric_stats_to_row(
                        row, phase_name, 'InterBoutInterval_minute',
                        ibi_by_phase.get(phase_name, [])
                    )
                    add_phase_metric_stats_to_row(
                        row, phase_name, 'WithinBoutAcceleration_deltaRevPerMin',
                        accels_by_phase.get(phase_name, [])
                    )

                per_mouse_metric_rows.append(row)

        if not per_mouse_metric_rows:
            return pd.DataFrame()
        return pd.DataFrame(per_mouse_metric_rows).sort_values(['Cohort', 'ID'])


    def _ask_remove_lm45_from_mouse_pool(self, context="this analysis"):
        """
        Ask whether LM45 should be excluded from the mouse pool for the current analysis.
        Returns True if LM45 should be removed.
        """
        try:
            return messagebox.askyesno(
                "Remove LM45?",
                f"Remove LM45 from the mouse pool for {context}?\n\n"
                "Yes = exclude LM45\n"
                "No = keep LM45"
            )
        except Exception:
            return False

    def _apply_lm45_mouse_filter(self, mouse_ids, mouse_labels=None, remove_lm45=False, cohort_num=None, context=""):
        """
        Remove LM45 from a list of mouse IDs when requested.

        Important:
        - LM45 is mouse ID 2 only in cohort 1.
        - Mouse ID 2 in other cohorts is a different mouse and must not be removed.
        - Therefore, this filter removes only IDs whose label explicitly contains "LM45".
        - As an additional safety fallback, mouse ID 2 can only be treated as LM45 when cohort_num == 1.
        """
        mouse_ids = [int(mid) for mid in list(mouse_ids)]
        if not remove_lm45:
            return mouse_ids

        lm45_ids = set()
        if mouse_labels:
            for idx, label in enumerate(mouse_labels, start=1):
                if "LM45" in str(label):
                    lm45_ids.add(idx)

        # Safety fallback only for cohort 1. Never remove mouse ID 2 from other cohorts.
        if not lm45_ids and cohort_num == 1:
            lm45_ids.add(2)

        if not lm45_ids:
            return mouse_ids

        kept = [mid for mid in mouse_ids if int(mid) not in lm45_ids]
        removed = sorted(set(mouse_ids) - set(kept))
        if removed:
            print(f"[LM45 filter{': ' + context if context else ''}] removed mouse IDs {removed} from cohort {cohort_num}; kept {kept}")
        return kept

    def _print_mouse_candidates(self, context, cohort_num, mouse_ids, mouse_labels=None, stage=""):
        """
        Print exact mouse IDs and labels used by actogram/bout-statistics candidate filters.
        This is especially useful for verifying that LM45 is kept or removed only when intended.
        """
        try:
            ids = [int(mid) for mid in list(mouse_ids)]
        except Exception:
            ids = list(mouse_ids)

        tag = f"[{context}]"
        if cohort_num is not None:
            tag += f" Cohort {cohort_num}"
        if stage:
            tag += f" | {stage}"
        print(tag)

        if not ids:
            print("    No candidate mice.")
            return

        for mid in sorted(ids):
            label = ""
            try:
                if mouse_labels is not None and int(mid) - 1 < len(mouse_labels):
                    label = str(mouse_labels[int(mid) - 1])
            except Exception:
                label = ""
            if label:
                print(f"    mouse ID {mid}: {label}")
            else:
                print(f"    mouse ID {mid}")


    def bout_interval_csv_plot(self):
        """
        Export one audit CSV containing both classic bout rows and classic inter-bout
        interval rows, using the same bout-detection logic as
        generate_bout_statistics_summary_multi_cohort().

        Counting logic:
        - Bout = contiguous minutes with rev >= 10.
        - Bout speed = mean rev/min within that active run.
        - Bout duration = number of active minutes in that run.
        - Inter-bout interval = next bout start index - previous bout end index - 1,
          excluding the boundary minutes occupied by the two bouts.
        - No-bout days/windows do not generate interval rows.
        """
        DAY_MIN = 8
        DAY_MAX = 21
        LIGHT_ON_HOUR = 6
        BOUT_THRESHOLD_REVS_PER_MIN = 10

        file_paths = filedialog.askopenfilenames(
            title="Select cohort files for bout + interval audit CSV",
            filetypes=[("Data Files", "*.csv *.xls *.xlsx")]
        )
        if not file_paths:
            messagebox.showinfo("No Files", "No files selected.")
            return

        sex_csv_path = filedialog.askopenfilename(
            title="Select mouse sex CSV for bout metric sex-split plots",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        sex_lookup = {}
        if sex_csv_path:
            try:
                sex_df = pd.read_csv(sex_csv_path)
                if ('ID' not in sex_df.columns) or ('Sex' not in sex_df.columns):
                    messagebox.showwarning(
                        "Sex CSV warning",
                        "Sex CSV must contain columns named 'ID' and 'Sex'.\n"
                        "The sex-split bout metric plot will be skipped unless sex can be inferred."
                    )
                else:
                    for _, row in sex_df.iterrows():
                        sid = str(row['ID']).strip().lower()
                        sex = str(row['Sex']).strip().upper()
                        if sex.startswith('F'):
                            sex_lookup[sid] = 'Female'
                        elif sex.startswith('M'):
                            sex_lookup[sid] = 'Male'
                    print(f"Loaded sex metadata for {len(sex_lookup)} mouse IDs from: {sex_csv_path}")
            except Exception as e:
                messagebox.showwarning(
                    "Sex CSV warning",
                    f"Could not read sex CSV:\n{e}\n\n"
                    "The sex-split bout metric plot will be skipped."
                )
                sex_lookup = {}
        else:
            print("No sex CSV selected; sex-split bout metric plot will be skipped.")

        remove_lm45 = self._ask_remove_lm45_from_mouse_pool("bout + interval audit CSV export")

        # This export function keeps the historical cohort-2 default exclusion.
        # These defaults are required because _included_mice() references the same modular flags
        # used by other plotting functions.
        include_sc04 = False
        include_sc05 = False
        include_sc06 = False
        use_cohort2_special_colors = False

        def _ask_window_minutes():
            """
            Ask for temporal resolution in minutes.
            Recommended values: 5, 10, or 20.
            """
            val = simpledialog.askinteger(
                "Temporal resolution for mouse-day UMAP",
                "Enter temporal resolution in minutes.\nRecommended: 5, 10, or 20",
                initialvalue=10,
                parent=self.root,
                minvalue=1
            )
            if val is None:
                return None
            if val not in [5, 10, 20] and (60 % val != 0):
                messagebox.showerror(
                    "Invalid temporal resolution",
                    "Please choose a value that divides 60 evenly.\nRecommended values are 5, 10, or 20."
                )
                return None
            return int(val)

        def _cohort_num_from_path(file_path):
            base = os.path.splitext(os.path.basename(file_path))[0]
            patterns = [r'(?i)cohort[_\-\s]*([1-4])', r'(?i)c[_\-\s]*([1-4])', r'(?i)p\d+c([1-4])']
            for pat in patterns:
                m = re.search(pat, base)
                if m:
                    return int(m.group(1))
            m = re.search(r'([1-4])$', base)
            if m:
                return int(m.group(1))
            raise ValueError(f"Could not infer cohort number from filename: {os.path.basename(file_path)}")

        def _mouse_labels_for_cohort(cohort_num):
            if cohort_num == 1:
                return ["SC01(Control)", "LM45(SNr-DTA)", "SC02(GPi-DTA)"]
            if cohort_num == 2:
                return ["SC04(SNr-DTA)", "SC05(SNr-DTA)", "SC06(SNr-DTA)", "SC07(Control)", "SC08(Control)"]
            if cohort_num == 3:
                return ["SC09(SNr-DTA)", "SC10(SNr-DTA)", "SC11(SNr-DTA)", "SC12(SNr-DTA)", "SC13(Control)", "SC14(Control)", "SC15(Control)"]
            if cohort_num == 4:
                return ["SC29(SNr-DTA)", "SC30(SNr-DTA)", "SC31(SNr-DTA)", "SC32(SNr-DTA)", "SC33(Control)", "SC34(Control)", "SC35(Control)"]
            return []

        def _included_mice(mouse_ids, cohort_num):
            mouse_ids = list(mouse_ids)
            if cohort_num == 1:
                for i in [3, 5, 6, 7]:
                    if i in mouse_ids:
                        mouse_ids.remove(i)
            if cohort_num == 2:
                # Cohort 2 exclusion rule:
                # remove mouse IDs 1, 2, 3, and 4.
                # SC08 = mouse ID 5 remains available.
                for i in [1, 2, 3, 4]:
                    if i in mouse_ids:
                        mouse_ids.remove(i)
            if cohort_num == 4:
                for i in [7]:
                    if i in mouse_ids:
                        mouse_ids.remove(i)
            return mouse_ids

        def _group_from_label(mouse_label):
            if 'SNr' in mouse_label or 'DTA' in mouse_label:
                return 'SNr-DTA'
            if 'Control' in mouse_label:
                return 'Control'
            if 'GPi' in mouse_label:
                return 'GPi-DTA'
            return 'Unknown'

        def _load_cohort_file(file_path):
            cohort_num = _cohort_num_from_path(file_path)
            mouse_labels = _mouse_labels_for_cohort(cohort_num)
            if file_path.endswith('.xls') or file_path.endswith('.xlsx'):
                try:
                    df = pd.read_csv(file_path, skiprows=10, sep='\t')
                except Exception:
                    df = pd.read_csv(file_path, skiprows=10)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path, skiprows=10)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
            df = df.dropna(how='all').dropna(axis=1, how='all')
            df.columns = [col.strip() for col in df.columns]
            if 'Bin' not in df.columns:
                raise ValueError(f"Missing 'Bin' column in {os.path.basename(file_path)}")
            df['Bin'] = pd.to_datetime(df['Bin'], format='mixed', errors='coerce')
            df = df.dropna(subset=['Bin'])
            reference_date = df['Bin'].dt.normalize().min().date()
            if cohort_num == 3:
                reference_date = reference_date - timedelta(days=8)
            ref_ts = pd.Timestamp(reference_date)
            df['DateIndex'] = (df['Bin'].dt.normalize() - ref_ts).dt.days
            df = df[(df['DateIndex'] >= DAY_MIN) & (df['DateIndex'] <= DAY_MAX)].copy()
            mouse_ids = sorted(set(col.split()[2] for col in df.columns if col.startswith('1 8')))
            mouse_ids = [int(m) for m in mouse_ids if str(m).isdigit()]
            mouse_ids = _included_mice(mouse_ids, cohort_num)
            mouse_ids = self._apply_lm45_mouse_filter(
                mouse_ids, mouse_labels, remove_lm45,
                cohort_num=cohort_num, context='bout + interval audit CSV export'
            )
            return cohort_num, mouse_labels, df, mouse_ids

        def _fmt_hhmm(ts):
            if pd.isna(ts):
                return ''
            return pd.Timestamp(ts).strftime('%H:%M')

        def _clock_bin_label(ts, bin_hours):
            ts = pd.Timestamp(ts)
            clock_hour = ts.hour + ts.minute / 60.0 + ts.second / 3600.0
            bin_idx = int(np.floor(((clock_hour - LIGHT_ON_HOUR) % 24) / bin_hours))
            start_hour = int((LIGHT_ON_HOUR + bin_idx * bin_hours) % 24)
            end_hour = int((LIGHT_ON_HOUR + (bin_idx + 1) * bin_hours) % 24)
            end_label = 24 if end_hour == 0 else end_hour
            return f'"{start_hour:02d}-{end_label:02d}"'

        def _sex_lookup_id_from_label(mouse_label):
            label = str(mouse_label).strip()
            m = re.search(r'(SC\d+|LM45)', label, flags=re.IGNORECASE)
            if m:
                return m.group(1).lower()
            return label.split('(')[0].strip().lower()

        def _sex_from_label(mouse_label):
            return sex_lookup.get(_sex_lookup_id_from_label(mouse_label), 'Unknown')

        def _extract_bout_and_interval_rows(mouse_df, rev_col, cohort_num, mouse_id, mouse_label, group):
            rows = []
            work = mouse_df[['Bin', 'DateIndex', rev_col]].copy()
            work[rev_col] = pd.to_numeric(work[rev_col], errors='coerce').fillna(0.0)

            for date_index, day_df in work.groupby('DateIndex'):
                day_df = day_df.sort_values('Bin').copy()
                if day_df.empty or rev_col not in day_df.columns:
                    continue

                # Keep this logic aligned with generate_bout_statistics_summary_multi_cohort():
                # active minutes are rev >= threshold; consecutive active minutes form one bout.
                revs = pd.to_numeric(day_df[rev_col], errors='coerce').fillna(0.0)
                revs = revs.where(revs >= BOUT_THRESHOLD_REVS_PER_MIN, 0.0)
                active = revs > 0
                if not active.any():
                    continue

                run_id = (active != active.shift(fill_value=False)).cumsum()
                active_runs = []
                for _, group_revs in revs.groupby(run_id):
                    if not active.loc[group_revs.index].iloc[0]:
                        continue
                    start_idx = group_revs.index[0]
                    end_idx = group_revs.index[-1]
                    start_ts = pd.Timestamp(day_df.loc[start_idx, 'Bin'])
                    end_ts = pd.Timestamp(day_df.loc[end_idx, 'Bin'])
                    duration_min = int(len(group_revs))
                    speed_mean = float(group_revs.mean())
                    rev_sum = float(group_revs.sum())
                    active_runs.append({
                        'start_idx': start_idx,
                        'end_idx': end_idx,
                        'start_ts': start_ts,
                        'end_ts': end_ts,
                        'duration_min': duration_min,
                        'speed_mean': speed_mean,
                        'rev_sum': rev_sum,
                    })

                    rows.append({
                        'Cohort': cohort_num,
                        'ID': mouse_label[0:4],
                        'Group': group,
                        'DateIndex': int(date_index) if not pd.isna(date_index) else np.nan,
                        'Real Date': start_ts.date().isoformat(),
                        'PeriodType': 'bout',
                        'StartStamp': start_ts,
                        'EndStamp': end_ts,
                        'StartClock': _fmt_hhmm(start_ts),
                        'EndClock': _fmt_hhmm(end_ts),
                        'ClockBin_3h': _clock_bin_label(start_ts, 3),
                        'ClockBin_6h': _clock_bin_label(start_ts, 6),
                        'Duration_min': duration_min,
                        'BoutSpeed_revPerMin': round(speed_mean, 6),
                        'BoutTotalRevs': round(rev_sum, 6),
                        'PreviousBoutEndClock': '',
                        'NextBoutStartClock': '',
                        'CountingLogic': 'bout = contiguous minutes with rev >= threshold; same as generate_bout_statistics_summary_multi_cohort',
                        'BoutThreshold_revs_per_min': BOUT_THRESHOLD_REVS_PER_MIN,
                    })

                # Classic IBI rows, matching generate_bout_statistics_summary_multi_cohort():
                # IBI is exclusive of the two bout-boundary minutes:
                #   first IBI minute = previous bout end + 1 min
                #   last IBI minute  = next bout start - 1 min
                #   duration = next_start_idx - previous_end_idx - 1
                for i in range(len(active_runs) - 1):
                    current_run = active_runs[i]
                    next_run = active_runs[i + 1]
                    interval_min = int(next_run['start_idx'] - current_run['end_idx'] - 1)
                    if interval_min < 1:
                        continue
                    interval_start_ts = current_run['end_ts'] + pd.Timedelta(minutes=1)
                    interval_end_ts = next_run['start_ts'] - pd.Timedelta(minutes=1)
                    rows.append({
                        'Cohort': cohort_num,
                        'ID': mouse_label[0:4],
                        'Group': group,
                        'DateIndex': int(date_index) if not pd.isna(date_index) else np.nan,
                        'Real Date': interval_start_ts.date().isoformat(),
                        'PeriodType': 'inter_bout_interval',
                        'StartStamp': interval_start_ts,
                        'EndStamp': interval_end_ts,
                        'StartClock': _fmt_hhmm(interval_start_ts),
                        'EndClock': _fmt_hhmm(interval_end_ts),
                        'ClockBin_3h': _clock_bin_label(interval_start_ts, 3),
                        'ClockBin_6h': _clock_bin_label(interval_start_ts, 6),
                        'Duration_min': interval_min,
                        'BoutSpeed_revPerMin': np.nan,
                        'BoutTotalRevs': np.nan,
                        'PreviousBoutEndClock': _fmt_hhmm(current_run['end_ts']),
                        'NextBoutStartClock': _fmt_hhmm(next_run['start_ts']),
                        'CountingLogic': 'IBI is exclusive: next bout start index - previous bout end index - 1; boundary bout minutes are excluded',
                        'BoutThreshold_revs_per_min': BOUT_THRESHOLD_REVS_PER_MIN,
                    })
            return rows

        def _make_bout_metric_sex_split_plot(per_mouse_metric_df, output_dir):
            """
            Create one PDF page per metric pair in the per-mouse metric table.

            For each metric prefix with both *_median and *_mean columns:
              - upper panel: per-mouse median values
              - lower panel: per-mouse mean values

            X-axis order:
              SNr-DTA Female, SNr-DTA Male, Control Female, Control Male
            """
            if per_mouse_metric_df is None or per_mouse_metric_df.empty:
                return 'N/A', 'N/A'

            plot_df = per_mouse_metric_df.copy()
            plot_df['SexLookupID'] = plot_df['MouseLabel'].apply(_sex_lookup_id_from_label)
            plot_df['Sex'] = plot_df['MouseLabel'].apply(_sex_from_label)

            if (not sex_lookup) or (plot_df['Sex'].eq('Unknown').all()):
                print("Skipping sex-split bout metric plot: no usable sex metadata.")
                return 'N/A', 'N/A'

            # Find metric pairs automatically.
            mean_cols = [c for c in plot_df.columns if c.endswith('_mean')]
            metric_pairs = []
            for mean_col in mean_cols:
                prefix = mean_col[:-5]
                median_col = prefix + '_median'
                if median_col in plot_df.columns:
                    # Skip pure metadata or helper columns if any appear.
                    if prefix in ['']:
                        continue
                    metric_pairs.append((prefix, mean_col, median_col))

            if not metric_pairs:
                print("No *_mean / *_median metric pairs found for sex-split visualization.")
                return 'N/A', 'N/A'

            group_sex_order = [
                ('SNr-DTA', 'Female'),
                ('SNr-DTA', 'Male'),
                ('Control', 'Female'),
                ('Control', 'Male'),
            ]
            x_labels = ['SNr-DTA\nFemale', 'SNr-DTA\nMale', 'Control\nFemale', 'Control\nMale']
            color_map = {
                ('SNr-DTA', 'Female'): (0.95, 0.45, 0.45),
                ('SNr-DTA', 'Male'): (0.70, 0.05, 0.05),
                ('Control', 'Female'): (0.45, 0.65, 0.95),
                ('Control', 'Male'): (0.05, 0.20, 0.70),
            }

            def _sem(vals):
                vals = np.asarray(vals, dtype=float)
                vals = vals[np.isfinite(vals)]
                if len(vals) <= 1:
                    return 0.0
                return float(np.std(vals, ddof=1) / np.sqrt(len(vals)))

            def _draw_flat_metric_panel(ax, value_col, title_text, y_label):
                rng = np.random.default_rng(42)
                for xi, (group_name, sex_name) in enumerate(group_sex_order):
                    sub = plot_df[
                        (plot_df['Group'] == group_name) &
                        (plot_df['Sex'] == sex_name)
                    ].copy()
                    vals = pd.to_numeric(sub[value_col], errors='coerce').to_numpy(dtype=float)
                    vals = vals[np.isfinite(vals)]
                    color = color_map[(group_name, sex_name)]

                    if len(vals) > 0:
                        jitter = rng.normal(0, 0.035, size=len(vals))
                        ax.scatter(
                            np.full(len(vals), xi, dtype=float) + jitter,
                            vals,
                            s=58,
                            color=color,
                            edgecolor='black',
                            linewidth=0.75,
                            alpha=0.92,
                            zorder=3
                        )

                        center_val = float(np.mean(vals))
                        sem_val = _sem(vals)
                        ax.errorbar(
                            [xi],
                            [center_val],
                            yerr=[sem_val],
                            fmt='D',
                            color=color,
                            ecolor=color,
                            markeredgecolor='black',
                            markeredgewidth=0.8,
                            markersize=8,
                            capsize=4,
                            linewidth=1.8,
                            zorder=5
                        )

                        ax.text(
                            xi,
                            center_val,
                            f'n={len(vals)}',
                            ha='center',
                            va='bottom',
                            fontsize=8,
                            fontweight='bold'
                        )

                ax.set_title(title_text, fontsize=12, fontweight='bold')
                ax.set_ylabel(y_label, fontsize=10.5, fontweight='bold')
                ax.set_xticks(np.arange(len(group_sex_order)))
                ax.set_xticklabels(x_labels, fontsize=9)
                ax.grid(True, axis='y', alpha=0.3)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)

            pdf_path = os.path.join(output_dir, f'BoutInterval_MetricVisualization_ByGroupSex_D{DAY_MIN}-{DAY_MAX}.pdf')
            stats_csv_path = os.path.join(output_dir, f'BoutInterval_MetricVisualization_ByGroupSex_Stats_D{DAY_MIN}-{DAY_MAX}.csv')

            stats_rows = []
            for prefix, mean_col, median_col in metric_pairs:
                for value_type, col in [('mean', mean_col), ('median', median_col)]:
                    for group_name, sex_name in group_sex_order:
                        sub = plot_df[
                            (plot_df['Group'] == group_name) &
                            (plot_df['Sex'] == sex_name)
                        ].copy()
                        vals = pd.to_numeric(sub[col], errors='coerce').to_numpy(dtype=float)
                        vals = vals[np.isfinite(vals)]
                        stats_rows.append({
                            'MetricPrefix': prefix,
                            'ValueType': value_type,
                            'Column': col,
                            'Group': group_name,
                            'Sex': sex_name,
                            'n': int(len(vals)),
                            'MeanOfMouseValues': float(np.mean(vals)) if len(vals) else np.nan,
                            'MedianOfMouseValues': float(np.median(vals)) if len(vals) else np.nan,
                            'SEM': _sem(vals) if len(vals) else np.nan,
                            'SD': float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0 if len(vals) == 1 else np.nan,
                        })
            pd.DataFrame(stats_rows).to_csv(stats_csv_path, index=False)

            with PdfPages(pdf_path) as pdf:
                for prefix, mean_col, median_col in metric_pairs:
                    pretty_metric = prefix.replace('_', ' ')
                    fig, axes = plt.subplots(2, 1, figsize=(9.5, 8.3), sharex=True)
                    _draw_flat_metric_panel(
                        axes[0],
                        median_col,
                        f'{pretty_metric}: per-mouse medians',
                        'Per-mouse median value'
                    )
                    _draw_flat_metric_panel(
                        axes[1],
                        mean_col,
                        f'{pretty_metric}: per-mouse means',
                        'Per-mouse mean value'
                    )
                    fig.suptitle(
                        f'{pretty_metric}\nGroup first, sex split second',
                        fontsize=14,
                        fontweight='bold'
                    )
                    fig.text(
                        0.5, 0.01,
                        'Each point = one mouse. Diamond/error bar = subgroup mean ± SEM of mouse-level values.',
                        ha='center',
                        va='bottom',
                        fontsize=8.8
                    )
                    plt.tight_layout(rect=[0, 0.035, 1, 0.94])
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close(fig)

            print(f"Saved sex-split bout metric visualization PDF: {pdf_path}")
            print(f"Saved sex-split bout metric visualization stats CSV: {stats_csv_path}")
            return pdf_path, stats_csv_path

        all_rows = []
        loaded_cohorts = []
        cohort_data_dict = {}
        for file_path in file_paths:
            try:
                cohort_num, mouse_labels, df, mouse_ids = _load_cohort_file(file_path)
                loaded_cohorts.append(cohort_num)

                snr_mice = []
                ctrl_mice = []
                for mid_tmp in mouse_ids:
                    if mid_tmp - 1 < len(mouse_labels):
                        label_tmp = mouse_labels[mid_tmp - 1]
                        group_tmp = _group_from_label(label_tmp)
                        if group_tmp == 'SNr-DTA':
                            snr_mice.append(mid_tmp)
                        elif group_tmp == 'Control':
                            ctrl_mice.append(mid_tmp)
                cohort_data_dict[cohort_num] = {
                    'df': df,
                    'labels': mouse_labels,
                    'snr_mice': snr_mice,
                    'ctrl_mice': ctrl_mice,
                }

                for mid in mouse_ids:
                    rev_col = f'1 8 {mid} rev'
                    if rev_col not in df.columns:
                        continue
                    mouse_label = mouse_labels[mid - 1] if (mid - 1) < len(mouse_labels) else f'Mouse{mid}'
                    group = _group_from_label(mouse_label)
                    mouse_df = df[['Bin', 'DateIndex', rev_col]].copy()
                    all_rows.extend(_extract_bout_and_interval_rows(
                        mouse_df=mouse_df,
                        rev_col=rev_col,
                        cohort_num=cohort_num,
                        mouse_id=mid,
                        mouse_label=mouse_label,
                        group=group,
                    ))
                print(f"Processed cohort {cohort_num}: {len(mouse_ids)} included mice")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        loaded_cohorts = sorted(set(loaded_cohorts))
        cohort_str = '_'.join([f'C{c}' for c in loaded_cohorts]) if loaded_cohorts else 'selected'
        csv_path = f'./BoutAndInterval_AuditList_sameCountingAsHistogram_{cohort_str}_D{DAY_MIN}-{DAY_MAX}.csv'
        out_df = pd.DataFrame(all_rows)
        if not out_df.empty:
            column_order = [
                'Cohort', 'ID', 'Group', 'DateIndex', 'Real Date',
                'PeriodType', 'StartStamp', 'EndStamp', 'StartClock', 'EndClock',
                'ClockBin_3h', 'ClockBin_6h', 'Duration_min',
                'BoutSpeed_revPerMin', 'BoutTotalRevs',
                'PreviousBoutEndClock', 'NextBoutStartClock',
                'BoutThreshold_revs_per_min', 'CountingLogic'
            ]
            out_df = out_df[column_order]
            out_df = out_df.sort_values(['Cohort', 'ID', 'DateIndex', 'StartStamp', 'PeriodType'])
        out_df.to_csv(csv_path, index=False)

        per_mouse_metric_df = self._build_per_mouse_bout_metric_df(
            cohort_data_dict=cohort_data_dict,
            day_min=DAY_MIN,
            day_max=DAY_MAX,
            threshold=BOUT_THRESHOLD_REVS_PER_MIN,
            truncate_flag=0,
            acc_nozero=0,
        )
        if not per_mouse_metric_df.empty:
            per_mouse_metric_csv_path = os.path.join(
                os.path.dirname(os.path.abspath(csv_path)),
                self._per_mouse_bout_metric_csv_filename(DAY_MIN, DAY_MAX)
            )
            per_mouse_metric_df.to_csv(per_mouse_metric_csv_path, index=False)
            print(f"Saved per-mouse metric statistics CSV: {per_mouse_metric_csv_path}")

            bout_metric_plot_pdf_path, bout_metric_plot_stats_csv_path = _make_bout_metric_sex_split_plot(
                per_mouse_metric_df=per_mouse_metric_df,
                output_dir=os.path.dirname(os.path.abspath(csv_path))
            )
        else:
            per_mouse_metric_csv_path = 'N/A'
            bout_metric_plot_pdf_path = 'N/A'
            bout_metric_plot_stats_csv_path = 'N/A'
            print('Warning: No per-mouse metric rows generated from selected files.')

        print(f"Saved bout + interval audit CSV: {csv_path}")
        if out_df.empty:
            print("No bout or inter-bout interval rows found.")
            bout_n = interval_n = 0
        else:
            bout_n = int((out_df['PeriodType'] == 'bout').sum())
            interval_n = int((out_df['PeriodType'] == 'inter_bout_interval').sum())
            print(f"Audit rows: bouts={bout_n}, inter-bout intervals={interval_n}, total={len(out_df)}")
            print(out_df[['Cohort', 'ID', 'DateIndex', 'Real Date', 'PeriodType', 'StartClock', 'EndClock', 'Duration_min']].head(30).to_string(index=False))

        messagebox.showinfo(
            "Complete",
            f"Saved bout + interval audit CSV:\n{csv_path}\n\n"
            f"Saved per-mouse metric CSV:\n{per_mouse_metric_csv_path}\n\n"
            f"Saved sex-split metric PDF:\n{bout_metric_plot_pdf_path}\n\n"
            f"Saved sex-split metric stats CSV:\n{bout_metric_plot_stats_csv_path}\n\n"
            f"Bout rows: {bout_n}\n"
            f"Inter-bout interval rows: {interval_n}\n"
            f"Total rows: {len(out_df)}\n"
            f"Cohorts: {', '.join([str(c) for c in loaded_cohorts]) if loaded_cohorts else 'N/A'}\n\n"
            f"The CSV uses the same bout and IBI counting logic as generate_bout_statistics_summary_multi_cohort()."
        )



    def plot_custom_window_group_differences(self):
        """
        Custom-window group comparison.
        Each point in the statistics = one mouse summarized across days 8-21.
        """
        from matplotlib.backends.backend_pdf import PdfPages
        from tkinter import filedialog, messagebox, Toplevel, StringVar, Radiobutton, Button, Label, Frame
        import os
        import re

        try:
            from scipy import stats
        except Exception as e:
            messagebox.showerror("Missing dependency", f"scipy is required for this scan:\n{e}")
            return

        DAY_MIN = 8
        DAY_MAX = 21
        BOUT_THRESHOLD_REVS_PER_MIN = 10

        file_paths = filedialog.askopenfilenames(
            title="Select cohort files for discovery scan",
            filetypes=[("Data Files", "*.csv *.xls *.xlsx")]
        )
        if not file_paths:
            messagebox.showinfo("No Files", "No files selected.")
            return

        remove_lm45 = self._ask_remove_lm45_from_mouse_pool("discovery scan")

        # Cohort 2 mouse IDs 1-4 are excluded by rule; do not ask to include SC04/SC05/SC06.
        include_sc04 = False
        include_sc05 = False
        include_sc06 = False

        try:
            use_cohort2_special_colors = messagebox.askyesno(
                "Special colors for cohort 2?",
                "If cohort 2 mice SC04, SC05, SC06, or SC08 are included, use special colors?\n\n"
                "Yes = SC04/SC05/SC06 use orange gradients, SC08 uses gold-yellow\n"
                "No = use regular group colors"
            )
        except Exception:
            use_cohort2_special_colors = False

        def _cohort_num_from_path(file_path):
            base = os.path.splitext(os.path.basename(file_path))[0]
            patterns = [r'(?i)cohort[_\-\s]*([1-4])', r'(?i)c[_\-\s]*([1-4])', r'(?i)p\d+c([1-4])']
            for pat in patterns:
                m = re.search(pat, base)
                if m:
                    return int(m.group(1))
            m = re.search(r'([1-4])$', base)
            if m:
                return int(m.group(1))
            raise ValueError(f"Could not infer cohort number from filename: {os.path.basename(file_path)}")

        def _read_activity_file(file_path):
            if file_path.endswith('.xls') or file_path.endswith('.xlsx'):
                try:
                    return pd.read_csv(file_path, skiprows=10, sep='\t')
                except Exception:
                    return pd.read_csv(file_path, skiprows=10)
            if file_path.endswith('.csv'):
                return pd.read_csv(file_path, skiprows=10)
            raise ValueError(f"Unsupported file format: {file_path}")

        def _included_mice(mouse_ids, cohort_num):
            mouse_ids = list(mouse_ids)
            if cohort_num == 1:
                for i in [3, 5, 6, 7]:
                    if i in mouse_ids:
                        mouse_ids.remove(i)
            if cohort_num == 2:
                # Cohort 2 exclusion rule:
                # remove mouse IDs 1, 2, 3, and 4.
                # SC08 = mouse ID 5 remains available.
                for i in [1, 2, 3, 4]:
                    if i in mouse_ids:
                        mouse_ids.remove(i)
            if cohort_num == 4:
                for i in [7]:
                    if i in mouse_ids:
                        mouse_ids.remove(i)
            return mouse_ids

        def _group_from_label(label):
            if 'SNr' in label or 'DTA' in label:
                return 'SNr-DTA'
            if 'Control' in label:
                return 'Control'
            if 'GPi' in label:
                return 'GPi-DTA'
            return 'Unknown'

        def _cohort2_special_color_for_label(label):
            if not use_cohort2_special_colors:
                return None
            label_upper = str(label).upper()
            if 'SC04' in label_upper:
                return (0.95, 0.48, 0.05)
            if 'SC05' in label_upper:
                return (0.90, 0.35, 0.02)
            if 'SC06' in label_upper:
                return (0.75, 0.22, 0.00)
            if 'SC08' in label_upper:
                return '#FFD700'
            return None

        def _clock_hour(ts):
            ts = pd.Timestamp(ts)
            return ts.hour + ts.minute / 60.0 + ts.second / 3600.0

        def _in_window(ts, start_hour, end_hour):
            hour = _clock_hour(ts)
            if start_hour <= end_hour:
                return (hour >= start_hour) and (hour < end_hour)
            return (hour >= start_hour) or (hour < end_hour)

        def _parse_clock_to_hour(clock_text):
            clock_text = str(clock_text).strip()
            if ':' in clock_text:
                hh, mm = clock_text.split(':', 1)
                return int(hh) + int(mm) / 60.0
            return float(clock_text)

        def _format_hour_label(hour_float):
            hour_float = float(hour_float) % 24
            hh = int(np.floor(hour_float))
            mm = int(round((hour_float - hh) * 60))
            if mm == 60:
                hh = (hh + 1) % 24
                mm = 0
            return f'{hh:02d}:{mm:02d}'

        def _safe_window_name(name):
            name = str(name).strip()
            name = re.sub(r'[^A-Za-z0-9_\-]+', '_', name)
            name = re.sub(r'_+', '_', name).strip('_')
            return name if name else 'CustomWindow'

        def _ask_custom_window_specs():
            """
            Ask for custom clock windows.

            Format:
                WindowName, HH:MM-HH:MM
                WindowName2, HH:MM-HH:MM

            Example:
                Early sleep, 08:00-11:00
                Pre-dawn activity, 03:00-05:00
            """
            default_text = (
                'light1/4, 06:00-9:00\n'
                'light2/4, 09:00-12:00\n'
                'light3/4, 12:00-15:00\n'
                'light4/4, 15:00-18:00\n'
                'light1/2, 06:00-12:00\n'
                'light2/2, 12:00-18:00\n'
                'dark1/4, 18:00-21:00\n'
                'dark2/4, 21:00-24:00\n'
                'dark3/4, 00:00-03:00\n'
                'dark4/4, 03:00-06:00\n'
                'dark1/2, 18:00-24:00\n'
                'dark2/2, 00:00-06:00\n'
            )
            raw_text = simpledialog.askstring(
                'Customize time windows',
                'Enter one window per line:\n'
                'Format: Window name, start-end\n'
                'Example:\n'
                'Early sleep, 08:00-11:00\n'
                'Pre-dawn activity, 03:00-05:00\n\n'
                'Windows can cross midnight, e.g. Late night, 22:00-02:00',
                initialvalue=default_text,
                parent=self.root
            )
            if raw_text is None:
                return None

            specs = []
            for line in str(raw_text).splitlines():
                line = line.strip()
                if not line:
                    continue
                if ',' not in line or '-' not in line:
                    messagebox.showerror(
                        'Invalid time-window format',
                        f'Could not parse this line:\n{line}\n\n'
                        'Use format: Window name, HH:MM-HH:MM'
                    )
                    return None

                name_part, time_part = line.split(',', 1)
                start_text, end_text = time_part.split('-', 1)
                try:
                    start_hour = _parse_clock_to_hour(start_text)
                    end_hour = _parse_clock_to_hour(end_text)
                except Exception:
                    messagebox.showerror(
                        'Invalid clock time',
                        f'Could not parse clock times in line:\n{line}\n\n'
                        'Use examples like 08:00-11:00 or 3-5.'
                    )
                    return None

                if not (0 <= start_hour < 24) or not (0 <= end_hour <= 24):
                    messagebox.showerror(
                        'Invalid clock time',
                        f'Clock hours must be between 0 and 24 in line:\n{line}'
                    )
                    return None

                # Treat 24:00 as 00:00 for crossing-window logic and labels.
                end_hour = end_hour % 24

                clean_name = str(name_part).strip()
                clock_label = f'{_format_hour_label(start_hour)}-{_format_hour_label(end_hour)}'
                specs.append({
                    'Window': clean_name,
                    'WindowKey': _safe_window_name(clean_name),
                    'ClockWindow': clock_label,
                    'StartHour': float(start_hour),
                    'EndHour': float(end_hour),
                })

            if not specs:
                messagebox.showinfo('No windows', 'No valid windows were entered.')
                return None
            return specs

        window_specs = _ask_custom_window_specs()
        if not window_specs:
            return

        def _window_bounds_for_date(date_value, start_hour, end_hour):
            """
            Build absolute timestamps for a clock window on a given date.
            Supports windows crossing midnight.
            """
            base = pd.Timestamp(date_value).normalize()

            def _hour_to_delta(hour_float):
                hour_float = float(hour_float)
                hh = int(np.floor(hour_float))
                mm = int(round((hour_float - hh) * 60))
                return pd.Timedelta(hours=hh, minutes=mm)

            start_ts = base + _hour_to_delta(start_hour)
            end_ts = base + _hour_to_delta(end_hour)
            if end_hour <= start_hour:
                end_ts += pd.Timedelta(days=1)
            return start_ts, end_ts

        def _analyze_mouse_window(mouse_df, rev_col, start_hour, end_hour):
            """
            Compute per-mouse metrics within a custom clock window across days 8-21.

            Bout logic:
            - Detect complete daily bouts first.
            - Assign a bout to the window if its START time is inside the custom window.
            - Bout duration/speed are calculated from the full bout, not clipped window segments.

            InactivityInterval_mean:
            - Includes window start -> first bout.
            - Includes exclusive inactive gaps between bouts.
            - Includes last bout -> window end.
            - No-bout days are NaN rather than full-window duration.
            """
            daily_bout_counts = []
            daily_total_revs = []
            daily_active_minutes = []
            daily_inactivity_intervals = []

            all_bout_speeds = []
            all_bout_durations = []
            all_ibis = []

            for date_index in range(DAY_MIN, DAY_MAX + 1):
                day_df = mouse_df[mouse_df['DateIndex'] == date_index].sort_values('Bin').copy()
                if day_df.empty:
                    daily_bout_counts.append(0.0)
                    daily_total_revs.append(0.0)
                    daily_active_minutes.append(0.0)
                    daily_inactivity_intervals.append(np.nan)
                    continue

                day_date = pd.Timestamp(day_df['Bin'].dt.normalize().iloc[0])
                window_start_ts, window_end_ts = _window_bounds_for_date(day_date, start_hour, end_hour)

                # Window rows may cross midnight, so use absolute timestamps.
                win_df = mouse_df[
                    (mouse_df['Bin'] >= window_start_ts) &
                    (mouse_df['Bin'] < window_end_ts)
                ].sort_values('Bin').copy()

                if win_df.empty:
                    daily_bout_counts.append(0.0)
                    daily_total_revs.append(0.0)
                    daily_active_minutes.append(0.0)
                    daily_inactivity_intervals.append(np.nan)
                    continue

                raw_revs_window = pd.to_numeric(win_df[rev_col], errors='coerce').fillna(0.0)
                active_window = raw_revs_window >= BOUT_THRESHOLD_REVS_PER_MIN
                daily_total_revs.append(float(raw_revs_window.sum()))
                daily_active_minutes.append(float(active_window.sum()))

                # Detect full-day bouts first.
                revs = pd.to_numeric(day_df[rev_col], errors='coerce').fillna(0.0)
                revs = revs.where(revs >= BOUT_THRESHOLD_REVS_PER_MIN, 0.0)
                active = revs > 0

                active_runs = []
                if active.any():
                    run_id = (active != active.shift(fill_value=False)).cumsum()
                    for _, group_revs in revs.groupby(run_id):
                        if not active.loc[group_revs.index].iloc[0]:
                            continue

                        start_idx = group_revs.index[0]
                        end_idx = group_revs.index[-1]
                        start_ts = pd.Timestamp(day_df.loc[start_idx, 'Bin'])
                        end_ts = pd.Timestamp(day_df.loc[end_idx, 'Bin'])

                        active_runs.append({
                            'start_idx': start_idx,
                            'end_idx': end_idx,
                            'start_ts': start_ts,
                            'end_ts': end_ts,
                            'duration_min': float(len(group_revs)),
                            'speed_mean': float(group_revs.mean()),
                        })

                # Assign bouts by onset/start time inside the selected clock window.
                window_runs = [
                    run for run in active_runs
                    if (run['start_ts'] >= window_start_ts) and (run['start_ts'] < window_end_ts)
                ]

                daily_bout_counts.append(float(len(window_runs)))

                for run in window_runs:
                    all_bout_durations.append(run['duration_min'])
                    all_bout_speeds.append(run['speed_mean'])

                # Boundary-exclusive classic IBI, assigned by previous bout END time inside the window.
                for i in range(len(active_runs) - 1):
                    current_run = active_runs[i]
                    next_run = active_runs[i + 1]
                    if not ((current_run['end_ts'] >= window_start_ts) and (current_run['end_ts'] < window_end_ts)):
                        continue
                    ibi = float(next_run['start_idx'] - current_run['end_idx'] - 1)
                    if ibi >= 1:
                        all_ibis.append(ibi)

                # Window inactivity interval. Boundary-exclusive around bout ends.
                if len(window_runs) > 0:
                    sorted_runs = sorted(window_runs, key=lambda r: r['start_ts'])
                    gaps = []

                    first_gap = (sorted_runs[0]['start_ts'] - window_start_ts).total_seconds() / 60.0
                    if first_gap >= 0:
                        gaps.append(float(first_gap))

                    for i in range(len(sorted_runs) - 1):
                        gap = (sorted_runs[i + 1]['start_ts'] - sorted_runs[i]['end_ts']).total_seconds() / 60.0 - 1.0
                        if gap >= 0:
                            gaps.append(float(gap))

                    trailing_gap = (window_end_ts - (sorted_runs[-1]['end_ts'] + pd.Timedelta(minutes=1))).total_seconds() / 60.0
                    if trailing_gap >= 0:
                        gaps.append(float(trailing_gap))

                    daily_inactivity_intervals.append(float(np.nanmean(gaps)) if gaps else np.nan)
                else:
                    daily_inactivity_intervals.append(np.nan)

            daily_bout_counts = np.asarray(daily_bout_counts, dtype=float)
            daily_total_revs = np.asarray(daily_total_revs, dtype=float)
            daily_active_minutes = np.asarray(daily_active_minutes, dtype=float)
            daily_inactivity_intervals = np.asarray(daily_inactivity_intervals, dtype=float)

            total_bouts = float(np.nansum(daily_bout_counts))
            total_active_minutes = float(np.nansum(daily_active_minutes))
            inactivity_valid = daily_inactivity_intervals[np.isfinite(daily_inactivity_intervals)]

            return {
                'BoutCount_avgDaily': float(np.nanmean(daily_bout_counts)) if len(daily_bout_counts) else np.nan,
                'ActiveMinutes_avgDaily': float(np.nanmean(daily_active_minutes)) if len(daily_active_minutes) else np.nan,
                'WindowRevs_avgDaily': float(np.nanmean(daily_total_revs)) if len(daily_total_revs) else np.nan,
                'BoutSpeed_revPerMin_mean': float(np.mean(all_bout_speeds)) if all_bout_speeds else np.nan,
                'BoutSpeed_revPerMin_median': float(np.median(all_bout_speeds)) if all_bout_speeds else np.nan,
                'BoutDuration_mean': float(np.mean(all_bout_durations)) if all_bout_durations else np.nan,
                'BoutDuration_median': float(np.median(all_bout_durations)) if all_bout_durations else np.nan,
                'BoutDuration_minute_mean': float(np.mean(all_bout_durations)) if all_bout_durations else np.nan,
                'BoutDuration_minute_median': float(np.median(all_bout_durations)) if all_bout_durations else np.nan,
                'InterBoutInterval_minute_mean': float(np.mean(all_ibis)) if all_ibis else np.nan,
                'InterBoutInterval_minute_median': float(np.median(all_ibis)) if all_ibis else np.nan,
                'InactivityInterval_mean': float(np.nanmean(inactivity_valid)) if len(inactivity_valid) else np.nan,
                'InactivityInterval_median': float(np.nanmedian(inactivity_valid)) if len(inactivity_valid) else np.nan,
                'Fragmentation_BoutPerActiveMin': float(total_bouts / total_active_minutes) if total_active_minutes > 0 else np.nan,
                'n_bouts': int(len(all_bout_durations)),
                'n_ibis': int(len(all_ibis)),
                'n_inactivity_days': int(len(inactivity_valid)),
                'n_days': int(len(daily_bout_counts)),
                'DailyBoutCounts_D8_D21': ';'.join([str(int(x)) for x in daily_bout_counts]),
            }

        rows = []

        for file_path in file_paths:
            try:
                cohort_num = _cohort_num_from_path(file_path)
                labels = self._labels_for_cohort_global(cohort_num)
                df = _read_activity_file(file_path)
                df = df.dropna(how='all').dropna(axis=1, how='all')
                df.columns = [col.strip() for col in df.columns]

                if 'Bin' not in df.columns:
                    print(f"Warning: missing Bin column in {file_path}; skipped.")
                    continue

                df['Bin'] = pd.to_datetime(df['Bin'], format='mixed', errors='coerce')
                df = df.dropna(subset=['Bin']).copy()
                if df.empty:
                    continue

                reference_date = df['Bin'].dt.normalize().min().date()
                if cohort_num == 3:
                    reference_date = reference_date - timedelta(days=8)
                ref_ts = pd.Timestamp(reference_date)
                df['DateIndex'] = (df['Bin'].dt.normalize() - ref_ts).dt.days
                df = df[(df['DateIndex'] >= DAY_MIN) & (df['DateIndex'] <= DAY_MAX)].copy()
                if df.empty:
                    continue

                mouse_ids = sorted(set(col.split()[2] for col in df.columns if col.startswith('1 8')))
                mouse_ids = [int(m) for m in mouse_ids if str(m).isdigit()]
                mouse_ids = _included_mice(mouse_ids, cohort_num)
                mouse_ids = self._apply_lm45_mouse_filter(
                    mouse_ids, labels, remove_lm45,
                    cohort_num=cohort_num, context='early sleep / pre-dawn group differences'
                )

                for mid in mouse_ids:
                    rev_col = f'1 8 {mid} rev'
                    if rev_col not in df.columns:
                        continue
                    mouse_label = labels[mid - 1] if (mid - 1) < len(labels) else f'Mouse {mid}'
                    group = _group_from_label(mouse_label)
                    if group not in ['SNr-DTA', 'Control']:
                        continue

                    mouse_df = df[['Bin', 'DateIndex', rev_col]].copy()
                    daily_whole_revs = (
                        mouse_df.assign(Revs=pd.to_numeric(mouse_df[rev_col], errors='coerce').fillna(0.0))
                        .groupby('DateIndex')['Revs']
                        .sum()
                        .reindex(range(DAY_MIN, DAY_MAX + 1), fill_value=0.0)
                    )
                    whole_day_revs_avg = float(daily_whole_revs.mean()) if len(daily_whole_revs) else np.nan

                    for ws in window_specs:
                        metrics = _analyze_mouse_window(
                            mouse_df=mouse_df,
                            rev_col=rev_col,
                            start_hour=ws['StartHour'],
                            end_hour=ws['EndHour'],
                        )
                        row = {
                            'Cohort': cohort_num,
                            'MouseID': int(mid),
                            'ID': mouse_label[0:4],
                            'MouseLabel': mouse_label,
                            'Group': group,
                            'Window': ws['Window'],
                            'WindowKey': ws.get('WindowKey', _safe_window_name(ws['Window'])),
                            'ClockWindow': ws['ClockWindow'],
                            'BoutThreshold_revPerMin': BOUT_THRESHOLD_REVS_PER_MIN,
                        }
                        row.update(metrics)
                        row['WholeDayRevs_avgDaily'] = whole_day_revs_avg
                        if np.isfinite(whole_day_revs_avg) and whole_day_revs_avg > 0:
                            row['WindowRevsFractionOfWholeDay'] = row.get('WindowRevs_avgDaily', np.nan) / whole_day_revs_avg
                        else:
                            row['WindowRevsFractionOfWholeDay'] = np.nan
                        rows.append(row)

                print(f"Processed cohort {cohort_num}: {len(mouse_ids)} included mice")

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        if not rows:
            messagebox.showwarning("No Data", "No valid mouse/window rows were generated.")
            return

        out_df = pd.DataFrame(rows)
        csv_path = './CustomWindow_GroupDifferences_perMouseMetrics.csv'
        out_df.to_csv(csv_path, index=False)

        metric_specs = [
            ('BoutCount_avgDaily', 'Bout count / day'),
            ('ActiveMinutes_avgDaily', 'Active minutes / day'),
            ('BoutDuration_mean', 'Mean bout duration (min)'),
            ('InactivityInterval_mean', 'Mean inactivity interval (min)'),
            ('Fragmentation_BoutPerActiveMin', 'fragmentation ratio (#bouts/active minutes)'),
            ('WindowRevsFractionOfWholeDay', 'revs / whole-day revs'),
        ]

        def _ask_metric_spec_selection(metric_specs):
            result = {'value': None}
            win = Toplevel(self.root)
            win.title('Select metric to plot')
            win.transient(self.root)
            win.grab_set()

            Label(
                win,
                text='Choose one metric for Custom Window Group Differences:',
                font=('Arial', 11, 'bold'),
                justify='left'
            ).pack(anchor='w', padx=12, pady=(12, 8))

            var = StringVar(value=metric_specs[0][0])
            for metric_col, ylabel in metric_specs:
                Radiobutton(
                    win,
                    text=f'{metric_col}   —   {ylabel}',
                    variable=var,
                    value=metric_col,
                    anchor='w',
                    justify='left'
                ).pack(anchor='w', padx=16, pady=2)

            def _ok():
                chosen = var.get()
                for mc, yl in metric_specs:
                    if mc == chosen:
                        result['value'] = (mc, yl)
                        break
                win.destroy()

            def _cancel():
                result['value'] = None
                win.destroy()

            btn_frame = Frame(win)
            btn_frame.pack(pady=(10, 12))
            Button(btn_frame, text='OK', width=10, command=_ok).pack(side='left', padx=6)
            Button(btn_frame, text='Cancel', width=10, command=_cancel).pack(side='left', padx=6)

            win.wait_window()
            return result['value']

        selected_metric_spec = _ask_metric_spec_selection(metric_specs)
        if not selected_metric_spec:
            messagebox.showinfo('Cancelled', 'No metric selected.')
            return

        selected_metric_specs = [selected_metric_spec]

        def _custom_window_group_stats(out_df, metric_specs):
            stat_rows = []
            for window_name in out_df['Window'].dropna().unique():
                wdf = out_df[out_df['Window'] == window_name].copy()
                clock_window = wdf['ClockWindow'].iloc[0] if (not wdf.empty and 'ClockWindow' in wdf.columns) else ''
                window_key = wdf['WindowKey'].iloc[0] if (not wdf.empty and 'WindowKey' in wdf.columns) else ''
                for metric_col, ylabel in metric_specs:
                    snr_vals = pd.to_numeric(wdf.loc[wdf['Group'] == 'SNr-DTA', metric_col], errors='coerce').to_numpy(dtype=float)
                    ctrl_vals = pd.to_numeric(wdf.loc[wdf['Group'] == 'Control', metric_col], errors='coerce').to_numpy(dtype=float)
                    snr_vals = snr_vals[np.isfinite(snr_vals)]
                    ctrl_vals = ctrl_vals[np.isfinite(ctrl_vals)]

                    def _sem(vals):
                        return float(np.std(vals, ddof=1) / np.sqrt(len(vals))) if len(vals) > 1 else 0.0

                    def _cohens_d(x, y):
                        if len(x) < 2 or len(y) < 2:
                            return np.nan
                        sx = np.var(x, ddof=1)
                        sy = np.var(y, ddof=1)
                        pooled = ((len(x) - 1) * sx + (len(y) - 1) * sy) / max(len(x) + len(y) - 2, 1)
                        if pooled <= 0:
                            return np.nan
                        return float((np.mean(x) - np.mean(y)) / np.sqrt(pooled))

                    def _hedges_g(d, nx, ny):
                        if not np.isfinite(d):
                            return np.nan
                        dfree = nx + ny - 2
                        if dfree <= 1:
                            return d
                        return float(d * (1 - (3 / (4 * dfree - 1))))

                    def _cliffs_delta(x, y):
                        if len(x) == 0 or len(y) == 0:
                            return np.nan
                        gt = 0
                        lt = 0
                        for xi in x:
                            gt += np.sum(xi > y)
                            lt += np.sum(xi < y)
                        return float((gt - lt) / (len(x) * len(y)))

                    if len(snr_vals) == 0 or len(ctrl_vals) == 0:
                        stat_rows.append({
                            'WindowKey': window_key,
                            'WindowName': window_name,
                            'ClockWindow': clock_window,
                            'Metric': metric_col,
                            'MetricLabel': ylabel,
                            'n_SNr-DTA': len(snr_vals),
                            'n_Control': len(ctrl_vals),
                        })
                        continue

                    d = _cohens_d(snr_vals, ctrl_vals)
                    stat_rows.append({
                        'WindowKey': window_key,
                        'WindowName': window_name,
                        'ClockWindow': clock_window,
                        'Metric': metric_col,
                        'MetricLabel': ylabel,
                        'n_SNr-DTA': int(len(snr_vals)),
                        'n_Control': int(len(ctrl_vals)),
                        'SNr-DTA_mean': float(np.mean(snr_vals)),
                        'Control_mean': float(np.mean(ctrl_vals)),
                        'SNr-DTA_median': float(np.median(snr_vals)),
                        'Control_median': float(np.median(ctrl_vals)),
                        'SNr-DTA_SEM': _sem(snr_vals),
                        'Control_SEM': _sem(ctrl_vals),
                        'Difference_mean_SNrMinusControl': float(np.mean(snr_vals) - np.mean(ctrl_vals)),
                        'Direction': 'SNr-DTA > Control' if np.mean(snr_vals) > np.mean(ctrl_vals) else 'SNr-DTA < Control',
                        'Cohens_d': d,
                        'Hedges_g': _hedges_g(d, len(snr_vals), len(ctrl_vals)),
                        'Cliffs_delta': _cliffs_delta(snr_vals, ctrl_vals),
                    })
            return pd.DataFrame(stat_rows)

        selected_metric_col, selected_metric_label = selected_metric_spec
        metric_tag = re.sub(r'[^A-Za-z0-9_]+', '_', str(selected_metric_col)).strip('_')
        stats_csv_path = f'./CustomWindow_GroupDifferences_{metric_tag}_Stats.csv'
        custom_stats_df = _custom_window_group_stats(out_df, selected_metric_specs)
        custom_stats_df.to_csv(stats_csv_path, index=False)

        pdf_path = f'./CustomWindow_GroupDifferences_{metric_tag}.pdf'
        eps_paths = []

        group_order = ['SNr-DTA', 'Control']

        # Green / grey schematic for custom-window group plots.
        SNR_BAR_FILL = (0.45, 0.75, 0.45)   # light green
        CTRL_BAR_FILL = (0.55, 0.55, 0.55)  # light grey
        SNR_DOT = (0.25, 0.55, 0.25)        # dark green
        CTRL_DOT = (0.35, 0.35, 0.35)       # dark grey

        group_bar_fill = {
            'SNr-DTA': SNR_BAR_FILL,
            'Control': CTRL_BAR_FILL,
        }
        group_dot_color = {
            'SNr-DTA': SNR_DOT,
            'Control': CTRL_DOT,
        }

        def _p_to_stars(p):
            if not np.isfinite(p):
                return 'ns'
            if p < 0.001:
                return '***'
            if p < 0.01:
                return '**'
            if p < 0.05:
                return '*'
            return 'ns'

        def _format_p_line(p):
            if not np.isfinite(p):
                return 'p = NA'
            return f'p = {p:.2e}' if p < 0.001 else f'p = {p:.3f}'

        def _draw_custom_window_panel(ax, wdf, metric_col, ylabel):
            """
            Green/grey group bar plot:
              - bar = group mean
              - error bar = SEM
              - dots = individual animals
              - significance = Mann-Whitney U, two-sided, one value per animal
            """
            x_pos = {'SNr-DTA': 0, 'Control': 1}
            bar_width = 0.5
            dot_size = 55
            dot_edge_lw = 0.8
            jitter_half_width = 0.12
            rng = np.random.default_rng(42)

            group_vals = {}
            all_vals = []

            for group_name in group_order:
                vals = pd.to_numeric(
                    wdf.loc[wdf['Group'] == group_name, metric_col],
                    errors='coerce'
                ).dropna().to_numpy(dtype=float)
                vals = vals[np.isfinite(vals)]
                group_vals[group_name] = vals
                if len(vals):
                    all_vals.extend(vals.tolist())

            if len(all_vals) == 0:
                ax.text(0.5, 0.5, 'No valid values', ha='center', va='center',
                        transform=ax.transAxes, fontsize=11, fontweight='bold')
                ax.set_axis_off()
                return

            all_vals = np.asarray(all_vals, dtype=float)
            data_min = float(np.nanmin(all_vals))
            data_max = float(np.nanmax(all_vals))
            data_range = max(data_max - data_min, 1e-9)

            # Bars, SEM error bars, and animal-level dots.
            for group_name in group_order:
                vals = group_vals[group_name]
                x = x_pos[group_name]
                if len(vals) == 0:
                    continue

                mean_val = float(np.mean(vals))
                sem_val = float(stats.sem(vals)) if len(vals) > 1 else 0.0

                ax.bar(
                    x, mean_val,
                    width=bar_width,
                    color=group_bar_fill[group_name],
                    edgecolor='black',
                    linewidth=1.0,
                    zorder=2
                )

                ax.errorbar(
                    x, mean_val,
                    yerr=sem_val,
                    fmt='none',
                    ecolor='black',
                    elinewidth=1.5,
                    capsize=7,
                    capthick=1.5,
                    zorder=4
                )

                jitter = rng.uniform(-jitter_half_width, jitter_half_width, size=len(vals))
                ax.scatter(
                    np.full(len(vals), x) + jitter,
                    vals,
                    s=dot_size,
                    facecolor=group_dot_color[group_name],
                    edgecolor='black',
                    linewidth=dot_edge_lw,
                    alpha=1.0,
                    zorder=5
                )

                ax.text(
                    x, mean_val + sem_val + 0.035 * data_range,
                    f'n={len(vals)}',
                    ha='center',
                    va='bottom',
                    fontsize=9
                )

            # Mann-Whitney U significance bracket.
            snr_vals = group_vals['SNr-DTA']
            ctrl_vals = group_vals['Control']
            p = np.nan
            if len(snr_vals) > 0 and len(ctrl_vals) > 0:
                try:
                    p = float(stats.mannwhitneyu(snr_vals, ctrl_vals, alternative='two-sided').pvalue)
                except Exception:
                    p = np.nan

                bracket_y = data_max + 0.10 * data_range
                tick_h = 0.03 * data_range
                ax.plot(
                    [0, 0, 1, 1],
                    [bracket_y, bracket_y + tick_h, bracket_y + tick_h, bracket_y],
                    color='black',
                    linewidth=1.2,
                    clip_on=False,
                    zorder=6
                )
                ax.text(
                    0.5,
                    bracket_y + tick_h,
                    f'{_p_to_stars(p)}\n{_format_p_line(p)}',
                    ha='center',
                    va='bottom',
                    fontsize=10,
                    fontweight='bold',
                    zorder=7
                )

            ax.set_xticks([0, 1])
            ax.set_xticklabels(group_order, fontsize=11, fontweight='bold')
            ax.set_xlim(-0.65, 1.65)
            ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
            ax.tick_params(axis='y', labelsize=11)
            ax.tick_params(direction='out', width=1.1, length=5)
            ax.grid(False)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_linewidth(1.2)
            ax.spines['bottom'].set_linewidth(1.2)

            y_bottom = max(0.0, data_min - 0.06 * data_range) if data_min >= 0 else data_min - 0.08 * data_range
            y_top = data_max + 0.28 * data_range
            ax.set_ylim(y_bottom, y_top)

        with PdfPages(pdf_path) as pdf:
            for ws in window_specs:
                window_key = ws['WindowKey']
                window_name = ws['Window']
                clock_window_label = ws['ClockWindow']
                wdf = out_df[out_df['WindowKey'] == window_key].copy()
                if wdf.empty:
                    continue

                fig, ax = plt.subplots(figsize=(6.8, 6.2))
                _draw_custom_window_panel(ax, wdf, selected_metric_col, selected_metric_label)
                ax.set_title(
                    f'{window_name} ({clock_window_label}; Days {DAY_MIN}–{DAY_MAX})',
                    fontsize=14, fontweight='bold'
                )
                fig.text(
                    0.5, 0.01,
                    'Bar = mean ± SEM; dots = individual animals; bracket = Mann-Whitney U, two-sided.',
                    ha='center', va='bottom', fontsize=8.5
                )
                plt.tight_layout(rect=[0, 0.04, 1, 0.96])
                pdf.savefig(fig, bbox_inches='tight')

                eps_path = f'./CustomWindow_GroupDifferences_{metric_tag}_{window_key}.eps'
                fig.savefig(eps_path, format='eps')
                eps_paths.append(eps_path)
                plt.close(fig)

        print(f"Saved custom-window group-difference PDF: {pdf_path}")




    def plot_pooled_circadian_activity_by_phase(self):
        """
        Pooled circadian activity and bout-structure plots across multiple cohort files.

        Outputs:
        - Grouped revolutions PDF (phase-normalized + 24h-normalized), 2 pages: 6-hour bins and 3-hour bins for each plot.
        - Grouped durations PDF (sum-daily-median normalized, average-across-days raw, average-across-days phase-normalized).
        - Extra 3-hour duration PDF using average-across-days real-duration values, normalized individually across 24 h.
        - Grouped intervals PDF (average-across-days raw, average-across-days phase-normalized).
        - Existing bout-count PDFs are also retained.
        - One per-mouse CSV containing all metrics.
        - One group-summary CSV containing mean, SEM, and median for all metrics.

        Notes:
        - Light phase is defined as 06:00-18:00.
        - Dark phase is defined as 18:00-06:00.
        - Locomotor activity is normalized either within phase or across the full 24 h, depending on the page.
        - Bout count is calculated as average number of bouts per day per clock-time bin, with count PDFs retained from earlier versions.
        - Mean bout duration and mean inactivity interval now each have both raw averaged-data plots and phase-normalized averaged-data plots.
        """
        from tkinter import filedialog, messagebox, Toplevel, StringVar, IntVar, BooleanVar, Radiobutton, Checkbutton, Button, Label, Frame
        from matplotlib.backends.backend_pdf import PdfPages
        from matplotlib.lines import Line2D
        from matplotlib.patches import Rectangle

        DAY_MIN = 8
        DAY_MAX = 21
        LIGHT_ON_HOUR = 6
        LIGHT_OFF_HOUR = 18
        BIN_HOURS_LIST = [6, 3]
        BOUT_THRESHOLD_REVS_PER_MIN = 10

        # Stronger red/blue palettes. Blue is shifted toward cyan to avoid a purple tone.
        snr_fill = (0.86, 0.34, 0.38)
        snr_dark = (0.68, 0.10, 0.16)
        ctrl_fill = (0.28, 0.62, 0.92)
        ctrl_dark = (0.03, 0.34, 0.70)
        # Make the light-phase panel almost white; keep the dark phase subtly shaded.
        plot_bg = (0.995, 0.995, 0.995)
        dark_panel_bg = (0.93, 0.93, 0.93)
        group_fill_colors = {'SNr-DTA': snr_fill, 'Control': ctrl_fill}
        group_line_colors = {'SNr-DTA': snr_dark, 'Control': ctrl_dark}
        group_offsets = {'SNr-DTA': -0.14, 'Control': 0.14}
        group_markers = {'SNr-DTA': 'o', 'Control': 'o'}

        file_paths = filedialog.askopenfilenames(
            title="Select cohort files for pooled circadian activity",
            filetypes=[("Data Files", "*.csv *.xls *.xlsx")]
        )
        if not file_paths:
            messagebox.showinfo("No Files", "No files selected.")
            return

        remove_lm45 = self._ask_remove_lm45_from_mouse_pool("pooled circadian activity plots")

        def make_gradient_colors(base_color, n):
            """Within-group mouse colors. Slightly varied but not washed out."""
            if n <= 0:
                return []
            gradients = []
            for i in range(n):
                ratio = 0.02 + (0.18 * i / max(n - 1, 1))
                color = tuple(base_color[j] * (1 - ratio) + ratio for j in range(3))
                gradients.append(color)
            return gradients

        def normalize_vector_within_phase(mouse_vector, n_bins):
            vec = np.asarray(mouse_vector, dtype=float)
            norm = np.full_like(vec, np.nan, dtype=float)
            half = n_bins // 2
            for idxs in [list(range(0, half)), list(range(half, n_bins))]:
                phase_total = np.nansum(vec[idxs])
                if phase_total > 0:
                    norm[idxs] = vec[idxs] / phase_total * 100.0
            return norm

        def normalize_vector_over_24h(mouse_vector):
            """Normalize one mouse's binned values across the full 24-hour cycle."""
            vec = np.asarray(mouse_vector, dtype=float)
            norm = np.full_like(vec, np.nan, dtype=float)
            total = np.nansum(vec)
            if total > 0:
                norm = vec / total * 100.0
            return norm

        def build_bin_labels(bin_hours):
            """
            Clock-time labels ordered from light onset at 06:00.

            For bin_hours=6:
                06-12, 12-18 are light phase; 18-24, 00-06 are dark phase.
            For bin_hours=3:
                06-09, 09-12, 12-15, 15-18 are light;
                18-21, 21-24, 00-03, 03-06 are dark.

            The computation still uses time relative to LIGHT_ON_HOUR, so bin index 0
            always starts at 06:00, not midnight.
            """
            labels = []
            n_bins = int(24 / bin_hours)
            for i in range(n_bins):
                start_hour = int((LIGHT_ON_HOUR + i * bin_hours) % 24)
                end_hour = int((LIGHT_ON_HOUR + (i + 1) * bin_hours) % 24)
                end_label = 24 if end_hour == 0 else end_hour
                labels.append(f'{start_hour:02d}-{end_label:02d}')
            return labels

        def build_phase_specs(bin_hours):
            labels = build_bin_labels(bin_hours)
            n_bins = len(labels)
            half = n_bins // 2
            return labels, [
                ('Light phase', list(range(0, half)), labels[:half]),
                ('Dark phase', list(range(half, n_bins)), labels[half:]),
            ]

        def _cohort_num_from_path(file_path):
            base = os.path.splitext(os.path.basename(file_path))[0]
            patterns = [r'(?i)cohort[_\-\s]*([1-4])', r'(?i)c[_\-\s]*([1-4])', r'(?i)p\d+c([1-4])']
            for pat in patterns:
                m = re.search(pat, base)
                if m:
                    return int(m.group(1))
            m = re.search(r'([1-4])$', base)
            if m:
                return int(m.group(1))
            raise ValueError(f"Could not infer cohort number from filename: {os.path.basename(file_path)}")

        def _mouse_labels_for_cohort(cohort_num):
            if cohort_num == 1:
                return ["SC01(Control)", "LM45(SNr-DTA)", "SC02(GPi-DTA)"]
            if cohort_num == 2:
                return ["SC04(SNr-DTA)", "SC05(SNr-DTA)", "SC06(SNr-DTA)", "SC07(Control)", "SC08(Control)"]
            if cohort_num == 3:
                return ["SC09(SNr-DTA)", "SC10(SNr-DTA)", "SC11(SNr-DTA)", "SC12(SNr-DTA)", "SC13(Control)", "SC14(Control)", "SC15(Control)"]
            if cohort_num == 4:
                return ["SC29(SNr-DTA)", "SC30(SNr-DTA)", "SC31(SNr-DTA)", "SC32(SNr-DTA)", "SC33(Control)", "SC34(Control)", "SC35(Control)"]
            return []

        def _included_mice(mouse_ids, cohort_num):
            mouse_ids = list(mouse_ids)
            if cohort_num == 1:
                for i in [3, 5, 6, 7]:
                    if i in mouse_ids:
                        mouse_ids.remove(i)
            if cohort_num == 2:
                # Cohort 2: SC04/SC05/SC06 are excluded with SC07.
                # SC07 (mouse ID 4) remains excluded by default.
                for i in [1, 2, 3, 4]:
                    if i in mouse_ids:
                        mouse_ids.remove(i)
            if cohort_num == 4:
                for i in [7]:
                    if i in mouse_ids:
                        mouse_ids.remove(i)
            return mouse_ids

        def _load_cohort_file(file_path):
            cohort_num = _cohort_num_from_path(file_path)
            mouse_labels = _mouse_labels_for_cohort(cohort_num)
            if file_path.endswith('.xls') or file_path.endswith('.xlsx'):
                try:
                    df = pd.read_csv(file_path, skiprows=10, sep='\t')
                except Exception:
                    df = pd.read_csv(file_path, skiprows=10)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path, skiprows=10)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
            df = df.dropna(how='all').dropna(axis=1, how='all')
            df.columns = [col.strip() for col in df.columns]
            if 'Bin' not in df.columns:
                raise ValueError(f"Missing 'Bin' column in {os.path.basename(file_path)}")
            df['Bin'] = pd.to_datetime(df['Bin'], format='mixed', errors='coerce')
            df = df.dropna(subset=['Bin'])
            reference_date = df['Bin'].dt.normalize().min().date()
            if cohort_num == 3:
                reference_date = reference_date - timedelta(days=8)
            ref_ts = pd.Timestamp(reference_date)
            df['DateIndex'] = (df['Bin'].dt.normalize() - ref_ts).dt.days
            df = df[(df['DateIndex'] >= DAY_MIN) & (df['DateIndex'] <= DAY_MAX)].copy()
            mouse_ids = sorted(set(col.split()[2] for col in df.columns if col.startswith('1 8')))
            mouse_ids = [int(m) for m in mouse_ids if str(m).isdigit()]
            mouse_ids = _included_mice(mouse_ids, cohort_num)
            mouse_ids = self._apply_lm45_mouse_filter(mouse_ids, mouse_labels, remove_lm45, cohort_num=cohort_num, context='multi-cohort bout statistics')
            return cohort_num, mouse_labels, df, mouse_ids

        def _stats(values):
            vals = np.asarray(values, dtype=float)
            vals = vals[~np.isnan(vals)]
            n = len(vals)
            if n == 0:
                return {'n': 0, 'mean': np.nan, 'sem': np.nan, 'median': np.nan}
            return {
                'n': n,
                'mean': float(np.mean(vals)),
                'sem': float(np.std(vals, ddof=1) / np.sqrt(n)) if n > 1 else np.nan,
                'median': float(np.median(vals)),
            }

        def compute_bout_vectors_by_bin(mouse_df, rev_col, bin_col, n_bins):
            """
            Returns per-mouse vectors for both normalized-ratio plots and raw-value plots.

            Bouts are contiguous minutes with rev >= BOUT_THRESHOLD_REVS_PER_MIN.
            Each bout is assigned to the clock-time bin in which it starts.

            Interval metric used here is a window-inactivity metric:
            for each mouse/day/bin, calculate inactive gaps within that bin window.
            If no bout starts in that bin/day, the interval is kept as NaN and ignored
            by downstream np.nanmean-based averaging.
            If one or more bouts start in that bin/day, the interval is the mean of:
              1) bin start -> first bout start,
              2) gaps between consecutive bouts whose starts are in the same bin,
              3) last bout end -> bin end.
            This makes sparse bout-containing windows contribute long inactivity values
            without allowing completely no-bout windows to dominate the mean.
            """
            day_values = sorted(mouse_df['DateIndex'].dropna().unique())
            if len(day_values) == 0:
                zeros = np.zeros(n_bins, dtype=float)
                nans = np.full(n_bins, np.nan, dtype=float)
                return zeros, nans, zeros, nans, nans

            count_matrix = np.zeros((len(day_values), n_bins), dtype=float)
            median_duration_matrix = np.full((len(day_values), n_bins), np.nan, dtype=float)
            mean_duration_matrix = np.full((len(day_values), n_bins), np.nan, dtype=float)
            mean_interval_matrix = np.full((len(day_values), n_bins), np.nan, dtype=float)

            for day_i, (_, day_df) in enumerate(mouse_df.groupby('DateIndex')):
                # Reset the row index so bout positions are true minute positions within the day.
                # The original file index can have large gaps, and subtracting original index labels
                # can create impossible inactivity intervals such as hundreds of minutes inside a 3-h bin.
                day_df = day_df.sort_values('Bin').copy().reset_index(drop=True)
                revs = pd.to_numeric(day_df[rev_col], errors='coerce').fillna(0.0)
                active = revs >= BOUT_THRESHOLD_REVS_PER_MIN

                durations_by_bin = {i: [] for i in range(n_bins)}
                active_runs_by_bin = {i: [] for i in range(n_bins)}

                if active.any():
                    run_id = (active != active.shift(fill_value=False)).cumsum()
                    for _, run_group in day_df.groupby(run_id):
                        active_this_run = bool(active.loc[run_group.index].iloc[0])
                        if not active_this_run:
                            continue
                        start_pos = int(run_group.index[0])
                        end_pos = int(run_group.index[-1])
                        bin_idx = int(day_df.loc[start_pos, bin_col])
                        if bin_idx < 0 or bin_idx >= n_bins:
                            continue
                        duration_min = len(run_group)
                        count_matrix[day_i, bin_idx] += 1
                        durations_by_bin[bin_idx].append(duration_min)
                        active_runs_by_bin[bin_idx].append((start_pos, end_pos))

                # Window-inactivity interval metric.
                # No-bout bin/days remain NaN and are ignored by np.nanmean.
                # Sparse bins with at least one bout contribute the leading gap,
                # gaps between bouts, and trailing gap.
                intervals_by_bin = {i: [] for i in range(n_bins)}
                for bin_idx, runs in active_runs_by_bin.items():
                    runs = sorted(runs, key=lambda x: x[0])
                    bin_positions = np.where(day_df[bin_col].astype(int).values == int(bin_idx))[0]
                    if len(bin_positions) == 0:
                        continue
                    bin_start_pos = int(bin_positions[0])
                    bin_end_pos = int(bin_positions[-1])

                    if not runs:
                        # No bout in this bin/day: keep interval as NaN by leaving
                        # intervals_by_bin[bin_idx] empty. This bin/day will not
                        # contribute to future averaged inactivity-interval statistics.
                        continue

                    # Leading inactive gap: window start to first bout start.
                    leading_gap = max(0, runs[0][0] - bin_start_pos)
                    intervals_by_bin[bin_idx].append(leading_gap)

                    # Internal inactive gaps: end of one bout to start of the next bout.
                    for i in range(len(runs) - 1):
                        current_end_pos = runs[i][1]
                        next_start_pos = runs[i + 1][0]
                        interval_min = max(0, next_start_pos - current_end_pos - 1)
                        intervals_by_bin[bin_idx].append(interval_min)

                    # Trailing inactive gap: last bout end to window end.
                    trailing_gap = max(0, bin_end_pos - runs[-1][1])
                    intervals_by_bin[bin_idx].append(trailing_gap)

                for bin_idx, durations in durations_by_bin.items():
                    if durations:
                        median_duration_matrix[day_i, bin_idx] = float(np.median(durations))
                        mean_duration_matrix[day_i, bin_idx] = float(np.mean(durations))

                for bin_idx, intervals in intervals_by_bin.items():
                    if intervals:
                        mean_interval_matrix[day_i, bin_idx] = float(np.mean(intervals))

            # Ratio plot metric: total bout count across all analyzed days in each bin.
            count_total_vector = np.nansum(count_matrix, axis=0)

            # Ratio plot metric: accumulated daily-median duration values across days.
            has_median_duration = np.any(~np.isnan(median_duration_matrix), axis=0)
            duration_sum_daily_median_vector = np.where(
                has_median_duration,
                np.nansum(median_duration_matrix, axis=0),
                np.nan
            )

            # Raw-value plot metrics.
            count_avg_per_day_vector = np.nanmean(count_matrix, axis=0)
            mean_duration_avg_across_days_vector = np.nanmean(mean_duration_matrix, axis=0)
            mean_interval_avg_across_days_vector = np.nanmean(mean_interval_matrix, axis=0)

            return (
                count_total_vector,
                duration_sum_daily_median_vector,
                count_avg_per_day_vector,
                mean_duration_avg_across_days_vector,
                mean_interval_avg_across_days_vector,
            )

        results_by_bin = {}
        for bin_hours in BIN_HOURS_LIST:
            labels, phase_specs = build_phase_specs(bin_hours)
            results_by_bin[bin_hours] = {
                'bin_labels': labels,
                'phase_specs': phase_specs,
                'group_to_mouse_records': {'SNr-DTA': [], 'Control': []},
            }

        per_mouse_rows = []
        loaded_cohorts = []

        for file_path in file_paths:
            try:
                cohort_num, mouse_labels, df, mouse_ids = _load_cohort_file(file_path)
                loaded_cohorts.append(cohort_num)
                for mid in mouse_ids:
                    rev_col = f'1 8 {mid} rev'
                    if rev_col not in df.columns or mid - 1 >= len(mouse_labels):
                        continue
                    mouse_label = mouse_labels[mid - 1]
                    if 'SNr' in mouse_label or 'DTA' in mouse_label:
                        group = 'SNr-DTA'
                    elif 'Control' in mouse_label:
                        group = 'Control'
                    else:
                        continue

                    mouse_df = df[['Bin', 'DateIndex', rev_col]].copy()
                    mouse_df[rev_col] = pd.to_numeric(mouse_df[rev_col], errors='coerce').fillna(0.0)
                    clock_hour = (mouse_df['Bin'].dt.hour + mouse_df['Bin'].dt.minute / 60.0 + mouse_df['Bin'].dt.second / 3600.0)
                    mouse_df['ZTHour'] = (clock_hour - LIGHT_ON_HOUR) % 24

                    row = {
                        'Cohort': cohort_num,
                        'MouseID': mid,
                        'ID': mouse_label[0:4],
                        'Group': group,
                        'MouseLabel': mouse_label,
                        'DayRange': f'{DAY_MIN}-{DAY_MAX}',
                        'LightOn_clock_hour': LIGHT_ON_HOUR,
                        'LightOff_clock_hour': LIGHT_OFF_HOUR,
                        'BoutThreshold_revs_per_min': BOUT_THRESHOLD_REVS_PER_MIN,
                    }

                    n_days_any = None
                    for bin_hours in BIN_HOURS_LIST:
                        labels = results_by_bin[bin_hours]['bin_labels']
                        n_bins = len(labels)
                        bin_col = f'Clock{bin_hours}hBin'
                        mouse_df[bin_col] = np.floor(mouse_df['ZTHour'] / bin_hours).astype(int).clip(0, n_bins - 1)
                        daily_bin_sums = (
                            mouse_df.groupby(['DateIndex', bin_col])[rev_col]
                            .sum().unstack(fill_value=0)
                            .reindex(columns=list(range(n_bins)), fill_value=0)
                        )
                        if daily_bin_sums.empty:
                            continue
                        n_days_any = int(daily_bin_sums.shape[0]) if n_days_any is None else n_days_any
                        # Use total accumulated activity across all analyzed days in each bin.
                        mouse_vector = daily_bin_sums.sum(axis=0).values.astype(float)
                        mouse_vector_norm = normalize_vector_within_phase(mouse_vector, n_bins)
                        mouse_vector_24h_norm = normalize_vector_over_24h(mouse_vector)
                        (
                            bout_count_vector,
                            bout_duration_vector,
                            bout_count_avg_per_day_vector,
                            bout_mean_duration_avg_days_vector,
                            bout_mean_interval_avg_days_vector,
                        ) = compute_bout_vectors_by_bin(mouse_df, rev_col, bin_col, n_bins)
                        bout_count_vector_norm = normalize_vector_within_phase(bout_count_vector, n_bins)
                        bout_duration_vector_norm = normalize_vector_within_phase(bout_duration_vector, n_bins)
                        bout_mean_duration_avg_days_vector_norm = normalize_vector_within_phase(bout_mean_duration_avg_days_vector, n_bins)
                        # Extra duration metric: use the real averaged-duration values, then normalize
                        # each mouse individually across the full 24-hour cycle. This is especially
                        # useful for the 3-hour-bin figure.
                        bout_mean_duration_avg_days_vector_24h_norm = normalize_vector_over_24h(bout_mean_duration_avg_days_vector)
                        bout_mean_interval_avg_days_vector_norm = normalize_vector_within_phase(bout_mean_interval_avg_days_vector, n_bins)

                        results_by_bin[bin_hours]['group_to_mouse_records'][group].append({
                            'Cohort': cohort_num,
                            'MouseID': mid,
                            'ID': mouse_label[0:4],
                            'MouseLabel': mouse_label,
                            'Group': group,
                            'activity_raw': mouse_vector,
                            'activity_phase_norm': mouse_vector_norm,
                            'activity_24h_norm': mouse_vector_24h_norm,
                            'bout_count': bout_count_vector,
                            'bout_count_phase_norm': bout_count_vector_norm,
                            'bout_count_avg_per_day': bout_count_avg_per_day_vector,
                            'bout_mean_duration': bout_duration_vector,
                            'bout_mean_duration_phase_norm': bout_duration_vector_norm,
                            'bout_mean_duration_avg_across_days': bout_mean_duration_avg_days_vector,
                            'bout_mean_duration_avg_across_days_phase_norm': bout_mean_duration_avg_days_vector_norm,
                            'bout_mean_duration_avg_across_days_24h_norm': bout_mean_duration_avg_days_vector_24h_norm,
                            'bout_mean_interval_avg_across_days': bout_mean_interval_avg_days_vector,
                            'bout_mean_interval_avg_across_days_phase_norm': bout_mean_interval_avg_days_vector_norm,
                            'N_days_used': int(daily_bin_sums.shape[0]),
                        })
                        for i, label in enumerate(labels):
                            row[f'Clock_{label}_accumulated_revs_totalAcrossDays_per_{bin_hours}h'] = round(float(mouse_vector[i]), 4)
                            row[f'Clock_{label}_{bin_hours}h_phaseNormalized_percent'] = round(float(mouse_vector_norm[i]), 4) if not np.isnan(mouse_vector_norm[i]) else np.nan
                            row[f'Clock_{label}_{bin_hours}h_24hNormalized_percent'] = round(float(mouse_vector_24h_norm[i]), 4) if not np.isnan(mouse_vector_24h_norm[i]) else np.nan
                            row[f'Clock_{label}_bout_count_totalAcrossDays_per_{bin_hours}h'] = round(float(bout_count_vector[i]), 4) if not np.isnan(bout_count_vector[i]) else np.nan
                            row[f'Clock_{label}_bout_count_{bin_hours}h_phaseNormalized_percent'] = round(float(bout_count_vector_norm[i]), 4) if not np.isnan(bout_count_vector_norm[i]) else np.nan
                            row[f'Clock_{label}_bout_count_avgPerDay_per_{bin_hours}h'] = round(float(bout_count_avg_per_day_vector[i]), 4) if not np.isnan(bout_count_avg_per_day_vector[i]) else np.nan
                            row[f'Clock_{label}_bout_duration_sumDailyMedian_min_per_{bin_hours}h'] = round(float(bout_duration_vector[i]), 4) if not np.isnan(bout_duration_vector[i]) else np.nan
                            row[f'Clock_{label}_bout_duration_sumDailyMedian_{bin_hours}h_phaseNormalized_percent'] = round(float(bout_duration_vector_norm[i]), 4) if not np.isnan(bout_duration_vector_norm[i]) else np.nan
                            row[f'Clock_{label}_bout_duration_meanMin_avgAcrossDays_per_{bin_hours}h'] = round(float(bout_mean_duration_avg_days_vector[i]), 4) if not np.isnan(bout_mean_duration_avg_days_vector[i]) else np.nan
                            row[f'Clock_{label}_bout_duration_meanMin_avgAcrossDays_{bin_hours}h_phaseNormalized_percent'] = round(float(bout_mean_duration_avg_days_vector_norm[i]), 4) if not np.isnan(bout_mean_duration_avg_days_vector_norm[i]) else np.nan
                            row[f'Clock_{label}_bout_duration_meanMin_avgAcrossDays_{bin_hours}h_24hIndividualNormalized_percent'] = round(float(bout_mean_duration_avg_days_vector_24h_norm[i]), 4) if not np.isnan(bout_mean_duration_avg_days_vector_24h_norm[i]) else np.nan
                            row[f'Clock_{label}_inactivity_interval_meanMin_avgAcrossDays_per_{bin_hours}h'] = round(float(bout_mean_interval_avg_days_vector[i]), 4) if not np.isnan(bout_mean_interval_avg_days_vector[i]) else np.nan
                            row[f'Clock_{label}_inactivity_interval_meanMin_avgAcrossDays_{bin_hours}h_phaseNormalized_percent'] = round(float(bout_mean_interval_avg_days_vector_norm[i]), 4) if not np.isnan(bout_mean_interval_avg_days_vector_norm[i]) else np.nan
                    row['N_days_used'] = n_days_any if n_days_any is not None else 0
                    per_mouse_rows.append(row)
                print(f"Loaded cohort {cohort_num}: {len(mouse_ids)} included mice")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")

        if not per_mouse_rows:
            messagebox.showerror("No Data", "No valid mouse activity data found for pooled circadian plot.")
            return

        # Assign stable within-group gradients.
        for bin_hours in BIN_HOURS_LIST:
            for group in ['SNr-DTA', 'Control']:
                records = results_by_bin[bin_hours]['group_to_mouse_records'][group]
                records.sort(key=lambda r: (r['Cohort'], str(r['ID']), r['MouseID']))
                colors = make_gradient_colors(group_fill_colors[group], len(records))
                for rec, color in zip(records, colors):
                    rec['color'] = color

        loaded_cohorts = sorted(set(loaded_cohorts))
        cohort_str = '_'.join([f'C{c}' for c in loaded_cohorts]) if loaded_cohorts else 'selected'
        activity_pdf_path = './Circadian_Activity_ByPhase_Normalized_6h3hBin.pdf'
        activity_24h_pdf_path = './Circadian_Activity_24hNormalized_6h3hBin.pdf'
        grouped_revolution_pdf_path = './Circadian_Revolutions_Grouped_6h3hBin.pdf'
        bout_count_pdf_path = './Circadian_BoutCount_Normalized_6h3hBin.pdf'
        bout_count_avg_pdf_path = './Circadian_BoutCount_AvgPerDay_6h3hBin.pdf'
        bout_duration_pdf_path = './Circadian_BoutDuration_SumDailyMedian_Normalized_6h3hBin.pdf'
        bout_duration_avg_pdf_path = './Circadian_BoutDuration_MeanAvgAcrossDays_6h3hBin.pdf'
        bout_duration_avg_phase_norm_pdf_path = './Circadian_BoutDuration_MeanAvgAcrossDays_PhaseNormalized_6h3hBin.pdf'
        bout_duration_avg_3h_individual_norm_pdf_path = './Circadian_BoutDuration_MeanAvgAcrossDays_3h_IndividuallyNormalized.pdf'
        grouped_duration_pdf_path = './Circadian_Durations_Grouped_6h3hBin.pdf'
        bout_interval_avg_pdf_path = './Circadian_InactivityInterval_MeanAvgAcrossDays_6h3hBin.pdf'
        bout_interval_phase_norm_pdf_path = './Circadian_InactivityInterval_MeanAvgAcrossDays_PhaseNormalized_6h3hBin.pdf'
        grouped_interval_pdf_path = './Circadian_Intervals_Grouped_6h3hBin.pdf'
        per_mouse_csv_path = f'./Pooled_Circadian_Activity_Bouts_PerMouse_Light06Dark18_6h_3h_{cohort_str}_D{DAY_MIN}-{DAY_MAX}.csv'
        summary_csv_path = './All_bout_info.csv'
        zero_value_csv_path = f'./Pooled_Circadian_ZeroValue_SanityCheck_Light06Dark18_6h_3h_{cohort_str}_D{DAY_MIN}-{DAY_MAX}.csv'
        count_duration_interval_sanity_csv_path = f'./Pooled_Circadian_CountDurationInterval_SanityCheck_Light06Dark18_6h_3h_{cohort_str}_D{DAY_MIN}-{DAY_MAX}.csv'
        printed_zero_data_csv_path = './CircadianStatistics_ZeroBountPoints_sortedbyBinnedWindow.csv'

        per_mouse_df = pd.DataFrame(per_mouse_rows).sort_values(['Group', 'Cohort', 'ID'])
        per_mouse_df.to_csv(per_mouse_csv_path, index=False)

        metric_configs = {
            'activity_phase_norm': {
                'summary_prefix': 'phaseNormalized_percent',
                'pdf_path': activity_pdf_path,
                'title': 'Wheeling Revolutions',
                'ylabel': lambda bh: 'Rev (%)',
                'ylim': (0, 100),
                'calc_note': (
                    'Calculation: total wheel revolutions per bin across days; '
                    'then normalized within each mouse and phase. '
                    f'Days {DAY_MIN}-{DAY_MAX}; light 06:00-18:00, dark 18:00-06:00.'
                ),
            },
            'activity_24h_norm': {
                'summary_prefix': 'twentyFourHourNormalized_percent',
                'pdf_path': activity_24h_pdf_path,
                'title': 'Wheeling Revolutions',
                'ylabel': lambda bh: 'Rev (% of 24 h)',
                'ylim': (0, 100),
                'calc_note': (
                    'Calculation: total wheel revolutions per bin across days; '
                    'then normalized across the full 24-hour cycle for each mouse. '
                    f'Days {DAY_MIN}-{DAY_MAX}; light 06:00-18:00, dark 18:00-06:00.'
                ),
            },
            'bout_count_phase_norm': {
                'summary_prefix': 'bout_count_phaseNormalized_percent',
                'pdf_path': bout_count_pdf_path,
                'title': 'Bout count',
                'ylabel': lambda bh: 'Bout count (%)',
                'ylim': (0, 100),
                'calc_note': (
                    'Calculation: total number of bouts per bin across days; '
                    'then normalized within each mouse and phase. '
                    f'Days {DAY_MIN}-{DAY_MAX}; light 06:00-18:00, dark 18:00-06:00.'
                ),
            },
            'bout_count_avg_per_day': {
                'summary_prefix': 'bout_count_avgPerDay',
                'pdf_path': bout_count_avg_pdf_path,
                'title': 'Bout count',
                'ylabel': lambda bh: f'Bouts / {bh} h bin / day',
                'ylim': None,
                'calc_note': (
                    'Calculation: number of bouts in each bin for each day; '
                    'then averaged across days for each mouse. '
                    f'Days {DAY_MIN}-{DAY_MAX}; light 06:00-18:00, dark 18:00-06:00.'
                ),
            },
            'bout_mean_duration_phase_norm': {
                'summary_prefix': 'bout_duration_sumDailyMedian_phaseNormalized_percent',
                'pdf_path': bout_duration_pdf_path,
                'title': 'Bout duration',
                'ylabel': lambda bh: 'Bout duration (%)',
                'ylim': (0, 100),
                'calc_note': (
                    'Calculation: median bout duration per day/bin, summed across days; '
                    'then normalized within each mouse and phase. '
                    f'Days {DAY_MIN}-{DAY_MAX}; light 06:00-18:00, dark 18:00-06:00.'
                ),
            },
            'bout_mean_duration_avg_across_days': {
                'summary_prefix': 'bout_duration_meanMin_avgAcrossDays',
                'pdf_path': bout_duration_avg_pdf_path,
                'title': 'Bout duration',
                'ylabel': lambda bh: 'Mean bout duration (min)',
                'ylim': None,
                'calc_note': (
                    'Calculation: mean bout duration in each bin for each day; '
                    'then averaged across days for each mouse. '
                    f'Days {DAY_MIN}-{DAY_MAX}; light 06:00-18:00, dark 18:00-06:00.'
                ),
            },
            'bout_mean_duration_avg_across_days_phase_norm': {
                'summary_prefix': 'bout_duration_meanMin_avgAcrossDays_phaseNormalized_percent',
                'pdf_path': bout_duration_avg_phase_norm_pdf_path,
                'title': 'Bout duration',
                'ylabel': lambda bh: 'Mean bout duration (%)',
                'ylim': (0, 100),
                'calc_note': (
                    'Calculation: mean bout duration in each bin for each day; '
                    'then averaged across days for each mouse and normalized within light and dark phase separately. '
                    f'Days {DAY_MIN}-{DAY_MAX}; light 06:00-18:00, dark 18:00-06:00.'
                ),
            },
            'bout_mean_duration_avg_across_days_24h_norm': {
                'summary_prefix': 'bout_duration_meanMin_avgAcrossDays_24hIndividualNormalized_percent',
                'pdf_path': bout_duration_avg_3h_individual_norm_pdf_path,
                'title': 'Bout duration',
                'ylabel': lambda bh: 'Mean bout duration (% of 24 h)',
                'ylim': (0, 100),
                'calc_note': (
                    'Calculation: mean bout duration in each bin for each day; '
                    'then averaged across days for each mouse and normalized individually across the full 24-hour cycle. '
                    'This PDF is generated only for 3-hour bins. '
                    f'Days {DAY_MIN}-{DAY_MAX}; light 06:00-18:00, dark 18:00-06:00.'
                ),
            },
            'bout_mean_interval_avg_across_days': {
                'summary_prefix': 'inactivity_interval_meanMin_avgAcrossDays',
                'pdf_path': bout_interval_avg_pdf_path,
                'title': 'Inactivity interval',
                'ylabel': lambda bh: 'Mean inactivity interval (min)',
                'ylim': None,
                'calc_note': (
                    'Calculation: mean within-window inactivity interval in each bin/day; '
                    'then averaged across days for each mouse. '
                    f'Days {DAY_MIN}-{DAY_MAX}; light 06:00-18:00, dark 18:00-06:00.'
                ),
            },
            'bout_mean_interval_avg_across_days_phase_norm': {
                'summary_prefix': 'inactivity_interval_meanMin_avgAcrossDays_phaseNormalized_percent',
                'pdf_path': bout_interval_phase_norm_pdf_path,
                'title': 'Inactivity interval',
                'ylabel': lambda bh: 'Mean inactivity interval (%)',
                'ylim': (0, 100),
                'calc_note': (
                    'Calculation: mean within-window inactivity interval in each bin/day; '
                    'then averaged across days for each mouse and normalized within light and dark phase separately. '
                    f'Days {DAY_MIN}-{DAY_MAX}; light 06:00-18:00, dark 18:00-06:00.'
                ),
            },
        }

        # Sanity check: print and save all plotted mouse/bin values that are exactly zero.
        # This helps identify whether zeros are real mouse-level zeros and which clock-time
        # windows produced them. NaNs are not reported here because they usually mean no
        # valid bouts/intervals were available for that mouse/bin.
        zero_debug_rows = []
        for bin_hours in BIN_HOURS_LIST:
            labels = results_by_bin[bin_hours]['bin_labels']
            half = len(labels) // 2
            for group, records in results_by_bin[bin_hours]['group_to_mouse_records'].items():
                for rec in records:
                    for metric_key, cfg in metric_configs.items():
                        # The individually normalized duration figure is intentionally 3-h only.
                        if metric_key == 'bout_mean_duration_avg_across_days_24h_norm' and bin_hours != 3:
                            continue
                        values = np.asarray(rec[metric_key], dtype=float)
                        for i, value in enumerate(values):
                            if np.isfinite(value) and np.isclose(value, 0.0, atol=1e-12):
                                phase = 'Light' if i < half else 'Dark'
                                zero_debug_rows.append({
                                    'Metric': metric_key,
                                    'MetricTitle': cfg['title'],
                                    'YLabel': cfg['ylabel'](bin_hours),
                                    'BinHours': bin_hours,
                                    'Phase': phase,
                                    'Clock_bin': labels[i],
                                    'Clock_bin_index': i,
                                    'Cohort': rec['Cohort'],
                                    'MouseID': rec['MouseID'],
                                    'ID': rec['ID'],
                                    'MouseLabel': rec['MouseLabel'],
                                    'Group': rec['Group'],
                                    'Value': float(value),
                                    'N_days_used': rec.get('N_days_used', np.nan),
                                })

        zero_debug_df = pd.DataFrame(zero_debug_rows)
        zero_debug_df.to_csv(zero_value_csv_path, index=False)

        print('\n=== ZERO-VALUE SANITY CHECK: plotted mouse-level values == 0 ===')
        if zero_debug_df.empty:
            print('No exact zero plotted values found.')
        else:
            print(f'Found {len(zero_debug_df)} exact zero plotted values. Full table saved to: {zero_value_csv_path}')
            # Print a compact but complete table to the console.
            print(zero_debug_df[[
                'Metric', 'BinHours', 'Phase', 'Clock_bin',
                'Cohort', 'ID', 'MouseLabel', 'Group', 'Value'
            ]].to_string(index=False))
        print('=== END ZERO-VALUE SANITY CHECK ===\n')

        # Additional sanity check focused on low-bout windows and the relationship among
        # bout count, duration, and inactivity interval.
        # Interpretation:
        # - bout_count == 0 means no bouts started in that mouse/bin across all analyzed days.
        # - duration should be NaN when bout_count == 0, because there is no bout duration to compute.
        # - inactivity interval should be NaN when bout_count == 0 because no-bout
        #   bin/days are ignored instead of being assigned the full window duration.
        # - the dedicated low-bout CSV reports windows with bout_count <= 1, as requested.
        cdi_rows = []
        for bin_hours in BIN_HOURS_LIST:
            labels = results_by_bin[bin_hours]['bin_labels']
            half = len(labels) // 2
            for group, records in results_by_bin[bin_hours]['group_to_mouse_records'].items():
                for rec in records:
                    count_total = np.asarray(rec['bout_count'], dtype=float)
                    count_avg = np.asarray(rec['bout_count_avg_per_day'], dtype=float)
                    dur_sum_median = np.asarray(rec['bout_mean_duration'], dtype=float)
                    dur_avg = np.asarray(rec['bout_mean_duration_avg_across_days'], dtype=float)
                    dur_phase = np.asarray(rec['bout_mean_duration_avg_across_days_phase_norm'], dtype=float)
                    interval_avg = np.asarray(rec['bout_mean_interval_avg_across_days'], dtype=float)
                    interval_phase = np.asarray(rec['bout_mean_interval_avg_across_days_phase_norm'], dtype=float)
                    for i, label in enumerate(labels):
                        phase = 'Light' if i < half else 'Dark'
                        ct = count_total[i]
                        row = {
                            'BinHours': bin_hours,
                            'Phase': phase,
                            'Clock_bin': label,
                            'Clock_bin_index': i,
                            'Cohort': rec['Cohort'],
                            'MouseID': rec['MouseID'],
                            'ID': rec['ID'],
                            'MouseLabel': rec['MouseLabel'],
                            'Group': rec['Group'],
                            'BoutCount_totalAcrossDays': ct,
                            'BoutCount_avgPerDay': count_avg[i],
                            'Duration_sumDailyMedian_min': dur_sum_median[i],
                            'Duration_meanAvgAcrossDays_min': dur_avg[i],
                            'Duration_meanAvgAcrossDays_phaseNorm_percent': dur_phase[i],
                            'InactivityInterval_meanAvgAcrossDays_min': interval_avg[i],
                            'InactivityInterval_meanAvgAcrossDays_phaseNorm_percent': interval_phase[i],
                        }
                        if np.isfinite(ct) and ct <= 1:
                            row['SanityStatus'] = 'LOW_BOUT_COUNT_LE_1'
                            if np.isclose(ct, 0.0, atol=1e-12):
                                row['LowBoutCategory'] = 'zero_bouts'
                                row['DurationOK'] = bool(np.isnan(dur_sum_median[i]) and np.isnan(dur_avg[i]) and np.isnan(dur_phase[i]))
                            else:
                                row['LowBoutCategory'] = 'one_bout'
                                row['DurationOK'] = bool(np.isfinite(dur_sum_median[i]) and np.isfinite(dur_avg[i]))
                            if np.isclose(ct, 0.0, atol=1e-12):
                                row['InactivityIntervalOK'] = bool(np.isnan(interval_avg[i]) and np.isnan(interval_phase[i]))
                            else:
                                row['InactivityIntervalOK'] = bool(np.isfinite(interval_avg[i]))
                            cdi_rows.append(row)
                        elif np.isfinite(ct) and ct > 1:
                            duration_missing = np.isnan(dur_sum_median[i]) or np.isnan(dur_avg[i])
                            interval_missing = np.isnan(interval_avg[i])
                            if duration_missing or interval_missing:
                                row['SanityStatus'] = 'BOUTS_PRESENT_BUT_VALUE_MISSING_CHECK'
                                row['LowBoutCategory'] = 'more_than_one_bout'
                                row['DurationOK'] = not duration_missing
                                row['InactivityIntervalOK'] = not interval_missing
                                cdi_rows.append(row)

        cdi_df = pd.DataFrame(cdi_rows)
        cdi_df.to_csv(count_duration_interval_sanity_csv_path, index=False)

        # Dedicated CSV for low-bout rows printed below.
        # It contains every mouse/bin where bout count is <= 1, with matching duration
        # and inactivity-interval fields shown so sparse windows can be audited directly.
        printed_zero_columns = [
            'BinHours', 'Phase', 'Clock_bin', 'Clock_bin_index',
            'Cohort', 'MouseID', 'ID', 'MouseLabel', 'Group',
            'BoutCount_totalAcrossDays', 'BoutCount_avgPerDay',
            'Duration_sumDailyMedian_min', 'Duration_meanAvgAcrossDays_min',
            'Duration_meanAvgAcrossDays_phaseNorm_percent',
            'InactivityInterval_meanAvgAcrossDays_min',
            'InactivityInterval_meanAvgAcrossDays_phaseNorm_percent',
            'LowBoutCategory', 'DurationOK', 'InactivityIntervalOK', 'SanityStatus'
        ]
        if cdi_df.empty:
            printed_zero_df = pd.DataFrame(columns=printed_zero_columns)
        else:
            printed_zero_df = cdi_df[cdi_df['SanityStatus'] == 'LOW_BOUT_COUNT_LE_1'].copy()
            for col in printed_zero_columns:
                if col not in printed_zero_df.columns:
                    printed_zero_df[col] = np.nan
            printed_zero_df = printed_zero_df[printed_zero_columns]
        printed_zero_df.to_csv(printed_zero_data_csv_path, index=False)

        print('\n=== COUNT-DURATION-INACTIVITY-INTERVAL SANITY CHECK ===')
        if cdi_df.empty:
            print('No low-bout bins or count/duration/inactivity-interval inconsistencies found.')
        else:
            low_bout_df = cdi_df[cdi_df['SanityStatus'] == 'LOW_BOUT_COUNT_LE_1']
            bad_low_bout_df = low_bout_df[(low_bout_df['DurationOK'] == False) | (low_bout_df['InactivityIntervalOK'] == False)] if not low_bout_df.empty else low_bout_df
            bad_duration_df = cdi_df[cdi_df['SanityStatus'] == 'BOUTS_PRESENT_BUT_VALUE_MISSING_CHECK']
            print(f'Low-bout mouse/bin windows found (bout count <= 1): {len(low_bout_df)}')
            print(f'Low-bout rows with unexpected duration/inactivity-interval status: {len(bad_low_bout_df)}')
            print(f'Rows where bouts were present but duration or inactivity interval was missing: {len(bad_duration_df)}')
            print(f'Full table saved to: {count_duration_interval_sanity_csv_path}')
            print(f'Low-bout rows saved to: {printed_zero_data_csv_path}')
            if len(low_bout_df) > 0:
                print('\nLow-bout windows, compact table:')
                print(low_bout_df[[
                    'BinHours', 'Phase', 'Clock_bin', 'Cohort', 'ID', 'MouseLabel', 'Group',
                    'BoutCount_totalAcrossDays', 'Duration_meanAvgAcrossDays_min',
                    'InactivityInterval_meanAvgAcrossDays_min', 'LowBoutCategory',
                    'DurationOK', 'InactivityIntervalOK'
                ]].to_string(index=False))
            if len(bad_duration_df) > 0:
                print('\nRows needing check:')
                print(bad_duration_df[[
                    'BinHours', 'Phase', 'Clock_bin', 'Cohort', 'ID', 'MouseLabel', 'Group',
                    'BoutCount_totalAcrossDays', 'Duration_meanAvgAcrossDays_min',
                    'InactivityInterval_meanAvgAcrossDays_min', 'DurationOK', 'InactivityIntervalOK', 'SanityStatus'
                ]].to_string(index=False))
        print('=== END COUNT-DURATION-INACTIVITY-INTERVAL SANITY CHECK ===\n')

        summary_rows = []
        for bin_hours in BIN_HOURS_LIST:
            labels = results_by_bin[bin_hours]['bin_labels']
            for group, records in results_by_bin[bin_hours]['group_to_mouse_records'].items():
                if not records:
                    continue
                half = len(labels) // 2
                for metric_key, cfg in metric_configs.items():
                    arr = np.asarray([r[metric_key] for r in records], dtype=float)
                    for i, label in enumerate(labels):
                        st = _stats(arr[:, i])
                        phase = 'Light' if i < half else 'Dark'
                        summary_rows.append({
                            'Metric': metric_key,
                            'BinHours': bin_hours,
                            'Group': group,
                            'Phase': phase,
                            'Clock_bin': label,
                            'Clock_bin_index': i,
                            'n_mice': st['n'],
                            f"{cfg['summary_prefix']}_mean": round(st['mean'], 4) if not np.isnan(st['mean']) else np.nan,
                            f"{cfg['summary_prefix']}_sem": round(st['sem'], 4) if not np.isnan(st['sem']) else np.nan,
                            f"{cfg['summary_prefix']}_median": round(st['median'], 4) if not np.isnan(st['median']) else np.nan,
                        })
        pd.DataFrame(summary_rows).to_csv(summary_csv_path, index=False)

        def draw_mean_sem_box(ax, center_x, st, width, facecolor):
            if st['n'] == 0 or np.isnan(st['mean']):
                return
            sem_val = 0.0 if np.isnan(st['sem']) else st['sem']
            y0 = st['mean'] - sem_val
            height = max(2 * sem_val, 0.35)
            rect = Rectangle((center_x - width / 2, y0), width, height,
                             facecolor=facecolor, edgecolor='black', linewidth=2.0,
                             alpha=0.68, zorder=4)
            ax.add_patch(rect)
            ax.hlines(st['mean'], center_x - width / 2, center_x + width / 2,
                      color='black', linewidth=2.4, zorder=5)


        def metric_ylim(metric_key, bin_hours):
            cfg_ylim = metric_configs[metric_key]['ylim']
            if cfg_ylim is not None:
                return cfg_ylim
            vals = []
            for group in ['SNr-DTA', 'Control']:
                records = results_by_bin[bin_hours]['group_to_mouse_records'][group]
                for rec in records:
                    vals.extend(list(np.asarray(rec[metric_key], dtype=float)))
            vals = np.asarray(vals, dtype=float)
            vals = vals[~np.isnan(vals)]
            if len(vals) == 0:
                return (0, 1)
            top = float(np.nanmax(vals))
            if top <= 0:
                top = 1.0
            return (0, top * 1.25)

        def _ask_pooled_metric_selection():
            result = {'value': None}
            win = Toplevel(self.root)
            win.title('Select pooled circadian metric')
            win.transient(self.root)
            win.grab_set()

            Label(
                win,
                text='Choose one metric to plot:',
                font=('Arial', 11, 'bold'),
                justify='left'
            ).pack(anchor='w', padx=12, pady=(12, 8))

            metric_order = [
                'activity_phase_norm',
                'activity_24h_norm',
                'bout_count',
                'bout_count_avg_per_day',
                'bout_mean_duration',
                'bout_mean_duration_avg_across_days',
                'bout_mean_duration_avg_across_days_phase_norm',
                'bout_mean_duration_avg_across_days_24h_norm',
                'bout_mean_interval_avg_across_days',
                'bout_mean_interval_avg_across_days_phase_norm',
            ]
            options = []
            for key in metric_order:
                if key in metric_configs:
                    cfg = metric_configs[key]
                    options.append((key, f"{cfg['title']}   —   {key}"))

            var = StringVar(value=options[0][0] if options else '')
            for key, label_text in options:
                Radiobutton(
                    win, text=label_text, variable=var, value=key,
                    anchor='w', justify='left'
                ).pack(anchor='w', padx=16, pady=2)

            def _ok():
                result['value'] = var.get()
                win.destroy()

            def _cancel():
                result['value'] = None
                win.destroy()

            btn_frame = Frame(win)
            btn_frame.pack(pady=(10, 12))
            Button(btn_frame, text='OK', width=10, command=_ok).pack(side='left', padx=6)
            Button(btn_frame, text='Cancel', width=10, command=_cancel).pack(side='left', padx=6)
            win.wait_window()
            return result['value']

        def _ask_bin_hours_selection():
            result = {'value': None}
            win = Toplevel(self.root)
            win.title('Select bin size')
            win.transient(self.root)
            win.grab_set()

            Label(
                win, text='Choose time-window resolution:',
                font=('Arial', 11, 'bold')
            ).pack(anchor='w', padx=12, pady=(12, 8))

            var = IntVar(value=6)
            Radiobutton(win, text='6-hour bins', variable=var, value=6).pack(anchor='w', padx=16, pady=2)
            Radiobutton(win, text='3-hour bins', variable=var, value=3).pack(anchor='w', padx=16, pady=2)

            def _ok():
                result['value'] = int(var.get())
                win.destroy()

            def _cancel():
                result['value'] = None
                win.destroy()

            btn_frame = Frame(win)
            btn_frame.pack(pady=(10, 12))
            Button(btn_frame, text='OK', width=10, command=_ok).pack(side='left', padx=6)
            Button(btn_frame, text='Cancel', width=10, command=_cancel).pack(side='left', padx=6)
            win.wait_window()
            return result['value']

        def _ask_clock_bin_selection(bin_hours, labels):
            result = {'value': None}
            win = Toplevel(self.root)
            win.title('Select clock bin(s)')
            win.transient(self.root)
            win.grab_set()

            Label(
                win,
                text=f'Select one or more {bin_hours}-hour time windows:',
                font=('Arial', 11, 'bold'),
                justify='left'
            ).pack(anchor='w', padx=12, pady=(12, 8))

            var_map = {}
            for lab in labels:
                v = BooleanVar(value=True)
                var_map[lab] = v
                Checkbutton(win, text=lab, variable=v).pack(anchor='w', padx=16, pady=2)

            def _all():
                for v in var_map.values():
                    v.set(True)

            def _none():
                for v in var_map.values():
                    v.set(False)

            def _ok():
                chosen = [lab for lab in labels if var_map[lab].get()]
                result['value'] = chosen
                win.destroy()

            def _cancel():
                result['value'] = None
                win.destroy()

            btn_frame = Frame(win)
            btn_frame.pack(pady=(10, 12))
            Button(btn_frame, text='All', width=8, command=_all).pack(side='left', padx=4)
            Button(btn_frame, text='None', width=8, command=_none).pack(side='left', padx=4)
            Button(btn_frame, text='OK', width=10, command=_ok).pack(side='left', padx=6)
            Button(btn_frame, text='Cancel', width=10, command=_cancel).pack(side='left', padx=6)
            win.wait_window()
            return result['value']

        def save_metric_pdf(metric_key):
            cfg = metric_configs[metric_key]
            with PdfPages(cfg['pdf_path']) as pdf:
                for bin_hours in BIN_HOURS_LIST:
                    phase_specs = results_by_bin[bin_hours]['phase_specs']
                    group_to_mouse_records = results_by_bin[bin_hours]['group_to_mouse_records']
                    fig, axes = plt.subplots(1, 2, figsize=(16.5, 7.2), sharey=True)
                    fig.patch.set_facecolor('white')
                    rng = np.random.default_rng(100 + bin_hours + sum(ord(c) for c in metric_key))
                    box_width = 0.24 if bin_hours == 6 else 0.18
                    y_limits = metric_ylim(metric_key, bin_hours)

                    for ax, (phase_title, phase_indices, phase_labels) in zip(axes, phase_specs):
                        # For 6-hour bin pages, compress the x positions so neighboring
                        # time-bin box pairs sit closer together. 3-hour pages keep
                        # the original spacing.
                        x_step = 0.62 if bin_hours == 6 else 1.0
                        x = np.arange(len(phase_indices)) * x_step
                        ax.set_facecolor(plot_bg if phase_title.startswith('Light') else dark_panel_bg)
                        legend_handles = []

                        for group in ['SNr-DTA', 'Control']:
                            records = group_to_mouse_records[group]
                            if not records:
                                continue
                            arr = np.asarray([r[metric_key] for r in records], dtype=float)
                            phase_arr = arr[:, phase_indices]
                            offset = group_offsets[group]
                            fill_color = group_fill_colors[group]

                            for rec in records:
                                jitter = rng.normal(0, 0.018 if bin_hours == 6 else 0.014, size=len(phase_indices))
                                ax.scatter(x + offset + jitter,
                                           np.asarray(rec[metric_key], dtype=float)[phase_indices],
                                           s=85 if bin_hours == 6 else 64,
                                           color=rec['color'], edgecolor='black', linewidth=1.4,
                                           alpha=0.98, marker=group_markers[group], zorder=3)

                            for j in range(phase_arr.shape[1]):
                                st = _stats(phase_arr[:, j])
                                draw_mean_sem_box(ax, x[j] + offset, st, box_width, fill_color)

                            legend_handles.append(
                                Rectangle((0, 0), 1, 1, facecolor=fill_color, edgecolor='black', alpha=0.68,
                                          label=f'{group} (n={len(records)} mice)')
                            )

                        ax.set_title(phase_title, fontsize=18, fontweight='bold')
                        ax.set_xticks(x)
                        ax.set_xticklabels(phase_labels, fontsize=12)
                        ax.set_xlabel('Clock time (h)', fontsize=14, fontweight='bold')
                        ax.set_ylim(*y_limits)
                        ax.grid(True, axis='y', linestyle='-', alpha=0.28, linewidth=1.0)
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        ax.spines['left'].set_linewidth(1.8)
                        ax.spines['bottom'].set_linewidth(1.8)
                        ax.tick_params(axis='both', labelsize=12, width=1.6, length=6)
                        ax.legend(handles=legend_handles, loc='upper right', fontsize=9.0, frameon=False)

                    axes[0].set_ylabel(cfg['ylabel'](bin_hours), fontsize=17, fontweight='bold')
                    fig.suptitle(cfg['title'], fontsize=22, fontweight='bold', y=0.965)
                    fig.text(0.5, 0.025, cfg['calc_note'], ha='center', va='bottom', fontsize=9)
                    fig.tight_layout(rect=[0, 0.075, 1, 0.93])
                    pdf.savefig(fig, bbox_inches='tight')
                    plt.close(fig)

        # ------------------------------------------------------------------
        # Interactive selection: choose one metric and one set of clock bins.
        # ------------------------------------------------------------------
        selected_metric_key = _ask_pooled_metric_selection()
        if not selected_metric_key:
            messagebox.showinfo('Cancelled', 'No metric selected.')
            return

        selected_bin_hours = _ask_bin_hours_selection()
        if not selected_bin_hours:
            messagebox.showinfo('Cancelled', 'No bin size selected.')
            return

        available_labels = results_by_bin[selected_bin_hours]['bin_labels']
        selected_clock_bins = _ask_clock_bin_selection(selected_bin_hours, available_labels)
        if not selected_clock_bins:
            messagebox.showinfo('Cancelled', 'No clock bins selected.')
            return

        def _safe_name(text_value):
            import re as _re
            s = str(text_value).strip()
            s = _re.sub(r'[^A-Za-z0-9_\-]+', '_', s)
            s = _re.sub(r'_+', '_', s).strip('_')
            return s if s else 'selection'

        def save_selected_grouped_plot(metric_key, bin_hours, selected_labels):
            cfg = metric_configs[metric_key]
            phase_specs_full = results_by_bin[bin_hours]['phase_specs']
            group_to_mouse_records = results_by_bin[bin_hours]['group_to_mouse_records']
            y_limits = metric_ylim(metric_key, bin_hours)
            rng = np.random.default_rng(100 + bin_hours + sum(ord(c) for c in metric_key))
            box_width = 0.24 if bin_hours == 6 else 0.18

            selected_phase_specs = []
            selected_set = set(selected_labels)
            for phase_title, phase_indices, phase_labels in phase_specs_full:
                kept_pairs = [(idx, lab) for idx, lab in zip(phase_indices, phase_labels) if lab in selected_set]
                if kept_pairs:
                    sel_indices = [p[0] for p in kept_pairs]
                    sel_labels = [p[1] for p in kept_pairs]
                    selected_phase_specs.append((phase_title, sel_indices, sel_labels))

            if not selected_phase_specs:
                raise ValueError('No valid selected time windows were found for this bin size.')

            n_panels = len(selected_phase_specs)
            fig, axes = plt.subplots(1, n_panels, figsize=(8.5 * n_panels, 7.2), sharey=True)
            if n_panels == 1:
                axes = [axes]
            fig.patch.set_facecolor('white')

            for ax, (phase_title, phase_indices, phase_labels) in zip(axes, selected_phase_specs):
                x_step = 0.62 if bin_hours == 6 else 1.0
                x = np.arange(len(phase_indices)) * x_step
                ax.set_facecolor(plot_bg if phase_title.startswith('Light') else dark_panel_bg)
                legend_handles = []

                for group in ['SNr-DTA', 'Control']:
                    records = group_to_mouse_records[group]
                    if not records:
                        continue
                    arr = np.asarray([r[metric_key] for r in records], dtype=float)
                    phase_arr = arr[:, phase_indices]
                    offset = group_offsets[group]
                    fill_color = group_fill_colors[group]

                    for rec in records:
                        jitter = rng.normal(0, 0.018 if bin_hours == 6 else 0.014, size=len(phase_indices))
                        ax.scatter(x + offset + jitter,
                                   np.asarray(rec[metric_key], dtype=float)[phase_indices],
                                   s=85 if bin_hours == 6 else 64,
                                   color=rec['color'], edgecolor='black', linewidth=1.4,
                                   alpha=0.98, marker=group_markers[group], zorder=3)

                    for j in range(phase_arr.shape[1]):
                        st = _stats(phase_arr[:, j])
                        draw_mean_sem_box(ax, x[j] + offset, st, box_width, fill_color)

                    legend_handles.append(
                        Rectangle((0, 0), 1, 1, facecolor=fill_color, edgecolor='black', alpha=0.68,
                                  label=f'{group} (n={len(records)} mice)')
                    )

                ax.set_title(phase_title, fontsize=18, fontweight='bold')
                ax.set_xticks(x)
                ax.set_xticklabels(phase_labels, fontsize=12)
                ax.set_xlabel('Clock time (h)', fontsize=14, fontweight='bold')
                ax.set_ylim(*y_limits)
                ax.grid(True, axis='y', linestyle='-', alpha=0.28, linewidth=1.0)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_linewidth(1.8)
                ax.spines['bottom'].set_linewidth(1.8)
                ax.tick_params(axis='both', labelsize=12, width=1.6, length=6)
                ax.legend(handles=legend_handles, loc='upper right', fontsize=9.0, frameon=False)

            axes[0].set_ylabel(cfg['ylabel'](bin_hours), fontsize=17, fontweight='bold')
            fig.suptitle(f"{cfg['title']} ({bin_hours}h bins)", fontsize=22, fontweight='bold', y=0.965)
            fig.text(0.5, 0.025, cfg['calc_note'], ha='center', va='bottom', fontsize=9)
            fig.tight_layout(rect=[0, 0.075, 1, 0.93])

            metric_tag = _safe_name(metric_key)
            window_tag = _safe_name('_'.join(selected_labels))
            output_pdf = f'./SelectedPooledCircadian_{metric_tag}_{bin_hours}h_{window_tag}.pdf'
            output_eps = output_pdf.replace('.pdf', '.eps')

            fig.savefig(output_pdf, bbox_inches='tight')
            fig.savefig(output_eps, format='eps')
            plt.close(fig)
            return output_pdf, output_eps

        selected_pdf_path, selected_eps_path = save_selected_grouped_plot(
            selected_metric_key, selected_bin_hours, selected_clock_bins
        )

        print(f"Saved selected pooled circadian PDF: {selected_pdf_path}")
        print(f"Saved selected pooled circadian EPS: {selected_eps_path}")
        print(f"Saved per-mouse CSV: {per_mouse_csv_path}")
        print(f"Saved group summary CSV: {summary_csv_path}")
        print(f"Saved zero-value sanity-check CSV: {zero_value_csv_path}")
        print(f"Saved count/duration/inactivity-interval sanity-check CSV: {count_duration_interval_sanity_csv_path}")
        print(f"Saved low-bout-count data points CSV: {printed_zero_data_csv_path}")

        messagebox.showinfo(
            "Done",
            f"Selected pooled circadian PDF:\n{selected_pdf_path}\n\n"
            f"Selected pooled circadian EPS:\n{selected_eps_path}\n\n"
            f"CSV per mouse: {per_mouse_csv_path}\n"
            f"CSV group summary: {summary_csv_path}\n"
            f"CSV zero-value sanity check: {zero_value_csv_path}\n"
            f"CSV count/duration/inactivity-interval sanity check: {count_duration_interval_sanity_csv_path}\n"
            f"CSV low-bout-count data points: {printed_zero_data_csv_path}"
        )

    # backward-compatible alias
    def plot_pooled_4h_circadian_activity(self):
        return self.plot_pooled_circadian_activity_by_phase()

    def generate_bout_statistics_summary_multi_cohort(self):
        """
        Generate a multi-cohort bout-statistics summary.

        Outputs:
        1) A cohort-separated PDF (4 figures; each figure is a 2x2 layout, one panel per cohort)
        2) A truly pooled PDF (4 figures; each figure shows only pooled SNr-DTA vs pooled Control)
        3) A CSV summarizing light/dark bout metrics and Lomb-Scargle circadian metrics per mouse

        Notes / filters:
        - Only uses days 8-21
        - Excludes mouse 3 in cohort 1
        - Excludes mice 1-4 in cohort 2 (matches the previous script logic)
        - Excludes mouse 7 in cohort 4
        """
        from matplotlib.backends.backend_pdf import PdfPages
        from matplotlib.lines import Line2D
        from tkinter import filedialog
        from scipy import signal as scipy_signal

        truncate_flag = 0
        acc_plot = 1
        acc_nozero = 0

        file_paths = filedialog.askopenfilenames(
            title="Select cohort data files (multiple cohorts)",
            filetypes=[("Data Files", "*.csv *.xls *.xlsx")]
        )

        if not file_paths:
            messagebox.showinfo("No Files", "No files selected.")
            return

        remove_lm45 = self._ask_remove_lm45_from_mouse_pool("multi-cohort bout statistics")
        # Cohort 2 mouse IDs 1-4 are excluded by rule; do not ask to include SC04/SC05/SC06.
        include_sc04 = False
        include_sc05 = False
        include_sc06 = False

        try:
            use_cohort2_special_colors = messagebox.askyesno(
                "Special colors for cohort 2?",
                "If cohort 2 mice SC04, SC05, SC06, or SC08 are included, use special colors?\n\n"
                "Yes = SC04/SC05/SC06 use orange gradients, SC08 uses gold-yellow\n"
                "No = use regular group colors"
            )
        except Exception:
            use_cohort2_special_colors = False

        print(f"Loading {len(file_paths)} cohort file(s)...")

        DAY_MIN = 8
        DAY_MAX = 21
        threshold = 10

        def _cohort2_special_color_for_label(label):
            if not use_cohort2_special_colors:
                return None
            label_upper = str(label).upper()
            if 'SC04' in label_upper:
                return (0.95, 0.48, 0.05)
            if 'SC05' in label_upper:
                return (0.90, 0.35, 0.02)
            if 'SC06' in label_upper:
                return (0.75, 0.22, 0.00)
            if 'SC08' in label_upper:
                return '#FFD700'
            return None

        # ------------------------------------------------------------------
        # Load cohort data
        # ------------------------------------------------------------------
        cohort_data_dict = {}

        for file_path in file_paths:
            try:
                if file_path.endswith('.xls') or file_path.endswith('.csv'):
                    cohort_num = int(file_path[-5:-4])
                else:
                    cohort_num = int(file_path[-6:-5])

                mouse_labels = self._labels_for_cohort_global(cohort_num)

                if file_path.endswith('.xls') or file_path.endswith('.xlsx'):
                    try:
                        df = pd.read_csv(file_path, skiprows=10, sep='	')
                    except Exception:
                        df = pd.read_csv(file_path, skiprows=10)
                elif file_path.endswith('.csv'):
                    df = pd.read_csv(file_path, skiprows=10)
                else:
                    continue

                df = df.dropna(how='all').dropna(axis=1, how='all')
                df.columns = [col.strip() for col in df.columns]

                if 'Bin' not in df.columns:
                    print(f"Warning: No 'Bin' column in cohort {cohort_num}, skipping")
                    continue

                df['Bin'] = pd.to_datetime(df['Bin'], format='mixed', errors='coerce')
                df = df.dropna(subset=['Bin'])

                reference_date = df['Bin'].dt.normalize().min().date()
                if cohort_num == 3:
                    reference_date = reference_date - timedelta(days=8)

                ref_ts = pd.Timestamp(reference_date)
                df['DateIndex'] = (df['Bin'].dt.normalize() - ref_ts).dt.days
                df = df[(df['DateIndex'] >= DAY_MIN) & (df['DateIndex'] <= DAY_MAX)]

                if df.empty:
                    print(f"Warning: No data in day range {DAY_MIN}-{DAY_MAX} for cohort {cohort_num}")
                    continue

                mouse_ids = sorted(set(col.split()[2] for col in df.columns if col.startswith('1 8')))
                mouse_ids = [int(m) for m in mouse_ids if str(m).isdigit()]

                excluded_mice = []
                if cohort_num == 1 and 3 in mouse_ids:
                    mouse_ids.remove(3)
                    excluded_mice.append(3)
                if cohort_num == 2:
                    # Cohort 2 exclusion rule:
                    # remove mouse IDs 1, 2, 3, and 4.
                    # SC08 = mouse ID 5 remains available.
                    for i in [1, 2, 3, 4]:
                        if i in mouse_ids:
                            mouse_ids.remove(i)
                            excluded_mice.append(i)
                if cohort_num == 4:
                    for i in [7]:
                        if i in mouse_ids:
                            mouse_ids.remove(i)
                            excluded_mice.append(i)

                before_lm45_filter = list(mouse_ids)
                mouse_ids = self._apply_lm45_mouse_filter(mouse_ids, mouse_labels, remove_lm45, cohort_num=cohort_num, context='multi-cohort bout statistics')
                for removed_mid in sorted(set(before_lm45_filter) - set(mouse_ids)):
                    if removed_mid not in excluded_mice:
                        excluded_mice.append(removed_mid)

                snr_mice = []
                ctrl_mice = []
                for mid in mouse_ids:
                    if mid - 1 < len(mouse_labels):
                        label = mouse_labels[mid - 1]
                        if 'SNr' in label or 'DTA' in label:
                            snr_mice.append(mid)
                        elif 'Control' in label:
                            ctrl_mice.append(mid)

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
            messagebox.showerror('Error', 'No cohort files loaded successfully.')
            return

        cohort_numbers = sorted(cohort_data_dict.keys())
        print(f"\nSuccessfully loaded {len(cohort_numbers)} cohort(s): {cohort_numbers}")

        # ------------------------------------------------------------------
        # Analysis helpers
        # ------------------------------------------------------------------
        def analyze_mouse_bouts(mouse_df, rev_col, threshold=10):
            bout_speeds = []
            bout_durations = []
            inter_bout_intervals = []

            for _, day_df in mouse_df.groupby('DateIndex'):
                day_df = day_df.sort_values('Bin').copy()
                if rev_col not in day_df.columns:
                    continue

                revs = pd.to_numeric(day_df[rev_col], errors='coerce').fillna(0.0)
                revs = revs.where(revs >= threshold, 0.0)
                active = revs > 0
                if not active.any():
                    continue

                run_id = (active != active.shift(fill_value=False)).cumsum()
                active_runs = []

                for _, group in revs.groupby(run_id):
                    if not active.loc[group.index].iloc[0]:
                        continue
                    if truncate_flag & len(group)>=3:
                        group = group[1:-1]
                    bout_durations.append(len(group))
                    bout_speeds.append(group.mean())
                    active_runs.append(group.index)

                for i in range(len(active_runs) - 1):
                    current_end_idx = active_runs[i][-1]
                    next_start_idx = active_runs[i + 1][0]
                    ibi_val = next_start_idx - current_end_idx - 1
                    if ibi_val >= 1:
                        inter_bout_intervals.append(ibi_val)

            return bout_speeds, bout_durations, inter_bout_intervals

        def collect_accelerations(mouse_list, df_src, threshold=10):
            accels = []
            for mid in mouse_list:
                rev_col = f'1 8 {mid} rev'
                if rev_col not in df_src.columns:
                    continue
                for _, day_df in df_src.groupby('DateIndex'):
                    day_df = day_df.sort_values('Bin').copy()
                    revs = pd.to_numeric(day_df[rev_col], errors='coerce').fillna(0.0)
                    revs = revs.where(revs >= threshold, 0.0).values
                    active = revs > 0
                    for i in range(1, len(revs)):
                        if active[i] and active[i - 1]:
                            delta =revs[i] - revs[i - 1]
                            if acc_nozero:
                                if delta != 0:
                                    accels.append(revs[i] - revs[i - 1])
                            else:
                                accels.append(revs[i] - revs[i - 1])
            return accels

        def make_log_bins(values, min_edge=1.0, max_cap=1440.0, n_edges=40):
            vals = [float(v) for v in values if pd.notna(v) and v >= min_edge]
            upper = min(max(vals), max_cap) if vals else 10.0
            if upper <= min_edge:
                upper = min_edge * 10.0
            return np.logspace(np.log10(min_edge), np.log10(upper), n_edges)

        snr_color = (0.4, 0.7, 0.4)
        ctrl_color = (0.3, 0.3, 0.3)

        def value_stats(values):
            """Return n, mean, SEM, and median for a numeric vector."""
            arr = np.asarray(values, dtype=float)
            arr = arr[~np.isnan(arr)]
            n = len(arr)
            if n == 0:
                return {'n': 0, 'mean': np.nan, 'sem': np.nan, 'median': np.nan}
            sem = float(np.std(arr, ddof=1) / np.sqrt(n)) if n > 1 else np.nan
            return {
                'n': n,
                'mean': float(np.mean(arr)),
                'sem': sem,
                'median': float(np.median(arr))
            }

        def add_custom_legend(ax, snr_stats=None, ctrl_stats=None,
                              stat_name='mean', stat_decimals=1,
                              count_label='bouts', pooled=False,
                              fontsize=8):
            handles = []
            labels = []

            snr_base =  'SNr-DTA'
            ctrl_base = 'Control'

            def _stat_label(base, stats):
                if stats is None or stats['n'] == 0:
                    return None
                sem_text = 'NA' if np.isnan(stats['sem']) else f"{stats['sem']:.{stat_decimals}f}"
                if stat_name == 'mean':
                    return f"{base} mean ± SEM = {stats['mean']:.{stat_decimals}f} ± {sem_text}"
                return (
                    f"{base} {stat_name} = {stats['median']:.{stat_decimals}f}; "
                    f"mean ± SEM = {stats['mean']:.{stat_decimals}f} ± {sem_text}"
                )

            if snr_stats is not None and snr_stats['n'] > 0:
                handles.append(Line2D([0], [0], color=snr_color, lw=2.2, linestyle='-'))
                labels.append(f"{snr_base} (n={snr_stats['n']} {count_label})")
                handles.append(Line2D([0], [0], color=snr_color, lw=2.0, linestyle='--'))
                labels.append(_stat_label(snr_base, snr_stats))

            if ctrl_stats is not None and ctrl_stats['n'] > 0:
                handles.append(Line2D([0], [0], color=ctrl_color, lw=2.2, linestyle='-'))
                labels.append(f"{ctrl_base} (n={ctrl_stats['n']} {count_label})")
                handles.append(Line2D([0], [0], color=ctrl_color, lw=2.0, linestyle='--'))
                labels.append(_stat_label(ctrl_base, ctrl_stats))

            if handles:
                ax.legend(handles, labels, loc='best', fontsize=fontsize, frameon=False)


        def add_accel_split_legend(ax, snr_vals, ctrl_vals,
                                   count_label='transitions', fontsize=8,
                                   stat_decimals=2):
            """
            Legend specifically for acceleration plots.

            Instead of reporting one overall mean for each group, report two
            conditional means per group:
              - positive Δ speed transitions only (acceleration)
              - negative Δ speed transitions only (deceleration)
            """
            handles = []
            labels = []

            def _mean_sem_text(values, decimals=2):
                stats = value_stats(values)
                if stats['n'] == 0:
                    return "n=0"
                sem_text = 'NA' if np.isnan(stats['sem']) else f"{stats['sem']:.{decimals}f}"
                return f"mean ± SEM = {stats['mean']:.{decimals}f} ± {sem_text} (n={stats['n']}) "

            def _add_group(base, color, vals):
                vals = np.asarray(vals, dtype=float)
                vals = vals[~np.isnan(vals)]
                pos_vals = vals[vals > 0]
                neg_vals = vals[vals < 0]

                handles.append(Line2D([0], [0], color=color, lw=2.2, linestyle='-'))
                labels.append(f"{base} (n={len(vals)} {count_label})")

                handles.append(Line2D([0], [0], color=color, lw=2.0, linestyle='--'))
                labels.append(f"{base} acceleration: {_mean_sem_text(pos_vals, stat_decimals)}")

                handles.append(Line2D([0], [0], color=color, lw=2.0, linestyle=':'))
                labels.append(f"{base} deceleration: {_mean_sem_text(neg_vals, stat_decimals)}")

            if snr_vals:
                _add_group('SNr-DTA', snr_color, snr_vals)
            if ctrl_vals:
                _add_group('Control', ctrl_color, ctrl_vals)

            if handles:
                ax.legend(handles, labels, loc='best', fontsize=fontsize, frameon=False)

        def draw_two_group_hist(ax, snr_vals, ctrl_vals, bins_arr,
                                xlabel, title,
                                stat_func=np.mean, stat_name='mean', stat_decimals=1,
                                use_log_x=False, xlim=None,
                                count_label='bouts', pooled=False,
                                accel_split_legend=False):
            """
            Draw SNr-DTA vs Control histograms as within-group proportions.

            Each group is normalized independently, so the area/count contribution
            across all bins sums to 1.0 for SNr-DTA and 1.0 for Control. This makes
            the y-axis comparable even when groups have different numbers of mice
            or different total numbers of bouts/intervals/transitions.
            """
            from matplotlib.ticker import PercentFormatter

            snr_vals = list(snr_vals) if snr_vals is not None else []
            ctrl_vals = list(ctrl_vals) if ctrl_vals is not None else []

            snr_stats = value_stats(snr_vals)
            ctrl_stats = value_stats(ctrl_vals)

            if snr_vals:
                snr_weights = np.ones(len(snr_vals), dtype=float) / len(snr_vals)
                ax.hist(snr_vals, bins=bins_arr, histtype='step', weights=snr_weights,
                        edgecolor=snr_color, linewidth=2.2)

            if ctrl_vals:
                ctrl_weights = np.ones(len(ctrl_vals), dtype=float) / len(ctrl_vals)
                ax.hist(ctrl_vals, bins=bins_arr, histtype='step', weights=ctrl_weights,
                        edgecolor=ctrl_color, linewidth=2.2)

            if use_log_x:
                ax.set_xscale('log')
                right_edge = bins_arr[-1] if xlim is None else xlim[1]
                ax.set_xlim(1, right_edge)

                # Cleaner tick labels for inactivity interval plots.
                # ibi_xticks is defined later in the enclosing function before plotting.
                try:
                    ax.set_xticks(ibi_xticks)
                except NameError:
                    ax.set_xticks([1, 2, 3, 4, 5, 10, 20, 50, 100, 500, 1000])
                ax.get_xaxis().set_major_formatter(plt.ScalarFormatter())
            elif xlim is not None:
                ax.set_xlim(*xlim)

            ax.set_xlabel(xlabel, fontsize=11, fontweight='bold')
            ax.set_ylabel('Proportion within group', fontsize=11, fontweight='bold')
            ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            if accel_split_legend:
                add_accel_split_legend(
                    ax,
                    snr_vals=snr_vals,
                    ctrl_vals=ctrl_vals,
                    count_label=count_label,
                    fontsize=8,
                    stat_decimals=stat_decimals
                )
            else:
                add_custom_legend(
                    ax,
                    snr_stats=snr_stats if snr_vals else None,
                    ctrl_stats=ctrl_stats if ctrl_vals else None,
                    stat_name=stat_name,
                    stat_decimals=stat_decimals,
                    count_label=count_label,
                    pooled=pooled,
                    fontsize=8
                )

        # ------------------------------------------------------------------
        # Collect cohort-level data
        # ------------------------------------------------------------------
        cohort_bout_data = {}
        cohort_accel_data = {}
        highspeed_mouse_rows = []

        for cohort_num in cohort_numbers:
            cohort_info = cohort_data_dict[cohort_num]
            df = cohort_info['df']
            snr_mice = cohort_info['snr_mice']
            ctrl_mice = cohort_info['ctrl_mice']

            snr_bout_speeds, snr_bout_durations, snr_intervals = [], [], []
            ctrl_bout_speeds, ctrl_bout_durations, ctrl_intervals = [], [], []

            for mid in snr_mice:
                rev_col = f'1 8 {mid} rev'
                if rev_col not in df.columns:
                    continue
                mouse_df = df[['Bin', 'DateIndex', rev_col]].copy()
                speeds, durations, intervals = analyze_mouse_bouts(mouse_df, rev_col, threshold)
                snr_bout_speeds.extend(speeds)
                snr_bout_durations.extend(durations)
                snr_intervals.extend(intervals)

                total_bouts = len(speeds)
                highspeed_bouts = int(np.sum(np.asarray(speeds, dtype=float) > 60)) if total_bouts > 0 else 0
                highspeed_pct = float(100.0 * highspeed_bouts / total_bouts) if total_bouts > 0 else np.nan
                mouse_label = cohort_info['labels'][int(mid) - 1] if int(mid) - 1 < len(cohort_info['labels']) else f'Mouse {mid}'
                highspeed_mouse_rows.append({
                    'Cohort': cohort_num,
                    'MouseID': int(mid),
                    'ID': str(mouse_label).split('(')[0],
                    'MouseLabel': mouse_label,
                    'Group': 'SNr-DTA',
                    'TotalBouts': int(total_bouts),
                    'HighSpeedBouts_gt60revPerMin': int(highspeed_bouts),
                    'LowSpeedBouts_le60revPerMin': int(total_bouts - highspeed_bouts),
                    'HighSpeedBoutPercent_gt60revPerMin': highspeed_pct,
                    'LowSpeedBoutPercent_le60revPerMin': float(100.0 - highspeed_pct) if np.isfinite(highspeed_pct) else np.nan,
                })

            for mid in ctrl_mice:
                rev_col = f'1 8 {mid} rev'
                if rev_col not in df.columns:
                    continue
                mouse_df = df[['Bin', 'DateIndex', rev_col]].copy()
                speeds, durations, intervals = analyze_mouse_bouts(mouse_df, rev_col, threshold)
                ctrl_bout_speeds.extend(speeds)
                ctrl_bout_durations.extend(durations)
                ctrl_intervals.extend(intervals)

                total_bouts = len(speeds)
                highspeed_bouts = int(np.sum(np.asarray(speeds, dtype=float) > 60)) if total_bouts > 0 else 0
                highspeed_pct = float(100.0 * highspeed_bouts / total_bouts) if total_bouts > 0 else np.nan
                mouse_label = cohort_info['labels'][int(mid) - 1] if int(mid) - 1 < len(cohort_info['labels']) else f'Mouse {mid}'
                highspeed_mouse_rows.append({
                    'Cohort': cohort_num,
                    'MouseID': int(mid),
                    'ID': str(mouse_label).split('(')[0],
                    'MouseLabel': mouse_label,
                    'Group': 'Control',
                    'TotalBouts': int(total_bouts),
                    'HighSpeedBouts_gt60revPerMin': int(highspeed_bouts),
                    'LowSpeedBouts_le60revPerMin': int(total_bouts - highspeed_bouts),
                    'HighSpeedBoutPercent_gt60revPerMin': highspeed_pct,
                    'LowSpeedBoutPercent_le60revPerMin': float(100.0 - highspeed_pct) if np.isfinite(highspeed_pct) else np.nan,
                })

            cohort_bout_data[cohort_num] = {
                'snr_speeds': snr_bout_speeds,
                'snr_durations': snr_bout_durations,
                'snr_intervals': snr_intervals,
                'ctrl_speeds': ctrl_bout_speeds,
                'ctrl_durations': ctrl_bout_durations,
                'ctrl_intervals': ctrl_intervals,
                'n_snr': len(snr_mice),
                'n_ctrl': len(ctrl_mice)
            }

            cohort_accel_data[cohort_num] = {
                'snr': collect_accelerations(snr_mice, df, threshold),
                'ctrl': collect_accelerations(ctrl_mice, df, threshold),
            }

            print(f"Cohort {cohort_num}: SNr {len(snr_bout_speeds)} bouts, Ctrl {len(ctrl_bout_speeds)} bouts")

        def _save_speed_and_boutcount_group_barplots(highspeed_rows):
            """
            Save a group-level PDF with two bar plots:
              1. percentage of high-speed bouts (>60 rev/min)
              2. total bout count

            Each dot is one mouse. Bars show group mean ± SEM.
            SNr-DTA = green; Control = grey.
            """
            if not highspeed_rows:
                print('No high-speed / bout-count rows generated.')
                return 'N/A', pd.DataFrame()

            hs_df = pd.DataFrame(highspeed_rows)
            hs_df = hs_df.sort_values(['Group', 'Cohort', 'ID']).copy()

            pdf_out = './BoutStatistics_GroupBars_HighSpeedPercent_and_BoutCount.pdf'

            color_map = {
                'SNr-DTA': (0.18, 0.62, 0.18),  # green
                'Control': (0.50, 0.50, 0.50),  # grey
            }
            group_order = ['SNr-DTA', 'Control']

            def _sem(vals):
                vals = np.asarray(vals, dtype=float)
                vals = vals[np.isfinite(vals)]
                if len(vals) <= 1:
                    return 0.0
                return float(np.std(vals, ddof=1) / np.sqrt(len(vals)))

            def _draw_group_bar(ax, metric_col, y_label, title):
                rng = np.random.default_rng(42)
                x = np.arange(len(group_order))
                means = []
                sems = []

                for gi, group_name in enumerate(group_order):
                    sub = hs_df[hs_df['Group'] == group_name].copy()
                    vals = pd.to_numeric(sub[metric_col], errors='coerce').to_numpy(dtype=float)
                    vals = vals[np.isfinite(vals)]

                    mean_val = float(np.mean(vals)) if len(vals) else np.nan
                    sem_val = _sem(vals) if len(vals) else np.nan
                    means.append(mean_val)
                    sems.append(sem_val if np.isfinite(sem_val) else 0.0)

                    color = color_map[group_name]
                    if len(vals) > 0:
                        jitter = rng.normal(0, 0.045, size=len(vals))
                        ax.scatter(
                            np.full(len(vals), gi, dtype=float) + jitter,
                            vals,
                            s=70,
                            color=color,
                            edgecolor='black',
                            linewidth=0.8,
                            alpha=0.92,
                            zorder=4
                        )
                        ax.text(
                            gi,
                            mean_val,
                            f'n={len(vals)}',
                            ha='center',
                            va='bottom',
                            fontsize=9,
                            fontweight='bold'
                        )

                ax.bar(
                    x,
                    means,
                    yerr=sems,
                    color=[color_map[g] for g in group_order],
                    edgecolor='black',
                    linewidth=1.0,
                    alpha=0.75,
                    capsize=5,
                    zorder=2
                )
                ax.set_xticks(x)
                ax.set_xticklabels(group_order, fontsize=11, fontweight='bold')
                ax.set_ylabel(y_label, fontsize=12, fontweight='bold')
                ax.set_title(title, fontsize=14, fontweight='bold')
                ax.grid(True, axis='y', alpha=0.30, linestyle='--')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)

                finite_vals = pd.to_numeric(hs_df[metric_col], errors='coerce').to_numpy(dtype=float)
                finite_vals = finite_vals[np.isfinite(finite_vals)]
                if len(finite_vals):
                    ax.set_ylim(0, max(1.0, float(np.nanmax(finite_vals)) * 1.22))

            with PdfPages(pdf_out) as pdf:
                fig, ax = plt.subplots(figsize=(6.8, 5.8))
                _draw_group_bar(
                    ax,
                    'HighSpeedBoutPercent_gt60revPerMin',
                    'High-speed bouts (% of total bouts)',
                    f'High-speed bout percentage (>60 rev/min), Days {DAY_MIN}-{DAY_MAX}'
                )
                fig.text(
                    0.5, 0.01,
                    'Each dot = one mouse. Bar = group mean ± SEM.',
                    ha='center',
                    va='bottom',
                    fontsize=9
                )
                plt.tight_layout(rect=[0, 0.045, 1, 0.95])
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

                fig, ax = plt.subplots(figsize=(6.8, 5.8))
                _draw_group_bar(
                    ax,
                    'TotalBouts',
                    'Total bout count',
                    f'Total bout count, Days {DAY_MIN}-{DAY_MAX}'
                )
                fig.text(
                    0.5, 0.01,
                    'Each dot = one mouse. Bar = group mean ± SEM.',
                    ha='center',
                    va='bottom',
                    fontsize=9
                )
                plt.tight_layout(rect=[0, 0.045, 1, 0.95])
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

            print(f"Saved group bar PDF for high-speed percentage and bout count: {pdf_out}")
            return pdf_out, hs_df

        highspeed_pdf_path, highspeed_df = _save_speed_and_boutcount_group_barplots(highspeed_mouse_rows)


        all_intervals = []
        for cohort_num in cohort_numbers:
            all_intervals.extend([x for x in cohort_bout_data[cohort_num]['snr_intervals'] if x >= 1])
            all_intervals.extend([x for x in cohort_bout_data[cohort_num]['ctrl_intervals'] if x >= 1])

        # Hybrid bins for integer-minute inactivity intervals on a log x-axis.
        # Rationale:
        #   - 1-20 min keeps integer-centered bins, so early intervals remain literal.
        #   - >20 min uses log-spaced tail bins, so the long tail is not visually crushed
        #     into many tiny needle-like boxes on the log axis.
        max_ibi = int(np.nanmax(all_intervals)) if all_intervals else 60
        ibi_integer_tail_start = 20

        if max_ibi <= ibi_integer_tail_start:
            ibi_bins = np.arange(0.5, max_ibi + 1.5, 1)
        else:
            ibi_integer_edges = np.arange(0.5, ibi_integer_tail_start + 1.5, 1)
            tail_start_edge = ibi_integer_tail_start + 0.5
            tail_end_edge = max_ibi + 0.5
            # About 24 tail edges gives smooth visual resolution without producing
            # ultra-thin boxes near 100-1000 min.
            ibi_tail_edges = np.logspace(
                np.log10(tail_start_edge),
                np.log10(tail_end_edge),
                24
            )
            ibi_bins = np.unique(np.concatenate([ibi_integer_edges, ibi_tail_edges[1:]]))

        ibi_xticks = [1, 2, 3, 4, 5, 10, 20, 50, 100, 500, 1000]
        ibi_xticks = [x for x in ibi_xticks if x <= max_ibi + 1]

        # ------------------------------------------------------------------
        # Cohort-separated PDF (2x2 layouts)
        # ------------------------------------------------------------------
        cohort_str = '_'.join([f'C{c}' for c in cohort_numbers])
        pdf_path = './BoutStatistics_CohortSeparated.pdf'

        with PdfPages(pdf_path) as pdf:
            # Figure 1: Speed
            fig1, axes1 = plt.subplots(2, 2, figsize=(14, 12))
            axes1 = axes1.flatten()
            speed_bins = np.arange(10, 160, 5)
            for idx, cohort_num in enumerate(cohort_numbers[:4]):
                data = cohort_bout_data[cohort_num]
                draw_two_group_hist(
                    axes1[idx],
                    data['snr_speeds'], data['ctrl_speeds'], speed_bins,
                    'Bout Speed (revs/min)', f'Cohort {cohort_num}',
                    stat_func=np.mean, stat_name='mean', stat_decimals=1,
                    count_label='bouts', pooled=False
                )
            for idx in range(len(cohort_numbers), 4):
                axes1[idx].axis('off')
            fig1.suptitle(f'Bout Speed Proportional Distribution (Days {DAY_MIN}-{DAY_MAX})', fontsize=15, fontweight='bold')
            fig1.tight_layout(rect=[0, 0, 1, 0.96])
            pdf.savefig(fig1, bbox_inches='tight')
            plt.close(fig1)

            # Figure 2: Duration
            fig2, axes2 = plt.subplots(2, 2, figsize=(14, 12))
            axes2 = axes2.flatten()
            duration_bins = np.arange(1, 51, 1)
            for idx, cohort_num in enumerate(cohort_numbers[:4]):
                data = cohort_bout_data[cohort_num]
                draw_two_group_hist(
                    axes2[idx],
                    data['snr_durations'], data['ctrl_durations'], duration_bins,
                    'Bout Duration (minutes)', f'Cohort {cohort_num}',
                    stat_func=np.mean, stat_name='mean', stat_decimals=1,
                    xlim=(1, 50), count_label='bouts', pooled=False
                )
            for idx in range(len(cohort_numbers), 4):
                axes2[idx].axis('off')
            fig2.suptitle(f'Bout Duration Proportional Distribution (Days {DAY_MIN}-{DAY_MAX})', fontsize=15, fontweight='bold')
            fig2.tight_layout(rect=[0, 0, 1, 0.96])
            pdf.savefig(fig2, bbox_inches='tight')
            plt.close(fig2)

            # Figure 3: Inter-bout interval
            fig3, axes3 = plt.subplots(2, 2, figsize=(14, 12))
            axes3 = axes3.flatten()
            for idx, cohort_num in enumerate(cohort_numbers[:4]):
                data = cohort_bout_data[cohort_num]
                snr_intervals_filtered = [x for x in data['snr_intervals'] if x >= 1]
                ctrl_intervals_filtered = [x for x in data['ctrl_intervals'] if x >= 1]
                draw_two_group_hist(
                    axes3[idx],
                    snr_intervals_filtered, ctrl_intervals_filtered, ibi_bins,
                    'Inter-Bout Interval (minutes)', f'Cohort {cohort_num}',
                    stat_func=np.median, stat_name='median', stat_decimals=1,
                    use_log_x=True, count_label='intervals', pooled=False
                )
            for idx in range(len(cohort_numbers), 4):
                axes3[idx].axis('off')
            fig3.suptitle(f'Inter-Bout Interval Proportional Distribution (Days {DAY_MIN}-{DAY_MAX})', fontsize=15, fontweight='bold')
            fig3.tight_layout(rect=[0, 0, 1, 0.96])
            pdf.savefig(fig3, bbox_inches='tight')
            plt.close(fig3)

            # Figure 4: Acceleration
            fig4, axes4 = plt.subplots(2, 2, figsize=(14, 12))
            axes4 = axes4.flatten()
            accel_bins = np.arange(-100, 102, 2)
            for idx, cohort_num in enumerate(cohort_numbers[:4]):
                adata = cohort_accel_data[cohort_num]
                draw_two_group_hist(
                    axes4[idx],
                    adata['snr'], adata['ctrl'], accel_bins,
                    'Δ Speed between consecutive active bins (revs/min)', f'Cohort {cohort_num}',
                    stat_func=np.mean, stat_name='mean', stat_decimals=2,
                    count_label='', pooled=False,
                    accel_split_legend=True
                )
                axes4[idx].axvline(0, color='black', linewidth=1.0, linestyle='-', alpha=0.4)
            for idx in range(len(cohort_numbers), 4):
                axes4[idx].axis('off')
            fig4.suptitle(
                f'Within-Bout Acceleration Proportional Distribution (Days {DAY_MIN}-{DAY_MAX})\n'
                f'Δ speed between consecutive 1-min active bins; negative = deceleration',
                fontsize=14, fontweight='bold'
            )
            fig4.tight_layout(rect=[0, 0, 1, 0.96])
            pdf.savefig(fig4, bbox_inches='tight')
            plt.close(fig4)

        print(f"\nSaved multi-cohort summary: {pdf_path}")

        # ------------------------------------------------------------------
        # Summary CSV (light/dark + Lomb-Scargle)
        # ------------------------------------------------------------------
        def lomb_scargle_period(times, values, min_period=20, max_period=28):
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
                print(f'Lomb-Scargle error: {e}')
                return np.nan, np.nan, np.nan, np.nan

        LIGHT_HOURS = set(range(6, 18))
        summary_rows = []

        for cohort_num in cohort_numbers:
            cohort_info = cohort_data_dict[cohort_num]
            df_c = cohort_info['df'].copy()
            all_mice = cohort_info['snr_mice'] + cohort_info['ctrl_mice']

            for mid in all_mice:
                rev_col = f'1 8 {mid} rev'
                if rev_col not in df_c.columns:
                    continue

                label = cohort_info['labels'][int(mid) - 1] if int(mid) - 1 < len(cohort_info['labels']) else f'Mouse {mid}'

                mouse_df = df_c[['Bin', 'DateIndex', rev_col]].copy()
                mouse_df[rev_col] = pd.to_numeric(mouse_df[rev_col], errors='coerce').fillna(0.0)

                def _phase_from_bout_start(ts):
                    """
                    Assign phase by full-bout START time.

                    This is intentionally aligned with _build_per_mouse_bout_metric_df(),
                    where columns such as Light_06_18_BoutSpeed_revPerMin_mean are
                    computed from complete full-day bouts assigned by bout onset.
                    Do not pre-split the dataframe by light/dark hours here, because that
                    truncates/splits bouts crossing 06:00 or 18:00 and changes the speed.
                    """
                    h = pd.Timestamp(ts).hour + pd.Timestamp(ts).minute / 60.0 + pd.Timestamp(ts).second / 3600.0
                    if 6 <= h < 18:
                        return 'Light_06-18'
                    return 'Dark_18-06'

                def bout_stats_from_full_day_by_start_phase(mouse_df_in, rc, thr):
                    phase_speeds = {'Light_06-18': [], 'Dark_18-06': []}
                    phase_durations = {'Light_06-18': [], 'Dark_18-06': []}
                    phase_counts = {'Light_06-18': 0, 'Dark_18-06': 0}

                    for _, day_data in mouse_df_in.groupby('DateIndex'):
                        day_data = day_data.sort_values('Bin').copy()
                        revs = pd.to_numeric(day_data[rc], errors='coerce').fillna(0.0)
                        revs = revs.where(revs >= thr, 0.0)
                        active = revs > 0
                        if not active.any():
                            continue

                        run_id = (active != active.shift(fill_value=False)).cumsum()
                        for _, grp in revs.groupby(run_id):
                            if not active.loc[grp.index].iloc[0]:
                                continue
                            start_idx = grp.index[0]
                            start_ts = pd.Timestamp(day_data.loc[start_idx, 'Bin'])
                            phase = _phase_from_bout_start(start_ts)
                            phase_counts[phase] += 1
                            phase_speeds[phase].append(float(grp.mean()))
                            phase_durations[phase].append(float(len(grp)))

                    def _mean(vals):
                        return float(np.mean(vals)) if len(vals) else np.nan

                    def _median(vals):
                        return float(np.median(vals)) if len(vals) else np.nan

                    return {
                        'n_light': int(phase_counts['Light_06-18']),
                        'n_dark': int(phase_counts['Dark_18-06']),
                        'spd_light_mean': _mean(phase_speeds['Light_06-18']),
                        'spd_dark_mean': _mean(phase_speeds['Dark_18-06']),
                        'spd_light_median': _median(phase_speeds['Light_06-18']),
                        'spd_dark_median': _median(phase_speeds['Dark_18-06']),
                        'dur_light_mean': _mean(phase_durations['Light_06-18']),
                        'dur_dark_mean': _mean(phase_durations['Dark_18-06']),
                        'dur_light_median': _median(phase_durations['Light_06-18']),
                        'dur_dark_median': _median(phase_durations['Dark_18-06']),
                    }

                phase_stats = bout_stats_from_full_day_by_start_phase(mouse_df, rev_col, threshold)
                n_light = phase_stats['n_light']
                n_dark = phase_stats['n_dark']
                spd_light = phase_stats['spd_light_mean']
                spd_dark = phase_stats['spd_dark_mean']

                count_ratio = (n_light / (n_dark + n_light)) if (n_dark + n_light) > 0 else np.nan
                speed_ratio = (spd_light / (spd_dark + spd_light)) if (
                    np.isfinite(spd_light) and np.isfinite(spd_dark) and (spd_dark + spd_light) > 0
                ) else np.nan

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
                    'Cohort': cohort_num,
                    'Day': cohort_num,
                    'ID': label[0:4],
                    'Group': label.split('(')[1][:-1],
                    'BoutCount_Light_06-18': n_light,
                    'BoutCount_Dark_18-06': n_dark,
                    'BoutCount_Light06-18FractionOfLightPlusDark': round(count_ratio, 3) if not np.isnan(count_ratio) else np.nan,
                    'BoutSpeed_Light_06-18_revPerMin_mean': round(spd_light, 4) if not np.isnan(spd_light) else np.nan,
                    'BoutSpeed_Dark_18-06_revPerMin_mean': round(spd_dark, 4) if not np.isnan(spd_dark) else np.nan,
                    'BoutSpeed_Light06-18FractionOfLightPlusDark_mean': round(speed_ratio, 3) if not np.isnan(speed_ratio) else np.nan,
                    'BoutSpeed_Light_06-18_revPerMin_median': round(phase_stats['spd_light_median'], 4) if not np.isnan(phase_stats['spd_light_median']) else np.nan,
                    'BoutSpeed_Dark_18-06_revPerMin_median': round(phase_stats['spd_dark_median'], 4) if not np.isnan(phase_stats['spd_dark_median']) else np.nan,
                    'BoutDuration_Light_06-18_minute_mean': round(phase_stats['dur_light_mean'], 4) if not np.isnan(phase_stats['dur_light_mean']) else np.nan,
                    'BoutDuration_Dark_18-06_minute_mean': round(phase_stats['dur_dark_mean'], 4) if not np.isnan(phase_stats['dur_dark_mean']) else np.nan,
                    'BoutDuration_Light_06-18_minute_median': round(phase_stats['dur_light_median'], 4) if not np.isnan(phase_stats['dur_light_median']) else np.nan,
                    'BoutDuration_Dark_18-06_minute_median': round(phase_stats['dur_dark_median'], 4) if not np.isnan(phase_stats['dur_dark_median']) else np.nan,
                    'Tau_hours': round(tau, 2) if not np.isnan(tau) else np.nan,
                    'LS_Power': round(ls_power, 4) if not np.isnan(ls_power) else np.nan,
                    'LS_Amplitude': round(ls_amplitude, 2) if not np.isnan(ls_amplitude) else np.nan,
                    'LS_FalseAlarmProb': round(ls_fap, 4) if not np.isnan(ls_fap) else np.nan,
                })

        if summary_rows:
            summary_df = pd.DataFrame(summary_rows).sort_values(['Cohort', 'ID'])
            print('Generated light/dark ratio columns; these will be merged into the general per-mouse CSV.')
        else:
            summary_df = pd.DataFrame()
            print('Warning: No light/dark summary rows generated for CSV merge.')
        csv_path = 'merged into general per-mouse CSV'

        # ------------------------------------------------------------------
        # Console summary
        # ------------------------------------------------------------------
        print('\n' + '=' * 60)
        print(f'MULTI-COHORT BOUT STATISTICS SUMMARY (Days {DAY_MIN}-{DAY_MAX})')
        print('=' * 60)

        for cohort_num in cohort_numbers:
            data = cohort_bout_data[cohort_num]
            print(f'\nCohort {cohort_num}:')
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

        print('=' * 60 + '\n')

        # ------------------------------------------------------------------
        # Per-mouse metric statistics CSV
        # ------------------------------------------------------------------
        per_mouse_metric_df = self._build_per_mouse_bout_metric_df(
            cohort_data_dict=cohort_data_dict,
            day_min=DAY_MIN,
            day_max=DAY_MAX,
            threshold=threshold,
            truncate_flag=truncate_flag,
            acc_nozero=acc_nozero,
        )

        merge_keys = ['Cohort', 'ID', 'Group']
        if not per_mouse_metric_df.empty and isinstance(summary_df, pd.DataFrame) and not summary_df.empty:
            try:
                _check_df = per_mouse_metric_df.merge(
                    summary_df[['Cohort', 'ID', 'Group', 'BoutSpeed_Light_06-18_revPerMin_mean',
                                'BoutCount_Light_06-18']],
                    on=['Cohort', 'ID', 'Group'],
                    how='left'
                )
                if 'Light_06_18_BoutSpeed_revPerMin_mean' in _check_df.columns:
                    _diff = (
                        pd.to_numeric(_check_df['Light_06_18_BoutSpeed_revPerMin_mean'], errors='coerce') -
                        pd.to_numeric(_check_df['BoutSpeed_Light_06-18_revPerMin_mean'], errors='coerce')
                    ).abs()
                    if np.nanmax(_diff.to_numpy(dtype=float)) > 1e-6:
                        print('Warning: Light bout speed consistency check found nonzero differences:')
                        print(_check_df.loc[_diff > 1e-6, [
                            'Cohort', 'ID', 'Group',
                            'Light_06_18_BoutSpeed_revPerMin_mean',
                            'BoutSpeed_Light_06-18_revPerMin_mean'
                        ]].to_string(index=False))
                    else:
                        print('Light bout speed consistency check passed: Light_06_18_BoutSpeed_revPerMin_mean == BoutSpeed_Light_06-18_revPerMin_mean.')
            except Exception as e:
                print(f'Warning: light/dark consistency check skipped: {e}')

        if not per_mouse_metric_df.empty:
            merged_per_mouse_df = per_mouse_metric_df.copy()

            if isinstance(summary_df, pd.DataFrame) and not summary_df.empty:
                lightdark_cols = [
                    c for c in summary_df.columns
                    if c not in merge_keys + ['MouseLabel']
                ]
                merged_per_mouse_df = merged_per_mouse_df.merge(
                    summary_df[merge_keys + lightdark_cols].drop_duplicates(subset=merge_keys),
                    on=merge_keys,
                    how='left'
                )

            if isinstance(highspeed_df, pd.DataFrame) and not highspeed_df.empty:
                highspeed_cols = [
                    'Cohort', 'ID', 'Group',
                    'TotalBouts',
                    'HighSpeedBouts_gt60revPerMin',
                    'LowSpeedBouts_le60revPerMin',
                    'HighSpeedBoutPercent_gt60revPerMin',
                    'LowSpeedBoutPercent_le60revPerMin',
                ]
                highspeed_cols = [c for c in highspeed_cols if c in highspeed_df.columns]
                merged_per_mouse_df = merged_per_mouse_df.merge(
                    highspeed_df[highspeed_cols].drop_duplicates(subset=merge_keys),
                    on=merge_keys,
                    how='left'
                )

            per_mouse_metric_csv_path = os.path.join(
                os.path.dirname(os.path.abspath(pdf_path)),
                self._per_mouse_bout_metric_csv_filename(DAY_MIN, DAY_MAX)
            )
        else:
            merged_per_mouse_df = pd.DataFrame()
            per_mouse_metric_csv_path = 'N/A'
            print('Warning: No per-mouse metric rows generated.')

        # ------------------------------------------------------------------
        # Truly pooled PDF
        # ------------------------------------------------------------------
        pooled_pdf_path = pdf_path.replace(
            f'CohortSeparated',
            f'CohortPooled'
        )

        pooled_snr_speeds = []
        pooled_ctrl_speeds = []
        pooled_snr_durations = []
        pooled_ctrl_durations = []
        pooled_snr_intervals = []
        pooled_ctrl_intervals = []
        pooled_snr_accel = []
        pooled_ctrl_accel = []

        for cohort_num in cohort_numbers:
            pooled_snr_speeds.extend(cohort_bout_data[cohort_num]['snr_speeds'])
            pooled_ctrl_speeds.extend(cohort_bout_data[cohort_num]['ctrl_speeds'])
            pooled_snr_durations.extend(cohort_bout_data[cohort_num]['snr_durations'])
            pooled_ctrl_durations.extend(cohort_bout_data[cohort_num]['ctrl_durations'])
            pooled_snr_intervals.extend([x for x in cohort_bout_data[cohort_num]['snr_intervals'] if x >= 1])
            pooled_ctrl_intervals.extend([x for x in cohort_bout_data[cohort_num]['ctrl_intervals'] if x >= 1])
            pooled_snr_accel.extend(cohort_accel_data[cohort_num]['snr'])
            pooled_ctrl_accel.extend(cohort_accel_data[cohort_num]['ctrl'])

        print(f'POOLED DIAGNOSTIC | Speed: SNr={len(pooled_snr_speeds)}, Control={len(pooled_ctrl_speeds)}')
        print(f'POOLED DIAGNOSTIC | Duration: SNr={len(pooled_snr_durations)}, Control={len(pooled_ctrl_durations)}')
        print(f'POOLED DIAGNOSTIC | IBI: SNr={len(pooled_snr_intervals)}, Control={len(pooled_ctrl_intervals)}')
        print(f'POOLED DIAGNOSTIC | Acceleration: SNr={len(pooled_snr_accel)}, Control={len(pooled_ctrl_accel)}')

        with PdfPages(pooled_pdf_path) as cpdf:
            fig_cs, ax_cs = plt.subplots(figsize=(10, 6))
            draw_two_group_hist(
                ax_cs,
                pooled_snr_speeds, pooled_ctrl_speeds, np.arange(10, 160, 5),
                'Bout Speed (revs/min)',
                'Bout Speed',
                stat_func=np.mean, stat_name='mean', stat_decimals=1,
                count_label='bouts', pooled=True
            )
            fig_cs.suptitle(f'Bout Speed - SNr-DTA vs Ctrl (Days {DAY_MIN}-{DAY_MAX})',
                            fontsize=13, fontweight='bold')
            fig_cs.tight_layout(rect=[0, 0, 1, 0.96])
            cpdf.savefig(fig_cs, bbox_inches='tight')
            plt.close(fig_cs)

            fig_cd, ax_cd = plt.subplots(figsize=(10, 6))
            draw_two_group_hist(
                ax_cd,
                pooled_snr_durations, pooled_ctrl_durations, np.arange(1, 51, 1),
                'Bout Duration (minutes)',
                'Bout Duration',
                stat_func=np.mean, stat_name='mean', stat_decimals=1,
                xlim=(1, 50), count_label='bouts', pooled=True
            )
            fig_cd.suptitle(f'Bout Duration - SNr-DTA vs Ctrl (Days {DAY_MIN}-{DAY_MAX})',
                            fontsize=13, fontweight='bold')
            fig_cd.tight_layout(rect=[0, 0, 1, 0.96])
            cpdf.savefig(fig_cd, bbox_inches='tight')
            plt.close(fig_cd)

            fig_ci, ax_ci = plt.subplots(figsize=(10, 6))
            draw_two_group_hist(
                ax_ci,
                pooled_snr_intervals, pooled_ctrl_intervals, ibi_bins,
                'Inter-Bout Interval (minutes)',
                'Inter-Bout Interval',
                stat_func=np.median, stat_name='median', stat_decimals=1,
                use_log_x=True, count_label='intervals', pooled=True
            )
            fig_ci.suptitle(f'Inter-Bout Interval - SNr-DTA vs Ctrl (Days {DAY_MIN}-{DAY_MAX})',
                            fontsize=13, fontweight='bold')
            fig_ci.tight_layout(rect=[0, 0, 1, 0.96])
            cpdf.savefig(fig_ci, bbox_inches='tight')
            plt.close(fig_ci)

            if acc_plot:
                fig_ca, ax_ca = plt.subplots(figsize=(10, 6))
                tt = 'Within-Bout Acceleration'
                if acc_nozero:
                    tt = 'Non-zero Within-Bout Acceleration'
                draw_two_group_hist(
                    ax_ca,
                    pooled_snr_accel, pooled_ctrl_accel, np.arange(-100, 102, 2),
                    'Δ Speed between consecutive active bins (revs/min)',
                    tt,
                    stat_func=np.mean, stat_name='mean', stat_decimals=2,
                    count_label='ΔSpeed', pooled=True,
                    accel_split_legend=True
                )
                ax_ca.axvline(0, color='black', linewidth=1.0, linestyle='-', alpha=0.4)
                fig_ca.suptitle(f'{tt} - SNr-DTA vs Ctrl (Days {DAY_MIN}-{DAY_MAX})',
                                fontsize=13, fontweight='bold')
                fig_ca.tight_layout(rect=[0, 0, 1, 0.96])
                cpdf.savefig(fig_ca, bbox_inches='tight')
                plt.close(fig_ca)

        # ------------------------------------------------------------------
        # Additional pooled time-zone histograms
        #   One grouped PDF with 3 metrics x 3 time zones:
        #   1) Bout speed
        #   2) Bout duration
        #   3) Inter-bout / inactivity interval
        # ------------------------------------------------------------------
        time_zone_specs = [
            ('Dark_18-24', '18:00-24:00'),
            ('Dark_00-06', '00:00-06:00'),
            ('Light_06-18', '06:00-18:00'),
        ]

        def _time_zone_from_timestamp(ts):
            hour_float = ts.hour + ts.minute / 60.0 + ts.second / 3600.0
            if 18 <= hour_float < 24:
                return 'Dark_18-24'
            if 0 <= hour_float < 6:
                return 'Dark_00-06'
            return 'Light_06-18'

        def _collect_mouse_bout_metrics_by_zone(mouse_df, rev_col, threshold=10):
            """
            Returns plotted bout metrics keyed by time-zone name:
              - bout speed: each bout assigned by bout start time
              - bout duration: each bout assigned by bout start time
              - IBI / interval: exclusive gap assigned by the end time of the previous bout
            """
            speed_by_zone = {name: [] for name, _ in time_zone_specs}
            duration_by_zone = {name: [] for name, _ in time_zone_specs}
            ibi_by_zone = {name: [] for name, _ in time_zone_specs}

            for _, day_df in mouse_df.groupby('DateIndex'):
                day_df = day_df.sort_values('Bin').copy()
                if rev_col not in day_df.columns:
                    continue

                raw = pd.to_numeric(day_df[rev_col], errors='coerce').fillna(0.0)
                revs = raw.where(raw >= threshold, 0.0)
                active = revs > 0
                if not active.any():
                    continue

                run_id = (active != active.shift(fill_value=False)).cumsum()
                active_runs = []

                for _, group in revs.groupby(run_id):
                    if not active.loc[group.index].iloc[0]:
                        continue
                    if truncate_flag & len(group) >= 3:
                        group = group[1:-1]
                    if len(group) == 0:
                        continue
                    bout_start_idx = group.index[0]
                    bout_start_time = day_df.loc[bout_start_idx, 'Bin']
                    zone_name = _time_zone_from_timestamp(bout_start_time)
                    speed_by_zone[zone_name].append(float(group.mean()))
                    duration_by_zone[zone_name].append(float(len(group)))
                    active_runs.append(group.index)

                for i in range(len(active_runs) - 1):
                    current_end_idx = active_runs[i][-1]
                    next_start_idx = active_runs[i + 1][0]
                    current_end_time = day_df.loc[current_end_idx, 'Bin']
                    next_start_time = day_df.loc[next_start_idx, 'Bin']
                    interval_min = (next_start_time - current_end_time).total_seconds() / 60.0 - 1.0
                    if interval_min >= 1:
                        gap_zone = _time_zone_from_timestamp(current_end_time)
                        ibi_by_zone[gap_zone].append(float(interval_min))

            return speed_by_zone, duration_by_zone, ibi_by_zone

        tz_speed_data = {name: {'SNr-DTA': [], 'Control': []} for name, _ in time_zone_specs}
        tz_duration_data = {name: {'SNr-DTA': [], 'Control': []} for name, _ in time_zone_specs}
        tz_ibi_data = {name: {'SNr-DTA': [], 'Control': []} for name, _ in time_zone_specs}
        tz_bout_count_rows = []

        for cohort_num in cohort_numbers:
            cohort_info = cohort_data_dict[cohort_num]
            df_zone = cohort_info['df']
            for group_name, mouse_list in [('SNr-DTA', cohort_info['snr_mice']),
                                           ('Control', cohort_info['ctrl_mice'])]:
                for mid in mouse_list:
                    rev_col = f'1 8 {mid} rev'
                    if rev_col not in df_zone.columns:
                        continue
                    mouse_df = df_zone[['Bin', 'DateIndex', rev_col]].copy()
                    spd_by_zone, dur_by_zone, ibi_by_zone = _collect_mouse_bout_metrics_by_zone(
                        mouse_df, rev_col, threshold=threshold
                    )
                    labels = cohort_info.get('labels', [])
                    mouse_label = labels[int(mid) - 1] if int(mid) - 1 < len(labels) else f'Mouse {mid}'
                    mouse_id_short = mouse_label[0:4]
                    count_row = {
                        'Cohort': cohort_num,
                        'MouseID': int(mid),
                        'ID': mouse_id_short,
                        'MouseLabel': mouse_label,
                        'Group': group_name,
                    }
                    for zone_name, _ in time_zone_specs:
                        tz_speed_data[zone_name][group_name].extend(spd_by_zone[zone_name])
                        tz_duration_data[zone_name][group_name].extend(dur_by_zone[zone_name])
                        tz_ibi_data[zone_name][group_name].extend(ibi_by_zone[zone_name])
                        count_row[f'{zone_name}_bout_count'] = int(len(dur_by_zone[zone_name]))
                    tz_bout_count_rows.append(count_row)

        time_zone_hist_pdf_path = './BoutStatistics_TimeZoneHistograms_BoutSpeed_BoutDuration_IBI.pdf'

        all_tz_ibi = []
        for zone_name, _ in time_zone_specs:
            all_tz_ibi.extend(tz_ibi_data[zone_name]['SNr-DTA'])
            all_tz_ibi.extend(tz_ibi_data[zone_name]['Control'])
        max_tz_ibi = int(np.nanmax(all_tz_ibi)) if all_tz_ibi else 60
        if max_tz_ibi <= ibi_integer_tail_start:
            tz_ibi_bins = np.arange(0.5, max_tz_ibi + 1.5, 1)
        else:
            tz_integer_edges = np.arange(0.5, ibi_integer_tail_start + 1.5, 1)
            tz_tail_edges = np.logspace(np.log10(ibi_integer_tail_start + 0.5),
                                        np.log10(max_tz_ibi + 0.5), 24)
            tz_ibi_bins = np.unique(np.concatenate([tz_integer_edges, tz_tail_edges[1:]]))

        ibi_bins_old = ibi_bins
        ibi_xticks_old = ibi_xticks
        ibi_bins = tz_ibi_bins
        ibi_xticks = [x for x in [1, 2, 3, 4, 5, 10, 20, 50, 100, 500, 1000]
                      if x <= max_tz_ibi + 1]

        with PdfPages(time_zone_hist_pdf_path) as tzpdf:
            # Bout speed pages
            for zone_name, zone_window in time_zone_specs:
                fig_z, ax_z = plt.subplots(figsize=(10, 6))
                draw_two_group_hist(
                    ax_z,
                    tz_speed_data[zone_name]['SNr-DTA'],
                    tz_speed_data[zone_name]['Control'],
                    np.arange(10, 160, 5),
                    'Bout speed (revs/min)',
                    f'Bout speed | {zone_name}',
                    stat_func=np.mean, stat_name='mean', stat_decimals=1,
                    count_label='bouts', pooled=True
                )
                fig_z.suptitle(f'Bout Speed - {zone_name} ({zone_window})',
                               fontsize=13, fontweight='bold')
                fig_z.tight_layout(rect=[0, 0, 1, 0.96])
                tzpdf.savefig(fig_z, bbox_inches='tight')
                plt.close(fig_z)

            # Bout duration pages
            for zone_name, zone_window in time_zone_specs:
                fig_z, ax_z = plt.subplots(figsize=(10, 6))
                draw_two_group_hist(
                    ax_z,
                    tz_duration_data[zone_name]['SNr-DTA'],
                    tz_duration_data[zone_name]['Control'],
                    np.arange(0.5, 61.5, 1),
                    'Bout duration (minutes)',
                    f'Bout duration | {zone_name}',
                    stat_func=np.median, stat_name='median', stat_decimals=1,
                    count_label='bouts', pooled=True
                )
                fig_z.suptitle(f'Bout Duration - {zone_name} ({zone_window})',
                               fontsize=13, fontweight='bold')
                fig_z.tight_layout(rect=[0, 0, 1, 0.96])
                tzpdf.savefig(fig_z, bbox_inches='tight')
                plt.close(fig_z)

            # Inter-bout / inactivity interval pages
            for zone_name, zone_window in time_zone_specs:
                fig_z, ax_z = plt.subplots(figsize=(10, 6))
                draw_two_group_hist(
                    ax_z,
                    tz_ibi_data[zone_name]['SNr-DTA'],
                    tz_ibi_data[zone_name]['Control'],
                    ibi_bins,
                    'Inter-bout interval (minutes)',
                    f'Inter-bout interval | {zone_name}',
                    stat_func=np.median, stat_name='median', stat_decimals=1,
                    use_log_x=True, count_label='intervals', pooled=True
                )
                fig_z.suptitle(f'Inter-Bout Interval - {zone_name} ({zone_window})',
                               fontsize=13, fontweight='bold')
                fig_z.tight_layout(rect=[0, 0, 1, 0.96])
                tzpdf.savefig(fig_z, bbox_inches='tight')
                plt.close(fig_z)

        ibi_bins = ibi_bins_old
        ibi_xticks = ibi_xticks_old
        print(f'Saved grouped time-zone histogram PDF: {time_zone_hist_pdf_path}')

        # ------------------------------------------------------------------
        # Bout source composition by phase for each mouse
        # ------------------------------------------------------------------
        if tz_bout_count_rows:
            tz_bout_count_df = pd.DataFrame(tz_bout_count_rows)
            phase_plot_pdf_path = './BoutStatistics_BoutCountComposition_ByPhase.pdf'

            # Ask which phases should be included in the bout-count composition plot.
            # The CSV still contains all available phase-count columns; this only controls the PDF figure.
            all_phase_order = ['Light_06-18', 'Dark_18-24', 'Dark_00-06']
            phase_selection = {'phases': None}
            try:
                phase_dialog = tk.Toplevel(self.root)
                phase_dialog.title('Select phases for bout-count composition')
                phase_dialog.transient(self.root)
                phase_dialog.grab_set()

                tk.Label(
                    phase_dialog,
                    text='Select phases to include in BoutStatistics_BoutCountComposition_ByPhase:',
                    font=('Arial', 11, 'bold'),
                    padx=10, pady=8
                ).pack(anchor='w')

                phase_vars = {}
                for phase_name in all_phase_order:
                    var = tk.BooleanVar(value=True)
                    phase_vars[phase_name] = var
                    tk.Checkbutton(
                        phase_dialog,
                        text=phase_name,
                        variable=var,
                        padx=15, pady=3
                    ).pack(anchor='w')

                def _select_all_phases():
                    for v in phase_vars.values():
                        v.set(True)

                def _clear_all_phases():
                    for v in phase_vars.values():
                        v.set(False)

                def _ok_phases():
                    phase_selection['phases'] = [
                        p for p in all_phase_order if phase_vars[p].get()
                    ]
                    phase_dialog.destroy()

                def _cancel_phases():
                    phase_selection['phases'] = all_phase_order
                    phase_dialog.destroy()

                btn_frame = tk.Frame(phase_dialog, padx=10, pady=10)
                btn_frame.pack(fill='x')
                tk.Button(btn_frame, text='Select all', command=_select_all_phases).pack(side='left', padx=4)
                tk.Button(btn_frame, text='Clear', command=_clear_all_phases).pack(side='left', padx=4)
                tk.Button(btn_frame, text='OK', command=_ok_phases).pack(side='right', padx=4)
                tk.Button(btn_frame, text='Cancel', command=_cancel_phases).pack(side='right', padx=4)

                phase_dialog.protocol('WM_DELETE_WINDOW', _cancel_phases)
                self.root.wait_window(phase_dialog)
                phase_order = phase_selection['phases'] if phase_selection['phases'] is not None else all_phase_order
            except Exception as e:
                print(f'Phase-selection popup failed; using all phases. Error: {e}')
                phase_order = all_phase_order

            if not phase_order:
                print('No phases selected for BoutStatistics_BoutCountComposition_ByPhase.pdf; skipping phase-composition PDF.')
                phase_order = []

            phase_colors = {
                'Light_06-18': (0.95, 0.72, 0.20),
                'Dark_18-24': (0.25, 0.25, 0.35),
                'Dark_00-06': (0.45, 0.45, 0.60),
            }

            plot_df = tz_bout_count_df.copy()
            group_rank = {'SNr-DTA': 0, 'Control': 1}
            plot_df['_group_rank'] = plot_df['Group'].map(group_rank).fillna(9)
            plot_df = plot_df.sort_values(['_group_rank', 'Cohort', 'ID']).reset_index(drop=True)

            x = np.arange(len(plot_df))
            n_selected_phases = max(1, len(phase_order))
            width = min(0.24, 0.72 / n_selected_phases)
            phase_offsets = np.linspace(
                -width * (n_selected_phases - 1) / 2,
                width * (n_selected_phases - 1) / 2,
                n_selected_phases
            )

            fig_phase, ax_phase = plt.subplots(figsize=(max(12, len(plot_df) * 0.72), 6.5))
            for offset, phase_name in zip(phase_offsets, phase_order):
                col = f'{phase_name}_bout_count'
                vals = plot_df[col].to_numpy(dtype=float) if col in plot_df.columns else np.zeros(len(plot_df))
                ax_phase.bar(
                    x + offset,
                    vals,
                    width=width,
                    label=phase_name,
                    color=phase_colors.get(phase_name, (0.5, 0.5, 0.5)),
                    edgecolor='black',
                    linewidth=0.7,
                    alpha=0.88
                )

            xtick_labels = [
                f"{row['ID']}\n{row['Group']}"
                for _, row in plot_df.iterrows()
            ]
            ax_phase.set_xticks(x)
            ax_phase.set_xticklabels(xtick_labels, rotation=45, ha='right', fontsize=8)
            if use_cohort2_special_colors:
                for tick_label, (_, row) in zip(ax_phase.get_xticklabels(), plot_df.iterrows()):
                    c = _cohort2_special_color_for_label(row.get('MouseLabel', row.get('ID', '')))
                    if c is not None:
                        tick_label.set_color(c)
                        tick_label.set_fontweight('bold')
            ax_phase.set_ylabel('Detected bout count', fontsize=12, fontweight='bold')
            ax_phase.set_xlabel('Mouse', fontsize=12, fontweight='bold')
            selected_phase_label = ', '.join(phase_order) if phase_order else 'No phases selected'
            ax_phase.set_title(
                f'Composition of Detected Bouts by Phase (Days {DAY_MIN}-{DAY_MAX})\n{selected_phase_label}',
                fontsize=14, fontweight='bold'
            )
            ax_phase.grid(True, axis='y', alpha=0.3, linestyle='--')
            ax_phase.legend(frameon=False, fontsize=10, loc='best')
            ax_phase.spines['top'].set_visible(False)
            ax_phase.spines['right'].set_visible(False)

            # Put a light vertical separator between SNr-DTA and Control if both are present.
            group_values = plot_df['Group'].tolist()
            if 'SNr-DTA' in group_values and 'Control' in group_values:
                last_snr_idx = max(i for i, g in enumerate(group_values) if g == 'SNr-DTA')
                ax_phase.axvline(last_snr_idx + 0.5, color='gray', linestyle='--', linewidth=1.0, alpha=0.55)

            fig_phase.tight_layout()
            fig_phase.savefig(phase_plot_pdf_path, bbox_inches='tight')
            plt.close(fig_phase)

            print(f'Saved bout-count phase composition PDF: {phase_plot_pdf_path}')
            print('Merged bout-count phase composition columns into the general per-mouse CSV.')
        else:
            tz_bout_count_df = pd.DataFrame()
            print('Warning: No bout-count phase composition rows generated.')

        # ------------------------------------------------------------------
        # Final merged per-mouse CSV
        # ------------------------------------------------------------------
        if isinstance(merged_per_mouse_df, pd.DataFrame) and not merged_per_mouse_df.empty:
            if isinstance(tz_bout_count_df, pd.DataFrame) and not tz_bout_count_df.empty:
                phase_cols = [
                    c for c in tz_bout_count_df.columns
                    if c not in merge_keys + ['MouseID', 'MouseLabel']
                ]
                merged_per_mouse_df = merged_per_mouse_df.merge(
                    tz_bout_count_df[merge_keys + phase_cols].drop_duplicates(subset=merge_keys),
                    on=merge_keys,
                    how='left'
                )
            merged_per_mouse_df.to_csv(per_mouse_metric_csv_path, index=False)
            print(f'Saved final merged per-mouse statistics CSV: {per_mouse_metric_csv_path}')

        print(f'Saved TRULY pooled single-panel PDF: {pooled_pdf_path}')

        messagebox.showinfo(
            'Complete',
            f"Generated multi-cohort bout statistics summary\n"
            f"Cohorts: {', '.join([str(c) for c in cohort_numbers])}\n"
            f"Days: {DAY_MIN}-{DAY_MAX}\n"
            f"PDF (4 figures, 2×2): {pdf_path}\n"
            f"PDF (4 figures, pooled): {pooled_pdf_path}\n"
            f"PDF (time-zone histograms: speed, duration): {time_zone_hist_pdf_path}\n"
            f"CSV (light/dark + phase composition merged): {csv_path}\n"
            f"CSV (per-mouse bout metrics): {per_mouse_metric_csv_path}"
        )

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
                    'TotalBoutTime_minutes': total_bout_time,
                    'MostFrequentBoutDuration_minutes': most_frequent_duration,
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
        ax.set_ylabel("Cumulative distance across days (km)", fontsize=12, fontweight='bold')
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




    def plot_functional_trajectory_umap_multi_cohort(self):
        """
        Mouse-day functional trajectory UMAP, version 1.

        Each sample = one mouse on one recruited day.
        Each sample is represented as a time-by-feature matrix:
            selected time windows x 5 bout/activity features
        The matrix is flattened, scaled, reduced by PCA, then embedded by UMAP.

        User inputs:
        1. DayIndex range/list to recruit.
        2. One or more time zones to include.
        3. Temporal resolution (5, 10, or 20 min).
        """
        LIGHT_ON_HOUR = 6
        BOUT_THRESHOLD_REVS_PER_MIN = 10

        try:
            import umap
        except Exception:
            messagebox.showerror(
                "UMAP unavailable",
                "The 'umap-learn' package is required for this analysis.\n"
                "Please install it first: pip install umap-learn"
            )
            return

        try:
            from sklearn.preprocessing import StandardScaler
            from sklearn.decomposition import PCA
        except Exception as e:
            messagebox.showerror("Missing dependency", f"Could not import scikit-learn:\n{e}")
            return

        def _parse_day_selection(day_text):
            """
            Parse strings like:
                1-28
                8-21
                1,2,3,8-21
            """
            if day_text is None:
                return None
            day_text = str(day_text).strip().replace(" ", "")
            if not day_text:
                return None

            days = set()
            for token in day_text.split(","):
                if not token:
                    continue
                if "-" in token:
                    a, b = token.split("-", 1)
                    a = int(a)
                    b = int(b)
                    if b < a:
                        a, b = b, a
                    for d in range(a, b + 1):
                        days.add(d)
                else:
                    days.add(int(token))
            return sorted(days)

        def _ask_time_zones():
            """
            Ask user to choose one or more of the four time zones.
            Return list of zone dicts in chronological order.
            """
            zone_defs = [
                {"key": "Dark1", "label": "Dark phase 1: 18:00–24:00", "start": 18.0, "end": 24.0},
                {"key": "Dark2", "label": "Dark phase 2: 00:00–06:00", "start": 0.0, "end": 6.0},
                {"key": "Light1", "label": "Light phase 1: 06:00–12:00", "start": 6.0, "end": 12.0},
                {"key": "Light2", "label": "Light phase 2: 12:00–18:00", "start": 12.0, "end": 18.0},
            ]

            dialog = tk.Toplevel(self.root)
            dialog.title("Select time zones for mouse-day UMAP")
            dialog.transient(self.root)
            dialog.grab_set()

            tk.Label(
                dialog,
                text="Select one or more time zones to include in the mouse-day feature matrix:",
                font=("Arial", 11, "bold"),
                padx=10, pady=8
            ).pack(anchor="w")

            vars_by_key = {}
            for z in zone_defs:
                var = tk.BooleanVar(value=True)
                vars_by_key[z["key"]] = var
                tk.Checkbutton(dialog, text=z["label"], variable=var, padx=15, pady=3).pack(anchor="w")

            selected = {"zones": None}

            def _select_all():
                for v in vars_by_key.values():
                    v.set(True)

            def _clear_all():
                for v in vars_by_key.values():
                    v.set(False)

            def _ok():
                chosen = [z for z in zone_defs if vars_by_key[z["key"]].get()]
                selected["zones"] = chosen
                dialog.destroy()

            def _cancel():
                selected["zones"] = None
                dialog.destroy()

            btn_frame = tk.Frame(dialog, padx=10, pady=10)
            btn_frame.pack(fill="x")
            tk.Button(btn_frame, text="Select all", command=_select_all).pack(side="left", padx=4)
            tk.Button(btn_frame, text="Clear", command=_clear_all).pack(side="left", padx=4)
            tk.Button(btn_frame, text="OK", command=_ok).pack(side="right", padx=4)
            tk.Button(btn_frame, text="Cancel", command=_cancel).pack(side="right", padx=4)

            dialog.protocol("WM_DELETE_WINDOW", _cancel)
            self.root.wait_window(dialog)
            return selected["zones"]

        def _cohort_num_from_path(file_path):
            base = os.path.splitext(os.path.basename(file_path))[0]
            patterns = [r'(?i)cohort[_\-\s]*([1-4])', r'(?i)c[_\-\s]*([1-4])', r'(?i)p\d+c([1-4])']
            for pat in patterns:
                m = re.search(pat, base)
                if m:
                    return int(m.group(1))
            m = re.search(r'([1-4])$', base)
            if m:
                return int(m.group(1))
            raise ValueError(f"Could not infer cohort number from filename: {os.path.basename(file_path)}")

        def _mouse_labels_for_cohort(cohort_num):
            if cohort_num == 1:
                return ["SC01(Control)", "LM45(SNr-DTA)", "SC02(GPi-DTA)"]
            if cohort_num == 2:
                return ["SC04(SNr-DTA)", "SC05(SNr-DTA)", "SC06(SNr-DTA)", "SC07(Control)", "SC08(Control)"]
            if cohort_num == 3:
                return ["SC09(SNr-DTA)", "SC10(SNr-DTA)", "SC11(SNr-DTA)", "SC12(SNr-DTA)", "SC13(Control)", "SC14(Control)", "SC15(Control)"]
            if cohort_num == 4:
                return ["SC29(SNr-DTA)", "SC30(SNr-DTA)", "SC31(SNr-DTA)", "SC32(SNr-DTA)", "SC33(Control)", "SC34(Control)", "SC35(Control)"]
            return []

        def _included_mice(mouse_ids, cohort_num):
            mouse_ids = list(mouse_ids)
            if cohort_num == 1:
                for i in [3, 5, 6, 7]:
                    if i in mouse_ids:
                        mouse_ids.remove(i)
            if cohort_num == 2:
                # Cohort 2: SC04/SC05/SC06 are excluded with SC07.
                # SC07 (mouse ID 4) remains excluded by default.
                for i in [1, 2, 3, 4]:
                    if i in mouse_ids:
                        mouse_ids.remove(i)
            if cohort_num == 4:
                for i in [7]:
                    if i in mouse_ids:
                        mouse_ids.remove(i)
            return mouse_ids

        def _group_from_label(mouse_label):
            if 'SNr' in mouse_label or 'DTA' in mouse_label:
                return 'SNr-DTA'
            if 'Control' in mouse_label:
                return 'Control'
            if 'GPi' in mouse_label:
                return 'GPi-DTA'
            return 'Unknown'

        def _read_activity_file(file_path):
            if file_path.endswith('.xls') or file_path.endswith('.xlsx'):
                try:
                    return pd.read_csv(file_path, skiprows=10, sep='\t')
                except Exception:
                    return pd.read_csv(file_path, skiprows=10)
            if file_path.endswith('.csv'):
                return pd.read_csv(file_path, skiprows=10)
            raise ValueError(f"Unsupported file format: {file_path}")

        def _make_gradient_colors(base_color, n):
            gradients = []
            for i in range(n):
                ratio = 0.1 + (0.55 * i / max(n - 1, 1))
                color = tuple(base_color[j] * (1 - ratio) + ratio for j in range(3))
                gradients.append(color)
            return gradients

        def _extract_sc_number(label):
            label = str(label)
            if 'LM45' in label:
                return 2.5
            match = re.search(r'SC(\d+)', label)
            return int(match.group(1)) if match else 999

        def _cohort2_special_color_for_label(label):
            if not use_cohort2_special_colors:
                return None
            label_upper = str(label).upper()
            if 'SC04' in label_upper:
                return (0.95, 0.48, 0.05)
            if 'SC05' in label_upper:
                return (0.90, 0.35, 0.02)
            if 'SC06' in label_upper:
                return (0.75, 0.22, 0.00)
            if 'SC08' in label_upper:
                return '#FFD700'
            return None

        def _hour_in_zone(hour, zone):
            start = zone["start"]
            end = zone["end"]
            if start <= end:
                return (hour >= start) and (hour < end)
            return (hour >= start) or (hour < end)

        def _selected_window_indices(selected_zones):
            indices = []
            labels = []
            for w in range(WINDOWS_PER_DAY):
                start_min = w * WINDOW_MINUTES
                start_hour = start_min / 60.0
                use_window = any(_hour_in_zone(start_hour, z) for z in selected_zones)
                if use_window:
                    indices.append(w)
                    hh = int(start_min // 60)
                    mm = int(start_min % 60)
                    labels.append(f"{hh:02d}:{mm:02d}")
            return indices, labels

        def _ask_window_minutes():
            """
            Ask for temporal resolution in minutes.
            Recommended values: 5, 10, or 20.
            """
            val = simpledialog.askinteger(
                "Temporal resolution for mouse-day UMAP",
                "Enter temporal resolution in minutes.\nRecommended: 5, 10, or 20",
                initialvalue=10,
                parent=self.root,
                minvalue=1
            )
            if val is None:
                return None
            if val not in [5, 10, 20] and (60 % val != 0):
                messagebox.showerror(
                    "Invalid temporal resolution",
                    "Please choose a value that divides 60 evenly.\nRecommended values are 5, 10, or 20."
                )
                return None
            return int(val)

        def _compute_bout_features_in_window(window_df, rev_col, window_start_ts, window_end_ts):
            """
            Return the 5-feature vector for one window.

            Features:
            1. log1p(total revolutions)
            2. active minutes
            3. log1p(bout count)
            4. longest bout duration
            5. mean bout speed
            """
            if window_df.empty:
                return np.zeros(5, dtype=float)

            work = window_df.sort_values('Bin').copy()
            revs = pd.to_numeric(work[rev_col], errors='coerce').fillna(0.0)
            active = revs >= BOUT_THRESHOLD_REVS_PER_MIN

            total_revs = float(revs.sum())
            active_minutes = float(active.sum())

            bout_durations = []
            bout_speeds = []
            if active.any():
                run_id = (active != active.shift(fill_value=False)).cumsum()
                for _, bout_revs in revs.groupby(run_id):
                    if not active.loc[bout_revs.index].iloc[0]:
                        continue
                    bout_durations.append(float(len(bout_revs)))
                    bout_speeds.append(float(bout_revs.mean()))

            bout_count = len(bout_durations)
            longest_bout = float(np.max(bout_durations)) if bout_durations else 0.0
            mean_speed = float(np.mean(bout_speeds)) if bout_speeds else 0.0

            return np.array([
                np.log1p(total_revs),
                active_minutes,
                np.log1p(bout_count),
                longest_bout,
                mean_speed,
            ], dtype=float)

        def _compute_mouse_day_matrix(day_df, rev_col, selected_indices):
            """
            Build selected time windows x 5 matrix for one mouse-day.
            """
            day_df = day_df.sort_values('Bin').copy()
            if day_df.empty:
                return None

            real_day_start = pd.Timestamp(day_df['Bin'].dt.normalize().min())
            vectors = []
            for w in selected_indices:
                window_start = real_day_start + pd.Timedelta(minutes=w * WINDOW_MINUTES)
                window_end = window_start + pd.Timedelta(minutes=WINDOW_MINUTES)
                win_df = day_df[(day_df['Bin'] >= window_start) & (day_df['Bin'] < window_end)]
                vectors.append(_compute_bout_features_in_window(win_df, rev_col, window_start, window_end))
            if not vectors:
                return None
            return np.vstack(vectors)

        day_text = simpledialog.askstring(
            "Days for mouse-day UMAP",
            "Enter DayIndex values to recruit.\nExamples: 1-28, 8-21, or 1,2,3,8-21",
            initialvalue="1-28",
            parent=self.root
        )
        recruited_days = _parse_day_selection(day_text)
        if not recruited_days:
            messagebox.showinfo("No days selected", "No valid DayIndex values were selected.")
            return

        selected_zones = _ask_time_zones()
        if not selected_zones:
            messagebox.showinfo("No time zones selected", "No time zones were selected.")
            return

        WINDOW_MINUTES = _ask_window_minutes()
        if WINDOW_MINUTES is None:
            return
        WINDOWS_PER_DAY = int(24 * 60 / WINDOW_MINUTES)

        selected_indices, selected_window_labels = _selected_window_indices(selected_zones)
        if not selected_indices:
            messagebox.showinfo("No windows selected", f"The selected time zones produced no {WINDOW_MINUTES}-min windows.")
            return

        file_paths = filedialog.askopenfilenames(
            title="Select cohort files for mouse-day functional trajectory UMAP",
            filetypes=[("Data Files", "*.csv *.xls *.xlsx")]
        )
        if not file_paths:
            messagebox.showinfo("No Files", "No files selected.")
            return

        remove_lm45 = self._ask_remove_lm45_from_mouse_pool("mouse-day functional trajectory UMAP")

        # Cohort 2 mouse IDs 1-4 are excluded by rule; do not ask to include SC04/SC05/SC06.
        include_sc04 = False
        include_sc05 = False
        include_sc06 = False

        try:
            use_cohort2_special_colors = messagebox.askyesno(
                "Special colors for cohort 2?",
                "If cohort 2 mice SC04, SC05, SC06, or SC08 are included, use special colors?\n\n"
                "Yes = SC04/SC05/SC06 use orange gradients, SC08 uses gold-yellow\n"
                "No = use regular group colors"
            )
        except Exception:
            use_cohort2_special_colors = False

        feature_rows = []
        meta_rows = []

        for file_path in file_paths:
            try:
                cohort_num = _cohort_num_from_path(file_path)
                mouse_labels = _mouse_labels_for_cohort(cohort_num)
                df = _read_activity_file(file_path)
                df = df.dropna(how='all').dropna(axis=1, how='all')
                df.columns = [col.strip() for col in df.columns]

                if 'Bin' not in df.columns:
                    print(f"Warning: missing Bin column in {file_path}; skipped.")
                    continue

                df['Bin'] = pd.to_datetime(df['Bin'], format='mixed', errors='coerce')
                df = df.dropna(subset=['Bin']).copy()
                if df.empty:
                    continue

                # Align cohort 3: raw day 0 should map to experimental day 8.
                reference_date = df['Bin'].dt.normalize().min().date()
                if cohort_num == 3:
                    reference_date = reference_date - timedelta(days=8)
                    print(f"Cohort 3 date alignment: raw first date {df['Bin'].dt.normalize().min().date()} -> Day 8 anchor {reference_date}")
                ref_ts = pd.Timestamp(reference_date)
                df['DateIndex'] = (df['Bin'].dt.normalize() - ref_ts).dt.days
                df = df[df['DateIndex'].isin(recruited_days)].copy()
                if df.empty:
                    print(f"No records for selected days {recruited_days} in cohort {cohort_num}; skipped.")
                    continue

                mouse_ids = sorted(set(col.split()[2] for col in df.columns if col.startswith('1 8')))
                mouse_ids = [int(m) for m in mouse_ids if str(m).isdigit()]
                self._print_mouse_candidates('mouse-day UMAP', cohort_num, mouse_ids, mouse_labels, stage='raw from file')
                mouse_ids = _included_mice(mouse_ids, cohort_num)
                self._print_mouse_candidates('mouse-day UMAP', cohort_num, mouse_ids, mouse_labels, stage='after cohort exclusions')
                mouse_ids = self._apply_lm45_mouse_filter(
                    mouse_ids, mouse_labels, remove_lm45,
                    cohort_num=cohort_num, context='mouse-day UMAP'
                )
                self._print_mouse_candidates('mouse-day UMAP', cohort_num, mouse_ids, mouse_labels, stage='final after LM45 decision')

                for mid in mouse_ids:
                    rev_col = f'1 8 {mid} rev'
                    if rev_col not in df.columns:
                        continue

                    label = mouse_labels[int(mid) - 1] if int(mid) - 1 < len(mouse_labels) else f'Mouse {mid}'
                    group = _group_from_label(label)
                    if group not in ['SNr-DTA', 'Control']:
                        continue

                    mouse_df = df[['Bin', 'DateIndex', rev_col]].copy()
                    for day in recruited_days:
                        day_df = mouse_df[mouse_df['DateIndex'] == day].copy()
                        if day_df.empty:
                            continue
                        matrix = _compute_mouse_day_matrix(day_df, rev_col, selected_indices)
                        if matrix is None:
                            continue
                        feature_rows.append(matrix.flatten())
                        real_date = pd.Timestamp(day_df['Bin'].dt.normalize().min()).date().isoformat()
                        # Summary stats for audit.
                        total_revs = float(pd.to_numeric(day_df[rev_col], errors='coerce').fillna(0).sum())
                        active_minutes = int((pd.to_numeric(day_df[rev_col], errors='coerce').fillna(0) >= BOUT_THRESHOLD_REVS_PER_MIN).sum())
                        meta_rows.append({
                            'Cohort': cohort_num,
                            'MouseID': int(mid),
                            'MouseLabel': label,
                            'Group': group,
                            'Day': int(day),
                            'RealDate': real_date,
                            'SelectedWindows_n': len(selected_indices),
                            'TotalRevs_selectedDay': total_revs,
                            'ActiveMinutes_selectedDay': active_minutes,
                        })

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        if len(feature_rows) < 4:
            messagebox.showwarning(
                "Too little data",
                "Need at least 4 mouse-day observations to compute a meaningful UMAP embedding."
            )
            return

        X = np.vstack(feature_rows).astype(float)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # PCA before UMAP stabilizes sparse high-dimensional matrices.
        n_pca = int(min(30, X_scaled.shape[0] - 1, X_scaled.shape[1]))
        if n_pca >= 2:
            pca = PCA(n_components=n_pca, random_state=42)
            X_for_umap = pca.fit_transform(X_scaled)
            pca_var = float(np.sum(pca.explained_variance_ratio_))
        else:
            X_for_umap = X_scaled
            pca_var = np.nan

        n_neighbors = max(2, min(15, X_for_umap.shape[0] - 1))
        reducer = umap.UMAP(
            n_neighbors=n_neighbors,
            min_dist=0.25,
            n_components=2,
            metric='cosine',
            random_state=42,
        )
        emb = reducer.fit_transform(X_for_umap)

        plot_df = pd.DataFrame(meta_rows)

        # Interpretable mouse-day feature summaries from the selected time windows.
        # The flattened matrix has 5 features per window:
        #   0 log1p(total revolutions), 1 active minutes, 2 log1p(bout count),
        #   3 longest bout duration, 4 mean bout speed.
        n_selected_windows = len(selected_indices)
        matrix_summary_rows = []
        for row in X:
            mat = row.reshape(n_selected_windows, 5)
            total_revs_selected = float(np.sum(np.expm1(mat[:, 0])))
            active_minutes_selected = float(np.sum(mat[:, 1]))
            bout_count_selected = float(np.sum(np.expm1(mat[:, 2])))
            longest_bout_selected = float(np.nanmax(mat[:, 3])) if mat.shape[0] else np.nan
            speed_vals = mat[:, 4]
            speed_vals = speed_vals[np.isfinite(speed_vals) & (speed_vals > 0)]
            mean_bout_speed_selected = float(np.nanmean(speed_vals)) if len(speed_vals) else 0.0
            fragmentation_index = (
                float(bout_count_selected / active_minutes_selected)
                if active_minutes_selected > 0 else np.nan
            )
            matrix_summary_rows.append({
                'SelectedTotalRevs': total_revs_selected,
                'SelectedActiveMinutes': active_minutes_selected,
                'SelectedBoutCount': bout_count_selected,
                'SelectedLongestBoutDuration_min': longest_bout_selected,
                'SelectedMeanBoutSpeed_revPerMin': mean_bout_speed_selected,
                'SelectedFragmentation_BoutPerActiveMin': fragmentation_index,
            })

        matrix_summary_df = pd.DataFrame(matrix_summary_rows)
        plot_df = pd.concat([plot_df.reset_index(drop=True), matrix_summary_df], axis=1)

        plot_df['UMAP1'] = emb[:, 0]
        plot_df['UMAP2'] = emb[:, 1]

        # PCA diagnostic coordinates and group-separation diagnostics.
        pca_coord_cols = [f'PC{i+1}' for i in range(X_for_umap.shape[1])]
        pca_coord_df = pd.DataFrame(X_for_umap, columns=pca_coord_cols)
        pca_coord_full_df = pd.concat([
            plot_df[['Cohort', 'MouseID', 'MouseLabel', 'Group', 'Day', 'RealDate']].reset_index(drop=True),
            matrix_summary_df.reset_index(drop=True),
            pca_coord_df.reset_index(drop=True)
        ], axis=1)

        if n_pca >= 2 and 'pca' in locals():
            pca_explained_df = pd.DataFrame({
                'PC': [f'PC{i+1}' for i in range(len(pca.explained_variance_ratio_))],
                'ExplainedVarianceRatio': pca.explained_variance_ratio_,
                'CumulativeExplainedVariance': np.cumsum(pca.explained_variance_ratio_)
            })
        else:
            pca_explained_df = pd.DataFrame({
                'PC': [],
                'ExplainedVarianceRatio': [],
                'CumulativeExplainedVariance': []
            })

        def _centroid_separation_rows(meta_df, coord_arr, space_name='PCA', level='Overall'):
            rows = []
            groups = ['SNr-DTA', 'Control']
            valid = meta_df['Group'].isin(groups).to_numpy()
            if valid.sum() == 0:
                return rows

            def _one_row(sub_meta, sub_coords, label_value):
                group_vecs = {}
                for g in groups:
                    mask = (sub_meta['Group'].to_numpy() == g)
                    if mask.sum() > 0:
                        group_vecs[g] = sub_coords[mask, :]
                if ('SNr-DTA' not in group_vecs) or ('Control' not in group_vecs):
                    return None

                c_snr = np.nanmean(group_vecs['SNr-DTA'], axis=0)
                c_ctrl = np.nanmean(group_vecs['Control'], axis=0)
                centroid_dist = float(np.linalg.norm(c_snr - c_ctrl))

                def _dispersion(vals, center):
                    if vals.shape[0] == 0:
                        return np.nan
                    return float(np.nanmean(np.linalg.norm(vals - center, axis=1)))

                disp_snr = _dispersion(group_vecs['SNr-DTA'], c_snr)
                disp_ctrl = _dispersion(group_vecs['Control'], c_ctrl)
                pooled_disp = float(np.nanmean([disp_snr, disp_ctrl]))
                sep_index = float(centroid_dist / pooled_disp) if pooled_disp and pooled_disp > 0 else np.nan
                return {
                    'Space': space_name,
                    'Level': level,
                    'Label': label_value,
                    'n_SNr-DTA': int(group_vecs['SNr-DTA'].shape[0]),
                    'n_Control': int(group_vecs['Control'].shape[0]),
                    'CentroidDistance': centroid_dist,
                    'WithinDispersion_SNr-DTA': disp_snr,
                    'WithinDispersion_Control': disp_ctrl,
                    'WithinDispersion_PooledMean': pooled_disp,
                    'SeparationIndex_CentroidDistanceOverPooledDispersion': sep_index,
                }

            overall = _one_row(meta_df.loc[valid].reset_index(drop=True), coord_arr[valid, :], 'All selected days')
            if overall is not None:
                rows.append(overall)

            for d in sorted(meta_df.loc[valid, 'Day'].dropna().unique()):
                day_mask = valid & (meta_df['Day'].to_numpy() == d)
                day_row = _one_row(meta_df.loc[day_mask].reset_index(drop=True), coord_arr[day_mask, :], f'D{int(d)}')
                if day_row is not None:
                    rows.append(day_row)
            return rows

        pca_separation_rows = _centroid_separation_rows(
            plot_df.reset_index(drop=True), X_for_umap, space_name='PCA', level='Overall/Day'
        )
        umap_separation_rows = _centroid_separation_rows(
            plot_df.reset_index(drop=True), emb, space_name='UMAP', level='Overall/Day'
        )
        separation_df = pd.DataFrame(pca_separation_rows + umap_separation_rows)

        plot_df = plot_df.sort_values(['Group', 'MouseLabel', 'Day']).reset_index(drop=True)

        base_red = (0.80, 0.24, 0.24)
        base_blue = (0.20, 0.45, 0.82)

        snr_labels = sorted(plot_df.loc[plot_df['Group'] == 'SNr-DTA', 'MouseLabel'].dropna().unique().tolist(), key=_extract_sc_number)
        ctrl_labels = sorted(plot_df.loc[plot_df['Group'] == 'Control', 'MouseLabel'].dropna().unique().tolist(), key=_extract_sc_number)
        label_to_color = {}
        for lab, c in zip(snr_labels, _make_gradient_colors(base_red, len(snr_labels))):
            label_to_color[lab] = c
        for lab, c in zip(ctrl_labels, _make_gradient_colors(base_blue, len(ctrl_labels))):
            label_to_color[lab] = c

        if use_cohort2_special_colors:
            for lab in list(label_to_color.keys()):
                c2_color = _cohort2_special_color_for_label(lab)
                if c2_color is not None:
                    label_to_color[lab] = c2_color

        from matplotlib.lines import Line2D
        legend_handles = [
            Line2D([0], [0], marker='o', color=label_to_color.get(lab, 'gray'),
                   markerfacecolor=label_to_color.get(lab, 'gray'), markeredgecolor='black',
                   markersize=7, linewidth=1.6, label=lab)
            for lab in snr_labels + ctrl_labels
        ]

        day_min = min(recruited_days)
        day_max = max(recruited_days)
        zones_short = '+'.join([z['key'] for z in selected_zones])
        zones_long = '; '.join([z['label'] for z in selected_zones])
        pdf_path = f'./FunctionalTrajectory_MouseDayUMAP_{WINDOW_MINUTES}minMatrix_D{day_min}-{day_max}_{zones_short}.pdf'
        csv_path = f'./FunctionalTrajectory_MouseDayUMAP_Coordinates_{WINDOW_MINUTES}minMatrix_D{day_min}-{day_max}_{zones_short}.csv'
        feature_csv_path = f'./FunctionalTrajectory_MouseDayUMAP_FeatureMatrix_{WINDOW_MINUTES}minMatrix_D{day_min}-{day_max}_{zones_short}.csv'
        pca_csv_path = f'./FunctionalTrajectory_MouseDayUMAP_PCAExplainedVariance_{WINDOW_MINUTES}minMatrix_D{day_min}-{day_max}_{zones_short}.csv'
        pca_coord_csv_path = f'./FunctionalTrajectory_MouseDayUMAP_PCACoordinates_{WINDOW_MINUTES}minMatrix_D{day_min}-{day_max}_{zones_short}.csv'
        separation_csv_path = f'./FunctionalTrajectory_MouseDayUMAP_GroupSeparation_{WINDOW_MINUTES}minMatrix_D{day_min}-{day_max}_{zones_short}.csv'

        note = (
            f"Each point = one mouse-day. Feature matrix = {len(selected_indices)} selected {WINDOW_MINUTES}-min windows × 5 features. "
            f"Selected zones: {zones_long}. Bout threshold: rev/min ≥ {BOUT_THRESHOLD_REVS_PER_MIN}. "
            f"PCA components before UMAP: {n_pca}; PCA variance explained: {pca_var:.2f}."
        )

        def _compute_density_grid(x_vals, y_vals, x_edges, y_edges):
            if len(x_vals) == 0 or len(y_vals) == 0:
                return np.zeros((len(x_edges) - 1, len(y_edges) - 1), dtype=float)
            H, _, _ = np.histogram2d(x_vals, y_vals, bins=[x_edges, y_edges])
            H = H.astype(float)
            if np.nansum(H) > 0:
                H = H / np.nansum(H)
            return H.T  # transpose for plotting with pcolormesh/contourf

        with PdfPages(pdf_path) as pdf:
            # Page 1: scatter only.
            fig, ax = plt.subplots(figsize=(13, 9))
            for label in snr_labels + ctrl_labels:
                sub = plot_df[plot_df['MouseLabel'] == label]
                color = label_to_color.get(label, 'gray')
                ax.scatter(sub['UMAP1'], sub['UMAP2'], s=58, color=color,
                           edgecolor='black', linewidth=0.7, alpha=0.92, label=label)
            ax.set_title(f"Mouse-Day UMAP: Functional Matrix (D{day_min}–D{day_max})", fontsize=15, fontweight='bold')
            ax.set_xlabel("UMAP 1", fontsize=12, fontweight='bold')
            ax.set_ylabel("UMAP 2", fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.25)
            if legend_handles:
                ax.legend(handles=legend_handles, loc='center left', bbox_to_anchor=(1.02, 0.5),
                          fontsize=8, frameon=False, title='Mouse')
            fig.text(0.5, 0.02, note, ha='center', va='bottom', fontsize=8.5)
            plt.tight_layout(rect=[0, 0.05, 0.84, 1])
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # Page 2: individual trajectories.
            fig, ax = plt.subplots(figsize=(13, 9))
            for label in snr_labels + ctrl_labels:
                sub = plot_df[plot_df['MouseLabel'] == label].sort_values('Day')
                if sub.empty:
                    continue
                color = label_to_color.get(label, 'gray')
                ax.plot(sub['UMAP1'], sub['UMAP2'], color=color, linewidth=1.8, alpha=0.75)
                ax.scatter(sub['UMAP1'], sub['UMAP2'], s=50, color=color,
                           edgecolor='black', linewidth=0.7, alpha=0.92)
                first = sub.iloc[0]
                last = sub.iloc[-1]
                ax.scatter([first['UMAP1']], [first['UMAP2']], s=140, facecolors='none',
                           edgecolors=color, linewidths=2.0)
                ax.scatter([last['UMAP1']], [last['UMAP2']], s=130, marker='X', color=color,
                           edgecolor='black', linewidth=0.8)
                for d in [day_min, 7, 14, 21, 28, day_max]:
                    hit = sub[sub['Day'] == d]
                    if not hit.empty:
                        r = hit.iloc[0]
                        ax.annotate(f"D{int(d)}", (r['UMAP1'], r['UMAP2']),
                                    xytext=(3, 3), textcoords='offset points',
                                    fontsize=7, color=color)
            ax.set_title(f"Mouse-Day Functional Trajectories (D{day_min}–D{day_max})", fontsize=15, fontweight='bold')
            ax.set_xlabel("UMAP 1", fontsize=12, fontweight='bold')
            ax.set_ylabel("UMAP 2", fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.25)
            if legend_handles:
                ax.legend(handles=legend_handles, loc='center left', bbox_to_anchor=(1.02, 0.5),
                          fontsize=8, frameon=False, title='Mouse')
            fig.text(0.5, 0.02, note + " Open circle = first selected day; X = last selected day.", ha='center', va='bottom', fontsize=8.5)
            plt.tight_layout(rect=[0, 0.05, 0.84, 1])
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # Page 3: group centroid trajectory by day.
            fig, ax = plt.subplots(figsize=(11, 8))
            group_color = {'SNr-DTA': base_red, 'Control': base_blue}
            for group in ['SNr-DTA', 'Control']:
                gdf = plot_df[plot_df['Group'] == group]
                if gdf.empty:
                    continue
                centers = gdf.groupby('Day')[['UMAP1', 'UMAP2']].mean().reset_index().sort_values('Day')
                sems = gdf.groupby('Day')[['UMAP1', 'UMAP2']].sem().reset_index().sort_values('Day')
                color = group_color[group]
                ax.plot(centers['UMAP1'], centers['UMAP2'], color=color, linewidth=2.8, marker='o',
                        markersize=8, markeredgecolor='black', label=f"{group} centroid")
                for _, row in centers.iterrows():
                    ax.annotate(f"D{int(row['Day'])}", (row['UMAP1'], row['UMAP2']),
                                xytext=(5, 4), textcoords='offset points', fontsize=8, color=color)
                # light SEM bars in UMAP space
                for i, row in centers.iterrows():
                    sx = float(sems.loc[sems['Day'] == row['Day'], 'UMAP1'].iloc[0]) if row['Day'] in sems['Day'].values else np.nan
                    sy = float(sems.loc[sems['Day'] == row['Day'], 'UMAP2'].iloc[0]) if row['Day'] in sems['Day'].values else np.nan
                    if not np.isnan(sx) and not np.isnan(sy):
                        ax.errorbar(row['UMAP1'], row['UMAP2'], xerr=sx, yerr=sy,
                                    fmt='none', ecolor=color, alpha=0.35, capsize=2)
            ax.set_title(f"Group-Centroid Functional Trajectory (D{day_min}–D{day_max})", fontsize=15, fontweight='bold')
            ax.set_xlabel("UMAP 1", fontsize=12, fontweight='bold')
            ax.set_ylabel("UMAP 2", fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.25)
            ax.legend(frameon=False, fontsize=10)
            fig.text(0.5, 0.02, "Centroids are means of mouse-day UMAP coordinates within each group and day.", ha='center', va='bottom', fontsize=8.5)
            plt.tight_layout(rect=[0, 0.05, 1, 1])
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # Page 4: feature overlays to interpret what drives the UMAP geometry.
            overlay_specs = [
                ('SelectedBoutCount', 'Selected bout count'),
                ('SelectedActiveMinutes', 'Selected active minutes'),
                ('SelectedFragmentation_BoutPerActiveMin', 'Fragmentation index\n(bout count / active minutes)'),
                ('SelectedLongestBoutDuration_min', 'Selected longest bout duration (min)'),
                ('SelectedMeanBoutSpeed_revPerMin', 'Selected mean bout speed\n(rev/min)'),
                ('Day', 'DayIndex')
            ]
            fig, axes = plt.subplots(2, 3, figsize=(14.5, 9.5))
            axes = axes.flatten()
            for ax, (col, title_txt) in zip(axes, overlay_specs):
                vals = plot_df[col].to_numpy(dtype=float)
                sc = ax.scatter(
                    plot_df['UMAP1'], plot_df['UMAP2'],
                    c=vals, s=52, cmap='viridis',
                    edgecolor='black', linewidth=0.35, alpha=0.95
                )
                ax.set_title(title_txt, fontsize=11, fontweight='bold')
                ax.set_xlabel('UMAP 1', fontsize=10)
                ax.set_ylabel('UMAP 2', fontsize=10)
                ax.grid(True, alpha=0.25)
                cbar = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
                cbar.ax.tick_params(labelsize=8)
            fig.suptitle('Feature overlays on mouse-day UMAP', fontsize=15, fontweight='bold', y=0.98)
            fig.text(
                0.5, 0.01,
                'These overlays help interpret a clumped UMAP by showing whether the map is structured by day, activity load, or fragmentation.',
                ha='center', va='bottom', fontsize=9
            )
            plt.tight_layout(rect=[0, 0.03, 1, 0.96])
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # Page 5: occupancy / density maps by group.
            x_all = plot_df['UMAP1'].to_numpy(dtype=float)
            y_all = plot_df['UMAP2'].to_numpy(dtype=float)
            x_pad = max(1e-6, 0.08 * (np.nanmax(x_all) - np.nanmin(x_all) if len(x_all) > 1 else 1.0))
            y_pad = max(1e-6, 0.08 * (np.nanmax(y_all) - np.nanmin(y_all) if len(y_all) > 1 else 1.0))
            x_edges = np.linspace(np.nanmin(x_all) - x_pad, np.nanmax(x_all) + x_pad, 40)
            y_edges = np.linspace(np.nanmin(y_all) - y_pad, np.nanmax(y_all) + y_pad, 40)

            snr_df = plot_df[plot_df['Group'] == 'SNr-DTA']
            ctrl_df = plot_df[plot_df['Group'] == 'Control']
            H_snr = _compute_density_grid(snr_df['UMAP1'].to_numpy(dtype=float), snr_df['UMAP2'].to_numpy(dtype=float), x_edges, y_edges)
            H_ctrl = _compute_density_grid(ctrl_df['UMAP1'].to_numpy(dtype=float), ctrl_df['UMAP2'].to_numpy(dtype=float), x_edges, y_edges)
            H_diff = H_snr - H_ctrl
            abs_max = float(np.nanmax(np.abs(H_diff))) if np.size(H_diff) else 1.0

            fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.8))
            mesh0 = axes[0].pcolormesh(x_edges, y_edges, H_snr, shading='auto', cmap='Reds')
            axes[0].scatter(snr_df['UMAP1'], snr_df['UMAP2'], s=12, color=base_red, alpha=0.35, edgecolor='none')
            axes[0].set_title('SNr-DTA occupancy density', fontsize=12, fontweight='bold')
            fig.colorbar(mesh0, ax=axes[0], fraction=0.046, pad=0.04)

            mesh1 = axes[1].pcolormesh(x_edges, y_edges, H_ctrl, shading='auto', cmap='Blues')
            axes[1].scatter(ctrl_df['UMAP1'], ctrl_df['UMAP2'], s=12, color=base_blue, alpha=0.35, edgecolor='none')
            axes[1].set_title('Control occupancy density', fontsize=12, fontweight='bold')
            fig.colorbar(mesh1, ax=axes[1], fraction=0.046, pad=0.04)

            mesh2 = axes[2].pcolormesh(
                x_edges, y_edges, H_diff, shading='auto', cmap='coolwarm',
                vmin=-abs_max, vmax=abs_max
            )
            axes[2].set_title('Density difference\n(SNr-DTA minus Control)', fontsize=12, fontweight='bold')
            fig.colorbar(mesh2, ax=axes[2], fraction=0.046, pad=0.04)

            for ax in axes:
                ax.set_xlabel('UMAP 1', fontsize=10)
                ax.set_ylabel('UMAP 2', fontsize=10)
                ax.grid(True, alpha=0.18)
            fig.suptitle('UMAP occupancy / density by group', fontsize=15, fontweight='bold', y=0.98)
            fig.text(
                0.5, 0.01,
                'High-impact behavior papers often interpret occupancy of embedded space, not only raw point separation.',
                ha='center', va='bottom', fontsize=9
            )
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # Page 6: UMAP parameter sweep to see whether clumping is robust.
            sweep_params = [(3, 0.0), (5, 0.05), (10, 0.25), (15, 0.5)]
            fig, axes = plt.subplots(2, 2, figsize=(12.0, 10.0))
            axes = axes.flatten()
            handles = []
            labels = []
            for ax, (nn, md) in zip(axes, sweep_params):
                nn_eff = max(2, min(nn, X_for_umap.shape[0] - 1))
                reducer_sweep = umap.UMAP(
                    n_neighbors=nn_eff,
                    min_dist=md,
                    n_components=2,
                    metric='cosine',
                    random_state=42,
                )
                emb_sweep = reducer_sweep.fit_transform(X_for_umap)

                for group_name, color in [('SNr-DTA', base_red), ('Control', base_blue)]:
                    gmask = plot_df['Group'].to_numpy() == group_name
                    sc = ax.scatter(
                        emb_sweep[gmask, 0], emb_sweep[gmask, 1],
                        s=38, color=color, edgecolor='black', linewidth=0.35, alpha=0.85, label=group_name
                    )
                    if group_name not in labels:
                        handles.append(sc)
                        labels.append(group_name)
                ax.set_title(f'n_neighbors={nn_eff}, min_dist={md}', fontsize=11, fontweight='bold')
                ax.set_xlabel('UMAP 1', fontsize=10)
                ax.set_ylabel('UMAP 2', fontsize=10)
                ax.grid(True, alpha=0.25)
            fig.legend(handles, labels, loc='upper center', ncol=2, frameon=False, fontsize=10)
            fig.suptitle('UMAP parameter sweep', fontsize=15, fontweight='bold', y=0.97)
            fig.text(
                0.5, 0.01,
                'If all panels are similarly clumped, the structure is likely genuinely weak in the current feature set / time selection.',
                ha='center', va='bottom', fontsize=9
            )
            plt.tight_layout(rect=[0, 0.03, 1, 0.94])
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)

            # Page 7: PCA explained variance diagnostic.
            if not pca_explained_df.empty:
                fig, ax = plt.subplots(figsize=(10.5, 6.2))
                pcs = np.arange(1, len(pca_explained_df) + 1)
                ax.bar(pcs, pca_explained_df['ExplainedVarianceRatio'].to_numpy(), alpha=0.55,
                       label='Per-PC variance')
                ax.plot(pcs, pca_explained_df['CumulativeExplainedVariance'].to_numpy(),
                        marker='o', linewidth=2.2, color='black', label='Cumulative variance')
                ax.set_xlabel('Principal component', fontsize=12, fontweight='bold')
                ax.set_ylabel('Explained variance ratio', fontsize=12, fontweight='bold')
                ax.set_title('PCA variance retained before UMAP', fontsize=15, fontweight='bold')
                ax.grid(True, axis='y', alpha=0.3)
                ax.legend(frameon=False, fontsize=10)
                fig.text(0.5, 0.02, note, ha='center', va='bottom', fontsize=8.5)
                plt.tight_layout(rect=[0, 0.05, 1, 1])
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

            # Page 5: group separation across days in PCA and UMAP spaces.
            if not separation_df.empty:
                fig, ax = plt.subplots(figsize=(11.5, 6.5))
                day_sep = separation_df[separation_df['Label'].astype(str).str.startswith('D')].copy()
                if not day_sep.empty:
                    day_sep['DayNum'] = day_sep['Label'].str.replace('D', '', regex=False).astype(int)
                    for space_name, color in [('PCA', 'black'), ('UMAP', 'gray')]:
                        sub = day_sep[day_sep['Space'] == space_name].sort_values('DayNum')
                        if sub.empty:
                            continue
                        ax.plot(sub['DayNum'], sub['SeparationIndex_CentroidDistanceOverPooledDispersion'],
                                marker='o', linewidth=2.2, label=f'{space_name}: centroid distance / within dispersion',
                                color=color)
                ax.set_xlabel('DayIndex', fontsize=12, fontweight='bold')
                ax.set_ylabel('Group separation index', fontsize=12, fontweight='bold')
                ax.set_title('SNr-DTA vs Control separation by day', fontsize=15, fontweight='bold')
                ax.grid(False)
                ax.legend(frameon=False, fontsize=9)
                fig.text(
                    0.5, 0.02,
                    'Separation index = distance between group centroids divided by mean within-group dispersion. '
                    'Interpret in PCA/original feature space first; UMAP is visualization-oriented.',
                    ha='center', va='bottom', fontsize=8.5
                )
                plt.tight_layout(rect=[0, 0.06, 1, 1])
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

        plot_df.to_csv(csv_path, index=False)
        feature_df = pd.DataFrame(X)
        feature_meta = plot_df[['Cohort', 'MouseID', 'MouseLabel', 'Group', 'Day', 'RealDate']].copy()
        feature_out = pd.concat([feature_meta, feature_df.add_prefix('F')], axis=1)
        feature_out.to_csv(feature_csv_path, index=False)
        pca_explained_df.to_csv(pca_csv_path, index=False)
        pca_coord_full_df.to_csv(pca_coord_csv_path, index=False)
        separation_df.to_csv(separation_csv_path, index=False)

        print(f"Saved mouse-day UMAP PDF: {pdf_path}")
        print(f"Saved mouse-day UMAP coordinates CSV: {csv_path}")
        print(f"Saved mouse-day UMAP feature matrix CSV: {feature_csv_path}")
        print(f"Saved PCA explained-variance CSV: {pca_csv_path}")
        print(f"Saved PCA coordinates CSV: {pca_coord_csv_path}")
        print(f"Saved group-separation CSV: {separation_csv_path}")
        messagebox.showinfo(
            "Complete",
            f"Generated mouse-day functional UMAP\n\n"
            f"PDF: {pdf_path}\n"
            f"Coordinates CSV: {csv_path}\n"
            f"Feature CSV: {feature_csv_path}\n"
            f"PCA variance CSV: {pca_csv_path}\n"
            f"Group-separation CSV: {separation_csv_path}"
        )


    def compare_activity_sum_across_days_multi_cohort(self):
        """
        Multi-cohort version of compare_activity_sum_across_days().
        It asks for multiple cohort files, applies the same cohort-level mouse exclusions,
        optionally removes LM45, aligns cohort 3 day indexing, and plots total daily
        distance for each included mouse over experimental days 8-21 only.
        """
        import matplotlib.pyplot as plt
        import numpy as np
        import re
        from tkinter import filedialog

        file_paths = filedialog.askopenfilenames(
            title="Select cohort data files for pooled distance comparison",
            filetypes=[("Data Files", "*.csv *.xls *.xlsx")]
        )
        if not file_paths:
            messagebox.showinfo("No Files", "No files selected.")
            return

        sex_csv_path = filedialog.askopenfilename(
            title="Select mouse sex CSV for 4-group distance plots",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        sex_lookup = {}
        if sex_csv_path:
            try:
                sex_df = pd.read_csv(sex_csv_path)
                if ('ID' not in sex_df.columns) or ('Sex' not in sex_df.columns):
                    messagebox.showwarning(
                        "Sex CSV warning",
                        "Sex CSV must contain columns named 'ID' and 'Sex'.\n"
                        "The 4-group genotype × sex plots will be skipped."
                    )
                else:
                    for _, row in sex_df.iterrows():
                        sid = str(row['ID']).strip().lower()
                        sex = str(row['Sex']).strip().upper()
                        if sex.startswith('F'):
                            sex_lookup[sid] = 'Female'
                        elif sex.startswith('M'):
                            sex_lookup[sid] = 'Male'
                    print(f"Loaded sex metadata for {len(sex_lookup)} mouse IDs from: {sex_csv_path}")
            except Exception as e:
                messagebox.showwarning(
                    "Sex CSV warning",
                    f"Could not read sex CSV:\n{e}\n\n"
                    "The 4-group genotype × sex plots will be skipped."
                )
                sex_lookup = {}
        else:
            print("No sex CSV selected; genotype × sex grouped plots will be skipped.")

        remove_lm45 = self._ask_remove_lm45_from_mouse_pool("pooled multi-cohort distance comparison")
        try:
            remove_sc08 = messagebox.askyesno(
                "Remove SC08?",
                "Remove SC08 from the mouse pool for pooled multi-cohort distance comparison?\n\n"
                "Yes = exclude SC08\n"
                "No = keep SC08"
            )
        except Exception:
            remove_sc08 = False
        try:
            remove_sc15 = messagebox.askyesno(
                "Remove SC15?",
                "Remove SC15 from the mouse pool for pooled multi-cohort distance comparison?\n\n"
                "Yes = exclude SC15\n"
                "No = keep SC15"
            )
        except Exception:
            remove_sc15 = False

        # Cohort 2 mouse IDs 1-4 are excluded by rule; do not ask to include SC04/SC05/SC06.
        include_sc04 = False
        include_sc05 = False
        include_sc06 = False

        try:
            use_cohort2_special_colors = messagebox.askyesno(
                "Special colors for cohort 2?",
                "If cohort 2 mice SC04, SC05, SC06, or SC08 are included, use special colors?\n\n"
                "Yes = SC04/SC05/SC06 use orange gradients, SC08 uses gold-yellow\n"
                "No = use regular group colors"
            )
        except Exception:
            use_cohort2_special_colors = False

        try:
            highlight_special_mice = messagebox.askyesno(
                "Highlight selected mice?",
                "Do you want to highlight selected mice in singleMouse_TotalDistance_OverDays.pdf?\n\n"
                "Yes = choose mice in the next popup window\n"
                "No = use regular group colors"
            )
        except Exception:
            highlight_special_mice = False

        try:
            use_cumulative_distance = messagebox.askyesno(
                "Distance value mode",
                "Use cumulative distance values for the distance-over-days plots?\n\n"
                "Yes = cumulative distance up to each day\n"
                "No = distance traveled on that day only"
            )
        except Exception:
            use_cumulative_distance = True

        distance_mode_label = "Cumulative" if use_cumulative_distance else "Daily"
        distance_mode_filetag = "Cumulative" if use_cumulative_distance else "DailyOnly"
        y_axis_distance_label = (
            "Cumulative distance per mouse (km)"
            if use_cumulative_distance else
            "Daily total distance per mouse (km)"
        )

        DAY_MIN = 8
        DAY_MAX = 21

        def _cohort_from_path(file_path):
            try:
                if file_path.endswith('.xls') or file_path.endswith('.csv'):
                    return int(file_path[-5:-4])
                return int(file_path[-6:-5])
            except Exception:
                m = re.search(r'[Cc]ohort\s*([0-9]+)|[Cc]([0-9]+)', os.path.basename(file_path))
                if m:
                    return int(next(g for g in m.groups() if g))
                raise

        def _labels_for_cohort(cohort_num):
            return self._labels_for_cohort_global(cohort_num)
        def _mouse_id_from_label_for_sex_lookup(mouse_label):
            label = str(mouse_label).strip()
            m = re.search(r'(SC\d+|LM45)', label, flags=re.IGNORECASE)
            if m:
                return m.group(1).lower()
            return label.split('(')[0].strip().lower()

        def _genotype_group_from_label(mouse_label):
            label = str(mouse_label)
            if 'SNr-DTA' in label:
                return 'SNr-DTA'
            if 'Control' in label or 'GPi-DTA' in label:
                return 'Control'
            return 'Other'

        def _genotype_sex_group_from_label(mouse_label):
            genotype = _genotype_group_from_label(mouse_label)
            sid = _mouse_id_from_label_for_sex_lookup(mouse_label)
            sex = sex_lookup.get(sid, None)
            if genotype in ['SNr-DTA', 'Control'] and sex in ['Female', 'Male']:
                return f'{genotype} {sex}'
            return None

        def _apply_exact_label_filter(mouse_ids, mouse_labels, label_token, should_remove, cohort_num=None, context=""):
            """
            Remove only mice whose label explicitly contains label_token.
            This avoids removing the same numeric mouse ID from unrelated cohorts.
            """
            mouse_ids = [int(mid) for mid in list(mouse_ids)]
            if not should_remove:
                return mouse_ids

            remove_ids = set()
            if mouse_labels:
                for idx, label in enumerate(mouse_labels, start=1):
                    if label_token in str(label):
                        remove_ids.add(idx)

            if not remove_ids:
                return mouse_ids

            kept = [mid for mid in mouse_ids if int(mid) not in remove_ids]
            removed = sorted(set(mouse_ids) - set(kept))
            if removed:
                print(f"[{label_token} filter{': ' + context if context else ''}] removed mouse IDs {removed} from cohort {cohort_num}; kept {kept}")
            return kept

        def _read_activity_file(file_path):
            if file_path.endswith('.xls') or file_path.endswith('.xlsx'):
                try:
                    return pd.read_csv(file_path, skiprows=10, sep='\t')
                except Exception:
                    return pd.read_csv(file_path, skiprows=10)
            if file_path.endswith('.csv'):
                return pd.read_csv(file_path, skiprows=10)
            raise ValueError(f"Unsupported file format: {file_path}")

        def make_gradient_colors(base_color, n):
            gradients = []
            for i in range(n):
                ratio = 0.10 + (0.55 * i / max(n - 1, 1))
                color = tuple(base_color[j] * (1 - ratio) + ratio for j in range(3))
                gradients.append(color)
            return gradients

        # Unified style for pooled multi-cohort distance figures
        png_flag = False  # optional PNG export; default off

        SNR_BAR_FILL = (0.45, 0.75, 0.45)
        CTRL_BAR_FILL = (0.55, 0.55, 0.55)
        SNR_DOT = (0.25, 0.55, 0.25)
        CTRL_DOT = (0.35, 0.35, 0.35)
        SNR_LINE = (0.40, 0.70, 0.40)
        CTRL_LINE = (0.30, 0.30, 0.30)
        OTHER_GRAY = (0.35, 0.35, 0.35)

        def extract_sc_number(label):
            match = re.search(r'SC(\d+)', str(label))
            return int(match.group(1)) if match else 999

        def _is_default_highlight_mouse_label(label):
            label_upper = str(label).upper()
            return (
                ('SC08' in label_upper) or
                ('SC15' in label_upper) or
                ('LM45' in label_upper) or
                ('SC33' in label_upper) or
                ('SC35' in label_upper)
            )

        def _cohort2_special_color_for_label(label):
            if not use_cohort2_special_colors:
                return None
            label_upper = str(label).upper()
            if 'SC04' in label_upper:
                return (0.95, 0.48, 0.05)
            if 'SC05' in label_upper:
                return (0.90, 0.35, 0.02)
            if 'SC06' in label_upper:
                return (0.75, 0.22, 0.00)
            if 'SC08' in label_upper:
                return '#FFD700'
            return None

        def _ask_highlight_mice_from_pool(sorted_mouse_ids, label_lookup_dict):
            """
            Popup checkbox selector for choosing which included mice to highlight
            in singleMouse_TotalDistance_OverDays.pdf.
            Default selections are SC08, SC15, LM45, SC33, and SC35 when present.
            """
            selected_ids = set()
            if not sorted_mouse_ids:
                return selected_ids

            dialog = tk.Toplevel(self.root)
            dialog.title("Choose mice to highlight")
            dialog.transient(self.root)
            dialog.grab_set()

            tk.Label(
                dialog,
                text="Choose mice to highlight in bright gold:",
                font=("Arial", 11, "bold"),
                padx=10, pady=8
            ).pack(anchor="w")

            outer = tk.Frame(dialog)
            outer.pack(fill="both", expand=True, padx=10, pady=(0, 8))

            canvas = tk.Canvas(outer, height=320)
            scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
            scroll_frame = tk.Frame(canvas)

            scroll_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            vars_by_uid = {}
            for uid in sorted_mouse_ids:
                label = label_lookup_dict.get(uid, uid)
                var = tk.BooleanVar(value=_is_default_highlight_mouse_label(label))
                vars_by_uid[uid] = var
                tk.Checkbutton(
                    scroll_frame,
                    text=label,
                    variable=var,
                    padx=8, pady=2
                ).pack(anchor="w")

            def _select_default():
                for uid, var in vars_by_uid.items():
                    var.set(_is_default_highlight_mouse_label(label_lookup_dict.get(uid, uid)))

            def _select_all():
                for var in vars_by_uid.values():
                    var.set(True)

            def _clear_all():
                for var in vars_by_uid.values():
                    var.set(False)

            def _ok():
                selected_ids.clear()
                for uid, var in vars_by_uid.items():
                    if var.get():
                        selected_ids.add(uid)
                dialog.destroy()

            def _cancel():
                selected_ids.clear()
                dialog.destroy()

            btn_frame = tk.Frame(dialog, padx=10, pady=10)
            btn_frame.pack(fill="x")
            tk.Button(btn_frame, text="Default", command=_select_default).pack(side="left", padx=4)
            tk.Button(btn_frame, text="Select all", command=_select_all).pack(side="left", padx=4)
            tk.Button(btn_frame, text="Clear", command=_clear_all).pack(side="left", padx=4)
            tk.Button(btn_frame, text="OK", command=_ok).pack(side="right", padx=4)
            tk.Button(btn_frame, text="Cancel", command=_cancel).pack(side="right", padx=4)

            dialog.protocol("WM_DELETE_WINDOW", _cancel)
            self.root.wait_window(dialog)
            return selected_ids

        activity_records = {}
        label_lookup = {}
        group_lookup = {}
        genotype_sex_group_lookup = {}
        sex_metadata_rows = []

        for file_path in file_paths:
            try:
                cohort_num = _cohort_from_path(file_path)
                mouse_labels = _labels_for_cohort(cohort_num)
                df = _read_activity_file(file_path)
                df = df.dropna(how='all').dropna(axis=1, how='all')
                df.columns = [col.strip() for col in df.columns]
                if 'Bin' not in df.columns:
                    print(f"Warning: no Bin column in {file_path}; skipped.")
                    continue
                df['Bin'] = pd.to_datetime(df['Bin'], format='mixed', errors='coerce')
                df = df.dropna(subset=['Bin'])
                if df.empty:
                    continue

                # Recompute DateIndex from Bin for this pooled multi-cohort plot.
                # Cohort 3 is shifted because its raw data day 0 should be interpreted
                # as experimental day 8, matching the convention used elsewhere.
                reference_date = df['Bin'].dt.normalize().min().date()
                if cohort_num == 3:
                    reference_date = reference_date - timedelta(days=8)
                    print(
                        f"Cohort 3 date alignment: raw first date "
                        f"{df['Bin'].dt.normalize().min().date()} is treated as Day 8; "
                        f"reference_date set to {reference_date}."
                    )
                ref_ts = pd.Timestamp(reference_date)
                df['DateIndex'] = (df['Bin'].dt.normalize() - ref_ts).dt.days
                df = df[(df['DateIndex'] >= DAY_MIN) & (df['DateIndex'] <= DAY_MAX)].copy()
                if df.empty:
                    print(f"No records in days {DAY_MIN}-{DAY_MAX} for cohort {cohort_num}; skipped.")
                    continue

                mouse_ids = sorted(set(col.split()[2] for col in df.columns if col.startswith('1 8')))
                mouse_ids = [int(m) for m in mouse_ids if str(m).isdigit()]

                excluded_mice = []
                if cohort_num == 1:
                    for i in [3, 5, 6, 7]:
                        if i in mouse_ids:
                            mouse_ids.remove(i)
                            excluded_mice.append(i)
                if cohort_num == 2:
                    # Cohort 2 exclusion rule:
                    # remove mouse IDs 1, 2, 3, and 4.
                    # SC08 = mouse ID 5 remains available.
                    for i in [1, 2, 3, 4]:
                        if i in mouse_ids:
                            mouse_ids.remove(i)
                            excluded_mice.append(i)
                if cohort_num == 4:
                    for i in [7]:
                        if i in mouse_ids:
                            mouse_ids.remove(i)
                            excluded_mice.append(i)

                self._print_mouse_candidates('pooled multi-cohort distance comparison', cohort_num, mouse_ids, mouse_labels, stage='after base exclusions')
                mouse_ids = self._apply_lm45_mouse_filter(
                    mouse_ids, mouse_labels, remove_lm45, cohort_num=cohort_num,
                    context='pooled multi-cohort distance comparison'
                )
                mouse_ids = _apply_exact_label_filter(
                    mouse_ids, mouse_labels, 'SC08', remove_sc08,
                    cohort_num=cohort_num, context='pooled multi-cohort distance comparison'
                )
                mouse_ids = _apply_exact_label_filter(
                    mouse_ids, mouse_labels, 'SC15', remove_sc15,
                    cohort_num=cohort_num, context='pooled multi-cohort distance comparison'
                )
                self._print_mouse_candidates('pooled multi-cohort distance comparison', cohort_num, mouse_ids, mouse_labels, stage='final candidates after LM45/SC08/SC15 decisions')

                for day, day_df in df.groupby('DateIndex'):
                    for mid in mouse_ids:
                        km_col = f'1 8 {mid} km'
                        if km_col not in day_df.columns:
                            continue
                        km = pd.to_numeric(day_df[km_col], errors='coerce')
                        total_km = float(km.sum())
                        label = mouse_labels[mid - 1] if mid - 1 < len(mouse_labels) else f'Mouse {mid}'
                        unique_id = f'C{cohort_num}_M{mid}'
                        display_label = label
                        activity_records.setdefault(unique_id, []).append((int(day), total_km))
                        label_lookup[unique_id] = display_label
                        group_lookup[unique_id] = _genotype_group_from_label(label)

                        # Optional 4-group classification: genotype × sex.
                        # Sex is read from user-selected CSV with ID values like sc09 and Sex values F/M.
                        sex_id = _mouse_id_from_label_for_sex_lookup(label)
                        sex_value = sex_lookup.get(sex_id, None)
                        genotype_sex_group = _genotype_sex_group_from_label(label)
                        if genotype_sex_group is not None:
                            genotype_sex_group_lookup[unique_id] = genotype_sex_group
                        sex_metadata_rows.append({
                            'UniqueID': unique_id,
                            'Cohort': cohort_num,
                            'MouseID': int(mid),
                            'MouseLabel': label,
                            'SexLookupID': sex_id,
                            'Sex': sex_value if sex_value is not None else 'Missing',
                            'GenotypeGroup': group_lookup[unique_id],
                            'GenotypeSexGroup': genotype_sex_group if genotype_sex_group is not None else 'Missing_or_Other'
                        })

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        if not activity_records:
            messagebox.showinfo("No Data", "No valid mouse/day distance records found.")
            return

        base_red = SNR_LINE
        base_blue = CTRL_LINE
        base_gray = OTHER_GRAY

        snr_ids = sorted([uid for uid, g in group_lookup.items() if g == 'SNr-DTA'],
                         key=lambda uid: extract_sc_number(label_lookup.get(uid, uid)))
        ctrl_ids = sorted([uid for uid, g in group_lookup.items() if g == 'Control'],
                          key=lambda uid: extract_sc_number(label_lookup.get(uid, uid)))
        other_ids = sorted([uid for uid, g in group_lookup.items() if g not in ['SNr-DTA', 'Control']])
        sorted_ids = snr_ids + ctrl_ids + other_ids

        selected_highlight_ids = set()
        if highlight_special_mice:
            selected_highlight_ids = _ask_highlight_mice_from_pool(sorted_ids, label_lookup)
            print(
                "Highlighted mice for singleMouse_TotalDistance_OverDays.pdf:",
                [label_lookup.get(uid, uid) for uid in sorted_ids if uid in selected_highlight_ids]
            )

        mouse_colors = {}
        for i, uid in enumerate(snr_ids):
            mouse_colors[uid] = make_gradient_colors(base_red, len(snr_ids))[i]
        for i, uid in enumerate(ctrl_ids):
            mouse_colors[uid] = make_gradient_colors(base_blue, len(ctrl_ids))[i]
        for i, uid in enumerate(other_ids):
            mouse_colors[uid] = make_gradient_colors(base_gray, len(other_ids))[i]

        if use_cohort2_special_colors:
            for uid in sorted_ids:
                c2_color = _cohort2_special_color_for_label(label_lookup.get(uid, uid))
                if c2_color is not None:
                    mouse_colors[uid] = c2_color

        fig, ax = plt.subplots(figsize=(14, 6))
        bright_gold = '#FFD700'
        for uid in sorted_ids:
            records = sorted(activity_records[uid], key=lambda x: x[0])
            days = ["D" + str(r[0]) for r in records]
            # One scalar per mouse per day, so the plot remains 2D: day x distance.
            if use_cumulative_distance:
                values = np.cumsum([r[1] for r in records])
            else:
                values = np.array([r[1] for r in records], dtype=float)

            this_label = label_lookup.get(uid, uid)
            should_highlight = bool(uid in selected_highlight_ids)
            line_color = bright_gold if should_highlight else mouse_colors.get(uid, 'gray')
            line_width = 3.2 if should_highlight else 2.0
            marker_size = 7.5 if should_highlight else 5.0
            zorder_value = 6 if should_highlight else 2

            ax.plot(days, values,
                    label=this_label,
                    marker='o',
                    color=line_color,
                    linewidth=line_width,
                    markersize=marker_size,
                    markeredgecolor='k',
                    markeredgewidth=0.8 if should_highlight else 0.4,
                    zorder=zorder_value)

        ax.set_xlabel("Date", fontsize=12, fontweight='bold')
        ax.set_ylabel(y_axis_distance_label, fontsize=12, fontweight='bold')
        ax.set_title(f"{distance_mode_label} Total Distance by Mouse (Days {DAY_MIN}–{DAY_MAX})", fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=8, ncol=2)
        plt.tight_layout()

        output_path = f'./singleMouse_{distance_mode_filetag}Distance_OverDays.pdf'
        fig.savefig(output_path, bbox_inches='tight')
        if png_flag:
            fig.savefig(output_path.replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
        print(f"Saved cumulative single-mouse distance comparison: {output_path}")

        # Build cumulative per-mouse daily distance records.
        cumulative_activity_records = {}
        for uid, records in activity_records.items():
            sorted_records = sorted(records, key=lambda x: x[0])
            running_total = 0.0
            cumulative_activity_records[uid] = []
            for d, v in sorted_records:
                running_total += float(v)
                cumulative_activity_records[uid].append((int(d), running_total))

        # Merge final cumulative distance into a user-selected CSV by ID.
        # This is always cumulative, independent of whether the current plot mode is cumulative or daily-only.
        final_cumulative_rows = []
        for uid in sorted_ids:
            records = sorted(activity_records.get(uid, []), key=lambda x: x[0])
            if not records:
                continue
            cumulative_total = 0.0
            final_day = None
            final_value = np.nan
            for d, v in records:
                cumulative_total += float(v)
                final_day = int(d)
                final_value = float(cumulative_total)

            animal_id = str(_mouse_id_from_label_for_sex_lookup(label_lookup.get(uid, uid))).upper()

            final_cumulative_rows.append({
                'ID': animal_id,
                'Group': group_lookup.get(uid, 'Unknown'),
                'FinalDay': final_day,
                'FinalCumulativeDistance_km': final_value,
            })

        final_cumulative_merge_path = filedialog.askopenfilename(
            title="Select CSV to merge final cumulative distance into by ID",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        if final_cumulative_merge_path:
            try:
                target_df = pd.read_csv(final_cumulative_merge_path)
                id_col = next((c for c in target_df.columns if str(c).strip().lower() == 'id'), None)
                if id_col is None:
                    messagebox.showwarning(
                        "Missing ID column",
                        "The selected CSV does not contain an ID column.\n"
                        "Final cumulative distance was not merged."
                    )
                    final_cumulative_csv_path = 'not merged: selected CSV missing ID column'
                else:
                    final_df = pd.DataFrame(final_cumulative_rows)
                    target_df['_merge_id_lower_tmp'] = target_df[id_col].astype(str).str.strip().str.lower()
                    final_df['_merge_id_lower_tmp'] = final_df['ID'].astype(str).str.strip().str.lower()

                    merge_cols = [
                        '_merge_id_lower_tmp',
                        'Group',
                        'FinalDay',
                        'FinalCumulativeDistance_km',
                    ]

                    # Remove old copies of these columns before replacing them with current values.
                    for col in ['Group', 'FinalDay', 'FinalCumulativeDistance_km']:
                        if col in target_df.columns:
                            target_df = target_df.drop(columns=[col])

                    merged_df = target_df.merge(
                        final_df[merge_cols].drop_duplicates(subset=['_merge_id_lower_tmp']),
                        on='_merge_id_lower_tmp',
                        how='left'
                    ).drop(columns=['_merge_id_lower_tmp'])

                    merged_df.to_csv(final_cumulative_merge_path, index=False)
                    final_cumulative_csv_path = final_cumulative_merge_path
                    print(f"Merged final cumulative distance into selected CSV: {final_cumulative_merge_path}")
                if '_merge_id_lower_tmp' in locals():
                    pass
            except Exception as e:
                final_cumulative_csv_path = 'merge failed'
                messagebox.showwarning(
                    "Cumulative merge failed",
                    f"Could not merge final cumulative distance into selected CSV:\n{e}"
                )
        else:
            final_cumulative_csv_path = 'not merged: no CSV selected'
            print("No CSV selected for final cumulative distance merge.")

        # Grouped plot: summarize selected per-mouse daily distances within each group.
        # Page 1: median ± SE across mice for each day.
        # Page 2: mean ± STD across mice for each day.
        group_days = list(range(DAY_MIN, DAY_MAX + 1))
        group_colors = {'SNr-DTA': base_red, 'Control': base_blue}

        # Select whether downstream grouped plots use cumulative values or day-only values.
        distance_records_for_group_plots = cumulative_activity_records if use_cumulative_distance else activity_records

        def _group_day_values(group_name, day):
            group_uids = [uid for uid, g in group_lookup.items() if g == group_name]
            vals = []
            for uid in group_uids:
                day_vals = [v for d, v in distance_records_for_group_plots.get(uid, []) if int(d) == int(day)]
                vals.extend(day_vals)
            vals = np.asarray(vals, dtype=float)
            return vals[np.isfinite(vals)]


        def _group_stats_by_day(group_name):
            rows = []
            for day in group_days:
                vals = _group_day_values(group_name, day)
                n = len(vals)
                if n == 0:
                    rows.append({
                        'Day': day, 'n': 0,
                        'mean': np.nan, 'std': np.nan,
                        'median': np.nan, 'se': np.nan
                    })
                    continue
                std = float(np.std(vals, ddof=1)) if n > 1 else 0.0
                se = float(std / np.sqrt(n)) if n > 1 else 0.0
                rows.append({
                    'Day': day,
                    'n': n,
                    'mean': float(np.mean(vals)),
                    'std': std,
                    'median': float(np.median(vals)),
                    'se': se
                })
            return pd.DataFrame(rows)

        grouped_stats = {
            'SNr-DTA': _group_stats_by_day('SNr-DTA'),
            'Control': _group_stats_by_day('Control')
        }

        # Grouped summary PDF. When cumulative mode is selected, this becomes
        # Grouped_CumulativeDistance_OverDays.pdf and uses the green / grey schematic below.
        group_output_path = f'./Grouped_{distance_mode_filetag}Distance_OverDays.pdf'
        group_colors = {'SNr-DTA': SNR_LINE, 'Control': CTRL_LINE}
        group_fill_colors = {'SNr-DTA': SNR_BAR_FILL, 'Control': CTRL_BAR_FILL}
        group_dot_colors = {'SNr-DTA': SNR_DOT, 'Control': CTRL_DOT}

        def _blend_with_white(color, alpha):
            import matplotlib.colors as mcolors
            rgb = np.asarray(mcolors.to_rgb(color), dtype=float)
            return tuple(rgb * float(alpha) + (1.0 - float(alpha)))

        def _all_group_values():
            all_vals = []
            for day in group_days:
                all_vals.extend(_group_day_values('SNr-DTA', day).tolist())
                all_vals.extend(_group_day_values('Control', day).tolist())
            all_vals = np.asarray(all_vals, dtype=float)
            return all_vals[np.isfinite(all_vals)]

        def _range_tuple():
            finite_all_vals = _all_group_values()
            data_min = float(np.nanmin(finite_all_vals)) if len(finite_all_vals) else 0.0
            data_max = float(np.nanmax(finite_all_vals)) if len(finite_all_vals) else 1.0
            data_range = max(data_max - data_min, 1.0)
            return data_min, data_max, data_range

        def _decorate_group_line_axis(ax, title, summary_key, err_key):
            data_min, data_max, data_range = _range_tuple()
            curve_top = -np.inf
            curve_bottom = np.inf

            for group_name in ['SNr-DTA', 'Control']:
                stats = grouped_stats[group_name]
                x = stats['Day'].to_numpy(dtype=float)
                y = stats[summary_key].to_numpy(dtype=float)
                err = stats[err_key].to_numpy(dtype=float)
                color = group_colors.get(group_name, base_gray)
                n_mice = len([uid for uid, g in group_lookup.items() if g == group_name])

                valid_upper = (y + err)[np.isfinite(y + err)]
                valid_lower = (y - err)[np.isfinite(y - err)]
                if len(valid_upper):
                    curve_top = max(curve_top, float(np.max(valid_upper)))
                if len(valid_lower):
                    curve_bottom = min(curve_bottom, float(np.min(valid_lower)))

                ax.plot(
                    x, y,
                    label=f"{group_name} (n={n_mice} mice)",
                    marker='o', linewidth=2.5, markersize=5.8,
                    color=color, markeredgecolor='k', markeredgewidth=0.8
                )
                ax.fill_between(x, y - err, y + err, color=color, alpha=0.20, linewidth=0)

            if not np.isfinite(curve_top):
                curve_top = data_max
            if not np.isfinite(curve_bottom):
                curve_bottom = data_min

            curve_range = max(curve_top - curve_bottom, 1.0)
            ax.set_ylim(
                bottom=max(0.0, curve_bottom - 0.01 * curve_range),
                top=curve_top + 0.03 * curve_range
            )
            ax.set_xlabel("Date", fontsize=12, fontweight='bold')
            ax.set_ylabel(y_axis_distance_label, fontsize=12, fontweight='bold')
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xticks(group_days)
            ax.set_xticklabels([f"D{d}" for d in group_days], rotation=45, fontsize=11)
            ax.tick_params(axis='y', labelsize=11)
            ax.grid(False)
            ax.legend(loc='best', fontsize=10, frameon=False)
        with PdfPages(group_output_path) as pdf:
            fig_med, ax_med = plt.subplots(figsize=(10.8, 6.0))
            _decorate_group_line_axis(
                ax_med,
                f"Grouped {distance_mode_label} Distance: Median ± SE (Days {DAY_MIN}–{DAY_MAX})",
                'median', 'se'
            )
            plt.tight_layout()
            pdf.savefig(fig_med, bbox_inches='tight')
            grouped_eps_median = group_output_path.replace('.pdf', '_median.eps')
            fig_med.savefig(grouped_eps_median, format='eps')
            if png_flag:
                fig_med.savefig(group_output_path.replace('.pdf', '_median.png'), dpi=300, bbox_inches='tight')
            plt.close(fig_med)

        # Exact-basename EPS: median page only, matching the PDF output.
        grouped_eps_exact = group_output_path.replace('.pdf', '.eps')

        def _decorate_group_line_axis_eps(ax, summary_key, err_key, show_ylabel=True):
            data_min, data_max, data_range = _range_tuple()
            curve_top = -np.inf
            curve_bottom = np.inf

            for group_name in ['SNr-DTA', 'Control']:
                stats = grouped_stats[group_name]
                x = stats['Day'].to_numpy(dtype=float)
                y = stats[summary_key].to_numpy(dtype=float)
                err = stats[err_key].to_numpy(dtype=float)
                color = group_colors.get(group_name, base_gray)
                n_mice = len([uid for uid, g in group_lookup.items() if g == group_name])

                valid_upper = (y + err)[np.isfinite(y + err)]
                valid_lower = (y - err)[np.isfinite(y - err)]
                if len(valid_upper):
                    curve_top = max(curve_top, float(np.max(valid_upper)))
                if len(valid_lower):
                    curve_bottom = min(curve_bottom, float(np.min(valid_lower)))

                ax.plot(
                    x, y,
                    label=f"{group_name} (n={n_mice} mice)",
                    marker='o', linewidth=2.5, markersize=5.8,
                    color=color, markeredgecolor='k', markeredgewidth=0.8
                )
                ax.fill_between(
                    x, y - err, y + err,
                    color=_blend_with_white(color, 0.20),
                    alpha=1.0, linewidth=0
                )

            if not np.isfinite(curve_top):
                curve_top = data_max
            if not np.isfinite(curve_bottom):
                curve_bottom = data_min

            curve_range = max(curve_top - curve_bottom, 1.0)
            ax.set_ylim(
                bottom=max(0.0, curve_bottom - 0.01 * curve_range),
                top=curve_top + 0.03 * curve_range
            )
            ax.set_xlabel("Date", fontsize=12, fontweight='bold')
            ax.set_ylabel(y_axis_distance_label if show_ylabel else '', fontsize=12, fontweight='bold')
            ax.set_xticks(group_days)
            ax.set_xticklabels([f"D{d}" for d in group_days], rotation=45, fontsize=11)
            ax.tick_params(axis='y', labelsize=11)
            ax.grid(False)
            ax.legend(loc='best', fontsize=10, frameon=False)

        fig_eps, ax_eps = plt.subplots(1, 1, figsize=(10.8, 6.0))
        _decorate_group_line_axis_eps(ax_eps, 'median', 'se', show_ylabel=True)
        fig_eps.tight_layout()
        fig_eps.savefig(grouped_eps_exact, format='eps', facecolor='white', edgecolor='white', transparent=False)
        plt.close(fig_eps)

        print(f"Saved grouped multi-cohort distance summary: {group_output_path}")
        print(f"Saved grouped multi-cohort distance exact-basename EPS: {grouped_eps_exact}")
        print(f"Saved grouped multi-cohort distance EPS page export: {grouped_eps_median}")
        if 'Cumulative' in group_output_path:
            print('Grouped_CumulativeDistance_OverDays.pdf style: '
                  'SNr-DTA = green schematic, Control = grey schematic.')

        # A second grouped visualization: day-by-day boxplots using the same per-mouse daily values.
        # Page 1 overlays median ± SE; Page 2 overlays mean ± STD.
        box_output_path = f'./Grouped_TotalDistance_BoxPlot_OverDays_{distance_mode_filetag}.pdf'

        def _draw_grouped_day_boxplot(ax, summary_mode='mean_std'):
            positions = []
            data = []
            colors = []
            offset = 0.16
            width = 0.32

            for day in group_days:
                for group_name, dx in [('SNr-DTA', -offset), ('Control', offset)]:
                    vals = _group_day_values(group_name, day)
                    vals = vals[np.isfinite(vals)]
                    positions.append(float(day) + dx)
                    data.append(vals if len(vals) > 0 else np.array([np.nan]))
                    colors.append(group_fill_colors.get(group_name, CTRL_BAR_FILL))

            bp = ax.boxplot(
                data,
                positions=positions,
                widths=width,
                patch_artist=True,
                showfliers=False,
                whis=0,
                showcaps=False,
                medianprops=dict(color='black', linewidth=1.4),
                whiskerprops=dict(linewidth=0),
                capprops=dict(linewidth=0)
            )

            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.95)
                patch.set_edgecolor('black')
                patch.set_linewidth(1.0)

            rng = np.random.default_rng(42)
            legend_added = set()
            for day in group_days:
                for group_name, dx in [('SNr-DTA', -offset), ('Control', offset)]:
                    vals = _group_day_values(group_name, day)
                    vals = vals[np.isfinite(vals)]
                    if len(vals) == 0:
                        continue
                    center = float(day) + dx
                    xjit = rng.uniform(center - 0.12, center + 0.12, size=len(vals))
                    label = group_name if group_name not in legend_added else None
                    legend_added.add(group_name)
                    ax.scatter(
                        xjit, vals,
                        s=55,
                        facecolor=group_dot_colors.get(group_name, CTRL_DOT),
                        edgecolor='black',
                        linewidth=0.8,
                        alpha=0.95, zorder=5,
                        label=label
                    )

                    if summary_mode == 'median_se':
                        summary_val = float(np.nanmedian(vals))
                        err_val = float(np.nanstd(vals, ddof=1) / np.sqrt(len(vals))) if len(vals) > 1 else 0.0
                    else:
                        summary_val = float(np.nanmean(vals))
                        err_val = float(np.nanstd(vals, ddof=1)) if len(vals) > 1 else 0.0

                    fill_color = group_fill_colors.get(group_name, CTRL_BAR_FILL)
                    ax.errorbar(
                        center,
                        summary_val,
                        yerr=err_val,
                        fmt='o',
                        color='black',
                        ecolor='black',
                        markerfacecolor=fill_color,
                        markeredgecolor='black',
                        markeredgewidth=0.8,
                        linewidth=1.5,
                        capsize=7,
                        zorder=6
                    )

            data_min, data_max, data_range = _range_tuple()
            ax.set_xlim(DAY_MIN - 0.75, DAY_MAX + 0.75)
            ax.set_ylim(bottom=max(0.0, data_min - 0.04 * data_range),
                        top=data_max + 0.10 * data_range)
            ax.set_xticks(group_days)
            ax.set_xticklabels([f"D{d}" for d in group_days], rotation=45, fontsize=11)
            ax.tick_params(axis='y', labelsize=11)
            ax.set_xlabel("Date", fontsize=12, fontweight='bold')
            ax.set_ylabel(y_axis_distance_label, fontsize=12, fontweight='bold')
            ax.grid(False)
            ax.legend(loc='best', fontsize=9, frameon=False)
        with PdfPages(box_output_path) as pdf:
            fig_box_med, ax_box_med = plt.subplots(figsize=(12.0, 6.2))
            _draw_grouped_day_boxplot(ax_box_med, summary_mode='median_se')
            ax_box_med.set_title(
                f"{distance_mode_label} Distance Boxplots: Median ± SE Overlay (Days {DAY_MIN}–{DAY_MAX})",
                fontsize=14, fontweight='bold'
            )
            plt.tight_layout()
            pdf.savefig(fig_box_med, bbox_inches='tight')
            if png_flag:
                fig_box_med.savefig(box_output_path.replace('.pdf', '_median.png'), dpi=300, bbox_inches='tight')
            plt.close(fig_box_med)

            fig_box_mean, ax_box_mean = plt.subplots(figsize=(12.0, 6.2))
            _draw_grouped_day_boxplot(ax_box_mean, summary_mode='mean_std')
            ax_box_mean.set_title(
                f"{distance_mode_label} Distance Boxplots: Mean ± STD Overlay (Days {DAY_MIN}–{DAY_MAX})",
                fontsize=14, fontweight='bold'
            )
            plt.tight_layout()
            pdf.savefig(fig_box_mean, bbox_inches='tight')
            if png_flag:
                fig_box_mean.savefig(box_output_path.replace('.pdf', '_mean.png'), dpi=300, bbox_inches='tight')
            plt.close(fig_box_mean)

        print(f"Saved grouped multi-cohort distance boxplots: {box_output_path}")

        # ------------------------------------------------------------------
        # Additional 4-group output: genotype × sex
        # Groups:
        #   SNr-DTA Female, SNr-DTA Male, Control Female, Control Male
        # Uses the same cumulative per-mouse/day values as the plots above.
        # ------------------------------------------------------------------
        # sex_metadata_rows are kept internally for checks, but no mouse-metadata CSV is saved.

        genotype_sex_order = ['SNr-DTA Female', 'SNr-DTA Male', 'Control Female', 'Control Male']
        genotype_sex_colors = {
            'SNr-DTA Female': (0.95, 0.45, 0.45),
            'SNr-DTA Male': (0.70, 0.05, 0.05),
            'Control Female': (0.45, 0.65, 0.95),
            'Control Male': (0.05, 0.20, 0.70),
        }

        valid_genotype_sex_groups = [
            g for g in genotype_sex_order
            if any(v == g for v in genotype_sex_group_lookup.values())
        ]

        def _group_day_values_from_lookup(group_lookup_dict, group_name, day):
            group_uids = [uid for uid, g in group_lookup_dict.items() if g == group_name]
            vals = []
            for uid in group_uids:
                day_vals = [v for d, v in distance_records_for_group_plots.get(uid, []) if int(d) == int(day)]
                vals.extend(day_vals)
            vals = np.asarray(vals, dtype=float)
            return vals[np.isfinite(vals)]

        def _group_stats_by_day_from_lookup(group_lookup_dict, group_name):
            rows = []
            for day in group_days:
                vals = _group_day_values_from_lookup(group_lookup_dict, group_name, day)
                n = len(vals)
                if n == 0:
                    rows.append({
                        'Day': day, 'n': 0,
                        'mean': np.nan, 'std': np.nan,
                        'median': np.nan, 'se': np.nan
                    })
                    continue
                std = float(np.std(vals, ddof=1)) if n > 1 else 0.0
                se = float(std / np.sqrt(n)) if n > 1 else 0.0
                rows.append({
                    'Day': day,
                    'n': n,
                    'mean': float(np.mean(vals)),
                    'std': std,
                    'median': float(np.median(vals)),
                    'se': se
                })
            return pd.DataFrame(rows)

        if valid_genotype_sex_groups:
            genotype_sex_stats = {
                group_name: _group_stats_by_day_from_lookup(genotype_sex_group_lookup, group_name)
                for group_name in valid_genotype_sex_groups
            }

            genotype_sex_summary_rows = []
            for group_name, sdf in genotype_sex_stats.items():
                tmp = sdf.copy()
                tmp.insert(0, 'Group', group_name)
                genotype_sex_summary_rows.append(tmp)
            if genotype_sex_summary_rows:
                genotype_sex_summary_df = pd.concat(genotype_sex_summary_rows, ignore_index=True)
                genotype_sex_summary_csv = './Grouped_TotalDistance_GenotypeSex_SummaryStats.csv'
                genotype_sex_summary_df.to_csv(genotype_sex_summary_csv, index=False)
                print(f"Saved genotype × sex summary CSV: {genotype_sex_summary_csv}")

            genotype_sex_line_pdf = f'./Grouped_TotalDistance_ByGenotypeSex_OverDays_{distance_mode_filetag}.pdf'
            with PdfPages(genotype_sex_line_pdf) as pdf:
                # Page 1: median ± SE.
                fig_med4, ax_med4 = plt.subplots(figsize=(11.5, 6.2))
                for group_name in valid_genotype_sex_groups:
                    stats = genotype_sex_stats[group_name]
                    x = stats['Day'].to_numpy(dtype=float)
                    y = stats['median'].to_numpy(dtype=float)
                    err = stats['se'].to_numpy(dtype=float)
                    color = genotype_sex_colors.get(group_name, base_gray)
                    n_mice = len([uid for uid, g in genotype_sex_group_lookup.items() if g == group_name])
                    ax_med4.plot(
                        x, y,
                        label=f"{group_name} (n={n_mice} mice)",
                        marker='o', linewidth=2.3, markersize=5.4,
                        color=color, markeredgecolor='k', markeredgewidth=0.45
                    )
                    ax_med4.fill_between(x, y - err, y + err, color=color, alpha=0.14, linewidth=0)

                ax_med4.set_xlabel("Date", fontsize=12, fontweight='bold')
                ax_med4.set_ylabel(y_axis_distance_label, fontsize=12, fontweight='bold')
                ax_med4.set_title(f"Grouped {distance_mode_label} Distance by Genotype × Sex: Median ± SE (Days {DAY_MIN}–{DAY_MAX})",
                                  fontsize=13.5, fontweight='bold')
                ax_med4.set_xticks(group_days)
                ax_med4.set_xticklabels([f"D{d}" for d in group_days], rotation=45)
                ax_med4.grid(True, alpha=0.3)
                ax_med4.legend(loc='best', fontsize=9, frameon=False)
                plt.tight_layout()
                pdf.savefig(fig_med4, bbox_inches='tight')
                plt.close(fig_med4)
            # Page 2: mean ± STD.
                fig_mean4, ax_mean4 = plt.subplots(figsize=(11.5, 6.2))
                for group_name in valid_genotype_sex_groups:
                    stats = genotype_sex_stats[group_name]
                    x = stats['Day'].to_numpy(dtype=float)
                    y = stats['mean'].to_numpy(dtype=float)
                    err = stats['std'].to_numpy(dtype=float)
                    color = genotype_sex_colors.get(group_name, base_gray)
                    n_mice = len([uid for uid, g in genotype_sex_group_lookup.items() if g == group_name])
                    ax_mean4.plot(
                        x, y,
                        label=f"{group_name} (n={n_mice} mice)",
                        marker='o', linewidth=2.3, markersize=5.4,
                        color=color, markeredgecolor='k', markeredgewidth=0.45
                    )
                    ax_mean4.fill_between(x, y - err, y + err, color=color, alpha=0.14, linewidth=0)

                ax_mean4.set_xlabel("Date", fontsize=12, fontweight='bold')
                ax_mean4.set_ylabel(y_axis_distance_label, fontsize=12, fontweight='bold')
                ax_mean4.set_title(f"Grouped {distance_mode_label} Distance by Genotype × Sex: Mean ± STD (Days {DAY_MIN}–{DAY_MAX})",
                                   fontsize=13.5, fontweight='bold')
                ax_mean4.set_xticks(group_days)
                ax_mean4.set_xticklabels([f"D{d}" for d in group_days], rotation=45)
                ax_mean4.grid(True, alpha=0.3)
                ax_mean4.legend(loc='best', fontsize=9, frameon=False)
                plt.tight_layout()
                pdf.savefig(fig_mean4, bbox_inches='tight')
                plt.close(fig_mean4)

    
            print(f"Saved genotype × sex grouped distance line plots: {genotype_sex_line_pdf}")

            genotype_sex_box_pdf = f'./Grouped_TotalDistance_BoxPlot_ByGenotypeSex_OverDays_{distance_mode_filetag}.pdf'

            def _draw_genotype_sex_day_boxplot(ax, summary_mode='mean_std'):
                n_groups = len(valid_genotype_sex_groups)
                if n_groups == 0:
                    return
                offsets = np.linspace(-0.33, 0.33, n_groups)
                width = min(0.15, 0.72 / max(n_groups, 1))
                positions = []
                data = []
                colors = []

                for day in group_days:
                    for group_name, dx in zip(valid_genotype_sex_groups, offsets):
                        vals = _group_day_values_from_lookup(genotype_sex_group_lookup, group_name, day)
                        vals = vals[np.isfinite(vals)]
                        positions.append(float(day) + dx)
                        data.append(vals if len(vals) > 0 else np.array([np.nan]))
                        colors.append(genotype_sex_colors.get(group_name, base_gray))

                bp = ax.boxplot(
                    data,
                    positions=positions,
                    widths=width,
                    patch_artist=True,
                    showfliers=False,
                    manage_ticks=False,
                    whis=0,
                    whiskerprops=dict(linewidth=0),
                    capprops=dict(linewidth=0),
                    medianprops=dict(linewidth=0),
                    boxprops=dict(linewidth=1.0)
                )
                for patch, color in zip(bp['boxes'], colors):
                    patch.set_facecolor(color)
                    patch.set_alpha(0.22)
                    patch.set_edgecolor(color)

                rng = np.random.default_rng(42)
                for day in group_days:
                    for group_name, dx in zip(valid_genotype_sex_groups, offsets):
                        vals = _group_day_values_from_lookup(genotype_sex_group_lookup, group_name, day)
                        vals = vals[np.isfinite(vals)]
                        if len(vals) == 0:
                            continue
                        center = float(day) + dx
                        jitter = rng.uniform(-0.025, 0.025, size=len(vals))
                        ax.scatter(
                            np.full(len(vals), center) + jitter,
                            vals,
                            s=24,
                            facecolor='white',
                            edgecolor=genotype_sex_colors.get(group_name, base_gray),
                            linewidth=0.9,
                            alpha=0.95,
                            zorder=4
                        )

                for group_name, dx in zip(valid_genotype_sex_groups, offsets):
                    color = genotype_sex_colors.get(group_name, base_gray)
                    xs, ys, errs = [], [], []
                    for day in group_days:
                        vals = _group_day_values_from_lookup(genotype_sex_group_lookup, group_name, day)
                        vals = vals[np.isfinite(vals)]
                        if len(vals) == 0:
                            continue
                        xs.append(float(day) + dx)
                        if summary_mode == 'mean_std':
                            ys.append(float(np.mean(vals)))
                            errs.append(float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0)
                        else:
                            std = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
                            ys.append(float(np.median(vals)))
                            errs.append(float(std / np.sqrt(len(vals))) if len(vals) > 1 else 0.0)

                    marker = 'D' if summary_mode == 'mean_std' else 's'
                    label = f"{group_name} ({'mean ± STD' if summary_mode == 'mean_std' else 'median ± SE'})"
                    ax.errorbar(
                        xs, ys, yerr=errs,
                        fmt=marker, markersize=5.6,
                        color=color, ecolor=color,
                        markerfacecolor=color,
                        markeredgecolor='black', markeredgewidth=0.65,
                        linewidth=1.8, capsize=3,
                        label=label, zorder=6
                    )

                ax.set_xlim(DAY_MIN - 0.75, DAY_MAX + 0.75)
                ax.set_xticks(group_days)
                ax.set_xticklabels([f"D{d}" for d in group_days], rotation=45)
                ax.set_xlabel("Date", fontsize=12, fontweight='bold')
                ax.set_ylabel(y_axis_distance_label, fontsize=12, fontweight='bold')
                ax.grid(True, axis='y', alpha=0.3)
                ax.legend(loc='best', fontsize=8, frameon=False)

            with PdfPages(genotype_sex_box_pdf) as pdf:
                fig_box_med4, ax_box_med4 = plt.subplots(figsize=(13.2, 6.4))
                _draw_genotype_sex_day_boxplot(ax_box_med4, summary_mode='median_se')
                ax_box_med4.set_title(
                    f"Genotype × Sex {distance_mode_label} Distance Boxplots: Median ± SE Overlay (Days {DAY_MIN}–{DAY_MAX})",
                    fontsize=13.5, fontweight='bold'
                )
                plt.tight_layout()
                pdf.savefig(fig_box_med4, bbox_inches='tight')
                plt.close(fig_box_med4)

                fig_box_mean4, ax_box_mean4 = plt.subplots(figsize=(13.2, 6.4))
                _draw_genotype_sex_day_boxplot(ax_box_mean4, summary_mode='mean_std')
                ax_box_mean4.set_title(
                    f"Genotype × Sex {distance_mode_label} Distance Boxplots: Mean ± STD Overlay (Days {DAY_MIN}–{DAY_MAX})",
                    fontsize=13.5, fontweight='bold'
                )
                plt.tight_layout()
                pdf.savefig(fig_box_mean4, bbox_inches='tight')
                plt.close(fig_box_mean4)


            print(f"Saved genotype × sex grouped distance boxplots: {genotype_sex_box_pdf}")
        else:
            print("No valid genotype × sex groups found; skipped 4-group distance plots.")

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

        remove_lm45 = self._ask_remove_lm45_from_mouse_pool("actogram analysis")
        print(f"[actogram analysis] LM45 removal option: {'REMOVE LM45' if remove_lm45 else 'KEEP LM45'}")

        df = self.df.sort_values(["DateIndex", "Bin"]).copy()

        # Actogram/profile binning. Smaller bins give finer temporal resolution.
        # 30 min means 48 bins across 24 h. Change this value if needed.
        ACTOGRAM_BIN_MINUTES = 10
        ACTOGRAM_BIN_HOURS = ACTOGRAM_BIN_MINUTES / 60.0
        N_ACTOGRAM_BINS = int(24 / ACTOGRAM_BIN_HOURS)
        ACTOGRAM_BIN_STARTS = np.arange(N_ACTOGRAM_BINS) * ACTOGRAM_BIN_HOURS
        ACTOGRAM_BIN_CENTERS = ACTOGRAM_BIN_STARTS + ACTOGRAM_BIN_HOURS / 2.0

        # EPS/PostScript does not support alpha transparency reliably. To make
        # Pooled_Actogram.eps visually match Pooled_Actogram.pdf, draw the
        # actogram figures without transparent artists by pre-blending colors
        # against a white background.
        def _blend_with_white(color, alpha):
            import matplotlib.colors as mcolors
            rgb = np.asarray(mcolors.to_rgb(color), dtype=float)
            return tuple(rgb * float(alpha) + (1.0 - float(alpha)))

        DARK_SPAN_COLOR = _blend_with_white('gray', 0.12)

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
        self._print_mouse_candidates('actogram current cohort', getattr(self, 'cohort', None), selected_mice, self.mouse_label, 'selected before LM45 filter')
        selected_mice = self._apply_lm45_mouse_filter(selected_mice, self.mouse_label, remove_lm45, cohort_num=getattr(self, 'cohort', None), context='actogram current cohort')
        self._print_mouse_candidates('actogram current cohort', getattr(self, 'cohort', None), selected_mice, self.mouse_label, 'selected after LM45 filter')
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

            # Organize by day and smaller clock-time bins.
            mouse_df['HourOfDay'] = (
                mouse_df['Bin'].dt.hour
                + mouse_df['Bin'].dt.minute / 60.0
                + mouse_df['Bin'].dt.second / 3600.0
            )

            mouse_day_data[mid] = {}

            # Get data for each day
            for day in sorted(mouse_df['DateIndex'].unique()):
                day_data = mouse_df[mouse_df['DateIndex'] == day].copy()

                binned_activity = np.zeros(N_ACTOGRAM_BINS)

                for i, bin_start in enumerate(ACTOGRAM_BIN_STARTS):
                    bin_end = bin_start + ACTOGRAM_BIN_HOURS
                    bin_mask = (day_data['HourOfDay'] >= bin_start) & (day_data['HourOfDay'] < bin_end)
                    if bin_mask.any():
                        # Mean rev/min inside this clock-time bin; this preserves the previous logic,
                        # but at a finer temporal resolution than hourly bins.
                        binned_activity[i] = day_data.loc[bin_mask, rev_col].mean()

                mouse_day_data[mid][int(day)] = binned_activity

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

                binned_activity = mouse_day_data[mid][day]

                # Normalize activity for visualization (0-1 scale per mouse for bar height)
                max_activity = max([np.max(mouse_day_data[mid][d])
                                    for d in mouse_day_data[mid].keys() if len(mouse_day_data[mid][d]) > 0])
                if max_activity > 0:
                    normalized_activity = binned_activity / max_activity * 0.8  # Scale to 0.8 for spacing
                else:
                    normalized_activity = binned_activity * 0

                # Plot 24 hours using smaller bins
                for i, bin_start in enumerate(ACTOGRAM_BIN_STARTS):
                    if normalized_activity[i] > 0:
                        ax_actogram.bar(bin_start, normalized_activity[i], bottom=y_offset,
                                        width=ACTOGRAM_BIN_HOURS, align='edge',
                                        color=color, alpha=0.7, edgecolor='none')

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

                binned_activity = mouse_day_data[mid][day]

                max_activity = max([np.max(mouse_day_data[mid][d])
                                    for d in mouse_day_data[mid].keys() if len(mouse_day_data[mid][d]) > 0])
                if max_activity > 0:
                    normalized_activity = binned_activity / max_activity * 0.8
                else:
                    normalized_activity = binned_activity * 0

                # Plot 24 hours using smaller bins
                for i, bin_start in enumerate(ACTOGRAM_BIN_STARTS):
                    if normalized_activity[i] > 0:
                        ax_actogram.bar(bin_start, normalized_activity[i], bottom=y_offset,
                                        width=ACTOGRAM_BIN_HOURS, align='edge',
                                        color=color, alpha=0.7, edgecolor='none')

                y_offset += 1

            ytick_positions.append(y_offset - len(all_days) / 2)
            ytick_labels.append(mouse_name)

        # Format actogram
        ax_actogram.set_xlim(0, 24)
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

        profile_x = ACTOGRAM_BIN_CENTERS

        if snr_mice:
            snr_mean, snr_sem = calc_group_average(snr_mice)
            if snr_mean is not None:
                ax_profile.plot(profile_x, snr_mean, color=base_red, linewidth=3,
                                label=f'SNr-DTA (n={len(snr_mice)})', marker='o', markersize=4)
                ax_profile.fill_between(profile_x, snr_mean - snr_sem, snr_mean + snr_sem,
                                        alpha=0.25, color=base_red)

        if ctrl_mice:
            ctrl_mean, ctrl_sem = calc_group_average(ctrl_mice)
            if ctrl_mean is not None:
                ax_profile.plot(profile_x, ctrl_mean, color=base_blue, linewidth=3,
                                label=f'Control (n={len(ctrl_mice)})', marker='s', markersize=4)
                ax_profile.fill_between(profile_x, ctrl_mean - ctrl_sem, ctrl_mean + ctrl_sem,
                                        alpha=0.25, color=base_blue)

        ax_profile.set_xlim(0, 24)
        ax_profile.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
        ax_profile.set_ylabel('Mean rev/min per 30-min bin\n(mean ± SEM)', fontsize=12, fontweight='bold')
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

                    c_labels = self._labels_for_cohort_global(c_num)

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
                    self._print_mouse_candidates('combined actogram', c_num, c_mids, c_labels, 'raw candidates from columns')

                    # excluded mice same rules as generate_bout_statistics_summary_multi_cohort
                    for skip in ([3, 5, 6, 7] if c_num == 1 else
                                 [4]           if c_num == 2 else
                                 [7] if c_num == 4 else []):
                        if skip in c_mids:
                            c_mids.remove(skip)

                    self._print_mouse_candidates('combined actogram', c_num, c_mids, c_labels, 'after base cohort exclusions, before LM45 filter')
                    c_mids = self._apply_lm45_mouse_filter(c_mids, c_labels, remove_lm45, cohort_num=c_num, context='combined actogram')
                    self._print_mouse_candidates('combined actogram', c_num, c_mids, c_labels, 'final candidates')

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
                        m_df['HourOfDay'] = (
                            m_df['Bin'].dt.hour
                            + m_df['Bin'].dt.minute / 60.0
                            + m_df['Bin'].dt.second / 3600.0
                        )

                        combined_mouse_day_data[key] = {}
                        for day in sorted(m_df['DateIndex'].unique()):
                            d_df = m_df[m_df['DateIndex'] == day]
                            h_arr = np.zeros(N_ACTOGRAM_BINS)
                            for i, bin_start in enumerate(ACTOGRAM_BIN_STARTS):
                                bin_end = bin_start + ACTOGRAM_BIN_HOURS
                                mask_h = (d_df['HourOfDay'] >= bin_start) & (d_df['HourOfDay'] < bin_end)
                                if mask_h.any():
                                    h_arr[i] = d_df.loc[mask_h, rev_col].mean()
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
                            for i, bin_start in enumerate(ACTOGRAM_BIN_STARTS):
                                if norm[i] > 0:
                                    ax_act.bar(bin_start, norm[i], bottom=y_off,
                                               width=ACTOGRAM_BIN_HOURS, align='edge',
                                               color=color, alpha=0.65, edgecolor='none')
                            y_off += 1
                            n_days_plotted += 1
                        if n_days_plotted:
                            ytick_pos.append(y_off - n_days_plotted / 2)
                            ytick_lbl.append(lbl)

                    if group_keys and sep_label == "SNr-DTA" and combined_ctrl_keys:
                        ax_act.axhline(y_off, color='black', linewidth=1.5, linestyle='--', alpha=0.6)
                        y_off += 0.5

                ax_act.set_xlim(0, 24)
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
                hours_x = ACTOGRAM_BIN_CENTERS

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

                ax_prof.set_xlim(0, 24)
                ax_prof.set_xticks(np.arange(0, 25, 3))
                ax_prof.set_xlabel('Hour of Day', fontsize=11, fontweight='bold')
                ax_prof.set_ylabel('Mean rev/min per 30-min bin\n(mean±SEM)', fontsize=11, fontweight='bold')
                ax_prof.set_title('Pooled Average Daily Activity Profile', fontsize=12, fontweight='bold')
                ax_prof.axvspan(18, 24, alpha=0.12, color='gray', zorder=0)
                ax_prof.axvspan(0,  6,  alpha=0.12, color='gray', zorder=0)
                ax_prof.grid(True, alpha=0.3, linestyle='--')
                ax_prof.legend(loc='best', fontsize=10, frameon=False)
                ax_prof.spines['top'].set_visible(False)
                ax_prof.spines['right'].set_visible(False)


                fig_all.tight_layout(rect=[0.03, 0.03, 0.98, 0.98])
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

    def plot_pooled_actogram(self):
        """
        Pooled actogram: select multiple cohort files, produce a single
        3-panel figure with exactly TWO group-level traces:
          Panel 1 (TOP)    – mean ± SEM hourly profile: SNr-DTA vs Control
          Panel 2 (MIDDLE) – stacked actogram, one row per mouse per day
          Panel 3 (BOTTOM) – Lomb-Scargle tau bar: SNr-DTA vs Control
        Days 8-21 only. Saved to ./AllCohorts_Pooled_Actogram_C*.pdf
        """
        from scipy import signal
        from tkinter import filedialog as _fd

        file_paths = _fd.askopenfilenames(
            title="Select cohort files for Pooled Actogram",
            filetypes=[("Data Files", "*.csv *.xls *.xlsx")]
        )
        if not file_paths:
            messagebox.showinfo("No Files", "No files selected.")
            return

        remove_lm45 = self._ask_remove_lm45_from_mouse_pool("pooled actogram")
        print(f"[pooled actogram] LM45 removal option: {'REMOVE LM45' if remove_lm45 else 'KEEP LM45'}")

        def lomb_scargle_period(times, values, min_period=20, max_period=28):
            mask         = ~np.isnan(np.array(values, dtype=float))
            times_clean  = np.array(times,  dtype=float)[mask]
            values_clean = np.array(values, dtype=float)[mask]
            if len(times_clean) < 24:
                return np.nan, np.nan, np.nan, np.nan
            frequencies = np.linspace(1 / max_period, 1 / min_period, 1000)
            try:
                ls_power = signal.lombscargle(
                    times_clean, values_clean - np.mean(values_clean),
                    frequencies * 2 * np.pi, normalize=True)
                peak_idx  = np.argmax(ls_power)
                tau       = 1.0 / frequencies[peak_idx]
                power     = ls_power[peak_idx]
                amplitude = np.sqrt(2 * power) * np.std(values_clean)
                M         = len(frequencies)
                fap       = 1 - (1 - np.exp(-power)) ** M
                return tau, power, amplitude, fap
            except Exception as e:
                print(f"Lomb-Scargle error: {e}")
                return np.nan, np.nan, np.nan, np.nan

        snr_shades  = [(0.80, 0.10, 0.10), (0.90, 0.35, 0.15),
                       (0.75, 0.20, 0.40), (0.95, 0.50, 0.30)]
        ctrl_shades = [(0.10, 0.25, 0.75), (0.20, 0.50, 0.85),
                       (0.10, 0.60, 0.70), (0.30, 0.40, 0.90)]

        # Actogram/profile binning. Smaller bins give finer temporal resolution.
        ACTOGRAM_BIN_MINUTES = 10
        ACTOGRAM_BIN_HOURS = ACTOGRAM_BIN_MINUTES / 60.0
        N_ACTOGRAM_BINS = int(24 / ACTOGRAM_BIN_HOURS)
        ACTOGRAM_BIN_STARTS = np.arange(N_ACTOGRAM_BINS) * ACTOGRAM_BIN_HOURS
        ACTOGRAM_BIN_CENTERS = ACTOGRAM_BIN_STARTS + ACTOGRAM_BIN_HOURS / 2.0

        # Local helper for EPS-compatible shading. EPS/PostScript does not
        # reliably support alpha, so transparent colors are pre-blended against white.
        def _blend_with_white(color, alpha):
            import matplotlib.colors as mcolors
            rgb = np.asarray(mcolors.to_rgb(color), dtype=float)
            return tuple(rgb * float(alpha) + (1.0 - float(alpha)))

        DARK_SPAN_COLOR = _blend_with_white('gray', 0.12)

        all_mouse_rows   = []
        snr_hourly_pool  = []
        ctrl_hourly_pool = []
        snr_48h_pool = []
        ctrl_48h_pool = []
        snr_tau_pool     = []
        ctrl_tau_pool    = []
        snr_mouse_count  = 0
        ctrl_mouse_count = 0
        cohort_nums_loaded = []

        for c_idx, fpath in enumerate(sorted(file_paths)):
            try:
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
                    ref_d = ref_d - timedelta(days=8)
                c_df['DateIndex'] = (c_df['Bin'].dt.normalize() - pd.Timestamp(ref_d)).dt.days
                c_df = c_df[(c_df['DateIndex'] >= 8) & (c_df['DateIndex'] <= 21)]

                c_mids = sorted(set(col.split()[2] for col in c_df.columns if col.startswith('1 8')))
                c_mids = [int(m) for m in c_mids if str(m).isdigit()]
                self._print_mouse_candidates('pooled actogram', c_num, c_mids, c_labels, 'raw candidates from columns')
                for skip in ([3,5,6,7] if c_num == 1 else
                             [1, 2, 3, 4] if c_num == 2 else
                             [7] if c_num == 4 else []):
                    if skip in c_mids:
                        c_mids.remove(skip)

                self._print_mouse_candidates('pooled actogram', c_num, c_mids, c_labels, 'after base cohort exclusions, before LM45 filter')
                c_mids = self._apply_lm45_mouse_filter(c_mids, c_labels, remove_lm45, cohort_num=c_num, context='pooled actogram')
                self._print_mouse_candidates('pooled actogram', c_num, c_mids, c_labels, 'final candidates')

                snr_col  = snr_shades[c_idx % len(snr_shades)]
                ctrl_col = ctrl_shades[c_idx % len(ctrl_shades)]
                cohort_nums_loaded.append(c_num)

                for mid in c_mids:
                    rev_col = f"1 8 {mid} rev"
                    if rev_col not in c_df.columns:
                        continue
                    lbl    = c_labels[mid - 1] if mid - 1 < len(c_labels) else f"C{c_num}M{mid}"
                    is_snr = "SNr" in lbl or "DTA" in lbl

                    m_df = c_df[['Bin', 'DateIndex', rev_col]].copy()
                    m_df[rev_col] = pd.to_numeric(m_df[rev_col], errors='coerce').fillna(0.0)
                    if len(m_df) < 24 * 60:
                        continue
                    m_df['HourOfDay'] = (
                        m_df['Bin'].dt.hour
                        + m_df['Bin'].dt.minute / 60.0
                        + m_df['Bin'].dt.second / 3600.0
                    )

                    day_arrays = {}
                    for day in sorted(m_df['DateIndex'].unique()):
                        d_df  = m_df[m_df['DateIndex'] == day]
                        h_arr = np.zeros(N_ACTOGRAM_BINS)
                        for i, bin_start in enumerate(ACTOGRAM_BIN_STARTS):
                            bin_end = bin_start + ACTOGRAM_BIN_HOURS
                            mask_h = (d_df['HourOfDay'] >= bin_start) & (d_df['HourOfDay'] < bin_end)
                            if mask_h.any():
                                h_arr[i] = d_df.loc[mask_h, rev_col].mean()
                        day_arrays[int(day)] = h_arr
                        (snr_hourly_pool if is_snr else ctrl_hourly_pool).append(h_arr)

                    all_mouse_rows.append({
                        'lbl':        lbl,
                        'color':      snr_col if is_snr else ctrl_col,
                        'is_snr':     is_snr,
                        'day_arrays': day_arrays,
                    })
                    if is_snr:
                        snr_mouse_count += 1
                    else:
                        ctrl_mouse_count += 1

                    m_df2 = m_df.sort_values('Bin').copy()
                    m_df2['HoursFromStart'] = (
                        m_df2['Bin'] - m_df2['Bin'].min()).dt.total_seconds() / 3600.0
                    tau_c, _, _, _ = lomb_scargle_period(
                        m_df2['HoursFromStart'].values, m_df2[rev_col].values)
                    if not np.isnan(tau_c):
                        (snr_tau_pool if is_snr else ctrl_tau_pool).append(tau_c)

                print(f"  Pooled actogram: loaded cohort {c_num}")
            except Exception as e_c:
                print(f"  Pooled actogram: skipped {fpath} ({e_c})")
                continue

        if not all_mouse_rows:
            messagebox.showerror("Error", "No data loaded.")
            return

        all_days   = sorted(set(d for row in all_mouse_rows for d in row['day_arrays'].keys()))

        # Build true 48-hour activity vectors for the 48 h profile.
        # Each vector is one mouse-specific adjacent-day window: day d followed by day d+1.
        # This is intentionally different from simply duplicating the 24 h mean profile.
        for row in all_mouse_rows:
            for day in all_days:
                if day in row['day_arrays'] and (day + 1) in row['day_arrays']:
                    pair_arr = np.concatenate([row['day_arrays'][day], row['day_arrays'][day + 1]])
                    (snr_48h_pool if row['is_snr'] else ctrl_48h_pool).append(pair_arr)

        cohort_tag = ', '.join(f'C{c}' for c in sorted(set(cohort_nums_loaded)))
        base_red   = (0.80, 0.20, 0.20)
        base_blue  = (0.20, 0.35, 0.75)

        # ── Build figure: profile on top (taller), actogram middle, tau bottom ──
        fig_all = plt.figure(figsize=(16, 14))
        gs_all  = fig_all.add_gridspec(3, 1, height_ratios=[3, 3, 1], hspace=0.40)

        # ---- Panel 1 (TOP): pooled mean ± SEM hourly profile ----
        ax_prof = fig_all.add_subplot(gs_all[0])
        hours_x = ACTOGRAM_BIN_CENTERS
        for hourly_pool, col, grp_lbl in [
                (snr_hourly_pool,  base_red,  f'SNr-DTA (n={snr_mouse_count} mice)'),
                (ctrl_hourly_pool, base_blue, f'Control (n={ctrl_mouse_count} mice)')]:
            if not hourly_pool:
                continue
            arr = np.array(hourly_pool)
            mn  = np.nanmean(arr, axis=0)
            sem = np.nanstd(arr, axis=0) / np.sqrt(len(hourly_pool))
            ax_prof.plot(hours_x, mn, color=col, linewidth=2.5,
                         label=grp_lbl, marker='o', markersize=3)
            ax_prof.fill_between(hours_x, mn - sem, mn + sem,
                                 alpha=1.0, color=_blend_with_white(col, 0.22), linewidth=0)
        ax_prof.set_xlim(0, 24)
        ax_prof.set_xticks(np.arange(0, 25, 3))
        ax_prof.set_xlabel('Hour of Day',           fontsize=11, fontweight='bold')
        ax_prof.set_ylabel('Mean rev/min per 30-min bin\n(mean±SEM)', fontsize=11, fontweight='bold')
        ax_prof.set_title('Pooled Daily Activity (Cohort 1,3,4; Days 8–21)',
                          fontsize=12, fontweight='bold')
        ax_prof.axvspan(18, 24, alpha=1.0, color=DARK_SPAN_COLOR, zorder=0)
        ax_prof.axvspan( 0,  6, alpha=1.0, color=DARK_SPAN_COLOR, zorder=0)
        ax_prof.grid(True, alpha=0.3, linestyle='--')
        ax_prof.legend(loc='best', fontsize=10, frameon=False)
        ax_prof.spines['top'].set_visible(False)
        ax_prof.spines['right'].set_visible(False)

        # ---- Panel 2 (MIDDLE): stacked actogram ----
        ax_act = fig_all.add_subplot(gs_all[1])
        y_off, ytick_pos, ytick_lbl = 0, [], []
        for is_snr_group in [True, False]:
            group_rows = [r for r in all_mouse_rows if r['is_snr'] == is_snr_group]
            for row in group_rows:
                max_act = max((np.max(row['day_arrays'][d]) for d in row['day_arrays']), default=1.0)
                n_plotted = 0
                for day in all_days:
                    if day not in row['day_arrays']:
                        continue
                    h_arr = row['day_arrays'][day]
                    norm  = h_arr / max_act * 0.8 if max_act > 0 else h_arr * 0
                    for i, bin_start in enumerate(ACTOGRAM_BIN_STARTS):
                        if norm[i] > 0:
                            ax_act.bar(bin_start, norm[i], bottom=y_off,
                                       width=ACTOGRAM_BIN_HOURS, align='edge',
                                       color=_blend_with_white(row['color'], 0.65), alpha=1.0, edgecolor='none')
                    y_off     += 1
                    n_plotted += 1
                if n_plotted:
                    ytick_pos.append(y_off - n_plotted / 2)
                    ytick_lbl.append(row['lbl'])
            if is_snr_group and ctrl_mouse_count > 0:
                ax_act.axhline(y_off, color='black', linewidth=1.5, linestyle='--', alpha=0.6)
                y_off += 0.5

        ax_act.set_xlim(0, 24)
        ax_act.set_ylim(0, y_off + 0.5)
        ax_act.set_xticks(np.arange(0, 25, 3))
        ax_act.set_yticks(ytick_pos)
        ax_act.set_yticklabels(ytick_lbl, fontsize=7)
        ax_act.set_xlabel('Time (hours)', fontsize=12, fontweight='bold')
        ax_act.set_ylabel('Mouse',        fontsize=12, fontweight='bold')
        ax_act.axvspan(18, 24, alpha=1.0, color=DARK_SPAN_COLOR, zorder=0)
        ax_act.axvspan( 0,  6, alpha=1.0, color=DARK_SPAN_COLOR, zorder=0)
        ax_act.grid(True, axis='x', alpha=0.3, linestyle='--')
        ax_act.set_title(
            f'Pooled Actogram',
            fontsize=13, fontweight='bold', pad=10)

        fig_all.tight_layout()
        out_path = f"./Pooled_Actogram.pdf"
        fig_all.savefig(out_path, dpi=300, bbox_inches='tight')
        fig_all.savefig(
            out_path.replace('.pdf', '.eps'),
            format='eps',
            facecolor='white',
            edgecolor='white',
            transparent=False
        )
        plt.close(fig_all)
        print(f"Saved pooled actogram: {out_path}")

        # ---- Second version: 48-hour double-plotted actogram ----
        fig_48 = plt.figure(figsize=(18, 14))
        gs_48 = fig_48.add_gridspec(2, 1, height_ratios=[2.4, 4.0], hspace=0.35)

        ax_prof48 = fig_48.add_subplot(gs_48[0])
        hours_x_48 = np.concatenate([ACTOGRAM_BIN_CENTERS, ACTOGRAM_BIN_CENTERS + 24])
        for pair_pool, col, grp_lbl in [
                (snr_48h_pool,  base_red,  f'SNr-DTA (n={snr_mouse_count} mice)'),
                (ctrl_48h_pool, base_blue, f'Control (n={ctrl_mouse_count} mice)')]:
            if not pair_pool:
                continue
            arr = np.array(pair_pool, dtype=float)
            mn48 = np.nanmean(arr, axis=0)
            sem48 = np.nanstd(arr, axis=0) / np.sqrt(len(pair_pool))
            ax_prof48.plot(hours_x_48, mn48, color=col, linewidth=2.5,
                           label=grp_lbl, marker='o', markersize=3)
            ax_prof48.fill_between(hours_x_48, mn48 - sem48, mn48 + sem48,
                                   alpha=1.0, color=_blend_with_white(col, 0.22), linewidth=0)
        for span_start, span_end in [(0, 6), (18, 30), (42, 48)]:
            ax_prof48.axvspan(span_start, span_end, alpha=1.0, color=DARK_SPAN_COLOR, zorder=0)
        ax_prof48.set_xlim(0, 48)
        ax_prof48.set_xticks(np.arange(0, 49, 6))
        ax_prof48.set_xlabel('Time (hours; true adjacent-day 48 h windows)', fontsize=11, fontweight='bold')
        ax_prof48.set_ylabel('Mean rev/min per 30-min bin\n(mean±SEM)', fontsize=11, fontweight='bold')
        ax_prof48.set_title('Pooled Daily Activity (Cohort 1,3,4; Days 8–21)', fontsize=12, fontweight='bold')
        ax_prof48.grid(True, alpha=0.3, linestyle='--')
        ax_prof48.legend(loc='best', fontsize=10, frameon=False)
        ax_prof48.spines['top'].set_visible(False)
        ax_prof48.spines['right'].set_visible(False)

        ax_act48 = fig_48.add_subplot(gs_48[1])
        y_off, ytick_pos, ytick_lbl = 0, [], []
        for is_snr_group in [True, False]:
            group_rows = [r for r in all_mouse_rows if r['is_snr'] == is_snr_group]
            for row in group_rows:
                max_act = max((np.max(row['day_arrays'][d]) for d in row['day_arrays']), default=1.0)
                n_plotted = 0
                for day in all_days:
                    if day not in row['day_arrays']:
                        continue
                    h_arr_1 = row['day_arrays'][day]
                    h_arr_2 = row['day_arrays'].get(day + 1, np.full(N_ACTOGRAM_BINS, np.nan))
                    pair_arr = np.concatenate([h_arr_1, h_arr_2])
                    norm = pair_arr / max_act * 0.8 if max_act > 0 else np.nan_to_num(pair_arr) * 0
                    bin_starts_48 = np.concatenate([ACTOGRAM_BIN_STARTS, ACTOGRAM_BIN_STARTS + 24])
                    for i, bin_start in enumerate(bin_starts_48):
                        if np.isfinite(norm[i]) and norm[i] > 0:
                            ax_act48.bar(bin_start, norm[i], bottom=y_off,
                                         width=ACTOGRAM_BIN_HOURS, align='edge',
                                         color=_blend_with_white(row['color'], 0.65), alpha=1.0, edgecolor='none')
                    y_off += 1
                    n_plotted += 1
                if n_plotted:
                    ytick_pos.append(y_off - n_plotted / 2)
                    ytick_lbl.append(row['lbl'])
            if is_snr_group and ctrl_mouse_count > 0:
                ax_act48.axhline(y_off, color='black', linewidth=1.5, linestyle='--', alpha=0.6)
                y_off += 0.5

        for span_start, span_end in [(0, 6), (18, 30), (42, 48)]:
            ax_act48.axvspan(span_start, span_end, alpha=1.0, color=DARK_SPAN_COLOR, zorder=0)
        ax_act48.set_xlim(0, 48)
        ax_act48.set_ylim(0, y_off + 0.5)
        ax_act48.set_xticks(np.arange(0, 49, 6))
        ax_act48.set_yticks(ytick_pos)
        ax_act48.set_yticklabels(ytick_lbl, fontsize=7)
        ax_act48.set_xlabel('Time (hours; 48 h double plot)', fontsize=12, fontweight='bold')
        ax_act48.set_ylabel('Mouse', fontsize=12, fontweight='bold')
        ax_act48.grid(True, axis='x', alpha=0.3, linestyle='--')
        ax_act48.set_title('Pooled Actogram, 48 h Double Plot', fontsize=13, fontweight='bold', pad=10)

        fig_48.tight_layout(rect=[0.03, 0.03, 0.98, 0.98])
        out_path_48 = f"./Pooled_Actogram_48h.pdf"
        fig_48.savefig(out_path_48, dpi=300, bbox_inches='tight')
        fig_48.savefig(
            out_path_48.replace('.pdf', '.eps'),
            format='eps',
            facecolor='white',
            edgecolor='white',
            transparent=False
        )
        plt.close(fig_48)
        print(f"Saved 48 h pooled actogram: {out_path_48}")

        messagebox.showinfo("Complete",
                            f"Pooled actograms saved to:\n{out_path}\n{out_path.replace('.pdf', '.eps')}\n"
                            f"{out_path_48}\n{out_path_48.replace('.pdf', '.eps')}\n\n"
                            f"Cohorts: {cohort_tag}\n"
                            f"SNr-DTA mice: {snr_mouse_count} | Control mice: {ctrl_mouse_count}")

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