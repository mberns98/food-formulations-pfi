import os
import sys
from pathlib import Path
import psycopg2

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

from src.config import DB_PARAMS

def run_setup():
    """
    Orquestador de arquitectura de datos:
    1. Crea Schemas (Bronze, Silver, Gold).
    2. Ejecuta archivos SQL de tablas en orden alfabético.
    """
    ddl_path = BASE_DIR / "data_engineering" / "ddl"
    tables_path = ddl_path / "1_tables"
    
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # --- 1. Borrar Schemas Antiguos (opcional) ---
        DROP_ALL = os.getenv("DROP_SCHEMAS_FIRST", "false").lower() == "true"
        if DROP_ALL:
            print("🧹 Borrando schemas antiguos (Clean Slate)...")
            for schema in ["bronze", "silver", "gold"]:
                cur.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")

        # --- 2. Crear Schemas ---
        print("📁 Creando estructuras Bronze, Silver y Gold...")
        for schema in ["bronze", "silver", "gold"]:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")

        # --- 3. Ejecutar Tablas ---
        # Usamos sorted() para que 01_ se ejecute antes que 02_
        sql_files = sorted(tables_path.glob("*.sql"))
        
        if not sql_files:
            print("⚠️ No se encontraron archivos .sql en ddl/1_tables/")
        
        for file_path in sql_files:
            print(f"📖 Ejecutando: {file_path.name}")
            with open(file_path, "r", encoding="utf-8") as f:
                cur.execute(f.read())

        conn.commit()
        print("🚀 ¡Arquitectura de datos desplegada con éxito!")

    except Exception as e:
        print(f"❌ Error durante el setup: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    run_setup()