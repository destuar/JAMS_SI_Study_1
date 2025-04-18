# Supplementary Methodology – Study 1 (Text‑Only Field Study)

> **Note** Numbers in ▢ brackets are placeholders and will be filled once final annotation counts are known.

---

## A. Hypothesis map

| ID | Hypothesis | Data source |
|----|------------|-------------|
| **H1** | *Rollback* (vs *Keep*) DEI → ↑ boycott‑rate & ↓ buy‑rate | Comment‑level Purchase‑Intent (PI) labels |
| **H2** | Effect magnitude larger in comments with **liberal lexical cues** than **conservative cues** | Ideology‑cue classifier |
| **H3** | High ex‑ante **Perceived Brand Authenticity (PBA)** attenuates boycott effect | External survey scale |

*Mediated paths via Self‑Brand Connection are reserved for Study 2.*

---

## B. End-to-end Python pipeline (overview)

| Step | Tool / script | Output |
|------|---------------|--------|
| 1  Collection | Manual DOM scraper (JS) → `scripts/extract/comment_extractor.js` | Raw JSON (in `data/raw/`) |
| 2a Base Processing | `scripts/preprocess/process_comments_json.py` | `data/derived/combined_comments.csv` |
| 2b Graph Features | `scripts/preprocess/graph_features.py` (**NetworkX** used) | `data/derived/graphed_comments.csv` |
| 3  Gold annotation (Planned) | *Prodigy* dual coders ▢ **TBD** comments | `gold_v1.csv` (Planned) |
| 4  Ideology cue coding (Planned) | Weak-supervision lexicon + ▢ **TBD** hand-labels; fine-tuned **SetFit** | `ideology_preds.parquet` (Planned) |
| 5  Model training (Planned) | **DeBERTa-v3-Large** + PEFT-LoRA; weighted focal loss | `stance_pi_adapter.bin` (Planned) |
| 6  Full inference (Planned) | Batch predict → weekly aggregation | `agg_weekly.csv` (Planned) |
| 7  Causal analysis (Planned) | **statsmodels / linearmodels** `PanelOLS` DID script (`did_results.py`) | Tables & event-study plots (Planned) |

(Planned) Commands orchestrated via `project.yml`; environment captured in `environment.yml` (conda). *(Currently empty placeholders)*

---

## C. Classification performance (held-out test – placeholders)

| Task | F1 | Recall (minority class) |
|------|----|-------------------------|
| Relevance | ▢ TBD | ▢ TBD |
| Stance | ▢ TBD | ▢ TBD |
| Purchase Intention | ▢ TBD | ▢ TBD |
| Ideology Cue | ▢ TBD | ▢ TBD |

---

## D. Difference-in-Difference-in-Differences (DDD) specification

Python implementation uses **statsmodels 0.14** with clustered standard errors.

```python
import statsmodels.formula.api as smf
model = smf.wls(
    formula="rate ~ Rollback * Post * LiberalCue + PBA + depth + is_reply + C(brand) + C(week)",
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
| `data/derived/combined_comments.csv` | Parsed comments from raw JSON |
| `data/derived/graphed_comments.csv` | Comments enriched with graph features |
| `scripts/extract/comment_extractor.js` | Data collection script |
| `scripts/preprocess/process_comments_json.py` | JSON parsing script |
| `scripts/preprocess/graph_features.py` | Graph feature calculation script |
| `docs/ethics.md` | Full compliance checklist |
| `docs/data_statement.md` | Dataset overview & details |
| `docs/methodology.md` | This document |
| `project.yml` | (Planned) spaCy project orchestrator *(currently empty)* |
| `environment.yml` | (Planned) Conda environment *(currently empty)* |
| `did_results.py` | (Placeholder Name) Planned DDD regression script (Python) |
| `gold_v1.csv` | (Planned) Annotated sample (▢ TBD rows, de-identified) |
| `stance_pi_adapter.bin` | (Planned) LoRA adapter (≈ 100 MB) |

---

**Contact:** Diego Estuar — diego.estuar@cgu.edu — 18 Apr 2025

