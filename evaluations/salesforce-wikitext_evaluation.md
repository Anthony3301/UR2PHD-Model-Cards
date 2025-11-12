## Basic Info
- **Card Title / URL:** Salesforce/wikitext — https://huggingface.co/datasets/Salesforce/wikitext  
- **Type:** Dataset  
- **Version / Date:** Contains subsets: *wikitext-103-raw-v1*, *wikitext-103-v1*, *wikitext-2-raw-v1*, *wikitext-2-v1*  
- **Owner / Contact:** Owner: Salesforce (dataset listed on HF “Salesforce / wikitext”). Contact: Stephen Merity (author of original paper).  

---

## 1 Snapshot
- **One-liner summary:**  
  A set of large Wikipedia-derived language-modeling datasets (WikiText-2 and WikiText-103) with preserved punctuation/case for training long-dependency text models.  
- **Intended use(s):**  
  Language modeling (word-level or character-level), long-dependency modeling, masked-language or fill-mask tasks.  
- **Out-of-scope use(s):**  
  Not designed for classification, QA, translation, or factual knowledge extraction tasks; not optimized for non-English text.  
- **Linked resources:**  
  - Original paper: *Pointer Sentinel Mixture Models* (Merity et al., 2016).  
  - License: CC BY-SA 4.0.  
  - Hosted on Hugging Face: https://huggingface.co/datasets/Salesforce/wikitext  

---

## 2 Standards Comparison
Mark ✓ (present), ✗ (missing), or ~ (partial).

| Standard Item | Status | Notes |
|----------------|---------|-------|
| Identity & versioning | ✓ | Clear subset versions: wikitext-2/103, raw vs non-raw. |
| Intended use(s) & limitations | ~ | Intended use given; limitations not discussed in depth. |
| Data provenance & composition | ~ | Mentions “Good/Featured” Wikipedia articles; missing collection details. |
| Evaluation data & metrics | ✗ | No benchmark metrics described. |
| Risks / ethical considerations | ✗ | “More information needed” placeholders on HF card. |
| Governance / maintenance | ~ | Maintainer (Salesforce) listed; no update policy. |
| Licensing & access | ✓ | CC BY-SA 4.0 (but 3.0 also mentioned—minor conflict). |
| Reproducibility (code, configs, seeds) | ✗ | No scripts or configs listed. |
| Clarity & structure | ✓ | Well-structured HF card with sections and examples. |
| Cross-references / traceability | ~ | Paper citation provided; preprocessing traceability unclear. |

---

## 3 Gaps & Inconsistencies
- **Missing:**  
  - Provenance (Wikipedia snapshot date, filtering criteria).  
  - Evaluation benchmarks and metrics.  
  - Explicit discussion of dataset biases or social impact.  
  - Reproducibility details (scripts, seeds, tokenization).  
  - Update/maintenance schedule.  
- **Inconsistent / conflicting:**  
  - License shows CC BY-SA 3.0 in header, CC BY-SA 4.0 later.  
- **Ambiguous:**  
  - Dataset size listed as “1M–10M”.  
  - Language field marked “More information needed”.  

---

## 4 Scoring (0–3 per category)
| Category | Score (0–3) |
|-----------|-------------|
| Identity | 3 |
| Intended Use | 2 |
| Data | 2 |
| Evaluations | 1 |
| Risks | 1 |
| Governance | 2 |
| Licensing | 3 |
| Reproducibility | 1 |
| Clarity | 3 |
| Traceability | 2 |
| **Total (/30)** | **19 / 30** |

---

## 5 Extracted Resources
| Resource Type | Link | Key Facts (version, license, metrics, etc.) |
|----------------|------|---------------------------------------------|
| Paper | https://arxiv.org/abs/1609.07843 | *Pointer Sentinel Mixture Models* introducing WikiText; ArXiv 1609.07843. |
| Dataset | https://huggingface.co/datasets/Salesforce/wikitext | WikiText-2/103 raw + clean splits; CC BY-SA license. |
| Other | — | License inconsistency (3.0 vs 4.0) noted. |

---

## 6 Recommendations
### Card Content Updates
- Clarify license version (3.0 vs 4.0).  
- Expand provenance details (Wikipedia dump version, filtering, preprocessing).  
- Add biases/ethical impact section (representation, content bias).  
- Include evaluation benchmarks or links to LM leaderboards.  
- Provide reproducibility info (scripts, seeds, tokenizer).  
- Specify maintenance/update policy.

### Layout or Design Improvements
- Add “Version History” table with dates.  
- Include counts for each split (tokens, articles).  
- Format “Supported tasks” section with concrete metrics.  
- Simplify size field to exact counts.

### Risk / RAI Additions
- Discuss Wikipedia content biases and possible sensitive content.  
- Note license obligations (CC BY-SA share-alike).  
- State out-of-scope uses explicitly (non-English, factual QA).

---

## Overall Comments
**Summary paragraph:**  
The Salesforce/WikiText dataset card is moderately comprehensive and easy to read. It correctly identifies the dataset’s purpose and structure but lacks depth on provenance, risk, and reproducibility. The license inconsistency (3.0 vs 4.0) and “More Information Needed” placeholders reduce confidence for compliance or governance use. Overall it scores **19/30**, suitable for research reproducibility references but below best practice for transparency and responsible-AI auditing.

---

> **Scoring Guide:**  
> 3 = fully documented / clear 2 = present but incomplete 1 = minimal mention 0 = missing entirely
