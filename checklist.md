# Project Checklist

## [Phase 1] Data Engineering – Thread & text cleaning

### [ ] 1.1 Rebuild conversation graph; add root_id, depth, siblings, time_since_root
- These thread metrics can later boost stance accuracy and allow study of cascade effects.
- **Deliverable:** `graph_features.py`.

### [ ] 1.2 Write custom spaCy cleaning component
- Removes URLs, emojis, lower-cases, lemmatises.
- **Deliverable:** `pipeline_clean.py` registered in `project.yml`.

---

## [Phase 2] Gold Annotation – Ground truth

### [ ] 2.1 Sample 1,000 comments stratified by company × week × reply/initial
- Stratification ensures linguistic and temporal diversity in the training data.
- **Deliverable:** `sample.csv`.

### [ ] 2.2 Double-label Relevance, Stance, Purchase Intent (κ ≥ 0.75)
- Achieving κ ≥ 0.75 ensures inter-coder agreement meets JAMS rigor.
- **Deliverable:** `gold_labels.csv`.

---

## [Phase 3] Active Learning – Real-data expansion

### [ ] 3.1 Fine-tune SetFit on 1,000 labels; predict remaining 19,000
- **Deliverable:** `setfit_base.pkl`.

### [ ] 3.2 Select 300 most-uncertain rows with small-text entropy
- **Deliverable:** `uncertain.csv`.

### [ ] 3.3 Annotate & merge; iterate until dev F1 ≥ 0.85 (relevance) / 0.80 (stance)
- **Deliverable:** `gold_v2.csv` (expanded label set).

---

## [Phase 4] Modern Model Training – Real labels only

### [ ] 4.1 Train DeBERTa-v3-large + LoRA for Stance & Purchase
- This approach provides SOTA accuracy with efficient training (<30 min on 16 GB GPU).
- **Deliverables:** `lora_adapter.bin`, `train_args.json`.

### [ ] 4.2 Implement Weighted Focal Loss for class imbalance
- **Deliverable:** Loss module (code inline).

### [ ] 4.3 5-fold cross-validation stratified by company
- **Deliverable:** `cv_results.csv`.

---

## [Phase 5] Decision Gate for LLM Augmentation

### [ ] Trigger → if any task F1 < target or minority-class recall < 0.60.
- **Deliverable:** `gate_report.md` summarising metrics & decision.

---

## [Phase 6] (Conditional) LLM-Generated Boosters

### [ ] 6.1 Generate ≤ 1 synthetic comment per real label via GPT-4o prompt
- **Deliverable:** `synthetic_raw.jsonl`.

### [ ] 6.2 Self-critique + perplexity filter (ppl ≤ 100)
- **Deliverable:** `synthetic_clean.jsonl`.

### [ ] 6.3 Re-train DeBERTa-LoRA on real + synthetic; evaluate on untouched real test set
- **Deliverables:** `lora_aug_adapter.bin`, `aug_results.csv`.

---

## [Phase 7] Full Inference & Aggregation

### [ ] 7.1 Predict Relevance → Stance → Purchase for all 20k comments
- **Deliverable:** `predictions.parquet`.

### [ ] 7.2 Weekly aggregation by company × stance
- Computes `boycott_rate` & `buy_rate`.
- **Deliverable:** `agg_weekly.csv`.

---

## [Phase 8] Causal Analysis – Triple Difference for Backlash vs Support

### [ ] 8.1 Estimate Difference-in-Difference-in-Differences (DDD)
- **Model:** `y = β7 Rollback×Post×AntiStance + β8 Authenticity×Rollback×Post×AntiStance …`
- `y` = `boycott_rate` and `buy_rate`; includes brand & week fixed effects.
- **Deliverable:** `did_results.do` (Stata/R) + event-study plots.

---

## [Phase 9] Reproducibility Package

### [ ] 9.1 Push code, project.yml, prompts, synthetic flags to GitHub
- **Deliverable:** `README.md` with run instructions.

### [ ] 9.2 Archive gold labels + replication notebook on OSF (no raw FB text)
- **Deliverable:** DOI link.

### [ ] 9.3 Write Ethics & Data-provenance statement (scraping policy, bias tests)
- **Deliverable:** `ethics.md`.

---

## [Phase 10] Manuscript Material for JAMS

### [ ] 10.1 Methods section (~1,500 words)
- Covers Phases 1–8; explains causal design, authenticity moderator, assumptions, robustness.

### [ ] 10.2 Appendices A-1…A-4
- Prompt templates, hyper-parameters, active-learning stats, bias-check tables.

---

## Toolkit

### Environment & Version Control
- **Git + GitHub (private repo):** Canonical way to freeze code and history.
- **spaCy `project.yml`:** Orchestrates every command (`run all`) from raw data to trained models.

### Data Storage & Graph Features
- **DuckDB:** Single-file analytics database; SQL identical to Postgres.
- **NetworkX:** Build `root_id`, `depth`, etc., with depth-first traversal.

### Text Cleaning & Pre-processing
- **spaCy v3.7:** Tokenisation, lemmatisation, easy custom components; all defined in the project file.

### Annotation & Active Learning
- **SetFit (Hugging Face):** Few-shot baseline; runs CPU-only if needed.
- **small-text (GitHub):** Plug-and-play entropy sampling for uncertain comments.

### Model Fine-tuning
- **Transformers + PEFT LoRA (Hugging Face):** Parameter-efficient DeBERTa-v3 fine-tuning.
- **Focal-loss layer:** Single Torch module (no external dependencies).

### (Optional) Synthetic-Data Booster
- **OpenAI GPT-4o API:** One-call generation; pair with OpenAI self-critique to filter noise.
  - _Note:_ Synthetic share ≤ 50 % to avoid "model collapse".

### Aggregation & Causal Analysis
- **pandas:** Weekly `boycott_rate`, `buy_rate` aggregation (no heavy BI tooling).
- **Stata `didregress`/`xtdidregress`:** One-line DDD with robust SEs.

### Reproducibility & Archiving
- **OSF (OSF Support):** Deposit `gold_labels.csv`, notebooks, and adapters (but not raw FB text).
- **JAMS submission guidelines (SpringerLink):** Cite for ethics, data transparency, and replication package.

