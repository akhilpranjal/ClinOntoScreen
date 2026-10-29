# ClinOntoScreen: Research and Engineering Plan

> **Project status:** implementation blueprint and starter repository.  No model has been trained and no empirical result is claimed in this document.
>
> **Project goal:** build the complete application and research pipeline from the start: a real medical ontology, reproducible ML training, temporal evaluation on NHANES, an interactive demo, and a results dashboard. The project will not use a preliminary pilot as a gate before building the main components. The final evaluation is part of the finished project, not an optional preliminary exercise.

## 1. Project definition

### Working title

**Ontology-Guided Screening for Undetected Dysglycemia: Evaluating Clinical Knowledge Integration Under Temporal Shift in NHANES**

The title may be revised after the literature comparison and results. Do not use “first”, “novel”, “clinically validated”, or “improves robustness” as an established fact until the evidence supports the exact claim.

### Problem statement

Machine-learning models can estimate the likelihood that an individual has an elevated HbA1c result, but they do not inherently explain how clinical screening recommendations apply to that individual. A small, explicit medical ontology can represent screening criteria, derive interpretable features, and show which criteria were met. This project evaluates whether using those outputs improves screening prioritization compared with ML alone.

### Primary research question

**At the same screening capacity, does an ontology-assisted ML policy identify more NHANES participants with HbA1c-defined screen-positive dysglycemia than an ML-only policy?**

### Secondary research questions

1. Do ontology-derived features change discrimination or probability calibration compared with the same ML model trained on raw features?
2. Does ontology-assisted ranking improve results on the later 2021–2023 NHANES cycle compared with historical validation?
3. Do ML–guideline disagreements identify additional positive cases beyond model-confidence-based review?
4. Which types of rule, missing data, and demographic subgroup account for any observed gain or loss?
5. Does the ontology improve traceability and explanation quality even where it does not improve predictive metrics?

### Hypotheses to test, not assumed outcomes

- **H1:** Adding ontology-derived features changes at least one predictive metric on the held-out temporal test set.
- **H2 (primary):** At 20% screening capacity, the ontology-assisted policy has higher sensitivity than the XGBoost-only ranking policy.
- **H3:** Guideline disagreement identifies a group with a different error profile from a group selected using model uncertainty alone.
- **H4:** Any benefit is not explained solely by generic feature engineering. This is assessed using equivalent manually engineered features and clear ablations.

A result can reject a hypothesis. Do not alter the final test set, metrics, or target after seeing results just to obtain a positive table.

## 2. Dataset and temporal study design

### Selected data source

Use the public-use **National Health and Nutrition Examination Survey (NHANES)** files from:

- **Historical development data:** NHANES 2017–March 2020 pre-pandemic release (`P_` filenames).
- **Locked temporal test data:** NHANES August 2021–August 2023 release (`_L` filenames).

Official data portals:

- NHANES 2021–2023: <https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023>
- NHANES 2017–March 2020: <https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2017-2020>
- NHANES variable search: <https://wwwn.cdc.gov/nchs/nhanes/default.aspx>

The CDC states that the 2021–2023 cycle uses an updated sample design, modified questionnaires, and modified examination procedures. Treat the evaluation as temporal generalization to a later survey cycle. Do **not** claim that any performance difference is caused by COVID-19 or a specific biological change. Do not combine the two periods as though they were one simple nationally representative sample.

### Files used

The notebook downloads public XPT files from the CDC. It should require only a working internet connection in Kaggle or Colab. Required files:

- `DEMO`: demographics and survey design metadata.
- `DIQ`: prior self-reported diabetes/prediabetes responses, used only for cohort definition.
- `GHB`: HbA1c laboratory measurement, used only to define the outcome.
- `BMX`: body measurements, including BMI and waist circumference.

Optional files that add useful complexity, where variables are present in both periods:

- `BPXO`: measured blood pressure readings.
- `BPQ`: self-reported hypertension and treatment.
- `SMQ`: smoking history.
- `PAQ`: work and recreational physical activity.
- `MCQ`: selected self-reported cardiovascular conditions.

The data loader must handle optional-file or optional-variable absence without silently changing feature names. It must log every skipped file, missing variable, and missingness rate. If an essential file or target variable is missing, stop with a clear error.

### Cohort and target

**Primary cohort:** adults aged 18 years or older who report neither a previous diabetes diagnosis nor a previous prediabetes diagnosis, and have a valid HbA1c measurement.

