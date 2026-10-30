import pandas as pd
import pytest
from src.clinontoscreen.data import (
    FEATURE_SETTINGS,
    make_cohort_table,
    assert_no_leakage,
    RAW_FEATURES,
)


def test_label_excludes_known_diabetes_and_prediabetes():
    frame = pd.DataFrame({
        "age_years": [25, 45, 50, 38],
        "reported_diabetes": [2, 1, 2, 2],
        "reported_prediabetes": [2, 2, 1, 2],
        "hba1c_percent": [5.8, 6.8, 6.0, 5.2],
    })
    cohort = make_cohort_table(frame)
    assert len(cohort) == 2
    assert cohort["target"].tolist() == [1, 0]


def test_feature_contract_has_no_leakage():
    assert_no_leakage(RAW_FEATURES)
    with pytest.raises(ValueError):
        assert_no_leakage(RAW_FEATURES + ["hba1c_percent"])
    with pytest.raises(ValueError):
        assert_no_leakage(RAW_FEATURES + ["SEQN"])


def test_all_feature_settings_exclude_target_and_questionnaire_sources():
    forbidden = {"LBXGH", "DIQ010", "DIQ160", "DIQ050", "DIQ070", "SEQN"}
    for name, features in FEATURE_SETTINGS.items():
        assert not forbidden.intersection(features), name
