import argparse

from .loader import load_platform_analytics
from .resolver import resolve_object
from .graph import traverse_lineage
from .classifier import classify_lineage
from .migration import build_migration_summary
from .output import export_results


def detect_project(object_location):
    """
    Obtiene el nombre del proyecto desde Object Location.

    Ejemplo:

        /Operaciones/Objetos públicos/...

    devuelve:

        Operaciones
    """

    if not object_location:
        return "UNKNOWN"

    parts = [
        part
        for part in object_location.split("/")
        if part
    ]

    if not parts:
        return "UNKNOWN"

    return parts[0]


def get_direct_components(lineage_result):
    """
    Obtiene únicamente los componentes directos
    del objeto inicial.
    """

    start_guid = lineage_result[
        "start_object"
    ]["guid"]

    return [
        edge
        for edge in lineage_result.get(
            "edges", []
        )
        if edge.get("parent_guid") == start_guid
    ]


def print_separator():
    print("-" * 70)


def print_object_summary(
    classified_result,
    direct_components
):
    """
    Imprime el resumen general del objeto.
    """

    obj = classified_result[
        "start_object"
    ]

    project = detect_project(
        obj.get("location", "")
    )

    print()
    print("=" * 70)
    print("MICROSTRATEGY LINEAGE BOT")
    print("=" * 70)

    print()
    print("RESUMEN DEL OBJETO")
    print_separator()

    print(
        f"Proyecto             : {project}"
    )

    print(
        f"Object Name          : "
        f"{obj.get('name', '')}"
    )

    print(
        f"Object GUID          : "
        f"{obj.get('guid', '')}"
    )

    print(
        f"Object Type          : "
        f"{obj.get('type', '')}"
    )

    print(
        f"Nivel                : "
        f"{obj.get('level', '')}"
    )

    print(
        f"Object Location      : "
        f"{obj.get('location', '')}"
    )

    print(
        f"Componentes directos : "
        f"{len(direct_components)}"
    )


def print_direct_components(
    direct_components
):
    """
    Imprime los componentes directos.
    """

    print()
    print("COMPONENTES DIRECTOS")
    print_separator()

    if not direct_components:
        print(
            "No se encontraron componentes directos."
        )
        return

    for edge in direct_components:

        print(
            f"[{edge.get('child_level', 'UNKNOWN')}] "
            f"{edge.get('child_type', '')} | "
            f"{edge.get('child_name', '')} | "
            f"{edge.get('child_guid', '')}"
        )


def print_logical_tables(
    classified_result
):
    """
    Imprime las Logical Tables únicas.
    """

    logical_tables = classified_result.get(
        "logical_tables", []
    )

    print()
    print("LOGICAL TABLES")
    print_separator()

    if not logical_tables:
        print(
            "No se encontraron Logical Tables."
        )
        return

    for table in logical_tables:

        print(
            f"{table.get('name', '')} | "
            f"{table.get('guid', '')} | "
            f"{table.get('level', '')}"
        )


def print_physical_tables(
    migration_summary
):
    """
    Imprime las tablas físicas y su
    clasificación de migración.
    """

    physical_tables = migration_summary.get(
        "physical_tables", []
    )

    print()
    print("PHYSICAL TABLES")
    print_separator()

    if not physical_tables:
        print(
            "No se encontraron tablas físicas."
        )
        return

    for table in physical_tables:

        print(
            f"{table.get('migration_status', ''):15} "
            f"| {table.get('name', '')} "
            f"| {table.get('guid', '')}"
        )


