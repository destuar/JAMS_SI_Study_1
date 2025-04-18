# Facebook Comment Text-Analytics Project – README ![status](https://img.shields.io/badge/status-Phase2_InProgress-yellow) ![target](https://img.shields.io/badge/target-JAMS-blue)

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
_Key points_: human‑initiated collection (Phase 1 complete), public comments only, no PII stored post-processing (planned).

---

## Directory Layout (Current & Planned)
```text
root/
│  README.md
│  LICENSE
│  CITATION.cff
│  environment.yml          ← Conda env lock‑file (Python 3.10, includes Label Studio)
│  project.yml              ← spaCy workflow config (includes annotation step)
│
├─data/
│   ├─raw/                  ← Raw JSON data (local only, **not** committed)
│   └─derived/              ← Processed data outputs
│        combined_comments.csv   # Output of combine_company_csv.py (or similar)
│        graphed_comments.csv    # Output of graph_features.py
│        labels_gold.csv         # (Planned - Phase 3 Output) Manually reconciled labels from annotation
│      # labels_predicted.csv    # (Planned - Phase 3 Output) Model predictions
│   └─corpus/                 ← spaCy DocBin files for train/dev/test splits
│        train.spacy           # Output of convert_to_docbin workflow step
│        dev.spacy             # Output of convert_to_docbin workflow step
│        test.spacy            # Output of convert_to_docbin workflow step
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
│   │  combine_company_csv.py # (Placeholder) Combines raw data
│   │  graph_features.py     # Adds thread graph features
│   │  clean_comments.py     # Cleans, splits, converts data to spaCy DocBin format
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

# 2 – Run Preprocessing Steps (via spaCy project)
# (Assumes raw data is placed in data/raw/<Company>/)
spacy project run preprocess # Runs combine -> graph -> convert_to_docbin

# 3 - Run Annotation (Phase 3 - Manual Steps Required)
# Start Label Studio (e.g., `label-studio start my_project`)
# Set up project(s) using `scripts/annotate/label_studio_config.xml`.
# Import data (e.g., from data/corpus/train.spacy) via UI or CLI.
# Set up user accounts for dual annotators.
# --> Perform annotation in the Label Studio UI <--
# Export annotations for each coder.
# Reconcile disagreements (manual/scripted) to produce labels_gold.csv.

# 4 – Run the entire spaCy project pipeline (Preprocessing -> Training -> Analysis)
# NOTE: Training/Analysis steps are placeholders. Annotation requires manual steps between.
# spacy project run all 

# 5 – Verify installation & run unit tests
# python -m spacy validate # Useful for checking spaCy installation
pytest tests/

# 6 – (Optional) Train models manually (Planned - Phase 3)
# python scripts/model/train_setfit.py ...
# python scripts/model/train_deberta_lora.py ...

# 7 – (Optional) Run causal Triple‑Difference analysis (Planned - Phase 4)
# python scripts/analysis/did_results.py ...
```

---

## Data Collection Methodology

### Phase 1 – Manual Extraction (Completed)
1. Scroll a public Facebook post until **all comments/replies are visible**.
2. Open **DevTools → Console** and paste `scripts/extract/comment_extractor.js` (captures each `div[role="article"]` outerHTML).
3. Save the JSON as `YYYYMMDD_HHMM.json` in `/data/raw/<Company>/`.

### Phase 2 – JSON Processing (In Progress)
1.  `scripts/preprocess/process_comments_json.py` parses raw JSON files, extracts key fields (text, date, reactions, etc.), and saves to `data/derived/combined_comments.csv`.
2.  `scripts/preprocess/graph_features.py` reads `combined_comments.csv`, calculates conversational thread features (root ID, depth, sibling count, time since root), and saves the enriched data to `data/derived/graphed_comments.csv`.
3.  `scripts/preprocess/pipeline_clean.py` defines a spaCy pipeline component for cleaning comment text (URL/mention replacement, emoji conversion, etc.).
4.  `scripts/preprocess/convert_comments.py` applies the cleaning component, stratifies `graphed_comments.csv` by company into train/dev/test splits, and saves the results as spaCy `DocBin` files (`.spacy`) in `data/derived/`.

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

---

## Annotation & Active Learning (Planned - Phase 3)

*   **Tool:** **Label Studio** will be used for annotation.
    *   Interface defined in `scripts/annotate/label_studio_config.xml`.
    *   Supports multi-label classification required for this project.
*   **Planned label schema:**
    *   `relevance` ∈ {0, 1}
    *   `stance` ∈ {–1 (anti), 0, +1 (pro)}
    *   `purchase` ∈ {–1 (boycott), 0, +1 (buy)}
    *   `ideology_cue` ∈ {liberal, conservative, neutral/unknown} (Optional)
*   **Planned Gold set:** ≈1,300 comments, dual‑coded (Target: **Cohen's κ ≥ 0.75**).
    *   Data to be annotated will primarily come from `data/corpus/train.spacy` (and potentially `dev.spacy`).
    *   **NOTE:** Since the train/dev/test split in Phase 2 is stratified only by `company_name`, care must be taken during annotation sampling to ensure adequate representation of potentially minority classes (e.g., `before_DEI = 1`) within the ~1,300 comments selected for the gold set.
    *   Dual coding will be managed by having annotators work independently in Label Studio (e.g., using separate user accounts or projects).
    *   Disagreements will be exported (e.g., as CSV/JSON) and reconciled manually or via a separate script to produce the final `labels_gold.csv`.
*   **Active learning:** (Removed from immediate plan) If needed later, Label Studio supports ML backends, but setup is simplified for now.

---

## Modeling Pipeline (Planned - Phase 3)

| Task                 | Planned Model (link)                                                                         | Planned Notes                  |
|----------------------|----------------------------------------------------------------------------------------------|----------------------------------|
| **Relevance**        | [`SetFit/all‑MiniLM‑L6‑v2`](https://huggingface.co/setfit/all-MiniLM-L6-v2)                  | Few‑shot, CPU‑friendly           |
| **Stance & Purchase**| [`microsoft/deberta-v3-large`](https://huggingface.co/microsoft/deberta-v3-large) + **LoRA** | PEFT adapter, focal loss         |
| **Ideology Cue**     | SetFit or similar weak-supervision + fine-tuning approach TBD                                | TBD                              |

---

## Causal Analysis (Planned - Phase 4)

Planned Triple‑Difference (DDD) on weekly rates using Python (`statsmodels`/`linearmodels`):
```text
# Planned Specification (example):
rate ~ Rollback * Post * LiberalCue + PBA + controls + C(brand) + C(week)
```
Implementation planned in `/scripts/analysis/did_results.py` (outputs to `/results/`).

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


