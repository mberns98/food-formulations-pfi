import sys
from pathlib import Path
import psycopg2

BASE_DIR = Path(__file__).resolve().parents[3] 
sys.path.append(str(BASE_DIR))

from src.config import DB_PARAMS

def insert_operarios():
    data = [
        ("Luisa", "Gómez", "LEG001"), 
        ("Miguel", "Paz", "LEG002"),
        ("Mayra", "Lopez", "XP2000"), 
        ("Lucas", "Gabriel", "R2D2")
    ]
    
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        cur.execute("SET search_path TO model, public;")
        cur.execute("DELETE FROM dim_operarios WHERE source = 'historical';")
        cur.executemany("INSERT INTO dim_operarios (nombre, apellido, legajo, source) VALUES (%s, %s, %s, %s)", 
                        [(name, last_name, legajo, 'historical') for name, last_name, legajo in data]
                        )
        
        conn.commit()
        print(f"✅ Operarios listos. Insertados: {len(data)}")
        cur.close()

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error en operarios: {e}")
        sys.exit(1) 
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    insert_operarios()