def print_aws_summary(
    migration_summary
):
    """
    Imprime el scope final AWS.
    """

    print()
    print("AWS MIGRATION SUMMARY")
    print_separator()

    print(
        "Physical Tables : "
        f"{migration_summary.get('physical_table_count', 0)}"
    )

    print(
        "MIGRATE         : "
        f"{migration_summary.get('migrate_count', 0)}"
    )

    print(
        "VALIDATE_SQL    : "
        f"{migration_summary.get('validate_sql_count', 0)}"
    )

    print(
        "AUXILIARY       : "
        f"{migration_summary.get('auxiliary_count', 0)}"
    )

    migrate = migration_summary.get(
        "migrate", []
    )

    if migrate:

        print()
        print(
            "TABLAS CONFIRMADAS PARA MIGRACIÓN"
        )

        for table in migrate:

            print(
                f"- {table.get('name', '')}"
            )

    validate_sql = migration_summary.get(
        "validate_sql", []
    )

    if validate_sql:

        print()
        print(
            "TABLAS QUE REQUIEREN VALIDACIÓN SQL"
        )

        for table in validate_sql:

            print(
                f"- {table.get('name', '')}"
            )

    auxiliary = migration_summary.get(
        "auxiliary", []
    )

    if auxiliary:

        print()
        print(
            "TABLAS AUXILIARES"
        )

        for table in auxiliary:

            print(
                f"- {table.get('name', '')}"
            )


def print_generated_files(
    generated_files
):
    """
    Imprime las rutas de los archivos generados.
    """

    print()
    print("ARCHIVOS GENERADOS")
    print_separator()

    print(
        f"Directorio         : "
        f"{generated_files['report_dir']}"
    )

    print(
        f"Resumen JSON       : "
        f"{generated_files['json']}"
    )

    print(
        f"Physical Tables CSV: "
        f"{generated_files['physical_tables_csv']}"
    )

    print(
        f"Lineage Edges CSV  : "
        f"{generated_files['lineage_edges_csv']}"
    )


def run_analysis(
    dataset_path,
    object_query,
    output_dir="outputs"
):
    """
    Ejecuta el pipeline completo:

        CSV
        -> Resolver objeto
        -> Recorrer lineage
        -> Clasificar N6-N1
        -> Clasificar migración
        -> Exportar resultados
    """

    # ---------------------------------
    # 1. Cargar dataset
    # ---------------------------------

    rows = load_platform_analytics(
        dataset_path
    )

    # ---------------------------------
    # 2. Resolver objeto
    # ---------------------------------

    obj = resolve_object(
        rows,
        object_query
    )

    # ---------------------------------
    # 3. Recorrer lineage
    # ---------------------------------

    lineage = traverse_lineage(
        rows,
        obj["guid"]
    )

    # ---------------------------------
    # 4. Clasificación arquitectónica
    # ---------------------------------

    classified = classify_lineage(
        lineage
    )

    # ---------------------------------
    # 5. Clasificación migración AWS
    # ---------------------------------

    migration_summary = (
        build_migration_summary(
            classified
        )
    )

    # ---------------------------------
    # 6. Componentes directos
    # ---------------------------------

    direct_components = (
        get_direct_components(
            classified
        )
    )

    # ---------------------------------
    # 7. Mostrar resultado
    # ---------------------------------

    print_object_summary(
        classified,
        direct_components
    )

    print_direct_components(
        direct_components
    )

    print_logical_tables(
        classified
    )

    print_physical_tables(
        migration_summary
    )

    print_aws_summary(
        migration_summary
    )

    # ---------------------------------
    # 8. Exportar archivos
    # ---------------------------------

    generated_files = export_results(
        classified,
        migration_summary,
        output_dir=output_dir
    )

    print_generated_files(
        generated_files
    )

    print()
    print("=" * 70)

    return {
        "classified_result":
            classified,

        "migration_summary":
            migration_summary,

        "generated_files":
            generated_files,
    }


def main():
    """
    Punto de entrada del robot.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Robot de lineage para "
            "MicroStrategy Platform Analytics"
        )
    )

    parser.add_argument(
        "--data",
        required=True,
        help=(
            "Ruta del CSV exportado "
            "desde Platform Analytics."
        ),
    )

    parser.add_argument(
        "--object",
        required=True,
        help=(
            "Nombre exacto o GUID "
            "del objeto MicroStrategy."
        ),
    )

    parser.add_argument(
        "--output-dir",
        default="outputs",
        help=(
            "Directorio donde se guardarán "
            "los resultados del análisis."
        ),
    )

    args = parser.parse_args()

    try:

        run_analysis(
            dataset_path=args.data,
            object_query=args.object,
            output_dir=args.output_dir
        )

    except Exception as error:

        print()
        print("ERROR")
        print_separator()
        print(str(error))
        print()

        raise SystemExit(1)


if __name__ == "__main__":
    main()
