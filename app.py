"""Streamlit research dashboard for ClinOntoScreen. Not for clinical use."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import networkx as nx
import joblib
from rdflib import URIRef, RDFS

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.clinontoscreen.data import RAW_FEATURES, NUMERIC_FEATURES, CATEGORICAL_FEATURES
from src.clinontoscreen.ontology import load_ontology, validate_ontology, derive_ontology_features, explain_case, graph_summary

ARTIFACT_DIR = ROOT / "artifacts"
BUNDLE_PATH = ARTIFACT_DIR / "model_bundle.joblib"
RESULTS_PATH = ARTIFACT_DIR / "research_results.json"

st.set_page_config(page_title="ClinOntoScreen", page_icon="🧬", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1500px;}
.small-muted {font-size: 0.88rem; color: #6b7280;}
</style>""", unsafe_allow_html=True)

@st.cache_resource
def load_bundle():
    if BUNDLE_PATH.exists():
        return joblib.load(BUNDLE_PATH)
    return None

@st.cache_data
def load_results():
    if RESULTS_PATH.exists():
        return json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    return None

@st.cache_resource
def get_graph():
    return load_ontology(ROOT / "ontology" / "diabetes_screening.ttl")


def probability_from_models(models, frame: pd.DataFrame) -> np.ndarray:
    if not isinstance(models, (list, tuple)):
        models = [models]
    outputs = [np.asarray(model.predict_proba(frame)[:, 1], dtype=float) for model in models]
    return np.mean(np.vstack(outputs), axis=0)


def fmt_num(value, digits=3):
    try:
        if value is None or not np.isfinite(float(value)):
            return "N/A"
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "N/A"


def render_overview(results):
    st.title("ClinOntoScreen")
    st.subheader("Medical knowledge + tabular ML for screening prioritization")
    st.write("A reproducible research prototype comparing Logistic Regression and XGBoost with an ontology-backed screening layer on NHANES data.")
    st.warning("Research prototype only. This is not a diagnostic tool, is not clinically validated, and must not be used to make medical decisions.")
    cols = st.columns(4)
    if results:
        cohort = results.get("cohort", {})
        metrics = results.get("metrics", {})
        test = results.get("temporal_test", {})
        cols[0].metric("Temporal test participants", f"{cohort.get('test_n', 'N/A'):,}" if isinstance(cohort.get("test_n"), (int, float)) else "N/A")
        cols[1].metric("Screen-positive prevalence", fmt_num(cohort.get("test_prevalence"), 3))
        primary = results.get("primary_effect", {})
        cols[2].metric("Hybrid sensitivity @ 20%", fmt_num(primary.get("hybrid_sensitivity"), 3))
        cols[3].metric("ML sensitivity @ 20%", fmt_num(primary.get("baseline_sensitivity"), 3))
    else:
        for c, label in zip(cols, ["Temporal test participants", "Positive prevalence", "Hybrid sensitivity @20%", "ML sensitivity @20%"]):
            c.metric(label, "Run notebook first")
    st.markdown("### How the system works")
    flow = go.Figure()
    nodes = [
        (0, 1, "NHANES XPT data"), (1.8, 1, "Leakage-safe cohort"),
        (3.6, 1.7, "Logistic Regression / XGBoost"), (3.6, 0.3, "OWL/RDF ontology + rules"),
        (5.7, 1, "ML vs ontology-assisted policy"), (7.8, 1, "Temporal evaluation + dashboard"),
    ]
    for x, y, label in nodes:
        flow.add_trace(go.Scatter(x=[x], y=[y], mode="markers+text", text=[label], textposition="bottom center", marker=dict(size=36, color="#dbeafe", line=dict(color="#2563eb", width=2)), hoverinfo="text", showlegend=False))
    edges = [(0, 1), (1.8, 3.6), (1.8, 3.6), (3.6, 5.7), (5.7, 7.8)]
    for x1, x2 in edges:
        flow.add_shape(type="line", x0=x1 + 0.2, y0=1, x1=x2 - 0.2, y1=1, line=dict(color="#64748b", width=2))
    flow.update_layout(height=300, margin=dict(l=20, r=20, t=10, b=80), xaxis=dict(visible=False, range=[-0.7, 8.6]), yaxis=dict(visible=False, range=[-0.15, 2.3]), showlegend=False)
    st.plotly_chart(flow, use_container_width=True)
    st.markdown("### Important interpretation")
    st.write("The primary outcome is HbA1c-defined screen-positive dysglycemia in participants who report neither prior diabetes nor prior prediabetes. It is based on one survey measurement, not a confirmed clinical diagnosis. The ontology encodes a documented subset of screening guidance; it does not diagnose disease.")


