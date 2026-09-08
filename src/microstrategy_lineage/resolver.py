def build_object_index(rows):
    """
    Construye un índice de objetos por GUID.

    Considera tanto:
    - Object GUID
    - Component Object GUID

    Esto es importante porque en Platform Analytics
    un objeto puede aparecer como padre o como componente.
    """

    objects = {}

    for row in rows:

        # -----------------------------
        # Object
        # -----------------------------
        object_guid = row.get("object_guid", "").strip()

        if object_guid:
            current = objects.get(object_guid, {})

            objects[object_guid] = {
                "guid": object_guid,
                "name": (
                    row.get("object_name")
                    or current.get("name", "")
                ),
                "type": (
                    row.get("object_type")
                    or current.get("type", "")
                ),
                "location": (
                    row.get("object_location")
                    or current.get("location", "")
                ),
            }

        # -----------------------------
        # Component Object
        # -----------------------------
        component_guid = row.get(
            "component_guid", ""
        ).strip()

        if component_guid:

            current = objects.get(component_guid, {})

            objects[component_guid] = {
                "guid": component_guid,
                "name": (
                    current.get("name")
                    or row.get("component_name", "")
                ),
                "type": (
                    current.get("type")
                    or row.get("component_type", "")
                ),
                "location": current.get("location", ""),
            }

    return objects


def resolve_object(rows, query):
    """
    Localiza un objeto por GUID o nombre.

    Prioridad:
    1. GUID exacto
    2. Nombre exacto ignorando mayúsculas/minúsculas

    Si existen varios objetos con el mismo nombre,
    obliga a desambiguar mediante GUID.
    """

    if not query:
        raise ValueError(
            "Debe proporcionar un nombre o GUID."
        )

    query = query.strip()

    objects = build_object_index(rows)

    # --------------------------------
    # 1. Buscar por GUID
    # --------------------------------
    query_guid = query.upper()

    for guid, obj in objects.items():
        if guid.upper() == query_guid:
            return obj

    # --------------------------------
    # 2. Buscar por nombre exacto
    # --------------------------------
    query_name = query.casefold()

    matches = []

    for obj in objects.values():

        name = obj.get("name", "")

        if name.casefold() == query_name:
            matches.append(obj)

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:

        details = []

        for obj in matches:
            details.append(
                f"{obj['name']} | "
                f"{obj['guid']} | "
                f"{obj['type']} | "
                f"{obj['location']}"
            )

        raise ValueError(
            "Se encontraron varios objetos "
            "con el mismo nombre.\n\n"
            + "\n".join(details)
            + "\n\nUtilice el GUID para desambiguar."
        )

    raise ValueError(
        f"No se encontró el objeto: {query}"
    )
