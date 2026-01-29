import sys
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

import psycopg2
from src.config import DB_PARAMS, DATA_PROCESSED # Ahora sí existe

MAP_OUT = DATA_PROCESSED / "formulas_map.csv"

def load_historical_formulations():

    formulas = [(f"Fórmula {i}", "vegana", None, "1.0") for i in range(1, 48)]
    mapa = [] 

    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM dim_formulas WHERE source = 'historical';")
                cur.execute("ALTER SEQUENCE dim_formulas_id_formula_seq RESTART WITH 1;")

                for nombre, tipo, descripcion, version in formulas:
                    cur.execute(
                        """
                        INSERT INTO dim_formulas (nombre, tipo, descripcion, version, source)
                        VALUES (%s, %s, %s, %s, 'historical')
                        RETURNING id_formula;
                        """,
                        (nombre, tipo, descripcion, version),
                    )
                    new_id = cur.fetchone()[0]
                    mapa.append({"nombre": nombre, "id_formula": new_id})
                conn.commit()
        
        pd.DataFrame(mapa).to_csv(MAP_OUT, index=False)
        print(f"✅ Fórmulas insertadas. Mapa en: {MAP_OUT}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    load_historical_formulations()