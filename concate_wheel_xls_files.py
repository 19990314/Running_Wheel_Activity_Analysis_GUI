import pandas as pd
import os
from tkinter import filedialog, messagebox
from datetime import datetime


def concatenate_xls_files_by_date():
    """
    Read multiple XLS files, skip first 10 rows, and concatenate by date.
    Assumes the first column contains date/time information.
    """
    # Select multiple files
    file_paths = filedialog.askopenfilenames(
        title="Select XLS files to concatenate",
        filetypes=[("Excel Files", "*.xls *.xlsx"), ("All Files", "*.*")]
    )

    if not file_paths:
        print("No files selected.")
        return None

    print(f"Selected {len(file_paths)} files")

    all_dataframes = []

    # Read each file
    for i, file_path in enumerate(file_paths, 1):
        print(f"Processing file {i}/{len(file_paths)}: {os.path.basename(file_path)}")

        try:
            # Try reading with tab separator first
            try:
                df = pd.read_csv(file_path, skiprows=10, sep="\t")
            except Exception:
                # Fall back to normal CSV reading
                df = pd.read_csv(file_path, skiprows=10)

            # Drop completely empty rows and columns
            df = df.dropna(how='all').dropna(axis=1, how='all')

            # Clean column names
            df.columns = [col.strip() for col in df.columns]

            # Get the first column name (should contain dates)
            first_col = df.columns[0]
            print(f"  First column: {first_col}")

            # Convert first column to datetime
            df[first_col] = pd.to_datetime(df[first_col], errors='coerce')

            # Remove rows where date conversion failed
            before_count = len(df)
            df = df.dropna(subset=[first_col])
            after_count = len(df)

            if before_count > after_count:
                print(f"  Removed {before_count - after_count} rows with invalid dates")

            print(f"  Loaded {len(df)} rows")
            print(f"  Date range: {df[first_col].min()} to {df[first_col].max()}")

            all_dataframes.append(df)

        except Exception as e:
            print(f"  ERROR loading file: {e}")
            continue

    if not all_dataframes:
        messagebox.showerror("Error", "No files were successfully loaded.")
        return None

    # Concatenate all dataframes
    print("\nConcatenating dataframes...")
    merged_df = pd.concat(all_dataframes, ignore_index=True)

    # Get the first column name
    first_col = merged_df.columns[0]

    # Sort by date
    print("Sorting by date...")
    merged_df = merged_df.sort_values(by=first_col)

    # Remove duplicate timestamps (keep first occurrence)
    print("Removing duplicate timestamps...")
    before_dedup = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=first_col, keep='first')
    after_dedup = len(merged_df)

    if before_dedup > after_dedup:
        print(f"Removed {before_dedup - after_dedup} duplicate timestamps")

    # Summary
    print("\n" + "=" * 60)
    print("CONCATENATION SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {len(all_dataframes)}")
    print(f"Total rows: {len(merged_df)}")
    print(f"Date range: {merged_df[first_col].min()} to {merged_df[first_col].max()}")
    print(f"Columns: {list(merged_df.columns)}")
    print("=" * 60)

    # Ask user where to save
    output_path = filedialog.asksaveasfilename(
        title="Save concatenated file as",
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx"), ("All Files", "*.*")]
    )

    if output_path:
        # Save based on extension
        if output_path.endswith('.xlsx'):
            merged_df.to_excel(output_path, index=False)
        else:
            merged_df.to_csv(output_path, index=False)

        print(f"\nSaved to: {output_path}")
        messagebox.showinfo("Success", f"Concatenated file saved to:\n{output_path}")
    else:
        print("Save cancelled.")

    return merged_df


def concatenate_xls_files_by_date_no_gui(file_paths, output_path):
    """
    Non-GUI version: concatenate XLS files programmatically.

    Parameters:
    -----------
    file_paths : list of str
        List of file paths to concatenate
    output_path : str
        Path where to save the output file

    Returns:
    --------
    pandas.DataFrame
        The concatenated dataframe
    """
    all_dataframes = []

    for i, file_path in enumerate(file_paths, 1):
        print(f"Processing file {i}/{len(file_paths)}: {os.path.basename(file_path)}")

        try:
            # Try reading with tab separator first
            try:
                df = pd.read_csv(file_path, skiprows=10, sep="\t")
            except Exception:
                df = pd.read_csv(file_path, skiprows=10)

            # Clean up
            df = df.dropna(how='all').dropna(axis=1, how='all')
            df.columns = [col.strip() for col in df.columns]

            # Convert first column to datetime
            first_col = df.columns[0]
            df[first_col] = pd.to_datetime(df[first_col], errors='coerce')
            df = df.dropna(subset=[first_col])

            print(f"  Loaded {len(df)} rows")
            all_dataframes.append(df)

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    if not all_dataframes:
        raise ValueError("No files were successfully loaded")

    # Concatenate and sort
    merged_df = pd.concat(all_dataframes, ignore_index=True)
    first_col = merged_df.columns[0]
    merged_df = merged_df.sort_values(by=first_col)
    merged_df = merged_df.drop_duplicates(subset=first_col, keep='first')

    # Save
    if output_path.endswith('.xlsx'):
        merged_df.to_excel(output_path, index=False)
    else:
        merged_df.to_csv(output_path, index=False)

    print(f"\nSaved {len(merged_df)} rows to: {output_path}")
    return merged_df


# Standalone script version
if __name__ == "__main__":
    import tkinter as tk

    # Create a simple GUI window
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Run the concatenation
    result = concatenate_xls_files_by_date()

    if result is not None:
        print("\nFirst few rows:")
        print(result.head())
        print("\nDataframe info:")
        print(result.info())