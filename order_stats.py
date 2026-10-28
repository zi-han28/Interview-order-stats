"""Per-dish quantity and revenue report for a restaurant POS CSV export.

Usage: python3 order_stats.py <input_csv> <start_date> <end_date> <output_json>
"""

import csv
import json
import sys
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

REQUIRED_COLUMNS = ("order_id", "order_date", "item_name", "qty", "unit_price", "status")
CENTS = Decimal("0.01")


def parse_iso_date(text):
    """Strict YYYY-MM-DD; returns None if the value is anything else."""
    text = text.strip()
    if len(text) != 10 or text[4] != "-" or text[7] != "-":
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def parse_qty(text):
    text = text.strip()
    if not text:
        return None, "missing qty"
    try:
        qty = int(text)
    except ValueError:
        return None, f"invalid qty: {text!r}"
    if qty <= 0:
        return None, f"invalid qty: {text!r}"
    return qty, None


def parse_price(text):
    text = text.strip()
    if not text:
        return None, "missing unit_price"
    try:
        price = Decimal(text)
    except InvalidOperation:
        return None, f"invalid unit_price: {text!r}"
    if not price.is_finite() or price < 0:
        return None, f"invalid unit_price: {text!r}"
    return price, None


def build_report(csv_path, start, end):
    items = {}  # normalized name -> {"item_name", "qty", "revenue"}
    skipped = []

    with open(csv_path, newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        line = 1  # physical line where the next record starts
        header = None
        columns = None

        for record in reader:
            record_line = line
            line = reader.line_num + 1

            if not record or all(not field.strip() for field in record):
                continue  # blank line, nothing to count

            normalized = [field.strip().lower() for field in record]

            if header is None:
                header = normalized
                missing = [c for c in REQUIRED_COLUMNS if c not in header]
                if missing:
                    raise ValueError(f"CSV header is missing columns: {', '.join(missing)}")
                columns = {name: header.index(name) for name in REQUIRED_COLUMNS}
                continue

            if normalized == header:
                continue  # header repeated mid-file (e.g. concatenated exports)

            if len(record) != len(header):
                skipped.append({
                    "line": record_line,
                    "reason": f"expected {len(header)} columns, got {len(record)}",
                })
                continue

            def field(name):
                return record[columns[name]]

            if field("status").strip().lower() != "completed":
                continue

            order_date = parse_iso_date(field("order_date"))
            if order_date is None:
                raw = field("order_date").strip()
                reason = "missing order_date" if not raw else f"invalid order_date: {raw!r}"
                skipped.append({"line": record_line, "reason": reason})
                continue
            if not start <= order_date <= end:
                continue

            name = field("item_name").strip()
            if not name:
                skipped.append({"line": record_line, "reason": "missing item_name"})
                continue

            qty, error = parse_qty(field("qty"))
            if error is None:
                price, error = parse_price(field("unit_price"))
            if error is not None:
                skipped.append({"line": record_line, "reason": error})
                continue

            entry = items.setdefault(name.lower(), {"item_name": name, "qty": 0, "revenue": Decimal(0)})
            entry["qty"] += qty
            entry["revenue"] += qty * price

    result = [
        {
            "item_name": e["item_name"],
            "qty": e["qty"],
            "revenue": e["revenue"].quantize(CENTS, rounding=ROUND_HALF_UP),
        }
        for e in items.values()
    ]
    result.sort(key=lambda e: (-e["revenue"], e["item_name"]))
    for e in result:
        e["revenue"] = float(e["revenue"])
    return {"items": result, "skipped": skipped}


def main(argv):
    if len(argv) != 4:
        print("Usage: run.sh <input_csv> <start_date> <end_date> <output_json>", file=sys.stderr)
        return 2
    csv_path, start_text, end_text, output_path = argv

    start, end = parse_iso_date(start_text), parse_iso_date(end_text)
    if start is None or end is None:
        print("start_date and end_date must be YYYY-MM-DD", file=sys.stderr)
        return 2
    if start > end:
        print("start_date must not be after end_date", file=sys.stderr)
        return 2

    try:
        report = build_report(csv_path, start, end)
    except (OSError, ValueError, csv.Error) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
