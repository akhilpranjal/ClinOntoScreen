import json
import pandas as pd

pd.set_option('display.width', 200)
r = json.load(open('artifacts/research_results.json', encoding='utf-8'))

print('== HISTORICAL VALIDATION ==')
print(pd.read_csv('artifacts/historical_validation_metrics.csv').round(4).to_string())
print('== COMPOSITION ==')
print(pd.read_csv('artifacts/cohort_composition.csv').round(3).to_string())
print('== MODEL TABLE (ensemble + brier) ==')
rows = []
for k, v in r['models'].items():
    e = v['ensemble']
    rows.append({'model': k, 'auroc': e['auroc'], 'auprc': e['auprc'], 'brier': e['brier'],
                 'auroc_sd': v['auroc_sd'], 'auprc_sd': v['auprc_sd'], 'params': str(v['cv_best_params'])})
print(pd.DataFrame(rows).round(4).to_string())
print('== SUBGROUPS ==')
print(pd.DataFrame(r['subgroups']).round(4).to_string())
print('== E1 DELTA (ontology - raw) ==')
e1 = pd.DataFrame(r['e1'])
piv = e1.pivot_table(index=['fraction', 'model'], columns='feature_set', values=['auprc_mean', 'sens_mean'])
d = pd.DataFrame({'d_auprc': piv['auprc_mean']['ontology'] - piv['auprc_mean']['raw'],
                  'd_sens20': piv['sens_mean']['ontology'] - piv['sens_mean']['raw']})
print(d.round(4).to_string())
print('== CAPACITY 10/30 for LR-onto and XGB-raw and published ==')
for p in ['XGBoost raw', 'Logistic raw', 'Logistic + ontology features', 'Ontology-only rule score',
          'CDC/ADA prediabetes risk test (published score)']:
    for pack in r['capacity_metrics'][p]:
        print(f"{p:52s} cap {pack['capacity']:.0%} sens {pack['sensitivity']:.3f} ppv {pack['precision']:.3f} "
              f"lift {pack['lift']:.2f} found {pack['positive_found']}/{pack['positive_total']} frac {pack['fraction_of_ceiling']:.3f}")
print('== E2 delta 0 -> 0.3 ==')
e2 = pd.DataFrame(r['e2'])
print(e2.pivot_table(index='model', columns='mask_rate', values=['auprc_mean', 'sens_mean']).round(4).to_string())
print('== DATA QC missingness (temporal, top) ==')
qc = json.load(open('artifacts/data_qc.json', encoding='utf-8'))
mf = qc['temporal_missing_fraction']
print(pd.Series(mf).sort_values(ascending=False).round(3).to_string())
print('unharmonized:', qc['unharmonized_variables'])
