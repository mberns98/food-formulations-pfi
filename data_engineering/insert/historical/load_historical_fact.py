import sys
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3] 
sys.path.append(str(BASE_DIR))

import psycopg2
from src.config import DB_PARAMS, DATA_RAW, DATA_PROCESSED

RAW_DATA_CSV = DATA_RAW / "ingredientes_historicos.csv"
FORMULA_MAP_CSV = DATA_PROCESSED / "formulas_map.csv"

def get_latest_ids(cur):
    """Obtiene los IDs reales de las dimensiones ya pobladas."""
    # Obtenemos el último dólar y tiempo cargado
    cur.execute("SELECT id_dolar FROM dim_dolar ORDER BY id_dolar DESC LIMIT 1;")
    id_dolar = cur.fetchone()[0]

    cur.execute("SELECT id_tiempo FROM dim_tiempo ORDER BY id_tiempo DESC LIMIT 1;")
    id_tiempo = cur.fetchone()[0]

    # Tomamos el primer evaluador y proceso real que cargamos ayer
    cur.execute("SELECT id_evaluador FROM dim_evaluadores LIMIT 1;")
    id_eval = cur.fetchone()[0]

    cur.execute("SELECT id_proceso FROM dim_procesos LIMIT 1;")
    id_proc = cur.fetchone()[0]

    return id_dolar, id_tiempo, id_eval, id_proc

def load_historical_fact():
    if not FORMULA_MAP_CSV.exists():
        raise FileNotFoundError(f"❌ No existe el mapa en {FORMULA_MAP_CSV}. Corré load_historical_formulations.py primero.")

    # 1. Preparar mapeo y datos
    fmap = pd.read_csv(FORMULA_MAP_CSV)
    nombre_to_id = dict(zip(fmap["nombre"], fmap["id_formula"]))
    
    df = pd.read_csv(RAW_DATA_CSV)
    
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                # Limpiar solo histórico para evitar duplicados
                cur.execute("DELETE FROM fact_form WHERE source = 'historical';")
                
                # Obtener los IDs de las dimensiones reales
                id_dolar, id_tiempo, id_eval, id_proc = get_latest_ids(cur)

                print("🚀 Cargando Fact Table con datos históricos...")
                
                for idx, row in df.iterrows():
                    nombre_formula = f"Fórmula {idx+1}"
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
                            100.0, 0.0  # Valores por defecto para histórica
                        )
                    )
                conn.commit()
                print(f"✅ Fact Table cargada con {len(df)} registros vinculados.")

    except Exception as e:
        print(f"❌ Error en la carga de Fact Table: {e}")

if __name__ == "__main__":
    load_historical_fact()