# Locked temporal-test evaluation: fixed-capacity policies, uncertainty, and exploratory analyses.
# This is the only stage that reads 2021–2023 outcomes for evaluation.
test_rule_score = test_onto['onto_rule_priority_score'].to_numpy(dtype=float)
test_rule_score_no_ethnicity = test_onto_no_ethnicity['onto_rule_priority_score'].to_numpy(dtype=float)
test_eligible = test_onto['onto_screening_eligible'].to_numpy(dtype=float)
hybrid_score = probabilities['xgboost_raw'] + HYBRID_ALPHA*test_rule_score
hybrid_score_no_ethnicity = probabilities['xgboost_raw'] + HYBRID_ALPHA_NO_ETHNICITY*test_rule_score_no_ethnicity
published_score = cdc_ada_risk_score(test_raw).to_numpy(dtype=float)

screening_budget_rows=[]
policy_scores={
    'XGBoost raw': probabilities['xgboost_raw'],
    'XGBoost + ontology features': probabilities['xgboost_ontology'],
    'XGBoost + ontology features (no higher-risk ethnicity flag)': probabilities['xgboost_ontology_no_ethnicity'],
    'XGBoost + ontology policy': hybrid_score,
    'XGBoost + ontology policy (no higher-risk ethnicity flag)': hybrid_score_no_ethnicity,
    'Logistic raw': probabilities['logistic_raw'],
    'Logistic + ontology features': probabilities['logistic_ontology'],
    'Ontology-only rule score': test_rule_score,
    'Ontology-only rule score (no higher-risk ethnicity flag)': test_rule_score_no_ethnicity,
    'XGBoost + generic equivalent features': probabilities['xgboost_generic_control'],
    'CDC/ADA prediabetes risk test (published score)': published_score,
}
for capacity in CAPACITIES:
    for policy,score in policy_scores.items():
        screening_budget_rows.append({'policy':policy,**capacity_pack(y_test,score,capacity)})
screening_budget_df=pd.DataFrame(screening_budget_rows)
display(screening_budget_df)

# H2, confirmatory: hybrid minus XGBoost-only sensitivity at 20% capacity.
# NOTE on sign convention: paired_capacity_bootstrap(a, b) returns sensitivity(a) - sensitivity(b).
# The stored 'difference' is therefore (ML-only) - (hybrid); the prespecified direction
# (hybrid) - (ML-only) is its negation. Both are stated explicitly in the run log and the paper.
primary_effect=paired_capacity_bootstrap(y_test,probabilities['xgboost_raw'],hybrid_score)
base_at20=capacity_pack(y_test,probabilities['xgboost_raw'],PRIMARY_CAPACITY)
hybrid_at20=capacity_pack(y_test,hybrid_score,PRIMARY_CAPACITY)
primary_effect.update({'baseline_sensitivity':base_at20['sensitivity'],'hybrid_sensitivity':hybrid_at20['sensitivity'],
                       'baseline_positive_found':base_at20['positive_found'],'hybrid_positive_found':hybrid_at20['positive_found'],
                       'baseline_precision':base_at20['precision'],'hybrid_precision':hybrid_at20['precision'],
                       'prevalence':base_at20['prevalence'],'sensitivity_ceiling':base_at20['sensitivity_ceiling'],
                       'fraction_of_ceiling_baseline':base_at20['fraction_of_ceiling'],
                       'fraction_of_ceiling_hybrid':hybrid_at20['fraction_of_ceiling'],
                       'mde_95_from_historical_validation':MDE['primary_hybrid_vs_xgb_raw']['mde_95'],
                       'capacity':PRIMARY_CAPACITY})
print('H2 primary endpoint (confirmatory). Stored difference = ML-only minus hybrid:',primary_effect)
print('Prespecified direction (hybrid minus ML-only):',
      round(-primary_effect['difference'],6),
      'CI [', round(-primary_effect['ci_high'],6), ',', round(-primary_effect['ci_low'],6), ']')

no_eth_base_at20=capacity_pack(y_test,probabilities['xgboost_raw'],PRIMARY_CAPACITY)
no_eth_hybrid_at20=capacity_pack(y_test,hybrid_score_no_ethnicity,PRIMARY_CAPACITY)
primary_effect_no_ethnicity=paired_capacity_bootstrap(y_test,probabilities['xgboost_raw'],hybrid_score_no_ethnicity)
primary_effect_no_ethnicity.update({'baseline_sensitivity':no_eth_base_at20['sensitivity'],'hybrid_sensitivity':no_eth_hybrid_at20['sensitivity'],
                                    'baseline_positive_found':no_eth_base_at20['positive_found'],'hybrid_positive_found':no_eth_hybrid_at20['positive_found'],
                                    'capacity':PRIMARY_CAPACITY})
print('Primary endpoint after removing the higher-risk ethnicity rule flag. Stored difference = ML-only minus hybrid:',
      primary_effect_no_ethnicity)

