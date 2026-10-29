# Changelog

All notable project changes are documented here.

## [0.2.0] - 2026-10-30

- Applied the `plan_addendum.md` amendments: fixed-capacity primary endpoint with prevalence ceilings,
  one confirmatory hypothesis (H2) with paired bootstrap and pre-registered smallest detectable
  difference, exploratory E1 (low-data), E2 (missing-input) and E3 (model-family) experiments,
  published CDC/ADA prediabetes risk-test baseline, XOR disagreement review (H3) and
  `race_ethnicity_ablation` disclosure.
- Cycle-harmonized the feature contract: added `hdl_chol_mgdl`, `leisure_activity_minutes` and
  `sedentary_minutes`; dropped the four yes/no activity items (100% missing in 2021–2023);
  `hypertension_treatment` re-sourced to `BPQ040A` with its cycle asymmetry disclosed;
  `MCQ300C` family history documented as not harmonized.
- Ontology v0.2.0: `sectionReference` and `operationalizationStatus` properties; family-history,
  gestational-diabetes and PCOS criteria marked described-but-not-operationalized; physical-inactivity
  criterion redefined on harmonized leisure minutes; HDL and family-history variables added with
  provenance notes.
- Rebuilt the notebook as generated cell sources (`tools/nb_cells/` + `tools/build_notebook.py`),
  14 cells, embedded ontology byte-identical to `ontology/diabetes_screening.ttl`.
- Froze the protocol before test evaluation: git tag `protocol-v1` (commit `d30f8f8`); run provenance
  (commit, tag relation, package versions) recorded in `artifacts/research_results.json`.
- Canonical run completed 2026-10-30: primary endpoint null (hybrid − ML-only = −0.0031,
  95% CI [−0.0100, +0.0079], below MDE 0.0143); all trained models outperform the published CDC/ADA
  score (AUPRC 0.460–0.463 vs 0.380); best capacity policy is logistic + ontology features
  (sensitivity 0.423 @20%, lift 2.12). Full log in `docs/DECISIONS.md`.
- Rewrote the dashboard for the new result schema (capacity ceiling/lift panels, E1/E2/E3, MDE,
  published baseline, subgroup table, updated case-explorer inputs).
- Added `paper/CLINONTOSCREEN_PAPER.md` (full draft with tables and figure references, all numbers
  read from the run artifacts) and registered new figures/tables in `docs/FIGURES.md`.
- Preserved the user's pre-addendum Colab run unmodified in `artifacts_colab_2026-10-29/` with a
  README explaining its schema and differences.

## [0.1.0] - 2026-10-29

- Define the research protocol, NHANES temporal split, outcome, leakage guards, ontology scope, metrics and application requirements.
- Add initial RDF/OWL screening ontology and rule execution module.
- Add NHANES download/harmonization module, model helpers, test scaffold and notebook/application entry points.

## [0.1.1] - 2026-10-29

- Fixed ontology explorer edge construction so all graph edges render independent of RDF iteration order.
- Included hypertension treatment as an encoded hypertension risk input.
- Added regression tests for graph edges and treatment-based risk flags.
- Updated the standalone Kaggle/Colab notebook's embedded ontology to match the repository ontology.
- Kept the independent manual-feature control aligned with the hypertension-treatment criterion and added a static regression guard.
- Smoke-tested the notebook training/evaluation/artifact flow using temporary synthetic data only; no synthetic metrics were retained as project results.
- Added the prespecified higher-risk race/ethnicity rule-flag ablation to the notebook, result artifacts, dashboard and experiment register, with explicit interpretation limits.
- Added static integrity tests for notebook syntax, empty outputs, ontology embedding parity and predictor leakage-contract presence.
- Added a project architecture diagram and made dashboard artifact-copy instructions explicit.
