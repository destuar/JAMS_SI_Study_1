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
│  environment.yml          ← (Planned) Python 3.10 Conda env lock‑file (currently empty)
│  project.yml              ← (Planned) spaCy workflow config (currently empty)
│
├─data/
│   ├─raw/                  ← Raw JSON data (local only, **not** committed)
│   └─derived/              ← Processed data outputs
│        combined_comments.csv   # Output of process_comments_json.py
│        graphed_comments.csv    # Output of graph_features.py
│      # labels_gold.csv         # (Planned - Phase 3)
│      # labels_predicted.csv    # (Planned - Phase 3)
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
│   │  graph_features.py     # Adds thread graph features
│   │  process_comments_json.py # Parses raw JSON
│   ├─annotate/             ← (Planned) Annotation setup & guidelines
│   │  annotation_guidelines.md # (Planned)
│   │  label_interface.json    # (Planned)
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
├─tests/                    ← (Planned) Unit tests
│   test_graph_features.py   # (Planned)
│   test_process_pipeline.py # (Planned)
│
└─results/                  ← (Planned) Outputs: model checkpoints, figures, tables
    model_artifacts/         # (Planned)
    figures/                 # (Planned)
    tables/                  # (Planned)
```

---

## Quick‑Start (Planned Workflow)
```bash
# 1 – Create environment (Python 3.10 required)
# NOTE: environment.yml is currently empty. Populating it is part of Phase 2.
# conda env create -f environment.yml
# conda activate fb-text

# 2 – Run Preprocessing Steps (Manual for now)
# python scripts/preprocess/process_comments_json.py <raw_json_dir> data/derived/combined_comments.csv
# python scripts/preprocess/graph_features.py data/derived/combined_comments.csv data/derived/graphed_comments.csv

# 3 – Run the entire spaCy project pipeline (Preprocessing -> Training -> Export)
# NOTE: project.yml orchestration is not yet implemented (Planned Phase 2/3).
# spacy project run all

# 4 – Verify installation & run unit tests (Planned)
# python -m spacy validate
# pytest tests/

# 5 – (Optional) Train models manually (Planned - Phase 3)
# python scripts/model/train_setfit.py
# python scripts/model/train_deberta_lora.py

# 6 – (Optional) Run causal Triple‑Difference analysis (Planned - Phase 4)
# python scripts/analysis/did_results.py
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

* **Planned label schema**
  * `relevance` ∈ {0, 1}
  * `stance` ∈ {–1 (anti), 0, +1 (pro)}
  * `purchase` ∈ {–1 (boycott), 0, +1 (buy)}
  * `ideology_cue` ∈ {liberal, conservative, neutral/unknown}
* **Planned Gold set**: ≈1,300 comments, dual‑coded (Target: **Cohen's κ ≥ 0.75**).
* **Planned Active learning**: entropy sampling with **`small-text`** to add ≈400 labels (Total Gold ≈ 1,700).

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

