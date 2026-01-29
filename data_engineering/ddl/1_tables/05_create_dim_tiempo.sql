CREATE TABLE IF NOT EXISTS silver.dim_tiempo (
            id_tiempo SERIAL PRIMARY KEY,
            fecha DATE UNIQUE NOT NULL,
            mes INT,
            anio INT,
            dia_semana TEXT
        );