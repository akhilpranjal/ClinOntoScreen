# ClinOntoScreen: NHANES + medical ontology + ML

This notebook downloads public NHANES XPT files, harmonizes the historical and later cycles, constructs a
leakage-safe cohort, loads the OWL/RDF screening ontology, trains Logistic Regression and XGBoost models,
evaluates ontology-assisted screening, and exports artifacts for the Streamlit dashboard and the paper.

**Primary question (H2, confirmatory):** at the same screening capacity, does an ontology-assisted ranking
identify more participants with HbA1c-defined screen-positive dysglycemia than XGBoost alone?

**Primary outcome:** among adults (18+) reporting neither prior diabetes nor prior prediabetes,
`LBXGH >= 5.7%`. This is a one-measurement research label, not a confirmed clinical diagnosis.

**Exploratory experiments (plan addendum §3):** E1 low-data learning curve, E2 missing-input stress test,
E3 model-family effect. They are reported whatever direction they take. H1, H3, H4 and all subgroup analyses
are exploratory; H2 is the only confirmatory test.

**Data periods:** NHANES 2017–March 2020 for training/validation; NHANES August 2021–August 2023 is kept as the
locked temporal test. CDC notes the later cycle has an updated sample design and modified
questionnaire/examination procedures, so results are temporal generalization, not evidence of a specific cause
of shift.

The notebook runs on CPU in Kaggle or Colab. Enable internet for data downloads. It does not use the temporal
test set for model selection. No performance result is assumed in advance.
