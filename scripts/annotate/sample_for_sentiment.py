# scripts/annotate/sample_for_sentiment.py
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
INPUT_PATH = "data/derived/comments_with_relevance.csv"
OUTPUT_PATH = "data/annotate/sample/sentiment_sample.csv"
SAMPLE_SIZE = 1000
STRATIFY_COLUMN = "company_name"
RELEVANCE_COLUMN = "relevance"
RANDOM_STATE = 42

# --- Load Data ---
logging.info(f"Loading data from {INPUT_PATH}")
try:
    df = pd.read_csv(INPUT_PATH)
    logging.info(f"Loaded {len(df)} total rows.")
except FileNotFoundError:
    logging.error(f"Error: Input data file not found at {INPUT_PATH}")
    exit()
except Exception as e:
    logging.error(f"Error loading data: {e}")
    exit()

# --- Stratified Sampling ---
if len(df) < SAMPLE_SIZE:
    logging.warning(f"Total comments ({len(df)}) is less than the desired sample size ({SAMPLE_SIZE}). Using all comments.")
    sample_df = df
else:
    logging.info(f"Performing stratified sampling by '{STRATIFY_COLUMN}' to get {SAMPLE_SIZE} samples from the full dataset.")
    # Check if stratification is possible
    if STRATIFY_COLUMN not in df.columns:
        logging.error(f"Stratification column '{STRATIFY_COLUMN}' not found in the data.")
        exit()

    # Check for strata with only one sample, as StratifiedShuffleSplit requires at least 2 per class
    value_counts = df[STRATIFY_COLUMN].value_counts()
    if (value_counts < 2).any():
        small_strata = value_counts[value_counts < 2].index.tolist()
        logging.error(f"Stratification cannot be performed because the following strata have fewer than 2 samples: {small_strata}. Required for StratifiedShuffleSplit.")
        # Optional: Could implement a fallback here if desired, e.g., random sampling.
        # For now, we exit as per the stricter requirement of StratifiedShuffleSplit.
        exit()

    try:
        # Use StratifiedShuffleSplit for exact stratified sampling
        splitter = StratifiedShuffleSplit(n_splits=1, test_size=SAMPLE_SIZE, random_state=RANDOM_STATE)
        
        # Get the indices for the sample set
        # Since n_splits=1, this loop runs once
        for _, sample_indices in splitter.split(df, df[STRATIFY_COLUMN]):
            sample_df = df.iloc[sample_indices]

        logging.info(f"Successfully sampled {len(sample_df)} comments.")
    except ValueError as e:
        # This error might occur if configuration is wrong or strata are too small
        logging.error(f"Error during StratifiedShuffleSplit: {e}")
        exit()

# --- Save Sample ---
output_dir = os.path.dirname(OUTPUT_PATH)
os.makedirs(output_dir, exist_ok=True)

logging.info(f"Saving sampled data to {OUTPUT_PATH}")
try:
    sample_df.to_csv(OUTPUT_PATH, index=False)
    logging.info("Sample saved successfully.")
except Exception as e:
    logging.error(f"Error saving sample data: {e}")
    exit()

print(f"\n--- Sampling Summary ---")
print(f"Input data: {INPUT_PATH}")
print(f"Total comments loaded: {len(df)}")
print(f"Desired sample size: {SAMPLE_SIZE}")
print(f"Actual sample size: {len(sample_df)}")
print(f"Stratified by: '{STRATIFY_COLUMN}'")
print(f"Output saved to: {OUTPUT_PATH}")
print("------------------------") 