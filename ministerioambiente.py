import io
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pymysql  # <--- Cambiado de sqlite3 a pymysql para MySQL
import seaborn as sns
import streamlit as st
import sqlalchemy
# ==============================================================================
# CONFIGURACIÓN DE LA PÁGINA Y TEMA VISUAL
# ==============================================================================
st.set_page_config(
    page_title="Dashboard APH - MAATE",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Estilo CSS personalizado para mejorar fuentes y espaciados
st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stMetric { background-color: rgba(28, 131, 225, 0.1); padding: 15px; border-radius: 10px; border: 1px solid rgba(28, 131, 225, 0.2); }
    </style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# MENÚ LATERAL DE NAVEGACIÓN (Control de secciones)
# ==============================================================================
st.sidebar.image(
    "https://img.icons8.com/clouds/100/000000/water-落下.png", width=80
)
st.sidebar.title("Panel de Control")
st.sidebar.markdown("---")

seccion = st.sidebar.radio(
    "Selecciona una sección:",
    [
        "🏠 Inicio y Carga de Datos",
        "🔍 Exploración de Datos (EDA)",
        "🧹 Limpieza de Datos",
        "🔄 Transformación",
        "📊 Visualización Estadística",
        "📥 Exportación Final",
    ],
)

# OBSERVACIÓN: Se ha removido la etiqueta del "Proyecto Integrador" para asegurar formato individual.

# ==============================================================================
# FLUJO PRINCIPAL DE DATOS (Conexión y Carga con MySQL)
# ==============================================================================
# ⚠️ AJUSTA ESTAS CREDENCIALES SEGÚN TU SERVIDOR LOCAL (XAMPP / WAMPSERVER)
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "Perlita8*"  
DB_NAME = "maate_db"  # Recuerda crear esta base de datos antes en phpMyAdmin
RUTA_DATASET = "maate_aph_2023diciembre.csv"


def inicializar_mysql_maate():
    if os.path.exists(RUTA_DATASET):
        # 1. Lectura del archivo plano
        df_csv = pd.read_csv(RUTA_DATASET, sep=";", encoding="latin1")

        # 2. Volcado hacia la base de datos MySQL
        try:
            # Conexión directa para crear la tabla usando la estructura de datos
            from sqlalchemy import create_engine

            # Creamos un motor SQLAlchemy temporal para facilitar el volcado con to_sql
            engine = create_engine(
                f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
            )
            df_csv.to_sql(
                "areas_hidricas", con=engine, if_exists="replace", index=False
            )
            return True
        except Exception as e:
            st.error(
                f"🚨 Error de conexión a MySQL: {e}. Verifica que tu servidor local (XAMPP) esté encendido y que exista la base de datos '{DB_NAME}'."
            )
            st.stop()
    return False


# Garantizar que la base de datos se inicialice antes de renderizar las vistas
db_lista = inicializar_mysql_maate()

if db_lista:
    # 3. Consulta de los datos cargados desde MySQL
    conn = pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    df_original = pd.read_sql_query("SELECT * FROM areas_hidricas", conn)
    conn.close()

    # Mapeo inicial de columnas de trabajo
    columnas_trabajo = [
        "REG_NAT",
        "DPA_DESPRO",
        "DPA_DESCAN",
        "NAM",
        "ANIO_CREACION",
        "EDEL",
        "AREA_HA",
    ]
    df = df_original[columnas_trabajo].copy()
    df = df.rename(
        columns={
            "REG_NAT": "region",
            "DPA_DESPRO": "provincia",
            "DPA_DESCAN": "canton",
            "NAM": "nombre_area",
            "ANIO_CREACION": "anio_creacion",
            "EDEL": "estado_tramite",
            "AREA_HA": "hectareas",
        }
    )

    # REPARACIÓN CRÍTICA: Convertimos hectáreas a número real desde el inicio
    df["hectareas"] = (
        df["hectareas"]
        .astype(str)
        .str.replace(",", ".")
    )
    df["hectareas"] = pd.to_numeric(df["hectareas"], errors="coerce")
    # Rellenamos nulos iniciales con la mediana real ya numérica
    df["hectareas"] = df["hectareas"].fillna(df["hectareas"].median())

else:
    st.error(
        f"🚨 Archivo crítico '{RUTA_DATASET}' no encontrado. Por favor verifique su repositorio."
    )
    st.stop()


# ==============================================================================
# VISTA: 1. INICIO Y CARGA DE DATOS
# ==============================================================================
if seccion == "🏠 Inicio y Carga de Datos":
    st.title("💧 Áreas de Protección Hídrica en Ecuador")
    st.caption("Ministerio del Ambiente, Agua y Transición Ecológica (MAATE)")
    st.markdown("---")

    st.subheader("1. Proceso de Carga y Persistencia")

    with st.container(border=True):
        st.success(
            f"💾 **Conexión Exitosa:** Los datos abiertos se han volcado correctamente en el servidor relacional MySQL (Base de datos: `{DB_NAME}`)."
        )

        # Indicadores en Tarjetas Modernas
        m1, m2 = st.columns(2)
        with m1:
            st.metric(
                label="Total de Registros Escaneados",
                value=f"{df_original.shape[0]} filas",
            )
        with m2:
            st.metric(
                label="Total de Columnas Indexadas",
                value=f"{df_original.shape[1]} variables",
            )

    st.markdown("### 📋 Vista Previa del Contenido de la Base de Datos")
    st.dataframe(df_original.head(10), use_container_width=True)


# ==============================================================================
# VISTA: 2. EXPLORACIÓN DE DATOS (EDA)
# ==============================================================================
elif seccion == "🔍 Exploración de Datos (EDA)":
    st.title("🔍 Análisis Exploratorio Automatizado")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(
        ["📋 Inspección de Filas", "📊 Propiedades e Info", "❓ Diagnóstico de Nulos"]
    )

    with tab1:
        st.markdown("### Muestra Seleccionada para Análisis")
        st.dataframe(df.head(15), use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Estructura de Variables (`df.dtypes`):**")
            st.dataframe(
                df.dtypes.astype(str).to_frame(name="Tipo de Dato"),
                use_container_width=True,
            )
        with c2:
            st.markdown("**Resumen Estadístico Rápido:**")
            st.dataframe(df.describe(include="all"), use_container_width=True)

    with tab3:
        st.markdown("### Detección de Vacíos en la Base de Datos")
        nulos_df = df.isnull().sum().to_frame(name="Valores Nulos")
        nulos_df["% de Pérdida"] = (nulos_df["Valores Nulos"] / len(df)) * 100
        st.dataframe(nulos_df.style.background_gradient(cmap="Reds"))


# ==============================================================================
# VISTA: 3. LIMPIEZA DE DATOS
# ==============================================================================
elif seccion == "🧹 Limpieza de Datos":
    st.title("🧹 Módulo de Sanitización y Calidad de Datos")
    st.markdown("---")

    df_limpio = df.copy()

    columnas_texto = [
        "region",
        "provincia",
        "canton",
        "nombre_area",
        "estado_tramite",
    ]
    for c in columnas_texto:
        df_limpio[c] = (
            df_limpio[c].astype(str).str.strip().replace({"nan": np.nan})
        )

    df_limpio["estado_tramite"] = df_limpio["estado_tramite"].fillna(
        "No Especificado"
    )

    filas_antes = df_limpio.shape[0]
    df_limpio = df_limpio.drop_duplicates()
    filas_despues = df_limpio.shape[0]

    with st.container(border=True):
        st.markdown("### 🛠️ Técnicas de Limpieza Aplicadas con Éxito")
        st.info(
            """
        1. **Casteo de Datos:** Corrección del formato decimal string (`2,065`) a numérico flotante (`float`).
        2. **Normalización:** Eliminación de espacios fantasmas usando `.str.strip()`.
        3. **Imputación Eficiente:** Relleno de estados nulos con la etiqueta de control *'No Especificado'*.
        4. **Deduplicación:** Purga completa de registros redundantes mediante ID de fila.
        """
        )
        st.metric(
            label="Filas duplicadas eliminadas", value=filas_antes - filas_despues
        )

    st.markdown("### ❇️ Dataset Depurado")
    st.dataframe(df_limpio, use_container_width=True)


# ==============================================================================
# VISTA: 4. TRANSFORMACIÓN
# ==============================================================================
elif seccion == "🔄 Transformación":
    st.title("🔄 Ingeniería de Variables y Transformación")
    st.markdown("---")

    df_transformado = df.copy()

    # T1: Feature Engineering
    def clasificar_tamano(ha):
        if ha <= 10.0:
            return "Pequeña (<= 10 ha)"
        elif ha <= 100.0:
            return "Mediana (10-100 ha)"
        return "Grande (> 100 ha)"

    df_transformado["categoria_tamano"] = df_transformado["hectareas"].apply(
        clasificar_tamano
    )

    # T2: Filtro Dinámico Estilizado
    st.markdown("### 🗺️ Segmentación por Ubicación")
    provincias_list = sorted(
        df_transformado["provincia"].dropna().unique().tolist()
    )
    provincia_sel = st.selectbox(
        "Filtrar el ecosistema por Provincia:", ["Todas"] + provincias_list
    )

    df_filtrado = (
        df_transformado
        if provincia_sel == "Todas"
        else df_transformado[df_transformado["provincia"] == provincia_sel]
    )
    st.dataframe(df_filtrado, use_container_width=True)

    # T3: Agrupación Estratégica
    st.markdown("### 📊 Métricas Agregadas por Región Natural")
    df_agrupado = (
        df_transformado.groupby("region")["hectareas"]
        .agg(["count", "mean", "sum"])
        .reset_index()
    )
    df_agrupado.columns = [
        "Región Natural",
        "Número de Áreas",
        "Promedio de Hectáreas",
        "Total Hectáreas Protegidas",
    ]
    st.dataframe(
        df_agrupado.style.background_gradient(
            cmap="Blues", subset=["Total Hectáreas Protegidas"]
        ),
        use_container_width=True,
    )


# ==============================================================================
# VISTA: 5. VISUALIZACIÓN ESTADÍSTICA
# ==============================================================================
elif seccion == "📊 Visualización Estadística":
    st.title("📊 Centro de Gráficos e Inteligencia Ambiental")
    st.markdown("---")

    # Configuración global estética de Matplotlib
    plt.style.use("seaborn-v0_8-whitegrid")
    sns.set_palette("muted")

    g1, g2 = st.columns(2)
    g3, g4 = st.columns(2)

    with g1:
        st.markdown("#### 🏢 Áreas por Región Natural (Gráfico Nativo)")
        st.bar_chart(df["region"].value_counts(), color="#1f77b4")

    with g2:
        st.markdown("#### 📈 Densidad y Distribución del Territorio")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.histplot(df["hectareas"], bins=12, kde=True, color="#4b0082", ax=ax)
        ax.set_title("Distribución de Hectáreas")
        sns.despine()
        st.pyplot(fig)

    with g3:
        st.markdown("#### ⏳ Evolución Cronológica de Reservas")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.scatterplot(
            data=df, x="anio_creacion", y="hectareas", color="#20b2aa", ax=ax
        )
        ax.set_title("Año de Fundación vs Tamaño (HA)")
        sns.despine()
        st.pyplot(fig)

    with g4:
        st.markdown("#### ⚖️ Estado Jurídico de Trámites")
        fig, ax = plt.subplots(figsize=(4, 4))
        data_pie = df["estado_tramite"].value_counts()
        ax.pie(
            data_pie,
            labels=data_pie.index,
            autopct="%1.1f%%",
            startangle=90,
            colors=sns.color_palette("pastel"),
        )
        st.pyplot(fig)


# ==============================================================================
# VISTA: 6. EXPORTACIÓN FINAL
# ==============================================================================
elif seccion == "📥 Exportación Final":
    st.title("📥 Compilación y Descarga del Dataset Depurado")
    st.markdown("---")

    df.to_csv("datos_maate_limpios.csv", index=False)

    with st.container(border=True):
        st.markdown("### 💾 Estado del Almacenamiento Remoto")
        st.success(
            "💾 **Acción en el Servidor:** El archivo comprimido estructurado `datos_maate_limpios.csv` se generó automáticamente en la raíz local del servidor."
        )

    st.markdown("### 📥 Descarga para el Usuario Terminal")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Ecosistemas MAATE", index=False)

    st.download_button(
        label="📥 Descargar Base de Datos Optimizada (.xlsx)",
        data=buffer.getvalue(),
        file_name="datos_maate_limpios.xlsx",
        mime="application/vnd.ms-excel",
        use_container_width=True,
    )