def render_results(results):
    st.title("Research results")
    if not results:
        st.info("No research results found. Run `notebooks/01_nhanes_ontology_ml.ipynb` from top to bottom to create `artifacts/research_results.json` and the model bundle.")
        return
    metrics = results.get("metrics", {})
    if metrics:
        rows = []
        for name, values in metrics.items():
            rows.append({"Model": name.replace("_", " ").title(), "AUROC": values.get("auroc_mean"), "AUPRC": values.get("auprc_mean"), "Brier": values.get("brier_mean"), "AUROC SD across seeds": values.get("auroc_sd")})
        table = pd.DataFrame(rows)
        for col in ["AUROC", "AUPRC", "Brier", "AUROC SD across seeds"]:
            table[col] = pd.to_numeric(table[col], errors="coerce")
        st.markdown("### Temporal test metrics")
        st.caption("All numbers below are read from generated result files. N/A means the corresponding value is not present in the run artifact.")
        st.dataframe(table.style.format({c: "{:.3f}" for c in table.columns if c != "Model"}, na_rep="N/A"), use_container_width=True, hide_index=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="AUROC", x=table["Model"], y=table["AUROC"].astype(float)))
        fig.add_trace(go.Bar(name="AUPRC", x=table["Model"], y=table["AUPRC"].astype(float)))
        fig.update_layout(barmode="group", yaxis_title="Score", yaxis_range=[0, 1], height=400)
        st.plotly_chart(fig, use_container_width=True)
    budgets = results.get("screening_budgets", [])
    if budgets:
        st.markdown("### Sensitivity at a fixed screening budget")
        bdf = pd.DataFrame(budgets)
        if {"policy", "capacity", "sensitivity"}.issubset(bdf.columns):
            bdf["budget_pct"] = 100 * bdf["capacity"].astype(float)
            fig = go.Figure()
            for policy, group in bdf.groupby("policy"):
                group = group.sort_values("budget_pct")
                fig.add_trace(go.Scatter(x=group["budget_pct"], y=group["sensitivity"], mode="lines+markers", name=policy))
            fig.update_layout(xaxis_title="Screening capacity (% of eligible cohort)", yaxis_title="Sensitivity / fraction of positive cases found", yaxis_range=[0, 1], height=430)
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(bdf, use_container_width=True, hide_index=True)
    effect = results.get("primary_effect", {})
    if effect:
        st.markdown("### Primary endpoint: hybrid minus ML-only sensitivity at 20% capacity")
        delta = effect.get("difference")
        low, high = effect.get("ci_low"), effect.get("ci_high")
        c1, c2, c3 = st.columns(3)
        c1.metric("Difference", fmt_num(delta), help="Hybrid sensitivity minus XGBoost-only sensitivity on the same temporal test set.")
        c2.metric("95% CI lower", fmt_num(low))
        c3.metric("95% CI upper", fmt_num(high))
        if low is not None and high is not None and low <= 0 <= high:
            st.info("The 95% interval includes zero. The result does not establish a clear improvement in the primary endpoint.")
        elif low is not None and low > 0:
            st.success("The interval is above zero for this run. Interpret the magnitude, assumptions, and limitations before claiming a research contribution.")
        elif high is not None and high < 0:
            st.warning("The estimated hybrid effect is below zero for this run. Report the negative result honestly.")
    ablation = results.get("race_ethnicity_ablation", {})
    ablation_effect = ablation.get("primary_effect_without_higher_risk_ethnicity_flag", {})
    if ablation_effect:
        st.markdown("### Sensitivity check: remove the higher-risk race/ethnicity rule flag")
        ab_cols = st.columns(3)
        ab_cols[0].metric("Full-rule hybrid sensitivity @20%", fmt_num(effect.get("hybrid_sensitivity"), 3))
        ab_cols[1].metric("Ablated hybrid sensitivity @20%", fmt_num(ablation_effect.get("hybrid_sensitivity"), 3))
        ab_cols[2].metric("Ablated hybrid minus ML", fmt_num(ablation_effect.get("difference"), 3))
        st.caption(ablation.get("interpretation", "Interpret this ablation within the limits of the encoded rules."))
    st.markdown("### Diagnostic plots from the notebook run")
    figure_names = ["roc_pr_curves.png", "calibration.png", "capacity_sensitivity.png", "primary_effect_ci.png"]
    present = [(name, ARTIFACT_DIR / name) for name in figure_names if (ARTIFACT_DIR / name).exists()]
    for name, path in present:
        st.markdown(f"**{name.replace('_', ' ').replace('.png', '').title()}**")
        st.image(str(path), use_container_width=True)
    if not present:
        st.caption("Notebook-generated figures will appear here after a complete run.")
    st.caption("Temporal-cycle differences can reflect survey design and measurement changes. These results do not establish clinical validity or causal explanations for distribution shift.")


