CREATE TABLE IF NOT EXISTS model.dim_dolar (
            id_dolar SERIAL PRIMARY KEY,
            fecha DATE UNIQUE NOT NULL,
            valor_oficial NUMERIC(10,2),
            valor_blue NUMERIC(10,2),
            fuente TEXT,
            source TEXT NOT NULL DEFAULT 'historical'
                CHECK (source IN ('historical', 'operational_ui'))
        );