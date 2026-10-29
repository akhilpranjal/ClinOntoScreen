"""Artifact writing and reproducible research-result reports."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
import numpy as np


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write_json(path: str | Path, content: dict) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json_safe(content)
    payload.setdefault("generated_at_utc", datetime.now(timezone.utc).isoformat())
    destination.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    return destination


def get_protocol_metadata() -> dict:
    """Collect reproducibility metadata for protocol freeze (plan addendum section 9).

    Returns git commit hash, package versions, Python version, and timestamp.
    """
    meta: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
    }
    # Git commit hash
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            meta["git_commit_hash"] = result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        meta["git_commit_hash"] = "unavailable"

    # Package versions
    packages = [
        "numpy", "pandas", "scikit-learn", "xgboost", "rdflib",
        "streamlit", "plotly", "networkx", "joblib", "matplotlib",
    ]
    versions = {}
    for pkg in packages:
        try:
            mod = __import__(pkg.replace("-", "_"))
            versions[pkg] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[pkg] = "not_installed"
    # scikit-learn special case
    try:
        import sklearn
        versions["scikit-learn"] = sklearn.__version__
    except ImportError:
        pass
    meta["package_versions"] = versions
    return meta


def cohort_summary(df, label: str = "cohort") -> dict:
    """Generate a summary of a cohort dataframe for reporting."""
    summary: dict[str, Any] = {
        "label": label,
        "n_participants": int(len(df)),
    }
    if "target" in df.columns:
        summary["positive_count"] = int(df["target"].sum())
        summary["negative_count"] = int(len(df) - df["target"].sum())
        summary["prevalence"] = float(df["target"].mean())
    if "cycle" in df.columns:
        summary["cycles"] = df["cycle"].value_counts().to_dict()

    # Missingness per feature
    missingness = {}
    for col in df.columns:
        n_missing = int(df[col].isna().sum())
        if n_missing > 0:
            missingness[col] = {
                "n_missing": n_missing,
                "pct_missing": round(float(n_missing / len(df) * 100), 2),
            }
    summary["missingness"] = missingness
    return summary


def write_feature_manifest(
    path: str | Path,
    raw_features: list[str],
    ontology_features: list[str],
    forbidden: list[str],
    feature_metadata: dict | None = None,
) -> Path:
    """Write a JSON feature manifest for reproducibility tracking."""
    manifest = {
        "raw_features": raw_features,
        "ontology_features": ontology_features,
        "forbidden_predictors": forbidden,
        "n_raw": len(raw_features),
        "n_ontology": len(ontology_features),
        "n_total": len(raw_features) + len(ontology_features),
    }
    if feature_metadata:
        manifest["metadata"] = feature_metadata
    return write_json(path, manifest)

