CREATE TABLE IF NOT EXISTS silver.fact_form (
            id_resultado SERIAL PRIMARY KEY,
            id_formula INT REFERENCES dim_formulas(id_formula),
            id_evaluador INT REFERENCES dim_evaluadores(id_evaluador),
            id_proceso INT REFERENCES dim_procesos(id_proceso),
            id_dolar INT REFERENCES dim_dolar(id_dolar),
            id_tiempo INT REFERENCES dim_tiempo(id_tiempo),
            aceptabilidad INT,
            dureza INT,
            elasticidad INT,
            color INT,
            precio_ars DECIMAL(10, 2),
            precio_usd DECIMAL(10, 2),
            source TEXT NOT NULL DEFAULT 'historical'
        );