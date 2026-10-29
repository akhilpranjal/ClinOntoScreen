# Persist research artifacts and provenance.
import pandas as pd
research_results = {
    'protocol': {**PROTOCOL, 'python': platform.python_version(), 'pandas': pd.__version__,
                 'sklearn': __import__('sklearn').__version__, 'xgboost': __import__('xgboost').__version__,
                 'rdflib': __import__('rdflib').__version__, 'seeds': SEEDS,
                 'primary_capacity': PRIMARY_CAPACITY, 'n_bootstrap': N_BOOTSTRAP,
                 'hybrid_alpha': HYBRID_ALPHA, 'hybrid_alpha_no_ethnicity': HYBRID_ALPHA_NO_ETHNICITY,
                 'hybrid_alpha_candidates': alpha_results,
                 'cdc_ada_unavailable_items': CDC_ADA_UNAVAILABLE_ITEMS,
                 'rule_sections': RULE_SECTIONS},
    'data': {'cohort_flow': COHORT_FLOW, 'qc': cohort_qc, 'composition': composition_df.to_dict('records')},
    'models': metrics_by_model, 'best_params': best_params,
    'capacity_metrics': {policy: [capacity_pack(y_test, score, c) for c in CAPACITIES] for policy, score in policy_scores.items()},
    'primary_effect': primary_effect, 'primary_effect_no_ethnicity': primary_effect_no_ethnicity,
    'paired_effects': paired_effects, 'mde': MDE,
    'review_summary': review_summary, 'subgroups': subgroup_df.to_dict('records'),
    'e1': e1_summary.to_dict('records'), 'e2': e2_summary.to_dict('records'),
    'published_baseline': published_df.to_dict('records'),
    'test_n': int(len(y_test)), 'test_positive_count': int(y_test.sum()), 'test_prevalence': float(y_test.mean()),
    'historical_n': int(len(historical)), 'historical_prevalence': float(historical['target'].mean()),
    'feature_names': {'raw': RAW_FEATURES, 'ontology': ONTOLOGY_FEATURES, 'manual': MANUAL_FEATURES},
}
(ARTIFACT_DIR / 'research_results.json').write_text(json.dumps(research_results, indent=2, default=str), encoding='utf-8')

feature_manifest = {
    'raw_numeric': RAW_NUMERIC, 'raw_categorical': RAW_CATEGORICAL, 'raw_features': RAW_FEATURES,
    'ontology_features': ONTOLOGY_FEATURES, 'manual_features': MANUAL_FEATURES,
    'forbidden_tokens': list(FORBIDDEN_FEATURE_TOKENS),
    'unharmonized_variables': unharmonized,
}
(ARTIFACT_DIR / 'feature_manifest.json').write_text(json.dumps(feature_manifest, indent=2), encoding='utf-8')

test_predictions = temporal_test[['SEQN']].copy()
test_predictions['target'] = y_test
test_predictions['hba1c_percent'] = pd.to_numeric(temporal_test['hba1c_percent'], errors='coerce')
for name, p in probabilities.items():
    test_predictions[name] = p
test_predictions['hybrid_score'] = hybrid_score
test_predictions['hybrid_score_no_ethnicity'] = hybrid_score_no_ethnicity
test_predictions['cdc_ada_score'] = published_score
test_predictions['onto_rule_priority_score'] = test_rule_score
test_predictions['disagreement_review'] = disagreement
test_predictions.to_csv(ARTIFACT_DIR / 'test_predictions.csv', index=False)

bundle = {'models': models, 'best_params': best_params, 'hybrid_alpha': HYBRID_ALPHA,
          'hybrid_alpha_no_ethnicity': HYBRID_ALPHA_NO_ETHNICITY, 'raw_features': RAW_FEATURES,
          'ontology_features': ONTOLOGY_FEATURES, 'manual_features': MANUAL_FEATURES,
          'ontology_ttl': ontology_path.read_text(encoding='utf-8') if ontology_path else ONTOLOGY_TTL_EMBEDDED,
          'cdc_ada_unavailable_items': CDC_ADA_UNAVAILABLE_ITEMS}
joblib.dump(bundle, ARTIFACT_DIR / 'model_bundle.joblib')

run_manifest = {
    'protocol': PROTOCOL, 'artifact_dir': str(ARTIFACT_DIR),
    'figure_paths': figure_paths,
    'csv_paths': [str(p) for p in sorted(ARTIFACT_DIR.glob('*.csv'))],
    'json_paths': [str(p) for p in sorted(ARTIFACT_DIR.glob('*.json'))],
    'generated_utc': datetime.now(timezone.utc).isoformat(),
}
(ARTIFACT_DIR / 'run_manifest.json').write_text(json.dumps(run_manifest, indent=2, default=str), encoding='utf-8')

zip_path = ARTIFACT_DIR / 'clinontoscreen_artifacts.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for path in sorted(ARTIFACT_DIR.rglob('*')):
        if path.is_file() and path != zip_path:
            zf.write(path, path.relative_to(ARTIFACT_DIR))
print('Artifacts written to', ARTIFACT_DIR)
for path in sorted(ARTIFACT_DIR.rglob('*')):
    if path.is_file():
        print(' ', path.relative_to(ARTIFACT_DIR), f'{path.stat().st_size/1024:.1f} KB')
