# Brief — issue 6583 / verify-toolbar-label-ellipsis-gone

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** verify-toolbar-label-ellipsis-gone
- **Defect:** Reported (v4.0.0): list-view toolbar buttons were labelled "Add…",
  "Merge…", "Edit…" (trailing ellipsis) alongside "Remove" (no ellipsis) — inconsistent,
  and the ellipsis cluttered the button bar.
- **Success criterion:** On `maintenance/gramps61`, confirm the list-view toolbar no
  longer presents inconsistent trailing-ellipsis button labels — the Add/Edit/Merge/Remove
  toolbar controls do not carry the "…" the report describes. Verification, not a new fix
  (no patch if confirmed). If a residual inconsistent ellipsis label survives, it is
  reported for a small follow-up text fix decision.
- **Invariant to restore:** toolbar action labels are consistent — a trailing ellipsis
  signals "opens a further dialog" and is applied uniformly, not arbitrarily on some
  list-view buttons and not others. Behavioural / UI-consistency invariant.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** low — verification only.
- **Scope:** verify the list-view toolbar (built via the `ActionGroup`/UIManager in
  `gramps/gui/views/listview.py`) no longer renders the "Add…/Edit…/Merge…" ellipsis
  labels the report flagged (modern toolbar is icon-based; the only remaining "…" strings
  are legitimate progress messages like "Processing…"/"Updating display…"). / out of
  scope: tooltip wording, icon choice, the column/format labels, any new label change.
- **Repro instruction:** original repro — start Gramps, view the various category list
  views, observe the toolbar buttons for trailing-ellipsis labels. On current
  `maintenance/gramps61` the toolbar shows icon buttons without the inconsistent ellipsis
  text labels.
- **Test file:** none expected (verification of a cosmetic/UI-label state). If Check wants
  evidence, a grep assertion that `gramps/gui/views/listview.py` defines no
  Add/Edit/Merge action *label* with a trailing ellipsis suffices; record the manual UI
  check at sign-off.
- **Citations expected:** cite `gramps/gui/views/listview.py` (the `ActionGroup`
  Edit/Add/Merge action definitions and the absence of ellipsis labels there) as evidence
  the reported inconsistency is gone.
- **New/removed files:** none.
- **Prior-art check (triage cycles):** searched by path `gramps/gui/views/listview.py` on
  `upstream/maintenance/gramps61` — no "Add…/Edit…/Merge…" ellipsis button labels remain;
  the toolbar is icon-based and only legitimate progress strings carry "…". → reported
  inconsistency no longer present; this bundle validates and resolves it.
- **Mantis:** 6583
- **Disposition hint:** POSSIBLY-FIXED → verify first

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: The builder correctly found the Add.../Edit.../Merge... ellipsis labels are still present on maintenance/gramps61 across ~10 view files (libpersonview.py, libplaceview.py, citationlistview.py, citationtreeview.py, eventview.py, familyview.py, mediaview.py, noteview.py, repoview.py, sourceview.py, relview.py). However it concluded "by-design / WONTFIX" under the argument that dialog-openers correctly take "...". That reading is wrong: maintainer Nick H confirms the GNOME Guidelines say to remove the ellipses from these labels. The fix is a text-only patch removing the trailing "..." from the Add/Edit/Merge toolbar button labels and their matching popup/menu label entries across all the view files listed in the build-notes. A close-disposition artifact is no longer appropriate; the next Do should produce patch.diff + commit-msg + pr-description.
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — run-verify.sh: no patch.diff in /home/eddie/workspace/gramps-testbed-v2/results/issue_6583
- Failing gate: C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) (advisory) — run-verify-interface.sh: no patch.diff in /home/eddie/workspace/gramps-testbed-v2/results/issue_6583
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).

## Iteration 2 — carry-forward (from the previous attempt)
- Sign-off rationale: The patch misapplies the GNOME HIG ellipsis rule. Per the HIG (GNOME 3.0): an ellipsis is required when the command needs the user to supply new input before the action can execute (Input Required), and must be dropped when the command opens a properties/info window (State/Info Window) or fires immediately. Applied to the three labels: - Add → opens a dialog to create a new record (Input Required) → keep Add... - Edit → opens the existing record for viewing/editing (State/Info Window) → drop to Edit ✓ (patch is correct here) - Merge → opens a dialog where the user chooses which fields to keep (Input Required) → keep Merge... The builder removed ellipses from all three uniformly. Only the Edit change is correct; Add and Merge must retain their ellipses. The next Do should also check all other labels touched across the view files for the same rule before rebuilding the patch.
- Full previous attempt preserved in `iteration-v2/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
