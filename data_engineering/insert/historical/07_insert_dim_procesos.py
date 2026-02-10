import sys
from pathlib import Path
import psycopg2

BASE_DIR = Path(__file__).resolve().parents[3] 
sys.path.append(str(BASE_DIR))

from src.config import DB_PARAMS

def insert_procesos():
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        cur.execute("SET search_path TO model, public;")
        
        print("🔍 Buscando operarios en model.dim_operarios...")
        cur.execute("SELECT id_operario, nombre FROM model.dim_operarios;")
        operarios_map = {row[1]: row[0] for row in cur.fetchall()}

        if not operarios_map:
            raise Exception("La tabla model.dim_operarios está vacía. Verificá el script 03.")

        print(f"✅ Operarios encontrados: {list(operarios_map.keys())}")

        id_luisa = operarios_map.get("Luisa")
        id_miguel = operarios_map.get("Miguel")

        if id_luisa is None or id_miguel is None:
            raise Exception(f"No se encontró el ID para Luisa ({id_luisa}) o Miguel ({id_miguel})")

        data = [
            (id_luisa, "Extrusión estándar", "Proceso a 130°C durante 15 minutos", 130, 15),
            (id_miguel, "Horneado corto", "Horno a 180°C durante 10 minutos", 180, 10),
        ]

        print("⚙️ Insertando procesos...")
        cur.execute("TRUNCATE TABLE model.dim_procesos RESTART IDENTITY CASCADE;")
        
        cur.executemany(
            """
            INSERT INTO model.dim_procesos (id_operario, nombre, descripcion, temperatura, tiempo_minutos) 
            VALUES (%s, %s, %s, %s, %s)
            """, 
            data
        )
        
        conn.commit()
        print("✅ Procesos listos.")

    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Error en procesos: {e}")
        sys.exit(1)
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    insert_procesos()