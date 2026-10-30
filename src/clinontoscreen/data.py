"""NHANES download, cycle harmonization, cohort construction, and feature contract."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import logging
from typing import Iterable

import numpy as np
import pandas as pd
import requests

LOGGER = logging.getLogger(__name__)

CYCLE_CONFIGS = {
    "2017_mar2020": {
        "label": "2017–March 2020 pre-pandemic",
        "base_url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/",
        "prefix": "P_",
        "suffix": "",
    },
    "2021_2023": {
        "label": "August 2021–August 2023",
        "base_url": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/",
        "prefix": "",
        "suffix": "_L",
    },
}

FILE_STEMS = ("DEMO", "DIQ", "GHB", "BMX", "BPXO", "BPQ", "SMQ", "PAQ", "MCQ", "HDL")
ESSENTIAL_STEMS = {"DEMO", "DIQ", "GHB", "BMX"}

NUMERIC_FEATURES = [
    "age_years", "income_poverty_ratio", "bmi", "waist_cm",
    "systolic_bp_mean", "diastolic_bp_mean",
    "hdl_cholesterol",
    "leisure_activity_minutes", "sedentary_minutes",
]
CATEGORICAL_FEATURES = [
    "sex_code", "race_ethnicity_code", "education_code",
    "hypertension_history", "ever_smoked_100_cigs",
    "heart_failure_history", "coronary_heart_disease_history", "angina_history",
    "heart_attack_history", "stroke_history",
]
RAW_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Input columns that can encode the outcome or prior knowledge of the outcome must never be predictors.
FORBIDDEN_PREDICTORS = {
    "LBXGH", "DIQ010", "DIQ160", "DIQ050", "DIQ070", "glucose", "hba1c",
    "diabetes_medication", "screen_positive_dysglycemia", "target",
}

FILE_VARIABLES = {
    "DEMO": ["SEQN", "RIDAGEYR", "RIAGENDR", "RIDRETH3", "DMDEDUC2", "INDFMPIR", "WTMECPRP", "WTMEC2YR", "SDMVSTRA", "SDMVPSU"],
    "DIQ": ["SEQN", "DIQ010", "DIQ160"],
    "GHB": ["SEQN", "LBXGH"],
    "BMX": ["SEQN", "BMXBMI", "BMXWAIST"],
    "BPXO": ["SEQN", "BPXOSY1", "BPXOSY2", "BPXOSY3", "BPXOSY4", "BPXODI1", "BPXODI2", "BPXODI3", "BPXODI4"],
    "BPQ": ["SEQN", "BPQ020", "BPQ040", "BPQ040A"],
    "SMQ": ["SEQN", "SMQ020"],
    "PAQ": ["SEQN", "PAQ605", "PAQ610", "PAQ615", "PAQ620", "PAQ625", "PAQ630",
            "PAQ635", "PAQ640", "PAQ645", "PAQ650", "PAQ655", "PAQ660", "PAD680",
            "PAD790Q", "PAD790U", "PAD800", "PAD810Q", "PAD810U", "PAD820"],
    "MCQ": ["SEQN", "MCQ160B", "MCQ160C", "MCQ160D", "MCQ160E", "MCQ160F"],
    "HDL": ["SEQN", "LBDHDD"],
}


def _file_name(stem: str, cfg: dict) -> str:
    return f"{cfg['prefix']}{stem}{cfg['suffix']}.xpt"


def read_xpt_url(url: str, cache_path: Path | None = None, timeout: int = 60) -> pd.DataFrame:
    """Read an NHANES SAS transport file, optionally caching the downloaded bytes."""
    if cache_path is not None and cache_path.exists():
        return pd.read_sas(cache_path, format="xport", encoding="utf-8")
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    content = response.content
    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(content)
    return pd.read_sas(BytesIO(content), format="xport", encoding="utf-8")


def load_cycle(cycle: str, cache_dir: str | Path = "data/raw") -> tuple[pd.DataFrame, dict]:
    """Download and merge one NHANES cycle. Missing optional files are reported and skipped."""
    if cycle not in CYCLE_CONFIGS:
        raise ValueError(f"Unknown cycle {cycle!r}; choose one of {list(CYCLE_CONFIGS)}")
    cfg = CYCLE_CONFIGS[cycle]
    cache_dir = Path(cache_dir) / cycle
    merged: pd.DataFrame | None = None
    report = {"cycle": cycle, "label": cfg["label"], "loaded_files": [], "skipped_files": [], "missing_variables": {}}
    for stem in FILE_STEMS:
        filename = _file_name(stem, cfg)
        url = cfg["base_url"] + filename
        try:
            frame = read_xpt_url(url, cache_dir / filename)
        except Exception as exc:  # optional-source failures must be visible in report
            if stem in ESSENTIAL_STEMS:
                raise RuntimeError(f"Failed to load essential NHANES file {url}: {exc}") from exc
            LOGGER.warning("Skipping optional file %s: %s", url, exc)
            report["skipped_files"].append({"file": filename, "reason": str(exc)})
            continue
        wanted = FILE_VARIABLES[stem]
        missing = [column for column in wanted if column not in frame.columns]
        report["missing_variables"][stem] = missing
        selected = frame[[column for column in wanted if column in frame.columns]].copy()
        if "SEQN" not in selected.columns:
            if stem in ESSENTIAL_STEMS:
                raise ValueError(f"Essential file {filename} is missing SEQN")
            report["skipped_files"].append({"file": filename, "reason": "SEQN missing"})
            continue
        if merged is None:
            merged = selected
        else:
            # Each source is selected to contain SEQN plus disjoint variables; assert that assumption.
            duplicate = (set(merged.columns) & set(selected.columns)) - {"SEQN"}
            if duplicate:
                LOGGER.warning("Duplicate source columns %s in %s; dropping duplicate columns from later file", duplicate, filename)
                selected = selected.drop(columns=list(duplicate))
            merged = merged.merge(selected, on="SEQN", how="left", validate="one_to_one")
        report["loaded_files"].append(filename)
    if merged is None:
        raise RuntimeError(f"No files loaded for cycle {cycle}")
    merged["cycle"] = cycle
    report["rows_after_merge"] = int(len(merged))
    return merged, report


def _numeric(frame: pd.DataFrame, col: str) -> pd.Series:
    if col not in frame:
        return pd.Series(np.nan, index=frame.index, dtype="float64")
    result = pd.to_numeric(frame[col], errors="coerce")
    result = result.mask(result.abs() < 1e-300)
    return result


def _mean_available(frame: pd.DataFrame, columns: Iterable[str]) -> pd.Series:
    usable = [col for col in columns if col in frame.columns]
    if not usable:
        return pd.Series(np.nan, index=frame.index, dtype="float64")
    return frame[usable].apply(pd.to_numeric, errors="coerce").mean(axis=1, skipna=True)


def _clean_response(series: pd.Series, invalid: set[float] | None = None) -> pd.Series:
    result = pd.to_numeric(series, errors="coerce").astype("float64")
    for bad in (invalid or {7.0, 9.0, 77.0, 99.0, 777.0, 999.0, 7777.0, 9999.0}):
        result = result.mask(result == bad)
    result = result.mask(result.abs() < 1e-300)
    return result


def canonicalize_cycle(raw: pd.DataFrame, cycle: str) -> pd.DataFrame:
    """Convert source variables to a stable feature schema; preserve target/filter fields separately."""
    out = pd.DataFrame(index=raw.index)
    out["SEQN"] = raw["SEQN"] if "SEQN" in raw else np.arange(len(raw))
    out["cycle"] = cycle
    out["age_years"] = _numeric(raw, "RIDAGEYR")
    out["sex_code"] = _clean_response(raw.get("RIAGENDR", pd.Series(np.nan, index=raw.index)), set())
    out["race_ethnicity_code"] = _clean_response(raw.get("RIDRETH3", pd.Series(np.nan, index=raw.index)), set())
    out["education_code"] = _clean_response(raw.get("DMDEDUC2", pd.Series(np.nan, index=raw.index)))
    out["income_poverty_ratio"] = _numeric(raw, "INDFMPIR")
    out["bmi"] = _numeric(raw, "BMXBMI")
    out["waist_cm"] = _numeric(raw, "BMXWAIST")
    out["systolic_bp_mean"] = _mean_available(raw, [f"BPXOSY{i}" for i in range(1, 5)])
    out["diastolic_bp_mean"] = _mean_available(raw, [f"BPXODI{i}" for i in range(1, 5)])
    for source, target in {
        "BPQ020": "hypertension_history", "SMQ020": "ever_smoked_100_cigs",
        "MCQ160B": "heart_failure_history",
        "MCQ160C": "coronary_heart_disease_history", "MCQ160D": "angina_history",
        "MCQ160E": "heart_attack_history", "MCQ160F": "stroke_history",
    }.items():
        out[target] = _clean_response(raw.get(source, pd.Series(np.nan, index=raw.index)))
    # BPQ040A is the cycle-specific treatment item.  BPQ040 is retained only
    # as a documented historical fallback because it is absent in the later cycle.
    treatment_source = "BPQ040A" if "BPQ040A" in raw else "BPQ040"
    out["hypertension_treatment"] = _clean_response(raw.get(treatment_source, pd.Series(np.nan, index=raw.index)))
    # Activity minutes: historical NHANES uses yes/no + days + minutes; the
    # 2021-2023 cycle uses frequency + unit (day/week/month/year) + minutes.
    if "PAQ635" in raw.columns:
        def minutes(days_col: str, duration_col: str, yes_no_col: str) -> pd.Series:
            yes_no = _clean_response(raw.get(yes_no_col, pd.Series(np.nan, index=raw.index)))
            days = _clean_response(raw.get(days_col, pd.Series(np.nan, index=raw.index)))
            duration = _clean_response(raw.get(duration_col, pd.Series(np.nan, index=raw.index)))
            result = days * duration
            result.loc[yes_no.eq(2)] = 0.0
            return result
        leisure_parts = [
            minutes("PAQ640", "PAQ645", "PAQ635"),
            minutes("PAQ655", "PAQ660", "PAQ650"),
        ]
        out["leisure_activity_minutes"] = pd.concat(leisure_parts, axis=1).sum(axis=1, min_count=1)
    elif "PAD790Q" in raw.columns:
        def _unit_series(col: str) -> pd.Series:
            values = raw.get(col, pd.Series("", index=raw.index))
            return values.map(lambda x: x.decode("utf-8", "replace").strip().upper() if isinstance(x, (bytes, bytearray)) else str(x).strip().upper())

        def _temporal_weekly(q_col: str, u_col: str, m_col: str) -> pd.Series:
            q = _clean_response(raw.get(q_col, pd.Series(np.nan, index=raw.index)))
            m = _clean_response(raw.get(m_col, pd.Series(np.nan, index=raw.index)))
            factor = _unit_series(u_col).map({"D": 7.0, "W": 1.0, "M": 52.0 / 12.0, "Y": 1.0 / 52.0})
            return q * m * factor

        leisure_parts = [
            _temporal_weekly("PAD790Q", "PAD790U", "PAD800"),
            _temporal_weekly("PAD810Q", "PAD810U", "PAD820"),
        ]
        out["leisure_activity_minutes"] = pd.concat(leisure_parts, axis=1).sum(axis=1, min_count=1)
    else:
        out["leisure_activity_minutes"] = pd.Series(np.nan, index=raw.index, dtype="float64")
    out["sedentary_minutes"] = _clean_response(raw.get("PAD680", pd.Series(np.nan, index=raw.index)))
    out["hdl_cholesterol"] = _numeric(raw, "LBDHDD")
    out["reported_diabetes"] = _clean_response(raw.get("DIQ010", pd.Series(np.nan, index=raw.index)), set())
    out["reported_prediabetes"] = _clean_response(raw.get("DIQ160", pd.Series(np.nan, index=raw.index)), set())
    out["hba1c_percent"] = _numeric(raw, "LBXGH")
    # Retain cycle-appropriate survey weights only for documented sensitivity/descriptive analysis.
    for weight_col in ("WTMECPRP", "WTMEC2YR", "SDMVSTRA", "SDMVPSU"):
        if weight_col in raw:
            out[weight_col.lower()] = _numeric(raw, weight_col)
    return out


def make_cohort_table(canonical: pd.DataFrame, adults_only: bool = True) -> pd.DataFrame:
    """Build a leakage-safe cohort and primary/secondary outcome labels."""
    frame = canonical.copy()
    if adults_only:
        frame = frame.loc[frame["age_years"] >= 18].copy()
    frame = frame.loc[
        (frame["reported_diabetes"] == 2) &
        (frame["reported_prediabetes"] == 2) &
        frame["hba1c_percent"].notna()
    ].copy()
    frame["target"] = (frame["hba1c_percent"] >= 5.7).astype("int8")
    frame["target_diabetes_range"] = (frame["hba1c_percent"] >= 6.5).astype("int8")
    return frame.reset_index(drop=True)


def load_all_cycles(cache_dir: str | Path = "data/raw") -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Load canonical historical cohort and locked later-cycle cohort."""
    historical_raw, historical_report = load_cycle("2017_mar2020", cache_dir)
    temporal_raw, temporal_report = load_cycle("2021_2023", cache_dir)
    historical = make_cohort_table(canonicalize_cycle(historical_raw, "2017_mar2020"))
    temporal = make_cohort_table(canonicalize_cycle(temporal_raw, "2021_2023"))
    reports = {"historical": historical_report, "temporal_test": temporal_report}
    return historical, temporal, reports


