from pathlib import Path

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
# CONFIGURACION GENERAL
# ============================================================

APP_NAME = "Maya"

APP_SUBTITLE = (
    "Linaje y Mapeo de Activos para la Migracion BI"
)

LOGO_PATH = Path(
    "assets/Maya.jpg"
)


# ============================================================
# ENLACES EXTERNOS
# ============================================================

CHATGPT_URL = (
    "https://chatgpt.com/share/e/"
    "6aa065e7-6ba8-8016-8fca-a76a5a4e65e8"
)

GEMINI_DIANA_URL = (
    "https://gemini.google.com/gem/"
    "1YjYZugs7wzG-9JBFy0U1YyoaL8kRJpl1"
    "?usp=sharing"
)


# ============================================================
# DATASETS
# ============================================================

DATASETS = {
    "Operaciones":
        Path(
            "data/Analisis de objetos_Operaciones.csv"
        ),

    "Sistemas y Operaciones":
        Path(
            "data/Analisis de objetos_Sistemas y Operaciones.csv"
        ),

    "CIB":
        Path(
            "data/Analisis de objetos_CIB.csv"
        ),

    "Datamart Auditoria":
        Path(
            "data/Analisis de objetos_Datamart Auditoria.csv"
        ),

    "Banca Comercial":
        Path(
            "data/Analisis de objetos_Banca Comercial.csv"
        ),
}


# ============================================================
# CONFIGURACION DE PAGINA
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
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

    /* ====================================================
       APP GENERAL
       ==================================================== */

    .stApp {
        background:
            linear-gradient(
                135deg,
                #020b14 0%,
                #031426 35%,
                #061c32 70%,
                #08243e 100%
            );

        color: #ffffff;
    }


    /* ====================================================
       SIDEBAR
       ==================================================== */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #010913 0%,
                #031424 100%
            );

        border-right:
            1px solid #174b73;
    }


    section[data-testid="stSidebar"] hr {
        border-color: #174b73;
    }


    /* ====================================================
       HEADER
       ==================================================== */

    .main-header {
        padding: 24px 28px;

        border:
            1px solid #23628f;

        border-radius:
            18px;

        background:
            linear-gradient(
                135deg,
                #06182b,
                #092844
            );

        margin-bottom: 18px;

        box-shadow:
            0px 0px 28px
            rgba(
                0,
                133,
                214,
                0.13
            );
    }


    .app-title {
        font-size: 31px;

        font-weight: 800;

        margin-bottom: 2px;

        color: #ffffff;
    }


    .app-title-accent {
        color: #4cb8ff;
    }


    .app-subtitle {
        color: #a8c6dd;

        font-size: 14px;

        margin-top: 5px;
    }


    /* ====================================================
       CARDS
       ==================================================== */

    .lineage-card {
        background:
            linear-gradient(
                145deg,
                #061729,
                #09243d
            );

        border:
            1px solid #215c87;

        border-radius:
            16px;

        padding: 20px;

        margin-bottom: 14px;

        box-shadow:
            0px 0px 15px
            rgba(
                0,
                100,
                180,
                0.07
            );
    }


    .metric-card {
        background: #071a2d;

        border:
            1px solid #1e567f;

        border-radius:
            14px;

        padding: 18px;

        text-align: center;

        min-height: 115px;
    }


    .metric-number {
        font-size: 28px;

        font-weight: 800;

        color: #54bdff;
    }


    .metric-title {
        font-size: 13px;

        color: #9dbbd0;

        margin-top: 5px;
    }


    /* ====================================================
       BOTONES NORMALES
       ==================================================== */

    div.stButton > button {
        width: 100%;

        border-radius: 10px;

        min-height: 42px;

        border:
            1px solid #3788bd;

        background:
            #092844;

        color: #ffffff;

        font-weight: 600;

        transition:
            all 0.15s ease;
    }


    div.stButton > button:hover {
        background: #10426b;

        border-color: #55bfff;

        color: #ffffff;

        transform:
            translateY(-1px);
    }


    div.stButton > button:active {
        background: #176295;

        color: #ffffff;
    }


    /* ====================================================
       BOTONES DE LINKS
       ==================================================== */

    [data-testid="stLinkButton"] a {
        width: 100%;

        min-height: 42px;

        border-radius: 10px;

        border:
            1px solid #3788bd;

        background:
            #092844;

        color: #ffffff;

        font-weight: 600;

        text-decoration: none;

        transition:
            all 0.15s ease;
    }


    [data-testid="stLinkButton"] a:hover {
        background: #10426b;

        border-color: #55bfff;

        color: #ffffff;

        transform:
            translateY(-1px);
    }


    /* ====================================================
       INPUTS
       ==================================================== */

    div[data-baseweb="input"] {
        background: #0a223b;

        border-radius: 10px;
    }


    div[data-baseweb="select"] > div {
        background: #0a223b;

        border-color: #245e87;

        color: white;
    }


    /* ====================================================
       DATAFRAMES
       ==================================================== */

    [data-testid="stDataFrame"] {
        border:
            1px solid #1e567f;

        border-radius: 10px;

        overflow: hidden;
    }


    /* ====================================================
       METRICAS NATIVAS
       ==================================================== */

    [data-testid="stMetric"] {
        background: #071a2d;

        border:
            1px solid #1e567f;

        border-radius: 12px;

        padding: 14px;
    }


    /* ====================================================
       OCULTAR DECORACION STREAMLIT
       ==================================================== */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FUNCIONES
