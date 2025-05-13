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
# Dates are inclusive for the 'after' period (before_DEI = 0 if date >= cutoff_date)
DEI_CUTOFF_DATES = {
    'Costco': datetime(2025, 1, 23),
    'Delta': datetime(2025, 2, 4),
    'Google': datetime(2025, 2, 5),
    'Target': datetime(2025, 1, 24),
}

# --- Deprecated: Time folders are no longer the source of truth for before/after ---
# TIME_FOLDERS = ['before_DEI', 'after_DEI']

def assign_before_dei_for_group(group, company_cutoff_dates_map):
    """
    Calculates 'before_DEI' for a group of comments sharing the same company and post_date.
    - For the first unique comment_date in the group, before_DEI is based on post_date vs cutoff.
    - For subsequent unique comment_dates, before_DEI is based on their comment_date vs cutoff.
    Returns a Pandas Series with before_DEI values (1 for before, 0 for on/after, pd.NA for issues).
    """
    company_name = group['company_name'].iloc[0]
    current_post_date = group['post_date_parsed'].iloc[0] # Constant for the group

    company_cutoff_date = company_cutoff_dates_map.get(company_name)

    # Initialize before_DEI series for this group with nullable integer type
    before_dei_series = pd.Series(pd.NA, index=group.index, dtype=pd.Int64Dtype())

    if pd.isna(company_cutoff_date):
        # This company might not be in the DEI_CUTOFF_DATES map if this function is ever called
        # directly with a group for an unmapped company (though the main script tries to prevent this).
        # Logging for unmapped companies is handled at a higher level per file.
        return before_dei_series

    # Sort unique, non-NaT comment dates for this post group
    unique_comment_dates = sorted(group['comment_date_parsed'].dropna().unique())

    if not unique_comment_dates: # No valid comment_dates in this post group
        return before_dei_series # All before_DEI remain NA

    first_unique_cd = unique_comment_dates[0]

    # Rule 1: For comments matching the first unique comment_date, use post_date for comparison
    # current_post_date is confirmed non-NaT for rows entering this group processing.
    primary_value = 1 if current_post_date < company_cutoff_date else 0
    mask_primary_comments_in_group = (group['comment_date_parsed'] == first_unique_cd)
    before_dei_series.loc[mask_primary_comments_in_group] = primary_value

    # Rule 2: For comments matching subsequent unique comment_dates, use their own comment_date
    if len(unique_comment_dates) > 1:
        for sub_cd in unique_comment_dates[1:]:
            sub_value = 1 if sub_cd < company_cutoff_date else 0
            mask_sub_comments_in_group = (group['comment_date_parsed'] == sub_cd)
            before_dei_series.loc[mask_sub_comments_in_group] = sub_value
            
    return before_dei_series

