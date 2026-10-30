from pathlib import Path

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
