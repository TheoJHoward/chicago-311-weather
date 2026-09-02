# History

An append-only ledger of process facts about this repository. Entries are dated
and are never rewritten. Where an entry corrects an earlier record, the earlier
record stays where it is and the correction is recorded here and in the file
itself.

## 2026-09-02 — The study was run twice before the results were committed

`study/run.py` changed between the code commit `9bfeca8` ("Add study code and
tests") and the results commit `c2eb8ae` ("Add study results"). The change was
confined to descriptive text and metadata key names: the `meta` block gained
`data_window_start`, `data_window_end`, `data_window_days`, `modelled_first_day`
and `modelled_last_day` in place of `window_start` and `window_end`, and the
header sentence written into `results/results.md` was rewritten to distinguish
the data window from the modelled days. `git diff 9bfeca8 c2eb8ae -- study/run.py`
shows the whole of it.

The study was run once before that change and once after. Only the second run's
output was committed. The first run's output was not committed and therefore
cannot be verified from this repository. A claim was made at the time that the
two runs' numbers were identical; that claim rests on narrative alone and is not
checkable here.

`c2eb8ae` also carries the code change and the results in a single commit. Both
the re-run and the combined commit are contrary to the practice this repository
states: results are committed as the run wrote them, and code changes are
committed before the run they affect.

## 2026-09-02 — A file outside the repository was edited during verification

`.claude/launch.json`, belonging to a different project in the directory the
session was working from, was edited twice and restored twice while verifying
that the visualization pages render. The edits added and then removed a local
static-file server entry. The file was left as it was found. The edits were
outside this repository and were not authorized by any instruction governing
this work.

## 2026-09-02 — PREREG.md differs from its source by blank lines

`PREREG.md` at HEAD is 83 lines, of which 32 are blank, leaving 51 lines of
text. The source it was transcribed from is 62 lines. The difference is inserted
blank lines; no word of the registration differs. The registration was described
at the time as transcribed exactly, and in content it was. Recorded because the
line counts do not match.

## 2026-09-02 — NOTES.md carried a false statement about the test year

`NOTES.md` stated that three of the five largest basement days, including the
largest, fall inside the test year. None of them do. The five are 2025-08-17,
2023-07-05, 2025-08-18, 2025-08-19 and 2023-07-03; the test year begins
2025-09-01. Three fall in the last fifteen days of training and two in July
2023. Corrected today in `NOTES.md`, under a dated heading, with the false line
left in place.

No result depended on the statement. It was a claim about where the data's
largest days sit relative to the split, not an input to anything.

## 2026-09-02 — A design defect in the registered analysis

The defect is in the registered design, not in the code, which implements the
registration faithfully.

Every model receives `t`, days since 2019-01-01, as a trend covariate. Every
test day has a `t` larger than any training day. A gradient-boosted tree cannot
extrapolate: beyond the training range it returns the value of its last leaf.
TREND, whose only feature is `t`, therefore emits a single constant for all 365
test days, and that constant is whatever the end of the training period looked
like.

For basement, the training period ends immediately after the three largest
basement days in the entire window (2025-08-17, 2025-08-18, 2025-08-19). TREND
carries that level forward across the whole test year. Its test MAE is 2.2919 on
the log scale, against 0.7383 for the seasonal-naive reference reported beside
it — the registered floor is three times worse than the simplest baseline in the
study. Because skill is defined as 1 − MAE/MAE(TREND), every basement skill in
`results/results.md` is measured against that floor, and P3's HELD verdict rests
on it.

The registered verdicts stand as registered. Nothing is re-scored.

The reproduction that raised this defect reported the TREND constant as 5.04 on
the log scale, about 154 complaints a day, against a test-year median of 9 a
day. At HEAD, in the environment the committed results were produced in, the
constant measures 4.7141, about 110.5 complaints a day, against the same median
of 9. Both figures describe the same defect; they differ because the two
environments run different scikit-learn versions, which is the same
version-sensitivity recorded in DISCUSSION.md. The measured figure is written to
`results/trend_diagnostic.json` by the exploratory run.

## 2026-09-02 — A commit and a push were issued in one invocation

The commit of `results/exploratory_no_trend.md` and its sibling outputs
(`fc5a5ec`) and the push that followed it were issued together, rather than as
separate acts each following a read of the previous one's exit status. Both
succeeded and the state is correct. Recorded because the practice this
repository states is that irreversible acts are taken one at a time, and this
one was not.

## 2026-09-01 — Every entry above is stamped with the wrong date

The six entries above, and the correction section added to `NOTES.md` on the
same day, are headed 2026-09-02. The correct date is **2026-09-01**. This entry
supersedes those date stamps; the stamps themselves are left as written.

The work they describe was done at about 19:20 to 19:30 America/Chicago on
2026-09-01, which the commits `3f21680` through `5ce75c3` record as
17:21 to 17:29 at UTC−07:00, the machine's own zone. The date was taken from a
shell whose timezone setting was ignored, so it returned the UTC date — by then
already past midnight — instead of the Chicago date the repository dates by.

No content other than the date stamps is affected.

## 2026-09-02 — All four visualization pages were restyled

The four pages under `viz/` — `year_strip.html`, `year_strip_exploratory.html`,
`year_ring.html` and `slider.html` — were rebuilt onto a shared set of colour
and type tokens, a viewport-height layout that cannot scroll, and a lighter
furniture set: a horizontal legend without a card, a single hairline above the
footer, and one line of key help in place of a five-line block. The exploratory
page's banner became a rule-and-text line instead of a filled box.

An earlier record in this repository claimed that the registered visualization
pages were byte-identical to the state at `68cb6dd`. That claim describes
`68cb6dd` and remains true of it. It is superseded from this commit forward:
all four pages differ from `68cb6dd` by design.

No registered file, no result and no number changed. The five protected paths —
`PREREG.md`, `PREREG_MAPPING.md`, `results/results.json`, `results/results.md`
and `results/frames.json` — are untouched, and `test_registered_results_untouched`
passes. The pages read the same `results/frames.json` and
`results/exploratory_frames.json` they read before.

The category colour assignment changed: the six categories were given a palette
validated for separation under simulated colour-vision deficiency, in a fixed
stack order that is part of that validation. Basement is no longer rendered in
blue. The repository's prose was searched for colour words describing the chart
— nine markdown files, for `blue`, `red`, `green`, `amber`, `orange`, `violet`,
`purple`, `pink`, `yellow`, `colour`, `color`, `swatch` and `band` — and nothing
matched, so no prose was made false by the reassignment and none was changed.

## 2026-09-02 — A file outside the repository was read during this work

A preview call was issued before the session's working directory had moved to
this repository. The harness resolved it against the previous directory and
read another project's launch configuration, briefly starting an unrelated
local server, which was stopped immediately. Nothing outside this repository
was written and no file outside it was modified.

The practice that prevents a recurrence is not a reminder to check first: the
browser and server path was removed from this work entirely. The page layout is
now asserted from the built HTML — a viewport-height flex column with hidden
overflow and no fixed pixel height on the plot band — by
`tests/test_viz.py::test_pages_declare_viewport_fit`, which needs no browser,
no server and no launch configuration. Rendered-viewport measurement, if it is
wanted, happens outside this repository.

## 2026-09-02 — Basement moved to the first position in the stack

The assignment of categories to colour slots changed on all four pages under
`viz/`. Basement now occupies the first stack position — the baseline on the
two strip pages and the slider, the innermost band on the ring. Pothole and
rodent shift up one place each; graffiti, tree debris and abandoned vehicle
keep the positions they had.

The palette itself did not change. The sequence of colour slots and the hex
value in each slot are byte-identical to the previous commit, on every page, so
every adjacent colour pair on screen is the pair that was checked for
separation under simulated colour-vision deficiency. This was a permutation of
category labels across fixed slots, not a new palette. What changed in each
page is the list of category names and the comment above it, and nothing else.

The reason is that basement is the only category whose model band differs
materially from its actual band, and it was previously drawn mid-stack, where a
band floats between two others with no fixed edge to read it against. Mean band
height across the twelve test months on the registered page, at a plot band of
297 px:

| Category | ACTUAL | MODEL | ratio |
|---|---|---|---|
| basement | 7.9 px | 42.0 px | 5.3 |
| pothole | 47.6 px | 34.1 px | 0.7 |
| rodent | 44.6 px | 44.0 px | 1.0 |
| graffiti | 101.5 px | 90.7 px | 0.9 |
| tree debris | 37.3 px | 28.2 px | 0.8 |
| abandoned vehicle | 58.2 px | 58.1 px | 1.0 |

These heights are the mean monthly share of the six-category total multiplied
by the plot band height, computed from `results/frames.json` at the final
training stage. Basement is the band the pages exist to show: the registered
TREND floor carries the end of the training period across the whole test year,
and the model's basement share is more than five times the share actually
observed. Every other category moves by a factor between 0.7 and 1.0.

No registered file, no result and no number changed.

The entry above this one contains the sentence "Basement is no longer rendered
in blue." That sentence described the state at the commit it was written for
and is superseded here: basement now occupies the first colour slot, which is
the blue one, `#2a78d6` in light and `#3987e5` in dark. The sentence is left as
written. A search of the repository's prose for colour words — the same nine
markdown files and the same thirteen terms as before — found matches only
inside this ledger, all of them in entries describing the colour scheme itself
rather than describing the chart, and this sentence was the only one the
reassignment made false.

## 2026-09-02 — A single-screen overview page was added

`viz/overview.html` carries the whole study on one screen: three rows of
monthly stacked bars — what Chicago reported, the registered model, and the
exploratory no-trend variant — with basement's mean share of the year beside
each; a daily basement series showing the flood of 17 August 2025 two weeks
before training ended and the flat level the registered model carried across
the test year; and six per-category panels, each with its recovery, its
prediction verdict, and the three monthly series drawn together.

Every figure the page prints is computed at build time by
`viz/build_overview.py` from a committed file — `results/frames.json`,
`results/exploratory_frames.json`, `results/results.json`,
`results/trend_diagnostic.json` and `data/study_daily.csv` — and embedded as
data. The page formats no number of its own. `tests/test_overview.py`
recomputes each of them from the same sources without importing the build
script and compares against the page's parsed data block.

That comparison is made against the parsed block rather than the page text on
purpose. The embedded data is JSON, and JSON separates adjacent array values
with a comma, so a search of the raw text for a formatted number such as
"6,999" succeeds by accident whenever a 6 is followed by a 999. A test that
searched the text would have passed whether or not the figure was on the page.

No result, registration, model or number changed, and none of the four existing
pages was modified. The five protected paths are untouched.

## 2026-09-02 — Two rendering defects in the overview page were corrected

A render of `viz/overview.html` at 1920×912 and 1600×760 found the page fitting
with nothing clipped, no script errors, playback stopping at 300 trees, and the
focus, counts and theme controls working. Two visual defects were found and are
corrected here.

**The panel headers collided.** The category name and the statistic shared one
line, so in the basement panel the name and the words "weather beat the
calendar" overprinted each other, and the two-word names in the tree debris and
abandoned vehicle panels wrapped onto a second line and ran into the
y-maximum label beneath. Both viewports, both themes. The header is now two
lines: the swatch, the name and the verdict chip on the first, the statistic
alone on the second, with the name set not to wrap. The panel headers are now
written as markup by the build rather than assembled by the page's script, so
the two lines are real nodes in the file and a test can check them without a
browser.

**The registered floor could not be seen.** The daily basement strip was drawn
on a linear axis running to 3,653, the flood of 17 August 2025, so the
registered model's floor of 111 complaints a day sat about three per cent above
the baseline, indistinguishable from it and from a typical day of ten. The
strip is now drawn on log1p, the scale every model in the study is scored on,
with hairline gridlines at ten, one hundred and one thousand complaints a day —
the only gridlines on the page. On that scale the floor sits at 57.5 per cent
of the plot height and a typical day at 29.2 per cent. The floor line is drawn
in the primary ink rather than the secondary so it reads against the gridlines,
and its label has moved to the right end of its own line, where it no longer
overprints the July data or the axis label.

Two facts worth recording about that scale. The median of the daily series over
the period drawn is exactly ten a day, so the typical level and the lowest
gridline coincide. And the floor at 111 a day sits just above the hundred
gridline, a little over one per cent of the plot height from it; the two are
told apart by weight and colour rather than position.

No figure, result, registered file or existing page changed. Every number the
page prints is still computed by `viz/build_overview.py` from a committed file,
and `tests/test_overview.py` still recomputes each one from the same sources
without importing the build script.

## 2026-09-02 — Three finishing changes to the overview page

A render at 1920×912 found the page fitting with nothing clipped, no script
errors, no overlapping text, the two-line panel headers correct, and the
flood strip's floor line visible against its gridlines. Three things still
worked against the page and are changed here.

**The flood strip read as texture.** On the log scale, ordinary variation
between one and thirty complaints a day fills the lower band with a jagged
line, and the level a typical day sits at cannot be picked out of it. The raw
daily series is now drawn at one pixel in a tint of the accent, and the
seven-day trailing mean of the same series is drawn over it at 1.6 pixels in
the full accent. The mean is the line the eye follows; the raw series stays
visible behind it. The peak label remains attached to the raw maximum, because
that is the day it names. The strip's description gains a sentence saying which
line is which. The mean is computed by the build from `data/study_daily.csv`
over days d−6 to d, with the first six days using the window available.

**The per-panel maximum labels were being crossed by the lines.** In the
graffiti and abandoned vehicle panels the actual series begins near its
maximum and passes straight through the label at the top left. The label now
carries a surface-coloured halo painted behind the glyphs, so it stays legible
wherever a line lands. The label is an HTML node rather than SVG text, so the
halo is set the way HTML text takes a stroke, with the paint order given
explicitly.

**The comparison the page exists to make was half off it.** Each panel showed
one recovery, the registered one. The claim that a prediction held under the
registered analysis and would have missed under the exploratory one could not
be read without opening a second file. Every panel's second line now carries
both values, read from `results/results.json` and
`results/exploratory_no_trend.json`. For the one category whose registered
recovery is undefined, the line states the criterion that decided it instead,
and the build checks that the criterion holds in both analyses before writing
that phrase rather than asserting it in prose.

No figure, result or registered file changed. The page still prints nothing it
did not compute: the two recoveries on each panel, the seven-day mean and its
maximum are all derived at build time from committed files, and the tests
recompute them from the same files without importing the build script.
