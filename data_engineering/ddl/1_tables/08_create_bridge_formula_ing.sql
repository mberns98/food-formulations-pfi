CREATE TABLE IF NOT EXISTS silver.bridge_formula_ing (
            id_formula INT REFERENCES dim_formulas(id_formula) ON DELETE CASCADE,
            id_ingrediente INT REFERENCES dim_ingredientes(id_ingrediente),
            proporcion NUMERIC(5,4) CHECK (proporcion >= 0 AND proporcion <= 1),
            PRIMARY KEY (id_formula, id_ingrediente)
        );