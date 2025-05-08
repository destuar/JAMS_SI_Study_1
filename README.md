# Facebook Comment Text-Analytics Project – README ![status](https://img.shields.io/badge/status-Phase5_Complete-green) ![target](https://img.shields.io/badge/target-JAMS-blue)

## Project Goal
This repository accompanies the study **"DEI Rollbacks, Brand Authenticity, and Consumer Reaction on Social Media"** (target journal: _Journal of the Academy of Marketing Science_).
We analyze **~33,000 public Facebook comments** (collected Jan-Mar 2025) posted during a ±30‑day window around four companies' DEI decisions to quantify:

1. **Relevance** – whether a comment addresses DEI.
2. **Stance** – pro‑DEI, anti‑DEI, or neutral.
3. **Purchase intent** – buy, boycott, or neutral intentions.

The planned pipeline will then **causally estimate shifts in boycott‑ and buy‑rates** via a Triple‑Difference (DDD) design moderated by brand authenticity.

---

## Compliance & Ethics Summary
See `/docs/ethics.md` for Meta/Facebook TOS compliance and and privacy safeguards.
_Key points_: human‑initiated collection (Phase 1 complete), public comments only, no PII stored post-processing.

---

## Directory Layout
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
│   ├─derived/              ← Processed data outputs
│   │    combined_comments.csv     # Output of combine_company_csv.py (Step 2b)
│   │    graphed_comments.csv      # Output of graph_features.py (Step 2c)
│   │    cleaned_threaded_comments.csv # (Phase 3 Output)
│   │    comments_with_relevance.csv # (Phase 4 Output)
│   │    comments_with_sentiment.csv # (Phase 5 Output - GPT-4o predictions)
│   └─annotate/             ← Annotation-related files
│      ├─sample/            # Data samples for annotation
│      │  relevance_sample.csv
│      │  sentiment_sample.csv
│      ├─complete/          # Completed annotations from Label Studio
│      │  combined_relevance_annotations.csv
│      │  combined_sentiment_annotations.csv
│      ├─instructions/      # Annotation guidelines & Label Studio configs
│      │  ANNOTATION_README.md
│      │  relevance_labeling_config.xml
│      │  sentiment_labeling_config.xml
│      └─ls_data/           # Label Studio's internal data storage (if used directly)
│
├─docs/                     ← Documentation (Data Statement, Ethics, Methodology)
│   ethics.md
│   data_statement.md
│   methodology.md
│
├─scripts/
│   ├─extract/              ← Data collection script
│   │  comment_extractor.js # (Used in Phase 1)
│   │  process_comments_json.py # (Step 2a) Parses raw JSON
│   ├─preprocess/           ← Data cleaning & feature scripts
│   │  combine_company_csv.py # (Step 2b) Combines raw CSVs, adds flags
│   │  graph_features.py     # (Step 2c) Adds thread graph features
│   │  clean_comments.py       # (Phase 3a script)
│   ├─annotate/             ← Annotation setup & guidelines
│   │  sample_for_relevance.py # Script to sample data for relevance annotation
│   │  sample_for_sentiment.py # Script to sample data for sentiment annotation
│   │  # Annotation guidelines are in data/annotate/instructions/ANNOTATION_README.md
│   ├─model/                ← Model training & helper scripts
│   │  train_relevance_model.py # (Phase 4c script for Relevance - SetFit)
│   │  apply_relevance_model.py # (Phase 4d script for Relevance - SetFit)
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

## Data Collection Methodology

### Phase 1 – Manual Extraction
1. Scroll a public Facebook post until **all comments/replies are visible**.
2. Open **DevTools → Console** and paste `scripts/extract/comment_extractor.js` (captures each `div[role="article"]` outerHTML).
3. Save the JSON as `YYYYMMDD_HHMM.json` in `/data/raw/<Company>/<Phase>/`.

### Phase 2 – JSON Processing
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

## Annotation (Completed for 1k sample used in model evaluation/development)

*   **Tool:** **Label Studio** was used for annotation.
    *   Interface defined in `scripts/annotate/label_studio_config.xml` (and `data/annotate/instructions/` for specific tasks).
    *   Annotation guidelines: `data/annotate/instructions/ANNOTATION_README.md`.
*   **Phase 4 (Relevance):**
    *   **Step 4a:** Sampled 500 comments (`data/annotate/sample/relevance_sample.csv`) using `scripts/annotate/sample_for_relevance.py`.
    *   **Step 4b:** Annotated for `relevance`. Result: `data/annotate/complete/combined_relevance_annotations.csv`.
*   **Phase 5 (Stance & Purchase Intention):**
    *   **Step 5a:** Sampled 1,000 comments (`data/annotate/sample/sentiment_sample.csv`) using `scripts/annotate/sample_for_sentiment.py`. This forms the basis for `data/annotate/complete/combined_sentiment_annotations.csv`.
    *   **Step 5b:** Annotated for `stance_dei` (−1=anti, 0=neutral, 1=pro) and `purchase_intention` (−1=boycott, 0=neutral, 1=buy).
*   **Process:** Dual coding was planned (Target: **Cohen's κ ≥ 0.75**). Disagreements were reconciled. Kappa scores reported in `models/sentiment_gpt4o_model/text_analytics.ipynb`.

---

## Modeling Pipeline (Phase 4 & 5)

| Task                  | Phase | Model Used (link)                                                                         | Notes                                                  | Script / Notebook                 | Output                      |
|-----------------------|-------|----------------------------------------------------------------------------------------------|--------------------------------------------------------|----------------------------------|---------------------------------------|
| **Relevance**         | 4c, 4d| [`SetFit/all‑MiniLM‑L6‑v2`](https://huggingface.co/setfit/all-MiniLM-L6-v2)                  | Few‑shot, CPU‑friendly. Trained using `train_relevance_model.py` | `scripts/model/train_relevance_model.py` & `scripts/model/apply_relevance_model.py`    | `data/derived/comments_with_relevance.csv` |
| **Stance & Purchase** | 5c    | OpenAI GPT-4o API                                                                            | API-based, evaluated on 1k sample, then applied to full dataset | `models/sentiment_gpt4o_model/text_analytics.ipynb` | `data/derived/comments_with_sentiment.csv`  |

---

## Causal Analysis (Phase 6)

Difference-in-Differences (DiD) on weekly rates using Python (`statsmodels`/`linearmodels`):
```text
# Specification (example):
rate ~ Rollback * Post + PBA + controls + C(brand) + C(week)
```

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
* **Raw Facebook JSON:** _not_ redistributed (Meta TOS).


