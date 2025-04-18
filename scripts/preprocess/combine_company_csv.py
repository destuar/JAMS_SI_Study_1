import os
import pandas as pd
import glob
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define which companies kept/rolled back DEI based on the user description
HAS_DEI_COMPANIES = ['Delta', 'Costco'] # Companies that kept DEI (has_DEI = 1)
NO_DEI_COMPANIES = ['Target', 'Google'] # Companies that rolled back (has_DEI = 0)
TARGET_COMPANIES = HAS_DEI_COMPANIES + NO_DEI_COMPANIES

TIME_FOLDERS = ['before_DEI', 'after_DEI']

if __name__ == "__main__":
    logging.info("Combine Company Comment CSVs across time periods")
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

        # Determine the value for has_DEI column
        has_DEI_value = 1 if company_name in HAS_DEI_COMPANIES else 0

        # --- Iterate through Time Folders (before/after) --- 
        for time_folder in TIME_FOLDERS:
            time_folder_path = os.path.join(company_path, time_folder)
            logging.info(f"  Looking in: {time_folder_path}")

            if not os.path.isdir(time_folder_path):
                logging.warning(f"    Subdirectory not found: {time_folder_path}. Skipping.")
                continue

            # Determine the value for before_DEI column
            before_DEI_value = 1 if time_folder == 'before_DEI' else 0

            # --- Find and Process CSV files --- 
            csv_pattern = os.path.join(time_folder_path, '*.csv')
            csv_files = glob.glob(csv_pattern)

            if not csv_files:
                logging.warning(f"    No CSV files found in '{time_folder_path}'.")
                continue

            logging.info(f"    Found {len(csv_files)} CSV files.")

            for f in csv_files:
                try:
                    df = pd.read_csv(f)
                    df['company_name'] = company_name # Ensure company name is a column
                    df['before_DEI'] = before_DEI_value
                    df['has_DEI'] = has_DEI_value
                    all_dfs.append(df)
                    # logging.debug(f"      Read: {os.path.basename(f)}")
                except Exception as e:
                    logging.error(f"      Error reading file {os.path.basename(f)}: {e}. Skipping.")

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
        logging.warning(combined_df[duplicates_mask].sort_values(by='id').head().to_string())
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