def render_case_explorer(bundle):
    st.title("Interactive case explorer")
    st.write("Enter a research example to inspect the model score and the encoded guideline criteria. Entries stay in this session and are not stored by the app.")
    st.warning("Demonstration only. Do not enter real patient information. Output is not a diagnosis or medical advice.")
    with st.form("case_form"):
        c1, c2, c3 = st.columns(3)
        age = c1.slider("Age (years)", 18, 80, 32)
        sex_label = c2.selectbox("NHANES sex code", ["Female (2)", "Male (1)"])
        race_label = c3.selectbox("Race/ethnicity category", ["Non-Hispanic White (3)", "Mexican American (1)", "Other Hispanic (2)", "Non-Hispanic Black (4)", "Non-Hispanic Asian (6)", "Other / multiracial (7)"])
        c4, c5, c6 = st.columns(3)
        bmi = c4.slider("BMI (kg/m²)", 15.0, 55.0, 28.0, 0.5)
        waist = c5.slider("Waist circumference (cm)", 50.0, 170.0, 94.0, 1.0)
        pir = c6.slider("Income-to-poverty ratio", 0.0, 5.0, 2.0, 0.1)
        c7, c8, c9 = st.columns(3)
        sbp = c7.slider("Mean systolic BP (mmHg)", 80, 220, 125)
        dbp = c8.slider("Mean diastolic BP (mmHg)", 40, 140, 78)
        education = c9.selectbox("Education code", ["1: less than 9th grade", "2: 9–11th grade", "3: high school / GED", "4: some college / AA", "5: college graduate", "Missing / not applicable"])
        c10, c11, c12 = st.columns(3)
        hypertension = c10.selectbox("Ever told BP was high?", ["Yes", "No", "Unknown"])
        treatment = c11.selectbox("Taking BP medicine?", ["Yes", "No", "Unknown"])
        smoking = c12.selectbox("Ever smoked 100 cigarettes?", ["Yes", "No", "Unknown"])
        c13, c14, c15, c16 = st.columns(4)
        vwork = c13.selectbox("Vigorous work activity", ["Yes", "No", "Unknown"])
        mwork = c14.selectbox("Moderate work activity", ["Yes", "No", "Unknown"])
        vrec = c15.selectbox("Vigorous recreational activity", ["Yes", "No", "Unknown"])
        mrec = c16.selectbox("Moderate recreational activity", ["Yes", "No", "Unknown"])
        c17, c18, c19 = st.columns(3)
        hf = c17.selectbox("Heart failure history", ["Yes", "No", "Unknown"])
        chd = c18.selectbox("Coronary heart disease history", ["Yes", "No", "Unknown"])
        stroke = c19.selectbox("Stroke history", ["Yes", "No", "Unknown"])
        c20, c21 = st.columns(2)
        angina = c20.selectbox("Angina history", ["Yes", "No", "Unknown"])
        heart_attack = c21.selectbox("Heart attack history", ["Yes", "No", "Unknown"])
        submitted = st.form_submit_button("Evaluate research example", type="primary")

    if submitted:
        def code(value):
            return {"Yes": 1.0, "No": 2.0, "Unknown": np.nan}[value]
        race_code = int(race_label.split("(")[-1].split(")")[0])
        sex_code = 1 if sex_label.startswith("Male") else 2
        edu_code = int(education.split(":")[0]) if not education.startswith("Missing") else np.nan
        row = {
            "age_years": float(age), "sex_code": float(sex_code), "race_ethnicity_code": float(race_code),
            "education_code": edu_code, "income_poverty_ratio": float(pir), "bmi": float(bmi), "waist_cm": float(waist),
            "systolic_bp_mean": float(sbp), "diastolic_bp_mean": float(dbp),
            "hypertension_history": code(hypertension), "hypertension_treatment": code(treatment),
            "ever_smoked_100_cigs": code(smoking), "vigorous_work_activity": code(vwork),
            "moderate_work_activity": code(mwork), "vigorous_recreation_activity": code(vrec),
            "moderate_recreation_activity": code(mrec), "heart_failure_history": code(hf),
            "coronary_heart_disease_history": code(chd), "angina_history": code(angina),
            "heart_attack_history": code(heart_attack), "stroke_history": code(stroke),
        }
        raw = pd.DataFrame([row])[RAW_FEATURES]
        derived = derive_ontology_features(raw)
        explanation = explain_case(row)
        st.markdown("### Ontology assessment")
        st.write(f"**Status:** {explanation['status']}")
        cols = st.columns(3)
        cols[0].metric("Encoded screening eligibility", "Yes" if explanation["eligible"] is True else "No" if explanation["eligible"] is False else "Unknown")
        cols[1].metric("Rule-priority score", fmt_num(explanation["rule_priority_score"]))
        cols[2].metric("Additional risk factors", fmt_num(derived.iloc[0]["onto_additional_risk_factor_count"], 0))
        if explanation["reasons"]:
            st.markdown("**Rules and criteria recorded**")
            for reason in explanation["reasons"]:
                st.write(f"- {reason}")
        if explanation["unknowns"]:
            st.markdown("**Cannot assess**")
            for reason in explanation["unknowns"]:
                st.write(f"- {reason}")
        if bundle:
            raw_prob = probability_from_models(bundle["models"]["xgboost_raw"], raw[RAW_FEATURES])[0]
            augmented = derived[RAW_FEATURES + bundle["ontology_feature_columns"]]
            onto_prob = probability_from_models(bundle["models"]["xgboost_ontology"], augmented)[0]
            alpha = float(bundle.get("hybrid_alpha", 0.0))
            hybrid_score = raw_prob + alpha * float(derived.iloc[0]["onto_rule_priority_score"])
            cols = st.columns(3)
            cols[0].metric("XGBoost-only model score", f"{raw_prob:.1%}")
            cols[1].metric("XGBoost + ontology features", f"{onto_prob:.1%}")
            cols[2].metric("Hybrid priority score", fmt_num(hybrid_score), help="This is a ranking score, not a probability.")
            st.caption("Model scores estimate the research label under the training data definition. They are not a diagnosis. The hybrid priority score is not a calibrated probability.")
        else:
            st.info("ML scores will appear after the training notebook has created `artifacts/model_bundle.joblib`. Ontology rule evaluation works without a trained model.")


