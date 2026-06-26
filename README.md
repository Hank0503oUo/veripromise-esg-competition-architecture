# ESG 承諾驗證競賽 v43 — 複現指南與架構說明

**AI CUP 2026 春季賽：ESG 永續承諾驗證競賽**

Team/account: `hank050389`

Final private leaderboard result:

| Item | Value |
|---|---|
| Submitted file | `submission_v43_tlonly_v39d.csv` |
| Private score | `0.6457201` |
| Private rank | `6 / 143` |
| Submitted at | `2026-06-18 21:58:59` |
| Expected SHA256 | `17fd3822058bf413b4b0475881af0268b88a1a3d290f29376ef1b06b124c896a` |

---

## What v43 Is

`v43` is a deterministic final assembly:

```text
v43 = v25 base submission
      + replace ONLY verification_timeline
        from v39d structurally safe explicit-year timeline variant
```

No LLM call, model training, random seed, or external API is used in the final assembly step.

The upstream `v25` base:

| Field | Source |
|---|---|
| `promise_status` | v18C field-best stack (Engine A/B/C + LightGBM + ticker prior) |
| `verification_timeline` | v18C baseline (replaced by v39d in v43) |
| `evidence_status` | v25 GLM-5.2 evidence-status judge probability feature |
| `evidence_quality` | v18/v18C conservative stack (EQ probes rejected by gate) |

The `v39d` timeline variant uses an explicit target-year anchor with structural safety constraints: confidence >= 0.70, reason in `{explicit_target_year, explicit_target_year_range}`, base `promise_status == Yes`, and current `verification_timeline != N/A`.

---

## Architecture Documentation

Detailed algorithm design and system architecture:

- **[v43最終架構.md](v43最終架構.md)** — Full v43 pipeline, algorithm layer table, per-field source rationale, version history, local vs private alignment analysis
- **[v18架構圖.md](v18架構圖.md)** — Detailed v18/v18C architecture: data layer, feature engineering, LLM/judge layer, stacking, calibration, deployment gate
- **[docs/v43_pipeline.md](docs/v43_pipeline.md)** — Mermaid pipeline diagrams, v39d rule detail, reproduction levels

Architecture diagrams (PNG):

| Figure | Description |
|---|---|
| [figures/full_algorithm_layer_map.png](figures/full_algorithm_layer_map.png) | Full 5-layer algorithm map: data → feature → LLM/logit → stack+calibration → deployment |
| [figures/v43_pipeline_overview.png](figures/v43_pipeline_overview.png) | Data / features / stack / v43 final flow |
| [figures/v43_field_transplant.png](figures/v43_field_transplant.png) | Field-level v43 assembly showing per-field sources |
| [figures/v43_validation_gate.png](figures/v43_validation_gate.png) | Validation and deployment gate; rejected branches |

---

## Environment

- OS: Windows 11 / Linux / macOS / Google Colab
- Language: Python 3.10+
- Required packages: `pandas==2.2.3`, `numpy==2.2.6`

```bash
pip install -r requirements.txt
```

No GPU, no LLM API call, and no model retraining are required for the final-assembly reproduction.

---

## Required Files

Place the competition project in this layout:

```text
ESG競賽/
  OUTPUT/
    submission_v25_evjudge.csv
    submission_v39d_timeline_explicit_year_tau070_structsafe.csv
  esg_competition/
    HARNESS/v43_repro_package/    <- this repository
```

To regenerate `v39d` from its deterministic features, also provide:

```text
ESG競賽/
  esg_competition/
    data/
      v35_timeline_anchor_features_test.csv
    outputs/
      v18C_test_probas.csv
```

---

## Local Reproduction

```powershell
# Windows PowerShell
pip install -r requirements.txt

# Optional: regenerate v39d timeline source from deterministic feature artifacts
python scripts/build_v39d_timeline.py --root "G:\我的雲端硬碟\ESG競賽"

# Reproduce final v43 submission and verify SHA256
python scripts/reproduce_v43.py --root "G:\我的雲端硬碟\ESG競賽"
```

```bash
# Linux / macOS / Colab
pip install -r requirements.txt

python scripts/build_v39d_timeline.py --root "/content/drive/MyDrive/ESG競賽"
python scripts/reproduce_v43.py --root "/content/drive/MyDrive/ESG競賽"
```

### Module I/O

