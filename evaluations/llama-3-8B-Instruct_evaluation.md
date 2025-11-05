## Basic Info
- **Card Title / URL:** [PhysicalAI-Autonomous-Vehicles](https://huggingface.co/datasets/nvidia/PhysicalAI-Autonomous-Vehicles)
- **Type:** Dataset
- **Version / Date:** October 28, 2025
- **Owner / Contact:** NVIDIA Corporation

---

## 1 Snapshot
- **One-liner summary:**  
  A large multi-sensor autonomous vehicle dataset (7 cameras, LiDAR, up to 10 radars) collected over 1,727 hours and 310,895 clips across 25 countries for physical AI driving systems.
- **Intended use(s):**  
  Research and development for autonomous vehicles, end-to-end driving models, perception, and multi-modal fusion.
- **Out-of-scope use(s):**  
  Any use violating NVIDIA’s dataset license (e.g., surveillance, re-identification, or illegal activity).
- **Linked resources:**  
  - [GitHub Repository](https://github.com/NVlabs/physical_ai_av)  
  - [NVIDIA Blog Announcement](https://blogs.nvidia.com/blog/open-physical-ai-dataset/)  

---

## 2 Standards Comparison
Mark ✓ (present), ✗ (missing), or ~ (partial).

| Standard Item | Status | Notes |
|----------------|---------|-------|
| Identity & versioning | ✓ | Dataset name, owner, and version date are clear. |
| Intended use(s) & limitations | ✓ | Described in the dataset card and license terms. |
| Data provenance & composition | ~ | General stats and sensors listed, but demographics and scenario distribution missing. |
| Evaluation data & metrics | ✗ | No quantitative evaluation metrics; purely descriptive dataset. |
| Risks / ethical considerations | ~ | Mentions license prohibiting certain uses, limited details on bias or privacy. |
| Governance / maintenance | ~ | States possible updates but no structured version history. |
| Licensing & access | ✓ | NVIDIA license and acceptance process included. |
| Reproducibility (code, configs, seeds) | ~ | Developer kit repo provided, but no reproducible sampling/config details. |
| Clarity & structure | ✓ | Organized and readable with summary stats. |
| Cross-references / traceability | ✓ | Links to GitHub, license, and official blog provided. |

---

## 3 Gaps & Inconsistencies
- **Missing:**  
  - Detailed annotation process and quality metrics.  
  - Demographic or scenario coverage data (e.g., weather, lighting, location ratios).  
  - Version history and changelog.
- **Inconsistent / conflicting:**  
  - Clip counts differ slightly between Hugging Face (310,895) and blog post (~320,000 trajectories).  
- **Ambiguous:**  
  - Geographic representation described vaguely (“25 countries” without full breakdown).  
  - Privacy handling and data anonymization steps are not explicit.

---

## 4 Scoring (0–3 per category)
| Category | Score (0–3) |
|-----------|-------------|
| Identity | 3 |
| Intended Use | 3 |
| Data | 2 |
| Evaluations | 0 |
| Risks | 2 |
| Governance | 2 |
| Licensing | 3 |
| Reproducibility | 2 |
| Clarity | 3 |
| Traceability | 3 |
| **Total (/30)** | **23 / 30** |

---

## 5 Extracted Resources
List and summarize embedded or related resources.

| Resource Type | Link | Key Facts (version, license, metrics, etc.) |
|----------------|------|---------------------------------------------|
| GitHub Repo | [NVlabs/physical_ai_av](https://github.com/NVlabs/physical_ai_av) | Developer kit, Apache-2.0 license. |
| Blog Article | [NVIDIA Blog](https://blogs.nvidia.com/blog/open-physical-ai-dataset/) | Dataset announcement with metrics (15 TB+, 25 countries, 1,727 hours). |
| Dataset Card | [Hugging Face Dataset Page](https://huggingface.co/datasets/nvidia/PhysicalAI-Autonomous-Vehicles) | 310,895 clips, 20s each, 7 cameras, LiDAR, radars; licensed under NVIDIA AV Dataset terms. |

---

## 6 Recommendations
### Card Content Updates
- Add annotation quality details and labeling methodology.  
- Provide demographic and environmental distribution breakdowns.  
- Include a versioning table with update history.

### Layout or Design Improvements
- Add summary statistics table (hours, clips, sensors) at top.  
- Use icons for sensor modalities (camera, radar, LiDAR).  
- Collapse detailed tables for readability.

### Risk / RAI Additions
- Document privacy/anonymization procedures.  
- Add bias and representation audit summary.  
- Provide contact or process for reporting dataset misuse.

---

## Overall Comments
The PhysicalAI-Autonomous-Vehicles dataset is extensive and technically detailed, offering rich multi-sensor data for autonomous driving research. The documentation is clear and well-structured, but transparency could be improved in annotation methodology, data demographics, and privacy processes. Strong licensing clarity and traceability make it a solid reference example, though additional ethical and quality details would bring it closer to full compliance with dataset documentation standards.

---

> **Scoring Guide:**  
> 3 = fully documented / clear  
> 2 = present but incomplete  
> 1 = minimal mention  
> 0 = missing entirely
