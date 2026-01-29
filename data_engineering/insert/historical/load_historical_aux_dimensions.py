import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3] 
sys.path.append(str(BASE_DIR))

import psycopg2
from src.config import DB_PARAMS

def load_metadata():
    # 1. Group mock data by dimensions
    evaluadores = [
        ("Rick", "Astley", False), 
        ("Bill", "Evans", True), 
        ("Miles", "Coltrane", True), 
        ("Diana", "Krall", True)
    ]
    
    operarios = [
        ("Luisa", "Gómez", "LEG001"), ("Miguel", "Paz", "LEG002"),
        ("Mayra", "Lopez", "XP2000"), ("Lucas", "Gabriel", "R2D2")
    ]
    
    procesos = [
        (1, "Extrusión estándar", "Proceso a 130°C durante 15 minutos", 130, 15),
        (2, "Horneado corto", "Horno a 180°C durante 10 minutos", 180, 10),
    ]

    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cursor:
                # Limpieza total con RESTART IDENTITY
                tables = ["dim_procesos", "dim_operarios", "dim_evaluadores"]
                for table in tables:
                    cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")

                # Cargas masivas
                cursor.executemany("INSERT INTO dim_evaluadores (nombre, apellido, is_trained) VALUES (%s, %s, %s)", evaluadores)
                cursor.executemany("INSERT INTO dim_operarios (nombre, apellido, legajo) VALUES (%s, %s, %s)", operarios)
                cursor.executemany("INSERT INTO dim_procesos (id_operario, nombre, descripcion, temperatura, tiempo_minutos) VALUES (%s, %s, %s, %s, %s)", procesos)
                
                conn.commit()
                print("✅ Metadata (Evaluadores, Operarios, Procesos) cargada con éxito.")

    except Exception as e:
        print(f"❌ Error en carga de metadata: {e}")

if __name__ == "__main__":
    load_metadata()