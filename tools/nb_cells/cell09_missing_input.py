# E2 (plan addendum §3): missing-input stress test. Exploratory.
# Masked inputs are re-derived into ontology features, so the rule layer never sees information
# the ML system does not receive; the executor reports criteria that are not assessable instead of guessing.
e2_rows = []
not_assessable_by_rate = {}
for rate in MASK_RATES:
    for rep in range(MASK_REPEATS):
        rng = np.random.default_rng(42 + rep)
        masked_raw = test_raw.copy()
        if rate > 0:
            for col in MASK_COLUMNS:
                if col in masked_raw.columns:
                    drop = rng.random(len(masked_raw)) < rate
                    masked_raw.loc[drop, col] = np.nan
        masked_onto = derive_ontology_features(masked_raw)[RAW_FEATURES + ONTOLOGY_FEATURES]
        not_assessable = float(masked_onto['onto_screening_eligible'].isna().mean())
        not_assessable_by_rate.setdefault(rate, []).append(not_assessable)
        variants = {
            'logistic_raw': (masked_raw[RAW_FEATURES], 'logistic'),
            'logistic_ontology': (masked_onto[RAW_FEATURES + ONTOLOGY_FEATURES], 'logistic'),
            'xgboost_raw': (masked_raw[RAW_FEATURES], 'xgboost'),
            'xgboost_ontology': (masked_onto[RAW_FEATURES + ONTOLOGY_FEATURES], 'xgboost'),
        }
        probs = {}
        for name, (X_m, family) in variants.items():
            probs[name] = np.mean(np.vstack([predict_prob(m, X_m) for m in models[name]]), axis=0)
        probs['xgboost_ontology_policy'] = probs['xgboost_raw'] + HYBRID_ALPHA * masked_onto['onto_rule_priority_score'].to_numpy(dtype=float)
        for name, p in probs.items():
            cls = metric_pack(y_test, p); cap = capacity_pack(y_test, p, PRIMARY_CAPACITY)
            e2_rows.append({'mask_rate': rate, 'repeat': rep, 'model': name, 'not_assessable_fraction': not_assessable,
                            'test_auroc': cls['auroc'], 'test_auprc': cls['auprc'], 'test_brier': cls['brier'],
                            'cap_sensitivity': cap['sensitivity'], 'cap_precision': cap['precision']})
e2_df = pd.DataFrame(e2_rows)
e2_summary = e2_df.groupby(['mask_rate','model']).agg(
    auprc_mean=('test_auprc','mean'), auprc_sd=('test_auprc','std'),
    auroc_mean=('test_auroc','mean'), brier_mean=('test_brier','mean'),
    sens_mean=('cap_sensitivity','mean'), sens_sd=('cap_sensitivity','std'),
    not_assessable_mean=('not_assessable_fraction','mean')).reset_index()
print('E2 missing-input stress test (mean over masked repeats):')
display(e2_summary.round(4))
e2_pivot = e2_summary.pivot_table(index=['mask_rate','model'], values=['auprc_mean','sens_mean'])
print('\nE2 degradation relative to the unmasked run:')
base = e2_summary[e2_summary['mask_rate']==0.0].set_index('model')
degraded = e2_summary.copy()
degraded['auprc_change_vs_unmasked'] = degraded['auprc_mean'] - degraded['model'].map(base['auprc_mean'])
degraded['sens_change_vs_unmasked'] = degraded['sens_mean'] - degraded['model'].map(base['sens_mean'])
display(degraded[['mask_rate','model','auprc_mean','auprc_change_vs_unmasked','sens_mean','sens_change_vs_unmasked','not_assessable_mean']].round(4))
e2_df.to_csv(ARTIFACT_DIR/'e2_missing_input_results.csv', index=False)
e2_summary.to_csv(ARTIFACT_DIR/'e2_missing_input_summary.csv', index=False)
json.dump({str(k): v for k, v in not_assessable_by_rate.items()}, open(ARTIFACT_DIR/'e2_not_assessable_rates.json','w'), indent=2)
