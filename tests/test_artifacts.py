from src.clinontoscreen.reporting import json_safe
import numpy as np


def test_json_safe_normalizes_numpy_and_nan():
    result = json_safe({"count": np.int64(3), "score": np.float64(0.5), "missing": np.float64(np.nan)})
    assert result == {"count": 3, "score": 0.5, "missing": None}
