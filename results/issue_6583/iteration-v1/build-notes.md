# Build notes — issue 6583 / verify-toolbar-label-ellipsis-gone

**Disposition: VERIFY-FIRST (POSSIBLY-FIXED) → `manual-verification`. No code patch.**
The verification's honest result is that the reported state is **NOT** already-fixed:
the inconsistent trailing-ellipsis toolbar/menu labels the report flagged
(`Add…`/`Edit…`/`Merge…` vs `Remove`/`Delete` with none) **still survive** on
`maintenance/gramps61`. Per the brief this is "reported for a small follow-up text fix
**decision**" — a decision that belongs to the human at sign-off, not a fix this builder
should pre-empt. Hence `manual-verification` and no patch.

## The brief's prior-art premise is incorrect — it grepped the wrong file

The brief's Scope and Prior-art check assert: "verify the list-view toolbar (built via the
`ActionGroup`/UIManager in `gramps/gui/views/listview.py`) no longer renders the
`Add…/Edit…/Merge…` ellipsis labels … the toolbar is icon-based and only legitimate
progress strings carry '…'." That conclusion came from grepping `listview.py` alone.

That file does **not** define the toolbar button *labels* — it only registers the action
*names* (handler bindings):

- `gramps/gui/views/listview.py:223-241` (target branch `upstream/maintenance/gramps61`):
  `ActionGroup(name=self.title + "/Edits")` with `add_actions([("Add", …), ("Remove", …),
  ("Merge", …)])` and `action_list.extend([… ("Edit", …) …])`. These are bare action
  identifiers (`"Add"`, `"Edit"`, `"Merge"`, `"Remove"`), **not** display strings — none
  can carry an ellipsis. So a grep of `listview.py` for ellipsis labels is *vacuously*
  clean, which is what produced the false "already-fixed" reading.
- The only `...` strings in `listview.py` are genuinely the progress messages the brief
  mentioned: `listview.py:674` `_("Processing...")`, `:767`
  `_("Column clicked, sorting...")`, `:1388` and `:1408` `_("Updating display...")`.

The user-visible **labels** for those actions live in each category view's UI-XML strings
(the `GtkToolButton` `label` properties and the `Popup`/menu `label` attributes), not in
the base class.

## The reported ellipsis labels are still present (path:line, target branch)

People view — `gramps/plugins/lib/libpersonview.py` (the inconsistency in one place):

- toolbar buttons: `:336` `<property name="label" …>_Add...</property>`,
  `:348` `Edit...`, `:372` `_Merge...`  — **but** `:360` `_Delete` (the Remove action) has
  **no** ellipsis.
- popup/menu items repeat it: `:256` `_Add...`, `:268` `_Merge...`, `:264` `_Delete`;
  `:407` `_Add...`, `:419` `_Merge...`, `:415` `_Delete`.

This exact `Add.../Edit.../Merge...` (ellipsis) alongside `_Delete` (no ellipsis) pattern
recurs in **every** list/tree view's UI XML on the target branch, e.g.:

- `gramps/plugins/lib/libplaceview.py:397,409,433` (Add/Edit/Merge `...`)
- `gramps/plugins/view/citationlistview.py:284,296,320`
- `gramps/plugins/view/citationtreeview.py:435,447,458,469,493`
  (also `Add source...`, `Add citation...`)
- `gramps/plugins/view/eventview.py:297,309,333`
- `gramps/plugins/view/familyview.py:254,266,290`
- `gramps/plugins/view/mediaview.py:361,373,397`
- `gramps/plugins/view/noteview.py:243,255,279`
- `gramps/plugins/view/repoview.py:279,291,315`
- `gramps/plugins/view/sourceview.py:251,263,287`
- `gramps/plugins/view/relview.py:414,428,504` (`Edit...`, `Add Partner...`)

So the literal artifact the reporter described (Gramps 4.0.0) is unchanged in 6.1: the
ellipsis is on Add/Edit/Merge and absent on Remove/Delete. The reporter's "inconsistent"
observation is reproducible today.

(Note: even when the toolbar style is icons-only, these strings are still user-visible — in
the right-click **Popup** menu items, the toolbar overflow menu, and accessibility names —
so this is not a non-rendering string.)

## Why this is a *decision*, not an obvious fix — the invariant cuts the other way

The brief's stated **Invariant to restore** is: "a trailing ellipsis signals 'opens a
further dialog' and is applied uniformly." Measured against that convention, the current
labels are arguably **already consistent and correct**, not broken:

