import csv
from pathlib import Path


REQUIRED_COLUMNS = {
    "Object Name",
    "Object GUID",
    "Object Location",
    "Object Type DESC",
    "Component Object Name",
    "Component Object GUID",
    "Component Object Type DESC",
}


def detect_encoding(file_path):
    """
    Detecta las codificaciones más habituales
    en exportaciones de Platform Analytics.

    UTF-16 LE comienza normalmente con:
        FF FE

    UTF-16 BE comienza normalmente con:
        FE FF

    En cualquier otro caso intentamos UTF-8
    con soporte para BOM.
    """

    with file_path.open("rb") as binary_file:
        first_bytes = binary_file.read(4)

    if first_bytes.startswith(b"\xff\xfe"):
        return "utf-16"

    if first_bytes.startswith(b"\xfe\xff"):
        return "utf-16"

    return "utf-8-sig"


def load_platform_analytics(file_path):
    """
    Carga un dataset CSV exportado desde
    Platform Analytics.

    Retorna:
        list[dict]:
            relaciones Object -> Component Object
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {file_path}"
        )

    encoding = detect_encoding(file_path)

    print(
        f"Dataset encoding detectado: {encoding}"
    )

    rows = []

    with file_path.open(
        mode="r",
        encoding=encoding,
        newline=""
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            raise ValueError(
                "El archivo CSV no contiene encabezados."
            )

        available_columns = {
            column.strip()
            for column in reader.fieldnames
            if column
        }

        missing_columns = (
            REQUIRED_COLUMNS
            - available_columns
        )

        if missing_columns:
            raise ValueError(
                "Faltan columnas obligatorias: "
                + ", ".join(
                    sorted(missing_columns)
                )
            )

        for row in reader:

            object_guid = (
                row.get(
                    "Object GUID", ""
                ).strip()
            )

            component_guid = (
                row.get(
                    "Component Object GUID", ""
                ).strip()
            )

            if not object_guid:
                continue

            rows.append({
                "object_name":
                    row.get(
                        "Object Name", ""
                    ).strip(),

                "object_guid":
                    object_guid,

                "object_location":
                    row.get(
                        "Object Location", ""
                    ).strip(),

                "object_type":
                    row.get(
                        "Object Type DESC", ""
                    ).strip(),

                "component_name":
                    row.get(
                        "Component Object Name", ""
                    ).strip(),

                "component_guid":
                    component_guid,

                "component_type":
                    row.get(
                        "Component Object Type DESC",
                        ""
                    ).strip(),
            })

    print(
        f"Relaciones cargadas: {len(rows)}"
    )

    return rows