**Primary target:** `screen_positive_dysglycemia = 1` if `LBXGH >= 5.7`; otherwise `0`, among the cohort above.

- `DIQ010 == 2` and `DIQ160 == 2` are used to define the primary cohort, not as model predictors.
- `LBXGH` is the outcome source and must never be a model input.
- Glucose, HbA1c, glycemic laboratory values, diabetes medication variables, and diagnosis-questionnaire variables must never enter the feature matrix.
- The outcome is **HbA1c-defined screen-positive dysglycemia**, not a confirmed clinical diagnosis. ADA guidance generally requires confirmatory testing for diagnosis when hyperglycemia is not unequivocal.
- Secondary analysis: HbA1c `>= 6.5%` as a diabetes-range laboratory result. Label it as a single-measurement secondary outcome, not confirmed diabetes. Report the positive count and uncertainty; do not overstate the result if the count is small.

### Feature set

Use non-glycemic data available before the HbA1c outcome is considered:

- Demographic: age, sex, NHANES race/ethnicity category, education, income-to-poverty ratio.
- Anthropometric: BMI, waist circumference.
- Examination: mean available systolic and diastolic blood pressure readings.
- Self-reported health: hypertension history/treatment and selected cardiovascular history variables.
- Behaviour: ever-smoked 100 cigarettes and available physical-activity questionnaire items.

Feature harmonization rules:

1. Use common semantic feature names across both cycles; preserve the original NHANES variable names in a data dictionary.
2. Treat codebook refusal, “don't know”, and other special response codes as missing, not as numeric values.
3. Do not infer that missing means “no”.
4. Fit imputation, scaling, and categorical encoders on historical training data only.
5. Report cohort exclusions, class counts, missingness, and variable availability by cycle.
6. Use the same final feature columns and encodings for both periods. Missing optional source variables become missing values with a documented reason, not an undocumented new category.

### Survey design

The primary goal is a predictive-model comparison, not a new national prevalence estimate. Report unweighted predictive metrics as the prespecified primary analysis and clearly state that they do not automatically represent national population performance. Include a documented survey-weighted descriptive or sensitivity analysis only when the cycle-specific weights and design variables are applied correctly according to CDC guidance. Do not concatenate weights from different designs naively.

## 3. Ontology and executable rule layer

### What the ontology does

Create a real, version-controlled RDF/OWL ontology at `ontology/diabetes_screening.ttl`. Use RDFLib to load, validate, query, and display it. The ontology represents:

- Patient characteristics and measurements.
- Screening criteria and the applicable guideline source.
- BMI thresholds, age-based screening criteria, and selected additional risk factors that can be reliably derived from the selected NHANES variables.
- The relationship between a criterion, a rule, a patient's observed feature, and the explanation emitted by the system.
- A mapping for the HbA1c laboratory concept (for outcome documentation only; never as a predictor), with source and identifier provenance.
- Version, citation, applicability notes, data requirements, and known limitations for each encoded rule.

Use LOINC only for a verified concept mapping. Do not claim that every NHANES field has a formal LOINC mapping. Maintain original NHANES source-variable identifiers and mapping evidence alongside any external terminology identifier.

### Guideline source

Use the **American Diabetes Association Standards of Care in Diabetes—2026**, especially the sections on diagnosis and screening. Official chapter: <https://diabetesjournals.org/care/article/49/Supplement_1/S27/163926/2-Diagnosis-and-Classification-of-Diabetes>

Encode a deliberately bounded, explicit subset of recommendations that can be operationalized from the chosen variables. Do not describe the ontology as a complete ADA guideline implementation. Record every limitation, including risk factors unavailable in the selected NHANES files and the imperfect fit between NHANES race/ethnicity categories and guideline language.

### Rule execution

The OWL/RDF graph is the authoritative, traceable knowledge representation. A deterministic Python rule executor reads the documented rule parameters and evaluates each participant. It emits:

- Rule/criterion flags.
- A count of observed criteria and a count of criteria not assessable because inputs are missing.
- `screening_eligible` and a separate study-defined ordinal rule score.
- A structured explanation listing the rules fired, the input feature values used, and the applicable source.

Do not call the ordinal rule score a validated clinical risk probability. Do not state that rule disagreement proves model uncertainty. Race/ethnicity-sensitive criteria require a separate ablation and a limitations discussion; do not present race as a biological cause.

### Ontology features

At minimum, evaluate these derived fields:

