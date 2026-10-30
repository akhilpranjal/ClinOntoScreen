"""RDF/OWL loading, ontology-backed rule features, and traceable case explanations."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from functools import lru_cache
import numpy as np
import pandas as pd
from rdflib import Graph, Namespace, RDF, RDFS

EX = Namespace("https://w3id.org/clinontoscreen/ontology#")
DEFAULT_ONTOLOGY = Path(__file__).resolve().parents[2] / "ontology" / "diabetes_screening.ttl"
ONTOLOGY_FEATURES = [
    "onto_age_based_screening", "onto_bmi_threshold_met", "onto_hypertension_risk",
    "onto_cvd_history", "onto_physical_inactivity", "onto_higher_risk_ethnicity",
    "onto_additional_risk_factor_count", "onto_screening_eligible",
    "onto_criteria_observed_count", "onto_criteria_missing_count", "onto_rule_priority_score",
]


def load_ontology(path: str | Path | None = None) -> Graph:
    candidate = Path(path) if path is not None else DEFAULT_ONTOLOGY
    if not candidate.exists():
        # When installed as a package from an editable project, repository root may be the parent.
        alternate = Path.cwd() / "ontology" / "diabetes_screening.ttl"
        if alternate.exists():
            candidate = alternate
        else:
            raise FileNotFoundError(f"Ontology file not found: {candidate}. Expected ontology/diabetes_screening.ttl")
    graph = Graph()
    graph.parse(candidate, format="turtle")
    return graph


@lru_cache(maxsize=4)
def get_rule_config(path_str: str | None = None) -> dict[str, Any]:
    """Read numeric thresholds and code mappings from the RDF/OWL graph, not from duplicated code constants."""
    graph = load_ontology(path_str)

    def literal_float(subject, predicate, default):
        values = list(graph.objects(subject, predicate))
        return float(values[0]) if values else float(default)

    def literal_codes(subject, predicate, default):
        values = list(graph.objects(subject, predicate))
        raw = str(values[0]) if values else default
        return [int(item.strip()) for item in raw.split(",") if item.strip()]

    return {
        "age_threshold": literal_float(EX.Age35Criterion, EX.thresholdValue, 35),
        "bmi_general_threshold": literal_float(EX.BMIOverweightGeneralCriterion, EX.thresholdValue, 25),
        "bmi_asian_threshold": literal_float(EX.BMIOverweightAsianCriterion, EX.thresholdValue, 23),
        "systolic_threshold": literal_float(EX.HypertensionRiskCriterion, EX.systolicThreshold, 130),
        "diastolic_threshold": literal_float(EX.HypertensionRiskCriterion, EX.diastolicThreshold, 80),
        "higher_risk_ethnicity_codes": literal_codes(EX.HigherRiskEthnicityCriterion, EX.categoryCodes, "1,2,4,6"),
    }


def validate_ontology(graph: Graph) -> list[str]:
    errors: list[str] = []
    required = [EX.AgeBasedScreeningRule, EX.YoungerAdultRiskBasedRule, EX.HbA1cTargetDefinition]
    for item in required:
        if (item, RDF.type, None) not in graph:
            errors.append(f"Missing required ontology individual: {item}")
    for rule in (EX.AgeBasedScreeningRule, EX.YoungerAdultRiskBasedRule):
        if not list(graph.objects(rule, EX.hasSource)):
            errors.append(f"Rule has no source: {rule}")
        if not list(graph.objects(rule, EX.ruleExpression)):
            errors.append(f"Rule has no documented expression: {rule}")
    return errors


def _num(frame: pd.DataFrame, col: str) -> pd.Series:
    if col not in frame:
        return pd.Series(np.nan, index=frame.index, dtype="float64")
    return pd.to_numeric(frame[col], errors="coerce")


def _yes_no_flag(frame: pd.DataFrame, col: str) -> pd.Series:
    """NHANES Yes=1/No=2 to float flag; invalid/missing codes stay NaN."""
    values = _num(frame, col)
    return values.map({1.0: 1.0, 2.0: 0.0}).astype("float64")


def _any_flag(flags: list[pd.Series], index: pd.Index) -> pd.Series:
    if not flags:
        return pd.Series(np.nan, index=index, dtype="float64")
    values = pd.concat(flags, axis=1)
    out = pd.Series(np.nan, index=index, dtype="float64")
    any_yes = values.eq(1).any(axis=1)
    any_known = values.notna().any(axis=1)
    out.loc[any_yes] = 1.0
    out.loc[~any_yes & any_known] = 0.0
    return out


def derive_ontology_features(frame: pd.DataFrame, include_ethnicity: bool = True) -> pd.DataFrame:
    """Derive rule features from canonical non-glycemic inputs. No outcome columns are read."""
    out = frame.copy()
    cfg = get_rule_config()
    age = _num(out, "age_years")
    bmi = _num(out, "bmi")
    race = _num(out, "race_ethnicity_code")
    asian = race.eq(6)
    cutoff = pd.Series(cfg["bmi_general_threshold"], index=out.index)
    cutoff.loc[asian] = cfg["bmi_asian_threshold"]
    bmi_flag = pd.Series(np.nan, index=out.index, dtype="float64")
    bmi_observed = bmi.notna() & race.notna()
    bmi_flag.loc[bmi_observed] = (bmi.loc[bmi_observed] >= cutoff.loc[bmi_observed]).astype(float)

    age_flag = pd.Series(np.nan, index=out.index, dtype="float64")
    age_flag.loc[age.notna()] = (age.loc[age.notna()] >= cfg["age_threshold"]).astype(float)

    sbp = _num(out, "systolic_bp_mean")
    dbp = _num(out, "diastolic_bp_mean")
    measured_bp = pd.Series(np.nan, index=out.index, dtype="float64")
    bp_observed = sbp.notna() | dbp.notna()
    high_bp_measure = (sbp >= cfg["systolic_threshold"]) | (dbp >= cfg["diastolic_threshold"])
    measured_bp.loc[bp_observed] = high_bp_measure.loc[bp_observed].astype(float)
    hypertension = _any_flag([measured_bp, _yes_no_flag(out, "hypertension_history"), _yes_no_flag(out, "hypertension_treatment")], out.index)

    cvd_cols = ["heart_failure_history", "coronary_heart_disease_history", "angina_history", "heart_attack_history", "stroke_history"]
    cvd = _any_flag([_yes_no_flag(out, col) for col in cvd_cols], out.index)

    leisure = _num(out, "leisure_activity_minutes")
    sedentary = _num(out, "sedentary_minutes")
    if leisure.notna().any() or sedentary.notna().any():
        inactivity = pd.Series(np.nan, index=out.index, dtype="float64")
        observed = leisure.notna() | sedentary.notna()
        inactivity.loc[observed] = ((leisure.fillna(0) <= 0) & (sedentary.fillna(0) >= 480)).loc[observed].astype(float)
    else:
        # Backward-compatible interpretation for older serialized examples.
        activity_cols = ["vigorous_work_activity", "moderate_work_activity", "vigorous_recreation_activity", "moderate_recreation_activity"]
        activity = pd.concat([_yes_no_flag(out, col) for col in activity_cols], axis=1)
        inactivity = pd.Series(np.nan, index=out.index, dtype="float64")
        any_active = activity.eq(1).any(axis=1)
        all_no = activity.notna().all(axis=1) & activity.eq(0).all(axis=1)
        inactivity.loc[any_active] = 0.0
        inactivity.loc[all_no] = 1.0

    ethnicity = pd.Series(np.nan, index=out.index, dtype="float64")
    if include_ethnicity:
        ethnicity.loc[race.notna()] = race.loc[race.notna()].isin(cfg["higher_risk_ethnicity_codes"]).astype(float)
    else:
        # Constant sentinel for the model feature schema; the criterion is excluded from
        # eligibility, additional-risk counts, and the priority denominator in this ablation.
        ethnicity = pd.Series(0.0, index=out.index, dtype="float64")

    risk_columns = [hypertension, cvd, inactivity]
    if include_ethnicity:
        risk_columns.append(ethnicity)
    risk_flags = pd.concat(risk_columns, axis=1)
    risk_count = risk_flags.fillna(0).sum(axis=1).astype(float)
    known_count = risk_flags.notna().sum(axis=1)
    risk_count.loc[known_count == 0] = np.nan

    eligible = pd.Series(np.nan, index=out.index, dtype="float64")
    eligible.loc[age >= cfg["age_threshold"]] = 1.0
    younger_known = age.notna() & (age < cfg["age_threshold"]) & bmi_flag.notna()
    # If BMI is below threshold, the encoded younger-adult rule does not qualify even if risk data are missing.
    younger_bmi_no = younger_known & bmi_flag.eq(0)
    eligible.loc[younger_bmi_no] = 0.0
    younger_bmi_yes = younger_known & bmi_flag.eq(1)
    has_risk = risk_count >= 1
    eligible.loc[younger_bmi_yes & has_risk] = 1.0
    eligible.loc[younger_bmi_yes & risk_count.eq(0)] = 0.0

    criteria_columns = [age_flag, bmi_flag, hypertension, cvd, inactivity]
    if include_ethnicity:
        criteria_columns.append(ethnicity)
    criteria = pd.concat(criteria_columns, axis=1)
    criteria_observed = criteria.notna().sum(axis=1).astype(float)
    criteria_missing = criteria.isna().sum(axis=1).astype(float)
    # This is a study-defined ordinal score for ranking, not a calibrated clinical risk probability.
    priority = criteria.fillna(0).sum(axis=1).astype(float) / criteria_observed.replace(0, np.nan)

    out["onto_age_based_screening"] = age_flag
    out["onto_bmi_threshold_met"] = bmi_flag
    out["onto_hypertension_risk"] = hypertension
    out["onto_cvd_history"] = cvd
    out["onto_physical_inactivity"] = inactivity
    out["onto_higher_risk_ethnicity"] = ethnicity
    out["onto_additional_risk_factor_count"] = risk_count
    out["onto_screening_eligible"] = eligible
    out["onto_criteria_observed_count"] = criteria_observed
    out["onto_criteria_missing_count"] = criteria_missing
    out["onto_rule_priority_score"] = priority.fillna(0.0)
    return out


def explain_case(row: dict[str, Any] | pd.Series) -> dict[str, Any]:
    """Return a plain-language, traceable screening explanation for one canonical case."""
    frame = pd.DataFrame([dict(row)])
    derived = derive_ontology_features(frame).iloc[0]
    age = pd.to_numeric(pd.Series([row.get("age_years")]), errors="coerce").iloc[0]
    bmi = pd.to_numeric(pd.Series([row.get("bmi")]), errors="coerce").iloc[0]
    race = pd.to_numeric(pd.Series([row.get("race_ethnicity_code")]), errors="coerce").iloc[0]
    cfg = get_rule_config()
    cutoff = cfg["bmi_asian_threshold"] if pd.notna(race) and race == 6 else cfg["bmi_general_threshold"]
    reasons: list[str] = []
    unknowns: list[str] = []
    if pd.notna(age) and age >= cfg["age_threshold"]:
        reasons.append("Age-based screening criterion met (age 35 or older).")
    elif pd.isna(age):
        unknowns.append("Age is missing, so age-based eligibility cannot be assessed.")
    else:
        if pd.isna(bmi):
            unknowns.append("BMI is missing, so the younger-adult BMI criterion cannot be assessed.")
        elif bmi >= cutoff:
            reasons.append(f"BMI criterion met (BMI {bmi:.1f} kg/m²; encoded threshold {cutoff:.0f} kg/m²).")
            if derived["onto_hypertension_risk"] == 1:
                reasons.append("Hypertension risk factor recorded.")
            if derived["onto_cvd_history"] == 1:
                reasons.append("Selected cardiovascular history risk factor recorded.")
            if derived["onto_physical_inactivity"] == 1:
                reasons.append("Physical-inactivity criterion recorded from available activity responses.")
            if derived["onto_higher_risk_ethnicity"] == 1:
                reasons.append("A mapped higher-risk race/ethnicity criterion is present; this is a guideline encoding, not a causal interpretation.")
            if derived["onto_additional_risk_factor_count"] >= 1:
                reasons.append("At least one encoded additional risk factor is present.")
            elif pd.isna(derived["onto_additional_risk_factor_count"]):
                unknowns.append("Additional risk-factor data are incomplete.")
            else:
                reasons.append("No encoded additional risk factor was found in the available fields.")
        else:
            reasons.append(f"BMI is below the encoded younger-adult threshold ({cutoff:.0f} kg/m²).")
    eligible = derived["onto_screening_eligible"]
    if pd.isna(eligible):
        status = "Cannot assess from available inputs"
    else:
        status = "Meets encoded screening eligibility" if eligible == 1 else "Does not meet the encoded rule subset"
    return {
        "status": status,
        "eligible": None if pd.isna(eligible) else bool(eligible),
        "rule_priority_score": float(derived["onto_rule_priority_score"]),
        "reasons": reasons,
        "unknowns": unknowns,
        "disclaimer": "Research demonstration only. Screening eligibility is not a diagnosis or a substitute for medical advice.",
    }


def graph_summary(graph: Graph | None = None, path: str | Path | None = None) -> tuple[list[dict[str, str]], list[tuple[str, str, str]]]:
    graph = graph or load_ontology(path)
    nodes: dict[str, dict[str, str]] = {}
    edges: list[tuple[str, str, str]] = []
    prefix = "https://w3id.org/clinontoscreen/ontology"
    # Build the full node set first. RDF graph iteration order is not guaranteed, so
    # creating edges while nodes are still being discovered silently drops valid edges.
    for subject, _, obj in graph:
        for term in (subject, obj):
            key = str(term)
            if key.startswith(prefix) and key not in nodes:
                label = next((str(v) for v in graph.objects(term, RDFS.label)), key.rsplit("#", 1)[-1])
                nodes[key] = {"id": key, "label": label[:48], "kind": "ontology"}
    for subject, predicate, obj in graph:
        skey, okey = str(subject), str(obj)
        if skey in nodes and okey in nodes:
            edge_label = str(predicate).rsplit("#", 1)[-1].rsplit("/", 1)[-1]
            edges.append((skey, edge_label, okey))
    return list(nodes.values()), edges
