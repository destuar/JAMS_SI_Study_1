# Supplementary Methodology – Study 1 (Text‑Only Field Study)

> **Note** Numbers in ▢ brackets are placeholders and will be filled once final annotation counts are known.

---

## A. Hypothesis map

| ID | Hypothesis | Data source |
|----|------------|-------------|
| **H1** | *Rollback* (vs *Keep*) DEI → ↑ boycott‑rate & ↓ buy‑rate | Comment‑level Purchase‑Intent (PI) labels |
| **H2** | High ex‑ante **Perceived Brand Authenticity (PBA)** attenuates boycott effect | External survey scale |

*Mediated paths via Self‑Brand Connection are reserved for Study 2.*

---

## B. End-to-end Python pipeline (overview)

| Step | Phase | Tool / script | Output |
|------|-------|---------------|--------|
| 1    | 1     | Manual DOM scraper (JS) → `scripts/extract/comment_extractor.js` | Raw JSON (in `data/raw/`) |
| 2a   | 2a    | `scripts/preprocess/process_comments_json.py` (moved to `scripts/extract/` by user) | Individual CSVs (`data/raw/<...>/comments-csv/`) |
| 2b   | 2b    | `scripts/preprocess/combine_company_csv.py` (Cmd: `combine_raw_csvs`) | `data/derived/combined_comments.csv` |
| 2c   | 2c    | `scripts/preprocess/graph_features.py` (Cmd: `preprocess_graph`) | `data/derived/graphed_comments.csv` |
| 3    | 3a, 3b| Text cleaning (`scripts/preprocess/clean_comments.py`) & `full_text` creation (e.g., in notebook or `clean_comments.py`) | `data/derived/cleaned_threaded_comments.csv` |
| 4    | 4a, 5a| Sampling for annotation (`scripts/annotate/sample_for_relevance.py`, `scripts/annotate/sample_for_sentiment.py`) | `data/annotate/sample/relevance_sample.csv`, `data/annotate/sample/sentiment_sample.csv` |
| 5    | 4b, 5b| **Label Studio** annotation (see `data/annotate/instructions/ANNOTATION_README.md`) | `data/annotate/complete/combined_relevance_annotations.csv`, `data/annotate/complete/combined_sentiment_annotations.csv` |
| 6    | 4c    | **SetFit** fine-tuning (`scripts/model/train_relevance_model.py`) | Relevance model artifact (Location TBD) |
| 7    | 4d    | **SetFit** prediction (`scripts/model/apply_relevance_model.py`) | `data/derived/comments_with_relevance.csv` |
| 8    | 5c    | **GPT-4o API** via `models/sentiment_gpt4o_model/text_analytics.ipynb` (Evaluation on `combined_sentiment_annotations.csv`) | Stance & PI predictions on 1k sample (`models/sentiment_gpt4o_model/dev_1000_with_gpt_preds_full.csv`) |
| 9    | 5c    | **GPT-4o API** via `models/sentiment_gpt4o_model/text_analytics.ipynb` (Prediction on `comments_with_relevance.csv`) | `data/derived/comments_with_sentiment.csv` |
| 10   | 6a, 6b| **statsmodels / linearmodels** `scripts/analysis/did_results.py` (Cmd: `analyze`) | Tables & event-study plots (Planned) |

Commands orchestrated via `project.yml`; environment captured in `environment.yml` (conda).

---

## C. Classification performance (held-out test – placeholders)

| Task | F1 (Macro Avg) | Accuracy | Notes |
|------|----|-------------------------|-------|
| Relevance (SetFit) | ▢ TBD | ▢ TBD | On held-out test set for `comments_with_relevance.csv` |
| Stance (GPT-4o) | 0.9245 | 0.9630 | On 1k annotated sample (`dev_1000_with_gpt4o_preds_full.csv`) |
| Purchase Intention (GPT-4o) | 0.9044 | 0.9600 | On 1k annotated sample (`dev_1000_with_gpt4o_preds_full.csv`) |

---

## D. Difference-in-Difference (DiD) specification

Python implementation uses **statsmodels 0.14** with clustered standard errors.

