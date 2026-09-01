# Deviations from PREREG.md

Append-only. Each entry carries a date and a reason.

## 2026-09-01 — Training excludes the first seven days of the window

PREREG.md defines the training set as "all earlier days", meaning every day
before the test period. It also requires that lagged and windowed features use
only days strictly before the day being predicted. The two cannot both hold for
2019-01-01 through 2019-01-07: those days have no complete seven-day lookback
inside the window, and the registration forbids reaching outside it.

Those seven days are therefore dropped rather than filled. The training set is
2019-01-08 through 2025-08-31, 2428 days of the 2435 days that precede the test
period. The test period is untouched: 365 days, 2025-09-01 through 2026-08-31.
This affects every model and every category identically, and is asserted by
`test_warmup_drop_is_seven_days`.

## 2026-09-01 — Scoring an UNDEFINED recovery under P1 and P2 (not exercised)

P1 and P2 state a numeric floor, "recovery >= 0.5". PREREG.md defines recovery
as UNDEFINED when skill(CLOCK) is not above 0.05, and requires each prediction
to be scored HELD or MISSED, but does not say which of the two an UNDEFINED
recovery yields for these predictions. P4, by contrast, names UNDEFINED
explicitly as one of its two ways to hold.

The code scores an UNDEFINED recovery as MISSED for P1 and P2, on the ground
that an undefined quantity does not meet a numeric floor.

This rule did not bind. In the run, recovery was defined for both pothole
(skill(CLOCK) = 0.4745) and rodent (skill(CLOCK) = 0.6127), so both verdicts
came from the numeric comparison alone. The rule is recorded because it is
present in `study/score.py`, not because it changed a verdict.
