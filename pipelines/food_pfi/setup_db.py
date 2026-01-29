import os
import sys
from pathlib import Path

# Add project root to sys.path to allow importing from src
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

import psycopg2
from src.config import DB_PARAMS

def create_tables():
    """
    Initializes the Data Warehouse schema for food formulations.
    Includes dimensions for ingredients, evaluators, processes, and the fact table.
    """
    ddl_statements = [
        # 1. Dimensions
        """
        CREATE TABLE IF NOT EXISTS dim_ingredientes (
            id_ingrediente SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            marca TEXT NOT NULL,
            proveedor TEXT,
            costo_unitario_ars NUMERIC(10,2) NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dim_evaluadores (
            id_evaluador SERIAL PRIMARY KEY,
            nombre TEXT,
            apellido TEXT,
            is_trained BOOLEAN DEFAULT FALSE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dim_formulas (
            id_formula SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            tipo TEXT,
            descripcion TEXT,
            fecha_creacion DATE DEFAULT CURRENT_DATE,
            version TEXT,
            source TEXT NOT NULL DEFAULT 'historical'
            CHECK (source IN ('historical', 'operational_ui'))
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dim_operarios (
            id_operario SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            legajo TEXT UNIQUE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dim_tiempo (
            id_tiempo SERIAL PRIMARY KEY,
            fecha DATE UNIQUE NOT NULL,
            mes INT,
            anio INT,
            dia_semana TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dim_dolar (
            id_dolar SERIAL PRIMARY KEY,
            fecha DATE UNIQUE NOT NULL,
            valor_oficial DECIMAL(10, 2),
            valor_blue DECIMAL(10, 2),
            fuente TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS dim_procesos (
            id_proceso SERIAL PRIMARY KEY,
            id_operario INT REFERENCES dim_operarios(id_operario),
            nombre TEXT NOT NULL,
            descripcion TEXT,
            temperatura NUMERIC,
            tiempo_minutos INT
        );
        """,
        # 2. Bridge Table (Many-to-Many relationship)
        """
        CREATE TABLE IF NOT EXISTS bridge_formula_ing (
            id_formula INT REFERENCES dim_formulas(id_formula) ON DELETE CASCADE,
            id_ingrediente INT REFERENCES dim_ingredientes(id_ingrediente),
            proporcion NUMERIC(5,4) CHECK (proporcion >= 0 AND proporcion <= 1),
            PRIMARY KEY (id_formula, id_ingrediente)
        );
        """,
        # 3. Fact Table
        """
        CREATE TABLE IF NOT EXISTS fact_form (
            id_resultado SERIAL PRIMARY KEY,
            id_formula INT REFERENCES dim_formulas(id_formula),
            id_evaluador INT REFERENCES dim_evaluadores(id_evaluador),
            id_proceso INT REFERENCES dim_procesos(id_proceso),
            id_dolar INT REFERENCES dim_dolar(id_dolar),
            id_tiempo INT REFERENCES dim_tiempo(id_tiempo),
            aceptabilidad INT,
            dureza INT,
            elasticidad INT,
            color INT,
            precio_ars DECIMAL(10, 2),
            precio_usd DECIMAL(10, 2),
            source TEXT NOT NULL DEFAULT 'historical'
        );
        """
    ]

    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()

        # Check environment variable for cleanup
        DROP_TABLES_FIRST = os.getenv("DROP_TABLES_FIRST", "false").lower() == "true"
        if DROP_TABLES_FIRST:
            tables_to_drop = [
                "fact_form", "bridge_formula_ing", "dim_formulas", 
                "dim_procesos", "dim_operarios", "dim_evaluadores", "dim_ingredientes"
            ]
            for table in tables_to_drop:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            print("🧹 Tables successfully deleted (Clean Slate)")

        # Create tables
        for ddl in ddl_statements:
            cursor.execute(ddl)
        
        conn.commit()
        print("✅ Database schema created successfully")

    except Exception as e:
        print(f"❌ Error during database setup: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_tables()