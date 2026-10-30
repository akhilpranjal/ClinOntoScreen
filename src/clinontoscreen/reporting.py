"""Artifact writing and reproducible research-result reports."""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
import numpy as np
import re
import shutil


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


def load_results(root: str | Path) -> dict | None:
    """Prefer private runtime artifacts, falling back to committed aggregate results."""
    root = Path(root)
    for candidate in (root / "artifacts" / "research_results.json", root / "results" / "research_results.json"):
        if candidate.exists():
            return json.loads(candidate.read_text(encoding="utf-8"))
    return None


def export_public_results(source: str | Path, destination: str | Path) -> list[Path]:
    """Copy aggregate result files while refusing participant identifiers or large tabular outputs."""
    source, destination = Path(source), Path(destination)
    if not source.exists():
        raise FileNotFoundError(source)
    allowed = {
        "research_results.json", "run_manifest.json", "tier1_metrics.csv", "figures.json",
        "roc_pr_curves.png", "calibration.png", "capacity_sensitivity.png", "primary_effect_ci.png",
    }
    destination.mkdir(parents=True, exist_ok=True)
    copied = []
    for path in source.iterdir():
        if not path.is_file() or path.name not in allowed:
            continue
        data = path.read_bytes()
        if re.search(rb"\bSEQN\b", data, flags=re.IGNORECASE):
            raise ValueError(f"Participant identifier SEQN found in {path}")
        if path.suffix.lower() == ".csv" and data.count(b"\n") > 1001:
            raise ValueError(f"Refusing implausibly large public table: {path}")
        target = destination / path.name
        shutil.copy2(path, target)
        copied.append(target)
    if not copied:
        raise ValueError(f"No allow-listed aggregate results found in {source}")
    return copied
