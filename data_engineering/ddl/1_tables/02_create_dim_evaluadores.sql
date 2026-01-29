CREATE TABLE IF NOT EXISTS silver.dim_evaluadores (
            id_evaluador SERIAL PRIMARY KEY,
            nombre TEXT,
            apellido TEXT,
            is_trained BOOLEAN DEFAULT FALSE
        );