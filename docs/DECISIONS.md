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

## 2026-10-30 — Post-hoc feature-setting analysis

- **Decision:** Preserve Setting 1 as the primary, non-glycemic feature setting. It excludes HDL and total cholesterol so the primary result is not a laboratory-inclusive rescue.
- **Decision:** Add Setting 2 (Setting 1 plus HDL and total cholesterol) and Setting 3 (Setting 2 plus fasting plasma glucose) as secondary/exploratory analyses. Setting 3 is evaluated only in the non-missing-FPG fasting subsample, with Settings 1 and 2 rerun on that same subsample.
- **Decision:** Never include HbA1c (`LBXGH`) or diabetes questionnaire items (`DIQ010`, `DIQ160`, `DIQ050`, `DIQ070`) in any setting. FPG is explicitly labeled a second glycemic test and is not encoded as an ontology rule.
- **Reason:** The analyses were added after seeing the original primary result. All settings are reported regardless of direction; they do not alter the primary ontology conclusion.
- **Observed secondary results:** On the main cohort, Setting 2 improved XGBoost raw 20%-capacity sensitivity from 0.4028 to 0.4140 and ontology-feature sensitivity from 0.3978 to 0.4242. On the 2,348-person fasting subsample, Setting 3 reached 0.4432 sensitivity versus 0.3956 for Setting 1, demonstrating the expected value of a closely related glycemic test rather than a neutral screening feature.
