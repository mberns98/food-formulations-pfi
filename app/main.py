import streamlit as st
import psycopg2
import os
from pathlib import Path
import sys
from dotenv import load_dotenv
import pandas as pd
from database import save_full_formulation

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
load_dotenv(BASE_DIR / ".env")

# Set coneccion con postgres
@st.cache_resource
def get_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", 5432)
        )
        return conn
    except Exception as e:
        st.error(f"❌ Error conectando a la base de datos: {e}")
        return None
    
conn = get_connection()

if conn:
    st.sidebar.success("✅ Conectado a Postgres")
else:
    st.sidebar.error("❌ Sin conexión")
    
st.set_page_config(
    page_title="Interfaz de carga de datos",
    page_icon="🔬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar con opciones de navegación
st.sidebar.title("🎛️ Navegación")
app_mode = st.sidebar.radio(
    "Selecciona una opción:",
    ["Cargar nueva formulación", "Evaluar nueva formulación"]
)


# esta parte es para si el usuario selecciona la opcion de cargar nueva formulacion.
if app_mode == "Cargar nueva formulación":
    st.header("🧪 Registro de Nueva Formulación")

    # 1. CARGA DE DATOS DE REFERENCIA
    with conn.cursor() as cur:
        # Traemos Ingredientes
        cur.execute("SELECT nombre FROM model.dim_ingredientes ORDER BY nombre;")
        lista_ingredientes = [r[0] for r in cur.fetchall()]
        
        # Traemos Operarios
        cur.execute("SELECT nombre FROM model.dim_operarios ORDER BY nombre;")
        lista_operarios = [r[0] for r in cur.fetchall()]
        
        # Traemos Evaluadores
        cur.execute("SELECT nombre FROM model.dim_evaluadores ORDER BY nombre;")
        lista_evaluadores = [r[0] for r in cur.fetchall()]

        # Traemos Procesos
        cur.execute("SELECT nombre FROM model.dim_procesos GROUP BY nombre ORDER BY nombre;")
        lista_procesos_base = [r[0] for r in cur.fetchall()]

    # 2. DEFINICIÓN DE TABS
    tab1, tab2, tab3 = st.tabs(["📋 Cabecera", "⚖️ Formulación", "🧪 Evaluación"])

    with tab1:
        st.subheader("📋 Información General del Lote")
        
        # Usamos columnas para que no ocupe tanto espacio vertical
        col_a, col_b = st.columns(2)
        
        with col_a:
            nombre_f = st.text_input(
                "Nombre de la Fórmula", 
                placeholder="Ej: salchicha_baja_en_almidon",
                help="Evita espacios, usa guiones bajos si es necesario."
            )
            
            # Tipo de Producto (Para dim_formulaciones.tipo)
            tipo_f = st.selectbox(
                "Tipo de Producto", 
                options=["Embutido Cocido", "Embutido Fresco", "Madurado", "Untable", "Otro"],
                help="Categoría técnica del producto."
            )
            
            version_f = st.number_input(
                "Número de Versión / Intento", 
                min_value=1, 
                value=1,
                help="Si es una corrección de una fórmula existente, aumenta este número."
            )

        with col_b:
            opciones_op = lista_operarios + ["➕ Agregar nuevo operario..."]
            operario_sel = st.selectbox("Operario Responsable", options=opciones_op)
            
            operario_f = operario_sel
            if operario_sel == "➕ Agregar nuevo operario...":
                operario_f = st.text_input("Nombre del nuevo operario")
            
            fecha_f = st.date_input(
                "Fecha de Elaboración",
                help="Fecha en la que se realizó físicamente la muestra."
            )

            # Descripción (Para dim_formulaciones.descripcion)
            desc_f = st.text_input(
                "Descripción breve", 
                placeholder="Ej: Prueba con reducción de sodio y reemplazo de grasa animal por vegetal."
            )
        notas_f = st.text_area(
            "Notas del Proceso", 
            placeholder="Ej: Se observó una viscosidad mayor a la esperada durante el mezclado..."
        )

        if nombre_f:
            st.caption(f"🆔 ID sugerido: **{nombre_f.lower().replace(' ', '_')}_v{version_f}**")

        st.markdown("---") # Separador visual
        st.subheader("⚙️ Parámetros Críticos de Proceso")
        
        # Traemos los tipos de procesos base de la DB (Mezclado, Horneado, etc.)
        with conn.cursor() as cur:
            cur.execute("SELECT nombre FROM model.dim_procesos GROUP BY nombre ORDER BY nombre;")
            lista_procesos_base = [r[0] for r in cur.fetchall()]

        col_p1, col_p2, col_p3 = st.columns(3)

        with col_p1:
            opciones_proc = lista_procesos_base + ["➕ Agregar nuevo proceso..."]
            proceso_sel = st.selectbox("Operación Unitaria", options=opciones_proc)

            tipo_proceso = proceso_sel
            if proceso_sel == "➕ Agregar nuevo proceso...":
                tipo_proceso = st.text_input("Nombre del nuevo proceso (ej: Extrusión)")
        
        with col_p2:
            temp_proceso = st.number_input(
                "Temperatura (°C)", 
                value=25.0, 
                step=0.5,
                help="Temperatura controlada durante la operación."
            )

        with col_p3:
            tiempo_proceso = st.number_input(
                "Tiempo (min)", 
                min_value=0, 
                value=10,
                help="Duración de la etapa de proceso."
            )

    with tab2:
        st.subheader("⚖️ Composición de la Mezcla")
        
        if 'ingredientes_nuevos' not in st.session_state:
            st.session_state.ingredientes_nuevos = []
        opciones_disponibles = sorted(list(set(lista_ingredientes + st.session_state.ingredientes_nuevos)))
        
        # --- 1. INICIALIZACIÓN CON TIPADO EXPLÍCITO---
        # Forzamos los dtypes para que PyArrow no falle al convertir
        if 'df_ingredientes' not in st.session_state:
            st.session_state.df_ingredientes = pd.DataFrame({
                "ingrediente": pd.Series([], dtype='str'),
                "proporcion": pd.Series([], dtype='float'),
                "marca": pd.Series([], dtype='str'),
                "proveedor": pd.Series([], dtype='str'),
                "precio": pd.Series([], dtype='float')
            })

        # --- 2. EL EDITOR ---
        edited_df = st.data_editor(
            st.session_state.df_ingredientes,
            column_config={
                "ingrediente": st.column_config.SelectboxColumn(
                    "Ingrediente", 
                    options=opciones_disponibles, 
                    required=True, 
                    width="large"
                ),
                "proporcion": st.column_config.NumberColumn(
                    "Proporción", 
                    min_value=0.0, max_value=1.0, format="%.4f"
                ),
                # Ocultamos las columnas técnicas de la vista del operario
                "marca": None, 
                "proveedor": None, 
                "precio": None
            },
            column_order=["ingrediente", "proporcion"],
            num_rows="dynamic",
            width="stretch",
            key="editor"
        )

        st.markdown("---")
        st.write("### ✨ Registro de Ingrediente Nuevo")
        
        # --- 3. FORMULARIO DE INYECCIÓN CORREGIDO ---
        with st.expander("➕ Cargar nuevo ítem al catálogo", expanded=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                n_nombre = st.text_input("Nombre", placeholder="Ej: Harina de Arveja")
            with c2:
                n_marca = st.text_input("Marca", value="GENERICA")
            with c3:
                n_prov = st.text_input("Proveedor", value="S/D")
            
            c4, c5 = st.columns([1, 2])
            with c4:
                n_precio = st.number_input("Costo ARS/kg", min_value=0.0)
            with c5:
                st.write(" ")
                st.write(" ")
                if st.button("🚀 Habilitar e Inyectar en Tabla", use_container_width=True):
                    if n_nombre:
                        # Creamos la fila asegurando los tipos de datos exactos
                        nueva_fila = pd.DataFrame([{
                            "ingrediente": str(n_nombre),
                            "proporcion": 0.0,
                            "marca": str(n_marca),
                            "proveedor": str(n_prov),
                            "precio": float(n_precio)
                        }])
                        
                        # Concatenamos y forzamos el tipo de vuelta por seguridad
                        updated_df = pd.concat([edited_df, nueva_fila], ignore_index=True)
                        st.session_state.df_ingredientes = updated_df.astype({
                            "ingrediente": 'str',
                            "marca": 'str',
                            "proveedor": 'str'
                        })
                        
                        if n_nombre not in st.session_state.ingredientes_nuevos:
                            st.session_state.ingredientes_nuevos.append(n_nombre)
                        
                        st.success(f"¡{n_nombre} listo!")
                        st.rerun()

        # --- 4. VALIDACIÓN DE SUMA ---
        proporciones_numeric = pd.to_numeric(edited_df["proporcion"], errors='coerce').fillna(0)
        total_proporcion = proporciones_numeric.sum()

        if abs(total_proporcion - 1.0) > 0.0001:
            st.warning(f"⚠️ Suma: {total_proporcion:.4f}. Debe ser 1.0000")
        else:
            st.success("✅ Mezcla balanceada")

    with tab3:
        st.subheader("🧪 Evaluación Sensorial y de Laboratorio")

        # --- SECCIÓN 1: EVALUADOR ---
        with st.expander("👤 Información del Evaluador", expanded=True):
            col_ev1, col_ev2 = st.columns(2)

            opciones_evaluadores = lista_evaluadores + ["➕ Agregar nuevo evaluador..."]
            evaluador_seleccionado = st.selectbox("Seleccione el Evaluador", options=opciones_evaluadores)
            
            with col_ev1:

                # Si elige agregar nuevo, mostramos el campo de texto
                nuevo_evaluador = None
                if evaluador_seleccionado == "➕ Agregar nuevo evaluador...":
                    nuevo_evaluador = st.text_input("Nombre del nuevo evaluador")
            
            with col_ev2:
                tipo_test = st.radio("Tipo de Panel", ["Entrenado", "Consumidor", "Línea"], horizontal=True)

        st.markdown("---")

        # --- SECCIÓN 2: EVALUACIONES
        st.subheader("📊 Atributos Evaluados")
        st.caption("Escala: 1 (Bajo/Malo) - 4 (Alto/Excelente)")

        # Usamos columnas para que los selectores queden alineados y ocupen menos espacio
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            aceptabilidad = st.selectbox("Aceptabilidad", options=[1, 2, 3, 4], index=2, help="1: Disgusto, 4: Me gusta mucho")
        with c2:
            color_eval = st.selectbox("Color", options=[1, 2, 3, 4], index=2, help="Evaluación visual según patrón")
        with c3:
            dureza_eval = st.selectbox("Dureza", options=[1, 2, 3, 4], index=2, help="Resistencia al primer mordisco")
        with c4:
            elasticidad_eval = st.selectbox("Elasticidad", options=[1, 2, 3, 4], index=2, help="Capacidad de recuperar forma")

        # Espacio para observaciones finales
        comentarios_lab = st.text_area("Observaciones técnicas de laboratorio", placeholder="Ej: La muestra presentó sinéresis a los 10 min...")

        # Botón de Guardado Final
        st.markdown("###")
        if st.button("🚀 FINALIZAR Y GUARDAR FORMULACIÓN", use_container_width=True, type="primary"):
            
            # --- AQUÍ VA EL BLOQUE DE LIMPIEZA ---
            # 1. Limpieza de datos (Para evitar el TypeError: unhashable type: 'list')
            df_clean = edited_df[edited_df["ingrediente"].notna()].copy()
            
            # Si Streamlit devolvió una lista, extraemos el string
            df_clean["ingrediente"] = df_clean["ingrediente"].apply(
                lambda x: x[0] if isinstance(x, list) and len(x) > 0 else str(x)
            )

            # 2. Ahora creamos el diccionario usando el df_clean
            composicion_dict = dict(zip(df_clean["ingrediente"], df_clean["proporcion"]))
            
            # 3. Preparar la lista de ingredientes (Usando también df_clean)
            lista_ingredientes_save = []
            for _, row in df_clean.iterrows():
                lista_ingredientes_save.append({
                    "nombre": row["ingrediente"],
                    "marca": row["marca"] if pd.notna(row["marca"]) and row["marca"] != "" else "GENERICA",
                    "proveedor": row["proveedor"] if pd.notna(row["proveedor"]) and row["proveedor"] != "" else "S/D",
                    "precio": float(row["precio"]) if pd.notna(row["precio"]) else 0.0
                })

            # 3. Consolidar todo el paquete de datos
            payload = {
                "nombre_f": nombre_f,
                "tipo": tipo_f,  
                "descripcion": desc_f,
                "version": version_f,
                "operario": operario_f,
                "es_nuevo_operario": (operario_sel == "➕ Agregar nuevo operario..."),
                "ingredientes": lista_ingredientes_save,
                "composicion_json": composicion_dict,
                "proceso": tipo_proceso,
                "temp": temp_proceso,
                "tiempo": tiempo_proceso,
                "evaluador": evaluador_f if evaluador_seleccionado != "➕ Agregar nuevo evaluador..." else nuevo_evaluador,
                "es_nuevo_evaluador": (evaluador_seleccionado == "➕ Agregar nuevo evaluador..."),
                "acep": aceptabilidad,
                "col": color_eval,
                "dur": dureza_eval,
                "ela": elasticidad_eval
            }

            # 4. Validaciones finales antes de disparar a SQL
            if not nombre_f or not operario_f:
                st.error("❌ Falta el nombre de la fórmula o el operario.")
            elif total_proporcion != 1.0:
                st.error("❌ La suma de proporciones debe ser 1.0")
            else:
                # 5. EJECUCIÓN DEL MEGA-MERGE
                with st.spinner("Guardando en base de datos..."):
                    success, msg = save_full_formulation(conn, payload)
                    if success:
                        st.success(msg)
                        st.balloons() # ¡Festejo de ingeniero!
                        # Opcional: st.rerun() para limpiar el formulario
                    else:
                        st.error(msg)

elif app_mode == "Evaluar nueva formulación":
    st.title("🤖 Predicción de Calidad")
    # ...

elif app_mode == "Evaluar nueva formulación":
    st.title("🤖 Simulador de Predicción (ML)")
    st.markdown("---")
    
    st.write("Selecciona una fórmula existente o crea una teórica para predecir su aceptabilidad.")