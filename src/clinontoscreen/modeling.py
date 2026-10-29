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
    """Rank participants and choose exactly ceil(capacity*n) for research screening prioritization.

    Returns prevalence, the sensitivity ceiling imposed by the capacity/prevalence ratio,
    the fraction of that ceiling achieved, PPV (=precision), and lift (enrichment) as
    required by the plan addendum section 4.
    """
    y = np.asarray(list(y_true), dtype=int)
    s = np.asarray(list(score), dtype=float)
    if not 0 < capacity < 1:
        raise ValueError("capacity must be between 0 and 1")
    n_select = max(1, int(np.ceil(len(y) * capacity))) if len(y) else 0
    order = np.argsort(-np.nan_to_num(s, nan=-np.inf), kind="mergesort")
    selected = order[:n_select]
    positives = int(y.sum())
    tp = int(y[selected].sum()) if len(selected) else 0
    prevalence = float(y.mean()) if len(y) else float("nan")
    # Sensitivity ceiling: at capacity k, maximum achievable sensitivity is min(1, k / prevalence).
    sensitivity_ceiling = min(1.0, capacity / prevalence) if prevalence > 0 else float("nan")
    sensitivity = float(tp / positives) if positives else float("nan")
    ppv = float(tp / len(selected)) if len(selected) else float("nan")
    fraction_of_ceiling = float(sensitivity / sensitivity_ceiling) if np.isfinite(sensitivity_ceiling) and sensitivity_ceiling > 0 else float("nan")
    lift = float(ppv / prevalence) if prevalence > 0 else float("nan")
    return {
        "capacity": float(capacity), "n_total": int(len(y)), "n_selected": int(len(selected)),
        "positive_total": positives, "positive_found": tp,
        "prevalence": prevalence,
        "sensitivity": sensitivity,
        "sensitivity_ceiling": sensitivity_ceiling,
        "fraction_of_ceiling": fraction_of_ceiling,
        "precision": ppv,
        "ppv": ppv,
        "lift": lift,
        "screening_yield": ppv,
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


def paired_bootstrap_capacity_ci(
    y_true: Iterable[int],
    score_a: Iterable[float],
    score_b: Iterable[float],
    capacity: float,
    n_bootstrap: int = 2000,
    seed: int = 42,
) -> dict:
    """Paired bootstrap CI for sensitivity difference at a fixed screening capacity.

    Returns the 95% CI for sensitivity(score_a) - sensitivity(score_b) at the given capacity.
    Uses participant-level resampling so the two policies are compared on the same bootstrap cohort.
    """
    y = np.asarray(list(y_true), dtype=int)
    sa = np.asarray(list(score_a), dtype=float)
    sb = np.asarray(list(score_b), dtype=float)
    rng = np.random.default_rng(seed)
    diffs = []
    attempts = 0
    while len(diffs) < n_bootstrap and attempts < n_bootstrap * 3:
        attempts += 1
        idx = rng.integers(0, len(y), size=len(y))
        yb = y[idx]
        if yb.sum() == 0:
            continue
        n_sel = max(1, int(np.ceil(len(yb) * capacity)))
        sens_a = float(yb[np.argsort(-np.nan_to_num(sa[idx], nan=-np.inf))[:n_sel]].sum() / yb.sum())
        sens_b = float(yb[np.argsort(-np.nan_to_num(sb[idx], nan=-np.inf))[:n_sel]].sum() / yb.sum())
        diffs.append(sens_a - sens_b)
    if not diffs:
        return {"difference_median": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"), "successful_resamples": 0}
    arr = np.array(diffs)
    return {
        "difference_median": float(np.median(arr)),
        "ci_low": float(np.quantile(arr, 0.025)),
        "ci_high": float(np.quantile(arr, 0.975)),
        "successful_resamples": len(diffs),
    }


# ---------------------------------------------------------------------------
# E1: Low-data learning curve (plan addendum section 3)
# ---------------------------------------------------------------------------

def learning_curve_experiment(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str,
    feature_sets: dict[str, list[str]],
    fractions: tuple[float, ...] = (0.05, 0.10, 0.25, 0.50, 1.0),
    n_repeats: int = 3,
    seed: int = 42,
    capacity: float = 0.20,
) -> list[dict]:
    """Train on subsets of historical data and evaluate on the full test set.

    For each (fraction, feature_set, repeat) combination, train a model on a stratified
    random subsample and evaluate classification + capacity metrics on the locked test set.
    Returns a list of result dicts suitable for DataFrame conversion.

    This is E1 from the plan addendum: "when does guideline knowledge help?"
    """
    from sklearn.model_selection import StratifiedShuffleSplit
    results = []
    for frac in fractions:
        if frac >= 1.0:
            splits = [(np.arange(len(y_train)), None)]
        else:
            sss = StratifiedShuffleSplit(n_splits=n_repeats, train_size=frac, random_state=seed)
            splits = list(sss.split(X_train, y_train))
        for rep_idx, (train_idx, _) in enumerate(splits):
            X_sub = X_train.iloc[train_idx]
            y_sub = y_train.iloc[train_idx]
            for fs_name, fs_cols in feature_sets.items():
                pipe = make_pipeline(model_name, fs_cols, seed=seed)
                pipe.fit(X_sub[fs_cols], y_sub)
                prob = predict_positive_probability(pipe, X_test[fs_cols])
                cls = classification_metrics(y_test, prob)
                cap = capacity_metrics(y_test, prob, capacity)
                results.append({
                    "fraction": frac, "repeat": rep_idx, "model": model_name,
                    "feature_set": fs_name, "n_train": len(train_idx),
                    **{f"test_{k}": v for k, v in cls.items()},
                    **{f"cap_{k}": v for k, v in cap.items()},
                })
    return results


# ---------------------------------------------------------------------------
# E2: Missing-input stress test (plan addendum section 3)
# ---------------------------------------------------------------------------

def missing_input_stress_test(
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    mask_columns: list[str],
    mask_rates: tuple[float, ...] = (0.0, 0.10, 0.30),
    n_repeats: int = 3,
    seed: int = 42,
    capacity: float = 0.20,
) -> list[dict]:
    """Randomly mask selected test-time columns at various MCAR rates.

    For each (mask_rate, repeat), zero out a random subset of entries in the specified
    columns, then evaluate the pipeline. The ontology rule executor should report
    "not assessable" for masked inputs.

    Returns a list of result dicts.
    """
    rng = np.random.default_rng(seed)
    results = []
    for rate in mask_rates:
        for rep in range(n_repeats):
            X_masked = X_test.copy()
            if rate > 0:
                for col in mask_columns:
                    if col in X_masked.columns:
                        mask = rng.random(len(X_masked)) < rate
                        X_masked.loc[mask, col] = np.nan
            prob = predict_positive_probability(model, X_masked)
            cls = classification_metrics(y_test, prob)
            cap = capacity_metrics(y_test, prob, capacity)
            results.append({
                "mask_rate": rate, "repeat": rep,
                "masked_columns": mask_columns,
                **{f"test_{k}": v for k, v in cls.items()},
                **{f"cap_{k}": v for k, v in cap.items()},
            })
    return results


# ---------------------------------------------------------------------------
# Published-knowledge baseline: CDC/ADA prediabetes risk test
# (plan addendum section 5)
# ---------------------------------------------------------------------------

# Mapping of the official CDC/ADA prediabetes risk test to NHANES canonical fields.
# Source: https://www.cdc.gov/diabetes/risk-factors/prediabetes-risk-test.html
# Items scored on the official test; NHANES mappings are approximate.

def cdc_ada_risk_score(frame: pd.DataFrame) -> pd.Series:
    """Compute the CDC/ADA prediabetes risk test score from NHANES canonical fields.

    Official scoring (CDC/ADA Prediabetes Risk Test, adapted from Bang et al., Ann Intern Med 2009):
      1. Age category: <40 -> 0, 40-49 -> 1, 50-59 -> 2, >=60 -> 3 points
      2. Sex: man -> 1 point, woman -> 0 points
      3. Gestational diabetes history -> 1 point   (UNAVAILABLE in the harmonized NHANES files)
      4. First-degree relative with diabetes -> 1 point (UNAVAILABLE: MCQ300C is absent from the
         August 2021-August 2023 public MCQ file, so it cannot be harmonized across cycles)
      5. Ever diagnosed with high blood pressure -> 1 point
      6. Physically inactive -> 1 point (active -> 0 points)
      7. BMI category: <25 (or <23 for Asian respondents) -> 0, 25-29 -> 1, 30-39 -> 2, >=40 -> 3 points

    Unavailable items are scored 0 and reported through CDC_ADA_UNAVAILABLE_ITEMS so the
    baseline is never presented as a complete implementation of the published score.
    """
    age = pd.to_numeric(frame.get("age_years", pd.Series(dtype="float64")), errors="coerce")
    score = pd.Series(0.0, index=frame.index, dtype="float64")

    # 1. Age category
    score += np.where(age >= 60, 3, np.where(age >= 50, 2, np.where(age >= 40, 1, 0)))

    # 2. Sex: Male -> 1
    sex = pd.to_numeric(frame.get("sex_code", pd.Series(dtype="float64")), errors="coerce")
    score += (sex == 1).astype(float)

    # 3. Gestational diabetes: UNAVAILABLE — scored 0
    # 4. Family history: UNAVAILABLE in the later cycle — scored 0

    # 5. High blood pressure (ever told by a professional)
    bp_hist = pd.to_numeric(frame.get("hypertension_history", pd.Series(dtype="float64")), errors="coerce")
    score += (bp_hist == 1).astype(float)

    # 6. Physically inactive (harmonized leisure-time activity minutes: 0 -> inactive point)
    minutes = pd.to_numeric(frame.get("leisure_activity_minutes", pd.Series(dtype="float64")), errors="coerce")
    score += (minutes.notna() & (minutes == 0)).astype(float)

    # 7. BMI category, with the official lower threshold for Asian respondents
    bmi = pd.to_numeric(frame.get("bmi", pd.Series(dtype="float64")), errors="coerce")
    race = pd.to_numeric(frame.get("race_ethnicity_code", pd.Series(dtype="float64")), errors="coerce")
    overweight_cut = np.where(race == 6, 23.0, 25.0)
    score += np.where(bmi >= 40, 3, np.where(bmi >= 30, 2, np.where(bmi >= overweight_cut, 1, 0)))

    return score


CDC_ADA_RISK_THRESHOLD = 5  # Official threshold: score ≥5 indicates high risk
CDC_ADA_UNAVAILABLE_ITEMS = ["gestational_diabetes_history", "family_diabetes_history"]
