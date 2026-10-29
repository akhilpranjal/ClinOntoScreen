%pip -q install pandas numpy requests scikit-learn xgboost rdflib joblib matplotlib

from __future__ import annotations
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone
import json, os, platform, warnings, zipfile, subprocess, sys
from IPython.display import display
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
from rdflib import Graph
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold, StratifiedShuffleSplit
from sklearn.metrics import (roc_auc_score, average_precision_score, brier_score_loss,
                             precision_score, recall_score, f1_score, confusion_matrix,
                             roc_curve, precision_recall_curve)
from sklearn.calibration import calibration_curve
from xgboost import XGBClassifier
import joblib

# Paths are selected for Kaggle, Colab, or a local Jupyter runtime.
if os.environ.get('CLINONTOSCREEN_WORK_DIR'):
    WORK_DIR = Path(os.environ['CLINONTOSCREEN_WORK_DIR'])
elif Path('/kaggle/working').exists() and ('KAGGLE_KERNEL_RUN_TYPE' in os.environ or Path('/kaggle/input').exists()):
    WORK_DIR = Path('/kaggle/working/clinontoscreen_run')
elif 'google.colab' in sys.modules:
    WORK_DIR = Path('/content/clinontoscreen_run')
else:
    WORK_DIR = Path.cwd() / 'clinontoscreen_run'
CACHE_DIR = WORK_DIR / 'data_cache'
ARTIFACT_DIR = WORK_DIR / 'artifacts'
CACHE_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

SEEDS = [17, 42, 123, 2025, 2026]
PRIMARY_CAPACITY = 0.20
CAPACITIES = [0.10, 0.20, 0.30]
N_BOOTSTRAP = 1000
LOW_DATA_FRACTIONS = [0.05, 0.10, 0.25, 0.50, 1.0]
LOW_DATA_REPEATS = 3
MASK_RATES = [0.0, 0.10, 0.30]
MASK_REPEATS = 3
MASK_COLUMNS = ['waist_cm', 'systolic_bp_mean', 'diastolic_bp_mean', 'hypertension_history',
                'vigorous_work_activity', 'moderate_work_activity',
                'vigorous_recreation_activity', 'moderate_recreation_activity']

def git_info():
    try:
        commit = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=10)
        exact = subprocess.run(['git', 'describe', '--tags', '--exact-match'], capture_output=True, text=True, timeout=10)
        nearest = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], capture_output=True, text=True, timeout=10)
        if exact.returncode == 0:
            tag, relation = exact.stdout.strip(), 'exact'
        elif nearest.returncode == 0:
            tag, relation = nearest.stdout.strip(), 'ancestor'
        else:
            tag, relation = 'not_tagged', 'none'
        return {
            'commit_hash': commit.stdout.strip() if commit.returncode == 0 else 'unavailable',
            'protocol_tag': tag,
            'tag_relation': relation,
        }
    except Exception:
        return {'commit_hash': 'unavailable', 'protocol_tag': 'not_tagged', 'tag_relation': 'none'}

PROTOCOL = git_info()
print('Work directory:', WORK_DIR)
print('Python:', platform.python_version(), '| pandas:', pd.__version__, '| scikit-learn:', __import__('sklearn').__version__)
print('Protocol commit:', PROTOCOL['commit_hash'], '| tag:', PROTOCOL['protocol_tag'])
print('Artifacts will be written to:', ARTIFACT_DIR)
