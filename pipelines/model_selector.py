import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

import mlflow
from src.config import MLFLOW_URI
from pipelines.data_loader import TARGETS

EXPERIMENT_NAME = "food_formulation_models"


def get_best_run_per_target() -> dict:
    """Return a dict of target -> {run_id, model_type, roc_auc, model_uri}."""
    mlflow.set_tracking_uri(MLFLOW_URI)
    client = mlflow.tracking.MlflowClient()

    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    if not experiment:
        raise ValueError(f"Experiment '{EXPERIMENT_NAME}' not found. Run train.py first.")

    results = {}
    for target in TARGETS:
        runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string=f"tags.target = '{target}' AND tags.is_best = 'true'",
            order_by=["metrics.roc_auc DESC"],
            max_results=1,
        )
        if not runs:
            raise ValueError(f"No best model found for target '{target}'. Run train.py first.")

        run = runs[0]
        results[target] = {
            "run_id":     run.info.run_id,
            "model_type": run.data.tags.get("model_type"),
            "roc_auc":    run.data.metrics.get("roc_auc"),
            "model_uri":  f"runs:/{run.info.run_id}/model",
        }

    return results
