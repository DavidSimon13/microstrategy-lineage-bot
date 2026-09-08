import csv
import json
import re
from pathlib import Path


def _safe_filename(value):
    """
    Convierte un nombre de objeto en un nombre
    seguro para archivos.
    """

    if not value:
        return "microstrategy_object"

    value = value.strip()

    value = re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        value
    )

    value = value.strip("_")

    return value or "microstrategy_object"


def _detect_project(location):
    """
    Obtiene el proyecto a partir de Object Location.

    Ejemplo:

        /Operaciones/Objetos públicos/...

    devuelve:

        Operaciones
    """

    if not location:
        return "UNKNOWN"

    parts = [
        part
        for part in location.split("/")
        if part
    ]

    if not parts:
        return "UNKNOWN"

    return parts[0]


def build_report_payload(
    classified_result,
    migration_summary
):
    """
    Construye la estructura principal del reporte.
    """

    obj = classified_result[
        "start_object"
    ]

    return {
        "project":
            _detect_project(
                obj.get(
                    "location", ""
                )
            ),

        "object": {
            "name":
                obj.get(
                    "name", ""
                ),

            "guid":
                obj.get(
                    "guid", ""
                ),

            "type":
                obj.get(
                    "type", ""
                ),

            "level":
                obj.get(
                    "level", ""
                ),

            "location":
                obj.get(
                    "location", ""
                ),
        },

        "summary": {
            "physical_table_count":
                migration_summary.get(
                    "physical_table_count",
                    0
                ),

            "migrate_count":
                migration_summary.get(
                    "migrate_count",
                    0
                ),

            "validate_sql_count":
                migration_summary.get(
                    "validate_sql_count",
                    0
                ),

            "auxiliary_count":
                migration_summary.get(
                    "auxiliary_count",
                    0
                ),
        },

        "logical_tables":
            classified_result.get(
                "logical_tables", []
            ),

        "physical_tables":
            migration_summary.get(
                "physical_tables", []
            ),

        "lineage_edges":
            classified_result.get(
                "edges", []
            ),
    }


def export_json(
    payload,
    file_path
):
    """
    Exporta el reporte completo en JSON.
    """

    with file_path.open(
        mode="w",
        encoding="utf-8"
    ) as json_file:

        json.dump(
            payload,
            json_file,
            ensure_ascii=False,
            indent=2
        )


def export_physical_tables_csv(
    migration_summary,
    file_path
):
    """
    Exporta las tablas físicas únicas.
    """

    fieldnames = [
        "name",
        "guid",
        "type",
        "level",
        "migration_status",
        "reason",
    ]

    with file_path.open(
        mode="w",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for table in migration_summary.get(
            "physical_tables", []
        ):

            writer.writerow({
                "name":
                    table.get(
                        "name", ""
                    ),

                "guid":
                    table.get(
                        "guid", ""
                    ),

                "type":
                    table.get(
                        "type", ""
                    ),

                "level":
                    table.get(
                        "level", ""
                    ),

                "migration_status":
                    table.get(
                        "migration_status", ""
                    ),

                "reason":
                    table.get(
                        "reason", ""
                    ),
            })


def export_lineage_edges_csv(
    classified_result,
    file_path
):
    """
    Exporta todas las relaciones del lineage.
    """

    fieldnames = [
        "depth",
        "parent_guid",
        "parent_name",
        "parent_type",
        "parent_level",
        "child_guid",
        "child_name",
        "child_type",
        "child_level",
    ]

    with file_path.open(
        mode="w",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for edge in classified_result.get(
            "edges", []
        ):

            writer.writerow({
                field:
                    edge.get(
                        field, ""
                    )
                for field in fieldnames
            })


def export_results(
    classified_result,
    migration_summary,
    output_dir="outputs"
):
    """
    Genera los archivos finales del análisis.

    Retorna las rutas generadas.
    """

    output_dir = Path(
        output_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    obj = classified_result[
        "start_object"
    ]

    base_name = _safe_filename(
        obj.get(
            "name", ""
        )
    )

    guid = obj.get(
        "guid", ""
    )

    if guid:
        base_name = (
            f"{base_name}_{guid}"
        )

    report_dir = (
        output_dir
        / base_name
    )

    report_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    json_path = (
        report_dir
        / "resumen.json"
    )

    physical_csv_path = (
        report_dir
        / "physical_tables.csv"
    )

    lineage_csv_path = (
        report_dir
        / "lineage_edges.csv"
    )

    payload = build_report_payload(
        classified_result,
        migration_summary
    )

    export_json(
        payload,
        json_path
    )

    export_physical_tables_csv(
        migration_summary,
        physical_csv_path
    )

    export_lineage_edges_csv(
        classified_result,
        lineage_csv_path
    )

    return {
        "report_dir":
            str(report_dir),

        "json":
            str(json_path),

        "physical_tables_csv":
            str(
                physical_csv_path
            ),

        "lineage_edges_csv":
            str(
                lineage_csv_path
            ),
    }
