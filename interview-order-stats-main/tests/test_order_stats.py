import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from order_stats import build_report  # noqa: E402

HEADER = "order_id,order_date,item_name,qty,unit_price,status\n"


class ReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def report(self, body, start="2026-10-01", end="2026-10-31", header=HEADER):
        path = Path(self.tmp.name) / "orders.csv"
        path.write_text(header + body, encoding="utf-8")
        return build_report(path, date.fromisoformat(start), date.fromisoformat(end))

    def test_only_completed_orders_count(self):
        r = self.report(
            "1,2026-10-01,Soup,1,10.00,completed\n"
            "2,2026-10-01,Soup,5,10.00,cancelled\n"
            "3,2026-10-01,Soup,-1,10.00,refunded\n"
            "4,2026-10-01,Soup,2,10.00, Completed \n"
        )
        self.assertEqual(r["items"], [{"item_name": "Soup", "qty": 3, "revenue": 30.0}])
        self.assertEqual(r["skipped"], [])

    def test_date_range_is_inclusive(self):
        r = self.report(
            "1,2026-09-30,Soup,1,1.00,completed\n"
            "2,2026-10-01,Soup,2,1.00,completed\n"
            "3,2026-10-31,Soup,4,1.00,completed\n"
            "4,2026-11-01,Soup,8,1.00,completed\n"
        )
        self.assertEqual(r["items"][0]["qty"], 6)

    def test_names_merge_ignoring_case_and_whitespace(self):
        r = self.report(
            "1,2026-10-01,Seafood Paella,1,28.00,completed\n"
            "2,2026-10-01,  seafood PAELLA ,2,28.00,completed\n"
        )
        self.assertEqual(len(r["items"]), 1)
        self.assertEqual(r["items"][0]["item_name"].lower(), "seafood paella")
        self.assertEqual(r["items"][0]["qty"], 3)

    def test_revenue_rounding_uses_exact_decimal(self):
        # 3 x 0.335 = 1.005 -> 1.01 with half-up; float math would give 1.0
        r = self.report("1,2026-10-01,Tea,3,0.335,completed\n")
        self.assertEqual(r["items"][0]["revenue"], 1.01)

    def test_sort_by_revenue_desc_then_name_asc(self):
        r = self.report(
            "1,2026-10-01,Beta,1,10.00,completed\n"
            "2,2026-10-01,Alpha,1,10.00,completed\n"
            "3,2026-10-01,Gamma,1,20.00,completed\n"
        )
        self.assertEqual([i["item_name"] for i in r["items"]], ["Gamma", "Alpha", "Beta"])

    def test_bad_rows_are_skipped_with_physical_line_numbers(self):
        r = self.report(
            "1,2026-10-01,Soup,1,,completed\n"          # line 2
            "2,2026/10/04,Soup,1,1.00,completed\n"      # line 3
            "3,2026-10-01,Soup,abc,1.00,completed\n"    # line 4
            "4,2026-10-01,Soup,-2,1.00,completed\n"     # line 5
            "5,2026-10-01,,1,1.00,completed\n"          # line 6
            "6,2026-10-01,Soup,1,x,completed\n"         # line 7
            "7,2026-10-01,Soup,1\n"                     # line 8
            "8,2026-10-01,Soup,1,1.00,completed\n"      # line 9 (valid)
        )
        self.assertEqual(r["items"], [{"item_name": "Soup", "qty": 1, "revenue": 1.0}])
        self.assertEqual([s["line"] for s in r["skipped"]], [2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(r["skipped"][0]["reason"], "missing unit_price")

    def test_bad_rows_not_counted_anyway_are_ignored(self):
        r = self.report(
            "1,2026-10-01,Soup,1,,cancelled\n"
            "2,2026-11-05,Soup,1,,completed\n"
        )
        self.assertEqual(r, {"items": [], "skipped": []})

    def test_repeated_header_and_blank_lines_are_ignored(self):
        r = self.report(
            "1,2026-10-01,Soup,1,1.00,completed\n"
            "\n"
            + HEADER +
            "2,2026-10-01,Soup,1,,completed\n"  # line 5
        )
        self.assertEqual(r["items"][0]["qty"], 1)
        self.assertEqual(r["skipped"], [{"line": 5, "reason": "missing unit_price"}])

    def test_quoted_fields_and_multiline_keep_line_numbers(self):
        r = self.report(
            '1,2026-10-01,"Fish, Chips",1,5.00,completed\n'   # line 2
            '2,2026-10-01,"Odd\nName",1,,completed\n'         # lines 3-4
            "3,2026-10-01,Soup,1,,completed\n"                # line 5
        )
        self.assertEqual(r["items"][0]["item_name"], "Fish, Chips")
        self.assertEqual([s["line"] for s in r["skipped"]], [3, 5])

    def test_columns_matched_by_name_not_position(self):
        r = self.report(
            "completed,5.00,2,Soup,2026-10-01,1\n",
            header="status,unit_price,qty,item_name,order_date,order_id\n",
        )
        self.assertEqual(r["items"], [{"item_name": "Soup", "qty": 2, "revenue": 10.0}])


class CliTest(unittest.TestCase):
    def test_sample_file_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "nested" / "result.json"
            subprocess.run(
                [str(ROOT / "run.sh"), str(ROOT / "data/orders.csv"), "2026-10-01", "2026-10-31", str(out)],
                check=True,
            )
            report = json.loads(out.read_text())
        self.assertEqual(report["items"][0], {"item_name": "Seafood Paella", "qty": 6, "revenue": 168.0})
        self.assertIn({"line": 8, "reason": "missing unit_price"}, report["skipped"])

    def test_invalid_arguments_exit_nonzero(self):
        result = subprocess.run(
            [str(ROOT / "run.sh"), "data/orders.csv", "2026/10/01", "2026-10-31", "out.json"],
            cwd=ROOT, capture_output=True,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