def render_ontology_explorer():
    st.title("Ontology explorer")
    st.write("The diagram is generated from the Turtle ontology file. Select a node to inspect its label, URI, comments and connected rules.")
    graph = get_graph()
    errors = validate_ontology(graph)
    if errors:
        st.error("Ontology validation findings: " + "; ".join(errors))
    nodes, edges = graph_summary(graph)
    G = nx.DiGraph()
    for node in nodes:
        G.add_node(node["id"], label=node["label"])
    for source, relation, target in edges:
        G.add_edge(source, target, label=relation)
    if not G.nodes:
        st.error("No ontology graph nodes were found.")
        return
    layout = nx.spring_layout(G, seed=7, k=0.7)
    edge_x, edge_y = [], []
    for s, t in G.edges():
        x0, y0 = layout[s]
        x1, y1 = layout[t]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=0.8, color="#94a3b8"), hoverinfo="none")
    node_x, node_y, node_text, node_ids = [], [], [], []
    label_lookup = {n["id"]: n["label"] for n in nodes}
    for node_id in G.nodes:
        x, y = layout[node_id]
        node_x.append(x); node_y.append(y); node_text.append(label_lookup.get(node_id, node_id)); node_ids.append(node_id)
    node_trace = go.Scatter(x=node_x, y=node_y, mode="markers+text", text=node_text, textposition="top center", customdata=node_ids, hovertemplate="%{text}<br>%{customdata}<extra></extra>", marker=dict(size=15, color="#bfdbfe", line=dict(width=1, color="#1d4ed8")))
    fig = go.Figure([edge_trace, node_trace])
    fig.update_layout(height=650, showlegend=False, margin=dict(l=10, r=10, t=20, b=20), xaxis=dict(visible=False), yaxis=dict(visible=False), hovermode="closest")
    st.plotly_chart(fig, use_container_width=True)
    node_choice = st.selectbox("Inspect ontology node", sorted(node_ids, key=lambda n: label_lookup.get(n, n)))
    from rdflib import RDFS
    node_uri = URIRef(node_choice)
    label = next((str(x) for x in graph.objects(node_uri, RDFS.label)), node_choice)
    comment = next((str(x) for x in graph.objects(node_uri, RDFS.comment)), "No comment is recorded for this node.")
    st.markdown(f"**{label}**")
    st.code(node_choice, language="text")
    st.write(comment)
    related = [(str(p).rsplit("#", 1)[-1], str(o)) for p, o in graph.predicate_objects(node_uri)]
    if related:
        st.dataframe(pd.DataFrame(related, columns=["Property", "Object"]), use_container_width=True, hide_index=True)


