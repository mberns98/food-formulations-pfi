# PFI — MLOps Platform for Vegan Food Formulations

End-to-end ML engineering project that integrates a data warehouse, experiment tracking, model training, model serving, and a data entry UI for vegan food product formulation.

---

## Architecture Overview

```
PostgreSQL (DWH)
    └── model schema (star schema: dims + fact + bridge)
    └── use_cases schema (ML training view)
        │
        ▼
pipelines/
    ├── data_loader.py       # Reads training view from Postgres
    ├── preprocessor.py      # Binarizes targets, builds feature matrix
    ├── train.py             # Trains 16 models, logs to MLflow
    └── model_selector.py    # Queries MLflow for best model per target
        │
        ▼
MLflow (experiment tracking + artifact storage)
        │
        ▼
serve/
    ├── predictor.py         # Loads best models from MLflow, runs inference
    └── api.py               # FastAPI: POST /predict
        │
        ▼
app/
    ├── main.py              # Streamlit UI (data entry + quality prediction)
    └── database.py          # DB write logic for operational data
```

---

## Stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL 15 (Docker) |
| Data Warehouse | Star schema (model + use_cases schemas) |
| Experiment Tracking | MLflow 3.x |
| ML Models | scikit-learn, XGBoost, LightGBM |
| Model Serving | FastAPI + Uvicorn |
| UI | Streamlit |
| Dependency Management | Poetry |
| Containerization | Docker Compose |

---

## Project Structure

```
├── app/
│   ├── main.py                  # Streamlit app
│   └── database.py              # DB write logic
├── data_engineering/
│   ├── ddl/                     # SQL schemas and table definitions
│   ├── insert/historical/       # Historical data loading scripts
│   └── scripts/                 # Setup and pipeline orchestrators
├── pipelines/
│   ├── data_loader.py
│   ├── preprocessor.py
│   ├── train.py
│   └── model_selector.py
├── serve/
│   ├── predictor.py
│   └── api.py
├── src/
│   └── config.py                # Centralized config (DB, MLflow URI)
├── data/
│   ├── 0_raw/                   # Raw CSV (gitignored)
│   └── 2_processed/             # Formula ID map
├── docker-compose.yml
└── pyproject.toml
```

---

## Setup & Reproduction

### 1. Prerequisites

- Docker Desktop running
- Python 3.10+
- Poetry installed (`pip install poetry`)

### 2. Environment

Create a `.env` file at the project root:

```
POSTGRES_DB=food_pfi
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
MLFLOW_TRACKING_URI=http://127.0.0.1:5000
```

### 3. Start infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL (port 5432) and MLflow (port 5000).

### 4. Install dependencies

```bash
poetry install
```

### 5. Initialize the data warehouse

```bash
# Create schemas and tables
poetry run python data_engineering/scripts/run_setup.py

# Load historical data (requires data/0_raw/Formulas_nuevo.csv)
poetry run python data_engineering/scripts/run_all_historical.py
```

> **Exchange rates:** the historical pipeline automatically fetches live USD/ARS rates (oficial + blue) from [dolarapi.com](https://dolarapi.com) — no API key required. If the API is unreachable, it falls back to the most recent rate stored in the database.

### 6. Train models

```bash
poetry run python pipelines/train.py
```

Trains 16 models (4 targets × 4 algorithms), logs all runs to MLflow, and tags the best model per target by ROC-AUC. View results at `http://localhost:5000`.

### 7. Run the Streamlit app

```bash
poetry run streamlit run app/main.py
```

Access at `http://localhost:8501`. Two modes:
- **Cargar nueva formulación** — enter a new formulation with sensory evaluation
- **Evaluar nueva formulación** — predict quality attributes for a given ingredient mix

### 8. Run the FastAPI (optional)

```bash
poetry run uvicorn serve.api:app --host 0.0.0.0 --port 8000 --reload
```

Interactive docs at `http://localhost:8000/docs`.

---

## ML Pipeline

### Targets

Four sensory attributes evaluated on a 1–4 scale:

| Target | Description |
|---|---|
| `aceptabilidad` | Overall consumer acceptance |
| `dureza` | Hardness (texture) |
| `elasticidad` | Elasticity (texture) |
| `color` | Visual color quality |

### Target Transformation

Each target is binarized before training:

```
{1, 2} → 0  (not acceptable)
{3, 4} → 1  (acceptable)
```

### Models trained per target

- Logistic Regression (with StandardScaler)
- Random Forest
- XGBoost
- LightGBM

### Model Selection

Best model per target is selected by **ROC-AUC** on the held-out test set (80/20 stratified split). The winning run is tagged `is_best=true` in MLflow.

### API Example

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": {
      "Agua": 0.631,
      "Aceite_coco": 0.04,
      "Sal": 0.013,
      "gluten_de_trigo": 0.18
    }
  }'
```

Response:

```json
{
  "aceptabilidad": { "prediction": 1, "probability": 0.82 },
  "dureza":        { "prediction": 0, "probability": 0.31 },
  "elasticidad":   { "prediction": 1, "probability": 0.74 },
  "color":         { "prediction": 1, "probability": 0.91 }
}
```

---

## Dataset & Limitations

See `TECHNICAL_NOTES.md` for a full discussion of design decisions and dataset constraints.
