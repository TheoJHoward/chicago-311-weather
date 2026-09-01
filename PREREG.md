# Preregistration — Calendar-blind: can a model learn Chicago's complaint calendar from weather alone?

Author: Theo Johann Howard
Registered: 2026-09-01
Status: registered before any date-level outcome data was retrieved (see "Permitted before registration").

## Question

Chicago's 311 complaints follow a seasonal calendar — potholes in late winter, rodents in summer. This study asks how much of that calendar a predictive model can recover from daily weather alone, when it is never given the date, the day of the week, or the day of the year.

## Data

- Outcomes: City of Chicago, "311 Service Requests" (data.cityofchicago.org, dataset v6vf-nfxy). Records flagged duplicate = true or legacy_record = true are excluded. Daily counts by request type, by created_date, America/Chicago.
- Predictors: Open-Meteo historical weather archive (archive-api.open-meteo.com), daily, latitude 41.8781, longitude -87.6298, timezone America/Chicago: temperature_2m_max, temperature_2m_min, temperature_2m_mean, precipitation_sum, rain_sum, snowfall_sum, wind_speed_10m_max.
- Window: 2019-01-01 through the last date, not later than 2026-08-31, for which the weather archive returns a non-null temperature_2m_max at pull time. The realized window is recorded in NOTES.md.

## Unit and split

- Unit: one calendar day.
- Test set: the final 365 days of the window. Training set: all earlier days. No day is in both. Nothing from the test period's outcomes is used for training, feature construction, or the reference baseline.

## Categories

Six request-type categories, each defined mechanically as the union of every sr_type whose lowercase form contains the keyword:

- pothole — "pothole"
- rodent — "rodent"
- basement — "water in basement"
- graffiti — "graffiti"
- tree debris — "tree debris"
- abandoned vehicle — "abandoned vehicle"

The first four carry predictions (confirmatory). The last two are exploratory: reported, no prediction. The exact sr_type strings matched are recorded in PREREG_MAPPING.md, produced by the rule above before any date-level data is retrieved.

Target per category per day: log(1 + count).

## Models

All models are scikit-learn HistGradientBoostingRegressor with fixed hyperparameters: max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=20, l2_regularization=1.0, early_stopping=False, random_state=0. No tuning of any kind.

Every model receives t = days since 2019-01-01, a trend covariate.

- TREND: t only.
- WEATHER: t; the seven same-day weather variables; lags 1, 2, 3 of each; 7-day sums of precipitation, rain, snowfall over the prior seven days; a freeze–thaw indicator (minimum below 0 °C and maximum above 0 °C on the day); the count of freeze–thaw days over the prior seven days. No date, day-of-week, or day-of-year information in any form.
- CLOCK: t; sine and cosine of day-of-year; day-of-week (one-hot).
- BOTH: the union of the WEATHER and CLOCK features.

Lagged and windowed features use only days strictly before the day being predicted.

## Metric

Mean absolute error of the target on the test set, per category. Skill of model m relative to TREND: skill(m) = 1 − MAE(m)/MAE(TREND).

Recovery = skill(WEATHER)/skill(CLOCK), defined only when skill(CLOCK) > 0.05; otherwise reported as UNDEFINED.

A seasonal-naive reference — the mean training-set target over training days within ±3 days of the same day-of-year — is reported for context and plays no part in the predictions below.

Uncertainty: 90% intervals from 1,000 monthly-block bootstrap resamples of the test days. Verdicts use point estimates; intervals are reported beside them.

## Predictions (fixed before any outcome data was seen)

- P1 pothole: recovery ≥ 0.5. Mechanism: freeze–thaw cycles open potholes.
- P2 rodent: recovery ≥ 0.5. Mechanism: warmth drives rodent activity and sightings.
- P3 basement: skill(WEATHER) > skill(CLOCK). Mechanism: basement flooding follows rain, not the calendar.
- P4 graffiti: recovery < 0.25, or UNDEFINED with skill(WEATHER) < 0.05. Mechanism: graffiti reporting is not weather-driven.

Each prediction is scored HELD or MISSED by code from these thresholds. Nothing is re-scored.

## Positive controls (run before the study is scored; a failure stops the study)

- PC1: a synthetic weather-driven target passed through the identical pipeline must give skill(WEATHER) > skill(CLOCK) and skill(WEATHER) > 0.3.
- PC2: a synthetic calendar-driven target passed through the identical pipeline must give skill(CLOCK) > skill(WEATHER) and skill(CLOCK) > 0.3.
- PC3: with training targets shuffled and models refit, |skill| < 0.1 for WEATHER, CLOCK and BOTH.

Also asserted by tests: the last training day precedes the first test day; lag features equal the prior day's raw values; the seasonal-naive reference uses training days only.

## Permitted before registration

Enumerating the dataset's schema and the all-time total count per sr_type, with no date dimension, is permitted: it cannot inform any prediction above. Retrieving any count with a date dimension is not.

## Deviations

Any departure from this document is recorded in DEVIATIONS.md, append-only, with the date and the reason. This document is not edited after registration.
