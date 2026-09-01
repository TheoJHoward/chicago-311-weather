# chicago-311-weather

Calendar-blind: can a model learn Chicago's seasonal 311 complaint calendar from daily weather alone, without ever being given the date?

Status: complete. The study was registered before any date-level outcome data was retrieved, the data were pulled, the positive controls passed, and the study was scored once against the registration. Data window 2019-01-01 through 2026-08-31 (2800 days). Held-out test year 2025-09-01 through 2026-08-31 (365 days); training 2019-01-08 through 2025-08-31 (2428 days). One of the four confirmatory predictions missed.

## What was asked

Four models per category, all with identical fixed hyperparameters, differing only in what they are shown. Every model gets `t`, a trend covariate. WEATHER additionally gets daily weather, its lags and seven-day windows, and a freeze–thaw indicator — and no date, day of week, or day of year in any form. CLOCK gets day-of-year sine and cosine and day-of-week instead. BOTH gets everything. Skill is measured against TREND; recovery is skill(WEATHER) divided by skill(CLOCK).

## Verdicts

| Code | Category | Prediction | Observed | Verdict |
|---|---|---|---|---|
| P1 | pothole | recovery >= 0.5 | recovery = 0.2422 | MISSED |
| P2 | rodent | recovery >= 0.5 | recovery = 0.5711 | HELD |
| P3 | basement | skill(WEATHER) > skill(CLOCK) | skill(WEATHER) = 0.0846, skill(CLOCK) = -0.0799 | HELD |
| P4 | graffiti | recovery < 0.25, or UNDEFINED with skill(WEATHER) < 0.05 | recovery = -0.0337 | HELD |

P1 missed: weather recovered about a quarter of the calendar's skill on potholes, not the half that was predicted from freeze–thaw. Full per-category tables, bootstrap intervals and the seasonal-naive reference are in `results/results.md`.

The two exploratory categories carried no prediction. Weather recovered most of the calendar's skill on tree debris (recovery 0.8580) and none of it on abandoned vehicles (recovery -0.0166).

## Files

- `PREREG.md` — the registration. Not edited after its commit.
- `PREREG_MAPPING.md` — category to request-type strings, derived mechanically from the registration's keyword rule.
- `DEVIATIONS.md` — every departure from the registration.
- `NOTES.md` — the data as found, including per-type coverage gaps.
- `results/` — written by the study run: `results.md`, `results.json`, `frames.json`, and `positive_controls.json`.
- `viz/year_strip.html` — a self-contained offline page showing the WEATHER model's twelve test-year months filling in as trees are added, beside the actual months.
- `data/` — the pulled data: all-time counts per request type, daily weather, daily counts by type, and the joined daily table.

## Reproduce

```
pip install -e .
pytest -q
python -m study.run
```

The positive controls run inside `pytest` and must pass before the study is believed: a weather-driven synthetic target must be learned by WEATHER and not by CLOCK, a calendar-driven one the other way round, and a shuffled target by neither. `python viz/build.py` rebuilds the visualization from `results/frames.json`.

License: MIT.
