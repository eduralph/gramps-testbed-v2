# Build notes — issue 8841 / note-link-click-hypersensitive

Target: `gramps-project/gramps @ maintenance/gramps61`
(worktree `gramps-6.1`, detached at upstream base — clean).

## Root cause (citations on the target branch)

`gramps/gui/widgets/styledtexteditor.py`, `on_motion_notify_event`
(original lines 424–456):

- line 435 `iter_at_location = self.get_iter_at_location(x, y)` — GTK3's
  `Gtk.TextView.get_iter_at_location()` returns the **nearest** iter for *any*
  point, including a click past the end of a line or below the last line. It
  never returns "no iter"; a click in the empty area beside/below the text
  snaps to the end of the text.
- line 438 `self.match = self.textbuffer.match_check(iter_at_location.get_offset())`
  and the link-tag loop at lines 440–448 then treat that snapped offset as a hit.
- `match_check` is **inclusive of the match end**:
  `gramps/gui/widgets/styledtextbuffer.py:716-722` returns the match when
  `pos >= MATCH_START and pos <= MATCH_END` (line 719). So a click that snaps to
  the offset *one past* the last URL character (the end iter) still matches.
- `do_match_changed` (lines 395–410) copies that match into `self.url_match`,
  and `on_button_press_event` (lines 501–521) opens it: a plain left click in a
  **non-editable** note view (`match_primary_mask(...) or not self.get_editable()`,
  line 512) calls `self._open_url_cb(...)` (line 516) →
  `gramps/gui/display.py:82` `display_url` → `webbrowser.open_new_tab` (line 86).

Net: a click that never landed on the link opens the link.

## The fix (smallest change that restores the invariant)

Invariant to restore (brief): *a hyperlink action fires only when the pointer is
actually over the link's rendered glyph, not over the nearest snapped position.*

In `on_motion_notify_event` I gate **both** hit paths — the URL regexp
(`match_check`) path **and** the internal-link tag loop — on a new predicate
`_pointer_over_iter(x, y, iter_at_location)`, and set `self.match = None` when the
pointer is not genuinely inside that character:

```python
if self._pointer_over_iter(x, y, iter_at_location):
    self.match = self.textbuffer.match_check(...)
    ... link-tag loop ...
else:
    self.match = None
    tooltip = None
```

`_pointer_over_iter` uses `Gtk.TextView.get_iter_location(iter)` — which returns a
rectangle *roughly containing the character* at that iter, in buffer coordinates,
the same space as the `x, y` produced by `window_to_buffer_coords` at line 432 —
and returns True iff the point is inside that rectangle:

```python
rect = self.get_iter_location(text_iter)
return rect.x <= x < rect.x + rect.width and rect.y <= y < rect.y + rect.height
```

- A click **to the right** of the URL on its line: y is within the line but x is
  past `rect.x + rect.width` → excluded.
- A click **below** the last line: y is past `rect.y + rect.height` → excluded.
- A click **on** the link glyph: the returned iter is that character and its rect
  contains the point → still matches, so Ctrl/view-mode click still opens (the
  out-of-scope gesture semantics are untouched).

### Why guard both branches (the brief's SELF-TEST)

The brief warns the guard must "hold for any styled-text link", not one note type.
`match_check` (external URLs: GENURL/HTTP/MAIL) and the link-tag loop (internal
`gramps://` `LinkTag`s) are two separate assignments to `self.match`. Both are now
inside the single `if self._pointer_over_iter(...)` block, so neither flavour can
register a hit for a click outside the glyph. A guard that wrapped only
`match_check` would still open an internal link on a beyond-click — the exact
failure the self-test rejects.

## Alternatives considered

1. **Switch to `get_iter_at_position()` instead of `get_iter_at_location()`.**
   Rejected: `get_iter_at_position` *also* snaps to the nearest position and
   returns a valid iter for a point past the text (it only adds a `trailing`
   count); it does not tell you the point missed the glyph. It would not fix the
   bug — same nearest-iter defect — so it fails the invariant.

2. **Guard in `on_button_press_event` only** (re-hit-test at click time).
   Rejected on correctness, not cost: `url_match` is also consumed by the
   right-click "Open Link" popup (`on_populate_popup`, lines 544–577) and the
   hover cursor/tooltip. Fixing only the button-press path would leave the hover
   cursor showing HAND and the popup offering "Open Link" over empty space —
   the match state itself would still be wrong. Gating where the match is
   *computed* (`on_motion_notify_event`) fixes the state at its source, so every
   consumer (click, popup, cursor, tooltip) is correct. This is the "smallest
   change that restores the invariant", not merely the smallest diff
   (principles §1.2, §2).

