import os
import pandas as pd
import glob
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define which companies kept/rolled back DEI based on the user description
HAS_DEI_COMPANIES = ['Delta', 'Costco'] # Companies that kept DEI (has_DEI = 1)
NO_DEI_COMPANIES = ['Target', 'Google'] # Companies that rolled back (has_DEI = 0)
TARGET_COMPANIES = HAS_DEI_COMPANIES + NO_DEI_COMPANIES

# --- Define DEI Cutoff Dates ---
# Dates are inclusive for the 'after' period (before_DEI = 0)
DEI_CUTOFF_DATES = {
    'Costco': datetime(2025, 1, 23),
    'Delta': datetime(2025, 2, 4),
    'Google': datetime(2025, 2, 5),
    'Target': datetime(2025, 1, 24),
}

# --- Deprecated: Time folders are no longer the source of truth for before/after ---
# TIME_FOLDERS = ['before_DEI', 'after_DEI']

if __name__ == "__main__":
    logging.info("Combine Company Comment CSVs based on Comment Dates")
    logging.info("-" * 30)

    # --- Define Base Paths Relative to Script Location ---
    script_dir = os.path.dirname(__file__)
    base_data_dir = os.path.abspath(os.path.join(script_dir, '..', '..', 'data'))
    raw_data_dir = os.path.join(base_data_dir, 'raw')
    derived_data_dir = os.path.join(base_data_dir, 'derived')

    # Ensure derived data directory exists
    os.makedirs(derived_data_dir, exist_ok=True)

    all_dfs = []

    # --- Iterate through Target Companies ---
    for company_name in TARGET_COMPANIES:
        logging.info(f"Processing company: {company_name}")
        company_path = os.path.join(raw_data_dir, company_name)

        if not os.path.isdir(company_path):
            logging.warning(f"  Company directory not found: {company_path}. Skipping.")
            continue

        # Determine the value for has_DEI column (remains the same)
        has_DEI_value = 1 if company_name in HAS_DEI_COMPANIES else 0

        # --- Get the company-specific cutoff date ---
        cutoff_date = DEI_CUTOFF_DATES.get(company_name)
        if not cutoff_date:
            logging.error(f"  Cutoff date not defined for company: {company_name}. Skipping.")
            continue
        logging.info(f"  Using cutoff date: {cutoff_date.strftime('%Y-%m-%d')}")

        # --- Find and Process ALL CSV files within the company directory (recursive) ---
        # We no longer rely on specific 'before_DEI'/'after_DEI' subfolders for the flag
        csv_pattern = os.path.join(company_path, '**', '*.csv') # Search recursively
        csv_files = glob.glob(csv_pattern, recursive=True)

        if not csv_files:
            logging.warning(f"    No CSV files found recursively in '{company_path}'.")
            continue

        logging.info(f"    Found {len(csv_files)} CSV files across all subdirectories.")

        for f in csv_files:
            # --- Add Debug Log ---
            logging.debug(f"      Processing file: {f}") # Log the full path
            # --- End Add Debug Log ---
            try:
                # logging.debug(f"      Processing file: {f}") # Original debug line (commented out)
                df = pd.read_csv(f)

                # Check for comment_date column
                if 'comment_date' not in df.columns:
                    logging.warning(f"      'comment_date' column not found in {os.path.basename(f)}. Skipping this file.")
                    continue

                # --- Assign before_DEI based on comment_date ---
                # Attempt to parse dates, coercing errors to NaT (Not a Time)
                df['comment_date_parsed'] = pd.to_datetime(df['comment_date'], errors='coerce')

                # Log rows where date parsing failed
                failed_dates = df[df['comment_date_parsed'].isna()]
                if not failed_dates.empty:
                    logging.warning(f"      Could not parse 'comment_date' for {len(failed_dates)} rows in {os.path.basename(f)}. Example invalid date: '{failed_dates['comment_date'].iloc[0]}'. These rows will be excluded from before/after assignment.")
                    # Optionally drop rows with unparseable dates, or handle them differently
                    df.dropna(subset=['comment_date_parsed'], inplace=True)
                    if df.empty:
                        logging.warning(f"      No valid dates found in {os.path.basename(f)} after attempting parse. Skipping file.")
                        continue


                # Assign before_DEI: 1 if date is strictly BEFORE cutoff, 0 otherwise
                df['before_DEI'] = (df['comment_date_parsed'] < cutoff_date).astype(int)

                # Assign company name and has_DEI flag
                df['company_name'] = company_name
                df['has_DEI'] = has_DEI_value

                # Drop the temporary parsed date column if no longer needed
                df.drop(columns=['comment_date_parsed'], inplace=True)

                all_dfs.append(df)
                # logging.debug(f"      Successfully processed and added data from: {os.path.basename(f)}")

            except Exception as e:
                logging.error(f"      Error processing file {os.path.basename(f)}: {e}. Skipping.")


    # --- Combine and Deduplicate ---
    if not all_dfs:
        logging.error("No dataframes were successfully read from any company/time folder. Exiting.")
        exit()

    logging.info("\nConcatenating all dataframes...")
    combined_df = pd.concat(all_dfs, ignore_index=True)
    initial_count = len(combined_df)
    logging.info(f"Total rows combined: {initial_count}")

    logging.info("Checking for and removing duplicate rows based on 'id' column...")
    # Check based on 'id' column for uniqueness
    duplicates_mask = combined_df.duplicated(subset=['id'], keep=False)
    if duplicates_mask.any():
        logging.warning(f"Found {duplicates_mask.sum()} rows with duplicate IDs. Example duplicates:")
        # Show some examples of the duplicates found
        # logging.warning(combined_df[duplicates_mask].sort_values(by='id').head().to_string()) # Commented out to prevent printing rows
        # Decide on removal strategy: keep='first' is common
        combined_df.drop_duplicates(subset=['id'], keep='first', inplace=True)
        final_count = len(combined_df)
        duplicates_removed = initial_count - final_count
        logging.warning(f"Removed {duplicates_removed} duplicate rows based on ID, keeping the first occurrence.")
    else:
        logging.info("No duplicate IDs found.")
        final_count = initial_count
        duplicates_removed = 0

    logging.info(f"Final row count after ID deduplication: {final_count}")

    # --- Save Combined DataFrame --- 
    output_file_name = "combined_comments.csv"
    output_file_path = os.path.join(derived_data_dir, output_file_name)
    logging.info(f"Saving final combined data to: {output_file_path}...")
    try:
        combined_df.to_csv(output_file_path, index=False, encoding='utf-8')
        logging.info("Successfully saved combined file.")
    except Exception as e:
        logging.error(f"Error saving combined file: {e}")

    logging.info("\nScript finished.") 