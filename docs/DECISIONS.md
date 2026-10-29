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

## 2026-10-29 — Addendum amendments accepted (recorded before any 2021–2023 outcome was modelled)

These entries adopt `plan_addendum.md` into the frozen protocol. They were written after a **historical-only**
sanity check on NHANES 2017–March 2020 and **before** any model was evaluated on the 2021–2023 cycle.

### Historical-only sanity check (addendum §2)

- Historical eligible cohort: n = 6,103; screen-positive count = 1,766; prevalence = 0.2894; single-measurement
  diabetes-range (HbA1c ≥ 6.5%) count = 131.
- Independent historical validation (stratified 80/20 split, seed 42): AUROC 0.758 / AUPRC 0.503 (XGBoost raw),
  AUROC 0.764 / AUPRC 0.510 (XGBoost + ontology features), AUROC 0.764 / AUPRC 0.528 (logistic raw),
  AUROC 0.767 / AUPRC 0.535 (logistic + ontology features).
- Verdict: the pipeline behaves as expected; no implausibly low discrimination and no tiny positive count, so no
  pipeline repair was required before proceeding. 2021–2023 outcomes remained unused for modelling.

### Scope (addendum §1)

- **Decision:** The paper draft is the primary deliverable; the dashboard is trimmed to five Streamlit views
  already present in `app.py` (Overview, Research Results, Case Explorer, Ontology Explorer, Data & Methods), and
  no new pages are added. `CONTRIBUTING.md`, `docs/FIGURES.md` and `DATA_DICTIONARY.md` are retained because they
  are small and are referenced by the paper; the data dictionary is additionally regenerable from the feature
  manifest.
- **Decision:** All implementation work is grouped into a small number of coherent commits rather than ten.

### Metric ceiling and screening capacity (addendum §4)

- **Decision:** The primary capacity stays at 20% (as registered in `plan.md`). Because historical prevalence is
  0.289, the maximum achievable sensitivity at 20% capacity is 0.691, not 1.0.
- **Reason:** The endpoint was fixed in `plan.md` before any data were seen, and a 0.69 ceiling is not degenerate;
  every capacity table therefore reports prevalence, the ceiling, and the fraction of the ceiling achieved,
  together with PPV and lift (enrichment) as required by the addendum.
- **Caveat:** Sensitivity values must never be interpreted without the ceiling beside them.

### Variable harmonization findings (addendum §6)

- **Decision:** `HDL cholesterol (LBDHDD)` is added to the raw feature set. Both cycles publish an `HDL` file with
  `LBDHDD`, and coverage is high (88.8% non-missing in 2017–March 2020; 85.4% in August 2021–August 2023).
- **Decision:** `hypertension_treatment` maps to `BPQ040A` in 2017–March 2020. The August 2021–August 2023 `BPQ`
  public file contains no hypertension-treatment item, so this canonical column is unavailable in the later cycle.
  It is retained in the schema, reported in the cycle availability table, and, because it is constant after the
  training-fitted imputation in the later cycle, it cannot change the ranking of the later-cycle cohort. The rule
  executor treats it as unobserved rather than as "no".
- **Decision:** First-degree family history of diabetes (`MCQ300C`) is **not** used as a feature or as an
  operationalized criterion. It exists in the 2017–March 2020 public `MCQ` file but is **not included** in the
  August 2021–August 2023 public `MCQ` file, so it cannot be harmonized across the temporal split.
- **Decision:** Gestational diabetes, PCOS and similar risk factors are recorded in the ontology as
  *not operationalized* (absent from the selected NHANES public files) rather than being approximated from
  unrelated fields.
- **Decision:** Every encoded rule stores its guideline section reference in the ontology
  (`:sectionReference`) so each flag is traceable to the ADA 2026 chapter text.

### Published-knowledge baseline (addendum §5)

- **Decision:** The CDC/ADA prediabetes risk test is encoded as an external baseline with the official scoring
  (age 0–3, man 1, gestational diabetes 1, family history 1, high blood pressure 1, physical inactivity 1,
  BMI 0–3 with a lower threshold for Asian respondents; high risk at ≥ 5 points). Score source:
  <https://www.cdc.gov/diabetes/widgets/risktest/pdf/prediabetes5of10.pdf> (CDC/ADA Prediabetes Risk Test,
  adapted from Bang et al., Ann Intern Med 2009).
- **Decision:** Items unavailable in the harmonized NHANES data are scored 0 and listed explicitly
  (`gestational_diabetes_history`, `family_diabetes_history`). The incomplete mapping is disclosed with every use
  of this baseline.

### Added exploratory experiments (addendum §3)

- **Decision:** Three pre-specified exploratory experiments are added and reported regardless of direction:
  E1 low-data learning curve (5/10/25/50/100% of historical data), E2 missing-input stress test (MCAR masking of
  waist, blood pressure, hypertension history and activity items at 10% and 30%, with ontology features
  re-derived from the masked inputs so the rule layer cannot read information the ML system does not have), and
  E3 model-family reporting (logistic regression and XGBoost reported separately, because threshold flags are
  expected to help a linear model more).
- **Reason:** With full historical data the rule flags are simple transforms of variables the model already sees,
  so a null primary result is plausible; these experiments test where knowledge can matter.

### Multiplicity and uncertainty hygiene (addendum §7, §8)

- **Decision:** H2 (hybrid vs XGBoost-only sensitivity at 20% capacity on the later cycle) is the **only**
  confirmatory test. H1, H3, H4, all addendum experiments and all subgroup analyses are exploratory and are
  labelled as such in `docs/EXPERIMENTS.md` and in the paper.
- **Decision:** Logistic regression and XGBoost defaults are deterministic; the five recorded seeds only affect
  the stochastic subsampling in XGBoost. Seed variability is reported separately from bootstrap uncertainty.
- **Decision:** The disagreement set is defined before evaluation as the symmetric difference between the top-k
  ML-selected set and the top-k rule-selected set at k = 20% capacity; the confidence-only review set is the same
  number of cases ranked closest to the ML top-k cutoff. Positives found and precision are compared at equal
  review sizes.
- **Decision:** The paired-bootstrap standard error of the sensitivity difference at 20% capacity is computed on
  **historical validation** and recorded as the smallest difference the design can resolve. Differences below that
  value are not described as wins.
- **Decision:** Outcomes of the later cycle are loaded once, in a single evaluation stage of the notebook, after
  the protocol documents above are final. Any subsequent code change is a bug fix and is recorded below.

## 2026-10-30 — Post-run log

- No entries yet. Bug fixes and deviations must be appended here with the date and the reason.