def assert_no_leakage(feature_columns: Iterable[str]) -> None:
    """Fail fast if the declared model feature list contains an outcome or diagnosis variable."""
    names = {str(col).lower() for col in feature_columns}
    forbidden = {name.lower() for name in FORBIDDEN_PREDICTORS}
    bad = sorted(names & forbidden)
    # Canonical names are also guarded.
    bad += sorted(name for name in names if any(token in name for token in ("hba1c", "glucose", "reported_diabetes", "reported_prediabetes", "target")))
    if bad:
        raise ValueError(f"Target leakage: forbidden predictor(s) found: {sorted(set(bad))}")
    if "seqn" in names:
        raise ValueError("SEQN is an NHANES participant identifier and must never be a predictor")


def assert_feature_availability(frame: pd.DataFrame, feature_columns: Iterable[str], cycle_column: str = "cycle") -> None:
    """Stop a run when a selected feature is entirely absent from any cycle."""
    features = list(feature_columns)
    missing_columns = [column for column in features if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Selected feature columns are absent: {missing_columns}")
    if cycle_column not in frame.columns:
        raise ValueError(f"Cycle column {cycle_column!r} is required for feature-QC")
    failures = []
    for cycle, group in frame.groupby(cycle_column, dropna=False):
        for feature in features:
            if group[feature].notna().sum() == 0:
                failures.append({"cycle": str(cycle), "feature": feature})
    if failures:
        raise ValueError(f"Selected features are 100% missing by cycle: {failures}")
