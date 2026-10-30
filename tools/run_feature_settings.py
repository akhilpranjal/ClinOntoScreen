"""Run the post-hoc feature-setting analysis without changing the primary endpoint."""
from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.clinontoscreen.data import (
    FEATURE_SETTINGS,
    SETTING_1_FEATURES,
    SETTING_2_FEATURES,
    SETTING_3_FEATURES,
    load_all_cycles,
    assert_feature_availability,
)
from src.clinontoscreen.modeling import make_pipeline, predict_positive_probability
from src.clinontoscreen.ontology import ONTOLOGY_FEATURES, derive_ontology_features

CACHE = ROOT / "data" / "raw"
RESULTS = ROOT / "results"
SEEDS = [17, 42, 123, 2025, 2026]
CAPACITIES = [0.10, 0.20, 0.30]


def _metrics(y: np.ndarray, score: np.ndarray, capacity: float) -> dict:
    n = len(y)
    selected = int(np.ceil(n * capacity))
    order = np.argsort(-np.nan_to_num(score, nan=-np.inf), kind="mergesort")
    pred = np.zeros(n, dtype=bool)
    pred[order[:selected]] = True
    tp = int(y[pred].sum())
    positive = int(y.sum())
    fp = selected - tp
    fn = positive - tp
    tn = n - positive - fp
    precision = tp / selected if selected else np.nan
    recall = tp / positive if positive else np.nan
    return {
        "capacity": capacity, "n": n, "n_selected": selected,
        "positive_total": positive, "prevalence": float(y.mean()),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "recall": recall, "sensitivity": recall, "precision": precision,
        "specificity": tn / (tn + fp) if tn + fp else np.nan,
        "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
    }


def _run_setting(name: str, features: list[str], historical: pd.DataFrame, test: pd.DataFrame) -> dict:
    assert_feature_availability(pd.concat([historical, test]), features)
    variants = {
        "xgboost_raw": (features, "xgboost"),
        "xgboost_ontology": (features + ONTOLOGY_FEATURES, "xgboost"),
    }
    predictions: dict[str, list[np.ndarray]] = {key: [] for key in variants}
    y_train = historical["target"].astype(int).to_numpy()
    y_test = test["target"].astype(int).to_numpy()
    train_base = historical[features].copy()
    test_base = test[features].copy()
    train_onto = derive_ontology_features(train_base)
    test_onto = derive_ontology_features(test_base)
    for seed in SEEDS:
        for variant, (variant_features, family) in variants.items():
            train_frame = train_base if variant == "xgboost_raw" else train_onto
            test_frame = test_base if variant == "xgboost_raw" else test_onto
            model = make_pipeline(
                family, variant_features, seed=seed,
                params={"n_estimators": 150, "max_depth": 2, "learning_rate": 0.07},
            )
            model.fit(train_frame[variant_features], y_train)
            predictions[variant].append(predict_positive_probability(model, test_frame[variant_features]))
    rows = []
    for variant, scores in predictions.items():
        score = np.mean(np.vstack(scores), axis=0)
        for capacity in CAPACITIES:
            rows.append({"variant": variant, **_metrics(y_test, score, capacity)})
    return {
        "setting": name, "features": features, "n_historical": len(historical),
        "n_test": len(test), "positive_test": int(y_test.sum()),
        "prevalence_test": float(y_test.mean()), "metrics": rows,
    }


def main() -> None:
    historical, temporal, reports = load_all_cycles(CACHE)
    settings = {}
    settings["setting_1_no_labs"] = _run_setting("setting_1_no_labs", SETTING_1_FEATURES, historical, temporal)
    settings["setting_2_routine_labs"] = _run_setting("setting_2_routine_labs", SETTING_2_FEATURES, historical, temporal)
    fasting_historical = historical.loc[historical["fasting_glucose"].notna()].copy()
    fasting_temporal = temporal.loc[temporal["fasting_glucose"].notna()].copy()
    if len(fasting_historical) < 100 or len(fasting_temporal) < 100:
        raise RuntimeError("Fasting-glucose subsample is too small for the prespecified secondary analysis")
    settings["setting_1_no_labs_fasting_subsample"] = _run_setting(
        "setting_1_no_labs_fasting_subsample", SETTING_1_FEATURES, fasting_historical, fasting_temporal
    )
    settings["setting_2_routine_labs_fasting_subsample"] = _run_setting(
        "setting_2_routine_labs_fasting_subsample", SETTING_2_FEATURES, fasting_historical, fasting_temporal
    )
    settings["setting_3_fasting_glucose"] = _run_setting(
        "setting_3_fasting_glucose", SETTING_3_FEATURES, fasting_historical, fasting_temporal
    )
    payload = {
        "analysis": "Secondary post-hoc feature settings",
        "primary_setting": "setting_1_no_labs",
        "settings": settings,
        "forbidden_predictors": ["LBXGH", "DIQ010", "DIQ160", "DIQ050", "DIQ070", "SEQN"],
        "fasting_subsample_definition": "non-missing LBXGLU in both development and temporal cohorts",
        "fpg_is_glycemic": True,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "source_reports": reports,
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "feature_settings.json").write_text(json.dumps(payload, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")
    print(json.dumps({key: {"n_test": value["n_test"], "positive_test": value["positive_test"]} for key, value in settings.items()}, indent=2))


if __name__ == "__main__":
    main()
