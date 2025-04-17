# Methodology: Analyzing Facebook Comment Reactions to Corporate DEI Actions

## 1. Objective
This project analyzes ~20,000 public Facebook comments surrounding corporate DEI decisions to quantify comment Relevance (to DEI), Stance (pro/anti/neutral), and Purchase Intent (buy/boycott/neutral). The methodology follows a phased, reproducible workflow designed for submission to the *Journal of the Academy of Marketing Science (JAMS)*, leveraging specific tools outlined in `checklist.md`.

## 2. Phase 1: Data Engineering – Thread & Text Cleaning
   - **Conversation Graph Reconstruction:** Utilize NetworkX to rebuild comment threads from raw data, calculating features like `root_id`, `depth`, `sibling_count`, and `time_since_root`. These features aid in understanding conversation dynamics and potentially improve model performance.
     - *Deliverable:* `graph_features.py`
   - **Text Normalization:** Employ a custom spaCy v3.7 component, defined in `project.yml`, for standard text cleaning including lowercasing, URL removal, emoji handling (e.g., replacement with text descriptions), and lemmatization.
     - *Deliverable:* `pipeline_clean.py`

## 3. Phase 2: Gold Annotation – Ground Truth Creation
   - **Stratified Sampling:** Select 1,000 comments for manual annotation, stratified by company, week, and comment type (initial vs. reply). This ensures linguistic and temporal diversity in the gold-standard dataset.
     - *Deliverable:* `sample.csv`
   - **Dual Annotation & Adjudication:** Two trained annotators label Relevance, Stance, and Purchase Intent for the sampled comments. Inter-coder reliability is targeted at Cohen's κ ≥ 0.75, meeting JAMS standards, with discrepancies resolved through discussion.
     - *Deliverable:* `gold_labels.csv`

## 4. Phase 3: Active Learning – Efficient Label Expansion
   - **Initial Model Training:** Fine-tune a SetFit model (CPU-friendly few-shot learner) on the initial 1,000 gold labels to predict labels for the remaining ~19,000 comments.
     - *Deliverable:* `setfit_base.pkl`
   - **Uncertainty Sampling:** Use `small-text` library to identify the 300 comments where the SetFit model is least confident (highest entropy).
     - *Deliverable:* `uncertain.csv`
   - **Iterative Annotation & Retraining:** Manually annotate the uncertain samples, merge them into the gold set, and retrain the model. Repeat this loop until development set F1 scores reach ≥ 0.85 for Relevance and ≥ 0.80 for Stance.
     - *Deliverable:* `gold_v2.csv` (final expanded gold set)

## 5. Phase 4: Modern Model Training – High-Performance Classification
   - **Transformer Fine-tuning:** Train a DeBERTa-v3-Large model using the Hugging Face Transformers library with Parameter-Efficient Fine-Tuning (PEFT LoRA) for the Stance and Purchase Intent tasks (Relevance is handled by the final SetFit model). This provides high accuracy with efficient training (~30 min on 16GB GPU).
     - *Deliverables:* `lora_adapter.bin`, `train_args.json`
   - **Handling Class Imbalance:** Implement a weighted Focal Loss layer directly in PyTorch to mitigate bias towards majority classes during training.
   - **Cross-Validation:** Evaluate model performance using 5-fold cross-validation, stratified by company, on the real-data gold standard set.
     - *Deliverable:* `cv_results.csv`

## 6. Phase 5: Decision Gate for LLM Augmentation
   - **Performance Check:** Evaluate the DeBERTa model's F1 scores and minority-class recall against predefined targets (e.g., F1 > target, Recall > 0.60).
   - **Conditional Step:** Proceed to Phase 6 (LLM Augmentation) *only if* performance targets are not met on the real-data evaluation.
     - *Deliverable:* `gate_report.md`

## 7. Phase 6: (Conditional) LLM-Generated Data Augmentation
   - **Synthetic Data Generation:** If triggered, use the OpenAI GPT-4o API to generate a maximum of one synthetic comment per real comment in the gold set, guided by specific prompts.
     - *Deliverable:* `synthetic_raw.jsonl`
   - **Filtering:** Apply self-critique prompts and perplexity filters (e.g., ppl ≤ 100) to remove low-quality or noisy synthetic examples.
     - *Deliverable:* `synthetic_clean.jsonl`
   - **Retraining & Evaluation:** Retrain the DeBERTa-LoRA model on a combined dataset (real + filtered synthetic, ensuring synthetic data constitutes ≤ 50% of the total). Evaluate performance on an untouched *real-data* test set. Keep the augmented model only if it significantly improves F1 score (e.g., ≥ 1 pp).
     - *Deliverables:* `lora_aug_adapter.bin`, `aug_results.csv`

## 8. Phase 7: Full Dataset Inference & Aggregation
   - **Prediction Pipeline:** Apply the final trained models (SetFit for Relevance, DeBERTa-LoRA for Stance/Purchase) to predict labels for all ~20,000 comments.
     - *Deliverable:* `predictions.parquet`
   - **Weekly Aggregation:** Use pandas to aggregate predicted labels weekly by company and stance, calculating key metrics like `boycott_rate` and `buy_rate`.
     - *Deliverable:* `agg_weekly.csv`

## 9. Phase 8: Causal Analysis – Estimating Treatment Effects
   - **Difference-in-Differences:** Employ a Difference-in-Differences (potentially DDD including stance/authenticity interactions) framework using Stata (`didregress`/`xtdidregress`) to estimate the causal impact of DEI rollbacks on consumer reaction (e.g., `boycott_rate`), controlling for company and time (e.g., day-of-week) fixed effects.
     - *Deliverable:* `did_results.do` (Stata/R script), event-study plots

## 10. Phase 9: Reproducibility & Archiving
    - **Code & Workflow:** Ensure all code, the `project.yml` file, prompts, and synthetic data flags are version-controlled on GitHub.
      - *Deliverable:* `README.md` with clear run instructions.
    - **Data & Artifacts:** Archive final gold labels, key notebooks, and model adapters on OSF (Open Science Framework), obtaining a DOI. Raw Facebook text is explicitly excluded per Meta's TOS.
      - *Deliverable:* OSF DOI link.
    - **Ethical Considerations:** Document data collection practices, privacy safeguards (de-identification), bias checks, and the use (if any) of synthetic data in an `ethics.md` file, adhering to JAMS guidelines.
      - *Deliverable:* `ethics.md`

## 11. Conclusion
This structured methodology aims to provide a robust, reproducible analysis of consumer reactions on social media, suitable for peer review and contributing to the understanding of brand authenticity and DEI communication impacts. 