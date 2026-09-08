import argparse

from .loader import load_platform_analytics
from .resolver import resolve_object
from .graph import traverse_lineage
from .classifier import classify_lineage
from .migration import build_migration_summary


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
        f"Object Name          : {obj.get('name', '')}"
    )
    print(
        f"Object GUID          : {obj.get('guid', '')}"
    )
    print(
        f"Object Type          : {obj.get('type', '')}"
    )
    print(
        f"Nivel                : {obj.get('level', '')}"
    )
    print(
        f"Object Location      : {obj.get('location', '')}"
    )
    print(
        f"Componentes directos : {len(direct_components)}"
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


def run_analysis(
    dataset_path,
    object_query
):
    """
    Ejecuta el pipeline completo.
    """

    rows = load_platform_analytics(
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

    direct_components = (
        get_direct_components(
            classified
        )
    )

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

    print()
    print("=" * 70)


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

    args = parser.parse_args()

    try:

        run_analysis(
            dataset_path=args.data,
            object_query=args.object
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
