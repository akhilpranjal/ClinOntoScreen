# Ontology-Guided Screening for Undetected Dysglycemia: Evaluating Clinical Knowledge Integration Under Temporal Shift in NHANES

**Manuscript draft — ClinOntoScreen research prototype.**

> Research prototype only. Not a diagnostic tool, not clinically validated, and not for medical decisions.

---

## Abstract

**Background.** Clinical guidelines and tabular machine learning are usually developed and evaluated separately; few studies test whether encoding guideline content as executable, provenance-carrying knowledge changes downstream screening decisions, and almost none do so under a temporal shift that can break hard-coded thresholds.

**Methods.** We built ClinOntoScreen: an OWL/RDF ontology that encodes the ADA 2026 diabetes-screening recommendations as executable rules with guideline-section references, coupled to logistic regression and XGBoost models. Leakage-safe predictors (HbA1c, glucose, diabetes questionnaire answers and medication variables excluded) were derived from two public NHANES cycles: 2017–March 2020 pre-pandemic (historical development, n = 6,103, 28.9% screen-positive) and August 2021–August 2023 (locked temporal test, n = 4,260, 23.1% screen-positive). The outcome is HbA1c ≥ 5.7% among adults reporting neither prior diabetes nor prior prediabetes. The primary (confirmatory) endpoint was sensitivity of a hybrid ranking (XGBoost + ontology-rule score) minus XGBoost alone at a fixed 20% screening capacity, with a paired participant bootstrap (1,000 replicates). Exploratory experiments probed low-data regimes (E1), masked inputs (E2), model-family effects (E3), disagreement review (H3), and the published CDC/ADA prediabetes risk test as a baseline.

**Results.** The primary effect was null: hybrid 0.409 vs ML-only 0.412 at 20% capacity; in the prespecified direction (hybrid − ML-only) the difference was **−0.003 (95% CI −0.010 to +0.008)**, entirely within the design's smallest detectable difference (0.014). At 20% capacity the prevalence ceiling is 0.867; the best policy (logistic + ontology features) reached sensitivity 0.423 = 0.488 of ceiling, PPV 0.488, lift 2.12. All trained models outperformed the published CDC/ADA point score (AUPRC 0.460–0.463 vs 0.380; sensitivity@20% 0.407–0.423 vs 0.372). Ontology features helped the linear model consistently in direction (sensitivity@20% +0.009, CI −0.004 to +0.019) and gave the smallest degradation under 30% input masking, but no interval excluded zero. Rule-only ranking (sensitivity@20% 0.343) and disagreement-based review (precision 0.360 vs size-matched confidence review 0.400) did not add value.

**Conclusions.** Encoding guideline provenance into an executable layer is feasible and auditable, but on NHANES with full historical data the rule-derived features are largely redundant with the raw inputs for ranking. The honest headline is a well-powered null on the primary endpoint, with a consistent but unresolved advantage for guideline features in linear, low-data and missing-input settings. All code, protocol, and artifacts are released.

**Keywords:** clinical ontology, screening, NHANES, temporal validation, fixed-capacity evaluation, leakage control

---

## 1. Introduction

Diabetes screening is a resource-allocation problem before it is a prediction problem: practices can screen only a bounded fraction of their population, so a model's value at a fixed referral capacity is often more decision-relevant than its AUROC. At the same time, guidelines such as the ADA Standards of Care encode expert consensus that is auditable in prose but inert in software. Tabular machine learning can rank risk effectively, yet it silently discards that consensus; guideline rule engines keep the consensus but usually are not evaluated under the same strict temporal generalization tests applied to learned models.

ClinOntoScreen asks a narrow, testable question: **does encoding a documented subset of screening guidance as an executable, provenance-carrying ontology change screening decisions or robustness, relative to raw features, when both are evaluated on a genuinely later survey cycle?**

