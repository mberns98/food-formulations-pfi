CREATE TABLE IF NOT EXISTS model.dim_evaluadores (
            id_evaluador SERIAL PRIMARY KEY,
            nombre TEXT,
            apellido TEXT,
            is_trained BOOLEAN DEFAULT FALSE,
            source TEXT NOT NULL DEFAULT 'historical'
                CHECK (source IN ('historical', 'operational_ui'))
        );