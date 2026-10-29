# Prespecified Experiments

This document defines the final experiment suite. It is not a pilot gate; all comparisons are part of the complete project.

## E1: Primary fixed-capacity policy comparison

- Test cohort: NHANES 2021–2023 participants satisfying the prespecified cohort/outcome rules.
- Primary comparison: XGBoost raw-feature ranking vs XGBoost raw-score-plus-ontology rule-priority ranking.
- Primary endpoint: sensitivity at 20% capacity.
- Secondary capacities: 10% and 30%.
- Selection/tuning: historical validation only.
- Uncertainty: paired participant bootstrap confidence interval on sensitivity difference; also report five-seed variation.

## E2: ML discrimination and calibration

- Logistic Regression raw and augmented.
- XGBoost raw and augmented.
- Report AUROC, average precision/AUPRC, prevalence, Brier score, calibration plot, and threshold metrics with thresholds clearly stated.
- Use identical held-out participants for paired comparisons.

## E3: Ontology attribution ablation

- Compare ontology-generated features with an independently implemented generic feature-engineering control that produces the same defined feature values.
- Verify value equality and leakage-free feature contract.
- Interpret equal predictive scores as evidence that the metrics are driven by the derived information rather than OWL serialization itself. Evaluate ontology provenance/traceability separately.

## E4: Rule-only ranking baseline

- Rank by the study-defined ordinal rule score, with stable ties.
- Clearly state that this is not a validated risk probability or a complete guideline implementation.
- Report the same fixed-capacity metrics as E1.

## E5: Confidence-only review baseline

- Use model uncertainty (for example, distance from 0.5 or entropy) to select cases for review.
- Compare with ontology disagreement at the same review capacity.
- Do not assume disagreement is uncertainty; test its observed relationship to model errors.

## E6: Temporal generalization

- Tune on historical development/validation only.
- Report historical validation and later-cycle test metrics.
- Do not attribute shifts to COVID-19 or a particular cause.

## E7: Sensitivity and subgroup analysis

- Primary rule model with and without the higher-risk race/ethnicity criterion.
- Secondary HbA1c threshold of >=6.5%, clearly labelled as a single-measurement diabetes-range result.
- Subgroup summaries only where sample size supports a meaningful estimate; always show counts and uncertainty.

## Automated integrity checks

- Assert outcome-only columns never enter a predictor set.
- Assert the temporal test set is not passed to GridSearchCV or policy-weight selection.
- Assert output metrics all derive from `y_test` and saved model predictions.
- Assert screening policies choose the requested number of people to within rounding.
- Assert each ontology rule has a source and a documented expression.
