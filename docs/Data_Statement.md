# Data_Statement.md
*Companion to “DEI Rollbacks, Brand Authenticity, and Consumer Reaction on Social Media”*

---

## 1 Dataset Overview
|                       | Description                                         |
|-----------------------|-----------------------------------------------------|
| **Name**              | *Facebook DEI Decision Comment Corpus*              |
| **Curators**          | Diego Estuar (CGU)            |
| **Size**              | 20,145 top-level comments and replies               |
| **Language**          | English                                             |
| **Temporal coverage** | 30-day window per company, Jan – Mar 2025           |
| **Domain**            | Public Facebook pages of four large U.S. companies  |
| **Version**           | v0.9 (2025-04-17) – frozen for JAMS review          |

---

## 2 Motivation & Research Goals
The corpus enables causal tests of how **maintaining vs. rolling back DEI initiatives** affects consumer purchase intention and whether **brand authenticity moderates backlash/support**.

---

## 3 Ethical Review & Legal Compliance
| Item             | Detail                                                                                |
|------------------|---------------------------------------------------------------------------------------|
| **IRB**          | LMU Protocol # XXXX — Exempt Category 4 (ii) (public online data).                    |
| **Facebook TOS** | Data captured via rendered DOM with manual user action; no API scraping or login spoofing. |
| **PII**          | User IDs, profile links, photos, and @-mentions removed immediately upon collection. |
| **GDPR/CCPA**    | Only public comments; no attempt to re-identify users; stored in U.S. servers.        |

---

## 4 Source Data

| Aspect              | Detail                                                                              |
|---------------------|-------------------------------------------------------------------------------------|
| **Companies**       | Four U.S. retailers (anonymised as *A–D* in public materials).                      |
| **Event types**     | *Rollback* (2 brands) and *Keep / Re-affirm* DEI (2 brands).                       |
| **Collection window** | −15 to +15 calendar days around each public DEI announcement.                        |
| **Selectors**       | All visible comments + replies; no filtering by reaction count or keywords.        |

---

## 5 Collection Process

1.  Analyst scrolls target post until “All comments loaded” indicator.
2.  Executes `scripts/extract/comment_extractor.js` in browser console.
3.  Script serialises each `div[role="article"]` outerHTML → JSON.
4.  File saved as `YYYYMMDD_HHMM.json` inside `/data/raw/<Company>/`.

No automated bots or pagination endpoints were used.

---

## 6 Pre-processing & Annotation

| Stage                | Steps                                                                                   |
|----------------------|-----------------------------------------------------------------------------------------|
| **Cleaning**         | spaCy v3.7: strip URLs, emojis, lemmatise. Thread metrics: `root_id`, `depth`.          |
| **Gold labels**      | 1,000 comments, dual-coded for `relevance`, `stance`, `purchase`; Cohen's κ = 0.78.     |
| **Active learning**  | `small-text v2.4.0` entropy sampling → +600 labels (κ = 0.76).                          |
| **Label schema**     | `relevance` ∈ {0,1}; `stance` ∈ {–1,0,+1}; `purchase` ∈ {–1,0,+1}.                        |
| **Class distribution** | Relevant 38%; Anti-DEI 19%, Pro-DEI 14%; Boycott 12%, Buy 7%.                            |

---

## 7 Dataset Splits

| Split        | Size | Purpose                       |
|--------------|------|-------------------------------|
| Train        | 70%  | Model fitting                 |
| Dev / Val    | 15%  | Early stopping + threshold    |
| Test (real)  | 15%  | Final metrics & causal agg.   |

Stratified by company to avoid cross-brand leakage.

---

## 8 Intended Uses

*   Training & evaluating classifiers on DEI-related stance and purchase intention.
*   Causal analysis of consumer backlash/support following corporate DEI decisions.
*   Academic replication and extension in marketing, CSR, or computational social science.

---

## 9 Potential Misuses

*   **User re-identification** — prohibited; raw JSON with profile info is never released.
*   **Hate-speech generation** — synthetic augmentation prompts must not produce disallowed content (OpenAI policy).
*   **Commercial targeting** — dataset licensed for research only (CC-BY-4.0 on derived, de-identified content).

---

## 10 Licensing & Access

| Layer                               | License / Access                          |
|-------------------------------------|-------------------------------------------|
| **Code & prompts**                  | MIT                                       |
| **Derived, de-identified datasets** | CC-BY-4.0 (Zenodo DOI)                    |
| **Raw Facebook JSON**               | **Not redistributed** (Meta TOS)          |

---

## 11 Maintenance & Contact

For questions or takedown requests, contact **Diego Estuar, PhD Candidate**
`email: destuar@cgu.edu`  •  GitHub: `@destuar`

_Last updated: 2025-04-17_ 