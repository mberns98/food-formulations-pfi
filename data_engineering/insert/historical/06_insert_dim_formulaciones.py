import sys
import pandas as pd
import psycopg2
from psycopg2.extras import Json
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parents[3] 
sys.path.append(str(BASE_DIR))

from src.config import DB_PARAMS, DATA_PROCESSED

RAW_DATA_PATH = BASE_DIR / "data" / "0_raw" / "formulations_pfi.csv"
MAP_OUT = DATA_PROCESSED / "formulas_map.csv"

def load_historical_formulations():
    df_raw = pd.read_csv(RAW_DATA_PATH)
    
    meta_columns = ['aceptabilidad', 'dureza', 'elasticidad', 'color']
    ingredient_columns = [c for c in df_raw.columns if c not in meta_columns]

    mapa = [] 

    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("SET search_path TO model;")
                
                print("🧹 Limpiando formulaciones históricas...")
                cur.execute("DELETE FROM model.dim_formulaciones WHERE source = 'historical';")
                cur.execute("ALTER SEQUENCE model.dim_formulaciones_id_formula_seq RESTART WITH 1;")

                print(f"🚀 Procesando {len(df_raw)} fórmulas desde el CSV...")
                
                for i, row in df_raw.iterrows():
                    composicion_dict = {
                        ing: float(row[ing]) 
                        for ing in ingredient_columns 
                        if row[ing] > 0
                    }

                    nombre = f"Fórmula {i+1}"
                    tipo = "vegana"
                    descripcion = f"Carga histórica automatizada - Fila {i+1}"
                    
                    cur.execute(
                        """
                        INSERT INTO model.dim_formulaciones 
                        (nombre, tipo, descripcion, fecha_creacion, version, composicion, source)
                        VALUES (%s, %s, %s, %s, %s, %s, 'historical')
                        RETURNING id_formula;
                        """,
                        (nombre, tipo, descripcion, date(2025, 1, 1), "1.0", Json(composicion_dict)),
                    )
                    
                    new_id = cur.fetchone()[0]
                    mapa.append({"nombre": nombre, "id_formula": new_id})
                
                conn.commit()
        
        MAP_OUT.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(mapa).to_csv(MAP_OUT, index=False)
        print(f"✅ {len(mapa)} Fórmulas insertadas con éxito.")

    except Exception as e:
        print(f"❌ Error en formulaciones: {e}")

if __name__ == "__main__":
    load_historical_formulations()