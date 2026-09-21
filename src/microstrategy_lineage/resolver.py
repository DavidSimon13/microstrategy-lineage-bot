import difflib
import unicodedata


class ObjectResolutionError(Exception):
    """
    Error funcional al intentar resolver
    un objeto de MicroStrategy.

    Estos errores NO representan fallas
    técnicas del Robot.
    """
    pass


class ObjectNotFoundError(
    ObjectResolutionError
):
    """
    El objeto solicitado no existe
    dentro del dataset analizado.
    """
    pass


class AmbiguousObjectError(
    ObjectResolutionError
):
    """
    Existen varios objetos candidatos
    y no es seguro seleccionar uno.
    """
    pass


class InvalidObjectQueryError(
    ObjectResolutionError
):
    """
    La búsqueda enviada está vacía
    o no es válida.
    """
    pass


def _normalize_text(value):
    """
    Normaliza texto para realizar
    comparaciones robustas:

    - ignora mayúsculas
    - ignora minúsculas
    - ignora acentos
    """

    if not value:
        return ""

    value = str(value).strip()
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
    Determina si un objeto pertenece
    a Objetos públicos.
    """

    normalized_location = (
        _normalize_text(
            location
        )
        .replace("\\", "/")
    )

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
    Construye un índice de objetos
    utilizando GUID como identidad.

    Un objeto puede aparecer como:

    - Object
    - Component Object

    dentro de Platform Analytics.
    """

    objects = {}

    for row in rows:

        # =================================
        # OBJECT
        # =================================

        object_guid = (
            row.get(
                "object_guid",
                ""
            )
            or row.get("object_guid_", "")
            or ""
        ).strip()

        if object_guid:

            current = objects.get(
                object_guid,
                {}
            )

            object_name = (
                row.get(
                    "object_name",
                    ""
                )
                or row.get("name", "")
                or ""
            )

            object_type = (
                row.get(
                    "object_type",
                    ""
                )
                or row.get("object_type_desc", "")
                or row.get("type", "")
                or ""
            )

            object_location = (
                row.get(
                    "object_location",
                    ""
                )
                or row.get("location", "")
                or ""
            )

            objects[object_guid] = {
                "guid":
                    object_guid,

                "name":
                    object_name
                    or current.get(
                        "name",
                        ""
                    ),

                "type":
                    object_type
                    or current.get(
                        "type",
                        ""
                    ),

                "location":
                    object_location
                    or current.get(
                        "location",
                        ""
                    ),
            }

        # =================================
        # COMPONENT OBJECT
        # =================================

        component_guid = (
            row.get(
                "component_guid",
                ""
            )
            or row.get("component_guid_", "")
            or ""
        ).strip()

        if component_guid:

            current = objects.get(
                component_guid,
                {}
            )

            component_name = (
                row.get(
                    "component_name",
                    ""
                )
                or row.get("component_object_name", "")
                or ""
            )

            component_type = (
                row.get(
                    "component_type",
                    ""
                )
                or row.get("component_type_desc", "")
                or row.get("component_object_type", "")
                or ""
            )

            objects[component_guid] = {
                "guid":
                    component_guid,

                "name":
                    current.get(
                        "name",
                        ""
                    )
                    or component_name,

                "type":
                    current.get(
                        "type",
                        ""
                    )
                    or component_type,

                "location":
                    current.get(
                        "location",
                        ""
                    ),
            }

    return objects


def _build_suggestions(
    objects,
    query,
    limit=5
):
    """
    Genera sugerencias cuando el nombre
    solicitado no tiene coincidencia exacta.

    Las sugerencias NO se seleccionan
    automáticamente.
    """

    normalized_query = (
        _normalize_text(
            query
        )
    )

    if not normalized_query:
        return []

    normalized_names = {}

    for obj in objects.values():

        name = obj.get(
            "name",
            ""
        )

        normalized_name = (
            _normalize_text(
                name
            )
        )

        if not normalized_name:
            continue

        normalized_names.setdefault(
            normalized_name,
            []
        )

        normalized_names[
            normalized_name
        ].append(obj)

    matches = difflib.get_close_matches(
        normalized_query,
        list(
            normalized_names.keys()
        ),
        n=limit,
        cutoff=0.45
    )

    suggestions = []

    seen_guids = set()

    for normalized_name in matches:

        for obj in normalized_names.get(
            normalized_name,
            []
        ):

            guid = obj.get(
                "guid",
                ""
            )

            if guid in seen_guids:
                continue

            seen_guids.add(
                guid
            )

            suggestions.append(
                obj
            )

            if len(
                suggestions
            ) >= limit:
                return suggestions

    return suggestions


