# Brief — issue 10604 / docreportdialog-css-keyerror-minus-one

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** docreportdialog-css-keyerror-minus-one
- **Defect:** As filed (v4.2.8): running an HTML/graph report whose CSS list comes from the
  Webstuff plugin crashes with `KeyError: -1` at `_docreportdialog.py … self.CSS[
  self.css_combo.get_active()]["filename"]` when the user has hidden the Webstuff plugin via
  the Plugin Manager — the CSS combo is empty, `get_active()` returns `-1`, and indexing the
  CSS map with `-1` fails.
- **Success criterion:** Confirming an HTML report dialog when no CSS is selectable (the
  Webstuff plugin hidden / empty CSS list) does **not** raise `KeyError: -1` — the empty /
  no-active-item state is tolerated. **Verify-first**: Do MUST reproduce on
  maintenance/gramps61 before writing any production change.
- **Invariant to restore:** A combo-box-driven selection tolerates the empty / "no active
  item" (`get_active() == -1`) state without indexing the backing map by `-1`. (Internal GUI
  robustness rule; behavioural, not a structural/lifecycle category.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Scope:** the CSS-selection read in `gramps/gui/plug/report/_docreportdialog.py`.
  **Likely already fixed:** `parse_html_frame` now guards the `-1` case explicitly —
  `_docreportdialog.py:274-279` reads `active = self.css_combo.get_active()`, substitutes
  `self.style_name` when `active == -1` ("legal for 'no active item' (see 7585, 8189, 9461)"),
  and only indexes when `if self.css:`. That guard was added 2016 (`5f1b719810`), long before
  the maintenance/gramps61 base, so the reported crash path appears closed. Do should confirm
  the Webstuff-hidden / empty-CSS scenario no longer raises; if it cannot be reproduced, route
  to §6 NEEDS-HUMAN (likely-close) — do not manufacture a change. / out of scope: redesigning
  the CSS combo population or the Webstuff plugin.
- **Repro instruction:** On maintenance/gramps61: Help → Plugin Manager → Hide the "Webstuff"
  plugin; restart; run a report that offers an HTML/CSS document option (e.g. a graph/HTML
  report) and click OK with no CSS selectable. Observe whether `KeyError: -1` still occurs.
- **Test file:** gramps/gui/plug/report/test/_docreportdialog_test.py — IF a live crash is
  found, a regression test driving the **production** `parse_html_frame` with an empty `self.css`
  / `get_active() == -1` and asserting no exception; new `*_test.py` → `po/POTFILES.skip`. If
  the guard already covers it, no production patch ships and C4 routes to §6 (verify-first
  close). GUI-dialog instantiation may make a headless unit test impractical — then it is a
  manual-verification §6 item.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **Prior-art check (triage cycles):** `git log -S 'legal for "no active item"' --
  gramps/gui/plug/report/_docreportdialog.py` → `5f1b719810` (2016) adds the `active == -1`
  guard referencing the sibling bugs 7585/8189/9461; present in the gramps61 base. Strong
  signal the defect is already resolved.
- **Mantis:** 10604
- **Disposition hint:** POSSIBLY-FIXED → verify first
