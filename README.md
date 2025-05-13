# Facebook Comment Text-Analytics Project – README ![status](https://img.shields.io/badge/status-Phase5_Complete-green) ![target](https://img.shields.io/badge/target-JAMS-blue)

## Project Goal
This repository accompanies the study **"DEI Rollbacks, Brand Authenticity, and Consumer Reaction on Social Media"** (target journal: _Journal of the Academy of Marketing Science_).
We analyze **~33,000 public Facebook comments** (collected Jan-Mar 2025) posted during a ±30‑day window around four companies' DEI decisions to quantify:

1. **Relevance** – whether a comment addresses DEI.
2. **Stance** – pro‑DEI, anti‑DEI, or neutral.
3. **Purchase intent** – buy, boycott, or neutral intentions.

The project focused on data processing, annotation, and predictive modeling of these reactions.

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
│
├─data/
│   ├─raw/                  
│   │  └─<Company>/<Phase>/
│   │     YYYYMMDD_HHMM.json
│   │     comments-csv/       
│   ├─derived/             
│   │    combined_comments.csv
│   │    graphed_comments.csv
│   │    cleaned_threaded_comments.csv
│   │    comments_with_relevance.csv
│   │    comments_with_sentiment.csv
│   └─annotate/             
│      ├─sample/
│      │  relevance_sample.csv
│      │  sentiment_sample.csv
│      ├─complete/
│      │  combined_relevance_annotations.csv
│      │  combined_sentiment_annotations.csv
│      ├─instructions/
│      │  ANNOTATION_README.md
│      │  relevance_labeling_config.xml
│      │  sentiment_labeling_config.xml
│      └─ls_data/
│
├─docs/
│   ethics.md
│   data_statement.md
│   methodology.md
│
├─scripts/
│   ├─extract/
│   │  comment_extractor.js
│   │  process_comments_json.py
│   ├─preprocess/
│   │  combine_company_csv.py
│   │  graph_features.py
│   │  clean_comments.py
│   ├─annotate/
│   │  sample_for_relevance.py
│   │  sample_for_sentiment.py
│   ├─model/
│   │  train_relevance_model.py
│   │  apply_relevance_model.py
│   │  causal_analysis.ipynb
│   └─visualize/
│   │  EDA_analysis.py
│   │  plot_post_graph.py
│
├─tests/
│   test_graph_features.py
│   test_process_pipeline.py
│
└─results/
    figures/
    tables/
    visualizations/
```

---

## Data Collection Methodology

### Phase 1 – Manual Extraction
1. Scroll a public Facebook post until **all comments/replies are visible**.
2. Open **DevTools → Console** and paste `scripts/extract/comment_extractor.js` (captures each `div[role="article"]` outerHTML).
3. Save the JSON as `YYYYMMDD_HHMM.json` in `/data/raw/<Company>/<Phase>/`.

### Phase 2 – JSON Processing
1.  **Step 2a:** `scripts/extract/process_comments_json.py` parses raw JSON files, extracts key fields, cleans them, parses timestamps, adds metadata (stripping PII), and saves individual CSV files to `data/raw/<Company>/<Phase>/comments-csv/`.
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

## Citation
```bibtex
@misc{estuar2025dei,
  author       = {Estuar, Diego},
  title        = {DEI Rollbacks, Brand Authenticity, and Consumer Reaction on Social Media},
  howpublished = {GitHub repository, \url{https://github.com/destuar/Facebook-TextAnalytics-Project}},
  year         = {2025},
  note         = {Working paper, target: Journal of the Academy of Marketing Science. Phase 5 (Modeling) complete.}
}
```
---

## License

* **Code & prompts:** MIT License
* **Raw Facebook JSON:** _not_ redistributed (Meta TOS).