def _format_candidate(obj):
    """
    Formatea un candidato para mostrarlo
    al usuario.
    """

    scope = (
        "PUBLIC"
        if _is_public_object(
            obj.get(
                "location",
                ""
            )
        )
        else "OTHER"
    )

    return (
        f"[{scope}] "
        f"{obj.get('name', '')} | "
        f"{obj.get('guid', '')} | "
        f"{obj.get('type', '')} | "
        f"{obj.get('location', '')}"
    )


def resolve_object(
    rows,
    query
):
    """
    Localiza un objeto por GUID o nombre.

    Reglas:

    1. GUID exacto.
    2. Nombre exacto normalizado.
    3. Si existen duplicados:
        priorizar un único objeto público.
    4. Si siguen existiendo varios:
        NEEDS_INPUT.
    5. Si no existe:
        ofrecer sugerencias sin adivinar.
    """

    if query is None:

        raise InvalidObjectQueryError(
            "Debe proporcionar "
            "un nombre o GUID."
        )

    query = str(
        query
    ).strip()

    if not query:

        raise InvalidObjectQueryError(
            "Debe proporcionar "
            "un nombre o GUID."
        )

    objects = build_object_index(
        rows
    )

    # =====================================
    # 1. BÚSQUEDA POR GUID
    # =====================================

    query_guid = query.upper()

    for guid, obj in objects.items():

        if (
            guid.upper()
            == query_guid
        ):
            return obj

    # =====================================
    # 2. BÚSQUEDA POR NOMBRE
    # =====================================

    query_name = (
        _normalize_text(
            query
        )
    )

    matches = []

    for obj in objects.values():

        object_name = (
            _normalize_text(
                obj.get(
                    "name",
                    ""
                )
            )
        )

        if (
            object_name
            == query_name
        ):
            matches.append(
                obj
            )

    # =====================================
    # 3. ÚNICO RESULTADO
    # =====================================

    if len(matches) == 1:

        return matches[0]

    # =====================================
    # 4. RESULTADOS DUPLICADOS
    # =====================================

    if len(matches) > 1:

        public_matches = [
            obj
            for obj in matches
            if _is_public_object(
                obj.get(
                    "location",
                    ""
                )
            )
        ]

        if len(
            public_matches
        ) == 1:

            selected = (
                public_matches[0]
            )

            print()
            print(
                "AVISO: se encontraron "
                f"{len(matches)} objetos "
                "con el mismo nombre."
            )

            print(
                "Se seleccionó automáticamente "
                "el único objeto ubicado en "
                "Objetos públicos:"
            )

            print()

            print(
                _format_candidate(
                    selected
                )
            )

            print()

            return selected

        details = [
            _format_candidate(
                obj
            )
            for obj in matches
        ]

        message = (
            "Se encontraron varios objetos "
            "con el mismo nombre y no es "
            "seguro seleccionar uno "
            "automáticamente.\n\n"
            + "\n".join(
                details
            )
            + "\n\n"
            + "Utilice el GUID del objeto "
              "que desea analizar."
        )

        raise AmbiguousObjectError(
            message
        )

    suggestions = (
        _build_suggestions(
            objects,
            query
        )
    )

    message = (
        f"No se encontró el objeto: {query}"
    )

    if suggestions:

        message += (
            "\n\n"
            "Posibles coincidencias:"
        )

        for index, obj in enumerate(
            suggestions,
            start=1
        ):

            message += (
                "\n\n"
                f"{index}. "
                f"{obj.get('name', '')}"
                "\n"
                f"   GUID: "
                f"{obj.get('guid', '')}"
                "\n"
                f"   Type: "
                f"{obj.get('type', '')}"
                "\n"
                f"   Location: "
                f"{obj.get('location', '')}"
            )

        message += (
            "\n\n"
            "No se seleccionó ninguna "
            "coincidencia automáticamente."
        )

    message += (
        "\n\n"
        "Utilice el nombre exacto "
        "o el GUID."
    )

    raise ObjectNotFoundError(
        message
    )

