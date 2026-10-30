"""Static integrity checks for the standalone Kaggle/Colab notebook."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks" / "01_nhanes_ontology_ml.ipynb"
ONTOLOGY_PATH = ROOT / "ontology" / "diabetes_screening.ttl"


def test_notebook_code_cells_are_syntax_valid_and_unexecuted():
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert code_cells
    for cell in code_cells:
        assert cell.get("execution_count") is None
        assert not cell.get("outputs")
        source = "\n".join(
            line for line in "".join(cell["source"]).splitlines()
            if not line.lstrip().startswith("%")
        )
        ast.parse(source)


def test_notebook_embeds_the_exact_versioned_ontology():
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    cell = next(
        cell for cell in notebook["cells"]
        if cell["cell_type"] == "code"
        and "ONTOLOGY_TTL_EMBEDDED = " in "".join(cell["source"])
    )
    first_line = "".join(cell["source"]).splitlines()[0]
    assignment = ast.parse(first_line).body[0]
    embedded_ttl = ast.literal_eval(assignment.value)
    assert embedded_ttl == ONTOLOGY_PATH.read_text(encoding="utf-8")


def test_notebook_declares_a_predictor_leakage_contract():
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    source = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )
    assert "FORBIDDEN_FEATURE_TOKENS" in source
    assert "assert 'SEQN' not in RAW_FEATURES" in source
    assert "LBXGH" in source
    assert "DIQ010" in source
    assert "DIQ160" in source
    assert "yes_no_flag(out,'hypertension_treatment')" in source
    assert "yn('hypertension_treatment')" in source
    assert "include_ethnicity=False" in source
    assert "race_ethnicity_ablation" in source
    assert "FEATURE_SETTINGS" in source
    assert "SETTING_3_FEATURES" in source
    assert "FORBIDDEN_SETTING_PREDICTORS" in source
