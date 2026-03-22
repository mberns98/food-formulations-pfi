import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

import os
import pickle
import tempfile

import mlflow
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from src.config import MLFLOW_URI
from pipelines.data_loader import load_training_data, get_feature_columns, TARGETS
from pipelines.preprocessor import binarize_targets, get_X_y

EXPERIMENT_NAME = "food_formulation_models"


def build_models(neg: int, pos: int) -> dict:
    spw = neg / pos if pos > 0 else 1.0
    return {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)),
        ]),
        "random_forest": RandomForestClassifier(
            n_estimators=100, class_weight="balanced", random_state=42
        ),
        "xgboost": XGBClassifier(
            n_estimators=100, scale_pos_weight=spw, random_state=42,
            eval_metric="logloss", verbosity=0,
        ),
        "lightgbm": LGBMClassifier(
            n_estimators=100, is_unbalance=True, random_state=42, verbose=-1
        ),
    }


def compute_metrics(y_true, y_pred, y_prob) -> dict:
    return {
        "accuracy":  accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall":    recall_score(y_true, y_pred, zero_division=0),
        "f1":        f1_score(y_true, y_pred, zero_division=0),
        "roc_auc":   roc_auc_score(y_true, y_prob),
    }


def train():
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    df = load_training_data()
    df = binarize_targets(df)
    feature_cols = get_feature_columns(df)

    print(f"Dataset: {len(df)} rows | {len(feature_cols)} features")
    print("Class distributions after binarization:")
    for t in TARGETS:
        dist = df[t].value_counts().sort_index().to_dict()
        print(f"  {t}: {dist}")

    best_runs = {}  # target -> (run_id, roc_auc)

    for target in TARGETS:
        X, y = get_X_y(df, feature_cols, target)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        neg = int((y_train == 0).sum())
        pos = int((y_train == 1).sum())

        print(f"\n--- {target} | train={len(X_train)} test={len(X_test)} | neg={neg} pos={pos} ---")

        models = build_models(neg, pos)

        for model_name, model in models.items():
            run_name = f"{target}_{model_name}"

            with mlflow.start_run(run_name=run_name) as run:
                model.fit(X_train, y_train)

                y_pred = model.predict(X_test)
                y_prob = model.predict_proba(X_test)[:, 1]

                metrics = compute_metrics(y_test, y_pred, y_prob)

                mlflow.log_params({
                    "model_type":  model_name,
                    "target":      target,
                    "train_size":  len(X_train),
                    "test_size":   len(X_test),
                    "n_features":  len(feature_cols),
                    "class_0":     int((y == 0).sum()),
                    "class_1":     int((y == 1).sum()),
                })
                mlflow.log_metrics(metrics)
                mlflow.set_tags({"target": target, "model_type": model_name})
                mlflow.log_dict({"features": feature_cols}, "feature_schema.json")

                with tempfile.TemporaryDirectory() as tmp:
                    model_path = os.path.join(tmp, "model.pkl")
                    with open(model_path, "wb") as f:
                        pickle.dump(model, f)
                    mlflow.log_artifact(model_path, artifact_path="model")

                roc = metrics["roc_auc"]
                print(f"  {run_name}: ROC-AUC={roc:.4f}  F1={metrics['f1']:.4f}")

                if target not in best_runs or roc > best_runs[target][1]:
                    best_runs[target] = (run.info.run_id, roc)

    # Tag best model per target
    print("\n--- Best models ---")
    for target, (run_id, roc) in best_runs.items():
        with mlflow.start_run(run_id=run_id):
            mlflow.set_tag("is_best", "true")
        print(f"  {target}: run_id={run_id}  ROC-AUC={roc:.4f}")

    print("\nTraining complete. Open MLflow UI at", MLFLOW_URI)


if __name__ == "__main__":
    train()
