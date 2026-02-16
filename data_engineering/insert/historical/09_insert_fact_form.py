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
    """Obtiene los IDs reales y el valor del dólar."""
    cur.execute("SET search_path TO model, public;")
    
    cur.execute("SELECT id_dolar, valor_oficial FROM dim_dolar ORDER BY fecha DESC LIMIT 1;")
    dolar_res = cur.fetchone()
    
    cur.execute("SELECT id_tiempo FROM dim_tiempo ORDER BY fecha DESC LIMIT 1;")
    tiempo_res = cur.fetchone()
    
    cur.execute("SELECT id_evaluador FROM dim_evaluadores LIMIT 1;")
    eval_res = cur.fetchone()
    
    cur.execute("SELECT id_proceso FROM dim_procesos LIMIT 1;")
    proc_res = cur.fetchone()

    if not all([dolar_res, tiempo_res, eval_res, proc_res]):
        raise Exception("Faltan datos en las dimensiones básicas. Revisá los scripts 01-07.")

    return dolar_res[0], dolar_res[1], tiempo_res[0], eval_res[0], proc_res[0]

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
        
        id_dolar, valor_dolar, id_tiempo, id_eval, id_proc = get_latest_ids(cur)

        print(f"🚀 Cargando Fact Table (Dólar ref: ${valor_dolar})...")
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
                SELECT 
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    COALESCE(SUM(b.proporcion * i.costo_unitario_ars), 0), -- Costo ARS
                    COALESCE(SUM(b.proporcion * i.costo_unitario_ars) / NULLIF(%s, 0), 0), -- Costo USD
                    'historical'
                FROM bridge_formula_ing b
                JOIN dim_ingredientes i ON b.id_ingrediente = i.id_ingrediente
                WHERE b.id_formula = %s
                GROUP BY b.id_formula;
                """,
                (
                    id_formula, id_eval, id_proc, id_dolar, id_tiempo,
                    int(row.aceptabilidad), int(row.dureza), 
                    int(row.elasticidad), int(row.color),
                    valor_dolar, 
                    id_formula
                )
            )
        
        conn.commit()
        print(f"✅ Fact Table cargada con registros históricos calculados.")

    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Error en la carga de Fact Table: {e}")
        sys.exit(1)
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    load_historical_fact()