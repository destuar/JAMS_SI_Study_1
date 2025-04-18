# Supplementary Methodology – Study 1 (Text‑Only Field Study, **Python‑only** workflow)

> **Note** Numbers in ▢ brackets are placeholders and will be filled once final annotation counts are known.

---

## A. Hypothesis map

| ID | Hypothesis | Data source |
|----|------------|-------------|
| **H1** | *Rollback* (vs *Keep*) DEI → ↑ boycott‑rate & ↓ buy‑rate | Comment‑level Purchase‑Intent (PI) labels |
| **H2** | Effect magnitude larger in comments with **liberal lexical cues** than **conservative cues** | Ideology‑cue classifier |
| **H3** | High ex‑ante **Perceived Brand Authenticity (PBA)** attenuates boycott effect | External survey scale |

*Mediated paths via Self‑Brand Connection are reserved for Study 2.*

---

## B. End‑to‑end Python pipeline (overview)

| Step | Tool / script | Output |
|------|---------------|--------|
| 1 Collection | Manual DOM scraper → `extract_comment_html.py` | Raw JSON |
| 2 Cleaning & thread features | **spaCy v3.7**, **NetworkX** | `clean_threads.parquet` |
| 3 Gold annotation | *Prodigy* dual coders ▢ **TBD** comments | `gold_v1.csv` |
| 4 Ideology cue coding | Weak‑supervision lexicon + ▢ **TBD** hand‑labels; fine‑tuned **SetFit** | `ideology_preds.parquet` |
| 5 Model training | **DeBERTa‑v3‑Large** + PEFT‑LoRA; weighted focal loss | `stance_pi_adapter.bin` |
| 6 Full inference | Batch predict → weekly aggregation (`agg_weekly.csv`) | Boycott / Buy rates per brand‑week |
| 7 Causal analysis | **statsmodels / linearmodels** `PanelOLS` DID script (`did_results.py`) | Tables & event‑study plots |

All commands orchestrated via `project.yml`; environment captured in `environment.yml` (conda).

---

## C. Classification performance (held‑out test – placeholders)

| Task | F1 | Recall (minority class) |
|------|----|-------------------------|
| Relevance | ▢ TBD | ▢ TBD |
| Stance | ▢ TBD | ▢ TBD |
| Purchase Intention | ▢ TBD | ▢ TBD |
| Ideology Cue | ▢ TBD | ▢ TBD |

---

## D. Difference‑in‑Difference‑in‑Differences (DDD) specification

Python implementation uses **statsmodels 0.14** with clustered standard errors.

```python
import statsmodels.formula.api as smf
model = smf.wls(
    formula="rate ~ Rollback * Post * LiberalCue + PBA + depth + is_reply + C(brand) + C(week)",
    data=panel_df,
    weights=panel_df["n_comments"],
).fit(cov_type="cluster", cov_kwds={"groups": panel_df["brand_week"]})
```

* `rate` = weekly boycott‑ or buy‑rate.
* Fixed effects via categorical dummies for brand & ISO week.
* Event‑study and placebo graphs generated with `linearmodels` DID utilities.

---

## E. Robustness & transparency checklist

* **Depth / reply covariates** – included, effects stable.
* **Multiple testing** – Benjamini‑Hochberg (FDR 0.10) across six coefficient families.
* **Non‑DEI comment sensitivity** – restrict to DEI‑relevant subset; coefficients directionally unchanged.
* **Re‑running** – `make reproduce` executes full pipeline end‑to‑end on a fresh clone.

---

## F. File manifest (OSF repository)

| File | Description |
|------|-------------|
| `gold_v1.csv` | Annotated sample (▢ TBD rows, de‑identified) |
| `project.yml` | spaCy project orchestrator |
| `stance_pi_adapter.bin` | LoRA adapter (≈ 100 MB) |
| `did_results.py` | DDD regression script (Python) |
| `ethics.md` | Full compliance checklist |

---

**Contact:** Diego Estuar — diego.estuar@cgu.edu — 18 Apr 2025

