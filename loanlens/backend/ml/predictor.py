# backend/ml/predictor.py
"""Machine learning inference utilities for LoanLens."""
import joblib
import pandas as pd
from pathlib import Path

MODEL_DIR = Path(__file__).parent
RF_MODEL_PATH = MODEL_DIR / 'models' / 'random_forest.pkl'
LR_MODEL_PATH = MODEL_DIR / 'models' / 'logistic_regression.pkl'

def _load_model():
    if RF_MODEL_PATH.exists():
        return joblib.load(RF_MODEL_PATH)
    elif LR_MODEL_PATH.exists():
        return joblib.load(LR_MODEL_PATH)
    else:
        raise FileNotFoundError('No trained model found.')

_MODEL = _load_model()

def predict_consistency_pattern(features: pd.DataFrame) -> pd.Series:
    return pd.Series(_MODEL.predict(features), index=features.index)
