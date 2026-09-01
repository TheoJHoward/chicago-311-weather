"""Every numeric threshold the verdicts depend on, and the PREREG.md text it
comes from.

Nothing else in the study may hard-code these numbers. A test asserts that each
string in PREREG_STRINGS appears verbatim in PREREG.md.
"""

from __future__ import annotations

# P1, P2: "recovery >= 0.5"
RECOVERY_HELD_MIN = 0.5

# P4: "recovery < 0.25"
RECOVERY_LOW_MAX = 0.25

# Recovery is defined only when "skill(CLOCK) > 0.05"; P4's alternative branch
# uses the same number as "skill(WEATHER) < 0.05".
CLOCK_SKILL_DEFINED_MIN = 0.05
P4_WEATHER_SKILL_MAX = 0.05

# PC1, PC2: the driven model must reach "> 0.3"
PC_SKILL_MIN = 0.3

# PC3: shuffled training targets must give "< 0.1" in absolute skill
PC3_SKILL_ABS_MAX = 0.1

# Bootstrap
BOOTSTRAP_DRAWS = 1000
BOOTSTRAP_LO = 5
BOOTSTRAP_HI = 95
BOOTSTRAP_SEED = 0

# The threshold strings as they are written in PREREG.md.
PREREG_STRINGS = ["≥ 0.5", "< 0.25", "> 0.05", "> 0.3", "< 0.1"]
