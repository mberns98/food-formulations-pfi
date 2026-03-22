# Technical Notes — Design Decisions & Dataset Constraints

This document justifies the key engineering and ML design decisions made in this project, and provides honest context about dataset limitations for academic evaluation purposes.

---

## 1. Dataset Constraints

### Size
The dataset contains **47 historical formulations** collected in a controlled laboratory setting. This is a known constraint of the project scope — data collection requires physical lab trials, which are resource-intensive and time-limited.

### Class Imbalance
After binarization, the class distribution is highly skewed toward class 0 (not acceptable):

| Target | Class 0 | Class 1 |
|---|---|---|
| aceptabilidad | 42 | 5 |
| dureza | 43 | 4 |
| elasticidad | 43 | 4 |
| color | 44 | 3 |

This reflects a real-world phenomenon: most experimental formulations do not reach acceptable quality on the first attempt. It is not a data collection artifact.

### Interpretation of Metrics
Given the dataset size and class imbalance, reported metrics (especially ROC-AUC) should be interpreted as **proof-of-concept indicators**, not as estimates of generalization performance. A 47-row dataset with a single 80/20 split yields test sets of ~10 rows, making metric variance high by definition.

The primary value of this pipeline is **architectural demonstration**, not predictive accuracy.

---

## 2. Target Transformation — Binary Classification

### Decision
Each sensory attribute (originally scored 1–4) is binarized:
- `{1, 2}` → `0` (not acceptable)
- `{3, 4}` → `1` (acceptable)

### Justification
- **Simplifies the learning problem** given the small dataset. A 4-class multiclass problem with 47 rows and severe imbalance would be intractable.
- **Aligns with domain logic**: the practical question is binary — does a formulation meet minimum quality standards or not?
- **Enables ROC-AUC** as a threshold-independent evaluation metric, which is appropriate for imbalanced binary problems.
- Binarization at the midpoint (≥3 = acceptable) is consistent with standard sensory evaluation practice where 3/4 represents the minimum acceptable hedonic score.

---

## 3. Model Selection — Four Algorithms

### Decision
Four model families were trained per target: Logistic Regression, Random Forest, XGBoost, LightGBM.

### Justification
- **Logistic Regression**: linear baseline, interpretable, requires feature scaling (applied via Pipeline). Serves as the reference model.
- **Random Forest**: non-linear ensemble, robust to irrelevant features, handles sparse data well — relevant given the wide, sparse ingredient feature matrix.
- **XGBoost**: gradient boosting with built-in handling for imbalanced classes via `scale_pos_weight`.
- **LightGBM**: efficient gradient boosting, `is_unbalance=True` flag explicitly addresses class imbalance.

This selection covers the main ML paradigms (linear, bagging, boosting) and is standard practice in applied ML benchmarking.

---

## 4. Feature Engineering — Ingredient Pivot

### Decision
The feature matrix is a **wide pivot** of ingredient proportions: one column per ingredient, value is the proportion used (0 if absent). This is generated dynamically as a SQL view (`use_cases.v_ml_training_set`).

### Justification
- Ingredient proportions are the natural, domain-meaningful representation of a formulation.
- The pivot is **sparse by design** — most formulations use a small subset of the 63 available ingredients. Tree-based models handle sparse matrices efficiently.
- Storing this as a SQL view (not a materialized table) ensures the feature schema always reflects the current ingredient catalog without manual updates.

---

## 5. Model Selection Criterion — ROC-AUC

### Decision
The best model per target is selected by **ROC-AUC**, not accuracy or F1.

### Justification
- Accuracy is misleading under class imbalance: a model that always predicts class 0 achieves ~90% accuracy but is useless.
- ROC-AUC measures the model's ability to **rank** positive cases above negative cases, independent of the classification threshold. This is the appropriate metric when class distributions are skewed.
- F1 is threshold-dependent and sensitive to the minority class size; less stable with very small positive counts (3–5 samples).

---

## 6. Infrastructure — MLflow for Experiment Tracking

### Decision
MLflow is used to log all 16 training runs with parameters, metrics, and model artifacts. The best model per target is tagged (`is_best=true`) and loaded at inference time.

### Justification
- Provides **full reproducibility**: every run records its hyperparameters, dataset statistics, and evaluation metrics.
- The `predictor.py` module queries MLflow at runtime to load the best model, decoupling training from serving.
- Using MLflow's artifact store for model persistence avoids hardcoding model paths and supports future retraining without changing serving code.

---

## 7. Serving Layer — FastAPI + Streamlit

### Decision
Two separate interfaces: a REST API (FastAPI) and a web UI (Streamlit).

### Justification
- **FastAPI** exposes a standard `POST /predict` endpoint, demonstrating that the model can be consumed programmatically by any external system.
- **Streamlit** provides an interactive UI for non-technical users (lab operators, formulators) to input ingredient proportions and receive predictions directly.
- Keeping them separate follows the principle of separation of concerns: the serving logic (`predictor.py`) is shared by both without duplication.

---

## Summary

This project demonstrates a complete MLOps pipeline within the constraints of an academic proof-of-concept:

- The **architecture is production-aligned** in structure and design patterns
- The **dataset size is a known constraint**, acknowledged explicitly in all metric interpretations
- All **design decisions are domain-justified**, not arbitrary
- The system is **fully reproducible** from a fresh environment using the steps in `README.md`
