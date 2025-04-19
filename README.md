# Facebook Comment Text-Analytics Project – README ![status](https://img.shields.io/badge/status-Phase3_InProgress-yellow) ![target](https://img.shields.io/badge/target-JAMS-blue)

## Project Goal
This repository accompanies the study **"DEI Rollbacks, Brand Authenticity, and Consumer Reaction on Social Media"** (target journal: _Journal of the Academy of Marketing Science_).
We analyze **~34,000 public Facebook comments** (collected Jan-Mar 2025) posted during a ±30‑day window around four companies' DEI decisions to quantify (planned):

1. **Relevance** – whether a comment addresses DEI.
2. **Stance** – pro‑DEI, anti‑DEI, or neutral.
3. **Purchase intent** – buy, boycott, or neutral intentions.

The planned pipeline will then **causally estimate shifts in boycott‑ and buy‑rates** via a Triple‑Difference (DDD) design moderated by brand authenticity.

---

## Compliance & Ethics Summary
See `/docs/ethics.md` for **CGU IRB Exempt status (Protocol TBD)**, Meta/Facebook TOS compliance, and privacy safeguards.
_Key points_: human‑initiated collection (Phase 1 complete), public comments only, no PII stored post-processing (planned Phase 2a).

---

## Directory Layout (Current & Planned)
```text
root/
│  README.md
│  LICENSE
│  CITATION.cff
│  environment.yml          ← Conda env lock‑file (Python 3.10, includes Label Studio)
│  project.yml              ← Workflow config (defines commands like combine_raw_csvs)
│
├─data/
│   ├─raw/                  ← Raw JSON data (local only, **not** committed)
│   │  └─<Company>/<Phase>/
│   │     YYYYMMDD_HHMM.json
│   │     comments-csv/       # Output of process_comments_json.py (Step 2a)
│   └─derived/              ← Processed data outputs
│        combined_comments.csv     # Output of combine_company_csv.py (Step 2b)
│        graphed_comments.csv      # Output of graph_features.py (Step 2c)
│        cleaned_threaded_comments.csv # (Planned - Phase 3 Output)
│        comments_with_relevance.csv # (Planned - Phase 4 Output)
│        comments_with_stance_pi.csv # (Planned - Phase 5 Output)
│
├─docs/                     ← Documentation (Data Statement, Ethics, Methodology)
│   ethics.md
│   data_statement.md
│   methodology.md
│   (IRB_exemption.pdf)     # (Placeholder for final document)
│
├─scripts/
│   ├─extract/              ← Data collection script
│   │  comment_extractor.js # (Used in Phase 1)
│   ├─preprocess/           ← Data cleaning & feature scripts
│   │  process_comments_json.py # (Step 2a) Parses raw JSON
│   │  combine_company_csv.py # (Step 2b) Combines raw CSVs, adds flags
│   │  graph_features.py     # (Step 2c) Adds thread graph features
│   │  # text_cleaner.py       # (Placeholder for Phase 3a cleaning script)
│   │  # thread_builder.py     # (Placeholder for Phase 3b thread field script)
│   ├─annotate/             ← Annotation setup & guidelines
│   │  label_studio_config.xml # Label Studio UI configuration
│   │  annotation_guidelines.md # (Planned) Guidelines for coders
│   │  # small_text_sampler.py # Removed: Not using active learning ML backend
│   ├─model/                ← (Planned) Model training & helper scripts
│   │  train_setfit.py         # (Planned)
│   │  train_deberta_lora.py   # (Planned)
│   │  prompts/                # (Planned) LLM prompts for synthetic data
│   │     gpt4o_synthetic_prompt.txt # (Planned)
│   └─analysis/             ← (Planned) Causal analysis scripts
│      did_results.py          # (Planned) DDD analysis script
│
├─notebooks/                ← (Planned) Exploratory Data Analysis & Diagnostics
│   EDA_threads.ipynb        # (Planned)
│   Diagnostics_bias.ipynb   # (Planned)
│
├─tests/                    ← Unit tests
│   test_graph_features.py
│   test_process_pipeline.py # Includes tests for cleaning & conversion
│
└─results/                  ← Outputs: model checkpoints, figures, tables
    model_artifacts/         # (Planned)
    figures/                 # (Planned)
    tables/                  # (Planned)
```

