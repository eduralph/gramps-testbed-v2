# Brief — issue 8841 / note-link-click-hypersensitive

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** note-link-click-hypersensitive
- **Defect:** In the styled-text Note editor/view, a hyperlink fires "open in browser"
  when the user clicks *beyond* the link — e.g. in the empty area below or to the right of
  the last line — not just on the link glyph. GTK snaps the click to the nearest text
  position (the end of the link), so the link opens repeatedly on clicks that never
  landed on it. Reproduced by RonJohn (XFCE, 4.2.0) and sam888 (Ubuntu/Unity, master).
- **Success criterion:** After the fix, a single click whose position is not actually
  over the link text does NOT open the link; a click on the link text still opens it
  (via the existing Ctrl+click / view-mode gesture). Demonstrable by the committed AT-SPI
  repro: clicking in the empty area beside/below a link in a read-only note does not
  launch the browser (red pre-fix — link opens; green post-fix).
- **Invariant to restore:** A hyperlink action must be triggered only when the pointer is
  actually over the link's rendered text, not over the nearest snapped text position when
  the click falls outside the text. (GTK3 text-view hit-testing rule — a nearest-iter
  lookup returns a position even for clicks past the end of a line/buffer; the link
  decision must confirm the point lies within the character, not merely adjacent to it.)
  SELF-TEST: fails for a guard on one note type — must hold for any styled-text link.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** medium
- **Scope:** The URL-match detection in the styled-text editor resolves the pointer to
  the nearest buffer iter and treats its link tag as a hit, so clicks beyond the text
  register as being on the link and open it. Restrict link activation to clicks whose
  position is genuinely within the link's glyphs. / out of scope: the right-click "Open
  Link" menu, the Ctrl+click gesture semantics, tooltip/hover behaviour beyond the same
  hit-test, and the `_open_url_cb` browser-launch path itself.
- **Repro instruction:** On `maintenance/gramps61`, Notes category → new note → paste a
  URL on its own line → OK. Reopen the note and click in the empty area below or to the
  right of the URL: the browser opens the link.
- **Test file:** `engine/interface/test_bug_0008841_note_link_hittest.py` (committed
  AT-SPI/dogtail repro in the testbed; NOT in `patch.diff`). Red on the unpatched
  worktree, green on the patched one. If Do extracts a hit-test seam, production must
  route through the same unit the test drives (principles §3.4).
- **Citations expected:** Do must cite path:line on the target branch for every change
  (root cause: `gramps/gui/widgets/styledtexteditor.py:435` `on_motion_notify_event`
  using `get_iter_at_location(x, y)` to set `self.match`/`url_match`, consumed by
  `styledtexteditor.py:501-516` `on_button_press_event`).
- **New/removed files:** none in gramps — `patch.diff` modifies existing files only; the
  AT-SPI repro ships in the testbed `engine/interface/`, outside gramps' POTFILES scope.
- **Prior-art check (triage cycles):** searched `gramps/gui/widgets/styledtexteditor.py`
  on `upstream/maintenance/gramps61` — only https/black/license/spellcheck-teardown
  churn, no link hit-test fix; no open/closed PR found on this path. Not already
  upstream.
- **Mantis:** 8841
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. A draft PR MAY be opened for CI; it MUST NOT be marked
ready before sign-off accepts.
