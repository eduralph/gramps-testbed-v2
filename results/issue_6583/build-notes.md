# Build notes — issue 6583 / verify-toolbar-label-ellipsis-gone

**Disposition: FIX (text-only). Iteration 3.** This iteration corrects the over-broad
Iteration-2 patch per the sign-off carry-forward.

## What the carry-forwards established

- **Iteration 1** ("verify → WONTFIX/by-design") was rejected: maintainer Nick H agreed the
  toolbar ellipses should go per the GNOME HIG. → produce a fix.
- **Iteration 2** stripped the ellipsis from **all three** of Add / Edit / Merge uniformly.
  That was rejected: the HIG ellipsis rule is *semantic*, not "make them all the same".
  Per GNOME HIG the trailing ellipsis means **"this command needs further input from the
  user before it can act"** (Input Required), and is dropped when the command opens a
  state/properties window or fires immediately. Applied to the three labels:
  - **Add** → opens a dialog to create a *new* record (Input Required) → **keep `Add...`**
  - **Edit** → opens the *existing* record in its editor (state/info window) → **drop to `Edit`** ✓
  - **Merge** → opens a dialog where the user chooses which fields to keep (Input Required)
    → **keep `Merge...`**
  Only the Edit change was correct.

## This iteration — the change

Drop the trailing ellipsis from the **Edit action label only**, across the 11 list /
category / relationship view source files. `Add...`, `_Merge...`, and the other
input-required Add-family labels are left **untouched** — they correctly keep their
ellipsis. The result is a *semantically consistent* toolbar (the invariant the brief asks
to restore): ellipsis iff the action needs further input before it acts. Edit now matches
`_Delete`/`Remove` (both act on the selected row without asking for new input).

### Per-file (path:line on target `upstream/maintenance/gramps61`, file
`gramps/plugins/lib/libpersonview.py` representative)

The user-visible label for `win.Edit` appears three times per list view and is the only
thing changed:
- `:271` `""" % _("_Edit...", "action")` → `_("_Edit", "action")` — the sgettext `%s` that
  fills the `CommonEdit` **menu** Edit item.
- `:348` toolbar `GtkToolButton` `<property name="label">Edit...</property>` → `Edit`.
- `:430` `% _("_Edit...", "action")` → `_("_Edit", "action")` — the sgettext `%s` that
  fills the right-click **popup** Edit item.

The identical 3-site change is applied in `libplaceview.py`, `citationlistview.py`,
`citationtreeview.py`, `eventview.py`, `familyview.py`, `mediaview.py`, `noteview.py`,
`repoview.py`, `sourceview.py`. `relview.py` carries the Edit label twice (the `win.Edit`
popup `<attribute name="label">Edit...` at `:414` and the toolbar `<property
name="label">Edit...` at `:504`) — both → `Edit`. Total: **32** label sites, Edit only.

Mechanically the change is a literal `Edit...` → `Edit` substitution scoped to these 11
files: `_("_Edit...", "action")` carries `Edit...` as a substring, so the same
substitution updates the `_Edit...` msgid to `_Edit` and the bare `Edit...` toolbar
literals together, and touches nothing else (verified: the only `Edit...` occurrences in
these files were Edit labels — `grep -n 'Edit\.\.\.'`).

### "Check all other labels for the same rule" (carry-forward instruction)

The other ellipsis labels in these toolbars were audited against the Input-Required rule
and **correctly keep their ellipsis** (so are NOT changed):
- `_Add...` (every list view) — opens a blank editor to create a new record → Input Required.
- `_Merge...` (every list view) — opens the merge dialog to pick fields → Input Required.
- `Add source...` / `Add citation...` (`citationtreeview.py`) — open a new-record editor → Input Required.
- `Add Partner...`, `Add New Parents...`, `Add Existing Parents...` (`relview.py`) — open an
  editor / selector before acting → Input Required.

Out of scope per the brief and unrelated to the report (left untouched): `Export View...`,
the bookmark `%s...` / `Organize Bookmarks...` labels, tooltips, icon choice, column/format
labels.

