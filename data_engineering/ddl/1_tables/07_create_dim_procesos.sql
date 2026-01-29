CREATE TABLE IF NOT EXISTS silver.dim_procesos (
            id_proceso SERIAL PRIMARY KEY,
            id_operario INT REFERENCES dim_operarios(id_operario),
            nombre TEXT NOT NULL,
            descripcion TEXT,
            temperatura NUMERIC,
            tiempo_minutos INT
        );