- `onto_age_based_screening`
- `onto_bmi_threshold_met`
- `onto_hypertension_risk`
- `onto_cvd_history`
- `onto_physical_inactivity`
- `onto_higher_risk_ethnicity` (only if the mapping is justified and documented)
- `onto_additional_risk_factor_count`
- `onto_screening_eligible`
- `onto_criteria_observed_count`
- `onto_criteria_missing_count`
- `onto_rule_score`

Use the same executable rules for the notebook, application, tests, and explanations. Add tests for boundary values, missing data, codebook categories, and conflicting criteria.

### Required ontology ablation

A fair paper must separate three things:

1. **Raw ML:** original input features only.
2. **ML + guideline-derived features:** original features plus ontology-derived features.
3. **ML + generic feature-engineering control:** equivalent logical transformations implemented without querying the ontology.

If systems 2 and 3 have identical features, their predictive metrics should be identical or effectively identical. The ontology's value in that case is traceability, consistency, explainability, and maintainable rule provenance, not a magical increase in AUROC. State this accurately.

## 4. ML models and evaluation

### Models

- **Logistic Regression:** interpretable baseline.
- **XGBoost:** primary nonlinear tabular model.
- **Ontology-only ranking:** rule-based baseline, clearly described as an ordinal policy, not a calibrated probability.

Use identical historical development data, target definition, temporal test participants, and outcome handling for fair comparisons. Tune only on historical data. Save fitted preprocessing and the model together as one scikit-learn pipeline.

### Training protocol

1. Load and validate the historical dataset and the locked 2021–2023 test dataset.
2. Split only the historical data into development and validation subsets with a fixed, recorded seed.
3. Select model hyperparameters with stratified cross-validation within the historical development split. Use average precision/AUPRC as the primary selection score; keep grids small and pre-specified.
4. Tune any hybrid policy weight or threshold using historical validation only.
5. Refit each configuration on all eligible historical data using the selected hyperparameters.
6. Repeat stochastic training for five fixed seeds. Report mean and standard deviation across seeds.
7. Evaluate on 2021–2023 only after the design and hyperparameters are fixed. Do not use the test set to choose thresholds, rule weights, features, or models.
8. Save the exact test predictions and metadata so all tables and plots can be regenerated.

### Main model variants

- Logistic Regression, raw features.
- XGBoost, raw features.
- Logistic Regression, raw + ontology features.
- XGBoost, raw + ontology features.
- Ontology-only rule score.
- ML + ontology policy: ML risk score adjusted by the documented ontology rule score, with the adjustment selected on historical validation only.
- Generic engineered-feature control.
- Confidence-only selective review baseline, so the ontology disagreement flag is not compared with an artificially weak alternative.

### Primary outcome

**Sensitivity/recall at 20% screening capacity** on the held-out 2021–2023 cohort, comparing the hybrid screening policy with the XGBoost-only ranking policy. A screening capacity of 20% means selecting the highest-ranked 20% of the eligible cohort, not applying an unvalidated fixed clinical probability threshold.

Also report results at 10% and 30% capacity. The policy's referral count must be the same for the ML-only and hybrid comparisons (allowing the final count to differ by at most rounding one participant).

### Secondary metrics

- AUROC: how well the model ranks positive above negative participants.
- AUPRC / average precision: precision-recall performance, important with class imbalance; always report outcome prevalence.
- Precision, recall/sensitivity, specificity and F1 at any stated classification threshold.
- Brier score and reliability/calibration plot.
- Positive cases captured and false referrals at each screening capacity.
- Temporal degradation from historical validation to 2021–2023 test.
- Performance across prespecified demographic subgroups where sample counts are adequate.
- Ontology rule coverage, missing-criteria rate, and ML–rule disagreement breakdown.

### Uncertainty

- Use paired bootstrap resampling on held-out test participants for primary differences, reporting 95% confidence intervals.
- Separately report variability across the five training seeds. Do not confuse seed variability with population sampling uncertainty.
- Report positive counts and avoid strong subgroup claims when the number of positive outcomes is small.
- Avoid declaring a “win” based only on a tiny point-estimate change without uncertainty and practical magnitude.

## 5. Application and visual showcase

Build the demo with **Streamlit + Plotly + RDFLib + NetworkX**. The dashboard must be attractive enough to demonstrate and honest enough not to imply clinical deployment.

### Pages

