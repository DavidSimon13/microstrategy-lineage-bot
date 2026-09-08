"""
Diagnósticos del MicroStrategy Lineage Bot.

Este módulo diferencia entre:

- SUCCESS
- SUCCESS_WITH_WARNINGS
- NEEDS_INPUT
- FAILED

El objetivo es evitar que condiciones normales
de metadata sean tratadas como errores técnicos.
"""


STATUS_SUCCESS = "SUCCESS"

STATUS_SUCCESS_WITH_WARNINGS = (
    "SUCCESS_WITH_WARNINGS"
)

STATUS_NEEDS_INPUT = "NEEDS_INPUT"

STATUS_FAILED = "FAILED"


def build_diagnostics(
    classified_result,
    migration_summary
):
    """
    Analiza el resultado del lineage y genera
    un diagnóstico funcional.

    No lanza excepciones.

    Retorna:

    {
        "status": "...",
        "warnings": [],
        "errors": [],
        "metrics": {...}
    }
    """

    warnings = []
    errors = []

    classified_result = (
        classified_result or {}
    )

    migration_summary = (
        migration_summary or {}
    )

    # ---------------------------------
    # Objeto inicial
    # ---------------------------------

    start_object = (
        classified_result.get(
            "start_object"
        )
        or {}
    )

    object_name = start_object.get(
        "name", ""
    )

    object_guid = start_object.get(
        "guid", ""
    )

    object_type = start_object.get(
        "type", ""
    )

    object_level = start_object.get(
        "level", ""
    )

    # ---------------------------------
    # Lineage
    # ---------------------------------

    edges = classified_result.get(
        "edges", []
    ) or []

    logical_tables = (
        classified_result.get(
            "logical_tables", []
        )
        or []
    )

    physical_tables = (
        migration_summary.get(
            "physical_tables", []
        )
        or []
    )

    # ---------------------------------
    # Validaciones críticas
    # ---------------------------------

    if not object_guid:

        errors.append(
            "El objeto inicial no tiene GUID."
        )

    if not object_name:

        warnings.append(
            "El objeto inicial no tiene nombre."
        )

    # ---------------------------------
    # Object Type
    # ---------------------------------

    if not object_type:

        warnings.append(
            "No se pudo determinar "
            "el Object Type."
        )

    # ---------------------------------
    # Nivel arquitectónico
    # ---------------------------------

    known_levels = {
        "N1",
        "N2",
        "N3",
        "N4",
        "N5",
        "N6",
    }

    if not object_level:

        warnings.append(
            "No se pudo determinar "
            "el nivel arquitectónico."
        )

    elif object_level not in known_levels:

        warnings.append(
            "Nivel arquitectónico "
            f"no reconocido: {object_level}"
        )

    # ---------------------------------
    # Componentes
    # ---------------------------------

    if not edges:

        warnings.append(
            "El objeto no tiene dependencias "
            "descendientes detectadas "
            "en Platform Analytics."
        )

    # ---------------------------------
    # Logical Tables
    # ---------------------------------

    if not logical_tables:

        warnings.append(
            "No se localizaron Logical Tables "
            "en el lineage del objeto."
        )

    # ---------------------------------
    # Physical Tables
    # ---------------------------------

    if not physical_tables:

        warnings.append(
            "No se localizaron tablas físicas "
            "relacionales en el lineage."
        )

    # ---------------------------------
    # Tablas sin GUID
    # ---------------------------------

    for table in physical_tables:

        if not table.get("guid"):

            warnings.append(
                "Se encontró una tabla física "
                "sin GUID: "
                f"{table.get('name', 'UNKNOWN')}"
            )

    # ---------------------------------
    # Clasificación de migración
    # ---------------------------------

    migrate_count = (
        migration_summary.get(
            "migrate_count",
            0
        )
    )

    validate_sql_count = (
        migration_summary.get(
            "validate_sql_count",
            0
        )
    )

    auxiliary_count = (
        migration_summary.get(
            "auxiliary_count",
            0
        )
    )

    # ---------------------------------
    # Determinar estado
    # ---------------------------------

    if errors:

        status = STATUS_FAILED

    elif warnings:

        status = (
            STATUS_SUCCESS_WITH_WARNINGS
        )

    else:

        status = STATUS_SUCCESS

    # ---------------------------------
    # Resultado
    # ---------------------------------

    return {
        "status":
            status,

        "warnings":
            warnings,

        "errors":
            errors,

        "metrics": {
            "edge_count":
                len(edges),

            "logical_table_count":
                len(logical_tables),

            "physical_table_count":
                len(physical_tables),

            "migrate_count":
                migrate_count,

            "validate_sql_count":
                validate_sql_count,

            "auxiliary_count":
                auxiliary_count,
        },
    }


def print_diagnostics(
    diagnostics
):
    """
    Imprime el diagnóstico de forma legible.
    """

    diagnostics = diagnostics or {}

    status = diagnostics.get(
        "status",
        STATUS_FAILED
    )

    warnings = diagnostics.get(
        "warnings", []
    )

    errors = diagnostics.get(
        "errors", []
    )

    metrics = diagnostics.get(
        "metrics", {}
    )

    print()
    print("DIAGNOSTICS")
    print("-" * 70)

    print(
        f"Status              : {status}"
    )

    print(
        "Lineage Edges       : "
        f"{metrics.get('edge_count', 0)}"
    )

    print(
        "Logical Tables      : "
        f"{metrics.get('logical_table_count', 0)}"
    )

    print(
        "Physical Tables     : "
        f"{metrics.get('physical_table_count', 0)}"
    )

    print(
        "MIGRATE             : "
        f"{metrics.get('migrate_count', 0)}"
    )

    print(
        "VALIDATE_SQL        : "
        f"{metrics.get('validate_sql_count', 0)}"
    )

    print(
        "AUXILIARY           : "
        f"{metrics.get('auxiliary_count', 0)}"
    )

    if warnings:

        print()
        print("WARNINGS")

        for warning in warnings:
            print(
                f"- {warning}"
            )

    if errors:

        print()
        print("ERRORS")

        for error in errors:
            print(
                f"- {error}"
            )
