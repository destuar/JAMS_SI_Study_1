import os
import pandas as pd
from datetime import datetime
import sys

def parse_datetime_from_filename(filename):
    """Parses datetime object from filename like MM_DD_YY_HHMM[AM|PM].csv"""
    base_name = filename.replace('.csv', '')
    # Handle potential variations if necessary, currently expects exact format
    try:
        # Define the format string including AM/PM
        format_string = "%m_%d_%y_%I%M%p" 
        dt_object = datetime.strptime(base_name, format_string)
        return dt_object
    except ValueError as e:
        print(f"Error parsing date from filename '{filename}': {e}. Skipping file.", file=sys.stderr)
        return None

def aggregate_csvs(company_name_filter, derived_data_dir, output_filename):
    """Aggregates CSVs from derived_data_dir matching company_name_filter, sorted by date."""
    if not os.path.isdir(derived_data_dir):
        print(f"Error: Derived data directory '{derived_data_dir}' not found.", file=sys.stderr)
        return

    csv_files_with_dates = []
    print(f"Scanning '{derived_data_dir}' for CSV files matching '{company_name_filter}*'...")
    for filename in os.listdir(derived_data_dir):
        # Match files starting with the company name and ending with .csv
        if filename.lower().startswith(company_name_filter.lower() + "_") and filename.lower().endswith('.csv'):
            full_path = os.path.join(derived_data_dir, filename)
            if os.path.isfile(full_path):
                # Extract the date part of the filename (after company_ prefix)
                date_part = filename[len(company_name_filter)+1:] # Get part after "CompanyName_"
                parsed_date = parse_datetime_from_filename(date_part)
                if parsed_date:
                    csv_files_with_dates.append((full_path, parsed_date))
                else:
                    print(f"Could not parse date from date part of {filename}, skipping.")

    if not csv_files_with_dates:
        print(f"No valid CSV files with parsable dates found in '{derived_data_dir}' for company '{company_name_filter}'.", file=sys.stderr)
        return

    # Sort files based on the parsed datetime (ascending - oldest first)
    csv_files_with_dates.sort(key=lambda item: item[1])

    print(f"Found {len(csv_files_with_dates)} CSV files for '{company_name_filter}' to aggregate.")
    print("Files will be appended in this order (oldest post first):")
    for path, dt in csv_files_with_dates:
        print(f"  - {os.path.basename(path)} ({dt.strftime('%Y-%m-%d %H:%M')})")

    all_data_frames = []
    for file_path, _ in csv_files_with_dates:
        try:
            df = pd.read_csv(file_path)
            # Optional: Add a column indicating the source file if needed
            # df['source_file'] = os.path.basename(file_path) 
            all_data_frames.append(df)
            print(f"Successfully read {os.path.basename(file_path)}")
        except pd.errors.EmptyDataError:
            print(f"Warning: Skipping empty file '{os.path.basename(file_path)}'.", file=sys.stderr)
        except Exception as e:
            print(f"Error reading '{os.path.basename(file_path)}': {e}. Skipping file.", file=sys.stderr)

    if not all_data_frames:
        print("No dataframes were successfully read. Aggregation cancelled.", file=sys.stderr)
        return

    # Concatenate all dataframes
    combined_df = pd.concat(all_data_frames, ignore_index=True)

    # Save the combined dataframe to the derived data directory
    output_path = os.path.join(derived_data_dir, output_filename)
    try:
        combined_df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\nSuccessfully aggregated data into '{output_path}'")
        print(f"Total rows aggregated: {len(combined_df)}")
    except Exception as e:
        print(f"\nError saving aggregated file '{output_path}': {e}", file=sys.stderr)


if __name__ == "__main__":
    # Define Base Paths Relative to Script Location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_data_dir = os.path.abspath(os.path.join(script_dir, '..', '..', 'data')) # Go up two levels to root, then data/
    derived_data_dir = os.path.join(base_data_dir, 'derived')
    # os.chdir(script_dir) # Avoid changing working directory
    print(f"Reading from: {derived_data_dir}")
    print(f"Will save output to: {derived_data_dir}")

    company = input("Enter the company name to aggregate (e.g., Target): ")
    default_output = f"{company}_aggregated_all.csv" # Changed default name
    output_file = input(f"Enter the desired output filename (e.g., {default_output}): ")

    # Use default if user enters nothing
    if not output_file:
        output_file = default_output
        print(f"Using default output file: {output_file}")

    # Basic validation for output filename
    if not output_file.lower().endswith('.csv'):
        output_file += '.csv'
        print(f"Added .csv extension. Output file will be: {output_file}")

    # Call the aggregation function with the derived dir path
    aggregate_csvs(company, derived_data_dir, output_file)