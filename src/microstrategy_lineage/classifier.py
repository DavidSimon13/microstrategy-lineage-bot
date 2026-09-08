from pathlib import Path

import yaml


DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "object_levels.yaml"
)


def load_level_config(config_path=None):
    """
    Carga la configuración arquitectónica N6-N1.
    """

    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"No se encontró la configuración: {config_path}"
        )

    with config_path.open(
        mode="r",
        encoding="utf-8"
    ) as config_file:

        config = yaml.safe_load(config_file)

    if not config:
        raise ValueError(
            "El archivo de configuración está vacío."
        )

    return config


def build_type_level_index(config):
    """
    Genera un índice:

        Object Type -> Nivel arquitectónico

    Ejemplo:

        Grid Report -> N5
        Metric      -> N4
        Attribute   -> N3
        Logical Table -> N2
        Database Table -> N1
    """

    type_index = {}

    levels = config.get("levels", {})

    for level, level_data in levels.items():

        object_types = level_data.get(
            "types", []
        )

        for object_type in object_types:
            type_index[object_type] = level

    return type_index


def get_object_level(object_type, config=None):
    """
    Devuelve el nivel arquitectónico de un
    Object Type.

    Si el tipo no está clasificado devuelve:
        UNKNOWN
    """

    if not object_type:
        return "UNKNOWN"

    if config is None:
        config = load_level_config()

    type_index = build_type_level_index(
        config
    )

    return type_index.get(
        object_type,
        "UNKNOWN"
    )


def classify_object(obj, config=None):
    """
    Agrega el nivel arquitectónico a un objeto.

    Entrada:

        {
            "guid": "...",
            "name": "...",
            "type": "Grid Report"
        }

    Salida:

        {
            "guid": "...",
            "name": "...",
            "type": "Grid Report",
            "level": "N5"
        }
    """

    classified = dict(obj)

    classified["level"] = get_object_level(
        obj.get("type", ""),
        config=config
    )

    return classified


def classify_objects(objects, config=None):
    """
    Clasifica una colección completa de objetos.
    """

    if config is None:
        config = load_level_config()

    return [
        classify_object(
            obj,
            config=config
        )
        for obj in objects
    ]


def classify_lineage(result, config=None):
    """
    Clasifica los principales objetos devueltos
    por traverse_lineage().
    """

    if config is None:
        config = load_level_config()

    classified_result = dict(result)

    classified_result["start_object"] = (
        classify_object(
            result["start_object"],
            config=config
        )
    )

    classified_result["logical_tables"] = (
        classify_objects(
            result.get(
                "logical_tables", []
            ),
            config=config
        )
    )

    classified_result["physical_tables"] = (
        classify_objects(
            result.get(
                "physical_tables", []
            ),
            config=config
        )
    )

    classified_result["terminal_objects"] = (
        classify_objects(
            result.get(
                "terminal_objects", []
            ),
            config=config
        )
    )

    classified_edges = []

    for edge in result.get("edges", []):

        classified_edge = dict(edge)

        classified_edge["parent_level"] = (
            get_object_level(
                edge.get(
                    "parent_type", ""
                ),
                config=config
            )
        )

        classified_edge["child_level"] = (
            get_object_level(
                edge.get(
                    "child_type", ""
                ),
                config=config
            )
        )

        classified_edges.append(
            classified_edge
        )

    classified_result["edges"] = (
        classified_edges
    )

    return classified_result