def render_methods():
    st.title("Data, methods and limitations")
    st.markdown("""
### Data periods
- Historical model development: NHANES 2017–March 2020 pre-pandemic release.
- Locked temporal test: NHANES August 2021–August 2023.

### Primary research outcome
HbA1c-defined screen-positive dysglycemia (`LBXGH >= 5.7%`) in adults who report neither prior diabetes nor prior prediabetes. A single HbA1c measurement is not a confirmed clinical diagnosis.

### Predictor exclusions
HbA1c, glucose, glycemic laboratory measurements, diabetes questionnaire answers, diabetes medication variables, participant identifiers and outcome fields are excluded from predictors.

### Main comparison
Logistic Regression and XGBoost with raw features versus raw + ontology-derived features; ontology-only screening-rule ranking; and an ML + ontology prioritization policy. The main policy metric is sensitivity at 20% screening capacity, with 10% and 30% as secondary capacities.

### Limitations
The ontology encodes a bounded subset of screening guidance. NHANES cycles use different survey designs and procedures. Results do not demonstrate clinical validity, causal mechanisms or guaranteed generalization to hospitals. Race/ethnicity-sensitive rules require careful interpretation and a sensitivity analysis.
""")
    st.markdown("### Official documentation")
    st.markdown("- [NHANES 2017–March 2020](https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2017-2020)\n- [NHANES 2021–2023](https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023)\n- [ADA Standards of Care 2026](https://diabetesjournals.org/care/article/49/Supplement_1/S27/163926/2-Diagnosis-and-Classification-of-Diabetes)")


results = load_results()
bundle = load_bundle()
with st.sidebar:
    st.title("ClinOntoScreen")
    page = st.radio("Navigate", ["Overview", "Research Results", "Patient Case Explorer", "Ontology Explorer", "Data & Methods"])
    st.divider()
    st.caption("Research-only prototype · not for clinical use")
if page == "Overview":
    render_overview(results)
elif page == "Research Results":
    render_results(results)
elif page == "Patient Case Explorer":
    render_case_explorer(bundle)
elif page == "Ontology Explorer":
    render_ontology_explorer()
else:
    render_methods()
