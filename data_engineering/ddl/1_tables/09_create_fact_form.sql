CREATE TABLE IF NOT EXISTS model.fact_form (
            id_fact SERIAL PRIMARY KEY,
            id_formula INT REFERENCES model.dim_formulaciones(id_formula) ON DELETE CASCADE,
            id_evaluador INT REFERENCES model.dim_evaluadores(id_evaluador),
            id_proceso INT REFERENCES model.dim_procesos(id_proceso),
            id_dolar INT REFERENCES model.dim_dolar(id_dolar),
            id_tiempo INT REFERENCES model.dim_tiempo(id_tiempo),
            aceptabilidad INT CHECK (aceptabilidad BETWEEN 1 AND 4),
            dureza INT CHECK (dureza BETWEEN 1 AND 4),
            elasticidad INT CHECK (elasticidad BETWEEN 1 AND 4),
            color INT CHECK (color BETWEEN 1 AND 4),
            precio_ars NUMERIC(10,2),
            precio_usd NUMERIC(10,2),
            source TEXT NOT NULL DEFAULT 'historical'
                CHECK (source IN ('historical', 'operational_ui'))
        );
