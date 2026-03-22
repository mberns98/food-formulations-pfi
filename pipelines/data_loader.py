import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

import pandas as pd
import psycopg2
from src.config import DB_PARAMS

TARGETS = ["aceptabilidad", "dureza", "elasticidad", "color"]
NON_FEATURE_COLS = ["id_formula", "formula_nombre"] + TARGETS


def load_training_data() -> pd.DataFrame:
    conn = psycopg2.connect(**DB_PARAMS)
    df = pd.read_sql("SELECT * FROM use_cases.v_ml_training_set", conn)
    conn.close()
    return df


def get_feature_columns(df: pd.DataFrame) -> list:
    return [c for c in df.columns if c not in NON_FEATURE_COLS]
