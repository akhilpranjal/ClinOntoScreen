# Published-knowledge baseline (plan addendum §5): the official CDC/ADA prediabetes risk test.
# Scoring source: CDC/ADA Prediabetes Risk Test (adapted from Bang et al., Ann Intern Med 2009).
# Items unavailable in the harmonized NHANES files are scored 0 and listed, never silently replaced.
val_published_score = cdc_ada_risk_score(historical.iloc[val_idx]).to_numpy(dtype=float)

def score_metrics(y, score):
    y = np.asarray(y, dtype=int); s = np.asarray(score, dtype=float)
    # The published risk test is a point total, not a probability: Brier is undefined for it.
    return {'n': int(len(y)), 'positive_count': int(y.sum()), 'prevalence': float(y.mean()),
            'auroc': float(roc_auc_score(y, s)), 'auprc': float(average_precision_score(y, s)),
            'brier': None, 'note': 'point total, not a probability; Brier not reported'}

published_rows = [
    {'cohort': 'historical_validation', **score_metrics(y_val, val_published_score)},
    {'cohort': 'temporal_test', **score_metrics(y_test, published_score)},
]
for capacity in CAPACITIES:
    published_rows.append({'cohort': 'temporal_test', 'capacity': capacity, **capacity_pack(y_test, published_score, capacity)})
published_df = pd.DataFrame(published_rows)
print('CDC/ADA published risk test, mapped to NHANES (unavailable items scored 0):')
display(published_df.round(4))
print('Unavailable items in the mapping:', CDC_ADA_UNAVAILABLE_ITEMS)
print('High-risk threshold on the published scale is a total score >= 5; the ranking analysis uses the raw point total.')
high_risk = (published_score >= 5).astype(int)
print('Temporal test at the published >=5 threshold:',
      {'n_flagged': int(high_risk.sum()), 'positives_captured': int(y_test[high_risk].sum()),
       'precision': float(y_test[high_risk].mean()) if high_risk.any() else None,
       'sensitivity': float(y_test[high_risk].sum() / max(1, y_test.sum()))})
published_df.to_csv(ARTIFACT_DIR/'published_score_baseline.csv', index=False)
