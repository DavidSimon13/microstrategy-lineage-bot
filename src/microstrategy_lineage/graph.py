from collections import defaultdict, deque

from .resolver import build_object_index


LOGICAL_TABLE_TYPES = {
    "Logical Table",
    "Partition Logical Table",
}

PHYSICAL_TABLE_TYPES = {
    "Database Table",
    "Managed Database Table",
}

TERMINAL_TYPES = {
    "Column",
    "Managed Column",
    "Managed Attribute Form",
    "Attribute Form Category",
}


# Cuando llegamos a una Logical Table no debemos
# regresar indiscriminadamente hacia Attributes/Facts.
#
# Solo continuamos hacia objetos técnicos/físicos.
LOGICAL_ALLOWED_CHILD_TYPES = {
    "Logical Table",
    "Partition Logical Table",
    "Database Table",
    "Managed Database Table",
    "Column",
    "Managed Column",
}


# Una tabla física puede contener columnas o incluso
# relacionarse con otra tabla física.
PHYSICAL_ALLOWED_CHILD_TYPES = {
    "Database Table",
    "Managed Database Table",
    "Column",
    "Managed Column",
}


def build_adjacency(rows):
    """
    Construye el grafo:

        Object GUID -> Component Object GUID

    Cada GUID padre puede tener múltiples componentes.
    """

    adjacency = defaultdict(list)

    for row in rows:

        parent_guid = row.get(
            "object_guid", ""
        ).strip()

        child_guid = row.get(
            "component_guid", ""
        ).strip()

        if not parent_guid or not child_guid:
            continue

        adjacency[parent_guid].append({
            "guid": child_guid,
            "name": row.get(
                "component_name", ""
            ).strip(),
            "type": row.get(
                "component_type", ""
            ).strip(),
        })

    return adjacency


def _unique_objects(objects):
    """
    Deduplica objetos por GUID.
    """

    unique = {}

    for obj in objects:

        guid = obj.get("guid")

        if not guid:
            continue

        if guid not in unique:
            unique[guid] = obj

    return list(unique.values())


def traverse_lineage(rows, start_guid):
    """
    Recorre las dependencias descendientes de un objeto.

    Reglas principales:

    - GUID es la identidad principal.
    - Se permiten relaciones entre objetos del mismo nivel.
    - Se permiten saltos de nivel.
    - Se evitan ciclos.
    - Las Logical Tables se recorren únicamente
      hacia dependencias técnicas/físicas.
    - Column y Managed Column son terminales.

    Retorna:

        start_object
        edges
        logical_tables
        physical_tables
        terminal_objects
        ignored_edges
        visited_guids
    """

    if not start_guid:
        raise ValueError(
            "Debe proporcionar un GUID inicial."
        )

    start_guid = start_guid.strip()

    object_index = build_object_index(rows)
    adjacency = build_adjacency(rows)

    if start_guid not in object_index:
        raise ValueError(
            f"No se encontró el GUID: {start_guid}"
        )

    start_object = object_index[start_guid]

    queue = deque()

    queue.append({
        "guid": start_guid,
        "depth": 0,
    })

    expanded_guids = set()
    visited_guids = set()
    visited_edges = set()

    edges = []
    ignored_edges = []

    logical_tables = []
    physical_tables = []
    terminal_objects = []

    while queue:

        current = queue.popleft()

        parent_guid = current["guid"]
        depth = current["depth"]

        if parent_guid in expanded_guids:
            continue

        expanded_guids.add(parent_guid)
        visited_guids.add(parent_guid)

        parent_object = object_index.get(
            parent_guid,
            {
                "guid": parent_guid,
                "name": "",
                "type": "",
                "location": "",
            }
        )

        parent_type = parent_object.get(
            "type", ""
        )

        children = adjacency.get(
            parent_guid,
            []
        )

        for child in children:

            child_guid = child["guid"]
            child_type = child["type"]

            edge_key = (
                parent_guid,
                child_guid,
            )

            if edge_key in visited_edges:
                continue

            visited_edges.add(edge_key)

            child_object = object_index.get(
                child_guid,
                {
                    "guid": child_guid,
                    "name": child.get(
                        "name", ""
                    ),
                    "type": child_type,
                    "location": "",
                }
            )

            # ---------------------------------
            # Regla especial para Logical Table
            # ---------------------------------

            if parent_type in LOGICAL_TABLE_TYPES:

                if (
                    child_type
                    not in LOGICAL_ALLOWED_CHILD_TYPES
                ):

                    ignored_edges.append({
                        "parent_guid":
                            parent_guid,
                        "parent_name":
                            parent_object.get(
                                "name", ""
                            ),
                        "parent_type":
                            parent_type,
                        "child_guid":
                            child_guid,
                        "child_name":
                            child_object.get(
                                "name", ""
                            ),
                        "child_type":
                            child_type,
                        "reason":
                            "Evitar expansión "
                            "semántica desde "
                            "Logical Table",
                    })

                    continue

            # ---------------------------------
            # Regla para tablas físicas
            # ---------------------------------

            if parent_type in PHYSICAL_TABLE_TYPES:

                if (
                    child_type
                    not in PHYSICAL_ALLOWED_CHILD_TYPES
                ):

                    continue

            # ---------------------------------
            # Registrar relación válida
            # ---------------------------------

            edges.append({
                "parent_guid":
                    parent_guid,
                "parent_name":
                    parent_object.get(
                        "name", ""
                    ),
                "parent_type":
                    parent_type,

                "child_guid":
                    child_guid,
                "child_name":
                    child_object.get(
                        "name", ""
                    ),
                "child_type":
                    child_type,

                "depth":
                    depth + 1,
            })

            visited_guids.add(
                child_guid
            )

            # ---------------------------------
            # Clasificación técnica
            # ---------------------------------

            if child_type in LOGICAL_TABLE_TYPES:

                logical_tables.append(
                    child_object
                )

            if child_type in PHYSICAL_TABLE_TYPES:

                physical_tables.append(
                    child_object
                )

            if child_type in TERMINAL_TYPES:

                terminal_objects.append(
                    child_object
                )

                # Los terminales no continúan.
                continue

            # ---------------------------------
            # Continuar recorrido
            # ---------------------------------

            if child_guid not in expanded_guids:

                queue.append({
                    "guid": child_guid,
                    "depth": depth + 1,
                })

    return {
        "start_object":
            start_object,

        "edges":
            edges,

        "logical_tables":
            _unique_objects(
                logical_tables
            ),

        "physical_tables":
            _unique_objects(
                physical_tables
            ),

        "terminal_objects":
            _unique_objects(
                terminal_objects
            ),

        "ignored_edges":
            ignored_edges,

        "visited_guids":
            sorted(visited_guids),
    }
