# Prespecified Experiments

This document defines the final experiment suite. It is not a pilot gate; all comparisons are part of the complete project.

**Multiplicity statement (plan addendum §8).** Only **H2** is confirmatory. Every other comparison in this
document — H1, H3, H4, EX-1 to EX-3, the ablations, the published-score baseline and all subgroup summaries —
is **exploratory** and is reported regardless of the direction of the result.

## Confirmatory endpoint

### H2 — Primary fixed-capacity policy comparison

- Test cohort: NHANES August 2021–August 2023 participants satisfying the prespecified cohort/outcome rules.
- Primary comparison: XGBoost raw-feature ranking vs a hybrid policy that adds the ontology rule-priority score
  to the XGBoost score, with the hybrid weight selected on historical validation only.
- Primary endpoint: sensitivity at 20% screening capacity.
- Secondary capacities: 10% and 30%. Sensitivity is always reported together with prevalence, the sensitivity
  ceiling `min(1, capacity / prevalence)`, the fraction of that ceiling achieved, PPV and lift.
- Uncertainty: paired participant bootstrap (1,000 resamples) 95% interval for the sensitivity difference; the
  same participants are resampled for both policies. Five-seed variability is reported separately.
- Interpretation rule: a difference smaller than the design's smallest detectable difference (see below) is never
  described as a win.

## Exploratory experiments

### EX-1 (addendum E1) — Low-data learning curve

- Train each model family on 5%, 10%, 25%, 50% and 100% of the historical data (three stratified subsamples per
  fraction; one fit at 100%).
- Compare raw vs ontology-augmented features for logistic regression and XGBoost on the locked later-cycle test.
- Reported: AUROC, AUPRC, Brier score and sensitivity/PPV at 20% capacity, mean ± SD over subsamples.
- Question answered: *when does guideline knowledge help?*

### EX-2 (addendum E2) — Missing-input stress test

- At test time, mask waist circumference, mean systolic/diastolic blood pressure, hypertension history and the
  four physical-activity items MCAR at rates 0%, 10% and 30% (three fixed seeds).
- Ontology features are **re-derived from the masked inputs**, so the rule layer never reads information the ML
  system does not receive. The executor reports the fraction of participants with at least one criterion that is
  *not assessable* instead of guessing.
- Compared: raw vs ontology-augmented models within each family, plus the hybrid policy, at 20% capacity.

### EX-3 (addendum E3) — Model-family effect

- Logistic regression and XGBoost are reported separately for every headline comparison.
- Prior expectation, stated before evaluation: threshold flags should help the linear model more than the tree
  ensemble, because the ensemble can already learn the same splits from the raw variables.

### H1 — Discrimination and calibration change (exploratory)

- Logistic Regression raw and augmented; XGBoost raw and augmented.
- Report AUROC, AUPRC, prevalence, Brier score, calibration plot, and paired bootstrap differences on the later
  cycle test set.

### H4 — Ontology attribution ablation (exploratory)

- Compare ontology-generated features with an independently implemented generic feature-engineering control that
  produces the same feature values, and assert value equality.
- Equal predictive scores are interpreted as evidence that the metrics are driven by the derived information
  rather than by the OWL serialization; ontology provenance and traceability are evaluated separately.

### E4 — Rule-only ranking baseline (exploratory)

- Rank by the study-defined ordinal rule score with stable ties. Not a validated risk probability.

### Published-knowledge baseline (addendum §5, exploratory)

- CDC/ADA prediabetes risk test, official point scoring, mapped to harmonized NHANES fields.
- Unavailable items are scored 0 and listed: gestational diabetes history, family history of diabetes
  (`MCQ300C` is absent from the August 2021–August 2023 public `MCQ` file).

### H3 — Confidence-only review vs guideline disagreement (exploratory)

- Disagreement set: participants in the top-k ML set **XOR** the top-k rule-eligible set, with k = 20% of the test
  cohort.
- Confidence-only review set: the same number of participants whose ML scores lie closest to the ML top-k cutoff.
- Compare positives found and precision at equal review sizes. Disagreement is not assumed to be uncertainty;
  the observed relationship to model errors is reported.

### E6 — Temporal generalization (exploratory)

- Tune on historical development/validation only; report historical validation and later-cycle test metrics.
- Do not attribute shifts to COVID-19 or any other single cause.

### E7 — Higher-risk race/ethnicity rule-flag ablation and subgroups (exploratory)

- Re-run the ontology-feature models and fixed-capacity policies after excluding the higher-risk race/ethnicity
  *risk-factor flag* from the rule. This is **not** a fully race-blind analysis: raw race/ethnicity remains a model
  predictor and the Asian-specific BMI threshold remains encoded.
- Secondary HbA1c ≥ 6.5% counts are reported as a single-measurement diabetes-range outcome.
- Subgroup summaries only where counts support a meaningful estimate; counts and uncertainty always shown.

## Smallest detectable difference

- Before any later-cycle evaluation, the paired-bootstrap standard error of the sensitivity difference at 20%
  capacity is computed on the historical validation split for the primary comparison and for the logistic
  regression raw-vs-augmented comparison.
- `MDE = 1.96 × SE` is stored in `research_results.json`. Effects below this magnitude are reported as below the
  resolution of the design.

## Automated integrity checks

- Assert outcome-only columns never enter a predictor set.
- Assert the temporal test set is not passed to GridSearchCV or policy-weight selection.
- Assert output metrics all derive from `y_test` and saved model predictions.
- Assert screening policies choose the requested number of people to within rounding.
- Assert each ontology rule has a source, a documented expression and a section reference.
