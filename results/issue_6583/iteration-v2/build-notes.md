# Build notes — issue 6583 / verify-toolbar-label-ellipsis-gone

**Disposition: FIX (text-only). Iteration 2.** The Iteration-1 "verify → WONTFIX/
by-design" reading was rejected at sign-off: maintainer Nick H (tracker ~0028219)
concluded "it looks like we should remove the ellipsis from the toolbar buttons" per the
GNOME HIG toolbar rule the reporter cited (~0028215): *"For buttons that correspond
directly to menu items, make the text label the same as the menu item, but without any
trailing ellipsis."* This iteration ships that change: strip the trailing `...` from the
Add / Edit / Merge (and their relationship/citation siblings: Add source / Add citation /
Add Partner / Add New Parents / Add Existing Parents) toolbar-button labels and their
matching menu / popup label entries across the list / category / relationship views.

## Root cause (two sentences)

The user-visible labels for the `win.Add` / `win.Edit` / `win.Merge` actions are defined
as literal `additional_ui` UI-XML strings in each view file (a `GtkToolButton`
`<property name="label">` for the toolbar, and `<attribute name="label">` for the menu /
right-click-popup items) — **not** in the base `listview.py` (which only registers bare
action *names*, which is why the Iteration-1 grep of `listview.py` came up vacuously
"clean"). Those label strings carried `...` on Add/Edit/Merge while `Remove`/`_Delete`
did not, producing the inconsistent toolbar the reporter screenshotted.

## What changed (path:line on target `upstream/maintenance/gramps61`)

Eleven view source files, label strings only (no logic, no handler, no action-name
change). Representative sites in `gramps/plugins/lib/libpersonview.py`:
- toolbar `GtkToolButton` labels: `:336` `_Add...`→`_Add`, `:348` `Edit...`→`Edit`,
  `:372` `_Merge...`→`_Merge`.
- `CommonEdit` menu section: `:256` `_Add...`→`_Add`, `:268` `_Merge...`→`_Merge`, and the
  shared Edit label `:271` `_("_Edit...", "action")`→`_("_Edit", "action")` (an sgettext
  `%s` filled into both the menu and the popup Edit item).
- right-click `Popup` menu: `:407` `_Add...`→`_Add`, `:419` `_Merge...`→`_Merge`, `:430`
  `_("_Edit...", "action")`→`_("_Edit", "action")`.

The identical pattern is applied in the other ten files:
`libplaceview.py`, `citationlistview.py`, `citationtreeview.py`, `eventview.py`,
`familyview.py`, `mediaview.py`, `noteview.py`, `repoview.py`, `sourceview.py`,
`relview.py`. `citationtreeview.py` additionally drops `...` from `Add source...` /
`Add citation...` (`:369,373,447,458` and the line-`:534` concatenated `"""Add
citation...`); `relview.py` from `Edit...` (`:414,504`), `Add New Parents...` (`:419`),
`Add Existing Parents...` (`:424`), `Add Partner...` (`:428`).

**Deliberately left untouched** (out of scope per the brief; not Add/Edit/Merge, and these
are not the reported inconsistency): `Export View...`, the bookmark `%s...` / `Organize
Bookmarks...` labels, and `_Delete`/`Remove` (which correctly never carried an ellipsis).

## Toolbar *and* matching menu/popup — per the carry-forward, and why it is consistent

The carry-forward directs removing `...` from "the Add/Edit/Merge toolbar button labels
**and their matching popup/menu label entries**". I followed that. In gramps61 the same
label string is reused across a view's toolbar button, its `CommonEdit` menu section, and
its right-click `Popup` (and for Edit a single `_("_Edit...", "action")` literally feeds
all three) — so stripping the ellipsis uniformly is what *restores the brief's invariant*
("applied uniformly, not arbitrarily on some buttons and not others"): every Add/Edit/
Merge presentation now reads without `...`, matching `_Delete`. Leaving the menu copies
with `...` while the toolbar lost it would re-introduce an inconsistency within the same
action.

## Test (red→green, headless-safe) — `gramps/plugins/test/toolbar_label_ellipsis_test.py`

The C4 runner is headless: importing any of these view modules pulls in `gramps.gui` / `gi`
and would crash it. The test therefore imports **nothing** from gramps — it reads each
view's source file (resolved via `__file__`, so it audits the *production* `additional_ui`
strings, not a copy), extracts every `name="label"` value and every `_(... , "action")`
sgettext label, and asserts that none in the Add/Edit/Merge/Partner family ends with
`...`. This is the production artifact itself (the labels are static source strings; there
is no runtime logic to route through), so the test cannot drift from what ships.

Proven via `git apply patch.diff` + running the test file as a script against the
`gramps-6.1` worktree (the Docker `run-verify.sh` is sandbox-blocked in this Do
environment; the test is import-free so a plain `python3` run is faithful and the C4 gate
will re-run it in Docker):
- **GREEN** with the full patch: `Ran 1 test … OK`.
- **RED** with the production change reverted (test kept): `FAILED` with **100** offending
  labels listed across all eleven files — the test genuinely catches the bug.

The first red→green attempt this iteration surfaced a real miss the suffix-anchored test
caught: `citationtreeview.py:534` defines `Add citation...` split across Python string
concatenation (`...>"""` newline `"""Add citation...`), which my initial `>`-anchored
replacement skipped; the replacements were switched to closing-tag-anchored
(`Add citation...</attribute>`) to catch it, and the scan now reports zero offenders.

## POTFILES

New core test file has no translatable strings → registered in `po/POTFILES.skip`
(`gramps/plugins/test/toolbar_label_ellipsis_test.py`, inserted alphabetically in the
`plugins/test` block, doc 16 §Adding and removing Python files). No file is removed. No
`POTFILES.in` change. (Note: the changed msgids `_Add...`→`_Add`, `_Edit...`→`_Edit`,
`_Merge...`→`_Merge` etc. are i18n string churn, expected for a label change; the
ellipsis-free forms already exist as msgids elsewhere, so most translations carry over.)

## Commit-readiness

`black --check` on all 12 touched `.py` files: "12 files would be left unchanged"
(gramps's commit hook runs black; the patch passes it). The patch is scoped to exactly the
13 intended files (11 views + test + POTFILES.skip) — verified the diff carries no
unrelated worktree leftovers.

## Alternatives considered / ruled out

- **Re-submit Iteration-1's WONTFIX / by-design close.** Rejected — explicitly overruled by
  the sign-off carry-forward (maintainer agreed the ellipses should go); re-submitting the
  rejected approach unchanged is forbidden.
- **Strip `...` from the toolbar buttons only, keep it on the menu items** (strict reading
  of the HIG, which keeps ellipsis on menu items). Rejected for this codebase: Gramps reuses
  one label string across toolbar + menu + popup (Edit is literally one
  `_("_Edit...", "action")` feeding all three), so a toolbar-only strip is not even
  expressible without *splitting* each shared label into two msgids — a larger, churnier
  change — and it would leave the menu/popup Add/Edit/Merge inconsistent with the now-bare
  toolbar, contradicting the brief's "applied uniformly" invariant and the carry-forward's
  explicit "and their matching popup/menu label entries".
- **Add `...` to `_Delete` to make them uniform the other way.** Rejected — contradicts the
  HIG (a confirm-only action takes no ellipsis) and the maintainer's stated direction.

## Files

- `patch.diff` — 11 view files (label text only) + new test + `po/POTFILES.skip`.
- `toolbar_label_ellipsis_test.py` — standalone copy of the shipped regression test.
- `build-notes.md` — this file (withheld from the reviewer).
