import unicodedata


def _normalize_text(value):
    """
    Normaliza texto para realizar comparaciones
    robustas ignorando mayúsculas y acentos.
    """

    if not value:
        return ""

    value = value.casefold()

    normalized = unicodedata.normalize(
        "NFKD",
        value
    )

    return "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )


def _is_public_object(location):
    """
    Determina si un objeto está ubicado dentro
    de la zona pública del proyecto.
    """

    normalized_location = _normalize_text(
        location
    ).replace("\\", "/")

    public_markers = (
        "/objetos publicos/",
        "/public objects/",
    )

    return any(
        marker in normalized_location
        for marker in public_markers
    )


def build_object_index(rows):
    """
    Construye un índice de objetos por GUID.

    Considera tanto:
    - Object GUID
    - Component Object GUID

    Un objeto de Platform Analytics puede
    aparecer como padre o como componente.
    """

    objects = {}

    for row in rows:

        # -----------------------------
        # Object
        # -----------------------------

        object_guid = row.get(
            "object_guid", ""
        ).strip()

        if object_guid:

            current = objects.get(
                object_guid,
                {}
            )

            objects[object_guid] = {
                "guid":
                    object_guid,

                "name":
                    row.get("object_name")
                    or current.get(
                        "name", ""
                    ),

                "type":
                    row.get("object_type")
                    or current.get(
                        "type", ""
                    ),

                "location":
                    row.get(
                        "object_location"
                    )
                    or current.get(
                        "location", ""
                    ),
            }

        # -----------------------------
        # Component Object
        # -----------------------------

        component_guid = row.get(
            "component_guid", ""
        ).strip()

        if component_guid:

            current = objects.get(
                component_guid,
                {}
            )

            objects[component_guid] = {
                "guid":
                    component_guid,

                "name":
                    current.get(
                        "name"
                    )
                    or row.get(
                        "component_name", ""
                    ),

                "type":
                    current.get(
                        "type"
                    )
                    or row.get(
                        "component_type", ""
                    ),

                "location":
                    current.get(
                        "location", ""
                    ),
            }

    return objects


def resolve_object(rows, query):
    """
    Localiza un objeto por GUID o nombre.

    Prioridad:

    1. GUID exacto.
    2. Nombre exacto.
    3. Si hay duplicados, priorizar un único
       objeto ubicado en Objetos públicos.
    4. Si sigue existiendo ambigüedad,
       solicitar GUID.
    """

    if not query:
        raise ValueError(
            "Debe proporcionar un nombre o GUID."
        )

    query = query.strip()

    objects = build_object_index(rows)

    # =================================
    # 1. Buscar por GUID
    # =================================

    query_guid = query.upper()

    for guid, obj in objects.items():

        if guid.upper() == query_guid:
            return obj

    # =================================
    # 2. Buscar por nombre
    # =================================

    query_name = _normalize_text(
        query
    )

    matches = []

    for obj in objects.values():

        object_name = _normalize_text(
            obj.get("name", "")
        )

        if object_name == query_name:
            matches.append(obj)

    # =================================
    # Un único resultado
    # =================================

    if len(matches) == 1:
        return matches[0]

    # =================================
    # Múltiples resultados
    # =================================

    if len(matches) > 1:

        public_matches = [
            obj
            for obj in matches
            if _is_public_object(
                obj.get(
                    "location", ""
                )
            )
        ]

        # -----------------------------
        # Un único objeto público
        # -----------------------------

        if len(public_matches) == 1:

            selected = public_matches[0]

            print()
            print(
                "AVISO: se encontraron "
                f"{len(matches)} objetos "
                "con el mismo nombre."
            )

            print(
                "Se seleccionó automáticamente "
                "el objeto ubicado en "
                "Objetos públicos:"
            )

            print(
                f"{selected['name']} | "
                f"{selected['guid']} | "
                f"{selected['type']} | "
                f"{selected['location']}"
            )

            print()

            return selected

        # -----------------------------
        # Sigue existiendo ambigüedad
        # -----------------------------

        details = []

        for obj in matches:

            scope = (
                "PUBLIC"
                if _is_public_object(
                    obj.get(
                        "location", ""
                    )
                )
                else "OTHER"
            )

            details.append(
                f"[{scope}] "
                f"{obj['name']} | "
                f"{obj['guid']} | "
                f"{obj['type']} | "
                f"{obj['location']}"
            )

        raise ValueError(
            "Se encontraron varios objetos "
            "con el mismo nombre y no fue "
            "posible seleccionar uno "
            "automáticamente.\n\n"
            + "\n".join(details)
            + "\n\nUtilice el GUID "
              "para desambiguar."
        )

    # =================================
    # Ningún resultado
    # =================================

    raise ValueError(
        f"No se encontró el objeto: {query}"
    )