## Test (red→green, headless-safe) — `gramps/plugins/test/toolbar_label_ellipsis_test.py`

The C4 runner is headless: importing any view module pulls in `gramps.gui` / `gi` and would
crash it. The test imports **nothing** from gramps — it reads each view's source file
(resolved via `__file__`, two dirs up, so it audits the *production* `additional_ui`
strings, not a copy) and, for each file, extracts every **Edit** label in its two
representations (the `name="label">...` XML value and the `_("...", "action")` sgettext
form) and asserts none ends with `...`. These labels are static source-string literals;
there is no runtime logic to route through, so reading the source *is* exercising the
production artifact and the test cannot drift from what ships.

A second test (`test_finds_the_edit_labels_at_all`) guards against vacuous success: it
asserts the parser actually finds ≥1 Edit label in every listed file, so a parser-drift
that silently matched nothing could not make the ellipsis assertion pass empty.

The test is deliberately **Edit-scoped** (it does not assert on Add/Merge): asserting that
Add/Merge *retain* `...` would lock in unchanged state and over-reach; the regression
contract here is precisely "Edit lost its ellipsis", which is what is proven red→green.

Proven red→green (the Docker `run-verify.sh` is sandbox-blocked in this Do environment;
the test is import-free so a plain `python3 -m unittest` run against the `gramps-6.1-lane0`
worktree is faithful, and the C4 gate will re-run it in Docker):
- **GREEN** with the full patch: `Ran 2 tests … OK`.
- **RED** with the 11 production files reverted (test kept): `FAILED` listing **32**
  offending Edit labels across all eleven files — the test genuinely catches the bug.

## POTFILES

New core test file has no translatable strings → registered in `po/POTFILES.skip`
(`gramps/plugins/test/toolbar_label_ellipsis_test.py`, inserted alphabetically in the
`plugins/test` block, doc 16 §Adding and removing Python files). No file removed; no
`POTFILES.in` change. The changed msgid `_Edit...` → `_Edit` is expected i18n churn for a
label change; `_Edit` already exists as a msgid elsewhere, so most translations carry over.

## Commit-readiness

`black --check` on all 12 touched `.py` files exits 0 (gramps's commit hook runs black; the
patch passes it). `git apply --check` of `patch.diff` against the unpatched
`upstream/maintenance/gramps61` checkout applies all 13 files cleanly. The diff is scoped to
exactly the intended 13 files (11 views + test + `po/POTFILES.skip`), 158 insertions /
32 deletions, no unrelated worktree leftovers.

## Alternatives considered / ruled out

- **Re-submit Iteration-2's uniform "strip all three" patch.** Rejected — explicitly
  overruled at sign-off; the HIG rule is semantic (Input-Required keeps the ellipsis), and
  Add/Merge are Input-Required. Re-submitting the rejected approach unchanged is forbidden.
- **Re-submit Iteration-1's WONTFIX close.** Rejected — overruled at Iteration 1.
- **Also strip the ellipsis from the matching Add/Merge menu/popup copies** to make the
  whole CommonEdit section bare. Rejected — that is the very over-reach Iteration 2 was
  bounced for; Add/Merge are Input-Required and must keep `...` in *every* presentation, so
  consistency means "Edit bare everywhere, Add/Merge ellipsised everywhere", which is
  exactly what this patch produces (the single shared `_("_Edit…","action")` msgid feeds
  both menu and popup, so Edit is uniform without splitting any label).
- **Add `...` to `_Delete` instead, to make Edit/Delete uniform the other way.** Rejected —
  contradicts the HIG (a confirm-only/immediate action takes no ellipsis) and the
  maintainer's stated direction.

## Files

- `patch.diff` — 11 view files (Edit label text only) + new test + `po/POTFILES.skip`.
- `toolbar_label_ellipsis_test.py` — standalone copy of the shipped regression test.
- `build-notes.md` — this file (withheld from the reviewer).
