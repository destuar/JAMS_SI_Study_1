import os
import json
import pandas as pd
import re
from datetime import datetime
try:
    from dateutil.relativedelta import relativedelta
    from dateutil.parser import parse as date_parse
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

# --- Helper Function to Parse Relative Comment Timestamps ---
def parse_relative_timestamp(timestamp_str, current_dt):
    """
    Attempts to parse relative Facebook timestamps (5w, 2d, 5h, 10m, Just now)
    or absolute timestamps (July 25, July 25 at 10:00 PM) into datetime objects.
    """
    if not DATEUTIL_AVAILABLE or not isinstance(timestamp_str, str):
        return pd.NaT # Return Not a Time if library missing or input invalid

    timestamp_str = timestamp_str.lower().strip()

    if timestamp_str == "just now":
        return current_dt

    # Try relative first (e.g., 5w, 2d, 3h, 10m)
    match = re.match(r"^(\d+)\s*([mhdwy])", timestamp_str)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        delta_args = {}
        if unit == 'm':
            delta_args['minutes'] = value
        elif unit == 'h':
            delta_args['hours'] = value
        elif unit == 'd':
            delta_args['days'] = value
        elif unit == 'w':
            delta_args['weeks'] = value
        elif unit == 'y':
            delta_args['years'] = value

        if delta_args:
            try:
                return current_dt - relativedelta(**delta_args)
            except Exception:
                return pd.NaT # Calculation error

    # If not relative, try parsing as a date/datetime string
    try:
        # Use fuzzy parsing to handle variations like "July 25 at ..."
        # Set default to current_dt to provide context if year/time missing
        parsed_dt = date_parse(timestamp_str, fuzzy=True, default=current_dt)

        # Heuristic: If the parsed date has no year info AND is in the future
        # compared to the current date, assume it was last year.
        # (Handles cases like scraping in Jan for a "Dec 25" comment)
        # Check if year was explicitly parsed or defaulted
        if parsed_dt.year == current_dt.year and timestamp_str.find(str(current_dt.year)) == -1:
             if parsed_dt > current_dt:
                 parsed_dt = parsed_dt - relativedelta(years=1)

        return parsed_dt
    except (ValueError, TypeError, OverflowError):
         # Handle parsing errors or unparseable formats
        return pd.NaT

# --- Helper Function to Parse Filename Post Date ---
def parse_filename_date(filename_str):
    """
    Attempts to parse a date/time string from the filename
    Expected format: MM_DD_YY_HHMM[AM|PM] (e.g., 02_03_25_0953AM)
    Returns a datetime object or NaT on failure.
    """
    try:
        # Define the expected format pattern
        format_pattern = '%m_%d_%y_%I%M%p'
        return datetime.strptime(filename_str, format_pattern)
    except (ValueError, TypeError):
        print(f"  Error: Could not parse post date from filename '{filename_str}'. Expected format MM_DD_YY_HHMM[AM|PM].")
        return pd.NaT


