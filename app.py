from pathlib import Path
import pandas as pd
import streamlit as st

from src.microstrategy_lineage.loader import (
    load_platform_analytics,
)
from src.microstrategy_lineage.resolver import (
    resolve_object,
    ObjectResolutionError,
)
from src.microstrategy_lineage.graph import (
    traverse_lineage,
)
from src.microstrategy_lineage.classifier import (
    classify_lineage,
)
from src.microstrategy_lineage.migration import (
    build_migration_summary,
)
from src.microstrategy_lineage.diagnostics import (
    build_diagnostics,
)

# ============================================================
# CONFIGURACION
# ============================================================

APP_NAME = "Maya"
APP_SUBTITLE = "Linaje y Mapeo de Activos para la Migracion BI"
LOGO_PATH = Path("assets/Maya.jpg")

CHATGPT_URL = "https://chatgpt.com/share/e/6aa065e7-6ba8-8016-8fca-a76a5a4e65e8"
GEMINI_MAYA_URL = "https://gemini.google.com/gem/1uUnE0tCXInojHDAqsPX889scRJ-e_Eqw?usp=sharing"

# ============================================================
# DATASETS
# ============================================================

DATASETS = {
    "Operaciones": Path("data/Analisis de objetos_Operaciones.csv"),
    "Sistemas y Operaciones": Path("data/Analisis de objetos_Sistemas y Operaciones.csv"),
    "CIB": Path("data/Analisis de objetos_CIB.csv"),
    "Datamart Auditoria": Path("data/Analisis de objetos_Datamart Auditoria.csv"),
    "Banca Comercial": Path("data/Analisis de objetos_Banca Comercial.csv"),
}

# ============================================================
# CONFIGURACION DE STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Maya",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "Inicio"

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_project" not in st.session_state:
    st.session_state.last_project = None

if "last_query" not in st.session_state:
    st.session_state.last_query = None

# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #020A12 0%, #031426 45%, #061D34 100%);
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #010811 0%, #031426 100%);
        border-right: 1px solid #15517B;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .maya-title {
        font-size: 34px;
        font-weight: 800;
        line-height: 1.1;
    }
    .maya-accent {
        color: #4CB8FF;
    }
    .maya-subtitle {
        color: #A9C6DA;
        font-size: 15px;
        margin-top: 6px;
    }
    .maya-card {
        padding: 22px;
        border-radius: 16px;
        border: 1px solid #1C5A84;
        background: linear-gradient(145deg, #061526, #09253D);
        margin-bottom: 18px;
    }
    .maya-section-title {
        color: #62C3FF;
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    
    /* Diseño general para los botones principales (pantalla central) */
    div.stButton > button {
        width: 100%;
        min-height: 44px;
        border-radius: 10px;
        border: 1px solid #2879AA;
        background: #092943;
        color: white;
        font-weight: 600;
    }
    div.stButton > button:hover {
        background: #10456D;
        border-color: #55BDFF;
        color: white;
    }

    /* SOBREESCRIBIR: Diseño transparente solo para los botones del SIDEBAR */
    section[data-testid="stSidebar"] div.stButton > button {
        border: none !important;
        background: transparent !important;
        color: #A9C6DA !important;
        justify-content: flex-start !important; /* Alinea el texto a la izquierda */
        padding-left: 10px !important;
        font-size: 16px !important;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        color: #62C3FF !important; /* Brilla en azul claro al pasar el mouse */
        background: rgba(255,255,255,0.05) !important;
    }

    [data-testid="stLinkButton"] a {
        width: 100%;
        min-height: 44px;
        border-radius: 10px;
        border: 1px solid #2879AA;
        background: #092943;
        color: white;
        font-weight: 600;
    }
    [data-testid="stLinkButton"] a:hover {
        background: #10456D;
        border-color: #55BDFF;
        color: white;
    }
    [data-testid="stMetric"] {
        background: #071A2C;
        border: 1px solid #1C567D;
        border-radius: 12px;
        padding: 12px;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #1C567D;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# FUNCIONES
# ============================================================

@st.cache_data(show_spinner=False)
def load_dataset(dataset_path):
    return load_platform_analytics(str(dataset_path))

def analyze_object(dataset_path, object_query):
    rows = load_dataset(dataset_path)
    obj = resolve_object(rows, object_query)
    lineage = traverse_lineage(rows, obj["guid"])
    classified = classify_lineage(lineage)
    migration_summary = build_migration_summary(classified)
    diagnostics = build_diagnostics(classified, migration_summary)
    
    return {
        "object": obj,
        "classified": classified,
        "migration": migration_summary,
        "diagnostics": diagnostics,
    }

def show_logo(width=120):
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=width)
    else:
        st.markdown("## 🤖")

def navigate(page_name):
    st.session_state.page = page_name

def status_icon(status):
    if status == "SUCCESS": return "✅"
    if status == "SUCCESS_WITH_WARNINGS": return "⚠️"
    if status == "NEEDS_INPUT": return "🟡"
    return "❌"

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    show_logo(width=120)
    st.markdown(f"# {APP_NAME}")
    st.caption("MicroStrategy Lineage")
    st.divider()

    # Botones transparentes con ancho completo
    if st.button("Inicio", use_container_width=True):
        navigate("Inicio")

    if st.button("Analisis", use_container_width=True):
        navigate("Analisis")

    if st.button("Lineage", use_container_width=True):
        navigate("Lineage")

    if st.button("Migracion AWS", use_container_width=True):
        navigate("Migracion")

    if st.button("Historial", use_container_width=True):
        navigate("Historial")

    st.divider()
    st.caption("Maya | Metadata & Lineage")

# ============================================================
# CONTENIDO PRINCIPAL
# ============================================================

page = st.session_state.page

# ============================================================
# HEADER
# ============================================================

header_logo, header_text = st.columns([1.2, 6], vertical_alignment="center")

with header_logo:
    show_logo(width=145)

with header_text:
    st.markdown(
        f"""
        <div class="maya-title">
            👋 Hola, soy <span class="maya-accent">{APP_NAME}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="maya-subtitle">
            {APP_SUBTITLE}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("MicroStrategy  •  Platform Analytics  •  AWS")

st.divider()

# ============================================================
# PAGINA INICIO
# ============================================================

if page == "Inicio":
    st.markdown("## Bienvenido 👋")
    st.markdown(
        """
        <div class="maya-card">
        <div class="maya-section-title">Maya</div>
        Este espacio permite localizar objetos de MicroStrategy, recorrer su lineage
        y determinar las tablas físicas que participan en el proceso.
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Arquitectura", "N6 → N1")
    with c2: st.metric("Identidad", "GUID")
    with c3: st.metric("Destino", "AWS")

    st.markdown("---")
    st.markdown("### ⚡ Acciones rapidas")

    a1, a2 = st.columns(2)
    with a1:
        if st.button("🔎 Analizar un objeto", use_container_width=True):
            navigate("Analisis")
            st.rerun()
        if st.button("🧬 Ver ultimo lineage", use_container_width=True):
            navigate("Lineage")
            st.rerun()
    with a2:
        if st.button("☁️ Ver scope AWS", use_container_width=True):
            navigate("Migracion")
            st.rerun()
        if st.button("🕘 Ver historial", use_container_width=True):
            navigate("Historial")
            st.rerun()

# ============================================================
# PAGINA ANALISIS
# ============================================================

elif page == "Analisis":
    st.markdown("## 🔎 Analizar objeto")

    project = st.selectbox("Proyecto", list(DATASETS.keys()))
    object_query = st.text_input("Nombre o GUID del objeto", placeholder="Ejemplo: TLP504 RASTREO")

    if st.button("🚀 Ejecutar analisis", type="primary", use_container_width=True):
        if not object_query.strip():
            st.warning("Debes introducir un nombre o GUID.")
        else:
            dataset_path = DATASETS[project]
            if not dataset_path.exists():
                st.error("No se encontró el dataset:")
                st.code(str(dataset_path))
            else:
                try:
                    with st.spinner("Analizando lineage..."):
                        result = analyze_object(dataset_path, object_query)
                    
                    st.session_state.last_result = result
                    st.session_state.last_project = project
                    st.session_state.last_query = object_query
                    st.success("✅ Analisis completado.")

                except ObjectResolutionError as error:
                    st.warning(str(error))
                except Exception as error:
                    st.error("Error técnico durante el analisis.")
                    st.exception(error)

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------
    result = st.session_state.last_result

    if result:
        classified = result["classified"]
        obj = classified.get("start_object", result["object"])
        migration = result["migration"]
        diagnostics = result["diagnostics"]

        st.divider()
        st.markdown("## 📊 Resultado")

        st.markdown(
            f"""
            <div class="maya-card">
            <b>Objeto</b><br>{obj.get("name", "")}<br><br>
            <b>GUID</b><br>{obj.get("guid", "")}<br><br>
            <b>Tipo</b><br>{obj.get("type", "")}<br><br>
            <b>Nivel</b><br>{obj.get("level", "")}<br><br>
            <b>Ubicacion</b><br>{obj.get("location", "")}
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Physical Tables", migration.get("physical_table_count", 0))
        c2.metric("MIGRATE", migration.get("migrate_count", 0))
        c3.metric("VALIDATE SQL", migration.get("validate_sql_count", 0))
        
        status = diagnostics.get("status", "UNKNOWN")
        c4.metric("Status", f"{status_icon(status)} {status}")

        physical_tables = migration.get("physical_tables", []) or []

        if physical_tables:
            st.markdown("### 🗄️ Tablas fisicas")

            # 1. Convertimos los resultados a un DataFrame de Pandas
            df_tables = pd.DataFrame(physical_tables)

            # 2. Arreglamos la columna rebelde pasándola a texto legible
            if "evidence_path" in df_tables.columns:
                df_tables["evidence_path"] = df_tables["evidence_path"].astype(str)

            # 3. Mostrar tabla corregida en pantalla
            st.dataframe(df_tables, use_container_width=True, hide_index=True)

            # --------------------------------------------------------
            # EXPORTACIONES CSV
            # --------------------------------------------------------
            try:
                # Usar el DataFrame corregido para la exportación
                export_df = df_tables.copy()

                # CSV COMPLETO
                csv_all = export_df.to_csv(index=False, encoding="utf-8-sig")

                # CSV MIGRATE
                if "Estado" in export_df.columns:
                    migrate_df = export_df[export_df["Estado"].astype(str).str.upper().eq("MIGRATE")].copy()
                elif "status" in export_df.columns:
                    migrate_df = export_df[export_df["status"].astype(str).str.upper().eq("MIGRATE")].copy()
                else:
                    migrate_df = pd.DataFrame(columns=export_df.columns)

                csv_migrate = migrate_df.to_csv(index=False, encoding="utf-8-sig")

                # CSV VALIDATE_SQL
                if "Estado" in export_df.columns:
                    validate_df = export_df[export_df["Estado"].astype(str).str.upper().eq("VALIDATE_SQL")].copy()
                elif "status" in export_df.columns:
                    validate_df = export_df[export_df["status"].astype(str).str.upper().eq("VALIDATE_SQL")].copy()
                else:
                    validate_df = pd.DataFrame(columns=export_df.columns)

                csv_validate = validate_df.to_csv(index=False, encoding="utf-8-sig")

                object_name = st.session_state.last_query or "objeto"
                safe_object_name = str(object_name).strip().replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_")

                st.markdown("### 📥 Descargar resultados")
                d1, d2, d3 = st.columns(3)

                with d1:
                    st.download_button(
                        label="📥 CSV completo",
                        data=csv_all,
                        file_name=f"Maya_{safe_object_name}_physical_tables.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with d2:
                    st.download_button(
                        label="📥 CSV MIGRATE",
                        data=csv_migrate,
                        file_name=f"Maya_{safe_object_name}_MIGRATE.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with d3:
                    st.download_button(
                        label="📥 CSV VALIDATE_SQL",
                        data=csv_validate,
                        file_name=f"Maya_{safe_object_name}_VALIDATE_SQL.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

            except Exception as export_error:
                st.warning("No fue posible generar los archivos CSV.")
                st.caption(f"Detalle: {export_error}")

# ============================================================
# PAGINA LINEAGE
# ============================================================

elif page == "Lineage":
    st.markdown("## 🧬 Lineage")
    result = st.session_state.last_result

    if not result:
        st.info("Ejecuta primero un analisis.")
    else:
        obj = result["classified"].get("start_object", {})
        st.markdown(f"**Objeto:** {obj.get('name', '')}\n\n**GUID:** `{obj.get('guid', '')}`")

        edges = result["classified"].get("edges", []) or []
        st.metric("Relaciones detectadas", len(edges))

        if edges:
            st.dataframe(edges, use_container_width=True, hide_index=True)
        else:
            st.info("No se detectaron relaciones.")

# ============================================================
# PAGINA MIGRACION
# ============================================================

elif page == "Migracion":
    st.markdown("## ☁️ Scope de Migracion AWS")
    result = st.session_state.last_result

    if not result:
        st.info("Ejecuta primero un analisis.")
    else:
        migration = result["migration"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Physical Tables", migration.get("physical_table_count", 0))
        c2.metric("MIGRATE", migration.get("migrate_count", 0))
        c3.metric("VALIDATE SQL", migration.get("validate_sql_count", 0))
        c4.metric("AUXILIARY", migration.get("auxiliary_count", 0))

        physical_tables = migration.get("physical_tables", []) or []

        if physical_tables:
            st.markdown("### Tablas")
            
            # También aplicamos la corrección aquí para la vista de migración
            df_migration = pd.DataFrame(physical_tables)
            if "evidence_path" in df_migration.columns:
                df_migration["evidence_path"] = df_migration["evidence_path"].astype(str)
                
            st.dataframe(df_migration, use_container_width=True, hide_index=True)

# ============================================================
# PAGINA HISTORIAL
# ============================================================

elif page == "Historial":
    st.markdown("## 🕘 Historial")

    if st.session_state.last_result is None:
        st.info("Todavia no hay analisis en esta sesion.")
    else:
        result = st.session_state.last_result
        obj = result["classified"].get("start_object", {})
        diagnostics = result["diagnostics"]

        st.markdown(
            f"""
            ### Ultimo analisis
            **Proyecto:** {st.session_state.last_project}

            **Busqueda:** {st.session_state.last_query}

            **Objeto:** {obj.get("name", "")}

            **GUID:** `{obj.get("guid", "")}`

            **Estado:** {diagnostics.get("status", "UNKNOWN")}
            """
        )

# ============================================================
# ACCIONES RAPIDAS / ASISTENTES
# ============================================================

st.sidebar.divider()
st.sidebar.markdown("### ⚡ Accesos rapidos")
st.sidebar.link_button("💬 Abrir ChatGPT", CHATGPT_URL, use_container_width=True)
st.sidebar.link_button("💎 Abrir Maya", GEMINI_MAYA_URL, use_container_width=True)
