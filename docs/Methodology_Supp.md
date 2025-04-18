# Methodology: Analyzing Facebook Comment Reactions to Corporate DEI Actions

## Objective
This project analyzes **33,872** public Facebook comments surrounding corporate DEI decisions (collected **15 days before and 30 days after** the announcement) to quantify comment Relevance (to DEI), Stance (pro/anti/neutral), and Purchase Intent (buy/boycott/neutral). The methodology follows a phased, reproducible workflow designed for submission to the *Journal of the Academy of Marketing Science (JAMS)*, leveraging a specific, lean technology stack (see Phase 10).

## 1. Phase 1: Data Collection – Manual Extraction & Initial Processing
   - **Manual Comment Extraction:**
     - Navigate to a target public Facebook post.
     - Ensure all comments and replies are loaded by scrolling to the bottom.
     - Open browser Developer Tools (Console).
     - Paste and execute the content of `scripts/extract/comment_extractor.js`.
     - Copy the resulting JSON output block.
     - *Deliverable:* Raw comment data saved as `MM_DD_YY_HHMMAM.json` within company-specific `before_DEI` or `after_DEI` subfolders (e.g., `/data/raw/Target/after_DEI/`).
   - **JSON to CSV Processing:**
     - Run the Python script `scripts/process/process_comments_json.py`.
     - Provide the company folder name (e.g., `Target`) and filename stem when prompted.
     - The script parses the JSON, extracts relevant fields (comment text, timestamp text, reaction count, comment ID, parent ID), approximates comment dates from relative timestamps (e.g., "2d ago"), incorporates the post date from the filename, and adds the company name.
     - *Deliverable:* Processed, structured data saved as `MM_DD_YY_HHMMAM.csv` within the company folder.

## 2. Phase 2: Data Engineering – Thread & Text Cleaning
   - **Conversation Graph Reconstruction:** Utilize **NetworkX** to rebuild comment threads from the processed CSV data, calculating features like `root_id`, `depth`, `sibling_count`, and `time_since_root` via depth-first traversal. These features aid in understanding conversation dynamics and potentially improve model performance or allow study of cascade effects.
     - *Deliverable:* `graph_features.py`
   - **Text Normalization:** Employ a custom **spaCy v3.7** component, defined in `project.yml`, for standard text cleaning including lowercasing, URL removal, emoji handling (e.g., replacement with text descriptions), and lemmatization.
     - *Deliverable:* `pipeline_clean.py` registered in `project.yml`.
   - **Data Storage:** Use **DuckDB** for efficient storage and querying of processed data within a single-file database (`data.duckdb`).
     - *Deliverable:* `data.duckdb`

## 3. Phase 3: Gold Annotation – Ground Truth Creation
   - **Stratified Sampling:** Select 1,000 comments for manual annotation, stratified by company, week, and comment type (initial vs. reply). This stratification ensures linguistic and temporal diversity in the gold-standard dataset.
     - *Deliverable:* `sample.csv`
   - **Dual Annotation & Adjudication:** Two trained annotators label Relevance, Stance, and Purchase Intent for the sampled comments. Inter-coder reliability is targeted at Cohen's κ ≥ 0.75 to meet JAMS rigor, with discrepancies resolved through discussion.
     - *Deliverable:* `gold_labels.csv`

## 4. Phase 4: Active Learning – Efficient Label Expansion
   - **Initial Model Training:** Fine-tune a **SetFit** model (a CPU-friendly few-shot learner from Hugging Face) on the initial 1,000 gold labels to predict labels for the remaining ~27,000 comments.
     - *Deliverable:* `setfit_base.pkl`
   - **Uncertainty Sampling:** Use the **`small-text`** library to identify the 300 comments where the SetFit model is least confident (highest entropy) for targeted annotation.
     - *Deliverable:* `uncertain.csv`
   - **Iterative Annotation & Retraining:** Manually annotate the uncertain samples, merge them into the gold set, and retrain the SetFit model. Repeat this loop until development set F1 scores reach ≥ 0.85 for Relevance and ≥ 0.80 for Stance.
     - *Deliverable:* `gold_v2.csv` (final expanded gold set)

