# Brief — issue 12110 / call-name-revalidate-on-given-change

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** call-name-revalidate-on-given-change
- **Defect:** In the Name editor, the Call name field is validated against the Given name
  (marked red when the call name is not contained in the given names). That check only
  fires when the **Call** field changes, never when the **Given** field changes. So: type
  a call name with an empty given (red), then fill the given to match → still red; or set
  given=call (black), then change given → still black though now invalid. The red/black
  indicator goes stale.
- **Success criterion:** Editing the Given name re-runs the call-name validity check, so
  the Call field's valid/invalid (red) state reflects the *current* given name without the
  user having to re-touch the Call field. Demonstrable by exercising the validation
  predicate against changing given-name input (red→black and black→red transitions).
- **Invariant to restore:** The call-name validity indicator is a function of the current
  given name — whenever the given name changes, the indicator is recomputed. (Behavioural
  consistency invariant; rationale: the predicate "call name is part of the given name"
  depends on both fields, so a change to either must trigger re-evaluation, not just one.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** medium — confined to the Name editor (`editname.py`), but wiring a
  re-validation across two monitored fields is a behavioural change a reviewer must trace
  through the editor's signal flow.
- **Scope:** the missing re-validation of the Call field when the Given field changes in
  `gramps/gui/editors/editname.py` (`_validate_call` is connected only to the call
  field's `validate`; the given field has no hook that re-fires it). / out of scope: the
  validation rule itself (what "valid" means), surname handling, the group-as logic.
- **Repro instruction:** example.gramps → Edit a person → Names → add/edit a name.
  Case 1: Call = "Jon" (red), then Given = "Jon" → expected black, observed red.
  Case 2: Given = "Marc", Call = "Marc" (black), then change Given to "Paul" → expected
  red, observed black.
- **Test file:** gramps/gui/editors/test/editname_test.py (core, `*_test.py` suffix in
  the existing `gramps/gui/editors/test/` package). Drive the **production** validation
  path — the test must exercise the same predicate the editor uses to set the red state,
  not a parallel copy (principles §3.4). If the predicate cannot be reached headlessly,
  ship the GUI repro at `engine/interface/test_bug_12110_call-name-revalidate.py` and
  record C4 (unit) as unverifiable for human sign-off.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** none expected (test lands in an existing `test/` package; if a
  new test module is added, register it in `po/POTFILES.skip`).
- **Prior-art check (triage cycles):** searched by path `gramps/gui/editors/editname.py`
  on `upstream/maintenance/gramps61` — only black/license/column-sizing commits; no
  call-name re-validation fix. No matching fork PR by this path. → unfixed.
- **Mantis:** 12110
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: Two issues to fix: 1. Stacked POTFILES entries: the patch includes po/POTFILES.skip additions for gramps/plugins/lib/test/__init__.py and gramps/plugins/lib/test/libsourceview_test.py — these belong to issue_13876, not this bundle. They were picked up from a stacked branch and must be removed from this patch before publishing (they cause a conflict if issue_13876 publishes first, or dangling entries if this publishes first). 2. C4 test coverage: the reviewer correctly flagged that the test is predicate-level only (exercises call_name_is_valid() directly) and never drives the GTK changed- callback or validate(force=True) wiring added in editname.py. The callback wiring is the actual fix site and is currently untested. The next Do should either deepen the headless test to exercise _revalidate_call via a minimal stub, or add an AT-SPI interface repro that drives the Given field and asserts the Call indicator state.
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).

## Iteration 2 — carry-forward (from the previous attempt)
- Sign-off rationale: C3 scope rejected: the call-name validity predicate and revalidation trigger must stay local to gramps/gui/editors/editname.py. Do not introduce gramps/gen/utils/callname.py or any other new production file; inline the logic in editname.py directly. T3 unit-runner crash is a known infrastructure issue — do not block on it. T5/V: if headless GTK signal-path testing is not feasible, manual confirmation of the Name editor behaviour is sufficient.
- Failing gate: T3 runtime: gramps core unit suite (whole-suite baseline) (advisory) — T3-baseline [delta]: DELTA: runner exited 1 producing NO JUnit XML — a pre-test crash (install / GI bootstrap / test col
- Full previous attempt preserved in `iteration-v2/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).

## Iteration 3 — carry-forward (from the previous attempt)
- Sign-off rationale: The patch correctly fixes the Name editor (editname.py) — manual GUI confirmed that editing the Given field now immediately re-validates the Call field indicator. However, gramps/gui/editors/editperson.py (the primary Person editor) has the same stale Call/Given validation pattern. The fix must be extended to cover editperson.py before publication. The editname.py approach is correct; apply the same _revalidate_call hook there.
- Failing gate: C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) (advisory) — run-verify-interface.sh: /home/eddie/workspace/gramps-6.1-lane0 has uncommitted changes — refusing to patch it
- Full previous attempt preserved in `iteration-v3/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