1. **Overview:** question, workflow, dataset periods, target definition, and clearly marked “research prototype—not for clinical use” notice.
2. **Research Results:** AUROC/AUPRC/Brier comparison; model-versus-hybrid performance; fixed-capacity sensitivity chart; confidence intervals; prevalence and test sample count. Values must load from generated artifacts, never be hardcoded.
3. **Patient Case Explorer:** form to enter age, demographics, BMI, waist, blood pressure, smoking, activity, hypertension history, and cardiovascular history. Show raw ML risk score, ontology-derived eligibility/criteria, hybrid ranking score, model–guideline agreement, and a traceable rule explanation. State that this is a research demonstration, not medical advice or a diagnostic tool.
4. **Ontology Explorer:** interactive graph of classes, properties, source guideline and rule relationships; node detail panel with source, description and input requirements.
5. **Data & Methods:** feature list, target/exclusion policy, temporal split, validation protocol, missingness notes, metrics, and limitations.

### Visuals required

- End-to-end system architecture.
- Ontology graph.
- ROC and precision-recall curves.
- Calibration plot.
- Sensitivity at 10%, 20% and 30% screening budgets.
- Paired comparison/uncertainty plot for the primary metric.
- Missingness and cohort flow chart.

No chart may show invented or placeholder performance as real evidence. If artifacts do not exist yet, show an explicit “Run the notebook to populate results” message.

## 6. Repository structure

```text
clinontoscreen/
├── README.md
├── plan.md
├── METHODOLOGY.md
├── DATA_DICTIONARY.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── CITATION.cff
├── requirements.txt
├── .gitignore
├── app.py
├── ontology/
│   └── diabetes_screening.ttl
├── notebooks/
│   └── 01_nhanes_ontology_ml.ipynb
├── src/
│   ├── __init__.py
│   └── clinontoscreen/
│       ├── __init__.py
│       ├── data.py
│       ├── ontology.py
│       ├── modeling.py
│       └── reporting.py
├── docs/
│   ├── PAPER_OUTLINE.md
│   ├── EXPERIMENTS.md
│   ├── FIGURES.md
│   └── DECISIONS.md
├── tests/
│   ├── test_ontology.py
│   ├── test_data_contract.py
│   └── test_artifacts.py
└── artifacts/
    └── .gitkeep
```

Generated raw participant files and large model artifacts should not be committed. The repository should contain code, ontology, documentation, notebook, tests, and small non-sensitive metadata. Never commit raw NHANES rows, copied participant-level prediction files, or credentials. Keep generated test predictions locally unless a disclosure and repository review confirms that sharing them is appropriate.

## 7. Commit-by-commit implementation plan

Use one coherent commit for each significant, testable change. Do not accumulate the entire project and make one enormous final commit. Use imperative commit messages and run relevant checks before each commit.

| Commit | Scope | Required checks | Documentation updated |
|---|---|---|---|
| `chore: initialize ClinOntoScreen repository` | Directory structure, requirements, `.gitignore`, basic project metadata | Import smoke test; clean repository status | `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md` |
| `docs: define study protocol and outcome` | Research questions, hypotheses, cohort, target, split, metrics, limitations | Check that target and features do not overlap | `plan.md`, `METHODOLOGY.md`, `docs/DECISIONS.md`, `docs/PAPER_OUTLINE.md` |
| `feat: add NHANES data downloader and harmonizer` | CDC XPT download, cycle-specific loading, merge, canonical fields, data checks | Unit tests for merges, required fields and special missing codes | `DATA_DICTIONARY.md`, `README.md` |
| `feat: add clinical screening ontology` | OWL/RDF terms, source-linked rule definitions, Python evaluator and explanations | Ontology parses; each executable rule has source and tests | `ontology/diabetes_screening.ttl`, `METHODOLOGY.md`, `docs/DECISIONS.md` |
| `feat: implement reproducible ML pipelines` | Imputation/encoding pipelines, logistic regression, XGBoost, model bundle | No leakage; preprocessing fit only on historical development data | `METHODOLOGY.md`, notebook |
| `feat: add temporal evaluation and confidence intervals` | Fixed-capacity metrics, paired bootstrap, seeds, ablations, calibration and subgroup reports | Deterministic run; metric unit tests; untouched test set | `docs/EXPERIMENTS.md`, `docs/FIGURES.md`, `METHODOLOGY.md` |
| `feat: add Kaggle and Colab training notebook` | Self-contained training workflow, artifact export and run instructions | Restart kernel/run top-to-bottom when network and runtime are available | `notebooks/01_nhanes_ontology_ml.ipynb`, `README.md` |
| `feat: build interactive Streamlit research dashboard` | Results, case explorer, ontology graph, methods/limitations views | App launches without artifacts; then test with generated artifacts | `README.md`, screenshots in `docs/` after real run |
| `test: add end-to-end research contract checks` | Data contract, leakage assertions, ontology checks, artifact checks | Run full test suite | `CONTRIBUTING.md`, `docs/EXPERIMENTS.md` |
| `docs: prepare reproducible paper materials` | Final data-flow diagram, methods, result tables and paper draft templates | Regenerate every reported number from artifact files | All applicable `.md`, `CITATION.cff`, paper files |

