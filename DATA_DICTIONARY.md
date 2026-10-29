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
| `hdl_chol_mgdl` | `LBDHDD` | `HDL` | HDL cholesterol, available in both cycles | Yes, numeric |
| `systolic_bp_mean` | `BPXOSY1`–`BPXOSY4` | `BPXO` | Mean of available valid systolic readings (4th reading absent in both cycles) | Yes, numeric |
| `diastolic_bp_mean` | `BPXODI1`–`BPXODI4` | `BPXO` | Mean of available valid diastolic readings (4th reading absent in both cycles) | Yes, numeric |
| `hypertension_history` | `BPQ020` | `BPQ` | Told by professional that BP was high | Yes, categorical |
| `hypertension_treatment` | `BPQ040A` | `BPQ` | Taking prescribed medicine for hypertension. **Cycle-asymmetric: exists only in 2017–March 2020, so it is 100% missing in the 2021–2023 test cohort** (disclosed, not imputed away silently) | Yes, categorical |
| `ever_smoked_100_cigs` | `SMQ020` | `SMQ` | Lifetime smoking history | Yes, categorical |
| `leisure_activity_minutes` | 2017–Mar 2020: `PAD660` + `PAD675` (skip pattern `PAQ650`/`PAQ665` = 2 → 0); 2021–2023: `PAD820` + `PAD800` | `PAQ` | Weekly minutes of vigorous + moderate **leisure-time** activity, cycle-harmonized across incompatible instruments (7777/9999/77777/99999 masked) | Yes, numeric |
| `sedentary_minutes` | `PAD680` | `PAQ` | Daily sedentary minutes (available in both cycles) | Yes, numeric |
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
| `onto_physical_inactivity` | Flag from the cycle-harmonized `leisure_activity_minutes` (0 minutes → inactive); unknown when minutes are missing |
| `onto_higher_risk_ethnicity` | Approximate implementation of a guideline risk factor; subject to fairness ablation |
| `onto_additional_risk_factor_count` | Count of observed additional risk factors; missing if none can be assessed |
| `onto_screening_eligible` | Output of the bounded encoded screening rules; not a diagnosis |
| `onto_criteria_observed_count` | Number of criteria that could be evaluated |
| `onto_criteria_missing_count` | Number of selected criteria not assessable |
| `onto_rule_priority_score` | Study-defined ordinal ranking score; not a calibrated risk probability |

## Forbidden predictors

Never include `SEQN`, `DIQ010`, `DIQ160`, `DIQ050`, `DIQ070`, `LBXGH`, any glucose/glycemic lab, HbA1c, disease outcome labels, or diabetes medication information in the model feature matrix. The test suite and notebook must check this contract.

## Variables intentionally not harmonized

Listed by the notebook in `artifacts/data_qc.json → unharmonized_variables`:

- `MCQ300C` (family history of diabetes) — only in 2017–March 2020; not used. This also makes the
  family-history item of the CDC/ADA risk test unavailable in both modeled cohorts (scored 0,
  disclosed).
- `BPQ040A` — present only in the earlier cycle (see row above); `gestational_diabetes_history`
  is unavailable in NHANES entirely, so two CDC/ADA risk-test items score 0 for everyone
  (`protocol.cdc_ada_unavailable_items`).
- Cycle-specific physical-activity minute items (`PAD660`/`PAD675` vs `PAD800`/`PAD820`) and
  gate questions (`PAQ650`/`PAQ665`) are inputs to `leisure_activity_minutes`, never model features.
- Survey weight columns (`WTMEC2YR` vs `WTMECPRP`) — different names per cycle; survey weights are
  **not used** in this study (documented limitation).
- `BPXOSY4`/`BPXODI4` — fourth BP reading absent from both cycles.
