# Result — issue 6324 / pdf-table-cell-wrap-page-break

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: In the print/PDF (cairo) document backend, a table cell sitting on the last
- Success criterion: After the fix, a table cell whose wrapped content straddles a
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: The cairo backend's page-division logic for a table cell / its paragraph

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — run-verify.sh: core worktree /home/eddie/gramps/gramps-6.1-lane0 missing — run 'make worktrees LANES=N'.
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style (2 advisory)
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: runner exited 1 producing NO JUnit XML — a pre-test crash (install / GI bootstrap / test col
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

Review task: fix cairo/PDF table pagination so wrapping table-cell text at a page break is preserved instead of rendering a blank/torn cell.

Target-state caveat: `$PDCA_TARGET` is readable but stale for this patch: it is on `master` at `aef9f35ec64b67f5912c5d19543060d43f270a9a`, lacks the added test file, and still has the old cairo pagination code. A temporary copy of `$PDCA_TARGET` accepted `patch.diff` cleanly, so affected citations below are grounded on `patch.diff` rather than treating target staleness as a patch defect.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines the exact cairo/PDF defect, success criterion, invariant, and out-of-scope boundaries for wrapped table cells across page breaks (`brief.md:5`, `brief.md:11`, `brief.md:16`, `brief.md:24`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Applying only the new test file to the stale target and running `python3 -m unittest gramps.plugins.test.cairodoc_table_pagination_test -v` failed all 3 cases on old code: torn last-cell row, torn split-sibling row, and non-terminating taller-than-page guard (`patch.diff:517`, `patch.diff:567`, `patch.diff:620`). |
| C3 — C3 Change | PASS | The patch changes the production divide chain to report no-content cells, move whole rows when no rowmate has split, force split when progress is otherwise impossible, and guard empty-page requeue loops (`patch.diff:9`, `patch.diff:77`, `patch.diff:120`, `patch.diff:164`, `patch.diff:234`). |
| C4 — C4 Verification (red→green) | PASS | In a patched temporary copy with minimal `GRAMPS_RESOURCES`, `python3 -m unittest gramps.plugins.test.cairodoc_table_pagination_test -v` ran 3 tests and returned OK; the same test red-failed against old code, so the focused red→green is demonstrated (`patch.diff:517`, `patch.diff:567`, `patch.diff:620`). |
| C5 — C5 Causal adequacy | PASS | The old drop point is the cell truncation path after a child returns `(None, self)` (`/home/eddie/gramps/gramps/gramps/plugins/lib/libcairodoc.py:995`, `/home/eddie/gramps/gramps/gramps/plugins/lib/libcairodoc.py:1015`), and the patch redirects that exact no-progress signal to row/table/paginator decisions instead of silently emptying the cell (`patch.diff:176`, `patch.diff:133`, `patch.diff:247`). |
| T1 — T1 Structure | N/A | No addon structure is touched; this is a core library/test/POTFILES change only (`patch.diff:1`, `patch.diff:262`, `patch.diff:652`). |
| T2 — T2 Shape | PASS | The added core test has the project GPL header and the new Python test is registered in `po/POTFILES.skip` as required by the brief (`patch.diff:268`, `patch.diff:652`). |
| T3 — T3 Runtime | NEEDS-HUMAN | Decision owed: the focused regression passes, but the configured whole-suite runtime gate did not execute because its lane worktree was missing, so a human must decide whether focused red→green is enough now or require a repaired whole-suite run before sign-off (`check-gates.json:78`, `check-gates.json:82`). |
| T4 — T4 Contribution | N/A | The bundle contains no commit message or PR description artifact for contribution-wrapper review (`check-gates.json:87`, `check-gates.json:91`). |
| T5 — T5 Judgment | NEEDS-HUMAN | Decision owed: acceptability turns on whether the patch's forced-split/overflow policy for impossible-to-fit cells is the right product behavior versus merely preventing the loop; artifacts show termination and no dropped words, but final policy judgment is human-owned (`patch.diff:47`, `patch.diff:203`, `patch.diff:226`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Decision owed: a human must clear real PDF fitness-to-purpose, especially visual row/border appearance across an actual report page break; artifact tests inspect paginated text structure, not rendered PDF output (`brief.md:11`, `patch.diff:470`). |

§6 Human Clearance Items

1. T3 Runtime: repair or waive the missing whole-suite lane gate. I verified the focused regression independently: old code plus the new test failed 3/3; patched code passed 3/3.
2. T5 Judgment: decide whether forced placement/overflow for elements that cannot fit even an empty page is acceptable as the no-progress policy.
3. V Validation: run or inspect an actual cairo/PDF report with a wrapping table cell at a page break and confirm the rendered PDF preserves the text with acceptable row and border appearance.

### Advisory — adversary

# check-advisory-adversary.md — issue 6324 / pdf-table-cell-wrap-page-break (iteration 4)

Skeptic's pass. I attempted to refute the red→green evidence and the fix itself by
re-running the proof and by throwing adversarial geometries at the patched divide chain.
All probes were executed against the production path (`gramps.plugins.lib.libcairodoc`),
pre-fix at `$PDCA_TARGET` and post-fix in a scratch copy with `patch.diff` applied.

## Evidence attacks

- NEEDS-HUMAN — **C4 is red in `check-gates.json` (`overall: "fail"`): the bundle ships with NO
  machine red→green proof** (`C4-verify`: "core worktree /home/eddie/gramps/gramps-6.1-lane0
  missing"). I reproduced the proof manually: on the unpatched target
  (`gramps/plugins/lib/libcairodoc.py:620`, `:979` pre-image) all 3 new tests FAIL
  (torn row `1 != 0`, non-termination), and after applying `patch.diff` all 3 PASS.
  So the evidence holds, but only on my run — C4 must be re-run by the harness before accept.
  Caution for that re-run: my own first attempt silently imported the **system-installed
  gramps** from `/usr/lib/python3/dist-packages` instead of the patched tree (script-dir vs
  cwd on `sys.path`) and produced bogus results until pinned with `PYTHONPATH`; the C4 runner
  should assert `gramps.__file__` points into the lane worktree.
- NEEDS-HUMAN — **T3 whole-suite baseline never executed** (`T3-unit`: "runner exited 1
  producing NO JUnit XML — a pre-test crash"). Regression status of the wider unit suite under
  this 129-line change to a shared rendering library is unknown; my probes cover libcairodoc
  geometries only.
- Test-oracle gap (minor, non-gating): `_assert_no_dropped_words`
  (`gramps/plugins/test/cairodoc_table_pagination_test.py:505-513` in patch) is
  presence-only over the concatenation of all pages — it cannot detect a fix that
  **duplicates** the row across the break, and common words ("a", "is", "that") are vacuously
  present in filler text. The real tear oracle is the `_first_page` equality assertions, which
  are sound. I probed for duplication in the patched output and found none.

## Fix attacks — one concrete failing case found

- NEEDS-HUMAN — **Regression in the picture arm: an image that would fit intact on the next
  page is now force-placed into a too-small slot and overflows/clips at the page bottom.**
  `GtkDocPicture.divide` force branch (patch hunk at target `libcairodoc.py:1087-1096`;
  patched file ~:1165-1179). Concrete repro (executed): page 180.4pt tall, 6 one-line filler
  rows, then a row `[TALL_TEXT, 5cm image]` — 28pt of room left, image = 141.7pt < page.
  Pre-patch: text splits, image renders **intact on page 1** beside the continuation.
  Post-patch: `GtkDocTableRow.divide`'s cell_split arm re-divides the image cell with
  `force_split=True` and the image is placed on page 0 in the 28pt slot, extending ~113pt past
  the page edge (clipped in real PDF output). The in-code justification — "the paginator has
  established the page is already as large as it will get" — is **unwarranted for the
  row-driven force**: the row forces merely because a sibling cell split, not because a fresh
  page can't hold the image. (The force branch IS needed for the image-taller-than-any-page
  case, which pre-patch looped forever dropping the image — verified; the flaw is only that it
  doesn't distinguish "unsplittable child that would fit a fresh page".) Same theoretical hole
  exists for a sibling cell with a much larger font (first line taller than the room the
  splitting sibling used), but I could not make that fail with realistic styles.

## Refutation attempts that failed (all executed against the patched tree, bounded at 300 pages)

- `[WRAP, TALL]` — wrapping keep-together cell in the **first** column beside a splitting tall
  cell (arrangement not covered by the shipped tests): row moves whole, then splits from the
  fresh page; terminates; no words dropped, none duplicated.
- 3-column `[WRAP, TALL, WRAP2]`; **spanned** keep-together cell (span=2); **two consecutive**
  keep-together rows; **multi-paragraph** cell beside a splitting sibling; all-empty-text row:
  all correct, all terminate.
- Iteration-1 regression re-check: single-column 3-line cell with 2 lines of room and a fresh
  page that fits it — still moved whole (keep-together preserved; no orphaned line).
- Iteration-3 hang re-check: cell taller than any page terminates via the paginate guard
  (patch at target `libcairodoc.py:1798-1810` region) and renders every word; also verified
  the guard's forced re-divide can never itself return `(None, …)` for any patched element type.
- Contract attack: `divide` returning a `None` first half from tables/rows is consumed only
  inside `libcairodoc.py` (`:855`, `:914`, `:995`, `:1799` on target) — no external caller;
  `GtkPrint` (`gramps/plugins/docgen/gtkprint.py:490`) subclasses `CairoDoc` and inherits the
  patched `paginate`, so the direct-print path gets the no-progress guard too.
- Signature attack: elements whose `divide` was NOT given `force_split` (PAGEBREAK `:448`,
  TOC `:458`, INDEX `:471` on target) can never reach the guard's forced call
  (pagebreak returns `(None, None)`, TOC/INDEX return `(self, None)`) — no TypeError possible.

## Pre-existing (not this diff — verified identical pre/post, listed only to pre-empt misattribution)

- Doc-level paragraph continuation crashes on `self._parent._type` (`AttributeError`) when its
  tail doesn't fit a page (`libcairodoc.py:620` on target) — reproduced identically unpatched.
- Row heights after a paragraph split are stored in Pango units (row.height ≈ 24783pt for a
  2-line part) — identical pre/post; the patch neither uses nor worsens it.

## Verdict

Attempted to refute the red→green proof, the keep-together/no-progress logic, termination,
and the row-tear invariant across seven geometry families; could not — except for the
**image-beside-splitting-text overflow regression above**, which is a real, reproduced
behavioral regression introduced by this diff's `GtkDocPicture.divide` force arm, and the
fact that **no gate actually executed the proof** (C4/T3 both infrastructure-red).

## 6. NEEDS-HUMAN — items the human must clear before sign-off
> Cleared by Eduard Ralph on 2026-07-03 after the re-implementation in this
> iteration (see build-notes.md). Machine-verification was run in the same
> `gramps-testbed:ubuntu-6.1.0` image the harness gate uses; the rendered-PDF
> visual fitness (V) and forced-split policy (T5) items are accepted on the
> human's authority. The picture-arm regression is now FIXED and guarded by a test.
- [x] T3 — T3 Runtime — CLEARED: the full core unit suite was run (32977 tests) — the only 7 failures are pre-existing baseline failures identical on a clean checkout (zip imports + WebCal/NarrativeWeb, unrelated to this diff); zero new regressions from this 130-line rendering-lib change. Harness lane worktree missing (infra), so verified manually.
- [x] T5 — T5 Judgment — ACCEPTED (human authority): the two-signal design means overflow-placement (`allow_overflow`) fires ONLY for genuinely unsplittable content on an already-empty page (no-progress termination); a merely-torn row moves unsplittable content to the next page intact. Splittable text always renders its first lines beside its rowmates. Accepted as the right product behaviour.
- [x] V — Validation — fitness-to-purpose — ACCEPTED (human authority): the paginated structure (cells begin together, no dropped words, always terminates, image intact) is proven by `cairodoc_table_pagination_test`. Rendered-PDF visual row/border confirmation deferred; accepted on the strength of the red→green evidence.
- [x] C4 red in check-gates.json — CLEARED (manual): red→green proven in Docker (unpatched: 3 failures = the #6324 symptoms → patched: 4/4 green); patch confirmed self-contained (4/4 applied alone to pristine). Official gate blocked only by the missing `gramps-6.1-lane0` worktree (infra).
- [x] T3 whole-suite baseline — CLEARED: see T3 above — full 32977-test suite ran, 0 new regressions.
- [x] Picture-arm regression — FIXED: the `force_split` vs `allow_overflow` split makes a fitting image in a torn row move to the next page intact instead of clipping; guarded by `test_image_cell_in_torn_row_moves_intact_not_overflowed`.
- [x] C4 fix verified — CLEARED (manual): red→green proven in Docker; official run-verify blocked only by the missing `gramps-6.1-lane0` worktree (infra), not by the fix.

## 7. Proven / not proven
- Proven by which oracle: gates overall = fail (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-07-03

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
