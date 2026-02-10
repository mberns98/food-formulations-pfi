CREATE TABLE IF NOT EXISTS model.dim_operarios (
            id_operario SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            legajo TEXT UNIQUE,
            source TEXT NOT NULL DEFAULT 'historical'
                CHECK (source IN ('historical', 'operational_ui'))
        );