# Order Stats — AI-assisted coding exercise

Time limit: **25 minutes**. You are expected to use AI coding tools (Claude Code, Cursor, Copilot, ChatGPT, etc.) the way you normally do. We are evaluating both the result and how you work with AI.

## Task

`data/orders.csv` is a raw export from a restaurant POS system. Write a program that, for a given date range, reports how many of each dish were sold and the revenue for each dish.

## Interface (must follow exactly)

Implement `run.sh` so this command works from the repo root:

```bash
./run.sh <input_csv> <start_date> <end_date> <output_json>
# example
./run.sh data/orders.csv 2026-10-01 2026-10-31 output/result.json
```

- `start_date` and `end_date` are `YYYY-MM-DD`.
- Your program will also be run against **other CSV files with the same columns**, so do not hard-code anything from `data/orders.csv`.

## Output format

```json
{
  "items": [
    { "item_name": "Seafood Paella", "qty": 6, "revenue": 168.00 }
  ],
  "skipped": [
    { "line": 8, "reason": "missing unit_price" }
  ]
}
```

- `line` is the physical line number in the CSV file. The header is line 1, the first data row is line 2.
- The example values above are for illustration only.

## Running the tests

<!-- this one -->
```bash
python3 -m unittest discover -s tests -v
```

## Business rules

1. Only orders with status `completed` count.
2. The date range is inclusive on both ends.
3. Item names that differ only in letter case or leading/trailing spaces are the same dish. Any one of the spellings may be used in the output.
4. `revenue` = sum of `qty × unit_price`, rounded to 2 decimal places.
5. Sort `items` by `revenue` descending, then by `item_name` ascending.
6. The export is not clean. Your program must not crash on bad rows and must not silently drop data: a row that should be counted but cannot be processed goes into `skipped` with a reason.

## Constraints

- Python 3.10+ or Node.js 20+.
- Standard library only. For tests you may use `unittest`, `pytest` or `node:test`.

## What to submit

1. Your implementation and a working `run.sh`.
2. Tests, plus the command to run them (add it to this README).
3. `AI_NOTES.md`, covering:
   - Which AI tools you used and how (agent mode, chat, autocomplete, etc.).
   - The key prompts you gave.
   - At least one place where you did not accept the AI's output, and why.
   - Any rules files, custom commands, skills or prompt templates you used (`CLAUDE.md`, `.cursorrules`, etc.). Commit them if you have them.
4. Push your work to **your own new public GitHub repository** and send us the link. Please do not open a pull request against this repository.
