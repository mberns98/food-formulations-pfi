CREATE TABLE IF NOT EXISTS silver.dim_ingredientes (
    id_ingrediente SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    categoria TEXT,
    costo_unidad DECIMAL(10, 2)
);