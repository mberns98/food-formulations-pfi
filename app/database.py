import psycopg2
import json
from datetime import date

def refresh_ml_training_view(cur):
    """
    Función auxiliar para regenerar la vista de ML cada vez que 
    se inserta un ingrediente nuevo o una nueva fórmula.
    """
    # 1. Obtener todos los ingredientes actuales para las columnas
    cur.execute("SELECT DISTINCT nombre FROM model.dim_ingredientes ORDER BY nombre;")
    ingredientes = [r[0] for r in cur.fetchall()]

    ingredientes_case = [
        f"MAX(CASE WHEN i.nombre = '{n}' THEN b.proporcion ELSE 0 END) AS \"{n}\""
        for n in ingredientes
    ]

    # 2. Re-crear la vista dinámica
    view_query = f"""
    CREATE OR REPLACE VIEW use_cases.v_ml_training_set AS
    SELECT 
        f.id_formula,
        f.nombre AS formula_nombre,
        {", ".join(ingredientes_case)},
        ff.aceptabilidad,
        ff.dureza,
        ff.elasticidad,
        ff.color
    FROM model.dim_formulaciones f
    LEFT JOIN model.bridge_formula_ing b ON f.id_formula = b.id_formula
    LEFT JOIN model.dim_ingredientes i ON b.id_ingrediente = i.id_ingrediente
    INNER JOIN model.fact_form ff ON f.id_formula = ff.id_formula
    GROUP BY f.id_formula, f.nombre, ff.aceptabilidad, ff.dureza, ff.elasticidad, ff.color
    ORDER BY f.id_formula;
    """
    cur.execute("DROP VIEW IF EXISTS use_cases.v_ml_training_set CASCADE;")
    cur.execute(view_query)