#### `scripts/build_v39d_timeline.py`

| | |
|---|---|
| **Input** | `--root`: path to `ESG競賽/` project root |
| | `esg_competition/data/v35_timeline_anchor_features_test.csv` — explicit target-year anchor features |
| | `esg_competition/outputs/v18C_test_probas.csv` — v18C timeline probabilities |
| **Output** | `OUTPUT/submission_v39d_timeline_explicit_year_tau070_structsafe.csv` |
| **Side effects** | Prints replaced-row count and confidence distribution |

#### `scripts/reproduce_v43.py`

| | |
|---|---|
| **Input** | `--root`: path to `ESG競賽/` project root |
| | `OUTPUT/submission_v25_evjudge.csv` — v25 base (SHA256: `2da16c99...`) |
| | `OUTPUT/submission_v39d_timeline_explicit_year_tau070_structsafe.csv` — timeline source |
| **Output** | `OUTPUT/submission_v43_tlonly_v39d.csv` — final reproduced submission |
| | `v43_repro_report.json` — validation result + SHA256 check |
| **Side effects** | Prints per-field diff vs v25, format validation, SHA256 match result |

Successful output:

```json
{
  "sha256_matches_expected": true,
  "diff_vs_base": {
    "promise_status": 0,
    "verification_timeline": 57,
    "evidence_status": 0,
    "evidence_quality": 0
  }
}
```

---

## Colab Reproduction

Open `colab/reproduce_v43_colab.ipynb` in Google Colab, then run cells top-to-bottom. The notebook mounts Google Drive, installs `pandas`/`numpy`, regenerates `v39d`, regenerates `v43`, and prints the checksum report.

---

## Validation Rules

Both scripts validate:

- Exactly 2000 rows
- Columns exactly `id, promise_status, verification_timeline, evidence_status, evidence_quality`
- Sorted numeric ids
- UTF-8 without BOM, LF newlines
- No accidental `NaN` conversion of `N/A` strings
- Valid class labels for all four target fields

---

## Artifact Checksums

| Artifact | SHA256 |
|---|---|
| `submission_v25_evjudge.csv` | `2da16c99e9b740ff7b9e638791f659fed246a4483e2fac4edcb913c6fca641a0` |
| `submission_v39d_timeline_explicit_year_tau070_structsafe.csv` | `17fd3822058bf413b4b0475881af0268b88a1a3d290f29376ef1b06b124c896a` |
| `submission_v43_tlonly_v39d.csv` | `17fd3822058bf413b4b0475881af0268b88a1a3d290f29376ef1b06b124c896a` |

Note: `v39d` and `v43` share the same SHA256 because v43 only replaces `verification_timeline`.

---

## Files in This Repository

| File | Role |
|---|---|
| `scripts/build_v39d_timeline.py` | Rebuilds deterministic timeline variant `v39d` from anchor features |
| `scripts/reproduce_v43.py` | Rebuilds final private-counting submission `v43` and verifies SHA256 |
| `colab/reproduce_v43_colab.ipynb` | Google Colab runner (mounts Drive, installs deps, runs both scripts) |
| `docs/v43_pipeline.md` | Architecture and decision record with Mermaid diagrams |
| `figures/full_algorithm_layer_map.png` | Full 5-layer algorithm map (matches public GitHub architecture) |
| `figures/v43_pipeline_overview.png` | v43 pipeline overview figure |
| `figures/v43_field_transplant.png` | Field-level transplant figure |
| `figures/v43_validation_gate.png` | Validation gate and rejected branches figure |
| `tools/generate_submission_report.py` | Generates the organizer-facing Word/PDF report |
| `MANIFEST.md` | Required artifacts, SHA256 checksums, field distributions |
| `requirements.txt` | Python dependencies (`pandas==2.2.3`, `numpy==2.2.6`) |
| `v18架構圖.md` | Detailed v18/v18C system architecture (data, feature, LLM, stack layers) |
| `v43最終架構.md` | v43 final architecture with algorithm tables and version history |

---

## Privacy / Public Scope

This repository contains code and documentation only. It does **not** include:

- Official competition train/validation/test data
- Submission CSV files or private LLM API outputs
- Model checkpoints, LoRA adapters, or large intermediate artifacts
- API credentials

Required deterministic artifacts can be supplied privately to the organizer when reproduction is requested.
