import unittest

from src.microstrategy_lineage.loader import load_platform_analytics
from src.microstrategy_lineage.resolver import resolve_object
from src.microstrategy_lineage.graph import traverse_lineage
from src.microstrategy_lineage.classifier import classify_lineage
from src.microstrategy_lineage.migration import build_migration_summary


DATASET = (
"data/Analisis de objetos_Sistemas y Operaciones.csv"
)

OBJECT_NAME = "TLP509 RAESTREO RECON"

EXPECTED_GUID = (
    "CBC58B2044FF5176F23BD4AB57791102"
)


class TestSistemasOperacionesLineage(
    unittest.TestCase
):

    def test_tlp504_rastreo_public_object(self):

        rows = load_platform_analytics(
            DATASET
        )

        # ---------------------------------
        # Resolver por nombre duplicado
        # ---------------------------------

        obj = resolve_object(
            rows,
            OBJECT_NAME
        )

        self.assertEqual(
            obj["guid"],
            EXPECTED_GUID
        )

        self.assertIn(
            "Objetos públicos",
            obj["location"]
        )

        # ---------------------------------
        # Lineage
        # ---------------------------------

        lineage = traverse_lineage(
            rows,
            obj["guid"]
        )

        classified = classify_lineage(
            lineage
        )

        summary = build_migration_summary(
            classified
        )

        # ---------------------------------
        # Validaciones del objeto
        # ---------------------------------

        self.assertEqual(
            classified["start_object"]["level"],
            "N5"
        )

        self.assertEqual(
            classified["start_object"]["type"],
            "Grid Report"
        )

        # ---------------------------------
        # Logical Table
        # ---------------------------------

        logical_names = {
            table["name"]
            for table in classified[
                "logical_tables"
            ]
        }

        self.assertEqual(
            logical_names,
            {
                "TLP504_FARASTREO(640)"
            }
        )

        # ---------------------------------
        # Physical Table
        # ---------------------------------

        self.assertEqual(
            summary["physical_table_count"],
            1
        )

        self.assertEqual(
            summary["migrate_count"],
            1
        )

        self.assertEqual(
            summary["validate_sql_count"],
            0
        )

        migrate_names = {
            table["name"]
            for table in summary["migrate"]
        }

        self.assertEqual(
            migrate_names,
            {
                "GORAPR.TLP504_FARASTREO"
            }
        )


if __name__ == "__main__":
    unittest.main()
