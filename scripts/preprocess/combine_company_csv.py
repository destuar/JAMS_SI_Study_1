import os
import pandas as pd
import glob

if __name__ == "__main__":
    print("Combine Company Comment CSVs")
    print("-" * 30)

    # --- Get User Input ---
    company_folder_name = input("Enter the company name (folder name, e.g., Google): ")

    # --- Define Base Paths Relative to Script Location ---
    script_dir = os.path.dirname(__file__)
    base_data_dir = os.path.abspath(os.path.join(script_dir, '..', '..', 'data'))
    raw_data_dir = os.path.join(base_data_dir, 'raw')
    derived_data_dir = os.path.join(base_data_dir, 'derived')

    # --- Construct Paths ---
    comments_json_dir = os.path.join(raw_data_dir, company_folder_name, 'comments-json')
    output_file_name = f"{company_folder_name}_all_comments.csv"
    output_file_path = os.path.join(derived_data_dir, output_file_name)

    # Ensure comments-json directory exists
    if not os.path.isdir(comments_json_dir):
        print(f"Error: Directory '{comments_json_dir}' not found.")
        exit()

    # Ensure derived data directory exists
    os.makedirs(derived_data_dir, exist_ok=True)

    # --- Find all CSV files in the directory ---
    csv_pattern = os.path.join(comments_json_dir, '*.csv')
    csv_files = glob.glob(csv_pattern)

    if not csv_files:
        print(f"No CSV files found in '{comments_json_dir}'.")
        exit()

    print(f"Found {len(csv_files)} CSV files to combine.")

    # --- Read and Concatenate CSVs ---
    all_dfs = []
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            # Optional: Add filename source if needed later
            # df['source_file'] = os.path.basename(f)
            all_dfs.append(df)
            print(f"  Read: {os.path.basename(f)}")
        except Exception as e:
            print(f"  Error reading file {os.path.basename(f)}: {e}. Skipping.")

    if not all_dfs:
        print("No dataframes were successfully read. Exiting.")
        exit()

    # Concatenate all dataframes
    combined_df = pd.concat(all_dfs, ignore_index=True)
    print(f"\nTotal comments combined: {len(combined_df)}")

    # --- Save Combined DataFrame ---
    print(f"Saving combined data to: {output_file_path}...")
    try:
        combined_df.to_csv(output_file_path, index=False, encoding='utf-8')
        print("Successfully saved combined file.")
    except Exception as e:
        print(f"Error saving combined file: {e}")

    print("\nScript finished.") 