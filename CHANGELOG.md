# Changelog

All notable project changes are documented here. The repository now includes aggregate outputs from the frozen `protocol-v1` run; participant-level predictions and model bundles remain private.

## [0.1.0] - 2026-10-29

- Define the research protocol, NHANES temporal split, outcome, leakage guards, ontology scope, metrics and application requirements.
- Add initial RDF/OWL screening ontology and rule execution module.
- Add NHANES download/harmonization module, model helpers, test scaffold and notebook/application entry points.

## 0.1.1 — 2026-10-29

- Fixed ontology explorer edge construction so all graph edges render independent of RDF iteration order.
- Included hypertension treatment as an encoded hypertension risk input.
- Added regression tests for graph edges and treatment-based risk flags.
- Updated the standalone Kaggle/Colab notebook's embedded ontology to match the repository ontology.
- Kept the independent manual-feature control aligned with the hypertension-treatment criterion and added a static regression guard.
- Smoke-tested the notebook training/evaluation/artifact flow using temporary synthetic data only; no synthetic metrics were retained as project results.
- Added the prespecified higher-risk race/ethnicity rule-flag ablation to the notebook, result artifacts, dashboard and experiment register, with explicit interpretation limits.
- Added static integrity tests for notebook syntax, empty outputs, ontology embedding parity and predictor leakage-contract presence.
- Added a project architecture diagram and made dashboard artifact-copy instructions explicit.

## 0.2.0 — 2026-10-30

- Harmonized activity-minute and HDL predictors across NHANES cycles and added cycle-level missingness QC.
- Added fixed-capacity headline metrics, prevalence ceilings, lift, paired-bootstrap evidence and safe aggregate-result export.
- Completed the CPU notebook run and committed paper-ready aggregate tables, manifests and figures under `results/`.
- Updated the dashboard to prefer private artifacts while falling back to committed aggregate results.
