import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

import json
import pickle
from functools import lru_cache

import mlflow
import pandas as pd

from src.config import MLFLOW_URI
from pipelines.model_selector import get_best_run_per_target
from pipelines.data_loader import TARGETS

mlflow.set_tracking_uri(MLFLOW_URI)


@lru_cache(maxsize=1)
def load_models():
    """Load best model per target from MLflow. Cached after first call."""
    best = get_best_run_per_target()
    client = mlflow.tracking.MlflowClient()

    models = {}
    feature_cols = None

    for target, info in best.items():
        model_path = client.download_artifacts(info["run_id"], "model/model.pkl")
        with open(model_path, "rb") as f:
            models[target] = pickle.load(f)

        if feature_cols is None:
            schema_path = client.download_artifacts(info["run_id"], "feature_schema.json")
            with open(schema_path) as f:
                feature_cols = json.load(f)["features"]

    return models, feature_cols


def predict(ingredient_dict: dict) -> dict:
    """
    Given a dict of {ingredient_name: proportion}, return predictions for all targets.

    Returns:
        {
            "aceptabilidad": {"prediction": 1, "probability": 0.87},
            ...
        }
    """
    models, feature_cols = load_models()

    X = pd.DataFrame([{col: float(ingredient_dict.get(col, 0.0)) for col in feature_cols}])

    results = {}
    for target in TARGETS:
        model = models[target]
        pred = int(model.predict(X)[0])
        prob = float(model.predict_proba(X)[0][1])
        results[target] = {"prediction": pred, "probability": round(prob, 4)}

    return results
