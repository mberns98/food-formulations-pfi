CREATE TABLE IF NOT EXISTS model.bridge_formula_ing (
    id_formula INT REFERENCES model.dim_formulaciones(id_formula) ON DELETE CASCADE,
    id_ingrediente INT REFERENCES model.dim_ingredientes(id_ingrediente),
    proporcion NUMERIC(5,4) CHECK (proporcion >= 0 AND proporcion <= 1),
    source TEXT NOT NULL DEFAULT 'historical' 
        CHECK (source IN ('historical', 'operational_ui')),
    PRIMARY KEY (id_formula, id_ingrediente)
);