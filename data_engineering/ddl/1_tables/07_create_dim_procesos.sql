CREATE TABLE IF NOT EXISTS model.dim_procesos (
            id_proceso SERIAL PRIMARY KEY,
            id_operario INT REFERENCES model.dim_operarios(id_operario),
            nombre TEXT NOT NULL,
            descripcion TEXT,
            temperatura NUMERIC,
            tiempo_minutos INT,
            source TEXT NOT NULL DEFAULT 'historical'
                CHECK (source IN ('historical', 'operational_ui'))
        );