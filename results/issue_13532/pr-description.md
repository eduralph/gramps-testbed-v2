# Fix: Fan Chart respects active name format preference

## Root cause

The fan-chart widget renders two-line person labels through hard-pinned name
formats registered as `TWO_LINE_FORMAT_1 = "%l"` (surname) and
`TWO_LINE_FORMAT_2 = "%f %s"` (given+suffix) in `gramps/gui/widgets/fanchart.py:102-105`
on the target branch — so `draw_person` always drew surname / given-suffix
regardless of the user's active "Name format" preference. Additionally, none
of the three fan-chart views connected the `nameformat-changed` uistate signal,
so even the single-line path (which *does* resolve through `name_displayer.display`)
never re-rendered when the preference changed.

## Fix

1. **`gramps/gen/display/name.py`** — Add two new public methods to `NameDisplay`:
   - Store the locale comma glyph as `self.COMMAGLYPH` (line 392) so a format
     can be split at the surname/given boundary
   - `get_two_line_format(num=None)` — returns the active (or given) name format
     split at the comma into `(line1_fmt, line2_fmt)`
   - `display_two_lines(person)` — renders a person's primary name as a
     two-line tuple using the active format split at the surname/given comma

2. **`gramps/gui/widgets/fanchart.py`** — Remove the dead `TWO_LINE_FORMAT_1/2`
   constants (lines 102-105) and the static `name_displayer.set_name_format([...])`
   registration in `FanChartBaseWidget.__init__`. Update `draw_person` (lines 743-744)
   to call `name_displayer.display_two_lines(person)` so it always uses the *current*
   active format. The `showid` gramps-id prefix on line 1 is preserved.

3. **`fanchartview.py`, `fanchartdescview.py`, `fanchart2wayview.py`** — Connect
   the `nameformat-changed` signal to trigger `person_rebuild` in each view's `__init__`,
   mirroring the pattern already used for `font-changed`. This ensures all three
   fan-chart views re-render when the name format preference changes.

4. **`po/POTFILES.skip`** — Register the new core test file (the file has no
   translatable strings, so it goes to `.skip`).

## Verified against

- `gramps/gen/display/name.py:392` — `COMMAGLYPH` locale definition on target branch
- `gramps/gui/widgets/fanchart.py:102-105` — dead `TWO_LINE_FORMAT_1/2` constants
- `gramps/gui/widgets/fanchart.py:743-744` — `draw_person` call site where names are formatted
- `gramps/plugins/view/fanchartview.py` — view initialization (signal connection point)
- `gramps/plugins/view/fanchartdescview.py` — descendant view initialization
- `gramps/plugins/view/fanchart2wayview.py` — two-way view initialization

## Test

**Core unit test (headless, red→green):**
`gramps/gen/display/test/fanchart_name_format_test.py` — exercises the new
`NameDisplay.get_two_line_format()` and `display_two_lines()` methods with no
GUI import. Demonstrates that (a) the LNFN format `"%l, %f %s"` splits into
surname / given-suffix lines, (b) the "Given" format `"%f"` yields only the
given name on line 1 with an empty line 2 (the reporter's case: "Avis" instead
of "Fernandez ... Avis III"), and (c) format changes are reflected in the labels.

**AT-SPI/dogtail repro (advisory, interface-level):**
`engine/interface/test_bug_13532_fanchart-name-format.py` — launches Gramps with
"Name format: Given", opens the Fan Chart view, and attempts to read chart text
via AT-SPI. The chart labels are Cairo-drawn and not exposed via AT-SPI, so this
test skips when the text cannot be read (the expected case), recording the result
as UNVERIFIABLE for human sign-off. The regression proof is the headless unit test.

Fixes #13532
