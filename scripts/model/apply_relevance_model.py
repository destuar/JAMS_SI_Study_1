# scripts/model/apply_relevance_model.py
import pandas as pd
from setfit import SetFitModel
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
MODEL_LOAD_PATH = "models/relevance_setfit_model"
DATA_PATH = "data/derived/cleaned_threaded_comments.csv"
OUTPUT_PATH = "data/derived/comments_with_relevance.csv"
TEXT_COLUMN = "full_text" # Column with text to predict on
NEW_LABEL_COLUMN = "relevance" # Name for the added prediction column

# --- Load Model ---
logging.info(f"Loading model from {MODEL_LOAD_PATH}")
try:
    model = SetFitModel.from_pretrained(MODEL_LOAD_PATH)
    logging.info("Model loaded successfully.")
except Exception as e:
    logging.error(f"Error loading model from {MODEL_LOAD_PATH}: {e}")
    exit()

# --- Load Data ---
logging.info(f"Loading data for prediction from {DATA_PATH}")
try:
    df = pd.read_csv(DATA_PATH)
    logging.info(f"Loaded {len(df)} rows for prediction.")
except FileNotFoundError:
    logging.error(f"Error: Data file not found at {DATA_PATH}")
    exit()
except Exception as e:
    logging.error(f"Error loading data: {e}")
    exit()

# --- Validate Data ---
if TEXT_COLUMN not in df.columns:
    logging.error(f"Error: Text column '{TEXT_COLUMN}' not found in {DATA_PATH}. Available columns: {df.columns.tolist()}")
    exit()

# Handle potential NaN values in the text column
df.dropna(subset=[TEXT_COLUMN], inplace=True)
logging.info(f"{len(df)} rows remaining after removing NaNs in '{TEXT_COLUMN}'.")

if len(df) == 0:
    logging.error("No data remaining after handling NaNs. Exiting.")
    exit()

# --- Predict ---
logging.info("Predicting relevance on the dataset...")
texts_to_predict = df[TEXT_COLUMN].astype(str).tolist()
try:
    predictions = model.predict(texts_to_predict)
    logging.info("Prediction finished.")
except Exception as e:
    logging.error(f"Error during prediction: {e}")
    exit()

# --- Add Predictions and Save ---
df[NEW_LABEL_COLUMN] = predictions
logging.info(f"Added predictions to column '{NEW_LABEL_COLUMN}'.")

# Ensure output directory exists
output_dir = os.path.dirname(OUTPUT_PATH)
os.makedirs(output_dir, exist_ok=True)

logging.info(f"Saving predictions to {OUTPUT_PATH}")
try:
    df.to_csv(OUTPUT_PATH, index=False)
    logging.info("Predictions saved successfully.")
except Exception as e:
    logging.error(f"Error saving predictions to {OUTPUT_PATH}: {e}")
    exit()

print(f"\n--- Prediction Summary ---")
print(f"Model used: {MODEL_LOAD_PATH}")
print(f"Input data: {DATA_PATH}")
print(f"Number of predictions: {len(df)}")
print(f"Output saved to: {OUTPUT_PATH}")
print("------------------------") 