CREATE TABLE IF NOT EXISTS model.dim_tiempo (
            id_tiempo SERIAL PRIMARY KEY,
            fecha DATE UNIQUE NOT NULL,
            mes INT,
            anio INT,
            dia_semana TEXT,
            source TEXT NOT NULL DEFAULT 'historical'
                CHECK (source IN ('historical', 'operational_ui'))
        );