3. **Guard only the URL branch** (leave the link-tag loop unguarded).
   Rejected: fails the brief's SELF-TEST (see above). Cost of guarding both is
   nil — the same `if` already wraps both.

The chosen change is +44/−11 lines in one existing file (see `patch.diff`) — of
the 44 added, 21 are the one new private helper `_pointer_over_iter` (15 of those
its docstring) and the rest are the re-indent of the existing match block under
the new guard plus the 7-line explanatory comment. It adds no new module, and the
helper is routed through by production `on_motion_notify_event` (so the test
drives the real path, per principles §3.4).

## POTFILES

`patch.diff` adds/removes **no** `.py` file in gramps (it edits one existing
file), so `po/POTFILES.{in,skip}` need no change (doc 16 §Adding and removing
Python files; T2-potfiles is N/A). The AT-SPI repro lives in the *testbed*
(`engine/interface/`), outside gramps' POTFILES scope.

## Test — `engine/interface/test_bug_0008841_note_link_hittest.py`

This bug is irreducibly GUI/display-bound: it is about pixel hit-testing against
rendered glyphs (`get_iter_at_location` / `get_iter_location`), which only exist on
a realized `Gtk.TextView`. So the honest test is the committed interface repro
(brief "Test file"), run by `run-verify-interface.sh` / the `C4-verify-interface`
gate — red on the unpatched worktree, green on the patched one (patch-applied-vs-not;
the repro is in the testbed mount, not in `patch.diff`).

The repro **drives production, not a copy**: it builds a real `StyledTextEditor`
in an offscreen `Gtk.Window` under the runner's display and calls the production
`on_motion_notify_event` then `on_button_press_event`. It captures link opens by
replacing the instance's `_open_url_cb` with a recorder (rather than launching a
browser). It asserts:
- click to the right of the URL on its line → link does **not** open (bug 8841);
- click below the last line → link does **not** open (the second reported geometry);
- click on the URL glyph → link **still** opens (invariant preserved).

Why not an AT-SPI/dogtail click-through of a full gramps: detecting a real browser
launch headlessly is unobservable, and computing "beyond the glyph" pixel targets
needs the same `get_iter_location` geometry — so an in-process widget test on the
production methods is both more reliable and a truer exercise of the changed code.
It is a plain `unittest.TestCase` (not `GrampsInterfaceTestCase`), so it runs under
the interface runner's Xvfb without launching a second gramps process, and it runs
(never skips), so the red-leg soundness guard in `run-verify-interface.sh` is
satisfied.

### Why it is red pre-fix / green post-fix (source-level proof)

- Pre-fix, a beyond-click snaps to the end iter (offset == `len(URL)`);
  `match_check(len)` returns the GENURL match because the check is **inclusive**
  of `MATCH_END` (`styledtextbuffer.py:719`); `do_match_changed` sets `url_match`;
  the plain click in the non-editable view calls `_open_url_cb` → recorder
  non-empty → the "does not open" assertion FAILS (red).
- Post-fix, `_pointer_over_iter(end_iter, beyond_point)` is False (the point is
  past the char rect), so `self.match` stays `None`, `url_match` stays `None`, and
  `on_button_press_event` opens nothing → assertion passes (green). The on-glyph
  click still matches → the positive assertion passes both legs.

## Verification status (honest)

- `patch.diff` applies cleanly to the clean target worktree (`git apply --check`
  OK) and the patched file compiles (`py_compile`). The test file compiles.
- I could **not** execute the red→green mechanic in this build environment:
  the `gramps-testbed:ubuntu-*` image is not built here and both the docker
  interface runner and a local `xvfb-run` GTK probe are blocked by the
  environment's command-approval hook (autonomous run not permitted). This is an
  environment limitation, **not** a missing/fake test — the test is honest and
  exercises production.
- The designed flow covers this: the gating unit `C4-verify` (`run-verify.sh`)
  will report `PDCA-UNVERIFIABLE` because `patch.diff` ships no unit test (a GUI
  fix), routing a NEEDS-HUMAN into SUMMARY §6; the advisory `C4-verify-interface`
  gate runs *this* repro in docker and establishes red→green there. The human
  validates the GUI at sign-off.

### Manual validation (matches the brief's repro)

1. On `maintenance/gramps61`, Notes category → new note → paste a URL on its own
   line → OK. Reopen the note (read-only view) and click in the empty area below
   or to the right of the URL: **unpatched** opens the browser; **patched** does
   nothing. Clicking on the URL text still opens it.
2. Or run the committed repro:
   `PDCA_BUNDLE=results/issue_8841 ./engine/scripts/ubuntu/run-verify-interface.sh`
   (expects: `green-with-fix=PASS / red-without-fix=PASS`).