---

## Quick‑Start (Planned Workflow)
```bash
# 1 – Create environment (Python 3.10 required)
# environment.yml now includes core dependencies + Label Studio
conda env create -f environment.yml
conda activate fb-text

# 2 – Run Preprocessing Steps (via project.yml commands)
# (Assumes raw data is placed in data/raw/<Company>/<Phase>/)
# python scripts/preprocess/process_comments_json.py ... # Step 2a (Run per company/phase)
# spacy project run combine_raw_csvs                    # Step 2b (Defined in project.yml)
# spacy project run preprocess_graph                    # Step 2c (Defined in project.yml)

# 3 - Run Text Preprocessing & Threading (Planned - Phase 3)
# (Commands TBD, assumes scripts like text_cleaner.py, thread_builder.py exist)
# python scripts/preprocess/text_cleaner.py ...
# python scripts/preprocess/thread_builder.py ...

# 4 - Run Annotation Prep & Annotation (Planned - Phase 4 & 5 - Manual Steps Required)
# (Script for stratified sampling - Step 4a & 5a - TBD)
# Start Label Studio (e.g., `label-studio start my_project`)
# Set up project(s) using `scripts/annotate/label_studio_config.xml`.
# Import data (e.g., sampled comment IDs/text) via UI or CLI.
# Set up user accounts for annotators.
# --> Perform annotation in the Label Studio UI (Step 4b & 5b) <--
# Export annotations for each coder/task.

# 5 – Train models & Predict (Planned - Phase 4c/d & 5c)
# python scripts/model/train_setfit.py ...        # Step 4c
# (Script/command for SetFit prediction - Step 4d - TBD)
# python scripts/model/train_deberta_lora.py ...  # Step 5c
# (Script/command for DeBERTa prediction - Needs Phase 5 output - TBD)

# 6 – Run unit tests
pytest tests/

# 7 – (Optional) Run causal Difference-in-Differences analysis (Planned - Phase 6)
# spacy project run analyze # Step 6b (Defined in project.yml)
# python scripts/analysis/did_results.py ... # Or run script directly
```

---

## Data Collection Methodology

### Phase 1 – Manual Extraction (Completed)
1. Scroll a public Facebook post until **all comments/replies are visible**.
2. Open **DevTools → Console** and paste `scripts/extract/comment_extractor.js` (captures each `div[role="article"]` outerHTML).
3. Save the JSON as `YYYYMMDD_HHMM.json` in `/data/raw/<Company>/<Phase>/`.

### Phase 2 – JSON Processing (In Progress)
1.  **Step 2a:** `scripts/preprocess/process_comments_json.py` parses raw JSON files, extracts key fields, cleans them, parses timestamps, adds metadata (stripping PII), and saves individual CSV files to `data/raw/<Company>/<Phase>/comments-csv/`.
2.  **Step 2b:** `scripts/preprocess/combine_company_csv.py` (run via `project.yml` command `combine_raw_csvs`) combines the individual CSVs, adds `company_name`, assigns `has_DEI`/`before_DEI` flags, deduplicates, and saves to `data/derived/combined_comments.csv`.
3.  **Step 2c:** `scripts/preprocess/graph_features.py` (run via `project.yml` command `preprocess_graph`) reads `combined_comments.csv`, calculates conversational thread features (root ID, depth, sibling count, time since root), and saves the enriched data to `data/derived/graphed_comments.csv`.

#### Processed Output Columns (`graphed_comments.csv`)

| Column            | Description                               | Source Script |
|-------------------|-------------------------------------------|---------------|
| `company_name`    | Company slug                              | process_comments | 
| `post_date`       | Source post timestamp                     | process_comments |
| `comment_text`    | Raw comment text                          | process_comments |
| `comment_date`    | Approx. comment date (parsed "2d", "5w")  | process_comments |
| `id`              | Unique comment identifier                 | process_comments |
| `parent_id`       | Parent comment ID                         | process_comments |
| `reaction_count`  | UI reactions                              | process_comments |
| `comment_type`    | `initial` / `reply`                       | process_comments |
| `root_id`         | ID of the root comment in the thread      | graph_features |
| `depth`           | Edges from root (root=0)                  | graph_features |
| `sibling_count`   | Comments with the same parent             | graph_features |
| `time_since_root` | Timedelta from root comment               | graph_features |
| `has_DEI`         | Treatment flag based on company           | combine_company_csv |
| `before_DEI`      | Treatment flag based on comment date      | combine_company_csv |