# --- Function to process a SINGLE specified comment JSON file ---
def process_comment_file(json_file_path, output_csv_path, company_name, post_date):
    """
    Reads a single JSON file, processes comments, adds company/post info,
    selects specific columns, and saves to a CSV file.

    Args:
        json_file_path (str): The path to the input JSON file.
        output_csv_path (str): The path where the output CSV file should be saved.
        company_name (str): The name of the company (from folder).
        post_date (datetime): The parsed date/time of the post (from filename).
    """
    comments_in_file = []
    filename = os.path.basename(json_file_path)
    print(f"Processing file: {filename} -> {os.path.basename(output_csv_path)}")

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                print(f"  Warning: File '{filename}' is empty. Skipping.")
                return False # Indicate failure
            data = json.loads(content)

        if not isinstance(data, list):
            print(f"  Warning: Expected a list of comments in '{filename}', but found type {type(data)}. Skipping file.")
            return False # Indicate failure

        # Extract needed fields from JSON
        for comment_json in data:
            if isinstance(comment_json, dict):
                # Get comment text and timestamp text
                comment_text = comment_json.get('text', None) # Use original 'text' field
                timestamp_text = comment_json.get('timestamp_text', None)
                # Get reaction count and comment type (with defaults)
                reaction_count = comment_json.get('reaction_count', 0)
                comment_type = comment_json.get('comment_type', 'unknown')
                # Get comment ID and parent ID (with defaults)
                comment_id_val = comment_json.get('id', None)
                parent_id_val = comment_json.get('parent_id', None)
                comments_in_file.append({
                    'comment_text': comment_text,
                    'timestamp_text': timestamp_text,
                    'reaction_count': reaction_count,
                    'comment_type': comment_type,
                    'id': comment_id_val,             # Add new field
                    'parent_id': parent_id_val         # Add new field
                })
            else:
                print(f"  Warning: Found non-dictionary item in list within '{filename}'. Skipping item.")
                continue # Skip this item but continue processing others

    except json.JSONDecodeError:
        print(f"  Error: Could not decode JSON from file '{filename}'. Skipping.")
        return False # Indicate failure
    except Exception as e:
        print(f"  Error: An unexpected error occurred while loading '{filename}': {e}")
        return False # Indicate failure

    if not comments_in_file:
        print(f"  No valid comments were extracted from '{filename}'.")
        return False # Indicate failure

    # Convert to Pandas DataFrame
    df = pd.DataFrame(comments_in_file)

    # --- Calculate Comment Date ---
    if DATEUTIL_AVAILABLE:
        print("  Calculating approximate comment dates...")
        now = datetime.now()
        df['comment_date'] = df['timestamp_text'].apply(lambda ts: parse_relative_timestamp(ts, now))
    else:
        df['comment_date'] = pd.NaT
        print("  Warning: 'python-dateutil' library not found. comment_date column will be empty.")

    # --- Add Company Name and Post Date ---
    df['company_name'] = company_name
    # Assign the pre-parsed post_date datetime object
    df['post_date'] = post_date


    # --- Select and Rename Final Columns ---
    # Define desired columns including the new ones, including id and parent_id
    # Place id and parent_id after post_date for clarity
    final_cols = ['company_name', 'post_date', 'id', 'parent_id', 'comment_text', 'comment_date', 'comment_type', 'reaction_count']
    try:
        # Ensure all desired columns exist before selecting
        # Note: 'text' -> 'comment_text', others added directly
        missing_cols = [col for col in final_cols if col not in df.columns]
        if missing_cols:
            print(f"  Error selecting final columns: Required columns {missing_cols} not found in DataFrame.")
            print(f"  Available columns before final selection: {df.columns.tolist()}")
            return False

        df = df[final_cols] # Select the columns in the desired order

    except Exception as e: # Catch any other potential error during selection
         print(f"  Error during final column selection: {e}")
         print(f"  Available columns before selection attempt: {df.columns.tolist()}")
         return False

    # --- Format Date Columns (before saving) ---
    if 'comment_date' in df.columns:
        # Convert to datetime first (handles NaT safely), then format YYYY-MM-DD
        df['comment_date'] = pd.to_datetime(df['comment_date']).dt.strftime('%Y-%m-%d')
        # Optional: Replace NaT string with empty string if preferred
        df['comment_date'] = df['comment_date'].replace('NaT', '', regex=False)

    if 'post_date' in df.columns:
         # Format post_date to YYYY-MM-DD HH:MM:SS
         df['post_date'] = pd.to_datetime(df['post_date']).dt.strftime('%Y-%m-%d %H:%M:%S')
         # Handle potential NaT from filename parsing
         df['post_date'] = df['post_date'].replace('NaT', '', regex=False)


    # --- Save to CSV ---
    print(f"  Saving comments to: {output_csv_path}...")
    try:
        df.to_csv(output_csv_path, index=False, encoding='utf-8')
        print(f"  Successfully saved comments to: {os.path.basename(output_csv_path)}")
        return True # Indicate success
    except Exception as e:
        print(f"  Error: Could not save DataFrame to CSV file '{output_csv_path}': {e}")
        return False # Indicate failure


if __name__ == "__main__":
    print("Facebook Comment Processor (Single File)")
    print("-" * 30)
    if not DATEUTIL_AVAILABLE:
        print("!! Warning: 'python-dateutil' is not installed. Comment date calculation requires it.")
        print("!! Please run: pip install python-dateutil")
        print("-" * 30)

    # --- Get User Input ---
    company_folder_name = input("Enter the company name (folder name, e.g., Target): ")
    file_name_str = input("Enter the date & time (file name without .json, e.g., 02_03_25_0953AM): ")

    # --- Define Base Paths Relative to Script Location ---
    script_dir = os.path.dirname(__file__)
    base_data_dir = os.path.abspath(os.path.join(script_dir, '..', '..', 'data')) # Go up two levels to root, then data/
    raw_data_dir = os.path.join(base_data_dir, 'raw')
    derived_data_dir = os.path.join(base_data_dir, 'derived')

    # Ensure derived data directory exists
    os.makedirs(derived_data_dir, exist_ok=True)

    # --- Validate Inputs and Construct Paths ---
    company_path = os.path.join(raw_data_dir, company_folder_name)
    if not os.path.isdir(company_path):
         print(f"Error: Company folder '{company_folder_name}' not found in '{raw_data_dir}'.")
         exit()

    json_file_name = f"{file_name_str}.json"
    json_file_path = os.path.join(company_path, json_file_name)

    if not os.path.isfile(json_file_path):
        print(f"Error: JSON file '{json_file_name}' not found in folder '{company_path}'.")
        exit()

    # Construct the output CSV filename and path
    output_csv_name = f"{company_folder_name}_{file_name_str}.csv" # Prepend company name for clarity
    output_csv_path = os.path.join(derived_data_dir, output_csv_name)

    # --- Parse Post Date from Filename ---
    post_date_dt = parse_filename_date(file_name_str)
    if pd.isna(post_date_dt):
        print("Error: Could not determine post date from filename. Exiting.")
        exit()

    # --- Process the Single File ---
    print("-" * 20)
    if process_comment_file(json_file_path, output_csv_path, company_folder_name, post_date_dt):
        print("\nProcessing finished successfully.")
    else:
        print("\nProcessing failed.")

    print("\nScript finished.") 