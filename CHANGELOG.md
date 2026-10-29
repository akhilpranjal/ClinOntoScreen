# Changelog

All notable project changes are documented here. This initial scaffold contains no trained model or observed empirical results.

## [0.1.0] - 2026-10-29

- Define the research protocol, NHANES temporal split, outcome, leakage guards, ontology scope, metrics and application requirements.
- Add initial RDF/OWL screening ontology and rule execution module.
- Add NHANES download/harmonization module, model helpers, test scaffold and notebook/application entry points.

## 0.1.1 — 2026-10-29

- Fixed ontology explorer edge construction so all graph edges render independent of RDF iteration order.
- Included hypertension treatment as an encoded hypertension risk input.
- Added regression tests for graph edges and treatment-based risk flags.
- Updated the standalone Kaggle/Colab notebook's embedded ontology to match the repository ontology.
- Added static integrity tests for notebook syntax, empty outputs, ontology embedding parity and predictor leakage-contract presence.
- Added a project architecture diagram and made dashboard artifact-copy instructions explicit.
