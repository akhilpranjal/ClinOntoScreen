from pathlib import Path
import json

import pandas as pd
import pytest

from src.clinontoscreen.data import assert_feature_availability
from src.clinontoscreen.modeling import simple_flag_metrics
from src.clinontoscreen.reporting import export_public_results, load_results


def test_simple_flag_metrics_matches_capacity_counts():
    result = simple_flag_metrics([1, 0, 1, 0, 1], [0.9, 0.8, 0.7, 0.2, 0.1], 0.4)
    assert result["n_selected"] == 2
    assert result["tp"] + result["fn"] == result["positive_total"]
    assert result["recall"] == result["sensitivity"]
    assert result["tp"] + result["fp"] + result["tn"] + result["fn"] == result["n"]


def test_feature_availability_stops_all_missing_cycle_feature():
    frame = pd.DataFrame({"cycle": ["old", "old", "new"], "feature": [1.0, 2.0, None]})
    with pytest.raises(ValueError, match="100% missing"):
        assert_feature_availability(frame, ["feature"])


def test_public_export_rejects_participant_identifier(tmp_path: Path):
    source = tmp_path / "source"
    destination = tmp_path / "results"
    source.mkdir()
    (source / "research_results.json").write_text('{"SEQN": 123}', encoding="utf-8")
    with pytest.raises(ValueError, match="SEQN"):
        export_public_results(source, destination)


def test_results_loader_prefers_artifacts_then_results(tmp_path: Path):
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "research_results.json").write_text('{"source": "results"}', encoding="utf-8")
    assert load_results(tmp_path)["source"] == "results"
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts" / "research_results.json").write_text('{"source": "artifacts"}', encoding="utf-8")
    assert load_results(tmp_path)["source"] == "artifacts"


def test_committed_tables_recompute_from_saved_aggregate_rows():
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "results" / "research_results.json").read_text(encoding="utf-8"))
    rows = payload["screening_budgets"]
    tier = payload["tier1_metrics"]
    assert len(rows) == len(tier)
    for source, table in zip(rows, tier):
        assert source["policy"] == table["policy"]
        assert source["capacity"] == table["capacity"]
        assert source["tp"] + source["fn"] == source["positive_total"]
        assert source["tp"] + source["fp"] + source["tn"] + source["fn"] == source["n_total"]
        assert table["recall"] == table["sensitivity"]


def test_committed_feature_settings_have_no_forbidden_predictors():
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "results" / "feature_settings.json").read_text(encoding="utf-8"))
    assert payload["all_settings_forbidden_check_passed"] is True
    for setting in payload["settings"].values():
        assert "LBXGH" not in setting["features"]
        assert "DIQ010" not in setting["features"]
        assert "DIQ160" not in setting["features"]


def test_paper_support_artifacts_match_primary_cohort():
    root = Path(__file__).resolve().parents[1]
    flow = json.loads((root / "results" / "cohort_flow.json").read_text(encoding="utf-8"))
    primary = json.loads((root / "results" / "research_results.json").read_text(encoding="utf-8"))
    by_cycle = {row["cycle"]: row for row in flow["flows"]}
    assert by_cycle["2017_mar2020"]["eligible_rows"] == primary["cohort"]["historical_n"]
    assert by_cycle["2021_2023"]["eligible_rows"] == primary["cohort"]["test_n"]
    assert by_cycle["2021_2023"]["screen_positive_rows"] == primary["cohort"]["test_positive_count"]


def test_paper_provenance_hashes_match_manifest():
    root = Path(__file__).resolve().parents[1]
    provenance = json.loads((root / "results" / "paper_provenance_check.json").read_text(encoding="utf-8"))
    assert provenance["all_checked_hashes_match"] is True
