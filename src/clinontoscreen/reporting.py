"""Artifact writing and reproducible research-result reports."""
from __future__ import annotations
import json
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