# E3, exploratory: does the knowledge layer change ranking metrics, and does it help one family more?
paired_effects = {
    'logistic_ontology_vs_raw_auprc': paired_metric_bootstrap(y_test, probabilities['logistic_ontology'], probabilities['logistic_raw'], 'auprc'),
    'logistic_ontology_vs_raw_auroc': paired_metric_bootstrap(y_test, probabilities['logistic_ontology'], probabilities['logistic_raw'], 'auroc'),
    'xgboost_ontology_vs_raw_auprc': paired_metric_bootstrap(y_test, probabilities['xgboost_ontology'], probabilities['xgboost_raw'], 'auprc'),
    'xgboost_ontology_vs_raw_auroc': paired_metric_bootstrap(y_test, probabilities['xgboost_ontology'], probabilities['xgboost_raw'], 'auroc'),
    'logistic_ontology_vs_raw_sens20': paired_capacity_bootstrap(y_test, probabilities['logistic_ontology'], probabilities['logistic_raw']),
    'xgboost_ontology_vs_raw_sens20': paired_capacity_bootstrap(y_test, probabilities['xgboost_ontology'], probabilities['xgboost_raw']),
    'xgboost_ontology_no_ethnicity_vs_raw_sens20': paired_capacity_bootstrap(y_test, probabilities['xgboost_ontology_no_ethnicity'], probabilities['xgboost_raw']),
}
MDE_KEY_FOR = {
    'logistic_ontology_vs_raw_auprc': 'logistic_ontology_vs_raw',
    'logistic_ontology_vs_raw_auroc': 'logistic_ontology_vs_raw',
    'logistic_ontology_vs_raw_sens20': 'logistic_ontology_vs_raw',
    'xgboost_ontology_vs_raw_auprc': 'xgboost_ontology_vs_raw',
    'xgboost_ontology_vs_raw_auroc': 'xgboost_ontology_vs_raw',
    'xgboost_ontology_vs_raw_sens20': 'xgboost_ontology_vs_raw',
    'xgboost_ontology_no_ethnicity_vs_raw_sens20': 'xgboost_ontology_vs_raw',
}
for key, res in paired_effects.items():
    res['mde_95_from_historical_validation'] = MDE[MDE_KEY_FOR[key]]['mde_95']
    print(key, {k: round(v,4) if isinstance(v,float) else v for k,v in res.items() if k in ('difference','ci_low','ci_high','std_error','mde_95_from_historical_validation')})

# H3, exploratory: guideline disagreement vs a size-matched confidence-only review set.
ml_topk = np.argsort(-probabilities['xgboost_raw'], kind='mergesort')[:base_at20['n_selected']]
rule_topk = np.argsort(-np.nan_to_num(test_rule_score, nan=-np.inf), kind='mergesort')[:base_at20['n_selected']]
in_ml = np.zeros(len(y_test), dtype=bool); in_ml[ml_topk] = True
in_rule = np.zeros(len(y_test), dtype=bool); in_rule[rule_topk] = True
disagreement = in_ml ^ in_rule
cutoff = float(np.sort(probabilities['xgboost_raw'])[::-1][base_at20['n_selected']-1])
confidence_rank = np.argsort(np.abs(probabilities['xgboost_raw'] - cutoff), kind='mergesort')[:int(disagreement.sum())]
review_summary = {
    'capacity': PRIMARY_CAPACITY,
    'ml_rule_overlap': int((in_ml & in_rule).sum()),
    'disagreement_set_size': int(disagreement.sum()),
    'disagreement_positives': int(y_test[disagreement].sum()),
    'disagreement_precision': float(y_test[disagreement].mean()) if disagreement.any() else None,
    'ml_set_positives': int(y_test[in_ml].sum()),
    'rule_set_positives': int(y_test[in_rule].sum()),
    'confidence_review_size': int(len(confidence_rank)),
    'confidence_review_positives': int(y_test[confidence_rank].sum()),
    'confidence_review_precision': float(y_test[confidence_rank].mean()) if len(confidence_rank) else None,
    'prevalence': float(y_test.mean()),
}
print('Disagreement vs size-matched confidence-only review:', review_summary)

# Exploratory subgroup summary at 20% capacity for the two headline policies.
def subgroup_rows(df, scores_dict):
    rows=[]
    age = pd.to_numeric(df['age_years'], errors='coerce')
    sex = pd.to_numeric(df['sex_code'], errors='coerce')
    race = pd.to_numeric(df['race_ethnicity_code'], errors='coerce')
    groups = {
        'all': np.ones(len(df), dtype=bool),
        'age_18_39': (age < 40), 'age_40_59': ((age >= 40) & (age < 60)), 'age_60_plus': (age >= 60),
        'female': (sex == 2), 'male': (sex == 1),
        'hispanic': race.isin([1, 2]), 'nh_black': (race == 4), 'nh_white': (race == 3), 'nh_asian': (race == 6),
    }
    for gname, mask in groups.items():
        mask = pd.Series(np.asarray(mask)).fillna(False).to_numpy().astype(bool)
        if mask.sum() < 50 or y_test[mask].sum() < 10:
            continue
        for pname, score in scores_dict.items():
            cap = capacity_pack(y_test[mask], score[mask], PRIMARY_CAPACITY)
            rows.append({'subgroup': gname, 'policy': pname, 'n': int(mask.sum()), 'positive_total': cap['positive_total'],
                         'prevalence': cap['prevalence'], 'sensitivity': cap['sensitivity'], 'precision': cap['precision']})
    return pd.DataFrame(rows)

subgroup_df = subgroup_rows(temporal_test, {'XGBoost raw': probabilities['xgboost_raw'], 'XGBoost + ontology features': probabilities['xgboost_ontology']})
print('\nSubgroup summary at 20% capacity (exploratory; only groups with >=50 participants and >=10 positives):')
display(subgroup_df)