if __name__ == "__main__":
    logging.info("Combine Company Comment CSVs based on new Comment/Post Date logic for before_DEI")
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

        # Determine the value for has_DEI column (remains the same for all rows from this company)
        has_DEI_value = 1 if company_name in HAS_DEI_COMPANIES else 0

        # Get the company-specific cutoff date (used by assign_before_dei_for_group indirectly via DEI_CUTOFF_DATES map)
        # This check ensures the company folder being processed is in our map.
        if company_name not in DEI_CUTOFF_DATES:
            logging.error(f"  Cutoff date not defined for company: {company_name} in DEI_CUTOFF_DATES. Skipping this company folder.")
            continue
        # cutoff_date variable itself isn't directly used in loop below, but DEI_CUTOFF_DATES map is.
        logging.info(f"  Using cutoff date: {DEI_CUTOFF_DATES[company_name].strftime('%Y-%m-%d')}")

        csv_pattern = os.path.join(company_path, '**', '*.csv') # Search recursively
        csv_files = glob.glob(csv_pattern, recursive=True)

        if not csv_files:
            logging.warning(f"    No CSV files found recursively in '{company_path}'.")
            continue

        logging.info(f"    Found {len(csv_files)} CSV files across all subdirectories.")

        for f in csv_files:
            logging.debug(f"      Processing file: {f}")
            try:
                df = pd.read_csv(f)

                required_cols = ['post_date', 'comment_date'] # company_name added later
                missing_cols_in_file = [col for col in required_cols if col not in df.columns]
                if missing_cols_in_file:
                    logging.warning(f"      File {os.path.basename(f)} is missing required columns: {missing_cols_in_file}. Skipping this file.")
                    continue

                # Assign company name and has_DEI flag (needed for grouping and cutoff lookup)
                df['company_name'] = company_name
                df['has_DEI'] = has_DEI_value

                # Parse dates
                df['post_date_parsed'] = pd.to_datetime(df['post_date'], errors='coerce')
                df['comment_date_parsed'] = pd.to_datetime(df['comment_date'], errors='coerce')

                # Log date parsing issues
                num_failed_post_dates = df['post_date_parsed'].isna().sum()
                if num_failed_post_dates > 0:
                    logging.warning(f"        Could not parse 'post_date' for {num_failed_post_dates} rows in {os.path.basename(f)}.")
                num_failed_comment_dates = df['comment_date_parsed'].isna().sum()
                if num_failed_comment_dates > 0:
                    logging.warning(f"        Could not parse 'comment_date' for {num_failed_comment_dates} rows in {os.path.basename(f)}.")

                # Initialize before_DEI column with Int64Dtype
                df['before_DEI'] = pd.Series(pd.NA, index=df.index, dtype=pd.Int64Dtype())

                # Filter rows that can be processed (must have company_name and post_date_parsed)
                # company_name is guaranteed by assignment above. post_date_parsed is critical for grouping.
                processing_candidate_mask = df['post_date_parsed'].notna() # company_name already set
                df_to_process = df[processing_candidate_mask]

                if not df_to_process.empty:
                    # Iterate through groups manually to assign results
                    for group_key, group_df in df_to_process.groupby(
                        ['company_name', 'post_date_parsed'] 
                    ):
                        group_before_dei_values = assign_before_dei_for_group(group_df, DEI_CUTOFF_DATES)
                        df.loc[group_df.index, 'before_DEI'] = group_before_dei_values
                
                # Final cast to Int64Dtype just in case, though assignments should maintain it.
                if not df['before_DEI'].empty:
                    df['before_DEI'] = df['before_DEI'].astype(pd.Int64Dtype())

                # Drop temporary parsed date columns
                df.drop(columns=['post_date_parsed', 'comment_date_parsed'], inplace=True)

                all_dfs.append(df)
                logging.debug(f"      Successfully processed and added data from: {os.path.basename(f)}")

            except Exception as e:
                logging.error(f"      Error processing file {os.path.basename(f)}: {e}. Skipping.")

    # --- Combine and Deduplicate ---
    if not all_dfs:
        logging.error("No dataframes were successfully read. Exiting.")
        exit()

    logging.info("\nConcatenating all dataframes...")
    combined_df = pd.concat(all_dfs, ignore_index=True)
    initial_count = len(combined_df)
    logging.info(f"Total rows combined: {initial_count}")

    logging.info("Checking for and removing duplicate rows based on 'id' column...")
    if 'id' in combined_df.columns:
        duplicates_mask = combined_df.duplicated(subset=['id'], keep=False)
        if duplicates_mask.any():
            logging.warning(f"Found {duplicates_mask.sum()} rows with duplicate IDs.")
            combined_df.drop_duplicates(subset=['id'], keep='first', inplace=True)
            final_count = len(combined_df)
            duplicates_removed = initial_count - final_count
            logging.warning(f"Removed {duplicates_removed} duplicate rows based on ID, keeping the first occurrence.")
        else:
            logging.info("No duplicate IDs found.")
            final_count = initial_count
    else:
        logging.warning("'id' column not found in combined data. Skipping deduplication based on ID.")
        final_count = initial_count

    logging.info(f"Final row count: {final_count}")

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