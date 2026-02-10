import streamlit as st
import psycopg2
import os
from pathlib import Path
import sys
from dotenv import load_dotenv
import pandas as pd

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
                placeholder="Ej: Galleta_Avena_Reforzada",
                help="Evita espacios especiales, usa guiones bajos si es necesario."
            )
            
            version_f = st.number_input(
                "Número de Versión / Intento", 
                min_value=1, 
                value=1,
                help="Si es una corrección de una fórmula existente, aumenta este número."
            )

        with col_b:
            operario_f = st.selectbox(
                "Operario Responsable",
                options=lista_operarios,
                help="Persona encargada de realizar la mezcla en planta/lab."
            )
            
            fecha_f = st.date_input(
                "Fecha de Elaboración",
                help="Fecha en la que se realizó físicamente la muestra."
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
            tipo_proceso = st.selectbox(
                "Operación Unitaria", 
                options=lista_procesos_base,
                help="Selecciona el proceso principal realizado."
            )
        
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
        
        # 1. Creamos un DataFrame vacío o con una fila de ejemplo para el editor
        if 'df_ingredientes' not in st.session_state:
            st.session_state.df_ingredientes = pd.DataFrame(
                [{"ingrediente": "", "proporcion": 0.0, "precio_unitario": 0.0}],
            )

        # 2. Configuramos las columnas del editor
        # 'ingrediente' será un desplegable con los nombres de model.dim_ingredientes
        # 'precio_unitario' solo será necesario si el ingrediente es nuevo
        edited_df = st.data_editor(
            st.session_state.df_ingredientes,
            column_config={
                "ingrediente": st.column_config.SelectboxColumn(
                    "Ingrediente",
                    help="Selecciona un ingrediente existente o escribe uno nuevo",
                    width="large",
                    options=lista_ingredientes, # La lista que trajimos de la DB
                    required=True,
                ),
                "proporcion": st.column_config.NumberColumn(
                    "Proporción (0-1)",
                    help="Cantidad en peso (ej: 0.5 para 50%)",
                    min_value=0.0,
                    max_value=1.0,
                    format="%.4f",
                    required=True,
                ),
                "precio_unitario": st.column_config.NumberColumn(
                    "Precio USD/kg (Solo si es nuevo)",
                    min_value=0.0,
                    format="$ %.2f",
                )
            },
            num_rows="dynamic", # Permite al usuario agregar/quitar filas tipo Excel
            width="stretch",
            key="editor_ingredientes"
        )

        # 3. Validación visual de la suma
        total_proporcion = edited_df["proporcion"].sum()
        if total_proporcion != 1.0:
            st.warning(f"⚠️ La suma de las proporciones es {total_proporcion:.2f}. Debe ser exactamente 1.00")
        else:
            st.success("✅ Mezcla balanceada (100%)")


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
            st.info("Guardando datos en Postgres...")

elif app_mode == "Evaluar nueva formulación":
    st.title("🤖 Predicción de Calidad")
    # ...

elif app_mode == "Evaluar nueva formulación":
    st.title("🤖 Simulador de Predicción (ML)")
    st.markdown("---")
    
    st.write("Selecciona una fórmula existente o crea una teórica para predecir su aceptabilidad.")