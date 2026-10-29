# Metric helpers. Capacity metrics report the prevalence ceiling required by plan addendum §4.
def metric_pack(y, p):
    y=np.asarray(y,dtype=int); p=np.asarray(p,dtype=float)
    return {'n':int(len(y)),'positive_count':int(y.sum()),'prevalence':float(y.mean()),
            'auroc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else np.nan,
            'auprc':float(average_precision_score(y,p)) if len(np.unique(y))==2 else np.nan,
            'brier':float(brier_score_loss(y,p))}

def capacity_pack(y, score, capacity):
    y=np.asarray(y,dtype=int); score=np.asarray(score,dtype=float)
    n=max(1,int(np.ceil(len(y)*capacity)))
    idx=np.argsort(-np.nan_to_num(score,nan=-np.inf),kind='mergesort')[:n]
    found=int(y[idx].sum()); pos=int(y.sum())
    prevalence=float(y.mean()) if len(y) else float('nan')
    ceiling=min(1.0, capacity/prevalence) if prevalence>0 else float('nan')
    sensitivity=float(found/pos) if pos else float('nan')
    ppv=float(found/n)
    return {'capacity':float(capacity),'n_total':int(len(y)),'n_selected':int(n),'positive_total':pos,'positive_found':found,
            'prevalence':prevalence,'sensitivity':sensitivity,'sensitivity_ceiling':ceiling,
            'fraction_of_ceiling':float(sensitivity/ceiling) if ceiling>0 else float('nan'),
            'precision':ppv,'ppv':ppv,'lift':float(ppv/prevalence) if prevalence>0 else float('nan'),
            'false_referrals':int(n-found)}

def paired_capacity_bootstrap(y, score_a, score_b, capacity=PRIMARY_CAPACITY, n_bootstrap=N_BOOTSTRAP, seed=2026):
    """Participant bootstrap for sensitivity(score_a) - sensitivity(score_b) at a fixed capacity."""
    y=np.asarray(y,dtype=int); sa=np.asarray(score_a,dtype=float); sb=np.asarray(score_b,dtype=float)
    rng=np.random.default_rng(seed); diffs=[]; attempts=0
    while len(diffs)<n_bootstrap and attempts < n_bootstrap*3:
        attempts += 1
        idx=rng.integers(0,len(y),size=len(y))
        yb=y[idx]
        if yb.sum()==0: continue
        n=max(1,int(np.ceil(len(yb)*capacity)))
        a=float(yb[np.argsort(-np.nan_to_num(sa[idx],nan=-np.inf),kind='mergesort')[:n]].sum()/yb.sum())
        b=float(yb[np.argsort(-np.nan_to_num(sb[idx],nan=-np.inf),kind='mergesort')[:n]].sum()/yb.sum())
        diffs.append(a-b)
    point_a=capacity_pack(y,sa,capacity)['sensitivity']; point_b=capacity_pack(y,sb,capacity)['sensitivity']
    if not diffs:
        return {'difference':point_a-point_b,'ci_low':float('nan'),'ci_high':float('nan'),'std_error':float('nan'),'n_bootstrap':0}
    arr=np.array(diffs)
    return {'difference':float(point_a-point_b),'ci_low':float(np.quantile(arr,.025)),'ci_high':float(np.quantile(arr,.975)),
            'std_error':float(np.std(arr,ddof=1)),'n_bootstrap':len(diffs)}

def paired_metric_bootstrap(y, p_a, p_b, metric='auprc', n_bootstrap=N_BOOTSTRAP, seed=2026):
    y=np.asarray(y,dtype=int); pa=np.asarray(p_a,dtype=float); pb=np.asarray(p_b,dtype=float)
    fn = average_precision_score if metric=='auprc' else roc_auc_score
    rng=np.random.default_rng(seed); diffs=[]; attempts=0
    while len(diffs)<n_bootstrap and attempts<n_bootstrap*3:
        attempts+=1
        idx=rng.integers(0,len(y),size=len(y))
        if len(np.unique(y[idx]))<2: continue
        diffs.append(float(fn(y[idx],pa[idx])-fn(y[idx],pb[idx])))
    arr=np.array(diffs) if diffs else np.array([np.nan])
    return {'metric':metric,'difference':float(fn(y,pa)-fn(y,pb)),
            'ci_low':float(np.nanquantile(arr,.025)),'ci_high':float(np.nanquantile(arr,.975)),
            'std_error':float(np.nanstd(arr,ddof=1)),'n_bootstrap':int(len(diffs))}

# Data quality, cohort flow, missingness and leakage contract.
for label, df in [('historical', historical), ('temporal_test', temporal_test)]:
    print(f"\n{label}: n={len(df):,}; positives={int(df['target'].sum()):,}; prevalence={df['target'].mean():.3f}; diabetes-range secondary positives={int(df['target_diabetes_range'].sum()):,}")
    display(df[RAW_FEATURES].isna().mean().sort_values(ascending=False).rename('missing_fraction').to_frame().head(12))

# Cycle-level availability of every requested source variable, so harmonization gaps are visible.
availability_rows=[]
for period, report in [('historical', historical_report), ('temporal_test', temporal_report)]:
    for stem, missing in report['missing_variables'].items():
        for var in FILE_VARIABLES[stem]:
            availability_rows.append({'period':period,'file':stem,'variable':var,'available':var not in missing})
