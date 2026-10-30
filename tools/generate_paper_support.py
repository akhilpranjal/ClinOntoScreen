"""Generate manuscript-support artifacts from the locked aggregate run."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.clinontoscreen.data import canonicalize_cycle, load_cycle

CACHE = ROOT / "data" / "raw"
RESULTS = ROOT / "results"


def _flow(cycle: str) -> dict:
    raw, report = load_cycle(cycle, CACHE)
    frame = canonicalize_cycle(raw, cycle)
    adult = frame["age_years"] >= 18
    no_diabetes = frame["reported_diabetes"] == 2
    no_prediabetes = frame["reported_prediabetes"] == 2
    valid_hba1c = frame["hba1c_percent"].notna()
    eligible = adult & no_diabetes & no_prediabetes & valid_hba1c
    fasting = frame["fasting_glucose"].notna()
    return {
        "cycle": cycle,
        "label": report["label"],
        "merged_rows": int(len(frame)),
        "adult_rows": int(adult.sum()),
        "excluded_under_18": int((~adult).sum()),
        "excluded_prior_diabetes": int((adult & (frame["reported_diabetes"] == 1)).sum()),
        "excluded_unknown_diabetes_response": int(
            (adult & ~frame["reported_diabetes"].isin([1, 2])).sum()
        ),
        "excluded_prior_prediabetes_after_no_diabetes": int(
            (adult & no_diabetes & (frame["reported_prediabetes"] == 1)).sum()
        ),
        "excluded_unknown_prediabetes_response_after_no_diabetes": int(
            (adult & no_diabetes & ~frame["reported_prediabetes"].isin([1, 2])).sum()
        ),
        "excluded_missing_hba1c_after_history_filter": int(
            (adult & no_diabetes & no_prediabetes & ~valid_hba1c).sum()
        ),
        "eligible_rows": int(eligible.sum()),
        "screen_positive_rows": int((eligible & (frame["hba1c_percent"] >= 5.7)).sum()),
        "screen_negative_rows": int((eligible & (frame["hba1c_percent"] < 5.7)).sum()),
        "fasting_glucose_available_eligible_rows": int((eligible & fasting).sum()),
        "source_files": report["source_files"],
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    flows = [_flow("2017_mar2020"), _flow("2021_2023")]
    payload = {
        "protocol": "protocol-v1-corrected-and-settings",
        "definition": (
            "Sequential exclusions from the merged cycle file: adults, no prior "
            "diabetes, no prior prediabetes, valid HbA1c."
        ),
        "flows": flows,
    }
    (RESULTS / "cohort_flow.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )

    feature_settings = json.loads(
        (RESULTS / "feature_settings.json").read_text(encoding="utf-8")
    )
    rows = []
    for name, setting in feature_settings["settings"].items():
        metrics = next(
            row for row in setting["metrics"]
            if row["variant"] == "xgboost_ontology" and row["capacity"] == 0.2
        )
        rows.append({
            "setting": name,
            "n_historical": setting["n_historical"],
            "n_test": setting["n_test"],
            "positive_test": setting["positive_test"],
            "sensitivity_at_20pct": metrics["sensitivity"],
            "precision_at_20pct": metrics["precision"],
            "tp_at_20pct": metrics["tp"],
            "fp_at_20pct": metrics["fp"],
        })
    header = list(rows[0])
    lines = [",".join(header)]
    lines.extend(",".join(str(row[column]) for column in header) for row in rows)
    (RESULTS / "secondary_feature_settings_table.csv").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    manifest = json.loads((RESULTS / "run_manifest.json").read_text(encoding="utf-8"))
    checksum_check = {
        "primary_results_sha256": _sha256(RESULTS / "research_results.json"),
        "manifest_primary_results_sha256": manifest["primary_result_sha256"],
        "feature_settings_sha256": _sha256(RESULTS / "feature_settings.json"),
        "manifest_feature_settings_sha256": manifest["feature_settings_sha256"],
        "ontology_sha256": _sha256(ROOT / "ontology" / "diabetes_screening.ttl"),
        "manifest_ontology_sha256": manifest["ontology_sha256"],
    }
    checksum_check["all_checked_hashes_match"] = (
        checksum_check["primary_results_sha256"]
        == checksum_check["manifest_primary_results_sha256"]
        and checksum_check["feature_settings_sha256"]
        == checksum_check["manifest_feature_settings_sha256"]
        and checksum_check["ontology_sha256"]
        == checksum_check["manifest_ontology_sha256"]
    )
    (RESULTS / "paper_provenance_check.json").write_text(
        json.dumps(checksum_check, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"flows": flows, "checksum_check": checksum_check}, indent=2))


if __name__ == "__main__":
    main()
