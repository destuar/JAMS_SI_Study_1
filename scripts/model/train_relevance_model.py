# scripts/modeling/train_relevance_model.py
import pandas as pd
from datasets import Dataset
from setfit import SetFitModel, SetFitTrainer, TrainingArguments
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, precision_recall_fscore_support, accuracy_score
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
DATA_PATH = "data/annotate/complete/combined_annotations.csv"
MODEL_SAVE_PATH = "models/relevance_setfit_model"
TEXT_COLUMN = "full_text"
LABEL_COLUMN = "relevance_label"
TEST_SIZE = 0.2
RANDOM_STATE = 42
BASE_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
NUM_EPOCHS_BODY = 1 # SetFit typically requires very few epochs for the body
NUM_EPOCHS_HEAD = 16 # More epochs usually needed for the classification head
BATCH_SIZE = 16
LEARNING_RATE = 2e-5

# --- Load Data ---
logging.info(f"Loading data from {DATA_PATH}")
try:
    df = pd.read_csv(DATA_PATH, usecols=[TEXT_COLUMN, LABEL_COLUMN])
    logging.info(f"Loaded {len(df)} rows.")
except FileNotFoundError:
    logging.error(f"Error: Data file not found at {DATA_PATH}")
    exit()
except Exception as e:
    logging.error(f"Error loading data: {e}")
    exit()

# --- Preprocess Data ---
logging.info("Preprocessing data...")
# Handle potential NaN values
df.dropna(subset=[TEXT_COLUMN, LABEL_COLUMN], inplace=True)
# Ensure label is integer
df[LABEL_COLUMN] = df[LABEL_COLUMN].astype(int)
# Ensure text is string
df[TEXT_COLUMN] = df[TEXT_COLUMN].astype(str)
# Rename label column for SetFit compatibility
df.rename(columns={LABEL_COLUMN: "label", TEXT_COLUMN: "text"}, inplace=True)
logging.info(f"Data preprocessed. {len(df)} rows remaining after handling NaNs.")
logging.info(f"Label distribution:\n{df['label'].value_counts(normalize=True)}")

if len(df) == 0:
    logging.error("No data remaining after preprocessing. Exiting.")
    exit()

# --- Split Data ---
logging.info(f"Splitting data (test_size={TEST_SIZE}, random_state={RANDOM_STATE})")
train_df, eval_df = train_test_split(
    df,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=df['label'] # Stratify to maintain label distribution
)
logging.info(f"Train set size: {len(train_df)}, Evaluation set size: {len(eval_df)}")

# Convert to Hugging Face Dataset
train_dataset = Dataset.from_pandas(train_df, preserve_index=False)
eval_dataset = Dataset.from_pandas(eval_df, preserve_index=False)

# --- Define Metrics ---
def compute_metrics(y_pred, y_true):
    """Computes accuracy, precision, recall, and F1 (weighted)."""
    accuracy = accuracy_score(y_true=y_true, y_pred=y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true=y_true, y_pred=y_pred, average='weighted')
    return {
        'accuracy': accuracy,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

# --- Model Training ---
logging.info(f"Initializing SetFit model with base: {BASE_MODEL_ID}")
model = SetFitModel.from_pretrained(BASE_MODEL_ID)

logging.info("Initializing SetFitTrainer...")
trainer = SetFitTrainer(
    model=model,
    batch_size=BATCH_SIZE,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    metric=compute_metrics, # Use custom metrics function
)

logging.info("Starting training...")
trainer.train(
    num_epochs=NUM_EPOCHS_BODY, # Body epochs go here
    learning_rate=LEARNING_RATE,
    num_epochs_classification_head=NUM_EPOCHS_HEAD
)
logging.info("Training finished.")

# --- Evaluation ---
logging.info("Evaluating model on the evaluation set...")
# Use the trainer's evaluation method which applies the trained head
evaluation_results = trainer.evaluate() # evaluate() uses the eval_dataset defined in trainer
logging.info(f"Evaluation results (Trainer): {evaluation_results}")

# For a more detailed report
logging.info("Generating detailed classification report...")
y_true = eval_dataset["label"]
# Ensure the model used for prediction has the trained classification head
final_model = trainer.model
y_pred = final_model.predict(eval_dataset["text"])

try:
    report = classification_report(y_true, y_pred, target_names=[f"Class {i}" for i in sorted(df['label'].unique())])
    logging.info(f"Classification Report:\n{report}")
except Exception as e:
    logging.error(f"Could not generate classification report: {e}")


# --- Save Model ---
logging.info(f"Saving model to {MODEL_SAVE_PATH}")
# Ensure the directory exists
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
# Save the final model from the trainer
final_model.save_pretrained(MODEL_SAVE_PATH)
logging.info("Model saved successfully.")

print(f"\n--- Training Summary ---")
print(f"Model trained: {BASE_MODEL_ID}")
print(f"Training data size: {len(train_df)}")
print(f"Evaluation data size: {len(eval_df)}")
print(f"Evaluation Accuracy (from Trainer): {evaluation_results.get('accuracy', 'N/A'):.4f}")
print(f"Evaluation F1 (weighted, from Trainer): {evaluation_results.get('f1', 'N/A'):.4f}")
print(f"Model saved to: {MODEL_SAVE_PATH}")
print("------------------------")