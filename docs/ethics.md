# Ethics & Compliance Statement – Study 1

> **Scope.** This document details the ethical review status, legal‑policy compliance, privacy safeguards, bias‑mitigation approach, and broader societal considerations for the *Facebook DEI Decision Comment Corpus* used in Study 1 of our manuscript.

---

## 1 | Human‑subjects review

| Item                 | Detail                                                                                                                                     |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Risk level**       | Minimal.  No intervention or interaction with human participants; only analysis of publicly observable content.                            |
| **Informed consent** | Not required under exemption category; however, we respect user privacy by removing personal identifiers (see Section 2).                  |

---

## 2 | Privacy & data handling

- **PII stripping.** Immediately after collection each JSON record is purged of user IDs, profile links, avatars, and @‑mentions.
- **Public‑interest allowance.** Facebook comments are legally public; nevertheless we treat them as *contextual integrity* sensitive and never release raw HTML.
- **Third-party processing**: De-identified comment text is programmatically sent to a third-party Large Language Model API (OpenAI GPT-4o) for sentiment classification.
- **Data access tiers.**
  - *Tier 1* — Raw HTML/JSON (PII) stored on encrypted CGU server; access limited to authorised project members.
  - *Tier 2* — De‑identified texts with internal comment IDs; shared among co‑authors under NDA.
  - *Tier 3* — Tokenised, lemmatised versions released via OSF (CC‑BY‑4.0) for replication.
- **Compliance.** Dataset complies with GDPR Recital 153 (academic exemption) and California CCPA §1798.140(o)(3) as it contains only public information and is de‑identified.
- **Retention & deletion.** PII‑containing raw data will be destroyed 12 months after publication or by 30 Jun 2027, whichever comes first.

---

## 3 | Collection method & platform terms

- **Manual browser capture.** Researchers scroll the target post until the "All comments loaded" notice appears, then execute `scripts/extract/comment_extractor.js`, which serialises the rendered DOM into JSON.  No automated crawling, API keys, or login spoofing.
- **Rate‑limit respect.** Each collection session targets a single post and completes within ≈ 3 min, well below Meta's stated 600 requests/10 min cap.
- **Meta Platform TOS compliance.** Section III of Meta's *Platform Terms* permits analysis of public‑facing content provided no attempt is made to identify users or circumvent technical restrictions; our workflow adheres to both conditions.

---

## 4 | Bias & fairness considerations

| Risk                                                   | Mitigation                                                                                                                                                        |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Algorithmic bias in classifiers (stance, PI, ideology) | Balanced gold‑label sampling across brands, weeks, initial vs reply; weighted focal loss for minority classes; report per‑class precision/recall.                 |
| Political‑ideology misclassification                   | Manual review of high‑entropy samples; 95 % CI on liberal‑cue prevalence.                                                                                         |
| Demographic inference                                  | We explicitly avoid inferring race, gender, or age from names or photos.                                                                                          |

Model training data composition and evaluation metrics are documented with the respective models and in the methodology.

---

## 5 | Downstream use & licensing restrictions

- De‑identified corpus released under **CC‑BY‑4.0** for academic, non‑commercial research.
- Prohibited uses: targeted advertising, user re‑identification, personalized political persuasion, hate‑speech generation.
- Users must cite the corpus and this ethics statement in derivative work.

---

## 6 | Responsible AI & broader impact

This study advances understanding of consumer responses to corporate DEI actions, informing both marketing scholarship and public discourse.  We acknowledge the potential for misinterpretation of stance and purchase intent; thus, we provide confidence intervals, robustness checks, and full data‑processing code for scrutiny.  No high‑risk automated decision systems are instantiated.

---

**Maintained by:** Diego Estuar (diego.estuar\@cgu.edu) – ver. 2025‑04‑18
