"""Leakage-safe model pipelines and evaluation helpers."""
from __future__ import annotations
from typing import Iterable
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import average_precision_score, brier_score_loss, f1_score, precision_score, recall_score, roc_auc_score, confusion_matrix

from .data import NUMERIC_FEATURES, CATEGORICAL_FEATURES, RAW_FEATURES, assert_no_leakage
from .ontology import ONTOLOGY_FEATURES


def _one_hot_encoder() -> OneHotEncoder:
    """Support both current and older scikit-learn keyword names."""
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    except TypeError:  # scikit-learn < 1.2
        return OneHotEncoder(handle_unknown="ignore", sparse=True)


def make_preprocessor(feature_names: Iterable[str]) -> ColumnTransformer:
    columns = list(feature_names)
    assert_no_leakage(columns)
    numeric = [col for col in columns if col in NUMERIC_FEATURES or col in ONTOLOGY_FEATURES]
    categorical = [col for col in columns if col not in numeric]
    transformers = []
    if numeric:
        transformers.append(("numeric", Pipeline([
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("scaler", StandardScaler()),
        ]), numeric))
    if categorical:
        transformers.append(("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", _one_hot_encoder()),
        ]), categorical))
    return ColumnTransformer(transformers=transformers, remainder="drop", verbose_feature_names_out=False)


def make_pipeline(model_name: str, feature_names: Iterable[str], seed: int = 42, params: dict | None = None) -> Pipeline:
    from xgboost import XGBClassifier
    params = dict(params or {})
    if model_name == "logistic":
        model = LogisticRegression(max_iter=3000, solver="lbfgs", random_state=seed, **params)
    elif model_name == "xgboost":
        defaults = {
            "n_estimators": 350, "max_depth": 3, "learning_rate": 0.04,
            "subsample": 0.85, "colsample_bytree": 0.85, "reg_lambda": 1.0,
            "min_child_weight": 3, "eval_metric": "logloss", "n_jobs": 2,
        }
        # Keep all defaults valid for XGBoost and permit selected parameters to override them.
        defaults["random_state"] = seed
        defaults.update(params)
        model = XGBClassifier(**defaults)
    else:
        raise ValueError("model_name must be 'logistic' or 'xgboost'")
    return Pipeline([("preprocess", make_preprocessor(feature_names)), ("model", model)])


def predict_positive_probability(model: Pipeline, frame: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        return np.asarray(model.predict_proba(frame)[:, 1], dtype=float)
    raise TypeError("Model pipeline must implement predict_proba")


def classification_metrics(y_true: Iterable[int], probability: Iterable[float], threshold: float = 0.5) -> dict:
    y = np.asarray(list(y_true), dtype=int)
    p = np.asarray(list(probability), dtype=float)
    pred = p >= threshold
    result = {
        "n": int(len(y)),
        "positive_count": int(y.sum()),
        "prevalence": float(y.mean()) if len(y) else float("nan"),
        "brier": float(brier_score_loss(y, p)),
        "precision_at_threshold_0_5": float(precision_score(y, pred, zero_division=0)),
        "recall_at_threshold_0_5": float(recall_score(y, pred, zero_division=0)),
        "f1_at_threshold_0_5": float(f1_score(y, pred, zero_division=0)),
    }
    result["auroc"] = float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else float("nan")
    result["auprc"] = float(average_precision_score(y, p)) if len(np.unique(y)) == 2 else float("nan")
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    result["true_negative"] = int(tn)
    result["false_positive"] = int(fp)
    result["false_negative"] = int(fn)
    result["true_positive"] = int(tp)
    result["specificity_at_threshold_0_5"] = float(tn / (tn + fp)) if tn + fp else float("nan")
    return result


def capacity_metrics(y_true: Iterable[int], score: Iterable[float], capacity: float) -> dict:
    """Rank participants and choose exactly ceil(capacity*n) for research screening prioritization."""
    y = np.asarray(list(y_true), dtype=int)
    s = np.asarray(list(score), dtype=float)
    if not 0 < capacity < 1:
        raise ValueError("capacity must be between 0 and 1")
    n_select = max(1, int(np.ceil(len(y) * capacity))) if len(y) else 0
    order = np.argsort(-np.nan_to_num(s, nan=-np.inf), kind="mergesort")
    selected = order[:n_select]
    positives = int(y.sum())
    tp = int(y[selected].sum()) if len(selected) else 0
    return {
        "capacity": float(capacity), "n_total": int(len(y)), "n_selected": int(len(selected)),
        "positive_total": positives, "positive_found": tp,
        "sensitivity": float(tp / positives) if positives else float("nan"),
        "precision": float(tp / len(selected)) if len(selected) else float("nan"),
        "screening_yield": float(tp / len(selected)) if len(selected) else float("nan"),
        "false_referrals": int(len(selected) - tp),
    }


def bootstrap_metric_ci(y_true: Iterable[int], probability: Iterable[float], metric_fn, n_bootstrap: int = 1000, seed: int = 42) -> dict:
    """Participant bootstrap confidence interval; invalid single-class resamples are skipped."""
    y = np.asarray(list(y_true), dtype=int)
    p = np.asarray(list(probability), dtype=float)
    if len(y) != len(p) or not len(y):
        raise ValueError("y_true and probability must be non-empty and equally sized")
    rng = np.random.default_rng(seed)
    scores = []
    attempts = 0
    while len(scores) < n_bootstrap and attempts < n_bootstrap * 3:
        attempts += 1
        idx = rng.integers(0, len(y), size=len(y))
        if len(np.unique(y[idx])) < 2:
            continue
        scores.append(float(metric_fn(y[idx], p[idx])))
    if not scores:
        return {"low": float("nan"), "median": float("nan"), "high": float("nan"), "successful_resamples": 0}
    return {
        "low": float(np.quantile(scores, 0.025)),
        "median": float(np.quantile(scores, 0.5)),
        "high": float(np.quantile(scores, 0.975)),
        "successful_resamples": int(len(scores)),
    }
