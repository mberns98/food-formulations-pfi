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
    1. Crea/Verifica Schemas (Bronze, model, Gold).
    2. Asegura la creación de todas las tablas (DDL).
    3. Limpia registros históricos si se solicita, preservando datos de la UI.
    """
    ddl_path = BASE_DIR / "data_engineering" / "ddl"
    schemas_path = ddl_path / "0_schemas"
    tables_path = ddl_path / "1_tables"
    
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        print("📁 Creando esquemas 'model' y 'analytics'...")
        for schema_file in sorted(os.listdir(schemas_path)):
            if schema_file.endswith(".sql"):
                file_path = schemas_path / schema_file
                
                # Leemos el contenido del archivo .sql
                with open(file_path, "r", encoding="utf-8") as f:
                    sql_script = f.read()
                
                # Ejecutamos el script leído
                print(f"  > Ejecutando: {schema_file}")
                cur.execute(sql_script)
        
        conn.commit()

        sql_files = sorted(tables_path.glob("*.sql"))
        
        if not sql_files:
            print("⚠️ No se encontraron archivos .sql en ddl/1_tables/")
        
        for file_path in sql_files:
            print(f"📖 Asegurando estructura: {file_path.name}")
            with open(file_path, "r", encoding="utf-8") as f:
                cur.execute(f.read())
        
        conn.commit()

        CLEAN_HISTORICAL = os.getenv("DROP_HISTORICAL_DATA_FIRST", "false").lower() == "true"
        
        if CLEAN_HISTORICAL:
            print("🧹 Limpiando registros (Vaciado total de hechos y limpieza selectiva de dimensiones)...")
            
            # 1. TABLAS DE HECHO Y PUENTES (Vaciado Total)
            total_clean = ["fact_form", "bridge_formula_ing", "dim_operarios"]
            
            # 2. DIMENSIONES 
            selective_clean = [
                "dim_formulaciones", "dim_ingredientes",
                "dim_evaluadores", "dim_dolar", "dim_tiempo", "dim_procesos"
            ]
            
            # Ejecutamos vaciado total primero
            for table in total_clean:
                print(f"  > Vaciando completamente: {table}")
                cur.execute(f"TRUNCATE model.{table} RESTART IDENTITY CASCADE;")

            # Ejecutamos limpieza selectiva después
            for table in selective_clean:
                print(f"  > Limpiando registros historical en: {table}")
                cur.execute(f"DELETE FROM model.{table} WHERE source = 'historical';")
            
            conn.commit() 
            print("✅ Limpieza completada.")

        print("🚀 ¡Arquitectura de datos lista y sincronizada!")

    except Exception as e:
        print(f"❌ Error crítico durante el setup: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    run_setup()