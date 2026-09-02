# Exploratory results — trend covariate removed

Exploratory. This analysis was designed after the registered results were seen. It removes the trend covariate from every model. It does not re-score any prediction; the registered verdicts in results.md stand. It is reported because the registered design carries a defect described in DISCUSSION.md, and because the comparison shows how much the verdicts depend on a design choice made in advance.

The floor model here is MEAN: the mean of the training targets, predicted for every test day. Skill is 1 - MAE/MAE(MEAN). WEATHER carries the weather block alone, CLOCK the clock block alone, BOTH the union. Hyperparameters, split, categories, target and bootstrap are unchanged.

## pothole (confirmatory)

| Model | MAE | MAE 90% interval | Skill | Skill 90% interval |
|---|---|---|---|---|
| MEAN | 0.6484 | 0.5618 to 0.7396 | - | - |
| WEATHER | 0.6245 | 0.5513 to 0.6984 | 0.0370 | -0.0755 to 0.1415 |
| CLOCK | 0.3277 | 0.2822 to 0.3782 | 0.4946 | 0.3825 to 0.5852 |
| BOTH | 0.3521 | 0.2969 to 0.4167 | 0.4570 | 0.3242 to 0.5714 |

Recovery: 0.0747 (90% interval -0.1650 to 0.2633; 1000 of 1000 resamples defined).

## rodent (confirmatory)

| Model | MAE | MAE 90% interval | Skill | Skill 90% interval |
|---|---|---|---|---|
| MEAN | 0.5131 | 0.4577 to 0.5786 | - | - |
| WEATHER | 0.4040 | 0.3582 to 0.4534 | 0.2125 | 0.1559 to 0.2728 |
| CLOCK | 0.2679 | 0.2003 to 0.3407 | 0.4778 | 0.3577 to 0.5848 |
| BOTH | 0.2388 | 0.1975 to 0.2858 | 0.5345 | 0.4953 to 0.5817 |

Recovery: 0.4448 (90% interval 0.3335 to 0.5831; 1000 of 1000 resamples defined).

## basement (confirmatory)

| Model | MAE | MAE 90% interval | Skill | Skill 90% interval |
|---|---|---|---|---|
| MEAN | 0.7384 | 0.6451 to 0.8412 | - | - |
| WEATHER | 0.6661 | 0.5748 to 0.7566 | 0.0980 | 0.0215 to 0.1718 |
| CLOCK | 0.6834 | 0.5941 to 0.7750 | 0.0745 | 0.0174 to 0.1279 |
| BOTH | 0.6058 | 0.5049 to 0.7124 | 0.1796 | 0.0865 to 0.2712 |

Recovery: 1.3152 (90% interval 0.2624 to 2.3542; 757 of 1000 resamples defined).

## graffiti (confirmatory)

| Model | MAE | MAE 90% interval | Skill | Skill 90% interval |
|---|---|---|---|---|
| MEAN | 0.5848 | 0.5510 to 0.6218 | - | - |
| WEATHER | 0.6027 | 0.5331 to 0.6839 | -0.0306 | -0.1102 to 0.0452 |
| CLOCK | 0.3539 | 0.2733 to 0.4410 | 0.3948 | 0.2760 to 0.5169 |
| BOTH | 0.3568 | 0.2818 to 0.4412 | 0.3898 | 0.2830 to 0.4946 |

Recovery: -0.0775 (90% interval -0.3276 to 0.0994; 1000 of 1000 resamples defined).

## tree debris (exploratory)

| Model | MAE | MAE 90% interval | Skill | Skill 90% interval |
|---|---|---|---|---|
| MEAN | 0.9987 | 0.7711 to 1.2316 | - | - |
| WEATHER | 0.6330 | 0.5323 to 0.7502 | 0.3662 | 0.2446 to 0.4555 |
| CLOCK | 0.4986 | 0.3756 to 0.6219 | 0.5007 | 0.4010 to 0.5850 |
| BOTH | 0.4734 | 0.3644 to 0.5933 | 0.5260 | 0.4251 to 0.6080 |

Recovery: 0.7314 (90% interval 0.5591 to 0.8395; 1000 of 1000 resamples defined).

## abandoned vehicle (exploratory)

| Model | MAE | MAE 90% interval | Skill | Skill 90% interval |
|---|---|---|---|---|
| MEAN | 0.4573 | 0.4362 to 0.4801 | - | - |
| WEATHER | 0.4173 | 0.3890 to 0.4449 | 0.0874 | 0.0199 to 0.1539 |
| CLOCK | 0.3209 | 0.2880 to 0.3559 | 0.2982 | 0.2228 to 0.3691 |
| BOTH | 0.2782 | 0.2317 to 0.3285 | 0.3917 | 0.2608 to 0.5040 |

Recovery: 0.2930 (90% interval 0.0758 to 0.4782; 1000 of 1000 resamples defined).

## Side by side with the registered analysis

The registered column is read from results/results.json and is the scored result. The exploratory column is this run. The last column is the word the exploratory value would have produced had it been put through the registered threshold; it is not a verdict, and no verdict changes.

| Code | Category | Prediction | Registered observed | Verdict | Exploratory observed | Would have been |
|---|---|---|---|---|---|---|
| P1 | pothole | recovery >= 0.5 | recovery = 0.2422 | MISSED | recovery = 0.0747 | MISSED |
| P2 | rodent | recovery >= 0.5 | recovery = 0.5711 | HELD | recovery = 0.4448 | MISSED |
| P3 | basement | skill(WEATHER) > skill(CLOCK) | skill(WEATHER) = 0.0846, skill(CLOCK) = -0.0799 | HELD | skill(WEATHER) = 0.0980, skill(CLOCK) = 0.0745 | HELD |
| P4 | graffiti | recovery < 0.25, or UNDEFINED with skill(WEATHER) < 0.05 | recovery = -0.0337 | HELD | recovery = -0.0775 | HELD |

The two exploratory categories, tree debris and abandoned vehicle, carry no prediction in either analysis.
