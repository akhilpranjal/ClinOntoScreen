# ClinOntoScreen: Addendum to plan.md (review amendments)

Status: proposed amendments. Record accepted ones in `docs/DECISIONS.md` **before** any 2021–2023 results are viewed.

## 0. Review summary

The protocol is rigorous: locked temporal test set, leakage deny-list, paired bootstrap, generic-feature control, honest claims. Three real risks remain:

1. **Scope.** Ten commits, seven documents and a five-page dashboard will not fit in 2–3 days, and the *paper* is the graded deliverable.
2. **Likely null predictive result.** The rule features are simple thresholds of variables the model already sees. XGBoost can learn them from full historical data. A null on H1/H2 is plausible, so the plan needs experiments where knowledge can matter.
3. **A few design gaps** (metric ceiling, outcome-measurement drift, unnamed closest papers, undefined disagreement baseline). Details below.

## 1. Scope triage (must / should / could)

| Priority | Item |
|---|---|
| MUST (Days 1–2) | Data downloader + harmonizer; `diabetes_screening.ttl` + rule executor + tests; LR/XGBoost raw, +ontology, +generic control; fixed-capacity evaluation with paired bootstrap; notebook that produces `research_results.json` |
| MUST (Day 3) | The paper draft with all tables/figures generated from artifacts |
| SHOULD | Streamlit with 3 pages only: Results, Case Explorer, Ontology Explorer (NetworkX/Plotly graph) |
| COULD | Data & Methods page, screenshots, `CITATION.cff` |
| CUT / MERGE | Merge `CONTRIBUTING`, `FIGURES.md`, `DATA_DICTIONARY.md` into README + METHODOLOGY (auto-generate the data dictionary from the feature manifest). Group the 10 commits into about 5 |

Write paper sections (Data, Ontology, Methods) while the notebook runs. Do not leave writing to the end.

## 2. Historical-only sanity check (not a test-set gate)

Your plan avoids a "pilot gate". Keep that for the **test set**, but add a risk control that touches **historical data only**:

- By end of Day 1: report cohort size, positive count, prevalence, missingness, and baseline AUROC/AUPRC on historical validation.
- If AUROC is implausibly low or the positive count is tiny, fix the pipeline then, not on Day 3.
- Never load 2021–2023 outcomes into modelling code before the protocol tag (section 9).

## 3. Make the ontology question non-trivial (add three pre-specified experiments)

With full historical data, rule flags may add nothing. Knowledge is more likely to help when data or inputs are limited, so add:

- **E1 Low-data learning curve:** train on 5%, 10%, 25%, 50%, 100% of historical data (repeated subsamples); compare raw vs +ontology for LR and XGBoost on the locked test.
- **E2 Missing-input stress test:** at test time randomly mask waist/BP/etc. at 0%, 10%, 30% (MCAR, fixed seeds); compare systems. The executor must report "not assessable" rather than guessing.
- **E3 Model-family effect:** report LR and XGBoost separately; threshold flags may help the linear model more.

Label E1–E3 exploratory. Report them whichever direction they go. They give the paper a real AI-side question ("when does guideline knowledge help?") even if H2 is null.

## 4. Metric ceiling and prevalence

Sensitivity at capacity k cannot exceed k / prevalence. If prevalence of HbA1c >= 5.7 in this cohort is above 20%, the 20% budget caps achievable sensitivity.

- Compute prevalence on **historical** data before finalising the capacity. Any change to the primary capacity must be logged in DECISIONS before test evaluation.
- Always report prevalence, the ceiling, **fraction of ceiling achieved**, PPV and lift (enrichment) beside sensitivity at 10/20/30%.

## 5. Published-knowledge baseline (matched comparator)

Add one published point-based screening score (for example the CDC/ADA prediabetes risk test or an ADA-derived risk score) as an external knowledge baseline. Verify the exact scoring from the source, map each item to NHANES variables, and list items that are unavailable. This answers "why not an existing score?" and parallels the matched-protocol strategy that worked for the reference paper.

## 6. ADA rule encoding checklist

