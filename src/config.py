import os
from pathlib import Path
from dotenv import load_dotenv

# BASE_DIR points to the project root (one level up from src/)
BASE_DIR = Path(__file__).resolve().parents[1]

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

# Dynamic data paths based on project structure
DATA_RAW = BASE_DIR / "data" / "0_raw"
DATA_INTERIM = BASE_DIR / "data" / "1_interim"

# Centralized Database Configuration
DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
}

# MLflow Tracking Configuration
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")