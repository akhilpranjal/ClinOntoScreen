# Ontology-Guided Screening for Undetected Dysglycemia: Evaluating Clinical Knowledge Integration Under Temporal Shift in NHANES

**Manuscript draft — ClinOntoScreen research prototype. All numbers in this manuscript are read from
`artifacts/research_results.json` produced by the protocol-tagged run (`protocol-v1`, commit `dc7fc37`;
full provenance in `research_results.json → protocol` and `docs/DECISIONS.md`).**

> Research prototype only. Not a diagnostic tool, not clinically validated, and not for medical decisions.

---

## Abstract

**Background.** Clinical guidelines and tabular machine learning are usually developed and evaluated
separately; few studies test whether encoding guideline content as executable, provenance-carrying
knowledge changes downstream screening decisions, and almost none do so under a temporal shift that
can break hard-coded thresholds.

**Methods.** We built ClinOntoScreen: an OWL/RDF ontology that encodes the ADA 2026 diabetes-screening
recommendations as executable rules with guideline-section references, coupled to logistic regression
and XGBoost models. Leakage-safe predictors (HbA1c, glucose, diabetes questionnaire answers and
medication variables excluded) were derived from two public NHANES cycles: 2017–March 2020 pre-pandemic
(historical development, n = 6,103, 28.9% screen-positive) and August 2021–August 2023 (locked temporal
test, n = 4,260, 23.1% screen-positive). The outcome is HbA1c ≥ 5.7% among adults reporting neither
prior diabetes nor prior prediabetes. The primary (confirmatory) endpoint was sensitivity of a hybrid
ranking (XGBoost + ontology-rule score) minus XGBoost alone at a fixed 20% screening capacity, with a
paired participant bootstrap (1,000 replicates). Exploratory experiments probed low-data regimes (E1),
masked inputs (E2), model-family effects (E3), disagreement review (H3), and the published CDC/ADA
prediabetes risk test as a baseline.

**Results.** The primary effect was null: hybrid 0.409 vs ML-only 0.412 at 20% capacity; in the
prespecified direction (hybrid − ML-only) the difference was **−0.003 (95% CI −0.010 to +0.008)**,
entirely within the design's smallest detectable difference (0.014).
At 20% capacity the prevalence ceiling is 0.867; the best policy (logistic + ontology features)
reached sensitivity 0.423 = 0.488 of ceiling, PPV 0.488, lift 2.12. All trained models outperformed
the published CDC/ADA point score (AUPRC 0.460–0.463 vs 0.380; sensitivity@20% 0.407–0.423 vs 0.372).
Ontology features helped the linear model consistently in direction (sensitivity@20% +0.009,
CI −0.004 to +0.019) and gave the smallest degradation under 30% input masking, but no interval
excluded zero. Rule-only ranking (sensitivity@20% 0.343) and disagreement-based review
(precision 0.360 vs size-matched confidence review 0.400) did not add value.

**Conclusions.** Encoding guideline provenance into an executable layer is feasible and auditable,
but on NHANES with full historical data the rule-derived features are largely redundant with the raw
inputs for ranking. The honest headline is a well-powered null on the primary endpoint, with a
consistent but unresolved advantage for guideline features in a linear, low-data and
missing-input settings. All code, protocol, and artifacts are released.

**Keywords:** clinical ontology, screening, NHANES, temporal validation, fixed-capacity evaluation,
leakage control

---

## 1. Introduction

Diabetes screening is a resource-allocation problem before it is a prediction problem: practices can
screen only a bounded fraction of their population, so a model's value at a fixed referral capacity is
often more decision-relevant than its AUROC. At the same time, guidelines such as the ADA Standards of
Care encode expert consensus that is auditable in prose but inert in software. Tabular machine learning
can rank risk effectively, yet it silently discards that consensus; guideline rule engines keep the
consensus but usually are not evaluated under the same strict temporal generalization tests applied to
learned models.

ClinOntoScreen asks a narrow, testable question: **does encoding a documented subset of screening
guidance as an executable, provenance-carrying ontology change screening decisions or robustness,
relative to raw features, when both are evaluated on a genuinely later survey cycle?**