- `Add` → opens an editor dialog for further input → ellipsis is *correct*.
- `Edit` → opens an editor dialog → ellipsis *correct*.
- `Merge` → opens a merge-selection dialog → ellipsis *correct*.
- `Remove`/`_Delete` → performs the action (at most a yes/no confirmation alert, which by
  the GNOME HIG ellipsis convention does **not** take an ellipsis) → no ellipsis *correct*.

So the three operations that open input dialogs carry `...` and the one that does not,
doesn't — which is exactly the *uniform* application the invariant asks for. Under that
reading the v4.0.0 reporter's "inconsistency" is the intended modern behaviour, and the
"follow-up text fix" may well be **no change (close as not-a-defect / by-design)**.

Because the resolution genuinely turns on a UI-text judgement (accept the
dialog-opener convention as-is, vs. strip all the `...`, vs. add `...` to Delete) and the
brief explicitly defers it to "a small follow-up text fix **decision**", the correct
builder output is a faithful verification report routed to the human — not a unilateral
patch that would bake in one of those choices.

## Why no patch, and why no red→green test

- **No patch.** The brief says "Verification, not a new fix (no patch if confirmed)", and
  the residual case is "reported for a … decision". Both branches of the Success criterion
  are no-patch. A close-disposition bundle records `close-disposition` as the Do artifact
  (it stands in for `patch.diff`: `src/pdca_harness/state.py:34,52-54`); shipping an empty
  `patch.diff` instead would risk the publisher's no-fix path (see memory
  `verify-first-close-empty-patch`). So: `close-disposition` present, **no** `patch.diff`,
  no `commit-msg.txt`, no `pr-description.md`.
- **No test file.** The brief says "none expected". A red→green test cannot exist here:
  there is no fix to flip the state, and the only behaviour to "test" is a static label
  audit. The brief's fallback ("a grep assertion that `listview.py` defines no Add/Edit/
  Merge action *label* with a trailing ellipsis") would *pass vacuously* precisely because
  `listview.py` holds action names, not labels — so it would mis-evidence "fixed". I
  deliberately did **not** ship that misleading assertion; the grep evidence across the
  real label sites (above) is the honest record instead.

## Alternatives considered / ruled out

- **Close as `already-fixed` / `not-reproducible` (the brief's expected happy path).**
  Rejected — it is false. The labels are present and the reporter's observation reproduces
  on `maintenance/gramps61` (citations above). Recording "fixed" would launder an
  incomplete prior-art grep into a wrong disposition.
- **Ship a text patch stripping the `...` from Add/Edit/Merge across all ~10 view files.**
  Rejected — (1) the brief does not authorise a fix here ("no patch … reported for a …
  decision"); (2) under the brief's own ellipsis invariant the current labels are arguably
  correct, so the change might be the *wrong* direction; (3) it would be a wide,
  cross-cutting i18n-string churn (each removed/changed `translatable="yes"` label
  re-opens a msgid for every locale) — roughly: People `libpersonview.py` 9 label sites,
  plus Place/Citation×2/Event/Family/Media/Note/Repo/Source/Rel ~6-9 sites each ≈ 70+
  string edits across 11 files — committed pre-emptively before the human has decided
  whether any change is wanted. That is exactly the kind of decision the brief reserves.
- **Ship a patch adding `...` to Delete (the other way to make them "uniform").** Same
  objection; and it contradicts the HIG ellipsis convention the invariant cites.

## Recommendation for sign-off (the deferred decision)

The human should decide one of:
1. **By-design / WONTFIX** — the labels already follow the dialog-opener ellipsis
   convention (Add/Edit/Merge open dialogs → `...`; Delete confirms only → none). This is
   my reading and the most defensible against the stated invariant. → close 6583 as
   not-a-defect.
2. **Text fix** — if the project prefers no ellipses on these toolbar/menu labels at all,
   file a focused follow-up to strip `...` uniformly across the views listed above. That is
   a separate, scoped change (not this verification bundle).

Either way, the verification itself is complete: the reported labels are characterised,
located, and shown to persist on the target branch.

## Files

- `close-disposition` — `manual-verification` (routes the decision to the human).
- `build-notes.md` — this file (withheld from the reviewer).
- No `patch.diff`, no test, no `commit-msg.txt`/`pr-description.md` (verify-first, no fix).