```python
import statsmodels.formula.api as smf
model = smf.wls(
    formula="rate ~ Rollback * Post + PBA + depth + is_reply + C(brand) + C(week)",
    data=panel_df,
    weights=panel_df["n_comments"],
).fit(cov_type="cluster", cov_kwds={"groups": panel_df["brand_week"]})
```

* `rate` = weekly boycott- or buy-rate.
* Fixed effects via categorical dummies for brand & ISO week.
* Event-study and placebo graphs generated with `linearmodels` DID utilities.

---

## E. Robustness & transparency checklist

* **Depth / reply covariates** – (Planned) to be included, check stability.
* **Multiple testing** – (Planned) Benjamini-Hochberg (FDR 0.10) across coefficient families.
* **Non-DEI comment sensitivity** – (Planned) restrict to DEI-relevant subset; check robustness.
* **Re-running** – (Planned Goal) Aim for full pipeline reproducibility, possibly via `project.yml` or `make`.

---

## F. File manifest (Current & Planned - OSF repository TBD)

| File | Description |
|------|-------------|
| `data/derived/combined_comments.csv` | Combined comments from Step 2b |
| `data/derived/graphed_comments.csv` | Comments enriched with graph features (Step 2c) |
| `data/derived/cleaned_threaded_comments.csv` | Output of text cleaning/threading (Phase 3) |
| `data/derived/comments_with_relevance.csv` | Output of relevance prediction (Phase 4) |
| `data/derived/comments_with_sentiment.csv` | Output of stance/PI prediction using GPT-4o (Phase 5) |
| `data/annotate/sample/relevance_sample.csv` | Sampled comments for relevance annotation |
| `data/annotate/sample/sentiment_sample.csv` | Sampled comments for sentiment annotation |
| `data/annotate/complete/combined_relevance_annotations.csv` | Relevance annotations from Label Studio |
| `data/annotate/complete/combined_sentiment_annotations.csv` | Sentiment annotations from Label Studio (1k sample) |
| `data/annotate/instructions/ANNOTATION_README.md` | Annotation guidelines and Label Studio setup notes |
| `data/annotate/instructions/relevance_labeling_config.xml` | Label Studio config for relevance task |
| `data/annotate/instructions/sentiment_labeling_config.xml` | Label Studio config for sentiment task |
| `scripts/extract/comment_extractor.js` | Data collection script (Phase 1) |
| `scripts/extract/process_comments_json.py` | JSON parsing script (Step 2a) |
| `scripts/preprocess/combine_company_csv.py` | CSV combining script (Step 2b) |
| `scripts/preprocess/graph_features.py` | Graph feature calculation script (Step 2c) |
| `scripts/preprocess/clean_comments.py` | Text cleaning script (Phase 3a) |
| `# scripts/preprocess/thread_builder.py` | (Phase 3b script - `full_text` creation might be in `clean_comments.py` or notebook) |
| `scripts/annotate/sample_for_relevance.py` | Script to sample data for relevance annotation (Step 4a) |
| `scripts/annotate/sample_for_sentiment.py` | Script to sample data for sentiment annotation (Step 5a) |
| `scripts/model/train_relevance_model.py` | Relevance model training script (Phase 4c - SetFit) |
| `scripts/model/apply_relevance_model.py` | Relevance model application script (Phase 4d - SetFit) |
| `models/sentiment_gpt4o_model/text_analytics.ipynb` | Jupyter notebook for GPT-4o Stance/PI evaluation and prediction |
| `scripts/analysis/did_results.py` | (Planned) DiD regression script (Phase 6) |
| `docs/ethics.md` | Full compliance checklist |
| `docs/data_statement.md` | Dataset overview & details |
| `docs/methodology.md` | This document |
| `project.yml` | (Planned) Workflow orchestrator |
| `environment.yml` | (Planned) Conda environment |
| `results/model_artifacts/setfit_model/` | (Planned) Saved SetFit model for relevance |
| `models/sentiment_gpt4o_model/dev_1000_with_gpt4o_preds_full.csv` | GPT-4o predictions on 1k annotated sample |
| `results/tables/` | (Planned) Output tables from analysis |
| `results/figures/` | (Planned) Output figures from analysis |

---

**Contact:** Diego Estuar — diego.estuar@cgu.edu — 18 Apr 2025