Contributions:

1. An OWL/RDF ontology whose executable rules carry `sectionReference` (which guideline section
   justifies the rule), `ruleExpression`, and `operationalizationStatus` (which criteria — family
   history, gestational diabetes, PCOS — are *described but not computable* from NHANES), so the
   knowledge layer is auditable rather than implicit.
2. A leakage-safe, cycle-harmonized feature contract (including activity minutes harmonized across
   the two cycles' incompatible physical-activity instruments) with an automated contract test.
3. A capacity-constrained evaluation protocol: sensitivity/PPV/lift at 10/20/30% referral budgets,
   always reported against the prevalence ceiling `min(1, capacity/prevalence)`; one pre-specified
   confirmatory comparison; everything else explicitly exploratory with paired-bootstrap uncertainty
   and a pre-registered smallest-effect-of-interest computed on historical validation *before* test access.
4. An honest temporal evaluation on the latest cycle (August 2021–August 2023), including a
   published-knowledge baseline (CDC/ADA prediabetes risk test) and three pre-specified stress
   experiments (low data, missing inputs, model family).

## 2. Related work

**NHANES-based dysglycemia prediction.** NHANES supports a large prediction literature; closest to us
in evaluation discipline is Kumar's leakage-controlled, survey-weighted benchmark of ten models with
rolling-origin temporal cross-validation and the same 2021–2023 holdout (Zenodo, 2026), which also
includes the ADA risk score as a baseline — but contains no knowledge-representation component.
Casacchia et al. (2024) externally validated an EHR-derived prediabetes model on 2017–2020 NHANES,
showing that variable-availability mismatch alone can block validation — a hazard we handle explicitly.
CardioMeta (2026) performs leakage-reduced multi-task cardiometabolic prediction with NHANES temporal
validation and MIMIC-IV transfer, foregrounding calibration and reporting discipline; it likewise has
no guideline layer.

**Ontology- and guideline-based decision support.** Pham and Soo (2026) combine community detection
with a diabetes ontology on Pima/130-US-hospitals/NHANES data and report high discrimination
(NHANES AUROC ≈ 0.91) with semantic-reasoning interpretability — but with lab-inclusive features, a
random-split design, and no temporal holdout or guideline-section provenance. Broader ontology-based
CDS work encodes knowledge but rarely reports fixed-capacity utility or uncertainty against a
learned baseline under distribution shift.

**Selecting evaluation design.** Random splits overstate performance under survey-cycle shift;
capacity-constrained (top-k) reporting is standard in screening/rare-event retrieval but rare in
clinical risk-model papers, where AUROC/PR alone hides the operational trade-off. Our ceiling-adjusted
capacity reporting makes the achievable operating point explicit.

### Capability comparison with the three closest papers

| Dimension | Pham & Soo 2026 (CEAI) | Kumar 2026 (CMPB, Zenodo) | CardioMeta 2026 (arXiv) | **ClinOntoScreen (this work)** |
|---|---|---|---|---|
| Data | Pima, 130-US-Hospitals, NHANES | NHANES 2005–2016 dev, 2017–2020 + 2021–2023 holdouts | NHANES dev + 2017–2020 temporal; MIMIC-IV transfer | NHANES 2017–Mar 2020 dev; **2021–2023 locked temporal test** |
| Target | Diabetes status (lab-inclusive) | HbA1c ≥ 6.5%, no diagnosed diabetes | Multi-task cardiometabolic status | HbA1c ≥ 5.7% in adults reporting no diabetes/prediabetes |
| Ontology / knowledge role | Domain ontology + clustering for semantics/interpretability | None | None | OWL/RDF rules with guideline-section provenance; features, ranking and policy |
| Leakage control | Not reported | Central (leakage-controlled) | Central (leakage-reduced heads) | Forbidden-predictor contract + pipeline-internal transforms + CI test |
| Baselines | Conventional ML/clustering | ADA risk score, survey-weighted GLM, boosting, ensembles | Strong GBDT/neural tabular baselines | LR/XGBoost raw, generic-feature control, rule-only, hybrid, **CDC/ADA published score** |
| Primary metric | Accuracy/AUROC | Discrimination + calibration + decision curves | Macro-AUROC/AUPRC + calibration | **Sensitivity @ fixed capacity with prevalence ceiling**, paired bootstrap CI |
| Missing-input / low-data probes | No | Ablations (unweighted, random split) | Domain-shift transfer | E2 masked inputs (rules report not-assessable), E1 learning curve |
| Limitation vs. us | Random split; lab-inclusive; no temporal test | No knowledge layer | No guideline content; different target | NHANES only; survey weights not used; cross-sectional outcome |

## 3. Data

**Sources.** CDC/NCHS public-use XPT files (DEMO, DIQ, GHB, BMX, BPXO, BPQ, SMQ, PAQ, MCQ, HDL) for
NHANES 2017–March 2020 pre-pandemic and August 2021–August 2023, downloaded from
`wwwn.cdc.gov/Nchs/Data/Nhanes/Public/...` by the notebook (no redistribution).

**Cohort flow (from `artifacts/data_qc.json`).**

| Step | Historical (2017–Mar 2020) | Temporal test (2021–2023) |
|---|---|---|
| Rows in DEMO file | 15,560 (merged panel) | 11,933 (merged panel) |
| Adults 18+ → no reported diabetes → no reported prediabetes → valid HbA1c | 6,103 | 4,260 |
| Screen-positive (HbA1c ≥ 5.7%) | 1,766 (28.94%) | 983 (23.08%) |
| Secondary: HbA1c ≥ 6.5% in test cohort | — | 67 |

**Composition (Table: `artifacts/cohort_composition.csv`).** Test cycle is older (mean age 49.2 vs
46.1; 36.7% vs 27.5% aged 60+) and less non-Hispanic Black (11.1% vs 24.7%) and non-Hispanic Asian
(5.4% vs 11.8%) — a genuine covariate shift that, with the instrument changes below, defines the
temporal-generalization challenge.

**Cycle differences and harmonization.** The physical-activity instruments changed completely
(PAQ650/665 + PAD660/675 in the earlier cycle vs. leisure minutes PAD800/820 in the later one);
they are harmonized into `leisure_activity_minutes` (skip-pattern zeros honored, 7777/9999/77777/99999
masked) and `sedentary_minutes` (PAD680, both cycles). `HDL` (LBDHDD) is available in both cycles and
is included. Not harmonized (excluded from the schema and disclosed): `BPQ040A` hypertension-treatment
item and `MCQ300C` family history exist only in the earlier cycle; cycle-specific weight columns
(`WTMEC2YR`/`WTMECPRP`); a fourth BP reading. **Consequence: `hypertension_treatment` is 100% missing
in the test cohort** (verified in `data_qc.json`); other missingness is small (income-to-poverty ratio
12.5%, CVD history items ≈ 5%, waist 4.1%, BP readings 3.2%, HDL 4.5%).

**Outcome.** `LBXGH ≥ 5.7%` (prediabetes-range HbA1c) among adults answering "no" to both
DIQ010 (told diabetes) and DIQ160 (told prediabetes). Single measurement, research label only — not a
confirmed clinical diagnosis.

## 4. Ontology and rule engine

`ontology/diabetes_screening.ttl` (OWL/RDF, Turtle; 253+ triples; version 0.2.0) encodes an age-based
screening rule and a younger-adult risk-based rule, criteria for age ≥ 35, overweight/obesity
(25 kg/m² general; 23 kg/m² for non-Hispanic Asian participants, per ADA), hypertension, physical
inactivity, CVD history, and higher-risk ethnicity, plus the screen-positive and diabetes-range
outcome definitions. Every rule and outcome carries:

- `hasSource` / `ruleExpression` — machine-checked in CI;
- `sectionReference` — e.g. *ADA Standards of Care in Diabetes—2026, Chapter 2, screening
  recommendations for adults*;
- for criteria not operationalizable on NHANES (family history, gestational diabetes, PCOS):
  dedicated classes with `operationalizationStatus` marking them *described, not computed*.

The executor (`src/clinontoscreen/ontology.py` and the notebook equivalent) derives 11
`onto_*` features, returns *unknown* instead of guessing when inputs are missing (visible as
`onto_criteria_missing_count`), and produces a per-participant rule-priority score. The ontology text
embedded in the notebook is byte-identical to the repository file (contract test).

## 5. Methods

**Leakage contract.** Predictors exclude `LBXGH`, glucose, diabetes questionnaire answers, diabetes
medication variables, `SEQN`, and any target-derived column (automated `FORBIDDEN_FEATURE_TOKENS`
assertions in code and in `tests/`). 9 numeric + 11 categorical raw features; imputation, scaling
and one-hot encoding fit inside each pipeline fold.

**Models.** Logistic regression (L2, `C` ∈ {0.1, 1, 10}) and XGBoost (n_estimators ∈ {150, 300},
depth ∈ {2, 3}, lr ∈ {0.03, 0.07}); hyperparameters selected by 3-fold stratified grid search on
historical data with a 80/20 stratified historical validation split (n = 1,221, 353 positives) used
for all selection, including the hybrid alpha grid {0, 0.025, 0.05, 0.1, 0.15, 0.2, 0.3}.
Six variants: LR/XGB × raw/ontology features, an XGBoost no-higher-risk-ethnicity-flag ablation, and
an XGBoost **generic-feature control** (independently coded columns with identical semantics, used to
check that any gain comes from the values, not the ontology plumbing; values asserted equal).

**Policies.** Model probability; probability + α · rule score (hybrid); ontology rule score alone;
CDC/ADA prediabetes risk test point total. Final models refit on all historical data, XGBoost ensembled
across 5 seeds (logistic regression deterministic — seed SD reported separately).

**Evaluation.** Test outcomes read once, after git tag `protocol-v1` (commit `d30f8f8`; executed commit
`dc7fc37` differs only in reporting-bug fixes, documented in `docs/DECISIONS.md`). Metrics: AUROC,
AUPRC, Brier; capacity tables at 10/20/30% with `sensitivity_ceiling = min(1, capacity/prevalence)`,
fraction-of-ceiling, PPV, lift; paired participant bootstrap (1,000) for sensitivity differences and
AUPRC/AUROC differences; smallest detectable difference (MDE = 1.96 · SE from historical validation,
computed before test access): **0.0143** (hybrid), **0.0146** (LR), **0.0179** (XGB).

**Confirmatory vs exploratory.** Only H2 (hybrid vs XGB-only sensitivity @20%) is confirmatory.
E1 (training fractions 5–100%, 3 subsamples each), E2 (MCAR masking 10%/30% of waist, BP,
hypertension history, activity items; ontology features re-derived from masked inputs), E3 (model
family), H3 (top-k disagreement vs size-matched confidence-only review), subgroups, and the
ethnicity-flag ablation are exploratory and labelled as such.

## 6. Results

### 6.1 Historical validation (selection data)

| Model | AUROC | AUPRC | Brier |
|---|---|---|---|
| Logistic raw | 0.7763 | 0.5419 | 0.1676 |
| Logistic + ontology | 0.7802 | 0.5486 | 0.1663 |
| XGBoost raw | 0.7797 | 0.5433 | 0.1663 |
| XGBoost + ontology | 0.7806 | 0.5437 | 0.1657 |
| XGBoost + ontology (no ethnicity flag) | 0.7785 | 0.5391 | 0.1665 |

Hybrid alpha selected: **0.10** (0.10/0.15/0.20 tied exactly on validation sensitivity/PPV; tie broken
toward the smallest alpha). Alpha 0.10 found 151/353 positives at 20% capacity vs 145 for α = 0.

### 6.2 Temporal test discrimination

| Model (5-seed ensemble) | AUROC | AUPRC | Brier | seed SD (AUROC/AUPRC) |
|---|---|---|---|---|
| Logistic raw | 0.7723 | 0.4598 | 0.1509 | – (deterministic) |
| **Logistic + ontology features** | 0.7718 | **0.4612** | 0.1503 | – |
| XGBoost raw | 0.7689 | **0.4629** | 0.1507 | 0.0005 / 0.0007 |
| XGBoost + ontology features | 0.7678 | 0.4600 | 0.1506 | 0.0004 / 0.0018 |
| XGBoost + ontology (no ethnicity flag) | 0.7686 | 0.4619 | 0.1505 | 0.0004 / 0.0011 |
| XGBoost + generic control features | 0.7678 | 0.4600 | 0.1506 | 0.0004 / 0.0018 |
| *CDC/ADA risk test (published)* | *0.7180* | *0.3803* | *n/a (points)* | — |

Figure: `artifacts/roc_pr_curves.png`, `artifacts/calibration.png`.

### 6.3 Fixed screening capacity (prevalence 0.2308; 20% ceiling = 0.867)

| Policy | Sens @10% | Sens @20% (found/983) | Sens @30% | PPV @20% | Lift @20% | Frac. of ceiling @20% |
|---|---|---|---|---|---|---|
| XGBoost raw | 0.230 | 0.412 (405) | 0.582 | 0.475 | 2.06 | 0.475 |
| XGBoost + ontology features | 0.225 | 0.409 (402) | 0.578 | 0.472 | 2.04 | 0.472 |
| Logistic raw | 0.223 | 0.414 (407) | 0.593 | 0.478 | 2.07 | 0.478 |
| **Logistic + ontology features** | 0.226 | **0.423 (416)** | **0.596** | **0.488** | **2.12** | **0.488** |
| Ontology-only rule score | 0.196 | 0.343 (337) | 0.475 | 0.396 | 1.71 | 0.396 |
| CDC/ADA risk test (published) | 0.199 | 0.372 (366) | 0.520 | 0.430 | 1.86 | 0.430 |

Figure: `artifacts/capacity_sensitivity.png` (ceiling drawn as dashed line).

**Every trained model beats the published risk test at every capacity**, but no policy comes close to
the 0.867 ceiling: the best policy achieves about half of what perfect ranking could achieve at this
budget, i.e. substantial headroom remains at this feature set.

### 6.4 Primary endpoint (H2, confirmatory) — null

| | Sensitivity @20% | Positives found |
|---|---|---|
| XGBoost only (ML policy) | 0.4120 | 405/983 |
| Hybrid (XGB + 0.10 · rule score) | 0.4090 | 402/983 |
| **Difference, prespecified direction (hybrid − ML-only)** | **−0.0031, 95% CI [−0.0100, +0.0079]** | (paired bootstrap, 1,000; SE 0.0046) |

(`research_results.json` stores the same interval as ML-only − hybrid = +0.0031
[−0.0079, +0.0100]; the sign convention is documented in `docs/DECISIONS.md`.)

The interval crosses zero and lies entirely within the pre-registered MDE (0.0143): the design cannot
resolve an effect of this size, and none is claimed. The ethnicity-flag ablation was likewise null in
the prespecified direction (ablated hybrid − ML-only = −0.0051, 95% CI [−0.0119, +0.0053]).
Figure: `artifacts/primary_effect_ci.png`.

### 6.5 E3 — does the knowledge layer help one model family more? (exploratory)

| Comparison | Δ sensitivity @20% (95% CI) | Δ AUPRC (95% CI) |
|---|---|---|
| Logistic + ontology vs raw | **+0.0092 [−0.0038, +0.0185]** | +0.0014 [−0.0047, +0.0070] |
| XGBoost + ontology vs raw | −0.0031 [−0.0181, +0.0114] | −0.0029 [−0.0092, +0.0038] |
| XGBoost + ontology (no ethnicity flag) vs raw | +0.0000 [−0.0110, +0.0144] | — |

All intervals cross zero and all point effects are below the MDE. The **direction** matches the
prespecified hypothesis (threshold flags help a linear model at least as much as a flexible tree),
but the data do not establish it. The generic-feature control is numerically identical to the
ontology-feature variant for XGBoost (AUPRC 0.4600 both; sensitivity@20% 0.409 both), showing the
rule columns carry no information beyond their raw inputs for the tree model.
Figure: `artifacts/e3_model_family_deltas.png`.

### 6.6 E1 — low-data learning curve (exploratory)

Ontology-minus-raw deltas (AUPRC, sensitivity@20%) by training fraction:

| Fraction (n) | Logistic ΔAUPRC | Logistic Δsens | XGBoost ΔAUPRC | XGBoost Δsens |
|---|---|---|---|---|
| 5% (305) | −0.0044 | −0.0119 | +0.0008 | +0.0020 |
| 10% (610) | −0.0037 | −0.0010 | +0.0012 | +0.0044 |
| 25% (1,525) | −0.0007 | −0.0020 | −0.0014 | +0.0003 |
| 50% (3,051) | **+0.0024** | **+0.0061** | −0.0021 | −0.0027 |
| 100% (6,103) | +0.0014 | +0.0092 | −0.0044 | −0.0061 |

No consistent low-data advantage: the linear model's gain turns positive only at ≥50% data, the tree
model's turns negative. Reported as measured. Figure: `artifacts/e1_learning_curve.png`.

### 6.7 E2 — missing-input stress test (exploratory)

Mean over 3 masked repeats:

| Model | AUPRC @0% | AUPRC @30% | Δ | Sens@20% @0% | Sens@20% @30% | Δ |
|---|---|---|---|---|---|---|
| Logistic + ontology | 0.4612 | 0.4597 | −0.0015 | 0.4232 | 0.4218 | **−0.0014** |
| Logistic raw | 0.4598 | 0.4578 | −0.0020 | 0.4140 | 0.4140 | −0.0000 |
| XGBoost raw | 0.4629 | 0.4597 | −0.0032 | 0.4120 | 0.4076 | −0.0044 |
| XGBoost + ontology policy (hybrid) | **0.4633** | **0.4608** | −0.0025 | 0.4090 | 0.4093 | +0.0003 |

The hybrid policy keeps the highest AUPRC at every masking rate; the linear models are the most
stable at capacity. The rule layer never saw information the ML system lacked: ontology features were
re-derived from the masked inputs and reported `not-assessable` rather than imputing rules. The
not-assessable fraction stayed at 0.004 because masked items are risk factors, not eligibility inputs.
Figure: `artifacts/e2_missing_input.png`.

### 6.8 H3 — guideline disagreement vs size-matched confidence review (exploratory)

Top-20% ML set and top-20% rule set overlap in 477 participants → disagreement set of 750
(270 positives, precision 0.360). The 750 participants nearest the ML cutoff (confidence-only review)
contain 300 positives (precision 0.400) against cohort prevalence 0.231. The disagreement set is **not**
enriched over simple confidence review; reviewing where the guideline and the model disagree is not
supported by these data.

### 6.9 Subgroups (exploratory, descriptive only)

Selected rows at 20% capacity (all groups ≥ 50 participants and ≥ 10 positives; full table in
`research_results.json → subgroups`):

| Subgroup | n | Prev. | Sens (XGB raw) | Sens (XGB + ontology) |
|---|---|---|---|---|
| All | 4,260 | 0.231 | 0.412 | 0.409 |
| Age 18–39 | 1,537 | 0.094 | 0.517 | 0.524 |
| Age 60+ | 1,562 | 0.354 | 0.295 | 0.293 |
| Female | 2,347 | 0.220 | 0.431 | 0.451 |
| Male | 1,913 | 0.244 | 0.388 | 0.373 |
| Non-Hispanic Black | 473 | 0.383 | 0.271 | 0.276 |
| Hispanic | 731 | 0.242 | 0.469 | 0.452 |

Sensitivity is far lower in the high-prevalence 60+ group simply because the fixed capacity is
oversubscribed there; differences between rows are not interaction tests and are not powered.

## 7. Discussion

**What the results support.**
1. **The primary endpoint is null and the null is informative.** With the protocol frozen before
   test access, α selected on historical validation, and an MDE computed in advance (0.0143), the
   hybrid rule-score policy neither helps nor harms top-20% triage: hybrid − ML-only = −0.003
   [−0.010, +0.008].
2. **Guideline provenance can be made executable and auditable.** Every rule carries its guideline
   section reference; criteria that NHANES cannot operationalize are declared rather than faked;
   unknown inputs produce "not assessable" rather than silent defaults. This is a contribution of
   engineering method, not of predictive performance.
3. **Learned models beat the published risk test on this cohort** at every capacity and by a large
   margin in ranking quality (AUPRC +0.08–0.083), while the published score remains fully transparent.
   Two of its items (gestational diabetes, family history) are unavailable in NHANES, which limits
   this comparison — disclosed, not hidden.
4. **Knowledge content, not ontology plumbing.** The generic-feature control matches the
   ontology-feature variant exactly for XGBoost: converting known rules into extra columns neither
   adds information the tree cannot reconstruct nor invents signal.

**What the results do not support.** No claim of improvement on the primary endpoint; no claim that
rule features help in low data (direction inconsistent across families); no claim that disagreement
review adds value; no clinical validity of any kind.

**Why the null is plausible.** Rule features are deterministic transforms of raw inputs the models
already see; with 6,103 historical participants the trees reconstruct them and the linear model's
remaining edge (+0.009 at capacity, CI crossing zero) is below resolution. The places where knowledge
could in principle dominate — sparse labels, missing inputs — show small consistent gains for the
guideline features (E2 stability; LR direction), which is exactly where a learned model has less to
reconstruct from.

**Practical role of the knowledge layer.** On this evidence, its value is provenance, audit and
behavior under missingness — not ranking. Deployment-minded use should treat the ontology as the
reporting/explanation substrate with the model supplying the score.

## 8. Limitations and ethics

- Single HbA1c measurement; the outcome is a screen-positive label, not confirmed disease.
- NHANES is a public, cross-sectional, complex-survey sample; **survey weights are not used**, so
  results are not population-representative estimates, and cycle design differences confound part of
  the temporal shift (test cohort is older and demographically different).
- The ontology operationalizes a bounded subset of ADA guidance; family history, gestational diabetes
  and PCOS criteria are declared unoperationalized, and `hypertension_treatment` is unavailable in the
  test cycle (100% missing) — a documented measurement gap the model must live with.
- Race/ethnicity enters in two ways (rule flag; Asian-specific BMI threshold). The no-flag ablation
  is disclosed as partial: the Asian BMI threshold and the raw predictor remain.
- Exploratory experiments and subgroups are not multiplicity-adjusted; all intervals are shown.
- No prospective or clinical evaluation; no patient data used; the Streamlit explorer must not be
  used with real patient information.

## 9. Conclusion

Under a pre-specified, temporally held-out evaluation on NHANES 2021–2023, adding an executable
guideline-ontology layer to screening models produced a **null primary effect on sensitivity at 20%
capacity** (hybrid − ML-only = −0.003, 95% CI −0.010 to +0.008, below the pre-registered smallest detectable difference),
while all trained models clearly outperformed the published CDC/ADA risk test and the knowledge layer
showed its only consistent value where data are scarce or inputs go missing. The most defensible
empirical finding is therefore a boundary: on rich tabular data, guideline features are redundant for
ranking but not for auditability — and any future claim that knowledge integration improves screening
must be made against this protocol, at this capacity, with this ceiling.

---

## Artifact index

| Figure / table | File |
|---|---|
| ROC + PR curves | `artifacts/roc_pr_curves.png` |
| Calibration | `artifacts/calibration.png` |
| Capacity sensitivity (all policies + ceiling) | `artifacts/capacity_sensitivity.png` |
| Primary effect CI | `artifacts/primary_effect_ci.png` |
| E1 learning curve | `artifacts/e1_learning_curve.png` |
| E2 missing-input stress | `artifacts/e2_missing_input.png` |
| E3 model-family deltas | `artifacts/e3_model_family_deltas.png` |
| All numbers | `artifacts/research_results.json` |
| Per-participant predictions | `artifacts/test_predictions.csv` |
| Cohort composition | `artifacts/cohort_composition.csv` |
| Historical validation metrics | `artifacts/historical_validation_metrics.csv` |
| Published baseline tables | `artifacts/published_score_baseline.csv` |
| QC / missingness / cohort flow | `artifacts/data_qc.json` |
| Provenance (commit, tag, versions) | `research_results.json → protocol`, `docs/DECISIONS.md` |
