## Using the outputs

- `research_results.json` is the machine-readable record of every reported number, including
  the protocol commit/tag, hybrid alpha selection, paired bootstrap intervals, smallest
  detectable differences, E1/E2/E3 summaries, and the published CDC/ADA baseline.
- `test_predictions.csv` holds one row per 2021–2023 participant with the locked label, every
  model probability, the hybrid scores, the CDC/ADA point total, the ontology rule score, and
  the disagreement-review flag.
- `model_bundle.joblib` reloads the five-seed ensembles, best hyperparameters, hybrid alphas,
  and the ontology text used at training time:

```python
import joblib, pandas as pd
bundle = joblib.load('artifacts/model_bundle.joblib')
proba = bundle['models']['xgboost_ontology'][0].predict_proba(X[bundle['raw_features'] + bundle['ontology_features']])[:, 1]
```

- `capacity_metrics` in `research_results.json` is the fixed-budget view: for each policy and
  capacity it reports sensitivity, its prevalence ceiling, the fraction of that ceiling
  achieved, PPV, and lift over random referral.
- The ontology shipped with the run is `diabetes_screening.ttl`; the `sectionReference` field
  on each rule and outcome definition records which guideline section justifies it, and
  `operationalizationStatus` records which criteria are described but not computable from
  NHANES (family history, gestational diabetes, PCOS).
