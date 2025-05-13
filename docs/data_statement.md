# Data Statement – Facebook DEI Decision Comment Corpus (v1.0)

## 1 | Dataset overview
|                       | Description |
|-----------------------|-------------|
| **Name**              | Facebook DEI Decision Comment Corpus |
| **Curators**          | Diego Estuar (CGU) |
| **Size**              | 33 872 unique comments & replies |
| **Language**          | English |
| **Temporal coverage** | −15 to +30 days relative to each public DEI announcement (Jan–Mar 2025) |
| **Domain**            | Public Facebook pages of four large U.S. retailers |
| **Treatment groups**  | 2 brands *Rollback* DEI, 2 brands *Keep* DEI |
| **Version**           | 1.0 (2025‑04‑18) |

## 2 | Research purpose
Enable analysis of how continuing vs. rolling‑back DEI programmes relates to boycott‑ and buy‑intent language, while examining whether perceived brand authenticity buffers backlash.

## 3 | Ethical review & legal compliance – summary
Exempt IRB §46.104(d)(4)(ii): publicly available data.  Collection performed via manual scrolling of publicly visible posts; no automated API calls, login spoofing, or rate‑limit circumvention.  Immediately after collection the dataset is stripped of user IDs, profile links, photos, and @‑mentions.

*(Full compliance checklist, Facebook TOS excerpts, and GDPR/CCPA assessment are provided in **ethics.md**.)*

## 4 | Source data & collection window
All visible comments and replies on the focal DEI announcement post for each brand, plus comments in the −15 day pre‑announcement buffer to establish a baseline, and +30 days post‑announcement to capture reaction decay.

## 5 | Processing & annotation snapshot
| Stage | Key steps |
|-------|-----------|
| Preprocessing (Phase 2) | Parse raw JSON (2a using `scripts/extract/process_comments_json.py`), Combine CSVs & Add Flags (2b), Add Graph Features (2c) |
| Text Prep (Phase 3) | Clean comment text (3a), Build `full_text` thread field (3b) |
| Annotation (Phase 4) | Sample 500 comments; Annotate `relevance` in Label Studio |
| Annotation (Phase 5) | Sample 1000 relevant comments; Annotate `stance_dei` & `purchase_intention` |
| Prediction (Phase 4/5) | Fine-tune & predict with SetFit (relevance); Use GPT-4o API for stance/PI (via `models/sentiment_gpt4o_model/text_analytics.ipynb`) |

## 6 | Intended use & licensing
Derived, de‑identified data **CC‑BY‑4.0**.  Raw HTML not redistributed.
