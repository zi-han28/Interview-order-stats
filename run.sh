#!/usr/bin/env bash
# Usage: ./run.sh <input_csv> <start_date> <end_date> <output_json>
exec python3 "$(dirname "$0")/order_stats.py" "$@"
