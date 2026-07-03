## Summary

**User-visible symptom:** When viewing a hyperlink in a Gramps Note (read-only view), clicking in the empty area beside or below the link causes the browser to open the URL, even though the click never landed on the link itself.

**Root cause:** `Gtk.TextView.get_iter_at_location()` returns the nearest character position for any point, including clicks past the end of a line or below the last line. The Note editor treats that snapped position as a hit and opens the link.

**One-line fix:** Verify the pointer is actually within the rendered glyph of the character at the snapped position before treating it as a link match.

## What to look at

**File:** `gramps/gui/widgets/styledtexteditor.py`

**Key methods:**
- `on_motion_notify_event()` (lines 424–456) — sets `self.match` based on URL regexp and link tags
- `on_button_press_event()` (lines 501–516) — opens the link when `self.url_match` is set and conditions are met
- `do_match_changed()` (called via "match-changed" signal) — updates cursor and match state

**To reproduce:** Open Gramps on `maintenance/gramps61`, create a Note, paste a URL on its own line, save it, and reopen it in read-only view. Click in the empty area below or to the right of the URL — **before the fix**, the browser opens; **after the fix**, the empty-area click does nothing.

## Root cause / Fix

`get_iter_at_location(x, y)` is a GTK3 API that returns the "nearest" text iterator for any point, including a click in the empty area beside/below text — it never returns "no iter". The returned position is then used directly to look up URLs and link tags, so an empty-area click snaps to the end of the text and opens the link if one ends there.

The fix adds a new private method `_pointer_over_iter(x, y, text_iter)` that uses `get_iter_location()` to confirm the point `(x, y)` is genuinely inside a character's bounding rectangle. Because `get_iter_at_location()` **advances past a glyph when the click lands in that glyph's trailing (right) half** (it adds Pango's trailing count), the character under the pointer may be the one *before* `text_iter`; the helper therefore checks the rectangle of the char at the iter **and**, on a miss, the char immediately before it. That keeps a genuine click on a link glyph's right half opening the link, while a click in the empty area beside/below the text — where neither the snapped char nor its predecessor contains the point — is rejected. Both the URL regexp match path (`match_check()`) and the internal link tag loop are guarded by this check:

```python
if self._pointer_over_iter(x, y, iter_at_location):
    self.match = self.textbuffer.match_check(...)
    ... link-tag loop ...
else:
    self.match = None
```

This ensures that:
- A click to the right of the URL on its line → excluded (past the last glyph's rectangle).
- A click below the last line → excluded (below every line's rectangle).
- A click anywhere on the URL glyph, left or right half → still matches (point inside the char's or its predecessor's rectangle → link still opens via the view-mode / Ctrl+click gesture).

Both URL matches and internal link tags are guarded, so neither hyperlink flavour can open on an empty-area click, and neither is lost on a real on-glyph click.

## Verified against

**Code review trail:**

| Claim | Evidence (path:lines on `maintenance/gramps61`) |
| --- | --- |
| Root cause: `get_iter_at_location()` snaps even for out-of-bounds clicks | `gramps/gui/widgets/styledtexteditor.py:435` sets `iter_at_location` from user click; GTK3 docs and `match_check` behavior confirm nearest-iter semantics |
| Fix gates URL matches | `gramps/gui/widgets/styledtexteditor.py:28` (patched): URL `match_check()` now inside `if self._pointer_over_iter()` block |
| Fix gates internal link tags | `gramps/gui/widgets/styledtexteditor.py:30–38` (patched): link-tag loop now inside same `if` block |
| Fix clears match for out-of-bounds clicks | `gramps/gui/widgets/styledtexteditor.py:39–41` (patched): `else` clause sets `self.match = None` |
| New helper checks glyph bounds (both the snapped char and its predecessor) | `_pointer_over_iter()` (patched): `get_iter_location()` confirms the point is inside the char at the iter or, on a miss, the char before it — covering the trailing-half advance of `get_iter_at_location()` so a real click on a link glyph's right half still opens the link |
| Signal consumption path is unbroken | `gramps/gui/widgets/styledtexteditor.py:450–451` (patched, unchanged): "match-changed" signal still emitted when `self.match` changes; `do_match_changed()` still updates `self.url_match` (line 404, preimage) |
| Button press still opens when match is set | `gramps/gui/widgets/styledtexteditor.py:511–516` (preimage): `on_button_press_event()` consumes `self.url_match` and calls `_open_url_cb()` only when set |

## Test

No core unit test ships in this patch — the behaviour is a GUI hit-test, not headless-testable. Coverage is a committed AT-SPI/dogtail repro in the gramps-testbed harness (not part of this PR), `engine/interface/test_bug_0008841_note_link_hittest.py`, exercising red without the fix and green with it:
- **Before fix:** an empty-area click snaps to the end of the URL, `match_check()` includes that end offset, so `self.match` is set, the non-editable view calls `_open_url_cb()` to open the browser, and the test's "does not open" assertion fails (red).
- **After fix:** `_pointer_over_iter()` returns False for the out-of-bounds point, `self.match` stays None, no browser launch occurs, and the assertion passes (green). On-glyph clicks still match → positive assertion passes both legs.

---

Fixes [#8841](https://gramps-project.org/bugs/view.php?id=8841)
