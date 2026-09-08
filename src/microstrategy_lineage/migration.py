from collections import defaultdict, deque


def _build_edge_adjacency(edges):
    """
    Construye un índice:

        parent_guid -> edges hijas
    """

    adjacency = defaultdict(list)

    for edge in edges:
        parent_guid = edge.get("parent_guid")

        if parent_guid:
            adjacency[parent_guid].append(edge)

    return adjacency


def _is_semantic_lateral_edge(edge):
    """
    Detecta relaciones laterales N3 -> N3.

    Ejemplos:

        Fact -> Attribute
        Fact -> Fact
        Attribute -> Attribute

    Estas relaciones son importantes para el
    lineage técnico, pero pueden introducir tablas
    físicas que no necesariamente participan en
    el SQL efectivo del reporte.
    """

    return (
        edge.get("parent_level") == "N3"
        and edge.get("child_level") == "N3"
    )


def _reconstruct_path(
    parent_state,
    final_state
):
    """
    Reconstruye una ruta desde el objeto inicial
    hasta un estado alcanzado.
    """

    path = []

    current = final_state

    while current in parent_state:

        previous_state, edge = (
            parent_state[current]
        )

        path.append(edge)
        current = previous_state

    path.reverse()

    return path


def analyze_reachability(
    classified_result
):
    """
    Recorre nuevamente el lineage ya clasificado.

    El estado utilizado es:

        (GUID, semantic_lateral)

    semantic_lateral=False:
        Existe una ruta sin N3 -> N3.

    semantic_lateral=True:
        La ruta atravesó al menos una
        relación semántica lateral N3 -> N3.
    """

    start_object = classified_result[
        "start_object"
    ]

    start_guid = start_object["guid"]

    edges = classified_result.get(
        "edges", []
    )

    adjacency = _build_edge_adjacency(
        edges
    )

    start_state = (
        start_guid,
        False
    )

    queue = deque([start_state])

    visited_states = {
        start_state
    }

    parent_state = {}

    while queue:

        current_guid, lateral = (
            queue.popleft()
        )

        for edge in adjacency.get(
            current_guid, []
        ):

            child_guid = edge[
                "child_guid"
            ]

            child_lateral = (
                lateral
                or _is_semantic_lateral_edge(
                    edge
                )
            )

            child_state = (
                child_guid,
                child_lateral
            )

            if child_state in visited_states:
                continue

            visited_states.add(
                child_state
            )

            parent_state[
                child_state
            ] = (
                (
                    current_guid,
                    lateral
                ),
                edge
            )

            queue.append(
                child_state
            )

    return {
        "visited_states":
            visited_states,
        "parent_state":
            parent_state,
    }


def classify_physical_tables(
    classified_result
):
    """
    Clasifica las tablas físicas encontradas.

    Regla V1:

    MIGRATE
        Existe al menos una ruta hacia la tabla
        que NO atraviesa una relación lateral
        N3 -> N3.

    VALIDATE_SQL
        La tabla únicamente puede alcanzarse
        mediante rutas que contienen al menos
        una relación N3 -> N3.

    Esto evita inflar el scope AWS por relaciones
    semánticas laterales de Facts o Attributes.
    """

    reachability = analyze_reachability(
        classified_result
    )

    visited_states = reachability[
        "visited_states"
    ]

    parent_state = reachability[
        "parent_state"
    ]

    results = []

    physical_tables = (
        classified_result.get(
            "physical_tables", []
        )
    )

    for table in physical_tables:

        guid = table["guid"]

        clean_state = (
            guid,
            False
        )

        lateral_state = (
            guid,
            True
        )

        if clean_state in visited_states:

            status = "MIGRATE"

            reason = (
                "Existe una ruta descendente "
                "hasta la tabla física sin "
                "expansión semántica lateral "
                "N3 -> N3."
            )

            evidence_path = (
                _reconstruct_path(
                    parent_state,
                    clean_state
                )
            )

        elif lateral_state in visited_states:

            status = "VALIDATE_SQL"

            reason = (
                "La tabla física se alcanza "
                "únicamente mediante una "
                "relación semántica lateral "
                "N3 -> N3. Validar el SQL "
                "real antes de incluirla en "
                "el scope AWS."
            )

            evidence_path = (
                _reconstruct_path(
                    parent_state,
                    lateral_state
                )
            )

        else:

            status = "AUXILIARY"

            reason = (
                "La tabla aparece en el "
                "resultado técnico pero no "
                "se pudo reconstruir una "
                "ruta válida desde el objeto "
                "inicial."
            )

            evidence_path = []

        results.append({
            "guid":
                guid,

            "name":
                table.get(
                    "name", ""
                ),

            "type":
                table.get(
                    "type", ""
                ),

            "level":
                table.get(
                    "level", "N1"
                ),

            "migration_status":
                status,

            "reason":
                reason,

            "evidence_path":
                evidence_path,
        })

    return results


def build_migration_summary(
    classified_result
):
    """
    Genera el resumen final para migración AWS.
    """

    tables = classify_physical_tables(
        classified_result
    )

    migrate = [
        table
        for table in tables
        if table[
            "migration_status"
        ] == "MIGRATE"
    ]

    validate_sql = [
        table
        for table in tables
        if table[
            "migration_status"
        ] == "VALIDATE_SQL"
    ]

    auxiliary = [
        table
        for table in tables
        if table[
            "migration_status"
        ] == "AUXILIARY"
    ]

    return {
        "physical_tables":
            tables,

        "migrate":
            migrate,

        "validate_sql":
            validate_sql,

        "auxiliary":
            auxiliary,

        "physical_table_count":
            len(tables),

        "migrate_count":
            len(migrate),

        "validate_sql_count":
            len(validate_sql),

        "auxiliary_count":
            len(auxiliary),
    }
