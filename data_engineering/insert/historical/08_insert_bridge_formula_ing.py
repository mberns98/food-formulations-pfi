import sys
import pandas as pd
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR))

from src.config import DB_PARAMS, DATA_RAW, DATA_PROCESSED

CSV_PATH = DATA_RAW / "formulations_pfi.csv"
FORMULA_MAP_CSV = DATA_PROCESSED / "formulas_map.csv"

def insert_bridge_data():
    if not FORMULA_MAP_CSV.exists():
        print(f"❌ No existe el mapa: {FORMULA_MAP_CSV}")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    cols_output = ["aceptabilidad", "dureza", "elasticidad", "color"]
    df_ingredientes = df.drop(columns=cols_output)

    fmap = pd.read_csv(FORMULA_MAP_CSV)
    nombre_to_id = dict(zip(fmap["nombre"], fmap["id_formula"]))

    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("SET search_path TO model, public;")

        cur.execute("SELECT nombre, id_ingrediente FROM model.dim_ingredientes;")
        ing_map = {nombre.strip(): id_ing for nombre, id_ing in cur.fetchall()}

        rows = []
        missing_ings = set()

        print("🔗 Relacionando fórmulas con ingredientes (usando normalización)...")
        for idx, row in df_ingredientes.iterrows():
            nombre_formula = f"Fórmula {idx+1}"
            if nombre_formula not in nombre_to_id:
                continue
            
            id_formula = int(nombre_to_id[nombre_formula])


            for ingrediente_csv, proporcion in row.items():
                if pd.isna(proporcion) or proporcion <= 0:
                    continue
                
                # Normalizamos el nombre del CSV 
                ing_key = ingrediente_csv.strip()
                
                if ing_key not in ing_map:
                    missing_ings.add(ingrediente_csv)
                    continue
                
                id_ingrediente = int(ing_map[ing_key])
                rows.append((id_formula, id_ingrediente, round(float(proporcion), 4), 'historical'))

        if missing_ings:
            print(f"⚠️ {len(missing_ings)} ingredientes no encontrados en la DB. Ejemplos: {list(missing_ings)[:5]}")

        if rows:
            execute_values(
                cur,
                """
                INSERT INTO bridge_formula_ing (id_formula, id_ingrediente, proporcion, source)
                VALUES %s
                ON CONFLICT (id_formula, id_ingrediente)
                DO UPDATE SET 
                    proporcion = EXCLUDED.proporcion,
                    source = EXCLUDED.source
                """,
                rows,
                page_size=500
            )
            conn.commit()
            print(f"✅ bridge_formula_ing: {len(rows)} relaciones sincronizadas.")
        else:
            print("⚠️ No se generaron filas para insertar. Revisar match de nombres.")

    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Error en bridge: {e}")
        sys.exit(1)
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    insert_bridge_data()