- Verify every rule against the 2026 chapter text: screening start age, BMI thresholds (including any lower threshold for Asian American adults, which needs the NHANES race/ethnicity code), and the risk-factor list.
- Store the section/recommendation identifier per rule in the ontology.
- Consider adding: first-degree relative with diabetes (MCQ family-history item) and HDL cholesterol if present in both cycles. List GDM, PCOS and similar items as unavailable or approximated.
- Confirm variable names exist in **both** cycles' codebooks (for example DIQ160, BPXO, PAQ items change or are modified).

## 7. Outcome-measurement and selection caveats (add to Limitations)

- CDC documents that the HbA1c instrument changed during the 2021–2023 cycle (Tosoh G8 to Bio-Rad D-100). A bridging study found r = 0.999 and CDC applied no correction. Treat this as a documented limitation, not something you adjust. Source: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GHB_L.htm
- The same page notes that phlebotomy nonresponse in 2021–2023 differed by age group and race/ethnicity. Report cohort flow and composition by period, and note possible selection into the "valid HbA1c" cohort.
- Expect test cohorts in the low thousands (a related external validation on NHANES 2021–2023 had N = 3,043 with a different cohort definition). Precompute the paired-bootstrap standard error on validation data so you know the smallest difference you can detect. Do not claim wins below it.

## 8. Experimental hygiene fixes

- **Seeds:** with deterministic LR and XGBoost defaults, five seeds change nothing. Make seeds meaningful (dev/validation split, `subsample`, `colsample_bytree`) or say the models are deterministic.
- **Multiplicity:** H2 is the only confirmatory test. H1, H3, H4, E1–E3 and subgroup analyses are exploratory; say so in `docs/EXPERIMENTS.md`.
- **H3 definitions:** fix before the test. Define the disagreement set (ML in top-k XOR rule-eligible) and a size-matched confidence-only review set (cases ranked closest to the top-k cutoff). Compare positives found and precision at equal review sizes.

## 9. Protocol freeze

- Create git tag `protocol-v1` after DECISIONS is final. Store the commit hash and package versions in `research_results.json`.
- Run test-set evaluation once, in a separate cell/script. After seeing results, change code only for recorded bug fixes.

## 10. Closest papers to read and compare by capability

- Yoo, Maggiore, Jolliet (J Clin Epidemiol, 2026): ML self-assessment trained on NHANES 1988–2018, externally validated on NHANES 2021–2023 and Korea NHANES 2023. Different target (prediabetes or diabetes). https://air.unipr.it/handle/11381/3056314
- arXiv 2607.16253: NHANES-trained T2D model with large external validation and fairness analysis. https://arxiv.org/pdf/2607.16253
- arXiv 2607.15721 (CardioMeta): temporal validation and NHANES-to-MIMIC-IV transfer. https://arxiv.org/pdf/2607.15721

Do a targeted search (about 1 hour) for: guideline-informed or knowledge-infused features for diabetes screening; ontology-based diabetes screening; selective prediction under a fixed referral budget. Compare to these works in a **capability table** (data, target, knowledge used, explanation, shift test), not by raw scores, because targets differ.

## 11. Honest expectation (for the paper's framing)

- Most likely: little or no predictive gain from rule features in the full-data regime. Then the paper's contribution is a rigorous, reproducible evaluation, a traceable ontology layer, and findings from E1–E3 and the disagreement analysis.
- Realistic venue class: a small conference, workshop or student symposium. Acceptance cannot be promised, and the plan's no-overclaiming stance is correct.

## 12. Revised 3-day schedule

| Day | Goal | Hard stop |
|---|---|---|
| 1 | Data pipeline, cohort/target checks, baselines on historical validation, ontology rules drafted | Sanity numbers in hand (section 2) |
| 2 | Ontology + features, all model variants, E1–E3 on validation, freeze protocol, run test once, tables/figures | `protocol-v1` tagged before test run |
| 3 | Paper (main deliverable), minimal Streamlit, README | Paper draft complete |

## 13. Definition-of-done additions

- [ ] Prevalence, ceiling and fraction-of-ceiling reported
- [ ] E1–E3 results generated and reported regardless of direction
- [ ] Published-score baseline included, with unavailable items listed
- [ ] HbA1c instrument change and selection caveats stated
- [ ] `protocol-v1` tag and commit hash stored in results JSON
- [ ] Capability-comparison table against the three closest papers
