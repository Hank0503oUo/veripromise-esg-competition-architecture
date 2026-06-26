# v43 Reproducibility Manifest

## Final Result

| Item | Value |
|---|---|
| Submitted file | `submission_v43_tlonly_v39d.csv` |
| Private score | `0.6457201` |
| Private rank | `6/143` |
| Submitted at | `2026-06-18 21:58:59` |
| SHA256 | `17fd3822058bf413b4b0475881af0268b88a1a3d290f29376ef1b06b124c896a` |

## Required Deterministic Artifacts

These are sufficient to reproduce the final submitted file.

| Artifact | Role | SHA256 |
|---|---|---|
| `OUTPUT/submission_v25_evjudge.csv` | v25 base submission | `2da16c99e9b740ff7b9e638791f659fed246a4483e2fac4edcb913c6fca641a0` |
| `OUTPUT/submission_v39d_timeline_explicit_year_tau070_structsafe.csv` | timeline source for v43 | `17fd3822058bf413b4b0475881af0268b88a1a3d290f29376ef1b06b124c896a` |
| `OUTPUT/submission_v43_tlonly_v39d.csv` | final submitted CSV | `17fd3822058bf413b4b0475881af0268b88a1a3d290f29376ef1b06b124c896a` |

Note: `v39d` and `v43` have the same SHA256 because `v39d` is already built on top of the same v25 base and changes only the `verification_timeline` column.

## Required Artifacts to Rebuild v39d

| Artifact | Role | SHA256 |
|---|---|---|
| `esg_competition/data/v35_timeline_anchor_features_test.csv` | explicit target-year anchor features | `324491abf1c6004f94ff021611862faa09158f7cd7ca88b37be02f2b0bf29e95` |
| `esg_competition/outputs/v18C_test_probas.csv` | v18C timeline probabilities for margin diagnostics | `d57b3d89be0b4a1bae84eecab4c2e6fe0c15d979da2438c0cbdd4b43d21e8a85` |

## v43 Diff Versus v25 Base

| Field | Changed cells |
|---|---:|
| `promise_status` | 0 |
| `verification_timeline` | 57 |
| `evidence_status` | 0 |
| `evidence_quality` | 0 |

## v43 Field Distributions

| Field | Distribution |
|---|---|
| `promise_status` | `Yes=1617`, `No=383` |
| `verification_timeline` | `already=580`, `between_2_and_5_years=612`, `more_than_5_years=330`, `N/A=383`, `within_2_years=95` |
| `evidence_status` | `Yes=1309`, `No=286`, `N/A=405` |
| `evidence_quality` | `Clear=1154`, `N/A=700`, `Not Clear=146`, `Misleading=0` |

## Report / Architecture Documentation

| File | Role |
|---|---|
| `submission_v43_reproduction_report.docx` | organizer-facing Word report |
| `submission_v43_reproduction_report.pdf` | organizer-facing PDF report |
| `figures/full_algorithm_layer_map.png` | report architecture figure: public-GitHub-aligned full algorithm layer map |
| `figures/v43_pipeline_overview.png` | report architecture figure: data/features/stack/final |
| `figures/v43_field_transplant.png` | report architecture figure: field-level final assembly |
| `figures/v43_validation_gate.png` | report architecture figure: validation gate and rejected branches |
| `docs/v43_pipeline.md` | GitHub-friendly architecture and decision record |
