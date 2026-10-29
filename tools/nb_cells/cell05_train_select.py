# Model pipelines. All transforms are fitted inside each pipeline, so nothing is learned from the test cycle.
def one_hot_encoder():
    try: return OneHotEncoder(handle_unknown='ignore', sparse_output=True)
    except TypeError: return OneHotEncoder(handle_unknown='ignore', sparse=True)

def make_preprocessor(features):
    numeric_cols = [c for c in features if c in RAW_NUMERIC or c.startswith('onto_') or c.startswith('manual_')]
    categorical_cols = [c for c in features if c not in numeric_cols]
    steps=[]
    if numeric_cols:
        steps.append(('numeric', Pipeline([('imputer',SimpleImputer(strategy='median',add_indicator=True)),('scale',StandardScaler())]), numeric_cols))
    if categorical_cols:
        steps.append(('categorical', Pipeline([('imputer',SimpleImputer(strategy='most_frequent')),('onehot',one_hot_encoder())]), categorical_cols))
    return ColumnTransformer(steps, remainder='drop', verbose_feature_names_out=False)

def make_pipeline(model_name, features, seed=42, params=None):
    params = dict(params or {})
    if model_name == 'logistic':
        base = {'C':1.0, 'max_iter':3000, 'solver':'lbfgs', 'random_state':seed}; base.update(params)
        estimator = LogisticRegression(**base)
    elif model_name == 'xgboost':
        base = {'n_estimators':250,'max_depth':3,'learning_rate':0.05,'subsample':0.85,'colsample_bytree':0.85,'reg_lambda':1.0,'min_child_weight':3,'eval_metric':'logloss','n_jobs':2,'random_state':seed,'tree_method':'hist'}; base.update(params)
        estimator = XGBClassifier(**base)
    else:
        raise ValueError(model_name)
    return Pipeline([('preprocess',make_preprocessor(features)),('model',estimator)])

def predict_prob(model, X): return np.asarray(model.predict_proba(X)[:,1],dtype=float)

# Independent historical validation is used for model/policy selection. The later cycle remains locked.
hist_raw = historical[RAW_FEATURES].copy()
hist_onto = derive_ontology_features(hist_raw)[RAW_FEATURES + ONTOLOGY_FEATURES].copy()
hist_onto_no_ethnicity = derive_ontology_features(hist_raw, include_ethnicity=False)[RAW_FEATURES + ONTOLOGY_FEATURES].copy()
hist_manual = derive_manual_control(hist_raw)[RAW_FEATURES + MANUAL_FEATURES].copy()
# Exact equivalence of values between ontology-derived and independently coded control features is expected.
for of, mf in zip(ONTOLOGY_FEATURES, MANUAL_FEATURES):
    a = hist_onto[of].to_numpy(dtype=float); b = hist_manual[mf].to_numpy(dtype=float)
    assert np.allclose(a, b, equal_nan=True), f'Feature control mismatch: {of} vs {mf}'
print('Generic feature-engineering control matches the same rule values independently.')
print('Ontology rule coverage on historical data:',
      {'eligible': float(hist_onto['onto_screening_eligible'].mean()),
       'criteria_missing_mean': float(hist_onto['onto_criteria_missing_count'].mean()),
       'fully_assessable': float((hist_onto['onto_criteria_missing_count']==0).mean())})

train_idx, val_idx = train_test_split(np.arange(len(historical)), test_size=0.20, random_state=42, stratify=historical['target'])
y_all = historical['target'].astype(int).to_numpy()
y_train, y_val = y_all[train_idx], y_all[val_idx]
X_variants = {
    'logistic_raw': (hist_raw, RAW_FEATURES, 'logistic'),
    'xgboost_raw': (hist_raw, RAW_FEATURES, 'xgboost'),
    'logistic_ontology': (hist_onto, RAW_FEATURES+ONTOLOGY_FEATURES, 'logistic'),
    'xgboost_ontology': (hist_onto, RAW_FEATURES+ONTOLOGY_FEATURES, 'xgboost'),
    'xgboost_ontology_no_ethnicity': (hist_onto_no_ethnicity, RAW_FEATURES+ONTOLOGY_FEATURES, 'xgboost'),
    'xgboost_generic_control': (hist_manual, RAW_FEATURES+MANUAL_FEATURES, 'xgboost'),
}
param_grids = {
    'logistic': {'model__C':[0.1,1.0,10.0]},
    'xgboost': {'model__n_estimators':[150,300], 'model__max_depth':[2,3], 'model__learning_rate':[0.03,0.07]},
}
searches, best_params, validation_probabilities = {}, {}, {}
cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
for name, (X_all_variant, features, family) in X_variants.items():
    X_train = X_all_variant.iloc[train_idx][features]
    X_val = X_all_variant.iloc[val_idx][features]
    search = GridSearchCV(make_pipeline(family,features,seed=42), param_grids[family], scoring='average_precision', cv=cv, n_jobs=1, refit=True, verbose=0, return_train_score=False)
    search.fit(X_train, y_train)
    searches[name] = search
    best_params[name] = {key.replace('model__',''): value for key,value in search.best_params_.items()}
    validation_probabilities[name] = predict_prob(search.best_estimator_, X_val)
    print(name, '| best CV AUPRC:', round(float(search.best_score_),4), '| params:', best_params[name])

