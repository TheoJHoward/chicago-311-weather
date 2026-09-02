# Discussion — post-hoc

Every section of this document was written after the registered results were seen. Nothing here re-scores anything. The verdicts in `results/results.md` stand as registered: P1 MISSED, P2 HELD, P3 HELD, P4 HELD.

Numbers are read from `results/results.json`, `results/trend_diagnostic.json` and `results/exploratory_no_trend.json`.

## The trend covariate

Every registered model receives `t`, days since 2019-01-01. The registration included it because 311 volume drifts over the years and a model with no way to express that drift would be penalised for it.

It does not work the way it was intended to. The test period is the final 365 days of the window, so every test day has a `t` strictly larger than any training day. A gradient-boosted tree ensemble cannot extrapolate: outside the range it was fitted on, every split resolves the same way and the ensemble returns the value of its last leaf. TREND, whose only feature is `t`, therefore emits **one constant for all 365 test days**. `results/trend_diagnostic.json` records this directly: for all six categories, the number of distinct TREND predictions on the test set is 1.

The constant is whatever the end of the training period looked like, which makes the floor a hostage to the last few weeks of training.

| Category | TREND constant (log1p) | implied complaints/day | test-year median/day | MAE(TREND) | MAE(seasonal-naive) | ratio |
|---|---|---|---|---|---|---|
| basement | 4.7141 | 110.5 | 9 | 2.2919 | 0.7383 | 3.10 |
| tree debris | 4.7330 | 112.6 | 58 | 1.1190 | 0.6173 | 1.81 |
| pothole | 4.1496 | 62.4 | 106 | 0.7276 | 0.4971 | 1.46 |
| rodent | 5.0742 | 158.8 | 111 | 0.5826 | 0.4116 | 1.42 |
| graffiti | 5.4328 | 227.8 | 275 | 0.5393 | 0.5886 | 0.92 |
| abandoned vehicle | 4.9749 | 143.7 | 157 | 0.3409 | 0.4513 | 0.76 |

Basement is distorted worst, tree debris next. Both are heavy-tailed and storm-driven: most days are small and a few days are enormous. The training period ends 2025-08-31, immediately after 2025-08-17, 2025-08-18 and 2025-08-19 — the first, third and fourth largest basement days in the entire window. TREND carries that flood forward across a whole year whose median is nine complaints a day, and its MAE is three times worse than the seasonal-naive reference reported beside it. For graffiti and abandoned vehicles, whose day-to-day counts are steadier, the same mechanism is nearly harmless and TREND actually beats the naive reference.

Because skill is defined as 1 − MAE(m)/MAE(TREND), every skill and every recovery in `results/results.md` is measured against this floor. For basement the floor is broken, and P3's HELD rests on it.

A better design would not have included a trend feature at all, or would have used a floor that cannot extrapolate — the training mean, or the seasonal-naive reference the registration already computes. The exploratory variant in `results/exploratory_no_trend.md` uses the training mean and is reported for that comparison.

## What the verdicts rest on

The registered analysis was fixed before any outcome data was retrieved. The exploratory analysis was designed after the results were seen. That is the only reason one of them counts, and it is a sufficient reason: a comparison chosen after seeing the answer can be chosen to produce the answer. The table below is not a re-scoring, and the right-hand column is not a verdict.

| Prediction | Registered | Exploratory | Registered verdict |
|---|---|---|---|
| P1 pothole, recovery ≥ 0.5 | 0.2422 | 0.0747 | MISSED |
| P2 rodent, recovery ≥ 0.5 | 0.5711 | 0.4448 | HELD |
| P3 basement, skill(WEATHER) > skill(CLOCK) | 0.0846 vs −0.0799 | 0.0980 vs 0.0745 | HELD |
| P4 graffiti, recovery < 0.25 or UNDEFINED with skill(WEATHER) < 0.05 | −0.0337 | −0.0775 | HELD |

- **P1** misses either way, and misses harder without the trend covariate. Nothing about this verdict depends on the defect.
- **P2** is the one that moves. Registered recovery is 0.5711, over the 0.5 floor; the exploratory value is 0.4448, under it. Under the exploratory design P2 would have missed. It did not: the registered analysis is the scored one, and P2 is HELD. What this shows is that the rodent verdict sits close enough to its threshold that a design choice made in advance — not the data — decided it.
- **P3** holds in both analyses, but for different reasons. In the registered analysis it holds on a floor that is three times worse than the naive reference, with skill(CLOCK) negative because CLOCK is also being measured against that broken floor. In the exploratory analysis it holds on a sane floor, with both skills positive and recovery 1.3152 — weather beating the calendar outright. The verdict is the same; the registered evidence for it is much weaker than it looks.
- **P4** holds in both, comfortably. Weather carries no signal for graffiti under either design; skill(WEATHER) is slightly negative in both.

## The pothole window

This is an interpretation offered after the result, not a registered hypothesis, and it belongs here rather than in `results/results.md`.

P1 predicted that weather would recover at least half of the calendar's skill on potholes, on the mechanism that freeze–thaw cycles open pavement. Registered recovery was 0.2422; without the trend covariate, 0.0747. The WEATHER block looks back at most seven days: three daily lags and seven-day sums, including the freeze–thaw count. Pavement damage does not work on that timescale. Freeze–thaw cycles accumulate over a winter, the pavement fails weeks later, and a complaint is filed only once someone drives over the hole and reports it. A seven-day window cannot see any of that, so the feature set may simply be too short for the mechanism it was built to test, rather than the mechanism being absent. Testing that would need a different registration with longer accumulators, and would be a new study.

## Reproducibility

Two runs in one environment are byte-identical: `test_run_is_deterministic` asserts that `run_category` fitted twice on the pothole target returns the same four MAEs, and the study run's outputs were compared byte-for-byte across a re-run at commit time.

Across environments they are not. The committed results were produced with Python 3.12.10 and scikit-learn 1.9.0, recorded in `requirements-lock.txt`. An independent reproduction from the public repository at `6dd3099`, using Python 3.11 and scikit-learn 1.8.0, obtained **all four verdicts identically** (MISSED, HELD, HELD, HELD) and point estimates that differ in the second to third decimal — rodent recovery 0.5711 against 0.5541, basement skill(WEATHER) 0.0846 against 0.1722.

The same version sensitivity shows in the trend diagnostic. That reproduction measured the basement TREND constant as 5.04 on the log scale, about 154 complaints a day; at HEAD in the committed environment it measures 4.7141, about 110.5 a day. The defect is identical in both — a single constant carried across the whole test year against a median of 9 a day — but its magnitude is not stable across versions.

`results/results.md` reports four decimal places. The third and fourth are not stable across scikit-learn versions and should not be read as meaningful. The verdicts are stable; the trailing decimals are not. Basement moves most, which is expected: it has the smallest counts, the heaviest tail, and the most broken floor.
