import sys
from datetime import date
from pathlib import Path
import psycopg2
import requests

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR))

from src.config import DB_PARAMS

DOLAR_API_URL = "https://dolarapi.com/v1/dolares"


def fetch_dolar_rates() -> tuple:
    """
    Fetches current USD/ARS exchange rates from dolarapi.com.
    Returns (valor_oficial, valor_blue).
    Falls back to the last known values in dim_dolar if the API is unavailable.
    """
    try:
        response = requests.get(DOLAR_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        oficial = next((d for d in data if d.get("casa") == "oficial"), None)
        blue    = next((d for d in data if d.get("casa") == "blue"), None)

        valor_oficial = float(oficial["venta"]) if oficial else None
        valor_blue    = float(blue["venta"])    if blue    else None

        return valor_oficial, valor_blue

    except Exception as e:
        print(f"⚠️  No se pudo conectar a dolarapi.com: {e}")
        return None, None


def get_fallback_rates(cur) -> tuple:
    """Returns the most recent rates stored in dim_dolar as a fallback."""
    cur.execute("""
        SELECT valor_oficial, valor_blue
        FROM model.dim_dolar
        ORDER BY fecha DESC
        LIMIT 1;
    """)
    row = cur.fetchone()
    return (float(row[0]), float(row[1])) if row else (0.0, 0.0)


def insert_dim_dolar():
    today = date.today()
    try:
        with psycopg2.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("SET search_path TO model, public;")

                valor_oficial, valor_blue = fetch_dolar_rates()

                if valor_oficial is None or valor_blue is None:
                    print("↩️  Usando cotización más reciente de la base de datos como fallback...")
                    fallback_oficial, fallback_blue = get_fallback_rates(cur)
                    valor_oficial = valor_oficial or fallback_oficial
                    valor_blue    = valor_blue    or fallback_blue
                    fuente = "Fallback-DB"
                else:
                    fuente = "dolarapi.com"

                print(f"💵 Insertando cotización del dólar para {today}...")
                print(f"   Oficial: ${valor_oficial:.2f} | Blue: ${valor_blue:.2f} | Fuente: {fuente}")

                cur.execute("""
                    INSERT INTO model.dim_dolar (fecha, valor_oficial, valor_blue, fuente)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (fecha) DO UPDATE
                    SET valor_oficial = EXCLUDED.valor_oficial,
                        valor_blue    = EXCLUDED.valor_blue,
                        fuente        = EXCLUDED.fuente;
                """, (today, valor_oficial, valor_blue, fuente))

                conn.commit()
                print("✅ Dimensión Dólar actualizada.")

    except Exception as e:
        print(f"❌ Error en dim_dolar: {e}")


if __name__ == "__main__":
    insert_dim_dolar()