## 5. Phase 5: Modern Model Training – High-Performance Classification
   - **Transformer Fine-tuning:** Train a **DeBERTa-v3-Large** model using the **Hugging Face Transformers** library with Parameter-Efficient Fine-Tuning (**PEFT LoRA**) for the Stance and Purchase Intent tasks (Relevance is handled by the final SetFit model). This provides high accuracy with efficient training (~30 min on 16GB GPU).
     - *Deliverables:* `lora_adapter.bin`, `train_args.json`
   - **Handling Class Imbalance:** Implement a weighted **Focal Loss** layer directly in PyTorch (no external dependencies) to mitigate bias towards majority classes during training.
   - **Cross-Validation:** Evaluate model performance using 5-fold cross-validation, stratified by company, on the real-data gold standard set.
     - *Deliverable:* `cv_results.csv`

## 6. Phase 6: Decision Gate for LLM Augmentation
   - **Performance Check:** Evaluate the DeBERTa model's F1 scores and minority-class recall against predefined targets (e.g., Stance F1 ≥ 0.80, Recall > 0.60).
   - **Conditional Step:** Proceed to Phase 7 (LLM Augmentation) *only if* performance targets are not met on the real-data evaluation.
     - *Deliverable:* `gate_report.md` summarizing metrics and decision.

## 7. Phase 7: (Conditional) LLM-Generated Data Augmentation
   - **Synthetic Data Generation:** If triggered, use the **OpenAI GPT-4o API** to generate a maximum of one synthetic comment per real comment in the gold set, guided by specific prompts.
     - *Deliverable:* `synthetic_raw.jsonl`
   - **Filtering:** Apply **OpenAI self-critique** prompts and **perplexity filters** (e.g., `ppl ≤ 100`) to remove low-quality or noisy synthetic examples.
     - *Deliverable:* `synthetic_clean.jsonl`
   - **Retraining & Evaluation:** Retrain the DeBERTa-LoRA model on a combined dataset (real + filtered synthetic, ensuring synthetic data constitutes ≤ 50% of the total to avoid model collapse). Evaluate performance on an untouched *real-data* test set. Keep the augmented model only if it significantly improves F1 score (e.g., ≥ 1 pp).
     - *Deliverables:* `lora_aug_adapter.bin`, `aug_results.csv`

## 8. Phase 8: Full Dataset Inference & Aggregation
   - **Prediction Pipeline:** Apply the final trained models (SetFit for Relevance, DeBERTa-LoRA for Stance/Purchase) to predict labels for all **33,872** comments.
     - *Deliverable:* `predictions.parquet`
   - **Weekly Aggregation:** Use **pandas** to aggregate predicted labels weekly by company and stance, calculating key metrics like `boycott_rate` and `buy_rate` (potentially separating before/after periods).
     - *Deliverable:* `agg_weekly.csv`

## 9. Phase 9: Causal Analysis – Estimating Treatment Effects
   - **Triple Difference (DDD):** Employ a Triple Difference (DDD) panel model using **Stata** (`didregress`) following current best practices to estimate the causal impact of DEI decisions (`Rollback`) on weekly consumer reaction rates (`boycott_rate`, `buy_rate`). The model specification will be `rate ~ Rollback × Post × AntiStance`, including interactions with an ex-ante **brand authenticity score** (measured using a recent JAMS scale) to test its moderating effect. Control for **brand (company) and week fixed effects** and use robust standard errors clustered at the company level.
     - *Deliverables:* `did_results.do` (Stata script), event-study plots, authenticity interaction results.

## 10. Phase 10: Reproducibility & Archiving
    - **Code & Workflow:** Ensure all code, the **spaCy `project.yml`** file (orchestrating all commands), prompts, and synthetic data flags are version-controlled on **GitHub**.
      - *Deliverable:* `README.md` with clear run instructions.
    - **Data & Artifacts:** Archive final gold labels (`gold_v2.csv`), key notebooks, and model adapters on **OSF (Open Science Framework)**, obtaining a DOI. Raw Facebook text is explicitly excluded per Meta's TOS. Cite specific **JAMS transparency guidelines** in the manuscript.
      - *Deliverable:* OSF DOI link.
    - **Ethical Considerations:** Document data collection practices (including scraping policy adherence), privacy safeguards (de-identification), bias checks, and the use (if any) of synthetic data in an `ethics.md` file, adhering to JAMS guidelines.
      - *Deliverable:* `ethics.md`

## 11. Conclusion
This structured methodology aims to provide a robust, reproducible analysis of consumer reactions on social media, suitable for peer review and contributing to the understanding of brand authenticity and DEI communication impacts. 