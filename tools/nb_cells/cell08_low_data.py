# E1 (plan addendum §3): low-data learning curve. Exploratory; reported whatever direction it takes.
e1_rows = []
for frac in LOW_DATA_FRACTIONS:
    if frac >= 1.0:
        splits = [(np.arange(len(y_all)), None)]
    else:
        sss = StratifiedShuffleSplit(n_splits=LOW_DATA_REPEATS, train_size=frac, random_state=42)
        splits = list(sss.split(hist_raw, y_all))
    for rep_idx, (sub_idx, _) in enumerate(splits):
        y_sub = y_all[sub_idx]
        for family, features_df, feature_sets in [
            ('logistic', hist_raw, {'raw': RAW_FEATURES, 'ontology': RAW_FEATURES + ONTOLOGY_FEATURES}),
            ('xgboost', hist_raw, {'raw': RAW_FEATURES, 'ontology': RAW_FEATURES + ONTOLOGY_FEATURES}),
        ]:
            for set_name, cols in feature_sets.items():
                if set_name == 'raw':
                    X_sub = hist_raw.iloc[sub_idx][cols]; X_full_test = test_raw[cols]
                else:
                    X_sub = hist_onto.iloc[sub_idx][cols]; X_full_test = test_onto[cols]
                pipe = make_pipeline(family, cols, seed=42, params=best_params['xgboost_raw' if family=='xgboost' else 'logistic_raw'])
                pipe.fit(X_sub, y_sub)
                p = predict_prob(pipe, X_full_test)
                cls = metric_pack(y_test, p); cap = capacity_pack(y_test, p, PRIMARY_CAPACITY)
                e1_rows.append({'fraction': frac, 'repeat': rep_idx, 'model': family, 'feature_set': set_name,
                                'n_train': int(len(sub_idx)), 'test_auroc': cls['auroc'], 'test_auprc': cls['auprc'],
                                'test_brier': cls['brier'], 'cap_sensitivity': cap['sensitivity'],
                                'cap_precision': cap['precision']})
e1_df = pd.DataFrame(e1_rows)
e1_summary = e1_df.groupby(['fraction','model','feature_set']).agg(
    auprc_mean=('test_auprc','mean'), auprc_sd=('test_auprc','std'),
    auroc_mean=('test_auroc','mean'), auroc_sd=('test_auroc','std'),
    sens_mean=('cap_sensitivity','mean'), sens_sd=('cap_sensitivity','std'),
    n_train=('n_train','mean')).reset_index()
e1_wide = e1_summary.pivot_table(index=['fraction','model','n_train'], columns='feature_set',
                                 values=['auprc_mean','sens_mean'])
print('E1 low-data learning curve (mean over subsamples, locked temporal test):')
display(e1_wide.round(4))
e1_delta = e1_summary.pivot_table(index=['fraction','model'], columns='feature_set', values='auprc_mean')
e1_delta['auprc_delta_ontology_minus_raw'] = e1_delta['ontology'] - e1_delta['raw']
e1_sens_delta = e1_summary.pivot_table(index=['fraction','model'], columns='feature_set', values='sens_mean')
e1_delta['sens20_delta_ontology_minus_raw'] = e1_sens_delta['ontology'] - e1_sens_delta['raw']
print('\nE1 gain from guideline features (positive = knowledge helped):')
display(e1_delta.round(4))
e1_df.to_csv(ARTIFACT_DIR/'e1_low_data_results.csv', index=False)
e1_summary.to_csv(ARTIFACT_DIR/'e1_low_data_summary.csv', index=False)
