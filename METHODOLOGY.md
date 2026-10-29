# Methodology and Study Protocol

## Study design

Retrospective predictive-model comparison using the NHANES 2017–March 2020 pre-pandemic dataset for model development and NHANES August 2021–August 2023 as a locked later-cycle test set. Differences between cycles can reflect sampling, participation, questionnaire and examination changes; results are described as temporal generalization, not causal effects of the pandemic.

## Outcome and cohort

Primary cohort: participants aged at least 18 years with a valid HbA1c measurement who answer “No” to both the NHANES questions on prior diabetes (`DIQ010 == 2`) and prior prediabetes (`DIQ160 == 2`). Primary target: `1` if `LBXGH >= 5.7%`, else `0`. Secondary outcome: a single HbA1c measurement `>= 6.5%` in the same cohort. The secondary threshold is a diabetes-range laboratory result, not a confirmed diagnosis. ADA guidance generally requires confirmatory testing where hyperglycemia is not unequivocal.

The outcome and cohort-filter variables are forbidden predictors. The model must not use HbA1c, plasma glucose, other glycemic laboratory measurements, diabetes diagnoses or treatment variables.

## Input features

The canonical non-glycemic input includes age, NHANES sex and race/ethnicity codes, education, family income-to-poverty ratio, BMI, waist circumference, mean available systolic/diastolic blood pressure readings, self-reported hypertension/treatment, smoking history, available work/recreational activity items, and selected cardiovascular history fields. Source variables can be absent or ineligible in certain cycle/file versions; the notebook logs such differences and preserves a consistent canonical schema.

Categorical responses are not treated as ordinal measurements. Refused/don't-know codes are set to missing according to each codebook. No missing answer is assumed to mean “No.” Preprocessing is fitted on historical data only.

## Ontology

`ontology/diabetes_screening.ttl` represents selected ADA screening concepts, rule sources, source variable identifiers, outcome definitions, and scope limitations. Python executes the documented numeric and logical rules deterministically and returns both features and explanations. The ontology is a bounded research encoding, not a complete clinical decision support system.

The selected encoded rule subset includes age-based screening and BMI-plus-additional-risk screening for younger adults, with available hypertension, selected cardiovascular history, physical activity and race/ethnicity factors. Some ADA risk factors are not represented because they may not be consistently available in these NHANES files. The ethnicity mapping is approximate and must be evaluated with an ablation excluding that criterion.

## Models

- Logistic Regression.
- XGBoost.
- Each model with raw features and with raw plus ontology-derived features.
- Ontology-only ordinal rule score for ranking.
- ML plus ontology ranking policy.
- Confidence-only selective-review baseline.
- Equivalent generic engineered-feature control.

Preprocessing, imputation, and encoding are inside each fitted pipeline. Hyperparameters are selected by cross-validation on historical development data using average precision. Policy weights are selected on a held-out historical validation subset. Models are refit on all historical eligible data for five fixed seeds. The 2021–2023 test set is evaluated only after choices are locked.

## Primary endpoint and metrics

Primary endpoint: sensitivity at 20% screening capacity, comparing the XGBoost-only ranking against the ontology-assisted ranking on the same temporal test cohort. Also report 10% and 30% capacity. Capacity is the fraction of participants selected for further screening, not a clinical probability threshold.

Secondary metrics: AUROC, average precision/AUPRC, prevalence, precision, recall, specificity, F1 at a clearly described threshold, Brier score, calibration curve, positive cases found, false referrals, rule coverage, disagreement breakdown, temporal performance degradation, and adequately powered subgroup analyses.

Report average and standard deviation over five model seeds. Use paired participant bootstrap confidence intervals for the primary comparisons. Seed variation and bootstrap uncertainty are distinct and both must be described.

## Fair comparison and attribution

The ontology-feature model is compared with a generic feature-engineering control. If both use exactly the same values, predictive performance should match; any ontology-specific contribution must instead be justified through provenance, queryability, consistency checks and explanation traceability. Do not claim that the OWL format itself increases predictive accuracy.

## Ethics and limitations

The target is one measured HbA1c result, not a clinical diagnosis. NHANES cycles differ in design and response rates. Data are survey samples, and unweighted model metrics are not automatically nationally representative. The screening ontology is incomplete. Race/ethnicity rules require careful interpretation and sensitivity analysis. The demo is not a medical device and must not be used for patient care.