After every commit:

1. Run the relevant unit tests and formatting/lint checks.
2. Update the changelog with a concise entry.
3. Update README or the appropriate documentation if behaviour, setup, outputs, variables, or findings changed.
4. Inspect `git diff --check`, `git status`, and the staged diff.
5. Commit only the intended files. Do not commit data or generated large artifacts accidentally.

Do not edit empirical claims in the paper without regenerating the result artifacts from the notebook.

## 8. Notebook requirements for Kaggle / Colab

The training notebook is the reproducible route to train models and populate the dashboard. It must:

- Install/import dependencies in a single setup cell and print versions.
- Work in Kaggle and Google Colab with a CPU runtime; no GPU is required for the tabular models.
- Download public NHANES XPT files directly from official CDC URLs.
- Cache raw downloads within the runtime and optionally Google Drive; do not require paid storage.
- Show cohort counts, positive counts, missingness, feature distributions and the temporal split before training.
- Implement the ontology rule-derived features and confirm that HbA1c and diabetes questionnaire predictors are absent.
- Train two model families and their ontology-enhanced versions over five fixed seeds.
- Tune only on historical data and evaluate the locked newer cycle at the end.
- Produce all metrics, tables and plots from actual computations.
- Save `model_bundle.joblib`, `research_results.json`, `test_predictions.csv` (local/private unless intentionally approved for release), `feature_manifest.json`, and PNG figures in `artifacts/`.
- Display links/instructions for downloading artifacts from Kaggle/Colab.
- Record dataset URLs, codebook access date, package versions, seeds, feature lists and a run timestamp in metadata.

After the GitHub repository exists, document how to open the notebook from the repository in Colab or Kaggle. Do not commit a GitHub URL that has not been created.

## 9. Documentation rules

### README.md

Must include project overview, research question, ethical/clinical disclaimer, architecture diagram, data sources and access instructions, notebook run steps, local dashboard setup, artifact outputs, test commands, limitations, and citation links. It must clearly say no empirical result is claimed until the notebook has been run.

### METHODOLOGY.md

Source of target, cohort exclusions, feature definitions, ontology scope, missing-data strategy, model pipeline, temporal split, model selection, metrics and confidence intervals.

### DATA_DICTIONARY.md

For each canonical feature: meaning, source NHANES variable, source file, coding, missing values, preprocessing, inclusion/exclusion reason, and whether it is used by ML, ontology, cohort filtering, or evaluation only.

### docs/EXPERIMENTS.md

Prespecified comparisons, hypotheses, metrics, screening capacities, seeds, bootstrap method, ablations, subgroup safeguards, and the exact final-test policy.

### docs/DECISIONS.md

A dated record of major design choices and why they were made. Changes to target, cohort, features, ontology rules or primary metrics must be recorded before viewing final test results, not retroactively rationalized.

### docs/FIGURES.md

List every paper figure/table, its source artifact, generating notebook section, and caption/interpretation. Figures must always be reproducible from committed code.

### CHANGELOG.md

Every significant code or documentation change gets an entry, ideally in the same commit.

## 10. Paper plan

1. **Abstract:** question, data, methods, key measured differences and limitations.
2. **Introduction:** the need for interpretable, clinically grounded screening support; precise gap after comparing the closest papers.
3. **Related work:** NHANES diabetes/dysglycemia prediction, clinical ontology integration, guideline-based screening, temporal evaluation and selective prediction.
4. **Data:** NHANES cycle differences, variables, cohort flow, target and missingness.
5. **Ontology:** concepts, source mappings, executable rules, rule coverage and limitations.
6. **Methods:** baselines, augmented models, hybrid policy, tuning, temporal test, metrics and uncertainty.
7. **Results:** cohort description, overall metrics, fixed-capacity screening results, calibration, temporal comparison, ablations, subgroup results, disagreement analysis.
8. **Discussion:** what the results support and do not support; relation to closest work; implications for research screening prioritization.
9. **Limitations:** single survey system, temporal/sampling differences, self-reported exclusions, single HbA1c measurement, unavailable clinical factors, missingness, survey weighting, limited ontology scope, no clinical validation.
10. **Reproducibility and ethics:** public sources, versioned ontology, code, model artifact policy, intended use, no clinical deployment claim.

