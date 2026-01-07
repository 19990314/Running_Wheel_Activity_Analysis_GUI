import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
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
        self.reference_date = date(2025, 7, 22)
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
        tk.Button(self.main_frame, text="Daily Data Visualization", command=self.plot_data).grid(row=3, column=0, pady=10)
        tk.Button(self.main_frame, text="Across-Mice Box Plot", command=self.plot_violin).grid(row=3, column=1, pady=10)
        tk.Button(self.main_frame, text="Save Plots", command=self.save_plots).grid(row=3, column=2, pady=10)

        tk.Label(self.main_frame, text="Input: xx\n output: oo\n").grid(row=4, column=0)
        tk.Label(self.main_frame, text="===========================\n").grid(row=4, column=1)
        tk.Label(self.main_frame, text="+++++++++++++++++++++++++++++++++++++\n").grid(row=4, column=2)

        # button row 2
        tk.Button(self.main_frame, text="Activity Summary Over Time", command=self.activity_summary_over_time).grid(row=5, column=0, pady=10)
        tk.Button(self.main_frame, text="Mice Activity Comparison", command=self.activity_comparison_each_day).grid(row=5, column=1, pady=10)
        tk.Button(self.main_frame, text="Bunch Save", command=self.bunch_save).grid(row=5, column=2, pady=10)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: one plot summarizing total distance that each mouse run on each day\n").grid(row=6, column=0)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: pdf, one page per day, distance on y axis and timeline on x\n").grid(row=6, column=1)
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
        tk.Button(self.main_frame, text="Hist Video", command=self.video_saving).grid(row=13, column=2, pady=10)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: 2 Bar Plots (l:ctr vs SNr vs GPi; r: ctr vs ctr vs SNc)\n").grid(row=14, column=0)
        tk.Label(self.main_frame, text="Input: file(s)\n Output: \n").grid(row=14, column=1)
        tk.Label(self.main_frame, text="---\n").grid(row=14, column=2)

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
        self.file_path = filedialog.askopenfilename(filetypes=[("Data Files", "*.csv *.xls")])
        if self.file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, self.file_path)
            self.load_dataframe()
        # plots
        self.plots = []
        self.plot_activity_comparison()
        self.generate_plots()
        self.plot_violin()
        print("tedst")

        #self.df.iloc[:, :3].to_excel("for_plot_test_m1_d12.xlsx", index=False)
        #self.df.iloc[:, :3].to_csv("for_plot_test_m1_d12.csv", index=False)


    def select_output_path(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")])
        if path:
            self.output_path.set(path)

    def load_dataframe(self):
        try:
            if self.file_path.endswith(".xls"):
                try:
                    df = pd.read_csv(self.file_path, skiprows=9, sep="\t")
                except Exception:
                    df = pd.read_csv(self.file_path, skiprows=9)
            elif self.file_path.endswith(".csv"):
                df = pd.read_csv(self.file_path, skiprows=9)
            else:
                raise ValueError("Unsupported file format")

            df = df.dropna(how='all')
            df = df.dropna(axis=1, how='all')
            df.columns = [col.strip() for col in df.columns]
            if 'Bin' not in df.columns:
                raise ValueError("Missing 'Bin' column")

            mouse_ids = sorted(set(col.split()[2] for col in df.columns if col.startswith('1 8')))
            self.mouse_ids = mouse_ids
            self.num_mice = len(mouse_ids)

            df['Bin'] = pd.to_datetime(df['Bin'], errors='coerce')
            self.date = df['Bin'].iloc[0].date()
            self.date_number = (self.date - self.reference_date).days

            for col in df.columns:
                if col != 'Bin':
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna(subset=['Bin'])
            df = df.dropna(axis=1, how='all')
            self.df = df

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def plot_data(self):
        if self.plots:
            self.show_plot(2)
        else:
            messagebox.showinfo("No Plots", "No mouse data found to plot.")

    def plot_data2(self):
        if self.plots:
            self.show_plot(8)
        else:
            messagebox.showinfo("No Plots", "No mouse data found to plot.")

    def generate_plots(self):
        mouse_label = ["Control", "SNr DTA", "GPi DTA", "DTA Control 1", "DTA Control 2", "DTA DAT"]

        for mid in self.mouse_ids:
            fig, ax1 = plt.subplots(figsize=(8, 4))
            rev_col = f'1 8 {mid} rev'
            km_col = f'1 8 {mid} km'

            if self.rev_var.get() and rev_col in self.df.columns:
                ax1.scatter(self.df['Bin'], self.df[rev_col], color='tab:blue', label='Revolutions', s=10)
                ax1.set_ylabel('Revolutions', color='tab:blue')
                ax1.tick_params(axis='y', labelcolor='tab:blue')
            else:
                ax1.set_ylabel('')

            if self.km_var.get() and km_col in self.df.columns:
                ax2 = ax1.twinx()

                # change v1
                ax2.bar(self.df['Bin'], self.df[km_col]*1000, color='tab:orange', label='Distance', width=0.001)
                ax2.set_ylabel('Distance (m)', color='tab:orange')
                ax2.tick_params(axis='y', labelcolor='tab:orange')

                # v2
                #times = self.df['Bin']
                #print(times.head())
                #distances = self.df[km_col].fillna(0)

                # Bar plot
                #ax2.bar(times, distances, width=2, align='center', alpha=0.5, color='tab:orange')

                #ax2.set_ylabel('Distance per Interval (km)', color='tab:orange')
                #ax2.tick_params(axis='y', labelcolor='tab:orange')

                # Format x-axis to show only HH:MM:SS
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                ax1.set_xlabel('Time')

            ax1.set_xlabel('Time')
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            #plt.title(f'Mouse {mid} Activity Over Time')
            if int(mid) < 4:
                plt.title(f'D{self.date_number} - Daily Activity - {mouse_label[int(mid) - 1]}')
            else:
                plt.title(f'D{self.date_number} - Daily Activity - {mouse_label[int(mid) - 2]}')
            fig.tight_layout()
            plt.xticks(rotation=45)
            plt.grid(True)

            self.plots.append((fig, mid))

    def plot_violin(self):
        if self.df is None:
            self.load_dataframe()

        df = self.df
        threshold = 2

        for mid in self.mouse_ids:
            col = f'1 8 {mid} rev'
            if col in self.df.columns:
                # Step 1: Zero out low values
                df[col] = df[col].where(df[col] >= threshold, 0)

                # Step 2: Find consecutive non-zero regions (bouts)
                is_active = df[col] > 0
                bout_id = (is_active != is_active.shift()).cumsum()
                bout_means = {}

                for i, group in df.groupby(bout_id):
                    if group[col].iloc[0] > 0:  # Only process active bouts
                        mean_val = group[col].mean()
                        df.loc[group.index, col] = mean_val

        mouse_label = ["Control", "SNr DTA", "GPi DTA", "DTA Control 1", "DTA Control 2", "DTA DAT"]

        for mid in self.mouse_ids:
            fig, ax = plt.subplots(figsize=(8, 4))
            rev_col = f'1 8 {mid} rev'
            km_col = f'1 8 {mid} km'

            if self.rev_var.get() and rev_col in df.columns:
                ax.plot(df['Bin'], df[rev_col],color='tab:orange', label='bout')
                ax.set_ylabel('Bouts', color='tab:blue')
                ax.tick_params(axis='y', labelcolor='tab:blue')
            else:
                ax.set_ylabel('')
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                ax.set_xlabel('Time')

            ax.set_xlabel('Time')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            # plt.title(f'Mouse {mid} Activity Over Time')
            if int(mid) < 4:
                plt.title(f'D{self.date_number} - Daily Activity* - {mouse_label[int(mid) - 1]}')
            else:
                plt.title(f'D{self.date_number} - Daily Activity* - {mouse_label[int(mid) - 2]}')
            fig.tight_layout()
            plt.xticks(rotation=45)
            plt.grid(True)

            fig.savefig(f"bouts-{mid}.png")
            #self.plots.append((fig, mid))

    def plot_activities_for_dayindex(self, day, df):
        mouse_label = ["Control", "SNr DTA", "GPi DTA", "DTA Control 1", "DTA Control 2", "DTA DAT"]

        fig, ax = plt.subplots(figsize=(10, 5))
        for mid in self.mouse_ids:
            km_col = f'1 8 {mid} km'
            if km_col in df.columns:
                smoothed = df[km_col].interpolate().rolling(window=15, min_periods=1, center=True).mean()
                df['Smoothed'] = smoothed  # keep the smoothed values with the df
                df = df.sort_values(by='Bin')  # ensure proper x order
                if int(mid) < 4:
                    ax.plot(df['Bin'], df['Smoothed'], label=mouse_label[int(mid) - 1])
                else:
                    ax.plot(df['Bin'], df['Smoothed'], label=mouse_label[int(mid) - 2])

        ax.set_xlabel("Time")
        ax.set_ylabel("Distance (km)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.title(f"Day {day} - Activity Comparison across Mice")
        plt.xticks(rotation=45)
        plt.grid(True)
        ax.legend()

        for widget in self.canvas_area.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        return fig


    def activity_comparison_each_day(self):
        merged_df = self.assemble_files()
        # Mouse label mapping
        mouse_label = ["Control", "SNr DTA", "GPi DTA", "DTA Control 1", "DTA Control 2", "DTA DAT"]

        filenames = [f"D1-D{self.dayrange}_activity_levels_each_day_allmice.pdf", f"D1-D{self.dayrange}_activity_levels_each_day_ctr_GPi_SN.pdf", f"D1-D{self.dayrange}_activity_levels_each_day_ctr_ctr_SNc.pdf"]
        for i in range(0,3):
            if i == 0:
                self.mouse_ids = [1, 2, 3, 5, 6, 7]
            elif i == 1:
                self.mouse_ids = [1, 2, 3]
            elif i == 2:
                self.mouse_ids = [5, 6, 7]

            with PdfPages(filenames[i]) as pdf:
                # Loop through each day
                for day, day_df in merged_df.groupby('DateIndex'):
                    if (i == 0) and (int(day) <8):
                        self.mouse_ids = [1, 2, 3]
                    elif (i == 0) and (int(day) >7):
                        self.mouse_ids = [1, 2, 3, 5, 6, 7]
                    fig = self.plot_activities_for_dayindex(day, day_df)
                    pdf.savefig(fig)
                    plt.close(fig)


    def activity_summary_over_time(self):
        activity_records = {}
        merged_df = self.assemble_files()
        mouse_label = ["Control", "SNr DTA", "GPi DTA", "DTA Control 1", "DTA Control 2", "DTA DAT"]

        for day, df in merged_df.groupby('DateIndex'):
                df.columns = [col.strip() for col in df.columns]
                if 'Bin' not in df.columns:
                    continue

                df['Bin'] = pd.to_datetime(df['Bin'], errors='coerce')
                df = df.dropna(subset=['Bin'])
                df = df.dropna(axis=1, how='all')

                mouse_ids = sorted(set(col.split()[2] for col in df.columns if col.startswith('1 8')))
                for mid in mouse_ids:
                    km_col = f'1 8 {mid} km'
                    #duration_hours = (df['Bin'].iloc[-1] - df['Bin'].iloc[0]).total_seconds() / 3600
                    if km_col in df.columns:
                        km = pd.to_numeric(df[km_col], errors='coerce')
                        total_km = km.sum()
                        activity_records.setdefault(mid, []).append((day, total_km))

        filenames = [f"D1-D{day}_activity_levels_allmice", f"D1-D{day}_activity_levels_ctr_GPi_SNr", f"D1-D{day}_activity_levels_ctr_ctr_SNc"]
        for i in range(0,3):
            fig, ax = plt.subplots(figsize=(13, 6))
            for mid, records in activity_records.items():
                records = sorted(records, key=lambda x: x[0])
                days = ["D"+str(r[0]) for r in records]
                values = [r[1] for r in records]
                if int(mid) < 4:
                    if i ==2:
                        continue
                    ax.plot(days, values, label=mouse_label[int(mid)-1], marker='o')
                else:
                    if i ==1:
                        continue
                    ax.plot(days, values, label=mouse_label[int(mid)-2], marker='o')

            ax.set_xlabel("Date")
            ax.set_ylabel("Distance run from 00:00 to 24:00 (km)")
            plt.title("Activity Level Over Time")
            plt.xticks(rotation=45)
            #plt.grid(True)
            ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
            ax.legend()
            fig.savefig(filenames[i])

        for widget in self.canvas_area.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)



    def assemble_files(self):
        file_paths = filedialog.askopenfilenames(title="Select multiple day files", filetypes=[("Data Files", "*.csv *.xls")])
        if not file_paths:
            return

        map_dates_activities = {}
        df_assembled = []

        for file_path in file_paths:
            try:
                if file_path.endswith(".xls"):
                    try:
                        df = pd.read_csv(file_path, skiprows=9, sep="\t")
                    except Exception:
                        df = pd.read_csv(file_path, skiprows=9)
                elif file_path.endswith(".csv"):
                    df = pd.read_csv(file_path, skiprows=9)
                else:
                    continue
                if file_path == "/Users/chen/Downloads/wheel_data/20250818-19_170137.xls":
                    print("haha")
                df = df.dropna(axis=1, how='all')
                df = df.dropna(how="any")
                df.columns = [col.strip() for col in df.columns]

                if 'Bin' not in df.columns:
                    continue
                df['Bin'] = pd.to_datetime(df['Bin'],format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
                df = df.fillna(0)
                df = df[df['Bin'] != 0]
                date_list = []
                day_idx = []
                for _, row in df.iterrows():
                    try:
                        date_list.append(row['Bin'].date())
                        day_idx.append((row['Bin'].date() - self.reference_date).days)
                    except Exception:
                        print(_)
                        print(row)
                        continue

                df['Date'] = date_list
                df['DateIndex'] = day_idx
                if df['Bin'].iloc[0] == df['Bin'].iloc[-1]:
                    df = df.iloc[:-1]
                df = df.sort_values(by='Bin')

                mask = pd.Series(False, index=df.index)
                for start, end in self.time_ranges:
                    mask |= df['Bin'].between(start, end)

                # Set all columns (except 'Bin') to 0 where the mask is True
                cols_to_zero = [col for col in df.columns if col != 'Bin' and col != 'DateIndex']
                df.loc[mask, cols_to_zero] = 0

                df_assembled.append(df)
            except Exception as e:
                print(e)

        # merge files
        merged_df = pd.concat(df_assembled, ignore_index=True)
        #merged_df = merged_df.fillna(0)

        #merged_df = pd.concat([merged_df, new_df], ignore_index=True)
        #merged_df = merged_df.sort_values(by='Bin').reset_index(drop=True)

        rev_cols = [col for col in merged_df.columns if col.endswith("rev")]
        max_rev_value = merged_df[rev_cols].max().max()
        self.dayrange = max(merged_df['DateIndex'])
        merged_df = merged_df.drop_duplicates(subset='Bin', keep='first')

        print("Max rev across all mice:", max_rev_value)
        return merged_df

    def hist_bouts_ct_per_min(self, circadian = "NA"):
        merged_df = self.assemble_files()
        # Mouse label mapping
        mouse_label = ["Control", "SNr DTA", "GPi DTA", "DTA Control 1", "DTA Control 2", "DTA DAT"]

        filename = "histograms_bout_count_each_day.pdf"
        sufix = ""
        if circadian == "day":
            merged_df = pd.DataFrame([x for i, x in merged_df.iterrows() if x['Bin'].hour >= 6 and x['Bin'].hour < 18])
            filename = "histograms_bout_count_each_day_(daytime).pdf"
            sufix = " - Daytime (6:00 - 18:00)"
        elif circadian == "night":
            merged_df = pd.DataFrame([x for i, x in merged_df.iterrows() if x['Bin'].hour >= 18 or x['Bin'].hour < 6])
            filename = "histograms_bout_count_each_day_(nighttime).pdf"
            sufix = " - Nighttime (18:00 - 06:00)"

        # Loop through each day
        with PdfPages(filename) as pdf:
            # Loop through each day
            for day, day_df in merged_df.groupby('DateIndex'):
                if day > 7:
                    self.mouse_ids = [1, 2, 3, 5, 6, 7]
                else:
                    self.mouse_ids = [1, 2, 3]

                fig, axes = plt.subplots(len(self.mouse_ids), 1, figsize=(8, 3 * len(self.mouse_ids)), sharex=True)
                fig.suptitle(f"Revolution counts/min Histogram - D{day}" + sufix)

                if len(self.mouse_ids) == 1:  # Handle case of 1 mouse
                    axes = [axes]

                # Loop through each mouse column
                for ax, mid in zip(axes, self.mouse_ids):
                    rev_col = f'1 8 {mid} rev'
                    if rev_col in day_df.columns:
                        counts, bins, patches = ax.hist(day_df[rev_col][(day_df[rev_col] != 0) & day_df[rev_col].notna()], range=(0, 160), bins=20, alpha=0.7, edgecolor='black')

                        # Title for each mouse
                        if int(mid) < 4:
                            ax.set_title(mouse_label[int(mid) - 1])
                        else:
                            ax.set_title(mouse_label[int(mid) - 2])

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
        merged_df = self.assemble_files()
        filename = "histograms_bout_duration_each_day.pdf"
        sufix = ""
        if circadian == "day":
            merged_df = pd.DataFrame([x for i, x in merged_df.iterrows() if x['Bin'].hour >= 6 and x['Bin'].hour < 18])
            filename = "histograms_bout_duration_each_day_(daytime).pdf"
            sufix = "\nDaytime (6:00 - 18:00)"
        elif circadian == "night":
            merged_df = pd.DataFrame([x for i, x in merged_df.iterrows() if x['Bin'].hour >= 18 or x['Bin'].hour < 6])
            filename = "histograms_bout_duration_each_day_(nighttime).pdf"
            sufix = "\nNighttime (18:00 - 06:00)"
        # Mouse label mapping
        mouse_label = ["Control", "SNr DTA", "GPi DTA", "DTA Control 1", "DTA Control 2", "DTA DAT"]

        # each day
        with PdfPages(filename) as pdf:
            # Loop through each day
            for day, day_df in merged_df.groupby('DateIndex'):
                print(f"Day{day} start")
                if day > 7:
                    self.mouse_ids = [1, 2, 3, 5, 6, 7]
                else:
                    self.mouse_ids = [1, 2, 3]
                fig, axes = plt.subplots(len(self.mouse_ids), 1, figsize=(8, 3 * len(self.mouse_ids)), sharex=True)
                fig.suptitle(f"Bout Duration Histograms - D{day}" + sufix)

                if len(self.mouse_ids) == 1:  # Handle case of 1 mouse
                    axes = [axes]

                # Loop through each mouse column
                max_rev = []
                for ax, mid in zip(axes, self.mouse_ids):
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
                            if day <=7 and mid >4:
                                continue
                            counts, bins, patches = ax.hist(bl, range=(0, 50), bins=50, alpha=0.7, edgecolor='black')
                        ax.grid(axis='y', linestyle='--', alpha=1)

                        max_rev.append(max(counts))
                        # Title for each mouse
                        if int(mid) < 4:
                            ax.set_title(mouse_label[int(mid) - 1])
                        else:
                            if day > 7:
                                ax.set_title(mouse_label[int(mid) - 2])

                        # Label axes
                        ax.set_ylabel("Count")
                        ax.set_xlabel("Bout Duration(min)")
                        ax.set_xlim(1, 50)
                        ax.set_xticks(np.arange(1, 51, 2))
                        fig.tight_layout()

                        # Add grid for readability
                        ax.grid(axis='y', linestyle='--', alpha=0.6)

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
        self.mouse_ids = [1, 2, 3, 5, 6, 7]
        mouse_label = ["Control", "SNr DTA", "GPi DTA", "DTA Control 1", "DTA Control 2", "DTA DAT"]
        merged_df = self.assemble_files()
        sufix = ""
        filename = "histograms_bout_duration_each_mouse.pdf"
        if circadian == "day":
            merged_df = pd.DataFrame([x for i, x in merged_df.iterrows() if x['Bin'].hour >= 6 and x['Bin'].hour < 18])
            filename = "histograms_bout_duration_each_mouse_(daytime).pdf"
            sufix = "\nDaytime (6:00 - 18:00)"
        elif circadian == "night":
            merged_df = pd.DataFrame([x for i, x in merged_df.iterrows() if x['Bin'].hour >= 18 or x['Bin'].hour < 6])
            filename = "histograms_bout_duration_each_mouse_(nighttime).pdf"
            sufix = "\nNighttime (18:00 - 06:00)"

        # clean up
        merged_df = merged_df.dropna(how='all').dropna(axis=1, how='all')

        # gather/lock the list of days (sorted)
        if 'DateIndex' not in merged_df.columns:
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
            for mid in self.mouse_ids:
                # count how many subplots we will actually show (some days may be skipped)
                valid_days = []
                rev_max = []
                for day in days:
                    # Apply your rule: on Day <=7, skip mice >4 (i.e., DTAs)
                    if day <= 7 and int(mid) > 4:
                        continue
                    # Only include if the column exists for this mouse on this day
                    rev_col = f'1 8 {mid} rev'
                    day_df = merged_df.loc[merged_df['DateIndex'] == day]
                    if rev_col in day_df.columns and not day_df.empty:
                        valid_days.append(day)

                # If nothing to plot for this mouse, still put a note page
                if not valid_days:
                    fig, ax = plt.subplots(figsize=(8, 3))
                    if int(mid) < 4:
                        mtitle = mouse_label[int(mid) - 1]
                    else:
                        mtitle = mouse_label[int(mid) - 2]
                    ax.text(0.5, 0.5, f"No bouts to plot for {mtitle}", ha='center', va='center',
                            transform=ax.transAxes)
                    ax.axis('off')
                    fig.suptitle(f"Bout Duration Histogram — {mtitle}" + sufix)
                    pdf.savefig(fig)
                    plt.close(fig)
                    continue

                # Make one figure with a row per day
                n_rows = len(valid_days)
                fig, axes = plt.subplots(n_rows, 1, figsize=(8, 2.5 * n_rows), sharex=True)
                if n_rows == 1:
                    axes = [axes]

                # Figure title: mouse name
                if int(mid) < 4:
                    mtitle = mouse_label[int(mid) - 1]
                else:
                    mtitle = mouse_label[int(mid) - 2]
                fig.suptitle(f"Bout Duration Histograms — {mtitle}"+ sufix)

                # ----- iterate over DAYS (one subplot per day) -----
                for ax, day in zip(axes, valid_days):
                    day_df = merged_df.loc[merged_df['DateIndex'] == day]
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

        # Nice labels
        label_map = {
            1: "Control", 2: "SNr DTA", 3: "GPi DTA",
            5: "DTA Control 1", 6: "DTA Control 2", 7: "DTA DAT"
        }

        records = []
        # Group by day
        for day, day_df in merged_df.groupby('DateIndex'):
            for mid in self.mouse_ids:
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
                    'MouseLabel': label_map.get(mid, f"Mouse {mid}"),
                    'Day': int(day),
                    'MinutesOnWheel': minutes_on,
                    'MinutesOnWheel_day': sum(intervals_day),
                    'MinutesOnWheel_night': sum(intervals_night)
                })

        if not records:
            raise ValueError("No time-on-wheel data computed. Check columns and threshold.")
        return pd.DataFrame(records)


    def plot_time_on_or_not_on_wheel(self, df, threshold = 0, save_path="time_on_wheel_summary.pdf", state = "on", notes = "", circadian=False):
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
            if notes==" *D1,D8 removed":
                df = df[df["Day"] != 1]
                df = df[df["Day"] != 8]
            fig.suptitle(f"Time NOT on Wheel (mean ± SEM)" + notes, y=0.98, fontsize=16)
            start_axes.set_ylabel("Minutes not on wheel per day")


        # Panels/groups
        groupA = [1, 2, 3]
        groupB = [5, 6, 7]

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
            groups = [(axes[0][0], GA, "Mice 1–3"), (axes[0][1], GB, "Mice 5–7"), (axes[1][0], GC, "Mice 1–3"), (axes[1][1], GD, "Mice 5–7"), (axes[2][0], GE, "Mice 1–3"), (axes[2][1], GF, "Mice 5–7")]
        else:
            groups = [(axes[0], GA, "Mice 1–3"), (axes[1], GB, "Mice 5–7")]

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
            ax.bar(x, means, yerr=sems, capsize=4, lw=1.2, edgecolor=bar_edge,
                   color=bar_face, width=0.6, error_kw=dict(lw=1.2))
            # overlay individual points (jittered)
            for i, (mid, label, _, _, _) in enumerate(rows):
                if mid > 3:
                    temp_df = df[df['Day'] >7]
                else:
                    temp_df = df
                if stop_ct <2:
                    pts = temp_df[temp_df['MouseID'] == mid]['MinutesOnWheel'].to_numpy(dtype=float)
                elif stop_ct >=2 and stop_ct <4:
                    pts = temp_df[temp_df['MouseID'] == mid]['MinutesOnWheel_day'].to_numpy(dtype=float)
                else:
                    pts = temp_df[temp_df['MouseID'] == mid]['MinutesOnWheel_night'].to_numpy(dtype=float)
                pts = pts[pts > 0]

                if pts.size == 0:
                    continue
                jitter = rng.normal(0, 0.06, size=pts.size)
                ax.scatter(np.full_like(pts, i, dtype=float) + jitter,
                           pts, s=24, color=point_col, alpha=0.85, zorder=3, linewidths=0.2, edgecolors="#000000")

            # styling
            ax.set_xticks(x)
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
        if save_path:
            if save_path.lower().endswith(".pdf"):
                with PdfPages(save_path) as pdf:
                    pdf.savefig(fig, bbox_inches="tight")
                    plt.close(fig)
            else:
                fig.savefig(save_path, dpi=300, bbox_inches="tight")
                plt.close(fig)

    def plot_time_on_wheel_summary(self, save_path="time_on_wheel_summary.pdf"):
        #merged_df = self.assemble_files()
        #self.plot_time_on_or_not_on_wheel(merged_df, threshold=0, save_path="time_on_wheel_summary0.jpg")
        #self.plot_time_on_or_not_on_wheel(merged_df, threshold=2, save_path="time_on_wheel_summary0.pdf")
        #self.plot_time_on_or_not_on_wheel(merged_df, threshold=5, save_path="time_on_wheel_summary4.pdf")
        #self.plot_time_on_or_not_on_wheel(merged_df, threshold=10, save_path="time_on_wheel_summary6.pdf")
        #self.plot_time_on_or_not_on_wheel(merged_df, threshold=15, save_path="time_on_wheel_summary1.pdf")
        #self.plot_time_on_or_not_on_wheel(merged_df, threshold=20, save_path="time_on_wheel_summary5.pdf")


        #not
        #self.plot_time_on_or_not_on_wheel(merged_df, threshold=1, save_path="time_not_on_wheel_D1-22.jpg",state = "off", notes = "")
        merged_df = self.assemble_files()
        self.plot_time_on_or_not_on_wheel(merged_df, threshold=1, save_path="time_not_on_wheel_D1-26_circadian.jpg",state = "off", notes = " *D1,D8 removed",circadian=True)
        self.plot_time_on_or_not_on_wheel(merged_df, threshold=1, save_path="time_on_wheel_D1-26_circadian.jpg",state = "on", circadian=True)



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
        Build two figures, each with 2 subplots side-by-side:

          Fig A (Group 1: mice 1–3):
             • Left  = Days 8–14
             • Right = Days 15–21

          Fig B (Group 2: mice 5–7):
             • Left  = Days 15–21
             • Right = Days 22–28

        Curves are mean ± SEM across days, aligned to minute of day (0..1439).
        Y-axis: meters per minute (m/min).
        """
        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        from tkinter import filedialog, messagebox
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

        # --- file selection ---
        file_paths = filedialog.askopenfilenames(
            title="Select daily files covering Days 8–28",
            filetypes=[("Data Files", "*.csv *.xls *.tsv")]
        )
        if not file_paths:
            return

        # --- groups & labels ---
        group1 = [1, 2, 3]  # (8–14) vs (15–21)
        group2 = [5, 6, 7]  # (15–21) vs (22–28)
        label_map = {1: "Control", 2: "SNr DTA", 3: "GPi DTA", 5: "DTA Control 1", 6: "DTA Control 2", 7: "DTA DAT"}

        # storage: per mouse -> arrays + corresponding day indices
        per_mouse_arrays = {m: [] for m in group1 + group2}
        per_mouse_days = {m: [] for m in group1 + group2}

        # robust reader
        def _read_one(path):
            if path.endswith(".xls") or path.endswith(".tsv"):
                try:
                    return pd.read_csv(path, skiprows=9, sep="\t")
                except:
                    return pd.read_csv(path, skiprows=9)
            elif path.endswith(".csv"):
                return pd.read_csv(path, skiprows=9)
            else:
                return pd.read_csv(path, skiprows=9, sep=None, engine="python")

        # reference date (must be set earlier in your app)
        ref = getattr(self, "reference_date", None)
        if ref is None:
            messagebox.showerror("Error", "self.reference_date (datetime.date) is not set.")
            return
        ref = pd.to_datetime(ref)

        minute_index = pd.Index(np.arange(1440), name="MinuteOfDay")
        any_rows = False

        # --- ingest files ---
        for path in file_paths:
            try:
                df = _read_one(path)
                if df is None or df.empty:
                    continue
                df.columns = [str(c).strip() for c in df.columns]
                if "Bin" not in df.columns:
                    cand = [c for c in df.columns if str(c).lower() == "bin"]
                    if not cand:
                        continue
                    df = df.rename(columns={cand[0]: "Bin"})
                df["Bin"] = pd.to_datetime(df["Bin"], errors="coerce")
                df = df.dropna(subset=["Bin"])
                if df.empty:
                    continue
                any_rows = True

                # compute the day index (integer) from reference date (by date only)
                day_index_series = (df["Bin"].dt.normalize() - ref).dt.days
                if day_index_series.empty:
                    continue
                # use the modal day index in this file
                di = int(day_index_series.mode().iloc[0])

                # minute-of-day index for alignment
                mod = df["Bin"].dt.hour * 60 + df["Bin"].dt.minute

                # per-mouse daily vectors
                for mid in (group1 + group2):
                    km_col = f"1 8 {mid} km"
                    if km_col not in df.columns:
                        continue
                    vals = pd.to_numeric(df[km_col], errors="coerce")
                    day_series = pd.Series(vals.values, index=mod.values, dtype="float64")
                    day_series = day_series.groupby(day_series.index).mean()
                    day_series = day_series.reindex(minute_index, fill_value=np.nan)
                    y = (day_series * 1000.0).to_numpy()  # meters per minute
                    y_s = smooth_1d_local(y, window=31, polyorder=2)
                    # normalized
                    #y_s = (y_s / np.nanmax(y_s)) *100
                    per_mouse_arrays[mid].append(y_s)
                    per_mouse_days[mid].append(di)
            except Exception as e:
                print(f"Failed to process {path}: {e}")

        if not any_rows:
            messagebox.showinfo("No Data", "No valid rows found in the selected files.")
            return

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
        def plot_group_two_weeks(group, week1, week2, title):
            """
            group: list of mouse IDs
            week1: (lo, hi)
            week2: (lo, hi)
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
                for mid in group:
                    # pick days within the range for this mouse
                    stacks = [arr for arr, di in zip(per_mouse_arrays[mid], per_mouse_days[mid]) if lo <= di <= hi]
                    if not stacks:
                        continue
                    m, s = mean_sem(stacks)
                    if m is None:
                        continue
                    line, = ax.plot(x, m, linewidth=1.8, label=label_map.get(mid, f"Mouse {mid}"))
                    ax.fill_between(x, m - s, m + s, alpha=0.25, linewidth=0, color=line.get_color())
                ax.set_title(f"{subtitle}", pad=8)
                ax.set_xlim(0, 1440)
                ax.set_xticks(tick_minutes)
                ax.set_xticklabels(tick_labels)
                ax.grid(axis="y", linestyle="--", alpha=0.35)
                ax.set_axisbelow(True)
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
            #normalize
            axes[0].set_ylabel("Speed (m/min)")
            #axes[0].set_ylabel("normalized speed (%)")
            axes[1].legend(loc="lower right", frameon=False)
            fig.suptitle(title, fontsize=15, y=0.99)
            fig.tight_layout(rect=[0, 0, 1, 0.96])
            return fig

        # --- build the two figures per your ranges ---
        #normalized
        figA = plot_group_two_weeks(group1, week1=(8, 14), week2=(15, 21), title="Temporal Activity")
        figB = plot_group_two_weeks(group2, week1=(15, 21), week2=(22, 28), title="Temporal Activity")

        # --- show Fig A in Tk canvas (swap to figB if you prefer)
        for w in self.canvas_area.winfo_children():
            w.destroy()
        canvas = FigureCanvasTkAgg(figA, master=self.canvas_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Optional: save both
        # normalized
        figA.savefig("temporal_activity_group1_w2vs3.png", bbox_inches="tight")
        figB.savefig("temporal_activity_group2_w2vs3.png", bbox_inches="tight")

    def bunch_save(self):
        file_paths = filedialog.askopenfilenames(title="Select multiple day files",
                                                 filetypes=[("Data Files", "*.csv *.xls")])
        if not file_paths:
            return

        for file_path in file_paths:
            self.file_path = file_path
            if self.file_path:
                self.file_entry.delete(0, tk.END)
                self.file_entry.insert(0, self.file_path)
                self.load_dataframe()
            # plots
            self.plots = []
            self.plot_activity_comparison()
            self.generate_plots()
            self.save_plots()

    def show_plot(self, index):
        for widget in self.canvas_area.winfo_children():
            widget.destroy()
        if 0 <= index < len(self.plots):
            fig, _ = self.plots[index]
            canvas = FigureCanvasTkAgg(fig, master=self.canvas_area)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            self.current_index = index

    def show_next_plot(self):
        if self.current_index + 1 < len(self.plots):
            self.show_plot(self.current_index + 1)

    def show_prev_plot(self):
        if self.current_index - 1 >= 0:
            self.show_plot(self.current_index - 1)

    def update_plots(self):
        if self.df is not None:
            self.generate_plots()
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


if __name__ == "__main__":
    root = tk.Tk()
    app = MouseActivityApp(root)
    root.mainloop()