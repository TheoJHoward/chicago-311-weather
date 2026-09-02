# Notes — data as found

Facts recorded during the data pull and the study run.

## Realized window

The weather archive returned a non-null `temperature_2m_max` for every day
requested, including the final day, so the window ends at the registration's
upper bound rather than earlier.

- Window: 2019-01-01 through 2026-08-31, 2800 days, no gaps.
- Test set: the final 365 days, 2025-09-01 through 2026-08-31.
- Training set: 2019-01-01 through 2025-08-31 before lag-dropping.
- `data/weather_daily.csv`: 2800 rows. Nulls within the window, per variable:
  0 for all seven variables. Trailing null days trimmed: 0.

## 311 pull

- 92 calendar months, 2019-01 through 2026-08, one request each.
- Every month succeeded under the primary strategy (grouped count by
  `sr_type` and `date_trunc_ymd(created_date)`). No month required the
  `sr_type IN (...)` fallback, so all types were retrieved, not only the
  mapped ones.
- No month returned a full 50000-row page, so no month required paging.
- `data/311_daily_by_type.csv`: 212376 rows.
- `data/study_daily.csv`: 2800 rows, one per day in the window, no missing days.
- Rows discarded for falling outside the window: 0.
- Every day in the window carries at least one 311 record of some type.
- All-time totals across the whole dataset (no date filter, `data/sr_types.csv`):
  110 distinct `sr_type` values, 14,572,249 records.

## Per-type coverage does not start on the same day

The mapped request types do not all appear from the first day of the window.
First and last day each mapped type appears within the window, with its count
in the window:

| sr_type | first day | last day | count in window |
|---|---|---|---|
| Abandoned Vehicle Complaint | 2019-01-01 | 2026-08-31 | 330,131 |
| Alley Pothole Complaint | 2019-01-02 | 2026-08-31 | 55,163 |
| Graffiti Removal Request | 2019-01-03 | 2026-08-31 | 686,184 |
| Pothole in Street Complaint | 2019-01-01 | 2026-08-31 | 290,697 |
| Rodent Baiting/Rat Complaint | 2019-02-25 | 2026-08-31 | 364,495 |
| Tree Debris Clean-Up Request | 2019-01-03 | 2026-08-31 | 211,639 |
| Water in Basement Complaint | 2019-01-01 | 2026-08-31 | 66,764 |

The rodent type carries no record at all before 2019-02-25. Its 55 zero-count
days are exactly the 55 days from 2019-01-01 to 2019-02-24; it has no
zero-count day after that. All of these days fall in the training period.

## Zero-count days by category

| Category | Zero-count days | Before 2019-03-01 | On or after 2019-03-01 |
|---|---|---|---|
| pothole | 0 | 0 | 0 |
| rodent | 55 | 55 | 0 |
| basement | 75 | 36 | 39 |
| graffiti | 49 | 49 | 0 |
| tree debris | 48 | 38 | 10 |
| abandoned vehicle | 0 | 0 | 0 |

Basement zero-count days are scattered across the whole window (last one
2026-06-28). Tree-debris zero-count days after 2019-03-01 are 2020-02-29,
2020-12-25, 2021-02-05, 2021-02-13, 2021-02-17, 2021-02-20, 2021-02-21,
2022-01-30, 2024-12-25 and 2025-01-01.

## Category totals within the window

| Category | Total | Mean per day | Largest single day |
|---|---|---|---|
| pothole | 345,860 | 123.5 | 615 |
| rodent | 364,495 | 130.2 | 534 |
| basement | 66,764 | 23.8 | 3,653 (2025-08-17) |
| graffiti | 686,184 | 245.1 | 1,314 |
| tree debris | 211,639 | 75.6 | 2,321 (2020-08-11) |
| abandoned vehicle | 330,131 | 117.9 | 664 |

The five largest basement days are 2025-08-17 (3,653), 2023-07-05 (2,004),
2025-08-18 (1,725), 2025-08-19 (1,380) and 2023-07-03 (1,353). Three of the
five, including the largest, fall inside the test year.

The five largest tree-debris days are 2020-08-11 (2,321), 2024-07-16 (2,239),
2026-06-11 (1,784), 2026-06-13 (1,693) and 2020-08-10 (1,671).

## Nothing else

The absence claims above ("no gaps", "no paging", "no fallback", "no missing
days", "0 rows discarded") were each checked over the full population of the
pull: all 2800 days of the window and all 92 monthly requests. No other data
problem was observed within that population.

## Correction — 2026-09-02

The sentence above that reads "Three of the five, including the largest, fall
inside the test year" is false. It is left in place; this section supersedes it.

The five largest basement days are 2025-08-17 (3,653), 2023-07-05 (2,004),
2025-08-18 (1,725), 2025-08-19 (1,380) and 2023-07-03 (1,353). The test year
begins 2025-09-01.

**Zero of the five fall inside the test year.** Three of them — 2025-08-17,
2025-08-18 and 2025-08-19 — fall in the last fifteen days of the training
period, which ends 2025-08-31. The other two fall in July 2023, also training.

The error was in the note only. No number in `results/` depended on it, and the
split itself is asserted by `test_split_no_overlap`.
