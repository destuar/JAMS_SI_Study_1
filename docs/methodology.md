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
| 2a   | 2a    | `scripts/preprocess/process_comments_json.py` | Individual CSVs (`data/raw/<...>/comments-csv/`) |
| 2b   | 2b    | `scripts/preprocess/combine_company_csv.py` (Cmd: `combine_raw_csvs`) | `data/derived/combined_comments.csv` |
| 2c   | 2c    | `scripts/preprocess/graph_features.py` (Cmd: `preprocess_graph`) | `data/derived/graphed_comments.csv` |
| 3    | 3a, 3b| (Text cleaning & thread field creation scripts TBD) | `data/derived/cleaned_threaded_comments.csv` |
| 4    | 4a, 4b| **Label Studio** annotation (Sample: 500 comments) | Relevance labels |
| 5    | 5a, 5b| **Label Studio** annotation (Sample: 1000 relevant comments) | Stance & PI labels |
| 6    | 4c    | **SetFit** fine-tuning (`train_setfit.py`) | Relevance model artifact |
| 7    | 4d    | **SetFit** prediction | `data/derived/comments_with_relevance.csv` |
| 8    | 5c    | **DeBERTa-LoRA** fine-tuning (`train_deberta_lora.py`) | `stance_pi_adapter.bin` (Planned) |
| 9    | 5c    | **DeBERTa-LoRA** prediction | `data/derived/comments_with_stance_pi.csv` |
| 10   | 6a, 6b| **statsmodels / linearmodels** `did_results.py` (Cmd: `analyze`) | Tables & event-study plots |

Commands orchestrated via `project.yml`; environment captured in `environment.yml` (conda).

---

## C. Classification performance (held-out test – placeholders)

| Task | F1 | Recall (minority class) |
|------|----|-------------------------|
| Relevance | ▢ TBD | ▢ TBD |
| Stance | ▢ TBD | ▢ TBD |
| Purchase Intention | ▢ TBD | ▢ TBD |

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
| `data/derived/cleaned_threaded_comments.csv` | (Planned) Output of text cleaning/threading (Phase 3) |
| `data/derived/comments_with_relevance.csv` | (Planned) Output of relevance prediction (Phase 4) |
| `data/derived/comments_with_stance_pi.csv` | (Planned) Output of stance/PI prediction (Phase 5) |
| `scripts/extract/comment_extractor.js` | Data collection script (Phase 1) |
| `scripts/preprocess/process_comments_json.py` | JSON parsing script (Step 2a) |
| `scripts/preprocess/combine_company_csv.py` | CSV combining script (Step 2b) |
| `scripts/preprocess/graph_features.py` | Graph feature calculation script (Step 2c) |
| `scripts/model/train_setfit.py` | (Planned) Relevance model training script (Phase 4) |
| `scripts/model/train_deberta_lora.py` | (Planned) Stance/PI model training script (Phase 5) |
| `scripts/analysis/did_results.py` | (Planned) DiD regression script (Phase 6) |
| `docs/ethics.md` | Full compliance checklist |
| `docs/data_statement.md` | Dataset overview & details |
| `docs/methodology.md` | This document |
| `project.yml` | (Planned) Workflow orchestrator |
| `environment.yml` | (Planned) Conda environment |
| `results/model_artifacts/setfit_model/` | (Planned) Saved SetFit model |
| `results/model_artifacts/stance_pi_adapter.bin` | (Planned) Saved DeBERTa LoRA adapter |
| `results/tables/` | (Planned) Output tables from analysis |
| `results/figures/` | (Planned) Output figures from analysis |

---

**Contact:** Diego Estuar — diego.estuar@cgu.edu — 18 Apr 2025

