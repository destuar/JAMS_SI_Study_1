import pandas as pd
from pathlib import Path
import logging
from sklearn.model_selection import StratifiedShuffleSplit

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define constants
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "data" / "derived" / "cleaned_threaded_comments.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "annotate"
OUTPUT_FILE = OUTPUT_DIR / "relevance_sample.csv"
SAMPLE_SIZE = 500
STRATIFY_COLUMN = "company_name" # Assuming this is the column name for company

def sample_for_relevance(input_path: Path, output_path: Path, n: int, stratify_col: str):
    """
    Reads a CSV file, performs stratified sampling, and saves the sample.

    Args:
        input_path: Path to the input CSV file.
        output_path: Path to save the sampled CSV file.
        n: The total number of samples desired.
        stratify_col: The column name to stratify by.
    """
    logging.info(f"Starting stratified sampling process.")
    if not input_path.exists():
        logging.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        logging.info(f"Reading input data from {input_path}...")
        df = pd.read_csv(input_path)
        logging.info(f"Read {len(df)} comments.")

        # Check if stratify column exists
        if stratify_col not in df.columns:
            logging.error(f"Stratification column '{stratify_col}' not found in the dataframe.")
            raise ValueError(f"Stratification column '{stratify_col}' not found in the dataframe.")

        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logging.info(f"Ensured output directory exists: {output_path.parent}")

        # Use StratifiedShuffleSplit for exact stratified sampling
        logging.info(f"Performing exact stratified sampling by '{stratify_col}' to get {n} samples.")
        splitter = StratifiedShuffleSplit(n_splits=1, test_size=n, random_state=42)
        for _, test_idx in splitter.split(df, df[stratify_col]):
            sampled_df = df.iloc[test_idx]

        logging.info(f"Saving {len(sampled_df)} sampled comments to {output_path}...")
        sampled_df.to_csv(output_path, index=False)
        logging.info(f"Sampling complete. Output saved to {output_path}")

    except pd.errors.EmptyDataError:
        logging.error(f"Input file is empty: {input_path}")
        raise
    except Exception as e:
        logging.error(f"An error occurred during sampling: {e}")
        raise

if __name__ == "__main__":
    sample_for_relevance(INPUT_FILE, OUTPUT_FILE, SAMPLE_SIZE, STRATIFY_COLUMN) 