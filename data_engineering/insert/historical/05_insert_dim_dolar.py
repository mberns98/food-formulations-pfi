import sys
from datetime import date
from pathlib import Path
import psycopg2

BASE_DIR = Path(__file__).resolve().parents[3] 
sys.path.append(str(BASE_DIR))

from src.config import DB_PARAMS

def insert_dim_dolar():
    today = date.today()
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("SET search_path TO model, public;")
                
                print(f"💵 Insertando cotización del dólar para {today}...")
                cur.execute(
                    """
                    INSERT INTO model.dim_dolar (fecha, valor_oficial, valor_blue, fuente)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (fecha) DO UPDATE 
                    SET valor_oficial = EXCLUDED.valor_oficial, 
                        valor_blue = EXCLUDED.valor_blue;
                    """,
                    (today, 950.00, 1200.00, "Manual-Setup")
                )
                conn.commit()
                print("✅ Dimensión Dólar actualizada.")
    except Exception as e:
        print(f"❌ Error en dim_dolar: {e}")

if __name__ == "__main__":
    insert_dim_dolar()