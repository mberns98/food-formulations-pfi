CREATE TABLE IF NOT EXISTS silver.dim_dolar (
            id_dolar SERIAL PRIMARY KEY,
            fecha DATE UNIQUE NOT NULL,
            valor_oficial DECIMAL(10, 2),
            valor_blue DECIMAL(10, 2),
            fuente TEXT
        );