# ============================================================

@st.cache_data(
    show_spinner=False
)
def load_dataset(
    dataset_path
):
    """
    Carga el dataset de Platform Analytics.

    Streamlit mantiene el dataset en cache
    para evitar leer el CSV nuevamente
    con cada click.
    """

    return load_platform_analytics(
        str(
            dataset_path
        )
    )


def analyze_object(
    dataset_path,
    object_query
):
    """
    Ejecuta el motor de lineage existente.
    """

    rows = load_dataset(
        dataset_path
    )

    obj = resolve_object(
        rows,
        object_query
    )

    lineage = traverse_lineage(
        rows,
        obj["guid"]
    )

    classified = classify_lineage(
        lineage
    )

    migration_summary = (
        build_migration_summary(
            classified
        )
    )

    diagnostics = (
        build_diagnostics(
            classified,
            migration_summary
        )
    )

    return {
        "object":
            obj,

        "classified":
            classified,

        "migration":
            migration_summary,

        "diagnostics":
            diagnostics,
    }


def change_page(
    page_name
):
    """
    Cambia la seccion visible
    dentro de la aplicacion.
    """

    st.session_state.page = (
        page_name
    )


def render_logo():
    """
    Muestra el logo personalizado
    cuando exista assets/logo.png.

    Mientras no exista utiliza
    un icono temporal.
    """

    if LOGO_PATH.exists():

        st.image(
           str(
               LOGO_PATH
           ),
           width=180,
       )

    else:

        st.markdown(
            """
            <div style="
                width:78px;
                height:78px;
                border-radius:50%;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:38px;
                background:#0a3154;
                border:2px solid #2c85bd;
                margin-bottom:10px;
                box-shadow:
                    0 0 18px
                    rgba(76,184,255,0.15);
            ">
                🤖
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    render_logo()

    st.markdown(
        f"### {APP_NAME}"
    )

    st.caption(
        "MicroStrategy Metadata"
    )

    st.markdown("---")

    if st.button(
        "🏠 Inicio",
        use_container_width=True,
    ):
        change_page(
            "Inicio"
        )

    if st.button(
        "🔎 Analisis",
        use_container_width=True,
    ):
        change_page(
            "Analisis"
        )

    if st.button(
        "🧬 Lineage",
        use_container_width=True,
    ):
        change_page(
            "Lineage"
        )

    if st.button(
        "☁️ Migracion AWS",
        use_container_width=True,
    ):
        change_page(
            "Migracion"
        )

    if st.button(
        "🕘 Historial",
        use_container_width=True,
    ):
        change_page(
            "Historial"
        )

    st.markdown("---")

    st.caption(
        "Robot de analisis read-only"
    )


# ============================================================
# HEADER
# ============================================================

header_logo, header_content = st.columns(
    [1, 7],
    vertical_alignment="center",
)

with header_logo:

    if LOGO_PATH.exists():

        st.image(
            str(LOGO_PATH),
            width=115,
        )

    else:

        st.markdown(
            """
            <div style="
                width:95px;
                height:95px;
                border-radius:50%;
                display:flex;
                align-items:center;
                justify-content:center;
                font-size:44px;
                background:#0A3154;
                border:2px solid #4CB8FF;
            ">
                🤖
            </div>
            """,
            unsafe_allow_html=True,
        )


with header_content:

    st.markdown(
        f"""
        <div class="main-header">

            <div class="app-title">
                Hola, soy
                <span class="app-title-accent">
                    {APP_NAME}
                </span>
            </div>

            <div class="app-subtitle">
                {APP_SUBTITLE}
            </div>

            <div style="
                margin-top:10px;
                color:#6FAED7;
                font-size:13px;
            ">
                MicroStrategy · Platform Analytics · AWS Migration
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# LAYOUT PRINCIPAL
# ============================================================

main_column, action_column = (
    st.columns(
        [4.5, 1.3],
        gap="large",
    )
)


# ============================================================
# ACCIONES RAPIDAS
# ============================================================

with action_column:

    st.markdown(
        "### ⚡ Acciones rapidas"
    )

    if st.button(
        "🔎 Analizar objeto",
        use_container_width=True,
    ):

        change_page(
            "Analisis"
        )

    if st.button(
        "🧬 Ver lineage",
        use_container_width=True,
    ):

        change_page(
            "Lineage"
        )

    if st.button(
        "☁️ Scope AWS",
        use_container_width=True,
    ):

        change_page(
            "Migracion"
        )

    if st.button(
        "🕘 Ultimo analisis",
        use_container_width=True,
    ):

        change_page(
            "Historial"
        )


    # --------------------------------------------------------
    # ASISTENTES EXTERNOS
    # --------------------------------------------------------

    st.markdown("---")

    st.markdown(
        "### 🤖 Asistentes"
    )

    st.link_button(
        "💬 Abrir ChatGPT",
        CHATGPT_URL,
        use_container_width=True,
    )

    st.link_button(
        "💎 Abrir Diana",
        GEMINI_DIANA_URL,
        use_container_width=True,
    )


    # --------------------------------------------------------
    # ESTADO DEL ROBOT
    # --------------------------------------------------------

    st.markdown("---")

    st.markdown(
        "### 📌 Estado"
    )

    if (
        st.session_state
        .last_result
        is not None
    ):

        diagnostics = (
            st.session_state
            .last_result[
                "diagnostics"
            ]
        )

        status = (
            diagnostics.get(
                "status",
                "UNKNOWN"
            )
        )

        if status == "SUCCESS":

            st.success(
                "✅ SUCCESS"
            )

        elif (
            status
            == "SUCCESS_WITH_WARNINGS"
        ):

            st.warning(
                "⚠️ SUCCESS WITH WARNINGS"
            )

        elif status == "NEEDS_INPUT":

            st.warning(
                "ℹ️ NEEDS INPUT"
            )

        else:

            st.error(
                status
            )

    else:

        st.info(
            "Sin analisis activo"
        )


# ============================================================
# CONTENIDO PRINCIPAL
# ============================================================

with main_column:

    page = (
        st.session_state.page
    )


    # ========================================================
    # INICIO
    # ========================================================

    if page == "Inicio":

        st.markdown(
            """
            <div class="lineage-card">

                <h3>
                    👋 Bienvenido
                </h3>

                <p>
                    Este Robot permite analizar
                    dependencias de objetos de
                    MicroStrategy utilizando
                    metadata de Platform Analytics.
                </p>

                <p>
                    Puedes localizar las tablas
                    fisicas utilizadas por un
                    reporte, documento o dashboard
                    y generar el scope tecnico
                    para migracion.
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:

            st.markdown(
                """
                <div class="metric-card">

                    <div class="metric-number">
                        N6 → N1
                    </div>

                    <div class="metric-title">
                        Lineage arquitectonico
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:

            st.markdown(
                """
                <div class="metric-card">

                    <div class="metric-number">
                        GUID
                    </div>

                    <div class="metric-title">
                        Identidad principal
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:

            st.markdown(
                """
                <div class="metric-card">

                    <div class="metric-number">
                        AWS
                    </div>

                    <div class="metric-title">
                        Scope de migracion
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


    # ========================================================
    # ANALISIS
    # ========================================================

    elif page == "Analisis":

        st.markdown(
            "## 🔎 Analizar objeto MicroStrategy"
        )

        st.markdown(
            """
            <div class="lineage-card">
                Selecciona el proyecto y escribe
                el nombre exacto o GUID del objeto
                que deseas analizar.
            </div>
            """,
            unsafe_allow_html=True,
        )

        project = st.selectbox(
            "Proyecto",
            list(
                DATASETS.keys()
            ),
        )

        object_query = st.text_input(
            "Nombre o GUID del objeto",
            placeholder=(
                "Ejemplo: "
                "TLP504 RASTREO"
            ),
        )

        analyze = st.button(
            "🚀 Analizar",
            type="primary",
            use_container_width=True,
        )

        if analyze:

            if not (
                object_query.strip()
            ):

                st.warning(
                    "Escribe el nombre "
                    "o GUID del objeto."
                )

            else:

                dataset_path = (
                    DATASETS[
                        project
                    ]
                )

                if not (
                    dataset_path.exists()
                ):

                    st.error(
                        "No se encontro "
                        "el dataset:\n\n"
                        f"{dataset_path}"
                    )

                else:

                    try:

                        with st.spinner(
                            "Analizando metadata..."
                        ):

                            result = (
                                analyze_object(
                                    dataset_path,
                                    object_query,
                                )
                            )

                        st.session_state.last_result = (
                            result
                        )

                        st.session_state.last_project = (
                            project
                        )

                        st.session_state.last_query = (
                            object_query
                        )

                        st.success(
                            "✅ Analisis completado."
                        )

                    except (
                        ObjectResolutionError
                    ) as error:

                        st.warning(
                            str(
                                error
                            )
                        )

                    except Exception as error:

                        st.error(
                            "Ocurrio un error tecnico "
                            "durante el analisis."
                        )

                        st.exception(
                            error
                        )


        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        result = (
            st.session_state
            .last_result
        )

        if result:

            obj = (
                result[
                    "classified"
                ].get(
                    "start_object",
                    result["object"]
                )
            )

            migration = (
                result[
                    "migration"
                ]
            )

            diagnostics = (
                result[
                    "diagnostics"
                ]
            )

            st.markdown("---")

            st.markdown(
                "## 📊 Resultado"
            )

            st.markdown(
                f"""
                <div class="lineage-card">

                    <b>Object Name</b><br>
                    {obj.get("name", "")}

                    <br><br>

                    <b>GUID</b><br>
                    {obj.get("guid", "")}

                    <br><br>

                    <b>Object Type</b><br>
                    {obj.get("type", "")}

                    <br><br>

                    <b>Nivel</b><br>
                    {obj.get("level", "")}

                    <br><br>

                    <b>Location</b><br>
                    {obj.get("location", "")}

                </div>
                """,
                unsafe_allow_html=True,
            )

            m1, m2, m3, m4 = (
                st.columns(4)
            )

            m1.metric(
                "Physical Tables",
                migration.get(
                    "physical_table_count",
                    0
                ),
            )

            m2.metric(
                "MIGRATE",
                migration.get(
                    "migrate_count",
                    0
                ),
            )

            m3.metric(
                "VALIDATE SQL",
                migration.get(
                    "validate_sql_count",
                    0
                ),
            )

            m4.metric(
                "Status",
                diagnostics.get(
                    "status",
                    "UNKNOWN"
                ),
            )

            physical_tables = (
                migration.get(
                    "physical_tables",
                    []
                )
                or []
            )

            if physical_tables:

                st.markdown(
                    "### 🗄️ Physical Tables"
                )

                st.dataframe(
                    physical_tables,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No se detectaron "
                    "tablas fisicas."
                )


    # ========================================================
    # LINEAGE
    # ========================================================

    elif page == "Lineage":

        st.markdown(
            "## 🧬 Lineage"
        )

        result = (
            st.session_state
            .last_result
        )

        if not result:

            st.info(
                "Primero ejecuta un analisis."
            )

        else:

            obj = (
                result[
                    "classified"
                ].get(
                    "start_object",
                    {}
                )
            )

            st.markdown(
                f"""
                <div class="lineage-card">

                    <b>Objeto analizado:</b>
                    {obj.get("name", "")}

                    <br>

                    <b>GUID:</b>
                    {obj.get("guid", "")}

                </div>
                """,
                unsafe_allow_html=True,
            )

            edges = (
                result[
                    "classified"
                ].get(
                    "edges",
                    []
                )
                or []
            )

            st.metric(
                "Relaciones detectadas",
                len(
                    edges
                ),
            )

            if edges:

                st.dataframe(
                    edges,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No se detectaron "
                    "relaciones de lineage."
                )


    # ========================================================
    # MIGRACION AWS
    # ========================================================

    elif page == "Migracion":

        st.markdown(
            "## ☁️ Scope de Migracion AWS"
        )

        result = (
            st.session_state
            .last_result
        )

        if not result:

            st.info(
                "Primero ejecuta un analisis."
            )

        else:

            migration = (
                result[
                    "migration"
                ]
            )

            c1, c2, c3, c4 = (
                st.columns(4)
            )

            c1.metric(
                "Physical Tables",
                migration.get(
                    "physical_table_count",
                    0
                ),
            )

            c2.metric(
                "MIGRATE",
                migration.get(
                    "migrate_count",
                    0
                ),
            )

            c3.metric(
                "VALIDATE SQL",
                migration.get(
                    "validate_sql_count",
                    0
                ),
            )

            c4.metric(
                "AUXILIARY",
                migration.get(
                    "auxiliary_count",
                    0
                ),
            )

            physical_tables = (
                migration.get(
                    "physical_tables",
                    []
                )
                or []
            )

            if physical_tables:

                st.markdown(
                    "### 🗄️ Inventario fisico"
                )

                st.dataframe(
                    physical_tables,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No existen tablas fisicas "
                    "para mostrar."
                )


    # ========================================================
    # HISTORIAL
    # ========================================================

    elif page == "Historial":

        st.markdown(
            "## 🕘 Historial"
        )

        if (
            st.session_state
            .last_result
            is None
        ):

            st.info(
                "Todavia no hay "
                "analisis en esta sesion."
            )

        else:

            result = (
                st.session_state
                .last_result
            )

            obj = (
                result[
                    "classified"
                ].get(
                    "start_object",
                    {}
                )
            )

            diagnostics = (
                result[
                    "diagnostics"
                ]
            )

            st.markdown(
                f"""
                <div class="lineage-card">

                    <h4>
                        Ultimo analisis
                    </h4>

                    <b>Proyecto:</b>
                    {st.session_state.last_project}

                    <br><br>

                    <b>Busqueda:</b>
                    {st.session_state.last_query}

                    <br><br>

                    <b>Objeto:</b>
                    {obj.get("name", "")}

                    <br><br>

                    <b>GUID:</b>
                    {obj.get("guid", "")}

                    <br><br>

                    <b>Status:</b>
                    {diagnostics.get("status", "UNKNOWN")}

                </div>
                """,
                unsafe_allow_html=True,
            )