def save_full_formulation(conn, data):
    try:
        with conn.cursor() as cur:
            # --- 1. dim_tiempo ---
            today = date.today()
            cur.execute("""
                INSERT INTO model.dim_tiempo (fecha, mes, anio, dia_semana, source)
                VALUES (%s, %s, %s, %s, 'operational_ui')
                ON CONFLICT (fecha) DO UPDATE SET fecha = EXCLUDED.fecha
                RETURNING id_tiempo;
            """, (today, today.month, today.year, today.strftime('%A')))
            id_tiempo = cur.fetchone()[0]

            # --- 2. dim_dolar ---
            cur.execute("""
                INSERT INTO model.dim_dolar (fecha, valor_oficial, source)
                VALUES (%s, %s, 'operational_ui')
                ON CONFLICT (fecha) DO UPDATE SET fecha = EXCLUDED.fecha
                RETURNING id_dolar;
            """, (today, 1000.0)) 
            id_dolar = cur.fetchone()[0]

            # --- 3. dim_operarios ---
            id_operario = None
            if data['es_nuevo_operario']:
                partes = data['operario'].split(' ', 1)
                nombre = partes[0]
                apellido = partes[1] if len(partes) > 1 else "S/D"
                cur.execute("""
                    INSERT INTO model.dim_operarios (nombre, apellido, legajo, source) 
                    VALUES (%s, %s, %s, 'operational_ui') 
                    ON CONFLICT (legajo) DO NOTHING RETURNING id_operario;
                """, (nombre, apellido, f"OP_{nombre[:3].upper()}_{today.strftime('%y%m%d')}"))
                res = cur.fetchone()
                id_operario = res[0] if res else None
            
            if not id_operario:
                cur.execute("SELECT id_operario FROM model.dim_operarios WHERE nombre LIKE %s LIMIT 1;", (data['operario'].split(' ')[0] + '%',))
                id_operario = cur.fetchone()[0]

            # --- 4. dim_ingredientes ---
            cur.execute("SELECT valor_oficial FROM model.dim_dolar WHERE id_dolar = %s", (id_dolar,))
            valor_dolar_hoy = cur.fetchone()[0]

            for ing in data['ingredientes']:
                cur.execute("""
                    INSERT INTO model.dim_ingredientes (
                        nombre, marca, proveedor, costo_unitario_ars, costo_unitario_usd, source
                    ) 
                    VALUES (%s, %s, %s, %s, %s / NULLIF(%s, 0), 'operational_ui') 
                    ON CONFLICT (nombre) 
                    DO UPDATE SET 
                        costo_unitario_ars = CASE WHEN EXCLUDED.costo_unitario_ars > 0 THEN EXCLUDED.costo_unitario_ars ELSE model.dim_ingredientes.costo_unitario_ars END,
                        costo_unitario_usd = CASE WHEN EXCLUDED.costo_unitario_ars > 0 THEN EXCLUDED.costo_unitario_ars / NULLIF(%s, 0) ELSE model.dim_ingredientes.costo_unitario_usd END,
                        marca = CASE WHEN EXCLUDED.marca <> 'GENERICA' THEN EXCLUDED.marca ELSE model.dim_ingredientes.marca END;
                """, (ing['nombre'], ing['marca'], ing['proveedor'], ing['precio'], ing['precio'], valor_dolar_hoy, valor_dolar_hoy))
            
            # --- 5. dim_formulaciones ---
            cur.execute("""
                INSERT INTO model.dim_formulaciones (nombre, tipo, descripcion, version, composicion, source, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, 'operational_ui', %s)
                RETURNING id_formula;
            """, (data['nombre_f'], data.get('tipo', 'Mezcla'), data.get('descripcion', ''), str(data['version']), json.dumps(data['composicion_json']), today))
            id_formula = cur.fetchone()[0]

            # --- 6. BRIDGE ---
            for ing_nombre, prop in data['composicion_json'].items():
                cur.execute("""
                    INSERT INTO model.bridge_formula_ing (id_formula, id_ingrediente, proporcion, source)
                    VALUES (%s, (SELECT id_ingrediente FROM model.dim_ingredientes WHERE nombre = %s LIMIT 1), %s, 'operational_ui');
                """, (id_formula, ing_nombre, prop))

            # --- 7. dim_procesos ---
            cur.execute("""
                INSERT INTO model.dim_procesos (id_operario, nombre, temperatura, tiempo_minutos, source)
                VALUES (%s, %s, %s, %s, 'operational_ui')
                RETURNING id_proceso;
            """, (id_operario, data['proceso'], data['temp'], data['tiempo']))
            id_proceso = cur.fetchone()[0]

            # --- 7.5 Asegurar Evaluador ---
            evaluador_input = data.get('evaluador', 'S/D')
            partes_eval = evaluador_input.split(' ', 1)
            nombre_eval, apellido_eval = partes_eval[0], (partes_eval[1] if len(partes_eval) > 1 else "S/D")

            cur.execute("""
                INSERT INTO model.dim_evaluadores (nombre, apellido, source)
                VALUES (%s, %s, 'operational_ui')
                ON CONFLICT (nombre) DO UPDATE SET apellido = EXCLUDED.apellido 
                RETURNING id_evaluador;
            """, (nombre_eval, apellido_eval))
            id_evaluador = cur.fetchone()[0]

            # --- 8. FACT FORM ---
            cur.execute("""
                INSERT INTO model.fact_form (
                    id_formula, id_evaluador, id_proceso, id_dolar, id_tiempo,
                    aceptabilidad, dureza, elasticidad, color, precio_ars, precio_usd, source
                ) 
                SELECT 
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    SUM(b.proporcion * i.costo_unitario_ars), 
                    SUM(b.proporcion * i.costo_unitario_ars) / NULLIF(%s, 0),
                    'operational_ui'
                FROM model.bridge_formula_ing b
                JOIN model.dim_ingredientes i ON b.id_ingrediente = i.id_ingrediente
                WHERE b.id_formula = %s
                GROUP BY b.id_formula;
            """, (id_formula, id_evaluador, id_proceso, id_dolar, id_tiempo,
                  data['acep'], data['dur'], data['ela'], data['col'],
                  valor_dolar_hoy, id_formula))

            # --- 9. ACTUALIZACIÓN DINÁMICA DE LA VISTA DE ML ---
            # Esto asegura que la vista siempre tenga todos los ingredientes como columnas
            refresh_ml_training_view(cur)

            conn.commit()
            return True, "✅ Formulación guardada, costos calculados y vista de ML actualizada."
            
    except Exception as e:
        if conn: conn.rollback()
        return False, f"❌ Error SQL: {str(e)}"