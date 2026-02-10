import sys
import pandas as pd
from pathlib import Path
import psycopg2

BASE_DIR = Path(__file__).resolve().parents[3] 
sys.path.append(str(BASE_DIR))

from src.config import DB_PARAMS, DATA_RAW, DATA_PROCESSED

RAW_DATA_CSV = DATA_RAW / "formulations_pfi.csv"
FORMULA_MAP_CSV = DATA_PROCESSED / "formulas_map.csv"

def get_latest_ids(cur):
    cur.execute("SET search_path TO model, public;")
    """Obtiene los IDs reales y valida que las tablas no estén vacías."""
    queries = {
        "id_dolar": "SELECT id_dolar FROM dim_dolar ORDER BY id_dolar DESC LIMIT 1;",
        "id_tiempo": "SELECT id_tiempo FROM dim_tiempo ORDER BY id_tiempo DESC LIMIT 1;",
        "id_eval": "SELECT id_evaluador FROM dim_evaluadores LIMIT 1;",
        "id_proc": "SELECT id_proceso FROM dim_procesos LIMIT 1;"
    }
    
    results = {}
    for key, query in queries.items():
        cur.execute(query)
        res = cur.fetchone()
        if res is None:
            raise Exception(f"La tabla asociada a '{key}' está vacía. Revisá los scripts previos (04-07).")
        results[key] = res[0]
        
    return results["id_dolar"], results["id_tiempo"], results["id_eval"], results["id_proc"]

def load_historical_fact():
    if not FORMULA_MAP_CSV.exists():
        print(f"❌ No existe el mapa en {FORMULA_MAP_CSV}")
        sys.exit(1)

    fmap = pd.read_csv(FORMULA_MAP_CSV)
    nombre_to_id = dict(zip(fmap["nombre"], fmap["id_formula"]))
    df = pd.read_csv(RAW_DATA_CSV)
    
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SET search_path TO model, public;")
        
        # Obtener IDs con validación
        id_dolar, id_tiempo, id_eval, id_proc = get_latest_ids(cur)

        print("🚀 Cargando Fact Table con datos históricos...")
        cur.execute("DELETE FROM fact_form WHERE source = 'historical';")
        
        for idx, row in df.iterrows():
            nombre_formula = f"Fórmula {idx+1}"
            if nombre_formula not in nombre_to_id:
                continue

            id_formula = int(nombre_to_id[nombre_formula])

            cur.execute(
                """
                INSERT INTO fact_form (
                    id_formula, id_evaluador, id_proceso, id_dolar, id_tiempo,
                    aceptabilidad, dureza, elasticidad, color,
                    precio_ars, precio_usd, source
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'historical');
                """,
                (
                    id_formula, id_eval, id_proc, id_dolar, id_tiempo,
                    int(row.aceptabilidad), int(row.dureza), 
                    int(row.elasticidad), int(row.color),
                    100.0, 0.0
                )
            )
        
        conn.commit()
        print(f"✅ Fact Table cargada con {len(df)} registros vinculados.")

    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Error en la carga de Fact Table: {e}")
        sys.exit(1)
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    load_historical_fact()