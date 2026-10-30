# ClinOntoScreen manuscript support

This file is the working evidence sheet for drafting the manuscript. Values below
are taken from the committed aggregate artifacts, not manually re-estimated. The
primary source files are [`results/research_results.json`](../results/research_results.json),
[`results/feature_settings.json`](../results/feature_settings.json), and
[`results/cohort_flow.json`](../results/cohort_flow.json).

## Recommended title

**Ontology-Assisted Screening Prioritization for HbA1c-Defined Dysglycemia Under
Temporal Shift in NHANES**

This title avoids claiming diagnosis, clinical validation, or predictive
superiority. Other suitable options:

1. **Evaluating an Auditable Clinical Ontology Layer for Dysglycemia Screening in
   Later-Cycle NHANES Data**
2. **Guideline-Traceable Machine Learning for HbA1c-Defined Dysglycemia Screening:
   A Temporal NHANES Evaluation**
3. **From Risk Scores to Rule-Provenance: An Ontology-Assisted NHANES Study of
   Dysglycemia Screening**
4. **Do Clinical Rules Improve Fixed-Capacity Dysglycemia Screening? An
   Ontology-Ablation Study in NHANES**
5. **Leakage-Safe and Temporally Evaluated Ontology-Assisted Screening for
   HbA1c-Defined Dysglycemia**
6. **Clinical Knowledge Integration Without Guaranteed Performance Gain: An
   Ontology-Assisted Dysglycemia Screening Study**

## One-paragraph study summary

This retrospective study evaluates whether an auditable clinical ontology layer
improves fixed-capacity screening prioritization for HbA1c-defined dysglycemia.
Adults from NHANES 2017–March 2020 who reported neither prior diabetes nor prior
prediabetes and had valid HbA1c were used for development; NHANES August
2021–August 2023 was held out as a later-cycle temporal test. The primary target
was a single-measurement HbA1c value of at least 5.7%, and HbA1c and diabetes
questionnaire variables were excluded from every feature setting. Logistic
Regression and XGBoost were compared with and without deterministic ontology
features and an ontology-assisted ranking policy. The primary endpoint was
sensitivity at 20% screening capacity. A post-hoc secondary analysis added
routine lipid measurements and, in a fasting subsample, fasting plasma glucose.

## Methods text to adapt

### Design and cohort

The analysis used public NHANES files from the 2017–March 2020 pre-pandemic
release for model development and the August 2021–August 2023 release as a
locked later-cycle test set. This is described as temporal generalization, not
as a causal comparison of survey periods. Participants were eligible for the
primary cohort if they were aged at least 18 years, reported no prior diabetes
(`DIQ010 = 2`) and no prior prediabetes (`DIQ160 = 2`), and had a valid HbA1c
measurement (`LBXGH`). The research target was `LBXGH >= 5.7%`; it is a
single-measurement label and not a confirmed diagnosis.

### Feature contract

The prespecified primary Setting 1 used non-glycemic, non-laboratory variables:
age, sex, race/ethnicity code, education, income-to-poverty ratio, BMI, waist
circumference, mean systolic and diastolic blood pressure, leisure activity
minutes, sedentary minutes, hypertension history, smoking history, and selected
cardiovascular history. HbA1c, glucose, diabetes questionnaire items, treatment
variables, and participant identifiers were prohibited predictors. Setting 2
added HDL and total cholesterol. Exploratory Setting 3 added fasting plasma
glucose and was restricted to participants with non-missing fasting glucose.
Settings 1 and 2 were rerun on that same fasting subsample for a fair comparison.

Settings 2 and 3 were added after the original primary result and must be
identified as secondary/exploratory post-hoc analyses. Fasting plasma glucose is
a second glycemic test and should not be described as a neutral routine feature.
No fasting-glucose threshold was added to the ontology.

### Models and evaluation

Logistic Regression and XGBoost were fitted with preprocessing inside each
pipeline. Historical data were used for model selection and policy-weight
selection; the later-cycle test set was not used for tuning. Five seeds
(`17, 42, 123, 2025, 2026`) were used for the model runs. Screening capacity
was fixed at 10%, 20%, and 30% of the temporal test cohort. The primary
comparison was sensitivity at 20% capacity for XGBoost raw ranking versus the
ontology-assisted policy. Paired participant bootstrap intervals used 1,000
replicates. The analysis was unweighted; therefore predictive metrics are not
automatically nationally representative.

## Cohort-flow evidence

The counts below were regenerated from the cached source files by
[`tools/generate_paper_support.py`](../tools/generate_paper_support.py). Exclusions
are sequential within each cycle.

| Cycle | Merged rows | Adults | Eligible | Screen-positive | Screen-negative | FPG available among eligible |
|---|---:|---:|---:|---:|---:|---:|
| 2017–March 2020 | 15,560 | 9,693 | 6,103 | 1,766 | 4,337 | 2,959 |
| August 2021–August 2023 | 11,933 | 8,153 | 4,260 | 983 | 3,277 | 2,348 |

For a CONSORT-style flow, report the corresponding sequential exclusions:

| Cycle | Under 18 | Prior diabetes | Unknown diabetes response | Prior prediabetes after no diabetes | Unknown prediabetes response | Missing HbA1c after valid histories |
|---|---:|---:|---:|---:|---:|---:|
| 2017–March 2020 | 5,867 | 1,423 | 272 | 923 | 13 | 959 |
| August 2021–August 2023 | 3,780 | 1,073 | 277 | 884 | 12 | 1,647 |