# Historical-only sanity check (plan addendum §2): no later-cycle data are touched here.
print('\nHistorical validation metrics (sanity check, never a test-set gate):')
val_metrics = pd.DataFrame([{'model':name, **metric_pack(y_val, p)} for name,p in validation_probabilities.items()])
display(val_metrics)
val_metrics.to_csv(ARTIFACT_DIR/'historical_validation_metrics.csv', index=False)

val_onto = hist_onto.iloc[val_idx]
val_rule_score = val_onto['onto_rule_priority_score'].to_numpy(dtype=float)
alpha_candidates = [0.0,0.025,0.05,0.10,0.15,0.20,0.30]
alpha_results=[]
for alpha in alpha_candidates:
    result=capacity_pack(y_val, validation_probabilities['xgboost_raw'] + alpha*val_rule_score, PRIMARY_CAPACITY)
    alpha_results.append({'alpha':alpha,**result})
alpha_results=sorted(alpha_results,key=lambda r:(r['sensitivity'] if np.isfinite(r['sensitivity']) else -1,r['precision'] if np.isfinite(r['precision']) else -1,-r['alpha']),reverse=True)
HYBRID_ALPHA=float(alpha_results[0]['alpha'])
print('Historical validation selects hybrid alpha:', HYBRID_ALPHA)
display(pd.DataFrame(alpha_results))

# Prespecified race_ethnicity_ablation: remove only the higher-risk ethnicity risk-factor flag.
# The ADA BMI threshold adaptation for Asian ancestry remains in this specific ablation and is disclosed.
val_onto_no_ethnicity = hist_onto_no_ethnicity.iloc[val_idx]
val_rule_score_no_ethnicity = val_onto_no_ethnicity['onto_rule_priority_score'].to_numpy(dtype=float)
alpha_results_no_ethnicity=[]
for alpha in alpha_candidates:
    result=capacity_pack(y_val, validation_probabilities['xgboost_raw'] + alpha*val_rule_score_no_ethnicity, PRIMARY_CAPACITY)
    alpha_results_no_ethnicity.append({'alpha':alpha,**result})
alpha_results_no_ethnicity=sorted(alpha_results_no_ethnicity,key=lambda r:(r['sensitivity'] if np.isfinite(r['sensitivity']) else -1,r['precision'] if np.isfinite(r['precision']) else -1,-r['alpha']),reverse=True)
HYBRID_ALPHA_NO_ETHNICITY=float(alpha_results_no_ethnicity[0]['alpha'])
print('Historical validation selects no-higher-risk-ethnicity alpha:', HYBRID_ALPHA_NO_ETHNICITY)

# Smallest detectable difference on historical validation (plan addendum §7).
MDE = {}
MDE['primary_hybrid_vs_xgb_raw'] = paired_capacity_bootstrap(y_val, validation_probabilities['xgboost_raw'] + HYBRID_ALPHA*val_rule_score, validation_probabilities['xgboost_raw'])
MDE['logistic_ontology_vs_raw'] = paired_capacity_bootstrap(y_val, validation_probabilities['logistic_ontology'], validation_probabilities['logistic_raw'])
MDE['xgboost_ontology_vs_raw'] = paired_capacity_bootstrap(y_val, validation_probabilities['xgboost_ontology'], validation_probabilities['xgboost_raw'])
for key, res in MDE.items():
    res['mde_95'] = float(1.96 * res['std_error']) if np.isfinite(res.get('std_error', np.nan)) else float('nan')
    print(f"Validation MDE for {key}: SE={res['std_error']:.4f}, MDE95={res['mde_95']:.4f}, point={res['difference']:.4f}")
print('Effects smaller than the MDE are reported as below the resolution of this design.')
