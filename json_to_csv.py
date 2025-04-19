import json
import csv
import sys

def convert_json_to_csv(json_file_path, csv_file_path):
    """Converts the Label Studio annotation JSON export to a CSV file.

    Args:
        json_file_path (str): Path to the input JSON file.
        csv_file_path (str): Path to the output CSV file.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            # Read the entire file content as it might be on a single line
            content = f.read()
            # Try loading the JSON data
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                # Attempt to handle potential multiple JSON objects on one line if separated by newline (less likely based on snippet)
                try:
                    data = [json.loads(line) for line in content.strip().split('\n') if line.strip()]
                    if not data: # If splitting didn't work, re-raise original error
                         raise e
                except json.JSONDecodeError:
                     print("Failed to parse JSON even after splitting lines. Please check file format.")
                     raise e # Re-raise original error if split also fails

        if not isinstance(data, list):
            print("Error: JSON data is not a list as expected.")
            sys.exit(1)

    except FileNotFoundError:
        print(f"Error: Input JSON file not found at {json_file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred opening or reading the JSON file: {e}")
        sys.exit(1)

    # Define the headers for the CSV file
    # Adjust these based on the fields you actually need
    headers = [
        'task_id', 'annotation_id', 'completed_by', 'relevance_choice',
        'annotation_created_at', 'company_name', 'post_date', 'comment_id',
        'parent_id', 'comment_text', 'comment_date', 'comment_type',
        'reaction_count', 'before_DEI', 'has_DEI', 'root_id', 'depth',
        'sibling_count', 'time_since_root', 'cleaned_text', 'full_text'
    ]

    try:
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            for item in data:
                row = {}
                # Extract top-level data
                row['task_id'] = item.get('id')

                # Extract annotation data (assuming one annotation per task)
                annotation = item.get('annotations', [{}])[0] # Get first annotation or empty dict
                row['annotation_id'] = annotation.get('id')
                row['completed_by'] = annotation.get('completed_by')
                row['annotation_created_at'] = annotation.get('created_at')

                # Extract relevance choice from result
                result = annotation.get('result', [{}])[0] # Get first result or empty dict
                value = result.get('value', {})
                choices = value.get('choices', [])
                row['relevance_choice'] = choices[0] if choices else None

                # Extract data from the 'data' object
                data_obj = item.get('data', {})
                row['company_name'] = data_obj.get('company_name')
                row['post_date'] = data_obj.get('post_date')
                row['comment_id'] = data_obj.get('id') # Note: 'id' within 'data' object
                row['parent_id'] = data_obj.get('parent_id')
                row['comment_text'] = data_obj.get('comment_text')
                row['comment_date'] = data_obj.get('comment_date')
                row['comment_type'] = data_obj.get('comment_type')
                row['reaction_count'] = data_obj.get('reaction_count')
                row['before_DEI'] = data_obj.get('before_DEI')
                row['has_DEI'] = data_obj.get('has_DEI')
                row['root_id'] = data_obj.get('root_id')
                row['depth'] = data_obj.get('depth')
                row['sibling_count'] = data_obj.get('sibling_count')
                row['time_since_root'] = data_obj.get('time_since_root')
                row['cleaned_text'] = data_obj.get('cleaned_text')
                row['full_text'] = data_obj.get('full_text')

                writer.writerow(row)

        print(f"Successfully converted {json_file_path} to {csv_file_path}")

    except IOError as e:
        print(f"Error writing to CSV file {csv_file_path}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during CSV writing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python json_to_csv.py <input_json_file> <output_csv_file>")
        # Provide default paths if no arguments are given, for convenience
        print("Running with default paths: data/annotate/project-1-at-2025-04-19-06-02-a8a8f5bc.json -> data/annotate/project-1-annotations.csv")
        input_json = "data/annotate/project-1-at-2025-04-19-06-02-a8a8f5bc.json"
        output_csv = "data/annotate/project-1-annotations.csv"
    else:
        input_json = sys.argv[1]
        output_csv = sys.argv[2]

    convert_json_to_csv(input_json, output_csv) 