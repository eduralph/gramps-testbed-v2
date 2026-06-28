## Root cause

The GNOME Human Interface Guidelines specify that a trailing ellipsis ("…") indicates "this command needs further input from the user before it can act". The Edit action opens the selected record in its editor without prompting for additional input—it is a state/properties window, not an input-required dialog—so its labels must not carry an ellipsis.

## Fix

Remove the trailing ellipsis from all Edit toolbar/menu/popup labels across 11 list-view and category-view files (32 label sites total), while leaving Add and Merge labels unchanged—they correctly retain their ellipsis because they open input-requiring dialogs.

## Verified against

- gramps/plugins/lib/libpersonview.py:271,348,430 — Edit label changed from "Edit..." to "Edit" in menu, toolbar, and popup
- gramps/plugins/lib/libplaceview.py:347,406,485 — Edit labels consistent with same pattern
- gramps/plugins/view/citationlistview.py:234,293,365 — same three-site pattern (menu, toolbar, popup)
- gramps/plugins/view/citationtreeview.py:385,466,554 — consistent Edit label removal
- gramps/plugins/view/eventview.py:247,306,378 — consistent pattern
- gramps/plugins/view/familyview.py:204,263,348 — consistent pattern
- gramps/plugins/view/mediaview.py:311,370,472 — consistent pattern
- gramps/plugins/view/noteview.py:193,252,324 — consistent pattern
- gramps/plugins/view/repoview.py:229,288,360 — consistent pattern
- gramps/plugins/view/sourceview.py:201,260,332 — consistent pattern
- gramps/plugins/view/relview.py:414,504 — Edit labels in popup and toolbar (two sites for this file)
- gramps/plugins/test/toolbar_label_ellipsis_test.py — new regression test asserting Edit labels have no trailing ellipsis
- po/POTFILES.skip — test file registered in skip list (no translatable strings)

## Test

The included regression test (`gramps/plugins/test/toolbar_label_ellipsis_test.py`) reads each view's source file (headless-safe, no GTK import) and asserts that all Edit action labels extracted from both toolbar XML literals and sgettext forms do not end with "…". The test RED before the patch (Edit… present in all 11 files) and GREEN after (Edit only, no ellipsis). A second assertion guards against vacuous parser success by verifying ≥1 Edit label is found in each listed file.

Fixes #6583
