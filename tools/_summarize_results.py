import json
import pandas as pd

r = json.load(open('artifacts/research_results.json', encoding='utf-8'))
print('== MODELS (temporal test) ==')
for k, v in r['models'].items():
    print(f"{k:32s} AUROC {v['auroc_mean']:.4f}+-{v['auroc_sd']:.4f}  AUPRC {v['auprc_mean']:.4f}+-{v['auprc_sd']:.4f}  ens_AUPRC {v['ensemble']['auprc']:.4f}")
print('== CAPACITY @20% ==')
for p, pk in r['capacity_metrics'].items():
    d = [x for x in pk if x['capacity'] == 0.2][0]
    print(f"{p:56s} sens {d['sensitivity']:.3f} ceiling {d['sensitivity_ceiling']:.3f} frac {d['fraction_of_ceiling']:.3f} ppv {d['precision']:.3f} lift {d['lift']:.2f}")
print('== PRIMARY H2 ==', {k: round(v, 4) for k, v in r['primary_effect'].items() if isinstance(v, float)})
print('== MDE ==', {k: round(v['mde_95'], 4) for k, v in r['mde'].items()})
print('== E1 ==')
print(pd.DataFrame(r['e1']).round(4).to_string())
print('== E2 ==')
print(pd.DataFrame(r['e2']).round(4).to_string())
print('== PUBLISHED ==')
print(pd.DataFrame(r['published_baseline']).round(4).to_string())
print('== REVIEW H3 ==', r['review_summary'])
print('== PAIRED E3 ==')
for k, v in r['paired_effects'].items():
    print(f"{k:44s} diff {v['difference']:+.4f} CI [{v['ci_low']:+.4f},{v['ci_high']:+.4f}]")
