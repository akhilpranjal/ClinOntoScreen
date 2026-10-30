# Figures and tables register

Every empirical figure must be generated from saved artifacts. No manually
fabricated metric values are allowed. The manuscript-ready mapping, captions
and table sources are maintained in [`PAPER_SUPPORT.md`](PAPER_SUPPORT.md).

The completed corrected/settings run generated the following aggregate figures in
[`results/`](../results/):

| File | Use |
|---|---|
| `roc_pr_curves.png` | Discrimination curves for the evaluated model variants |
| `calibration.png` | Temporal-test calibration comparison |
| `capacity_sensitivity.png` | Recall/sensitivity at 10%, 20% and 30% capacity |
| `primary_effect_ci.png` | Paired-bootstrap interval for ontology policy minus ML-only sensitivity |

All figures are generated from saved aggregate result artifacts. They are descriptive research
outputs, not evidence of clinical validity.
