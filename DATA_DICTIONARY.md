# Data Dictionary and Feature Contract

This dictionary describes the planned harmonized feature schema. The notebook must validate actual column availability against the relevant CDC cycle codebooks at runtime and update this file if the schema changes.

| Canonical field | Source variable(s) | Source file | Purpose | Model feature? |
|---|---|---|---|---|
| `SEQN` | `SEQN` | `DEMO` | Internal join key only | **No** |
| `cycle` | Project-defined from source cycle | all | Historical/temporal identifier | **No** |
| `age_years` | `RIDAGEYR` | `DEMO` | Age at screening; age 80 is top-coded | Yes |
| `sex_code` | `RIAGENDR` | `DEMO` | As-coded demographic category | Yes, categorical |
| `race_ethnicity_code` | `RIDRETH3` | `DEMO` | NHANES race/Hispanic-origin category, including non-Hispanic Asian | Yes, categorical; fairness analysis required |
| `education_code` | `DMDEDUC2` | `DEMO` | Adult education category; may be missing for younger adults | Yes, categorical |
| `income_poverty_ratio` | `INDFMPIR` | `DEMO` | Family income-to-poverty ratio | Yes, numeric |
| `bmi` | `BMXBMI` | `BMX` | Body mass index | Yes, numeric |
| `waist_cm` | `BMXWAIST` | `BMX` | Waist circumference in cm | Yes, numeric |
| `systolic_bp_mean` | `BPXOSY1`–`BPXOSY4` | `BPXO` | Mean of available valid systolic readings | Yes, numeric |
| `diastolic_bp_mean` | `BPXODI1`–`BPXODI4` | `BPXO` | Mean of available valid diastolic readings | Yes, numeric |
| `hypertension_history` | `BPQ020` | `BPQ` | Told by professional that BP was high | Yes, categorical |
| `hypertension_treatment` | `BPQ040A` (historical cycle only; `BPQ040` legacy fallback) | `BPQ` | Taking prescribed medicine for hypertension; used by ontology when available, not a harmonized model feature | No |
| `ever_smoked_100_cigs` | `SMQ020` | `SMQ` | Lifetime smoking history | Yes, categorical |
| `leisure_activity_minutes` | `PAQ635/640/645`, `PAQ650/655/660` | `PAQ` | Harmonized weekly recreational activity minutes; no-activity skip patterns are zero, special codes are missing | Yes, numeric |
| `sedentary_minutes` | `PAD680` | `PAQ` | Self-reported daily sitting time; special codes are missing | Yes, numeric |
| `hdl_cholesterol` | `LBDHDD` | `HDL` | HDL cholesterol measurement available in both cycles | Yes, numeric |
| `total_cholesterol` | `LBXTC` | `TCHOL` | Total cholesterol measurement available in both cycles; secondary lab setting only | Secondary setting 2 |
| `fasting_glucose` | `LBXGLU` | `GLU` | Fasting plasma glucose; available only for the fasting subsample and treated as a second glycemic test | Secondary setting 3 only |
| `heart_failure_history` | `MCQ160B` | `MCQ` | Self-reported congestive heart failure history | Yes, categorical |
| `coronary_heart_disease_history` | `MCQ160C` | `MCQ` | Self-reported coronary heart disease history | Yes, categorical |
| `angina_history` | `MCQ160D` | `MCQ` | Self-reported angina history | Yes, categorical |
| `heart_attack_history` | `MCQ160E` | `MCQ` | Self-reported heart attack history | Yes, categorical |
| `stroke_history` | `MCQ160F` | `MCQ` | Self-reported stroke history | Yes, categorical |
| `reported_diabetes` | `DIQ010` | `DIQ` | Cohort filter only; exact code `2` required | **No** |
| `reported_prediabetes` | `DIQ160` | `DIQ` | Cohort filter only; exact code `2` required | **No** |
| `hba1c_percent` | `LBXGH` | `GHB` | Primary outcome source only | **No** |
| `target` | Derived from `LBXGH >= 5.7` | project-derived | Screen-positive dysglycemia label | **No** |
| `target_diabetes_range` | Derived from `LBXGH >= 6.5` | project-derived | Secondary outcome only | **No** |

## Ontology-derived fields

| Field | Description |
|---|---|
| `onto_age_based_screening` | Age-based screening criterion flag, when age is known |
| `onto_bmi_threshold_met` | BMI threshold flag using encoded general/Asian ancestry thresholds, when assessable |
| `onto_hypertension_risk` | Combined measured-BP/self-report flag with missing data preserved where appropriate |
| `onto_cvd_history` | Any selected cardiovascular history response is positive |
| `onto_physical_inactivity` | Flag from harmonized leisure minutes and sedentary time; legacy yes/no fields are accepted only for backward-compatible examples |
| `onto_higher_risk_ethnicity` | Approximate implementation of a guideline risk factor; subject to fairness ablation |
| `onto_additional_risk_factor_count` | Count of observed additional risk factors; missing if none can be assessed |
| `onto_screening_eligible` | Output of the bounded encoded screening rules; not a diagnosis |
| `onto_criteria_observed_count` | Number of criteria that could be evaluated |
| `onto_criteria_missing_count` | Number of selected criteria not assessable |
| `onto_rule_priority_score` | Study-defined ordinal ranking score; not a calibrated risk probability |

## Forbidden predictors

Never include `SEQN`, `DIQ010`, `DIQ160`, `DIQ050`, `DIQ070`, `LBXGH`, or diabetes medication information in any model feature matrix. Fasting glucose is the explicit Setting 3 exception described below; it must never be silently included in Settings 1–2. The test suite and notebook check this contract.

## Feature settings

- **Setting 1 (primary):** `RAW_FEATURES`; non-glycemic, non-laboratory inputs only.
- **Setting 2 (secondary):** Setting 1 plus `hdl_cholesterol` and `total_cholesterol`.
- **Setting 3 (exploratory):** Setting 2 plus `fasting_glucose`, restricted to participants with non-missing `LBXGLU`. Settings 1 and 2 are rerun on this identical fasting subsample.

HbA1c and diabetes questionnaire items are excluded from every setting. Fasting glucose is not used in the ontology rules.
