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
| Table 1 | Cohort and missingness summary | `research_results.json` | Describe test cohort without overclaiming representativeness |
| Table 2 | Main ML metrics | `research_results.json` | Discrimination and calibration |
| Table 3 | Fixed-capacity metrics | `research_results.json` | Cases found, sensitivity, precision and referrals |
| Table 4 | Ablation and subgroup analysis | `research_results.json` | Attribute benefits/harms and show limitations |
