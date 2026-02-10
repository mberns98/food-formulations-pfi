CREATE TABLE IF NOT EXISTS model.dim_ingredientes (
            id_ingrediente SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            marca TEXT NOT NULL,
            proveedor TEXT,
            costo_unitario_ars NUMERIC(10,2) NOT NULL,
            source TEXT NOT NULL DEFAULT 'historical'
                CHECK (source IN ('historical', 'operational_ui'))
        );