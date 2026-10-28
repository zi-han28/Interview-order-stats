# AI Notes

## Tools used
- **Claude Code (agent mode)** — used to scaffold `order_stats.py`, generate the
  first draft of `tests/test_order_stats.py`, and create `run.sh`. I ran it in the
  repo root so it could read `README.md` and `data/orders.csv` directly.
- **Claude (chat)** — used for a second-opinion review of edge cases (line
  numbering, repeated headers, rounding) before I finalised the tests.

  - **DeepSeek (chat)** — used as a second-opinion reviewer after the first draft
  was working. I pasted the full contents of `order_stats.py` and
  `tests/test_order_stats.py` and asked it to look for correctness bugs, spec
  violations, and missing test coverage. It did not generate the initial code;
  its role was review and critique only.

## Key prompts
1. > "Read README.md and data/orders.csv. Write a Python 3.10+ script
   > order_stats.py that takes <input_csv> <start_date> <end_date> <output_json>
   > and emits the JSON in the README. Only status=completed counts; date range
   > inclusive; names merge case/whitespace-insensitively; revenue = sum(qty *
   > unit_price) rounded to 2 dp; sort by revenue desc then item_name asc. Bad
   > rows that *would* count go into `skipped` with the physical line number.
   > Standard library only."
   Outcome: produced a working first draft. It used `float` for revenue — see
   rejection below.

2. > "The CSV can contain repeated header rows (concatenated exports) and quoted
   > fields with embedded newlines. Make sure `line` in `skipped` is still the
   > physical line number, not the record index."
   Outcome: it switched to `csv.reader` + `reader.line_num` to track physical
   lines and skip records whose normalised fields equal the header. Kept.

3. > "Write unittest tests covering: completed-only, inclusive dates, name
   > merging, exact-decimal rounding (3 × 0.335 should be 1.01), sort order,
   > skipped line numbers, repeated headers, and quoted/multiline fields."
   Outcome: generated the bulk of `ReportTest`. I added
   `test_columns_matched_by_name_not_position` myself because the AI's version
   assumed fixed column order.

## How I used DeepSeek for code review

After the implementation was working, I pasted `order_stats.py` and
`tests/test_order_stats.py` into DeepSeek (chat) and asked it to check the code
against the README spec and flag (a) business-rule violations, (b) inputs that
would crash, and (c) untested rules — explicitly *not* to rewrite anything.

Prompt: "Review this against the spec in README.md. List findings with
file/line references; don't rewrite the code."

Outcome: it flagged that an empty CSV exits non-zero (acceptable — a file with no
header isn't a valid export; I left a comment documenting this), and that a row
with the wrong column count was skipped but untested (I added
`test_wrong_column_count_is_skipped`). It also suggested Unicode-normalising
item names, which I rejected as scope creep beyond the spec's
case/whitespace rule. No logic changes were needed.

## Where I rejected AI output
**Case 1 — float vs Decimal for revenue**
- AI proposed: accumulate revenue as Python `float` and round with
  `round(revenue, 2)`.
- Why I rejected it: `3 × 0.335 = 1.005`, which `float` represents as
  `1.00499999...`, so `round()` gives `1.0` instead of `1.01`. The spec says
  "rounded to 2 decimal places", and half-up on the exact decimal is the
  defensible reading.
- What I did instead: sum with `Decimal` and quantise with
  `ROUND_HALF_UP` (`CENTS = Decimal("0.01")`), only converting to `float` at
  JSON-serialisation time.
- Evidence: `test_revenue_rounding_uses_exact_decimal` asserts `1.01`.

**Case 2 — skipped rows for out-of-range/cancelled data**
- AI proposed: append *every* malformed row to `skipped`, including rows that
  are `cancelled` or outside the date range.
- Why I rejected it: the spec says a row goes into `skipped` only if it "should
  be counted but cannot be processed". A cancelled row is never counted, so
  reporting it as skipped would be noise and would break the line-number
  expectations for real skips.
- What I did instead: apply the `status == completed` and date-range filters
  *before* validation, so only rows that pass the filters but fail parsing are
  reported.
- Evidence: `test_bad_rows_not_counted_anyway_are_ignored`.

**Case 3 — column lookup by position**
- AI proposed: `row[0]`, `row[1]`, … for each field.
- Why I rejected it: the README says the program will be run against other CSVs
  "with the same columns", not necessarily in the same order. Positional access
  would silently mis-read them.
- What I did instead: build a `{name: index}` map from the header and look up by
  name.
- Evidence: `test_columns_matched_by_name_not_position`.

## Rules files / prompt templates
- No `CLAUDE.md`, `.cursorrules`, custom commands, skills, or prompt templates
  were used. All interaction was ad-hoc chat/agent prompts.