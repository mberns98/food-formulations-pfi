import sys
from pathlib import Path
import psycopg2

BASE_DIR = Path(__file__).resolve().parents[3] 
sys.path.append(str(BASE_DIR))

from src.config import DB_PARAMS

def insert_evaluadores():
    data = [
        ("Rick", "Astley", False), 
        ("Bill", "Evans", True), 
        ("Miles", "Coltrane", True), 
        ("Diana", "Krall", True)
    ]
    
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("SET search_path TO model, public;")
                print("👥 Insertando evaluadores...")
                
                cur.execute("DELETE FROM model.dim_evaluadores WHERE source = 'historical';")
                cur.executemany(
                    "INSERT INTO model.dim_evaluadores (nombre, apellido, is_trained, source) VALUES (%s, %s, %s, %s)", 
                    [(name, last_name, is_trained, 'historical') for name, last_name, is_trained in data]
                )
                conn.commit()
                print("✅ Evaluadores listos.")
    except Exception as e:
        print(f"❌ Error en evaluadores: {e}")

if __name__ == "__main__":
    insert_evaluadores()