## 11. Risks and their mitigations

| Risk | Mitigation |
|---|---|
| Ontology does not improve AUROC/AUPRC | Evaluate the prespecified screening-policy outcome, explanation/traceability, and failure cases; report honestly. |
| Generic engineering explains the gain | Include the generic engineered-feature control and distinguish predictive gain from ontology-specific capabilities. |
| Temporal cycle differences distort results | Report as a later-cycle evaluation, document known survey changes, and avoid causal claims about why the distribution changed. |
| Target/feature leakage | Explicit deny-list in notebook and automated tests: `LBXGH`, `DIQ010`, `DIQ160`, glucose variables, glycemic labs and treatment variables cannot be model predictors. |
| Small positive subgroup | Report counts and confidence intervals; avoid overclaiming subgroup findings. |
| Missing source variables across cycles | Optional-file registry, missingness report and same canonical schema. Do not silently drop variables. |
| ADA guidelines are encoded incompletely | List the exact rule subset, source version, unavailable criteria and any approximations. |
| Race/ethnicity criteria introduce fairness concerns | Document rationale, provide ablation without the criterion, and report subgroup results only when adequately supported. |
| Dashboard is mistaken for clinical software | Persistent visible disclaimer; no diagnostic language; use synthetic form inputs only for demonstration and never persist entered data. |
| Results are not reproducible | Fixed seeds, saved environment versions, versioned code/ontology, generated result JSON, and one-command checks. |

## 12. Definition of done

The project is complete only when all items below are true:

- [ ] Full public-data pipeline runs from download to canonical dataset in Kaggle or Colab.
- [ ] Outcome definition, cohort flow and feature exclusions are recorded and checked.
- [ ] Versioned OWL/RDF ontology loads successfully and rules return traceable explanations.
- [ ] Two ML families and ontology-enhanced variants train using historical data only.
- [ ] Temporal evaluation on 2021–2023 runs without using that test set for model selection.
- [ ] Primary 20% screening-capacity result, 10%/30% sensitivity analyses and uncertainty are generated.
- [ ] Generic feature-engineering and confidence-only baselines are included.
- [ ] All charts/tables in the paper are generated from result artifacts.
- [ ] Streamlit pages work with real artifacts; ontology graph and rule explanations work without model artifacts.
- [ ] Unit tests and leakage checks pass.
- [ ] README, methodology, data dictionary, experiments, decisions, figures, changelog and citation metadata are current.
- [ ] Commit history reflects significant stages; no participant-level data or accidental large artifacts are committed.
- [ ] The paper's novelty claim is based on a documented comparison with the closest current papers.
- [ ] No claim of clinical validity, causal inference, or guaranteed publication is made.

## 13. References and source documentation

- CDC/NCHS, NHANES 2021–2023 data and documentation: <https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023>
- CDC/NCHS, NHANES 2017–March 2020 pre-pandemic data and documentation: <https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2017-2020>
- CDC/NCHS, 2021–2023 DEMO_L codebook: <https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.htm>
- CDC/NCHS, 2021–2023 DIQ_L codebook: <https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DIQ_L.htm>
- CDC/NCHS, 2021–2023 GHB_L codebook: <https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GHB_L.htm>
- CDC/NCHS, 2017–March 2020 P_DEMO codebook: <https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.htm>
- CDC/NCHS, 2017–March 2020 P_DIQ codebook: <https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DIQ.htm>
- CDC/NCHS, 2017–March 2020 P_GHB codebook: <https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_GHB.htm>
- American Diabetes Association, *Diagnosis and Classification of Diabetes: Standards of Care in Diabetes—2026*: <https://diabetesjournals.org/care/article/49/Supplement_1/S27/163926/2-Diagnosis-and-Classification-of-Diabetes>

**Important:** before submission, refresh the literature search, read the closest papers in full, and cite the exact source of each operationalized clinical rule. This plan specifies a research design; it does not claim that the planned method will necessarily improve predictive performance or be accepted for publication.
