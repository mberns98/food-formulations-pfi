import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

import psycopg2
from src.config import DB_PARAMS

def load_time_and_dolar():
    """Carga los registros iniciales para tiempo y dólar."""
    today = date.today()
    
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE dim_tiempo, dim_dolar RESTART IDENTITY CASCADE;")

                # 2. Insertar Tiempo (Hoy)
                cur.execute(
                    """
                    INSERT INTO dim_tiempo (fecha, mes, anio, dia_semana)
                    VALUES (%s, %s, %s, %s) RETURNING id_tiempo;
                    """,
                    (today, today.month, today.year, today.strftime("%A"))
                )
                id_tiempo = cur.fetchone()[0]

                # 3. Insertar Dólar (Valor manual para el histórico) -> Manejar con API en el futuro
                cur.execute(
                    """
                    INSERT INTO dim_dolar (fecha, valor_oficial, valor_blue, fuente)
                    VALUES (%s, %s, %s, %s) RETURNING id_dolar;
                    """,
                    (today, 950.00, 1200.00, "Manual-Setup")
                )
                id_dolar = cur.fetchone()[0]

                conn.commit()
                print(f"✅ Dimensiones de soporte listas: Tiempo ID {id_tiempo}, Dólar ID {id_dolar}")

    except Exception as e:
        print(f"❌ Error cargando dimensiones de soporte: {e}")

if __name__ == "__main__":
    load_time_and_dolar()