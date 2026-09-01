# Results

Data window 2019-01-01 through 2026-08-31 (2800 days). The first seven days are dropped because their lags reach before the window start, so the modelled days run 2019-01-08 through 2026-08-31. Training days 2019-01-08 through 2025-08-31 (2428 days). Test days 2025-09-01 through 2026-08-31 (365 days).

All errors are mean absolute error of log(1 + count) on the test set. Skill is 1 - MAE/MAE(TREND). Intervals are 5th-95th percentiles of 1000 monthly-block bootstrap resamples of the test year; verdicts use the point estimates.

## pothole (confirmatory)

| Model | MAE | MAE 90% interval | Skill | Skill 90% interval |
|---|---|---|---|---|
| TREND | 0.7276 | 0.6153 to 0.8447 | - | - |
| WEATHER | 0.6440 | 0.5758 to 0.7158 | 0.1149 | -0.0049 to 0.2213 |
| CLOCK | 0.3823 | 0.3167 to 0.4506 | 0.4745 | 0.3503 to 0.5765 |
| BOTH | 0.3759 | 0.3088 to 0.4486 | 0.4834 | 0.3541 to 0.5905 |
| seasonal-naive (context only) | 0.4971 | - | 0.3168 | - |

Recovery: 0.2422 (90% interval -0.0120 to 0.4399; 1000 of 1000 resamples defined).

## rodent (confirmatory)

| Model | MAE | MAE 90% interval | Skill | Skill 90% interval |
|---|---|---|---|---|
| TREND | 0.5826 | 0.4436 to 0.7431 | - | - |
| WEATHER | 0.3788 | 0.3516 to 0.4089 | 0.3499 | 0.1931 to 0.4648 |
| CLOCK | 0.2256 | 0.1768 to 0.2776 | 0.6127 | 0.5749 to 0.6447 |
| BOTH | 0.1834 | 0.1613 to 0.2071 | 0.6852 | 0.6239 to 0.7290 |
| seasonal-naive (context only) | 0.4116 | - | 0.2935 | - |

Recovery: 0.5711 (90% interval 0.3272 to 0.7408; 1000 of 1000 resamples defined).

## basement (confirmatory)

| Model | MAE | MAE 90% interval | Skill | Skill 90% interval |
|---|---|---|---|---|
| TREND | 2.2919 | 2.0871 to 2.4818 | - | - |
| WEATHER | 2.0980 | 1.9582 to 2.2249 | 0.0846 | 0.0126 to 0.1428 |
| CLOCK | 2.4751 | 2.2787 to 2.6509 | -0.0799 | -0.1155 to -0.0500 |
| BOTH | 2.0109 | 1.8803 to 2.1397 | 0.1226 | 0.0445 to 0.1890 |
| seasonal-naive (context only) | 0.7383 | - | 0.6779 | - |

Recovery: UNDEFINED (skill(CLOCK) = -0.0799 is not above 0.05).

## graffiti (confirmatory)

| Model | MAE | MAE 90% interval | Skill | Skill 90% interval |
|---|---|---|---|---|
| TREND | 0.5393 | 0.4990 to 0.5837 | - | - |
| WEATHER | 0.5478 | 0.5038 to 0.5963 | -0.0157 | -0.0379 to 0.0054 |
| CLOCK | 0.2878 | 0.2417 to 0.3376 | 0.4663 | 0.4150 to 0.5211 |
| BOTH | 0.2981 | 0.2558 to 0.3451 | 0.4473 | 0.3989 to 0.4965 |
| seasonal-naive (context only) | 0.5886 | - | -0.0914 | - |

Recovery: -0.0337 (90% interval -0.0816 to 0.0110; 1000 of 1000 resamples defined).

## tree debris (exploratory)

| Model | MAE | MAE 90% interval | Skill | Skill 90% interval |
|---|---|---|---|---|
| TREND | 1.1190 | 0.8228 to 1.4509 | - | - |
| WEATHER | 0.5817 | 0.5087 to 0.6723 | 0.4802 | 0.3091 to 0.5948 |
| CLOCK | 0.4928 | 0.3819 to 0.6270 | 0.5596 | 0.4135 to 0.6613 |
| BOTH | 0.4290 | 0.3332 to 0.5463 | 0.6166 | 0.4700 to 0.7174 |
| seasonal-naive (context only) | 0.6173 | - | 0.4483 | - |

Recovery: 0.8580 (90% interval 0.6877 to 0.9528; 1000 of 1000 resamples defined).

## abandoned vehicle (exploratory)

| Model | MAE | MAE 90% interval | Skill | Skill 90% interval |
|---|---|---|---|---|
| TREND | 0.3409 | 0.3164 to 0.3657 | - | - |
| WEATHER | 0.3440 | 0.3209 to 0.3675 | -0.0090 | -0.0379 to 0.0172 |
| CLOCK | 0.1554 | 0.1358 to 0.1757 | 0.5440 | 0.4972 to 0.5925 |
| BOTH | 0.1401 | 0.1261 to 0.1543 | 0.5891 | 0.5578 to 0.6208 |
| seasonal-naive (context only) | 0.4513 | - | -0.3239 | - |

Recovery: -0.0166 (90% interval -0.0665 to 0.0331; 1000 of 1000 resamples defined).

## Verdicts

| Code | Category | Prediction | Observed | Verdict |
|---|---|---|---|---|
| P1 | pothole | recovery >= 0.5 | recovery = 0.2422 | MISSED |
| P2 | rodent | recovery >= 0.5 | recovery = 0.5711 | HELD |
| P3 | basement | skill(WEATHER) > skill(CLOCK) | skill(WEATHER) = 0.0846, skill(CLOCK) = -0.0799 | HELD |
| P4 | graffiti | recovery < 0.25, or UNDEFINED with skill(WEATHER) < 0.05 | recovery = -0.0337 | HELD |

The two exploratory categories, tree debris and abandoned vehicle, carry no prediction and appear above for reporting only.
