# Paper Outline

## Provisional title
Ontology-Guided Screening for Undetected Dysglycemia: Evaluating Clinical Knowledge Integration Under Temporal Shift in NHANES

## Abstract
Write only after results are final. Include the precise cohort/target, data periods, model variants, primary metric, measured effect with uncertainty, and important limitations.

## 1. Introduction
- Explain why tabular ML can support but not replace clinical screening.
- Explain why transparent guideline encoding and later-cycle evaluation matter.
- State the narrow gap established by a current related-work comparison.
- State the primary question: sensitivity at 20% screening capacity.

## 2. Related work
- NHANES-based diabetes/dysglycemia prediction.
- Clinical ontology and guideline-based decision support.
- Temporal/generalization evaluation in health ML.
- Selective prediction and fixed-capacity screening.
- Closest-paper comparison table: dataset, target, ontology role, temporal test, baseline, primary metric, contribution, limitation.

## 3. Data
- CDC sources and access dates.
- Cycle differences and the rationale for calling this temporal generalization.
- Cohort flow, exclusions, outcome distribution, missingness and feature availability.
- Primary and secondary outcome definitions.

## 4. Ontology and rule engine
- Ontology scope, classes/properties, standard concepts, rule provenance.
- Executable rule subset and unknown/missing handling.
- Traceable explanation format.
- Scope limitations and race/ethnicity considerations.

## 5. Methods
- Leakage-safe feature contract.
- Logistic Regression and XGBoost pipelines.
- Cross-validation and historical validation.
- Raw, ontology-feature, generic-feature, rule-only and hybrid-policy comparisons.
- Temporal test and prespecified metrics.
- Seed variation and paired bootstrap confidence intervals.

## 6. Results
1. Cohort and data quality.
2. Main metrics on historical validation and temporal test.
3. Sensitivity at 10%, 20%, 30% screening capacity.
4. Paired uncertainty intervals for the primary difference.
5. Calibration and discrimination.
6. Ontology feature and generic-feature ablations.
7. Disagreement and confidence-only review baseline.
8. Subgroup performance where sample size supports interpretation.

## 7. Discussion
- What the results support.
- What the results do not support.
- Comparison to closest work without claiming unfair score superiority.
- Practical role of a guideline provenance/explanation layer.

## 8. Limitations and ethics
- Single HbA1c measurement, not confirmed diagnosis.
- Public survey sample and cycle design differences.
- Incomplete operationalization of ADA criteria.
- Missing features and self-report errors.
- Fairness concerns and limited subgroup sample sizes.
- No clinical deployment or prospective evaluation.

## 9. Conclusion
State the most defensible empirical finding, including uncertainty or a null result.