---

## Annotation (Planned - Phase 4 & 5)

*   **Tool:** **Label Studio** will be used for annotation.
    *   Interface defined in `scripts/annotate/label_studio_config.xml`.
*   **Phase 4 (Relevance):**
    *   **Step 4a:** Sample 500 comments (stratified by company) from `cleaned_threaded_comments.csv`.
    *   **Step 4b:** Annotate for `relevance` (0=not DEI-related, 1=DEI-related).
*   **Phase 5 (Stance & Purchase Intention):**
    *   **Step 5a:** Sample 1,000 comments (stratified by company) from *relevant* comments (`relevance=1`).
    *   **Step 5b:** Annotate for `stance_dei` (−1=anti, 0=neutral, 1=pro) and `purchase_intention` (−1=boycott, 0=neutral, 1=buy).
*   **Process:** Dual coding planned (Target: **Cohen's κ ≥ 0.75**). Disagreements will be reconciled.

---

## Modeling Pipeline (Planned - Phase 4 & 5)

| Task                  | Phase | Planned Model (link)                                                                         | Planned Notes                  | Script (Planned)                 | Output (Planned)                      |
|-----------------------|-------|----------------------------------------------------------------------------------------------|----------------------------------|----------------------------------|---------------------------------------|
| **Relevance**         | 4c, 4d| [`SetFit/all‑MiniLM‑L6‑v2`](https://huggingface.co/setfit/all-MiniLM-L6-v2)                  | Few‑shot, CPU‑friendly           | `scripts/model/train_setfit.py`    | `data/derived/comments_with_relevance.csv` |
| **Stance & Purchase** | 5c    | [`microsoft/deberta-v3-large`](https://huggingface.co/microsoft/deberta-v3-large) + **LoRA** | PEFT adapter, focal loss         | `scripts/model/train_deberta_lora.py` | `data/derived/comments_with_stance_pi.csv`  |

---

## Causal Analysis (Planned - Phase 6)

Planned Difference-in-Differences (DiD) on weekly rates using Python (`statsmodels`/`linearmodels`):
```text
# Planned Specification (example):
rate ~ Rollback * Post + PBA + controls + C(brand) + C(week)
```
Implementation planned in `/scripts/analysis/did_results.py` (outputs to `/results/`), potentially run via `project.yml` command `analyze`.

---

## Synthetic‑Data (Conditional Workflow - Planned)

To be activated **only if** real‑data model performance is insufficient (e.g., macro‑F1 < target or minority recall < 0.60).

1. Generate ≤ 1 synthetic comment per real label via GPT‑4o (`/scripts/model/prompts/`).
2. Filter with OpenAI self‑critique + perplexity checks.
3. Retrain; retain only if F1 improves significantly on real‑only test set.
4. Run toxicity & demographic bias checks (`/notebooks/Diagnostics_bias.ipynb`).

---

## Reproducibility & Replication (Planned)

* Goal: Every figure/table generated by code (`/scripts/`, `/notebooks/`) outputting to `/results/`.
* `project.yml` and `environment.yml` will define the workflow and dependencies.
* **Zenodo DOI** badge will be added on first release.
* OSF archive + GitHub tag (`v1.0.0`) will freeze artifacts upon completion.
* Random seeds will be set in `project.yml` & training scripts.

---

## Citation
```bibtex
@misc{estuar2025dei,
  author       = {Estuar, Diego},
  title        = {DEI Rollbacks, Brand Authenticity, and Consumer Reaction on Social Media},
  howpublished = {GitHub repository, \url{https://github.com/destuar/Facebook-TextAnalytics-Project}},
  year         = {2025},
  note         = {Working paper, target: Journal of the Academy of Marketing Science. Phase 2 (Preprocessing) in progress.}
}
```
---

## License

* **Code & prompts:** MIT License
* **Derived, de‑identified datasets & synthetic comments (Planned):** CC‑BY‑4.0
* **Raw Facebook JSON:** _not_ redistributed (Meta TOS).


