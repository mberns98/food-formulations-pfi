import psycopg2
from psycopg2 import sql
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR))

from src.config import DB_PARAMS

def create_dynamic_ml_view():
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        cur.execute("SELECT DISTINCT nombre FROM model.dim_ingredientes ORDER BY nombre;")
        ingredientes = [r[0] for r in cur.fetchall()]

        # Use psycopg2.sql to safely compose identifiers and literals.
        case_parts = [
            sql.SQL("MAX(CASE WHEN i.nombre = {} THEN b.proporcion ELSE 0 END) AS {}").format(
                sql.Literal(n),
                sql.Identifier(n)
            )
            for n in ingredientes
        ]

        view_query = sql.SQL("""
        CREATE OR REPLACE VIEW use_cases.v_ml_training_set AS
        SELECT
            f.id_formula,
            f.nombre AS formula_nombre,
            {cases},
            ff.aceptabilidad,
            ff.dureza,
            ff.elasticidad,
            ff.color
        FROM model.dim_formulaciones f
        LEFT JOIN model.bridge_formula_ing b ON f.id_formula = b.id_formula
        LEFT JOIN model.dim_ingredientes i ON b.id_ingrediente = i.id_ingrediente
        INNER JOIN model.fact_form ff ON f.id_formula = ff.id_formula
        WHERE f.source = 'historical'
        GROUP BY f.id_formula, f.nombre, ff.aceptabilidad, ff.dureza, ff.elasticidad, ff.color
        ORDER BY f.id_formula
        """).format(cases=sql.SQL(", ").join(case_parts))

        print("🪄 Generando vista 'use_cases.v_ml_training_set' en la base de datos...")
        cur.execute("DROP VIEW IF EXISTS use_cases.v_ml_training_set CASCADE;")
        cur.execute(view_query)
        conn.commit()
        print("✅ Vista creada exitosamente con todos los ingredientes como columnas.")

    except Exception as e:
        print(f"❌ Error al crear la vista: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    create_dynamic_ml_view()