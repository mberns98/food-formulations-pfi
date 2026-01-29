CREATE TABLE IF NOT EXISTS silver.dim_operarios (
            id_operario SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            legajo TEXT UNIQUE
        );