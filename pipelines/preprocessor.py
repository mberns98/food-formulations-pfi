import pandas as pd

TARGETS = ["aceptabilidad", "dureza", "elasticidad", "color"]


def binarize_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Convert 1-4 scale to binary: {1,2} -> 0 (bad), {3,4} -> 1 (good)."""
    df = df.copy()
    for t in TARGETS:
        df[t] = (df[t] >= 3).astype(int)
    return df


def get_X_y(df: pd.DataFrame, feature_cols: list, target: str):
    X = df[feature_cols].fillna(0).astype(float)
    y = df[target]
    return X, y