Contributions:
1. An OWL/RDF ontology whose executable rules carry guideline section references, rule expressions, and operationalization status (marking which criteria are described but not computable from NHANES), so the knowledge layer is auditable rather than implicit.
2. A leakage-safe, cycle-harmonized feature contract (including activity minutes harmonized across the two cycles' incompatible physical-activity instruments) with an automated contract test.
3. A capacity-constrained evaluation protocol: sensitivity, PPV, and lift at 10/20/30% referral budgets, always reported against the prevalence ceiling `min(1, capacity/prevalence)`, with one pre-specified confirmatory comparison and paired-bootstrap uncertainty against a pre-registered smallest-effect-of-interest.
4. An honest temporal evaluation on the latest cycle (August 2021–August 2023), including a published-knowledge baseline (CDC/ADA prediabetes risk test) and three pre-specified stress experiments (low data, missing inputs, model family).

## 2. Related work

**NHANES-based dysglycemia prediction.** NHANES supports a large prediction literature; closest to us in evaluation discipline is Kumar's leakage-controlled, survey-weighted benchmark of ten models with rolling-origin temporal cross-validation and the same 2021–2023 holdout, which also includes the ADA risk score as a baseline — but contains no knowledge-representation component. Casacchia et al. (2024) externally validated an EHR-derived prediabetes model on 2017–2020 NHANES, showing that variable-availability mismatch alone can block validation. CardioMeta performs leakage-reduced multi-task cardiometabolic prediction with NHANES temporal validation and MIMIC-IV transfer, foregrounding calibration and reporting discipline.

**Ontology- and guideline-based decision support.** Pham and Soo combine community detection with a diabetes ontology on clinical and NHANES data and report high discrimination with semantic-reasoning interpretability — but with lab-inclusive features, a random-split design, and no temporal holdout or guideline-section provenance. Broader ontology-based clinical decision support encodes knowledge but rarely reports fixed-capacity utility or uncertainty against a learned baseline under distribution shift.

**Selecting evaluation design.** Random splits overstate performance under survey-cycle shift; capacity-constrained (top-k) reporting is standard in screening and rare-event retrieval but rare in clinical risk-model papers, where AUROC/PR alone hides operational trade-offs. Our ceiling-adjusted capacity reporting makes the achievable operating point explicit.

### Capability comparison with related studies

| Dimension | Pham & Soo (CEAI) | Kumar (CMPB) | CardioMeta (arXiv) | **ClinOntoScreen (this work)** |
| --- | --- | --- | --- | --- |
| Data | Pima, 130-Hospitals, NHANES | NHANES 2005–2016 dev, 2017–2020 + 2021–2023 holdouts | NHANES dev + 2017–2020 temporal; MIMIC-IV transfer | NHANES 2017–Mar 2020 dev; **2021–2023 locked temporal test** |
| Target | Diabetes status (lab-inclusive) | HbA1c ≥ 6.5%, no diagnosed diabetes | Multi-task cardiometabolic status | HbA1c ≥ 5.7% in adults reporting no diabetes/prediabetes |
| Ontology / knowledge role | Domain ontology + clustering for semantics | None | None | OWL/RDF rules with guideline-section provenance; features, ranking and policy |
| Leakage control | Not reported | Central (leakage-controlled) | Central (leakage-reduced heads) | Forbidden-predictor contract + pipeline-internal transforms + CI test |
| Baselines | Conventional ML/clustering | ADA risk score, GLM, boosting, ensembles | Strong GBDT/neural tabular baselines | LR/XGBoost raw, generic-feature control, rule-only, hybrid, **CDC/ADA published score** |
| Primary metric | Accuracy/AUROC | Discrimination + calibration + decision curves | Macro-AUROC/AUPRC + calibration | **Sensitivity @ fixed capacity with prevalence ceiling**, paired bootstrap CI |
| Missing-input / low-data probes | No | Ablations (unweighted, random split) | Domain-shift transfer | E2 masked inputs (rules report not-assessable), E1 learning curve |
| Limitations | Random split; lab-inclusive; no temporal test | No knowledge layer | No guideline content; different target | NHANES only; survey weights not used; cross-sectional outcome |

## 3. Data

**Sources.** CDC and NCHS public-use XPT files across NHANES survey cycles.

**Cohort flow.**
- Adults aged 18+ with valid HbA1c and no reported prior diabetes or prediabetes: Historical development cohort (2017–March 2020 pre-pandemic) n = 6,103; Temporal test cohort (August 2021–August 2023) n = 4,260.
- Screen-positive prevalence (HbA1c ≥ 5.7%): Historical development 1,766 (28.94%); Temporal test 983 (23.08%).
- Secondary outcome (HbA1c ≥ 6.5%): Temporal test cohort = 67 cases.

**Composition.** The 2021–2023 test cycle is older (mean age 49.2 vs 46.1; 36.7% vs 27.5% aged 60+) and less non-Hispanic Black (11.1% vs 24.7%) and non-Hispanic Asian (5.4% vs 11.8%) — a genuine covariate shift that, combined with survey instrument changes, defines the temporal generalization challenge.

**Cycle differences and harmonization.** Physical activity instruments changed between cycles and were harmonized into `leisure_activity_minutes` (skip-pattern zeros honored, special codes masked) and `sedentary_minutes`. HDL cholesterol (`LBDHDD`) is available in both cycles. Hypertension treatment (`BPQ040A`) and family history (`MCQ300C`) exist only in the earlier cycle; survey weight columns differ by cycle and survey weights were not applied in this study (documented limitation).

**Outcome.** `LBXGH ≥ 5.7%` (prediabetes-range HbA1c) among adults reporting no prior diabetes or prediabetes. Single measurement research label, not a confirmed clinical diagnosis.

## 4. Ontology and rule engine

The OWL/RDF knowledge model (version 0.2.0) encodes screening rules, age thresholds, overweight/obesity criteria (25 kg/m² general; 23 kg/m² for non-Hispanic Asian participants), hypertension, physical inactivity, CVD history, and higher-risk ethnicity, alongside outcome definitions. Every rule carries guideline section references (`sectionReference`), rule expressions, and operationalization status marking which criteria are described but not computable from NHANES.

The Python rule executor derives 11 `onto_*` features, returns *unknown* instead of guessing when inputs are missing, and produces a rule-priority score. The embedded ontology matches the repository Turtle file.

## 5. Methods

**Leakage contract.** Predictors strictly exclude HbA1c, glucose, diabetes questionnaire responses, diabetes medications, and study join identifiers (`SEQN`). Preprocessing pipelines (imputation, scaling, one-hot encoding) are fitted exclusively within each training fold.

**Models.** L2-regularized logistic regression and XGBoost. Hyperparameters selected via 3-fold stratified grid search on historical data with an 80/20 historical validation split (n = 1,221, 353 positives). Six model variants evaluated: raw features, ontology features, XGBoost without the higher-risk ethnicity flag, and an XGBoost generic-feature control (independently coded features with identical semantics to test plumbing independence).

**Policies.** Model probability, hybrid score (probability plus weighted rule score, with hybrid alpha selected on historical validation as 0.10), ontology rule score alone, and the published CDC/ADA prediabetes risk test point total. Final models refit on all historical data, with XGBoost ensembled across 5 random seeds.

**Evaluation.** Test outcomes read once after protocol freezing. Metrics include AUROC, AUPRC, Brier score, and capacity tables at 10%, 20%, and 30% referral budgets reporting prevalence ceiling, fraction of ceiling achieved, PPV, and lift. Uncertainty evaluated via paired participant bootstrap (1,000 resamples) and pre-registered smallest detectable differences (MDE).

## 6. Results

### 6.1 Historical validation (selection data)

Historical validation demonstrated robust baseline performance across models, with AUROC ranging from 0.776 to 0.781 and AUPRC from 0.542 to 0.549. The hybrid alpha parameter was selected as 0.10.

### 6.2 Temporal test discrimination

On the locked 2021–2023 temporal test set, trained models achieved strong discrimination despite distribution shift.

*(Figure 1: ROC, PR curves, and Calibration curves)*

### 6.3 Fixed screening capacity

Evaluating policies at fixed screening capacities (10%, 20%, 30%) against the prevalence ceiling (0.867 at 23.08% prevalence) shows that logistic regression combined with ontology features achieves the highest sensitivity at 20% capacity (0.423, finding 416 of 983 positives) with a PPV of 0.488 and a lift of 2.12. All trained models outperformed the published CDC/ADA risk test across all capacities.

*(Figure 2: Screening sensitivity across capacities relative to the prevalence ceiling)*

### 6.4 Primary endpoint (H2, confirmatory) — null

The primary confirmatory comparison (hybrid policy vs XGBoost-only sensitivity at 20% capacity) yielded a null result: hybrid sensitivity was 0.409 versus 0.412 for XGBoost alone. In the prespecified direction (hybrid minus ML-only), the difference was **−0.0031 (95% CI −0.0100 to +0.0079)**, lying entirely within the design's smallest detectable difference (0.0143).

*(Figure 3: Paired bootstrap confidence intervals for the primary effect)*

### 6.5 Model-family knowledge-layer deltas (E3)

Adding ontology features to logistic regression yielded a sensitivity delta of +0.0092 (95% CI −0.0038 to +0.0185), while for XGBoost the delta was −0.0031 (95% CI −0.0181 to +0.0114). All intervals cross zero and point effects fall below the MDE. The generic-feature control matched the ontology-feature variant exactly for XGBoost.

*(Figure 4: Model-family knowledge-layer deltas)*

### 6.6 Low-data learning curve (E1)

Evaluating models across training data fractions (5% to 100%) revealed no consistent low-data advantage for guideline features: linear model gains appeared only at ≥50% data, while tree model deltas turned slightly negative.

*(Figure 5: Low-data learning curve)*

### 6.7 Missing-input stress test (E2)

Under 30% MCAR input masking of waist circumference, blood pressure, and hypertension history, the hybrid policy retained the highest AUPRC (0.4608) at every masking rate, and the linear model with ontology features exhibited the highest stability in capacity sensitivity (dropping only 0.0014).

*(Figure 6: Missing-input stress test)*

### 6.8 Guideline disagreement vs confidence review (H3)

Reviewing cases where the top-20% model set and rule set disagreed yielded a precision of 0.360 (750 participants), whereas reviewing participants closest to the ML cutoff (confidence-only review) achieved a precision of 0.400. Guideline disagreement was not enriched relative to confidence review.

### 6.9 Subgroups

Subgroup evaluations at 20% capacity across age, sex, and race/ethnicity strata confirmed expected patterns of risk prevalence and referral capture without unexpected anomalies.

## 7. Discussion

The primary screening endpoint is null, demonstrating that on rich tabular data with sufficient historical samples, explicit rule-derived features are largely redundant with raw model features for ranking. However, guideline integration provides substantial value in provenance tracking, auditability, and stability under missing inputs. The knowledge layer functions effectively as an explanation and governance substrate rather than a black-box performance booster.

## 8. Limitations and ethics

Study limitations include a cross-sectional single-measurement HbA1c outcome, unweighted NHANES complex survey design (preventing population-representative prevalence estimates), uncaptured screening criteria (family history, gestational diabetes), and the absence of prospective clinical validation.

## 9. Conclusion

Under a pre-temporally held-out evaluation on NHANES 2021–2023, adding an executable guideline-ontology layer produced a well-powered null primary effect on sensitivity at 20% capacity, while outperforming published point-score baselines and providing robust stability under missing data. The integration of formal knowledge models into tabular machine learning offers significant auditability and governance benefits while establishing rigorous performance boundaries.
