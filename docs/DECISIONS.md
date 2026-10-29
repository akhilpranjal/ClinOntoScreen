# Design Decisions Log

## 2026-10-29 — Initial protocol

- **Decision:** Use NHANES 2017–March 2020 for model development and 2021–2023 as the locked later-cycle test.
  - **Reason:** Public, standardized data and an explicit temporal generalization evaluation.
  - **Caveat:** The newer cycle has changed sample design and procedures; do not attribute any shift to a single cause.
- **Decision:** Define the primary outcome using HbA1c >=5.7% among adults who self-report neither diabetes nor prediabetes.
  - **Reason:** The outcome is independent of the ontology's screening criteria and supports a screening use case.
  - **Caveat:** One measurement is not a confirmed diagnosis.
- **Decision:** Exclude HbA1c, glucose, diabetes questionnaire labels and medication fields from predictors.
  - **Reason:** Prevent target leakage.
- **Decision:** Use Logistic Regression and XGBoost.
  - **Reason:** Interpretable baseline plus strong nonlinear tabular baseline.
- **Decision:** Make sensitivity at 20% screening capacity the primary policy metric.
  - **Reason:** Directly measures positive cases found at a fixed referral budget.
- **Decision:** Implement a bounded, source-linked OWL/RDF screening ontology and a deterministic Python rule engine.
  - **Reason:** Provides traceability and explanations while keeping execution auditable.
- **Decision:** Include raw ML, ontology features, an equivalent generic-feature control, ontology-only ranking, and confidence-only review.
  - **Reason:** Separate ontology traceability from generic feature engineering and test the added value of disagreement.
- **Decision:** Do not claim results or clinical validity until the full notebook completes and the evidence is assessed.
