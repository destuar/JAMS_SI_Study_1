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

def parse_relative_timestamp(timestamp_str, current_dt):
    if not DATEUTIL_AVAILABLE or not isinstance(timestamp_str, str):
        return pd.NaT

    timestamp_str = timestamp_str.lower().strip()
    if timestamp_str == "just now":
        return current_dt

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
                return pd.NaT

    try:
        parsed_dt = date_parse(timestamp_str, fuzzy=True, default=current_dt)
        if parsed_dt.year == current_dt.year and str(current_dt.year) not in timestamp_str:
            if parsed_dt > current_dt:
                parsed_dt = parsed_dt - relativedelta(years=1)
        return parsed_dt
    except (ValueError, TypeError, OverflowError):
        return pd.NaT

def parse_filename_date(filename_str):
    try:
        format_pattern = '%m_%d_%y_%I%M%p'
        return datetime.strptime(filename_str, format_pattern)
    except (ValueError, TypeError):
        print(f"  Error: Could not parse post date from filename '{filename_str}'. Expected format MM_DD_YY_HHMM[AM|PM].")
        return pd.NaT

def process_comment_file(json_file_path, output_csv_path, company_name, post_date):
    comments_in_file = []
    filename = os.path.basename(json_file_path)
    print(f"Processing file: {filename} -> {os.path.basename(output_csv_path)}")

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                print(f"  Warning: File '{filename}' is empty. Skipping.")
                return False
            data = json.loads(content)

        if not isinstance(data, list):
            print(f"  Warning: Expected a list of comments in '{filename}', but found {type(data)}. Skipping.")
            return False

        for comment_json in data:
            if isinstance(comment_json, dict):
                comment_text = comment_json.get('text', None)
                timestamp_text = comment_json.get('timestamp_text', None)
                reaction_count = comment_json.get('reaction_count', 0)
                comment_type = comment_json.get('comment_type', 'unknown')
                comment_id_val = comment_json.get('id', None)
                parent_id_val = comment_json.get('parent_id', None)
                comments_in_file.append({
                    'comment_text': comment_text,
                    'timestamp_text': timestamp_text,
                    'reaction_count': reaction_count,
                    'comment_type': comment_type,
                    'id': comment_id_val,
                    'parent_id': parent_id_val
                })

    except json.JSONDecodeError:
        print(f"  Error: Could not decode JSON from file '{filename}'. Skipping.")
        return False
    except Exception as e:
        print(f"  Error: Unexpected error while loading '{filename}': {e}")
        return False

    if not comments_in_file:
        print(f"  No valid comments extracted from '{filename}'.")
        return False

    df = pd.DataFrame(comments_in_file)

    if DATEUTIL_AVAILABLE:
        print("  Calculating approximate comment dates...")
        now = datetime.now()
        df['comment_date'] = df['timestamp_text'].apply(lambda ts: parse_relative_timestamp(ts, now))
    else:
        df['comment_date'] = pd.NaT
        print("  Warning: 'python-dateutil' not installed. comment_date will be empty.")

    df['company_name'] = company_name
    df['post_date'] = post_date

    final_cols = ['company_name', 'post_date', 'id', 'parent_id', 'comment_text', 'comment_date', 'comment_type', 'reaction_count']
    missing_cols = [col for col in final_cols if col not in df.columns]
    if missing_cols:
        print(f"  Error selecting final columns: Missing {missing_cols}")
        return False

    df = df[final_cols]

    df['comment_date'] = pd.to_datetime(df['comment_date']).dt.strftime('%Y-%m-%d').replace('NaT', '', regex=False)
    df['post_date'] = pd.to_datetime(df['post_date']).dt.strftime('%Y-%m-%d %H:%M:%S').replace('NaT', '', regex=False)

    try:
        df.to_csv(output_csv_path, index=False, encoding='utf-8')
        print(f"  Successfully saved to: {os.path.basename(output_csv_path)}")
        return True
    except Exception as e:
        print(f"  Error: Could not save to CSV '{output_csv_path}': {e}")
        return False

if __name__ == "__main__":
    print("Facebook Comment Processor (BATCH MODE)")
    print("-" * 30)
    if not DATEUTIL_AVAILABLE:
        print("!! Warning: 'python-dateutil' is not installed. Run: pip install python-dateutil")
        print("-" * 30)

    company_folder = input("Enter the company name (folder name, e.g., Target): ").strip()

    if not os.path.isdir(company_folder):
        print(f"Error: Folder '{company_folder}' not found.")
        exit()

    json_files = [f for f in os.listdir(company_folder) if f.endswith(".json")]
    if not json_files:
        print("No JSON files found.")
        exit()

    print(f"Found {len(json_files)} JSON file(s). Starting batch processing...")

    for json_filename in json_files:
        base_name = os.path.splitext(json_filename)[0]
        json_file_path = os.path.join(company_folder, json_filename)
        csv_file_path = os.path.join(company_folder, f"{base_name}.csv")

        # Skip if CSV already exists
        if os.path.isfile(csv_file_path):
            print(f"  Skipping '{json_filename}' (CSV already exists).")
            continue

        post_date_dt = parse_filename_date(base_name)
        if pd.isna(post_date_dt):
            print(f"  Skipping '{json_filename}' (invalid date format).")
            continue

        process_comment_file(json_file_path, csv_file_path, company_folder, post_date_dt)

    print("\nAll files processed. Done ✅")
