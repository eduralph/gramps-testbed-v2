# Build notes — issue 6324 (pdf-table-cell-wrap-page-break)

## Success criterion / invariant

A table cell whose wrapped text straddles a page boundary must render in full across
the two pages, never be silently dropped (cairo/PDF backend). Proven by a C4 docgen
test that drives the production pagination path and asserts the cell text survives,
red pre-fix → green post-fix.

## Root cause (target branch `maintenance/gramps61`)

`gramps/plugins/lib/libcairodoc.py`, `GtkDocParagraph.divide` — the step-1 shortcut
at `libcairodoc.py:618-621`:

```python
# 1. if paragraph part of a cell, we do not divide if only small part,
# of paragraph can be shown, instead move to next page
if line_count < 4 and self._parent._type == "CELL":
    return (None, self), 0
```

When a *short* (< 4 line) cell paragraph does not fully fit in the height it is
given, this shortcut moves the **whole** paragraph to the next page (`(None, self)`),
**with no guarantee the paragraph will fit there either**. The cell divide
(`libcairodoc.py:979-1021`) turns that `(None, self)` into `(self_emptied, new_cell)`,
the row/table propagate it, and the paginator (`CairoDoc.paginate`, `libcairodoc.py:1782`)
places the now-empty shell and retries the content on a fresh page. If the paragraph
cannot fit in the height it keeps being given (a wide/narrow cell whose 2–3 wrapped
lines exceed the space between the page top and the cell), it is moved forward again
and again and its text is never placed — the cell renders blank / pagination never
terminates. Other backends do their own layout and are unaffected.

### History confirming the diagnosis (git log -L on the branch)

- `917658df34` (bug 2714): infinite-loop fix — "allow cells to be split, so rows split
  automatically" — established that cell paragraphs *may* split across pages.
- `066d39a739` (bug 2860): rewrote the split to use exact Pango line iteration and, in
  doing so, changed the cell guard from `line_per_height < line_count < 4` to
  `line_count < 4` and hard-`return (None, self), 0`. The generic steps 2 and 3
  immediately below already handle both sub-cases correctly (step 2 moves the whole
  paragraph when *not even its first line* fits; step 3 splits it, placing at least the
  first line, otherwise). The step-1 shortcut is therefore redundant when it is safe
  and harmful when it is not — it is the only path that refuses to make progress.

## The fix (minimal change that restores the invariant)

Remove the step-1 shortcut (and the now-unused `line_count = layout.get_line_count()`
assignment it was the sole user of). A cell paragraph that does not fit now falls
through to the existing generic logic:

- **step 2** (`libcairodoc.py`, "if nothing fits, move to next page"): moves the whole
  paragraph when not even the first line fits — correct, and on the fresh page at least
  the first line then fits, so progress is guaranteed;
- **step 3** (the split): places at least the first line and carries the remainder to a
  new paragraph — guaranteeing progress and never dropping text.

This is the smallest change that restores the pagination invariant (principles §1.2,
§2): it deletes the specific content-dropping branch rather than reshaping the division
engine. Net −5 lines in one method.

### Behaviour change (for human sign-off)

A short (2–3 line) cell that lands on a page boundary now **splits** across the boundary
instead of always jumping whole to the next page. The invariant explicitly sanctions
"splitting **or** moving it intact"; splitting is what steps 2/3 already do for every
non-cell paragraph and for ≥ 4-line cell paragraphs. A randomized check of 500 realistic
multi-row / multi-column / multi-paragraph tables at page heights 120–700 pt showed **0**
content drops and **0** non-terminations both before *and* after the fix on ordinary
pages (the bug only bites when the cell cannot fit in the space it is given); the fix
adds the boundary case without regressing the ordinary ones.

## Alternatives considered and rejected (with cost)

1. **Restore the pre-2860 `line_per_height < line_count < 4` guard.** Recompute
   `line_per_height` (~3 lines) and re-add the lower bound. Rejected: that guard *also*
   returned `(None, self)` (move whole) whenever "some but not all lines fit", so it did
   **not** guarantee progress — it would loop/drop in exactly the same way. It does not
   restore the invariant.

