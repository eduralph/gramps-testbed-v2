# Build notes — issue 13532 (fanchart-view-respects-name-format)

Target: `gramps-project/gramps` @ `maintenance/gramps61`
(verified against the pinned upstream worktree `gramps-6.1` = `upstream/maintenance/gramps61`
@ `cbe5699b2e`).

## Root cause (two sentences)

The fan-chart widget renders two-line person labels through **hard-pinned** name
formats registered in `gramps/gui/widgets/fanchart.py:104-105,154-159` on the
target branch — `TWO_LINE_FORMAT_1 = "%l"` (surname) and `TWO_LINE_FORMAT_2 =
"%f %s"` (given+suffix) — so `draw_person` (`fanchart.py:743-744`) always drew
surname / given-suffix regardless of the user's active "Name format" preference.
Additionally none of the three fan-chart views connected the
`nameformat-changed` uistate signal, so even the single-line path
(`fanchart.py:721`, which *does* resolve through `name_displayer.display`) never
re-rendered when the preference changed.

This is exactly the reporter's symptom (Mantis notes, person I1200 Avis
Fernandez): with "Name format: Given" the chart still showed
"Fernandez … Avis III" instead of "Avis".

## Invariant restored

"A person label rendered by a view reflects the user's active display-name
format — the fan chart resolves names through the configured name displayer (and
re-renders when that configuration changes), not a hard-pinned format."

The smallest change that restores the invariant is to (a) make the two-line
rendering derive from the *active* format, and (b) make the views re-render when
the format changes.

## The fix

1. **`gramps/gen/display/name.py`** (import-light: only `gramps.gen.*`, no GUI):
   - store the locale comma glyph as `self.COMMAGLYPH` (next to where it is
     computed, name.py:392) so a format can be split at the surname/given
     boundary;
   - add `get_two_line_format(num=None)` — returns the active (or given) name
     format split at that comma into `(line1_fmt, line2_fmt)`; a format with no
     comma yields the whole format on line 1 and an empty line 2;
   - add `display_two_lines(person)` — renders a person's primary name as
     `(line1, line2)` using `get_two_line_format` + the existing `format_str`.

   Splitting the active format at the comma is the *original* two-line intent:
   the pinned `("%l", "%f %s")` is precisely the standard LNFN format
   `"%l, %f %s"` split at its comma — the bug was freezing it to LNFN instead of
   the active format. So `Given` ("%f") → `("Avis", "")`; LNFN → `("Fernandez",
   "Avis III")`.

2. **`gramps/gui/widgets/fanchart.py`**:
   - remove the dead `TWO_LINE_FORMAT_1/2` constants and the static
     `name_displayer.set_name_format([...])` registration in
     `FanChartBaseWidget.__init__`;
   - `draw_person` now calls `name_displayer.display_two_lines(person)` so it
     always uses the *current* active format (no stale registration to keep in
     sync). The `showid` gramps-id prefix on line 1 is preserved.

   `draw_person` lives on `FanChartBaseWidget`, which `FanChartDescWidget` and
   `FanChart2WayWidget` inherit unchanged, so the Descendant and 2-way fan
   charts get the fix too (brief: "the related Descendant / 2-way fan views").

3. **`fanchartview.py`, `fanchartdescview.py`, `fanchart2wayview.py`**: connect
   `self.uistate.connect("nameformat-changed", self.person_rebuild)` (mirrors
   `pedigreeview.py:570`), so all three views re-render when the preference
   changes.

4. **`po/POTFILES.skip`**: register the new core test file (doc 16 §Adding and
   removing Python files; the file has no translatable strings → `.skip`).

## Why not these alternatives

- **Derive + re-register the two `TWO_LINE_FORMAT_*` nums on every
  `nameformat-changed`** (keep `display_format(person, num)`): this keeps a
  global mutable registration in `name_displayer` that must be re-pushed from
  the GUI on each format change and each redraw, and leaves two otherwise-unused
  "inactive standard format" slots in the displayer. Routing `draw_person`
  straight through `display_two_lines` removes ~6 lines of registration
  scaffolding (the `set_name_format([...])` block + the two module constants)
  and has no synchronisation state — strictly smaller and always-current.
- **Touch only `fanchartview.py` (brief's primary scope)**: would leave the
  Descendant / 2-way charts and the *content* bug unfixed. The content fix has
  to be in the shared widget; the one-line view connections are the re-render
  half of the same invariant.

## Tests

- **Gated red→green (headless, core):**
  `gramps/gen/display/test/fanchart_name_format_test.py` (in `patch.diff`,
  `*_test.py` suffix per INTEGRATION §3). It drives the **production** methods
  the chart calls — `NameDisplay.get_two_line_format` / `display_two_lines` —
  with no GUI import, so it runs on the headless C4 runner. Proven locally:
  - GREEN with the fix (8/8 ok);
  - RED with `name.py` reverted (the C4 red leg): 8/8 ERROR
    (`AttributeError: 'NameDisplay' object has no attribute 'display_two_lines'`
    / `get_two_line_format`).
  The behavioural assertions encode the bug: with "Given" the labels are
  `("Avis", "")` (no surname leak — the reporter's case), and a format change
  changes the labels.

  Production routes through these exact methods (`fanchart.py` draw_person →
  `name_displayer.display_two_lines`), so the test is not a parallel copy
  (principles §3.4). The GUI-entangled `draw_person` loop itself can't be
  imported headlessly; the import-light name-resolution it now delegates to is
  what the test exercises.

  (Could not run the dockerised `run-verify.sh` in this environment — sandboxed
  docker invocation is blocked — so the red→green was reproduced directly with
  `python3 -m unittest` against the worktree, `GRAMPS_RESOURCES` pointed at a
  built tree. `git apply --check` confirms `patch.diff` applies cleanly to
  clean `upstream/maintenance/gramps61`.)

- **Committed AT-SPI repro (advisory, `Surfaces: gui` → C4-verify-interface):**
  `engine/interface/test_bug_13532_fanchart-name-format.py`. The fan-chart
  labels are Cairo-drawn onto a `Gtk.DrawingArea` and are **not exposed via
  AT-SPI**, so the dogtail driver cannot read them back. The test launches
  Gramps with "Name format: Given", opens the Fan Chart view, attempts to read
  any chart text the a11y tree exposes, and `skipTest`s when it cannot (the
  usual case) — which the interface gate records as UNVERIFIABLE for human
  sign-off — rather than asserting against text it cannot see. This is the
  honest outcome the brief anticipates; the real behavioural proof is the
  headless unit test above, plus a documented visual repro path.

## Conformance checks run

- `T2-potfiles`: ✓ (new core `.py` registered).
- `T2-shape`: ✓ (GPL header present, no diagnostic prints).
- `black 26.5.0`: all six touched files left unchanged (commit-hook clean).
- `py_compile`: all changed files OK.
