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

- **Decision:** Run a prespecified higher-risk race/ethnicity rule-flag ablation.
  - **Reason:** Check how much the particular encoded risk-factor flag contributes to the hybrid screening policy.
  - **Caveat:** This is not a full race-blind analysis because race/ethnicity remains a raw model feature and the Asian-specific BMI threshold remains encoded.

## 2026-10-30 — Protocol-v1 aggregate run

- **Decision:** Use harmonized leisure/sedentary minutes and HDL (`LBDHDD`) in the frozen predictor contract; do not use the four yes/no PAQ activity items.
  - **Reason:** The yes/no activity fields are entirely missing in the later cycle, while the harmonized minute fields and HDL are available for both cycles.
- **Decision:** Keep the analysis unweighted.
  - **Reason:** Survey weights differ by cycle and are not passed to model fitting; cycle-specific weights remain available only for future documented sensitivity analyses.
- **Decision:** Publish only aggregate JSON, tables, manifests and figures.
  - **Reason:** The export gate blocks `SEQN` and implausibly large tables; participant-level predictions and model bundles remain private.
- **Observed run:** 6,103 historical participants and 4,260 temporal-test participants; temporal prevalence 0.2308. At 20% capacity, hybrid sensitivity was 0.4130 versus 0.4069 for XGBoost raw; paired bootstrap difference 0.0061 (95% CI −0.0112 to 0.0143). This is research evidence, not clinical validation.