availability_df = pd.DataFrame(availability_rows).pivot_table(index='variable', columns='period', values='available', aggfunc='first')
availability_df = availability_df.reindex(columns=['historical', 'temporal_test']).fillna(False)
availability_df['harmonized'] = availability_df[['historical', 'temporal_test']].all(axis=1)
print('\nSource-variable availability by period (variables not in both periods are excluded from the model schema):')
display(availability_df.sort_values('harmonized'))
unharmonized = sorted(availability_df.index[~availability_df['harmonized']].astype(str))

capacity_ceiling = {}
for capacity in CAPACITIES:
    ceiling = min(1.0, capacity / float(historical['target'].mean()))
    capacity_ceiling[capacity] = {'historical_prevalence':float(historical['target'].mean()), 'sensitivity_ceiling':ceiling}
print('\nHistorical prevalence and the maximum sensitivity each capacity can reach:')
print(pd.DataFrame(capacity_ceiling).T)
if float(historical['target'].mean()) > PRIMARY_CAPACITY:
    print(f'Historical prevalence ({historical["target"].mean():.3f}) exceeds the {PRIMARY_CAPACITY:.0%} budget, so the primary endpoint is reported as the fraction of the {capacity_ceiling[PRIMARY_CAPACITY]["sensitivity_ceiling"]:.3f} ceiling achieved.')

cohort_qc = {
    'historical_n': int(len(historical)), 'historical_positive_count': int(historical['target'].sum()),
    'historical_prevalence': float(historical['target'].mean()),
    'temporal_test_n': int(len(temporal_test)), 'temporal_test_positive_count': int(temporal_test['target'].sum()),
    'temporal_test_prevalence': float(temporal_test['target'].mean()),
    'cohort_flow': COHORT_FLOW,
    'capacity_ceiling': capacity_ceiling,
    'unharmonized_variables': unharmonized,
    'historical_missing_fraction': historical[RAW_FEATURES].isna().mean().to_dict(),
    'temporal_missing_fraction': temporal_test[RAW_FEATURES].isna().mean().to_dict(),
    'historical_source_report': historical_report, 'temporal_source_report': temporal_report,
}
(ARTIFACT_DIR / 'data_qc.json').write_text(json.dumps(cohort_qc, indent=2, default=str), encoding='utf-8')

# Descriptive composition by period (selection and measurement caveats, plan addendum §7).
def composition(df, label):
    age = pd.to_numeric(df['age_years'], errors='coerce')
    return {
        'period': label, 'n': int(len(df)),
        'mean_age': float(age.mean()), 'pct_age_18_39': float((age<40).mean()), 'pct_age_40_59': float(((age>=40)&(age<60)).mean()), 'pct_age_60_plus': float((age>=60).mean()),
        'pct_male': float((pd.to_numeric(df['sex_code'],errors='coerce')==1).mean()),
        'pct_nh_black': float((pd.to_numeric(df['race_ethnicity_code'],errors='coerce')==4).mean()),
        'pct_nh_asian': float((pd.to_numeric(df['race_ethnicity_code'],errors='coerce')==6).mean()),
        'pct_hispanic': float(pd.to_numeric(df['race_ethnicity_code'],errors='coerce').isin([1,2]).mean()),
        'prevalence': float(df['target'].mean()),
    }
composition_df = pd.DataFrame([composition(historical,'historical'), composition(temporal_test,'temporal_test')])
print('\nCohort composition by period:')
display(composition_df)
composition_df.to_csv(ARTIFACT_DIR/'cohort_composition.csv', index=False)

for col in RAW_FEATURES:
    assert col not in {'SEQN','target','target_diabetes_range','hba1c_percent','reported_diabetes','reported_prediabetes'}
assert not any(any(token in col.lower() for token in FORBIDDEN_FEATURE_TOKENS) for col in RAW_FEATURES)
assert 'SEQN' not in RAW_FEATURES
print('Leakage contract passed. The cohort labels come from HbA1c; target-source fields are not model features.')

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
axes[0].bar(['Historical','Temporal test'], [historical['target'].mean(), temporal_test['target'].mean()])
axes[0].set_title('Primary outcome prevalence'); axes[0].set_ylabel('Fraction positive'); axes[0].set_ylim(0,1)
axes[1].hist(historical['age_years'].dropna(), bins=20, alpha=0.6, label='Historical')
axes[1].hist(temporal_test['age_years'].dropna(), bins=20, alpha=0.6, label='Temporal test')
axes[1].set_title('Age distribution'); axes[1].set_xlabel('Age (NHANES top-codes 80+)'); axes[1].legend()
flow_labels = list(COHORT_FLOW['historical'].keys())
axes[2].plot(flow_labels, [COHORT_FLOW['historical'][k] for k in flow_labels], marker='o', label='Historical')
axes[2].plot(flow_labels, [COHORT_FLOW['temporal_test'][k] for k in flow_labels], marker='o', label='Temporal test')
axes[2].set_title('Cohort flow'); axes[2].tick_params(axis='x', rotation=45); axes[2].legend(); axes[2].grid(alpha=.3)
plt.tight_layout(); plt.show()
