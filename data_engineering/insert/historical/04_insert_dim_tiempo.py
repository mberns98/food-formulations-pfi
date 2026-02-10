import sys
from datetime import date
from pathlib import Path
import psycopg2

BASE_DIR = Path(__file__).resolve().parents[3] 
sys.path.append(str(BASE_DIR))

from src.config import DB_PARAMS

def insert_dim_tiempo():
    today = date.today()
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("SET search_path TO model, public;")
                
                print(f"📅 Insertando fecha actual ({today}) en dim_tiempo...")
                cur.execute(
                    """
                    INSERT INTO dim_tiempo (fecha, mes, anio, dia_semana, source)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (fecha) DO NOTHING;
                    """,
                    (today, today.month, today.year, today.strftime("%A"), "historical")
                )
                conn.commit()
                print("✅ Dimensión Tiempo actualizada.")
    except Exception as e:
        print(f"❌ Error en dim_tiempo: {e}")

if __name__ == "__main__":
    insert_dim_tiempo()