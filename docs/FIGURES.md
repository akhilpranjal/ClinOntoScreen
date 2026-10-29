# Figures and Tables Register

Every empirical figure must be generated from saved artifacts by the notebook. No manually fabricated metric values are allowed.

| ID | Planned figure/table | Input artifact | Purpose |
|---|---|---|---|
| Fig. 1 | Architecture diagram | `plan.md` / ontology + code structure | Show data, ML, rule engine, policy and dashboard |
| Fig. 2 | Cohort flow and target prevalence by cycle | `research_results.json` and cohort metadata | Make exclusions and label counts transparent |
| Fig. 3 | Ontology graph visualization | `ontology/diabetes_screening.ttl` | Show concept, rule, source and variable links |
| Fig. 4 | AUROC / precision-recall curves | `test_predictions.csv` | Compare raw and ontology-enhanced model rankings |
| Fig. 5 | Calibration plot | `test_predictions.csv` | Show probability reliability |
| Fig. 6 | Sensitivity at 10%, 20%, 30% capacity | `research_results.json` | Main screening-policy result |
| Fig. 7 | Paired bootstrap CI for primary effect | `research_results.json` | Quantify uncertainty in the hybrid-minus-baseline difference |
| Fig. 8 | E1 low-data learning curve | `research_results.json → e1` | Test whether guideline features help when training data are scarce |
| Fig. 9 | E2 missing-input stress test | `research_results.json → e2` | Test discrimination/capacity stability when inputs are masked |
| Fig. 10 | E3 model-family deltas with paired CIs | `research_results.json → paired_effects` | Compare knowledge-layer effect for logistic regression vs XGBoost |
| Table 1 | Cohort and missingness summary | `research_results.json` | Describe test cohort without overclaiming representativeness |
| Table 2 | Main ML metrics | `research_results.json` | Discrimination and calibration |
| Table 3 | Fixed-capacity metrics | `research_results.json` | Cases found, sensitivity, precision and referrals |
| Table 4 | Ablation and subgroup analysis | `research_results.json` | Compare the full rule with the higher-risk ethnicity-flag ablation; state that this is not a fully race-blind model |
| Table 5 | Capacity ceiling and lift | `research_results.json → capacity_metrics` | Prevalence ceiling, fraction of ceiling, PPV and lift at 10/20/30% |
| Table 6 | Published CDC/ADA risk-test baseline | `published_score_baseline.csv` | Published-knowledge comparison (point score; Brier undefined) |
| Table 7 | H3 disagreement vs confidence review | `research_results.json → review_summary` | Equal-size comparison of the two review strategies |
| Table 8 | Smallest detectable differences (MDE) | `research_results.json → mde` | Pre-test noise floor from historical validation |
