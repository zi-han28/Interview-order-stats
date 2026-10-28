# Workspace Structure

Files listed in .gitignore will be excluded.

## Configuration Files

## File Structure

- 📄 .gitignore
- 📄 README.md
- 📁 data/
  - 📄 orders.csv
- 📄 order_stats.py
  - Imports:
    - import csv
    - import json
    - import sys
    - import datetime.date
    - import decimal.Decimal
    - import decimal.InvalidOperation
    - import decimal.ROUND_HALF_UP
    - import pathlib.Path
  - Functions:
    - parse_iso_date
    - parse_qty
    - parse_price
    - build_report
    - main
- 📁 output/
  - 📄 .gitkeep
  - 📄 result.json
- 📄 run.sh
- 📁 tests/
  - 📄 test_order_stats.py
    - Imports:
      - import json
      - import subprocess
      - import sys
      - import tempfile
      - import unittest
      - import datetime.date
      - import pathlib.Path
    - Classes:
      - ReportTest
      - CliTest
    - Methods:
      - setUp
      - report
      - test_only_completed_orders_count
      - test_date_range_is_inclusive
      - test_names_merge_ignoring_case_and_whitespace
      - test_revenue_rounding_uses_exact_decimal
      - test_sort_by_revenue_desc_then_name_asc
      - test_bad_rows_are_skipped_with_physical_line_numbers
      - test_bad_rows_not_counted_anyway_are_ignored
      - test_repeated_header_and_blank_lines_are_ignored
      - test_quoted_fields_and_multiline_keep_line_numbers
      - test_columns_matched_by_name_not_position
      - test_sample_file_end_to_end
      - test_invalid_arguments_exit_nonzero