## Primary results

The locked temporal test cohort contained 4,260 participants, of whom 983
(23.08%) met the HbA1c-defined screen-positive target. At 20% capacity, the
primary Setting 1 XGBoost raw ranking found 396 positives (sensitivity 40.28%;
precision 46.48%). The ontology-assisted policy found 404 positives (sensitivity
41.10%; precision 47.42%). The absolute sensitivity difference was **0.81
percentage points** with a paired bootstrap 95% CI of **−0.43 to 1.84
percentage points**. Because the interval includes zero, the primary analysis
does not establish a statistically clear ontology improvement.

The primary XGBoost raw sensitivity at 10%, 20%, and 30% capacity was 22.38%,
40.28%, and 57.07%, respectively. The corresponding ontology-assisted policy
sensitivities were 22.79%, 41.10%, and 56.88%.

The primary aggregate discrimination results were:

| Variant | AUROC | AUPRC | Brier score |
|---|---:|---:|---:|
| Logistic Regression, raw | 0.7650 | 0.4436 | 0.1529 |
| XGBoost, raw | 0.7632 | 0.4515 | 0.1524 |
| Logistic Regression, ontology features | 0.7621 | 0.4436 | 0.1529 |
| XGBoost, ontology features | 0.7634 | 0.4526 | 0.1518 |
| XGBoost, generic equivalent features | 0.7634 | 0.4526 | 0.1518 |

The identical XGBoost ontology-feature and generic-feature-control results
support attributing any numerical change to the engineered values rather than
to RDF/OWL serialization itself.

## Secondary and exploratory results

At 20% capacity on the main temporal cohort, Setting 2 XGBoost raw sensitivity
was 41.40% compared with 40.28% for Setting 1. Setting 2 XGBoost with ontology
features had sensitivity 42.42% in the committed secondary run. These are
post-hoc secondary findings.

The fasting test subsample contained 2,348 participants and 546 positives.
Setting 3, which adds fasting plasma glucose, reached 44.32% sensitivity at 20%
capacity for the XGBoost ontology-feature variant. In the same fasting
subsample, Setting 1 had 39.56% sensitivity and Setting 2 with ontology
features had 39.93%. This pattern is expected for a closely related glycemic
measurement and should be presented as context, not as evidence that the
ontology itself improves prediction.

The machine-readable secondary table is
[`results/secondary_feature_settings_table.csv`](../results/secondary_feature_settings_table.csv).

## Figure and table plan

Use the following committed artifacts:

| Manuscript item | Artifact | Suggested caption emphasis |
|---|---|---|
| Figure 1 | `docs/project_architecture.png` | Reproducible data, ontology, model, policy, and reporting flow |
| Figure 2 | `results/cohort_flow.json` | Sequential cohort exclusions and FPG availability |
| Figure 3 | `ontology/diabetes_screening.ttl` | Bounded rule provenance and source-variable links |
| Figure 4 | `results/roc_pr_curves.png` | Temporal-test discrimination; descriptive, not clinical validation |
| Figure 5 | `results/calibration.png` | Temporal-test probability calibration |
| Figure 6 | `results/capacity_sensitivity.png` | Sensitivity under fixed referral budgets |
| Figure 7 | `results/primary_effect_ci.png` | Uncertainty in ontology-policy minus ML-only sensitivity |
| Table 1 | `results/cohort_flow.json` and `artifacts/data_qc.json` | Cohort, prevalence, missingness, and source availability |
| Table 2 | `results/research_results.json` | AUROC, AUPRC, Brier score, and model variants |
| Table 3 | `results/tier1_metrics.csv` | Fixed-capacity cases found, sensitivity, precision, and false referrals |
| Table 4 | `results/secondary_feature_settings_table.csv` | Post-hoc Settings 1–3 and matched fasting-subset comparison |

## Reporting checklist before submission

- Replace the provisional abstract with the exact primary effect and interval.
- Add verified bibliographic references and a closest-paper comparison table.
- State that the primary analysis is unweighted and not automatically nationally representative.
- State that HbA1c is a single-measurement research label, not confirmed diabetes or prediabetes.
- Identify Settings 2–3 as post-hoc secondary/exploratory analyses.
- Identify fasting plasma glucose as a second glycemic test.
- Explain that ontology-feature and generic-feature results were numerically identical.
- Include the cohort-flow counts and source-file checksum provenance.
- Explain that the later-cycle evaluation is temporal generalization, not causal pandemic inference.
- Include race/ethnicity rule limitations and the higher-risk ethnicity-flag ablation.
- Do not claim clinical deployment, diagnosis, causal inference, national representativeness, or ontology superiority.
- Add a TRIPOD+AI checklist and venue-specific reporting requirements.
- Re-run the checksum/provenance script and test suite immediately before submission.

## Reproducibility status

The run manifest records the source URLs, file sizes, SHA-256 hashes, ontology
hash, feature-setting hash, primary-results hash, seeds, bootstrap count, and
the fact that the temporal test set was not used for tuning. Run:

```powershell
python tools\generate_paper_support.py
python -m pytest -q
```

The public result export remains aggregate-only. Do not add participant-level
predictions, model bundles, or `SEQN`-containing files to the manuscript
repository without a separate disclosure review.
