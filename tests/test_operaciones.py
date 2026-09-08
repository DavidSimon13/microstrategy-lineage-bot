import unittest

from src.microstrategy_lineage.loader import load_platform_analytics
from src.microstrategy_lineage.resolver import resolve_object
from src.microstrategy_lineage.graph import traverse_lineage
from src.microstrategy_lineage.classifier import classify_lineage
from src.microstrategy_lineage.migration import build_migration_summary


DATASET = "data/Analisis de objetos_Operaciones.csv"

OBJECT_GUID = "F4046D5D41493B9F435E9AB9124939C0"


class TestOperacionesLineage(unittest.TestCase):

    def test_rpt_acumulado_mensual(self):

        rows = load_platform_analytics(
            DATASET
        )

        obj = resolve_object(
            rows,
            OBJECT_GUID
        )

        self.assertEqual(
            obj["name"],
            "RPT - Acumulado Mensual"
        )

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

        self.assertEqual(
            classified["start_object"]["level"],
            "N5"
        )

        self.assertEqual(
            summary["physical_table_count"],
            4
        )

        self.assertEqual(
            summary["migrate_count"],
            2
        )

        self.assertEqual(
            summary["validate_sql_count"],
            2
        )

        migrate_names = {
            table["name"]
            for table in summary["migrate"]
        }

        validate_names = {
            table["name"]
            for table in summary["validate_sql"]
        }

        self.assertEqual(
            migrate_names,
            {
                "GORAPR.TDM501_CAT_CORRESP",
                "GORAPR.TDM503_OPR_CRR_RSM",
            }
        )

        self.assertEqual(
            validate_names,
            {
                "GORAPR.TDM502_GP_CD_CRRSP",
                "GORAPR.TDM156_TIEMPO",
            }
        )


if __name__ == "__main__":
    unittest.main()
