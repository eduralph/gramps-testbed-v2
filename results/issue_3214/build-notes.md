# Build notes — issue 3214 / preformatted-note-fontsize-reset-to-default

*Withheld from the reviewer. Rationale, alternatives, and evidence for the human at sign-off.*

Target branch: `gramps-project/gramps @ maintenance/gramps61` (blob
`0d9e1489084464fcea577aa8152f2338cc3b3a72`). All line citations below are on that branch.

## Root cause

`StyledTextBuffer._apply_style_to_selection` (`gramps/gui/widgets/styledtextbuffer.py:467`)
handles a value-typed style (str / int) by:

```
gramps/gui/widgets/styledtextbuffer.py:476-483
    elif ... == str:
        tag = self._find_tag_by_name(style, value)
        self._remove_style_from_selection(style)
        self._apply_tag_to_selection(tag)        # <-- unconditional
    elif ... == int:
        tag = self._find_tag_by_name(style, value)
        self._remove_style_from_selection(style)
        self._apply_tag_to_selection(tag)        # <-- unconditional
```

It removes any prior tag for the style, then **unconditionally** applies a fresh explicit
tag — even when `value == StyledTextTagType.STYLE_DEFAULT[style]` (FONTSIZE default = 10,
`gramps/gen/lib/styledtexttagtype.py:99`). So setting a note's font size to 12 and back to
10 leaves an explicit `FONTSIZE=10` `StyledTextTag` in the stored `StyledText`. In the
editor this looks correct, but docgens treat that tag as an *absolute* size override on top
of the report's Preformatted paragraph style (whose Normal size may be 12 — Mantis
0003214:0010776/0010784), so the rendered size differs from a note that was never touched,
and the user has no way back to "unset".

The buffer already knows the right invariant everywhere else it writes value-styles:

- `clear_selection` removes a style tag **only** when `value != STYLE_DEFAULT[style]`
  (`gramps/gui/widgets/styledtextbuffer.py:519-523`).
- `after_insert_text` re-applies a style to freshly typed text **only** when
  `value and value != STYLE_DEFAULT[style]` (`gramps/gui/widgets/styledtextbuffer.py:354-357`).

The apply path was the one place that broke the invariant.

## The fix (Invariant to restore, not smallest-diff)

The brief names an **Invariant to restore**, so the target is the smallest change that
restores it — not the smallest textual diff. Guard the tag application in *both* the `str`
and `int` branches on `value != STYLE_DEFAULT[style]`, after removing any prior tag:

```
gramps/gui/widgets/styledtextbuffer.py:476-483 (patched)
    elif ... == str:
        self._remove_style_from_selection(style)
        if value != StyledTextTagType.STYLE_DEFAULT[style]:
            self._apply_tag_to_selection(self._find_tag_by_name(style, value))
    elif ... == int:
        self._remove_style_from_selection(style)
        if value != StyledTextTagType.STYLE_DEFAULT[style]:
            self._apply_tag_to_selection(self._find_tag_by_name(style, value))
```

- `_find_tag_by_name` moved *inside* the guard: it creates a tag in the tag table as a side
  effect, so skipping it when the value is the default avoids fabricating an unused default
  tag. Reordering it after `_remove_style_from_selection` is safe — removal operates on tags
  applied to the *selection*, not on tag-table registration, so find-then-remove and
  remove-then-find are equivalent.
- `self.style_state[style] = value` at the end (`:488`) is unchanged: the state still records
  10, exactly as the constructor initialises it from `STYLE_DEFAULT`
  (`gramps/gui/widgets/styledtextbuffer.py:310`) — consistent with the `clear_selection` /
  `after_insert_text` guards that compare against `STYLE_DEFAULT`.

The `str` branch is included per the brief's Scope ("and, for consistency, str"): the same
absolute-override bug applies to FONTFACE / FONTCOLOR / HIGHLIGHT. The `bool` branch is
untouched (out of scope; it has no non-default explicit tag to leak — it removes the tag when
falsy). The docgen absolute-size handling is out of scope and correct once no explicit
default tag is written.

## Alternatives considered

