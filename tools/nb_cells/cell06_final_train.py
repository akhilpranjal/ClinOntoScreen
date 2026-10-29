# Final training: refit selected configurations on all historical data across five seeds.
# The 2021–2023 temporal test is not used for selecting hyperparameters or alpha.
# LR and XGBoost defaults are deterministic; the seeds only affect XGBoost subsampling.
models = {name: [] for name in X_variants}
test_raw = temporal_test[RAW_FEATURES].copy()
test_onto = derive_ontology_features(test_raw)[RAW_FEATURES + ONTOLOGY_FEATURES].copy()
test_onto_no_ethnicity = derive_ontology_features(test_raw, include_ethnicity=False)[RAW_FEATURES + ONTOLOGY_FEATURES].copy()
test_manual = derive_manual_control(test_raw)[RAW_FEATURES + MANUAL_FEATURES].copy()
y_test = temporal_test['target'].astype(int).to_numpy()
X_hist_variants = {
    'logistic_raw': (hist_raw, RAW_FEATURES, 'logistic'),
    'xgboost_raw': (hist_raw, RAW_FEATURES, 'xgboost'),
    'logistic_ontology': (hist_onto, RAW_FEATURES+ONTOLOGY_FEATURES, 'logistic'),
    'xgboost_ontology': (hist_onto, RAW_FEATURES+ONTOLOGY_FEATURES, 'xgboost'),
    'xgboost_ontology_no_ethnicity': (hist_onto_no_ethnicity, RAW_FEATURES+ONTOLOGY_FEATURES, 'xgboost'),
    'xgboost_generic_control': (hist_manual, RAW_FEATURES+MANUAL_FEATURES, 'xgboost'),
}
for seed in SEEDS:
    print('Training seed', seed)
    for name, (X_train_full, features, family) in X_hist_variants.items():
        params = best_params[name]
        pipeline = make_pipeline(family, features, seed=seed, params=params)
        pipeline.fit(X_train_full[features], y_all)
        models[name].append(pipeline)

X_test_variants = {
    'logistic_raw': test_raw[RAW_FEATURES],
    'xgboost_raw': test_raw[RAW_FEATURES],
    'logistic_ontology': test_onto[RAW_FEATURES+ONTOLOGY_FEATURES],
    'xgboost_ontology': test_onto[RAW_FEATURES+ONTOLOGY_FEATURES],
    'xgboost_ontology_no_ethnicity': test_onto_no_ethnicity[RAW_FEATURES+ONTOLOGY_FEATURES],
    'xgboost_generic_control': test_manual[RAW_FEATURES+MANUAL_FEATURES],
}
probabilities = {name: np.mean(np.vstack([predict_prob(m, X_test_variants[name]) for m in model_list]),axis=0) for name, model_list in models.items()}
metrics_by_model = {}
per_seed_metrics = {}
for name, model_list in models.items():
    seed_metrics=[metric_pack(y_test,predict_prob(model,X_test_variants[name])) for model in model_list]
    per_seed_metrics[name]=seed_metrics
    metrics_by_model[name]={}
    for metric in ['auroc','auprc','brier']:
        vals=np.asarray([m[metric] for m in seed_metrics],dtype=float)
        metrics_by_model[name][metric+'_mean']=float(np.nanmean(vals))
        metrics_by_model[name][metric+'_sd']=float(np.nanstd(vals,ddof=1))
    metrics_by_model[name]['ensemble'] = metric_pack(y_test, probabilities[name])
    metrics_by_model[name]['cv_best_params'] = best_params[name]

display(pd.DataFrame([{ 'model':k, **{m:v for m,v in val.items() if m.endswith('_mean') or m.endswith('_sd')} } for k,val in metrics_by_model.items()]))
print('Temporal test participants:',len(y_test),'| positive cases:',int(y_test.sum()),'| prevalence:',round(float(y_test.mean()),4))
print('Ontology rule coverage on the temporal test cohort:',
      {'eligible': float(test_onto['onto_screening_eligible'].mean(skipna=True)),
       'not_assessable_fraction': float(test_onto['onto_screening_eligible'].isna().mean()),
       'criteria_missing_mean': float(test_onto['onto_criteria_missing_count'].mean())})
