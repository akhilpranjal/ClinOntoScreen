from pathlib import Path
import pandas as pd
import numpy as np
from src.clinontoscreen.ontology import load_ontology, validate_ontology, derive_ontology_features, explain_case, graph_summary

ROOT = Path(__file__).resolve().parents[1]


def test_ontology_parses_and_required_rules_have_sources():
    graph = load_ontology(ROOT / "ontology" / "diabetes_screening.ttl")
    assert len(graph) > 20
    assert validate_ontology(graph) == []
    nodes, edges = graph_summary(graph)
    assert len(nodes) > 20
    assert len(edges) > 20  # Regression test: graph edges must not depend on RDF iteration order.


def test_age_based_eligibility_and_missingness():
    df = pd.DataFrame([
        {"age_years": 40, "race_ethnicity_code": 3, "bmi": 22, "systolic_bp_mean": 110, "diastolic_bp_mean": 70,
         "hypertension_history": 2, "heart_failure_history": 2, "coronary_heart_disease_history": 2,
         "angina_history": 2, "heart_attack_history": 2, "stroke_history": 2,
         "vigorous_work_activity": 1, "moderate_work_activity": 2, "vigorous_recreation_activity": 2, "moderate_recreation_activity": 2},
        {"age_years": np.nan, "race_ethnicity_code": np.nan, "bmi": np.nan},
    ])
    out = derive_ontology_features(df)
    assert out.loc[0, "onto_screening_eligible"] == 1.0
    assert np.isnan(out.loc[1, "onto_screening_eligible"])


def test_young_adult_bmi_plus_risk_rule():
    base = {
        "age_years": 28, "race_ethnicity_code": 3, "bmi": 29, "systolic_bp_mean": 145, "diastolic_bp_mean": 90,
        "hypertension_history": 1, "heart_failure_history": 2, "coronary_heart_disease_history": 2,
        "angina_history": 2, "heart_attack_history": 2, "stroke_history": 2,
        "vigorous_work_activity": 2, "moderate_work_activity": 2, "vigorous_recreation_activity": 2, "moderate_recreation_activity": 2,
    }
    out = derive_ontology_features(pd.DataFrame([base]))
    assert out.loc[0, "onto_bmi_threshold_met"] == 1.0
    assert out.loc[0, "onto_hypertension_risk"] == 1.0
    assert out.loc[0, "onto_screening_eligible"] == 1.0
    assert "BMI criterion met" in " ".join(explain_case(base)["reasons"])


def test_asian_bmi_threshold_is_lower():
    df = pd.DataFrame([
        {"age_years": 27, "race_ethnicity_code": 6, "bmi": 24, "systolic_bp_mean": 110, "diastolic_bp_mean": 70,
         "hypertension_history": 2, "heart_failure_history": 2, "coronary_heart_disease_history": 2,
         "angina_history": 2, "heart_attack_history": 2, "stroke_history": 2,
         "vigorous_work_activity": 1, "moderate_work_activity": 2, "vigorous_recreation_activity": 2, "moderate_recreation_activity": 2},
    ])
    assert derive_ontology_features(df).loc[0, "onto_bmi_threshold_met"] == 1.0


def test_hypertension_treatment_counts_as_risk_factor():
    df = pd.DataFrame([{
        "age_years": 29, "race_ethnicity_code": 3, "bmi": 28,
        "systolic_bp_mean": np.nan, "diastolic_bp_mean": np.nan,
        "hypertension_history": 2, "hypertension_treatment": 1,
        "heart_failure_history": 2, "coronary_heart_disease_history": 2,
        "angina_history": 2, "heart_attack_history": 2, "stroke_history": 2,
        "vigorous_work_activity": 1, "moderate_work_activity": 2,
        "vigorous_recreation_activity": 2, "moderate_recreation_activity": 2,
    }])
    out = derive_ontology_features(df)
    assert out.loc[0, "onto_hypertension_risk"] == 1.0
    assert out.loc[0, "onto_screening_eligible"] == 1.0
