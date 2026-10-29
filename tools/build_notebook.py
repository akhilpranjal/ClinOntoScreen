"""Rebuild notebooks/01_nhanes_ontology_ml.ipynb from tools/nb_cells/.

The notebook is the canonical, self-contained Kaggle/Colab entry point. Cell sources live
in tools/nb_cells/ so they can be edited and reviewed as plain Python, and the embedded
ontology copy is always taken from ontology/diabetes_screening.ttl.

Usage:  python tools/build_notebook.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CELL_DIR = ROOT / "tools" / "nb_cells"
NOTEBOOK_PATH = ROOT / "notebooks" / "01_nhanes_ontology_ml.ipynb"
ONTOLOGY_PATH = ROOT / "ontology" / "diabetes_screening.ttl"

ORDER = [
    ("markdown", "cell00_intro.md"),
    ("code", "cell01_setup.py"),
    ("code", "cell02_data.py"),
    ("code", "cell03_ontology.py"),
    ("code", "cell04_qc.py"),
    ("code", "cell05_train_select.py"),
    ("code", "cell06_final_train.py"),
    ("code", "cell07_test_eval.py"),
    ("code", "cell08_low_data.py"),
    ("code", "cell09_missing_input.py"),
    ("code", "cell10_published_baseline.py"),
    ("code", "cell11_figures.py"),
    ("code", "cell12_save_artifacts.py"),
    ("markdown", "cell13_usage.md"),
]


def as_lines(text: str) -> list[str]:
    lines = text.splitlines()
    return [line + "\n" for line in lines[:-1]] + ([lines[-1]] if lines else [])


def main() -> None:
    ontology_ttl = ONTOLOGY_PATH.read_text(encoding="utf-8")
    cells = []
    for cell_type, filename in ORDER:
        source = (CELL_DIR / filename).read_text(encoding="utf-8")
        if filename == "cell03_ontology.py":
            marker = "ONTOLOGY_TTL_EMBEDDED = '__ONTOLOGY_TTL__'\n"
            if marker not in source:
                raise RuntimeError("cell03_ontology.py must contain the ontology placeholder line")
            ttl_literal = json.dumps(ontology_ttl)
            source = source.replace(marker, f"ONTOLOGY_TTL_EMBEDDED = {ttl_literal}\n")
        cell = {"cell_type": cell_type, "metadata": {}, "source": as_lines(source)}
        if cell_type == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        cells.append(cell)
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.10"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    NOTEBOOK_PATH.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {NOTEBOOK_PATH} with {len(cells)} cells")


if __name__ == "__main__":
    main()
