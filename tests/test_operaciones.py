import unittest

from src.microstrategy_lineage.loader import load_platform_analytics
from src.microstrategy_lineage.resolver import resolve_object
from src.microstrategy_lineage.graph import traverse_lineage
from src.microstrategy_lineage.classifier import classify_lineage
from src.microstrategy_lineage.migration import build_migration_summary


DATASET = "data/Analisis de objetos_Operaciones.csv"
OBJECT_NAME_HINTS = (
    "RPT - Acumulado Diario",
    "Acumulado Diario",
    "Acumulado",
    "RPT",
)


class TestOperacionesLineage(unittest.TestCase):

    def _find_object_by_name_hint(self, rows):
        for hint in OBJECT_NAME_HINTS:
            for row in rows:
                name = (row.get("object_name", "") or "").strip()
                if name and hint.lower() in name.lower():
                    return row
        return None

    def test_rpt_acumulado_diario(self):

        rows = load_platform_analytics(DATASET)
        row = self._find_object_by_name_hint(rows)

        self.assertIsNotNone(row, "No se encontró el reporte de acumulado diario en el dataset actual.")

        obj = resolve_object(rows, row["object_name"])
        self.assertTrue(obj.get("guid"))
        self.assertTrue(obj.get("name"))
        self.assertTrue(obj.get("location"))

        lineage = traverse_lineage(rows, obj["guid"])
        classified = classify_lineage(lineage)
        summary = build_migration_summary(classified)

        self.assertIn("level", classified["start_object"])
        self.assertGreaterEqual(summary.get("physical_table_count", 0), 0)
        self.assertIsInstance(summary.get("migrate", []), list)
        self.assertIsInstance(summary.get("validate_sql", []), list)

        migrate_names = {
            table["name"]
            for table in summary.get("migrate", [])
            if table.get("name")
        }
        validate_names = {
            table["name"]
            for table in summary.get("validate_sql", [])
            if table.get("name")
        }

        self.assertTrue(migrate_names or validate_names)


if __name__ == "__main__":
    unittest.main()