1. **Fix in the docgens** (make each `docgen` ignore an explicit size equal to the paragraph
   style default). Rejected: the defect is in the tag model, not rendering — the stored
   `StyledText` is wrong at the source. It would need a change in *every* docgen that reads
   FONTSIZE absolutely (e.g. `gramps/plugins/docgen/latexdoc.py`, `htmldoc.py`, `odfdoc.py`,
   `pdfdoc.py`, `rtfdoc.py`, `svgdrawdoc.py`, `cairodoc.py` …) — ~7 files vs. this 8-line,
   1-file guard — and would leave the note data still carrying a spurious override that a
   *future* reader would also have to special-case. The one-file guard fixes the cause; the
   docgen route guards a symptom in N places.

2. **Post-process in `set_text`/`get_text`** to strip default-valued tags. Rejected: it would
   mask (not prevent) the write, run on every serialise, and diverge from where the other two
   write-paths (`clear_selection`, `after_insert_text`) already enforce the invariant. Larger
   surface, weaker fix.

3. **Compare in `_find_tag_by_name` / `_apply_tag_to_selection`** (make them no-op on default).
   Rejected: those helpers are shared by the `bool` path and by `set_text`'s tag rebuild
   (`:615`), where a default value can legitimately need a tag object; overloading them with
   default-suppression would change unrelated call sites.

## Test — headless, drives production

`gramps/gui/widgets/test/styledtextbuffer_test.py` (new; `test/` package already exists on
gramps61 with `__init__.py`, so none is added). It drives the **production public apply path**
`StyledTextBuffer.apply_style` → `_apply_style_to_selection` on a real buffer and inspects the
resulting `StyledText.get_tags()` — no parallel copy of the logic.

Headless-safety: a `StyledTextBuffer` is a `Gtk.TextBuffer` subclass (a `GObject`, **not** a
widget), so it constructs with no display / main loop / X server. Verified by instantiating it
and exercising `apply_style` with `DISPLAY`/`WAYLAND_DISPLAY` unset. The module pins
`gi.require_version("Gtk", "3.0")` before importing the buffer — the same pattern the existing
sibling test `gramps/gui/widgets/test/selectionwidget_test.py:55-57` uses — so it loads against
the GTK 3 ABI the widgets package requires.

Tests:
- `test_fontsize_default_leaves_no_explicit_tag` — the Mantis 3214 sequence (12 → 10): asserts
  no FONTSIZE tag remains. **This is the Success criterion.**
- `test_fontsize_default_matches_untouched_note` — a back-to-default note has *identical* tags
  to a note whose size was never changed (the Invariant, stated directly).
- `test_fontsize_nondefault_still_tagged` — a genuine non-default size (12) is still recorded
  (no over-removal); this test passes on *both* legs, guarding against a fix that just deletes
  all FONTSIZE tags.
- `test_fontface_default_leaves_no_explicit_tag` — the `str` branch upholds the same invariant.

## Red → green evidence

Verified locally against a **clean** `upstream/maintenance/gramps61` worktree (the shared C4
worktree `gramps-6.1` was dirty with an unrelated bundle's changes, so I used a throwaway
`git worktree` off the same ref and removed it after — I did not disturb the other bundle).
The mechanic mirrors C4-core (plain `python3 -m unittest`, no display; GTK pinned to 3.0 on
this host, which also has GTK 4 — the C4 container defaults to GTK 3 so no pin is needed
there):

- Patch applied → `git apply --check` clean; all 4 tests **PASS**.
- Production change reverted, test kept → 3 of 4 tests **FAIL** (the default-clearing ones);
  the non-default control still passes. This is the C4 red→green contract
  (green-with-fix AND red-without-fix).

`run-verify.sh` itself was not run because its pinned `gramps-6.1` worktree currently holds
another bundle's uncommitted changes (`git diff --quiet` would make it refuse); the C4 gate in
Check will run it on a clean worktree.

## POTFILES registration & formatting

- New core `.py` with no translatable strings (a test) → added to `po/POTFILES.skip` in the
  existing `gramps/gui/widgets/test` block (`patch.diff` hunk on `po/POTFILES.skip:515`),
  alphabetically after `selectionwidget_test.py`. Satisfies the T2-potfiles MUST.
- No file is removed, so no POTFILES deletion is needed.
- Formatting: `black` is not installed in this environment and a network install needs
  approval, so I could not run it. Both touched files were written in black style (double
  quotes, trailing commas, ≤88 cols — verified no line exceeds 88) and the one multi-line
  assertion message was refactored into a parenthesised string literal to avoid any black
  reflow ambiguity. **The human/Check should run `black` (gramps' pre-commit hook) over the
  two files before publish to be certain** — I could not mechanically confirm it here.
