# Facebook Comment Text‑Analytics Project – README ![status](https://img.shields.io/badge/JAMS--submission-2025-blue)

## Project Goal  
This repository accompanies the study **"DEI Rollbacks, Brand Authenticity, and Consumer Reaction on Social Media"** (target journal: _Journal of the Academy of Marketing Science_).  
We analyze **20 000 public Facebook comments** posted during a 30‑day window around four companies' DEI decisions to quantify:

1. **Relevance** – whether a comment addresses DEI.  
2. **Stance** – pro‑DEI, anti‑DEI, or neutral.  
3. **Purchase intent** – buy, boycott, or neutral intentions.  

The pipeline then **causally estimates shifts in boycott‑ and buy‑rates** via a Triple‑Difference (DDD) design moderated by brand authenticity.

---

## Compliance & Ethics Summary  
See `/docs/Data_Statement.md` for IRB protocol # XXXX, Meta/Facebook TOS compliance, and privacy safeguards.  
_Key points_: human‑initiated collection, public comments only, no PII stored.

---

## Directory Layout
```text
root/
│  README.md
│  LICENSE
│  CITATION.cff
│  environment.yml          ← Python 3.10 lock‑file
│  project.yml              ← spaCy workflow (clean → export → train)
│
├─data/
│   ├─raw/                  ← (local only, **not** committed)
│   └─derived/
│        comments_clean.parquet
│        labels_gold.csv
│        labels_predicted.csv
│
├─docs/
│   IRB_exemption.pdf
│   Data_Statement.md
│   Methodology_Supp.md
│
├─scripts/
│   extract/
│      comment_extractor.js
│   preprocess/
│      process_comments_json.py
│   annotate/
│      annotation_guidelines.md
│      label_interface.json
│   model/
│      train_setfit.py
│      train_deberta_lora.py
│      prompts/
│         gpt4o_synthetic_prompt.txt
│   analysis/
│      ddd_regression.Rmd
│
├─notebooks/
│   EDA_threads.ipynb
│   Diagnostics_bias.ipynb
│
├─tests/
│   test_graph_features.py
│   test_process_pipeline.py
│
└─results/
    model_artifacts/
    figures/
    tables/
```

---

## Quick‑Start
```bash
# 1 – Create environment (Python 3.10 required)
conda env create -f environment.yml
conda activate fb-text

# 2 – Run the entire spaCy project pipeline
spacy project run all

# 3 – Verify installation & run unit tests
python -m spacy validate
pytest tests/

# 4 – (Optional) Train models manually
# python scripts/model/train_setfit.py
# python scripts/model/train_deberta_lora.py

# 5 – (Optional) Run causal Triple‑Difference analysis
# R -e "rmarkdown::render('scripts/analysis/ddd_regression.Rmd')"
```

---

## Data Collection Methodology  

### Phase 1 – Manual Extraction  
1. Scroll a public Facebook post until **all comments/replies are visible**.  
2. Open **DevTools → Console** and paste `scripts/extract/comment_extractor.js` (captures each `div[role="article"]` outerHTML).  
3. Save the JSON as `YYYYMMDD_HHMM.json` in `/data/raw/<Company>/`.

### Phase 2 – JSON Processing  
`spacy project run all` parses raw JSON, extracts fields, computes thread dates, and saves `/data/derived/comments_clean.parquet`.  
Core logic in `scripts/preprocess/process_comments_json.py` (can be run standalone).

#### Output Columns (example)

| Column            | Description                               |
|-------------------|-------------------------------------------|
| `company_name`    | Company slug                              |
| `post_date`       | Source post timestamp                     |
| `comment_text`    | Raw comment text                          |
| `comment_date`    | Approx. comment date (parsed "2d", "5w")  |
| `id` / `parent_id`| Threading identifiers                     |
| `reaction_count`  | UI reactions                              |
| `comment_type`    | `initial` / `reply`                       |

---

## Annotation & Active Learning  

* **Label schema**  
  * `relevance` ∈ {0, 1}  
  * `stance` ∈ {–1 (anti), 0, +1 (pro)}  
  * `purchase` ∈ {–1 (boycott), 0, +1 (buy)}  
* **Gold set**: 1 000 comments, dual‑coded; **Cohen's κ ≥ 0.75**.  
* **Active learning**: entropy sampling with **`small-text v2.4.0`**.

---

## Modeling Pipeline  

| Task                 | Model (link)                                                                                 | Notes                            |
|----------------------|----------------------------------------------------------------------------------------------|----------------------------------|
| **Relevance**        | [`SetFit/all‑MiniLM‑L6‑v2`](https://huggingface.co/setfit/all-MiniLM-L6-v2)                  | Few‑shot, CPU‑friendly           |
| **Stance & Purchase**| [`microsoft/deberta-v3-large`](https://huggingface.co/microsoft/deberta-v3-large) + **LoRA** | PEFT adapter, focal loss         |

---

## Causal Analysis  

Triple‑Difference (DDD) on weekly rates:
```text
y = β0 + β1·Rollback_c + β2·Post_t + β3·AntiStance_s
    + β4·Rollback×Post + β5·Rollback×AntiStance
    + β6·Post×AntiStance + β7·Rollback×Post×AntiStance
    + β8·Authenticity×Rollback×Post×AntiStance
    + γ_c + δ_t + ε
```
Implementation & diagnostics in `/scripts/analysis/ddd_regression.Rmd` (outputs to `/results/figures/`).

---

## Synthetic‑Data (Conditional) Workflow  

Activated **only if** real‑data macro‑F1 < target or minority recall < 0.60.

1. Generate ≤ 1 synthetic comment per real label via GPT‑4o (`/scripts/model/prompts/`).  
2. Filter with OpenAI self‑critique + perplexity ≤ 100.  
3. Retrain; retain only if F1 ↑ ≥ 1 pp on real‑only test set.  
4. Run toxicity & demographic bias checks (`/notebooks/Diagnostics_bias.ipynb`).

---

## Reproducibility & Replication  

* Every figure/table is generated by code in `/results/`.  
* **Zenodo DOI** badge added on first release.  
* OSF archive + GitHub tag (`v1.0.0`) freeze artifacts.  
* Random seeds set in `project.yml` & training scripts.

---

## Citation  
```bibtex
@misc{estuar2025dei,
  author       = {Estuar, Diego},
  howpublished = {\url{https://github.com/destuar/Facebook-TextAnalytics-Project}},
  year         = {2025},
  note         = {Working paper, submitting to Journal of the Academy of Marketing Science}
}
```

---

## License  

* **Code & prompts:** MIT License  
* **Derived, de‑identified datasets & synthetic comments:** CC‑BY‑4.0  
* **Raw Facebook JSON:** _not_ redistributed (Meta TOS).

