CREATE TABLE IF NOT EXISTS silver.dim_formulas (
            id_formula SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            tipo TEXT,
            descripcion TEXT,
            fecha_creacion DATE DEFAULT CURRENT_DATE,
            version TEXT,
            source TEXT NOT NULL DEFAULT 'historical'
            CHECK (source IN ('historical', 'operational_ui'))
        );