2. **Propagate "nothing placed" (`e1 = None`) up cell → row → table → paginator** so the
   paginator starts a fresh page without placing an empty shell. Rejected on cost *and*
   correctness: it requires coordinated edits in three `divide` methods —
   `GtkDocTableCell.divide` return `(None, new_cell)` when `childnr == 0` (~2 lines),
   `GtkDocTableRow.divide` track "placed_any" and handle `c1 is None` (~5 lines),
   `GtkDocTable.divide` drop the emptied row from `self._children` when `r1 is None`
   (~4 lines) — ~11 lines across 3 methods versus −5 in one — and it *still* loops when
   a cell is taller than a full page (it only relocates to a fresh page, it never
   splits). It guards the symptom (empty-shell progress-faking) instead of removing the
   cause (the refuse-to-split shortcut).

3. **Thread the full page height into `divide` so the shortcut can move only when the
   paragraph fits on a fresh page.** Rejected: adds a parameter to ~10 polymorphic
   `divide` signatures (GtkDocBaseElement, Paragraph, Table, Row, Cell, Pagebreak,
   Picture, Frame, ToC, AlphabeticalIndex) — a broad signature churn the brief warns
   against ("any broad rewrite of the division engine … out of scope") for no behaviour
   the delete does not already achieve correctly.

## Test — `gramps/plugins/test/cairodoc_table_pagination_test.py`

Drives the **production** path, not a re-implementation of the pagination math
(principles §3.4):

- builds a real `GtkDocTable / GtkDocTableRow / GtkDocTableCell / GtkDocParagraph`
  (a single-column table, one wrapping cell);
- lays it out with a **real** Pango layout backed by an in-memory cairo `ImageSurface`
  (headless — no X display, no GTK main loop, no D-Bus/AT-SPI, so it runs under the
  plain `python3 -m unittest` C4 core runner);
- measures the paragraph's one-line and full heights and picks a page height between
  them, forcing the wrapping cell onto the page boundary regardless of the container's
  installed fonts;
- runs the production `CairoDoc.paginate` step in a **bounded** loop (the real
  `paginate_document` wrapper is `while not paginate(): pass`, which is the *infinite*
  loop the bug produces, so the test caps iterations and asserts termination);
- asserts (a) pagination terminated and (b) every word of the cell text is present in
  the paginated pages.

### Headless-import note

`libcairodoc` imports `gramps.gui.utils.SystemFonts` at module load. Under GTK 4 a bare
`from gi.repository import Gtk/Gdk` import does **not** require a display (only
`Gtk.init` / widget creation does), and Pango text layout needs only fontconfig — so
importing `libcairodoc` and building a Pango layout both succeed with `DISPLAY`/
`WAYLAND_DISPLAY` unset. Verified locally with the display env vars removed. No GUI
extraction was needed.

## Verification performed

The docker-based `run-verify.sh` (C4) requires container privileges not available in
this sandbox, so it could not be executed here. Equivalent red→green was proven by
running the **shipped test file verbatim** against the production import path:

- against the unpatched installed `gramps.plugins.lib.libcairodoc` → **FAIL**
  ("pagination did not terminate … bug 6324");
- with the fixed module registered under the same `gramps.plugins.lib.libcairodoc`
  name → **ok**.

Additionally, the full production `CairoDoc.paginate` + `divide` chain was exercised
directly on both the buggy and fixed code: buggy = never completes / cell text absent;
fixed = completes in 3 pages / cell text present; 500-config randomized regression = 0
drops both before and after on ordinary pages.

A human should run the C4 `run-verify.sh` (and ideally eyeball a Database Differences
Report → PDF with a cell wrapping at a page bottom) at sign-off to confirm in the real
container.

## Files / POTFILES

- `gramps/plugins/lib/libcairodoc.py` — the fix (modified).
- `gramps/plugins/test/cairodoc_table_pagination_test.py` — new test, no translatable
  strings → registered in `po/POTFILES.skip` (doc 16 §Adding and removing Python files).

Note: the shared validation worktree `gramps-6.1` was found carrying an unrelated
concurrent bundle's edits (a citationtreemodel search change). `patch.diff`'s
`po/POTFILES.skip` hunk was regenerated from the pristine `HEAD` blob so it contains
**only** this bundle's line; `git apply --check` against a clean tree passes for all
three files.
