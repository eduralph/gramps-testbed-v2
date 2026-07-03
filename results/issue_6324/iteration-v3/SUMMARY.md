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
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style (2 advisory)
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

Task under review: fix cairo/PDF table pagination so a wrapping table-cell paragraph at a page break is preserved instead of rendering a blank/torn cell.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | brief.md defines the cairo/PDF defect, invariant, scope, test path, and required production pagination path at brief.md:6, brief.md:16, brief.md:24, and brief.md:35. |
| C2 — C2 Reproduction (red pre-fix) | PASS | With the new test kept and the production patch reversed, `python3 -m unittest -v gramps.plugins.test.cairodoc_table_pagination_test` failed both cases with `wrap_page != label/tall_page`, matching the pre-fix blank/torn-row behavior asserted at patch.diff:433 and patch.diff:486. |
| C3 — C3 Change | PASS | The base root cause is present where short cell paragraphs return `(None, self)` at gramps/plugins/lib/libcairodoc.py:620 and table cells then truncate children at gramps/plugins/lib/libcairodoc.py:1015; the patch adds row-level move-whole/force-split handling at patch.diff:34, patch.diff:64, and patch.diff:128. |
| C4 — C4 Verification (red→green) | PASS | check-gates.json reports green-with-fix and red-without-fix pass at check-gates.json:33, and I independently observed the focused test pass after applying the patch in `/tmp/pdca-check-6324` with 2 tests OK. |
| C5 — C5 Causal adequacy | PASS | The test drives `CairoDoc.paginate` and imports the production `GtkDocTable`/`GtkDocTableRow`/`GtkDocTableCell`/`GtkDocParagraph` classes at patch.diff:219 and patch.diff:326, while assertions inspect rendered `_plaintext` at patch.diff:351 and patch.diff:381. |
| T1 — T1 Structure | N/A | This is a core-library/test change, not an addon layout change; the configured T1 gate also reports no `addons-source` path at check-gates.json:51. |
| T2 — T2 Shape | PASS | The added test has the project GPL header at patch.diff:154 and the new core test file is registered in `po/POTFILES.skip` at patch.diff:506; gates report T2 shape and potfiles pass at check-gates.json:59 and check-gates.json:68. |
| T3 — T3 Runtime | PASS | Runtime gate reports the core unit baseline matches recorded known reds at check-gates.json:77, and the focused patched-temp-clone run of `python3 -m unittest -v gramps.plugins.test.cairodoc_table_pagination_test` passed both tests. |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is in the review bundle, so contribution-wrapper checks do not apply; the gate records this as N/A at check-gates.json:86. |
| T5 — T5 Judgment | PASS | Reviewer judgment: the current patch addresses the prior iteration objections by preserving keep-together when no sibling split exists at patch.diff:64, testing `_plaintext` at patch.diff:351, and covering the earlier-column split branch at patch.diff:442. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: a maintainer/user must decide whether the tested pagination behavior is acceptable for real cairo/PDF reports on the intended `maintenance/gramps61` branch, because final output fitness and visual page composition are human sign-off criteria beyond artifact-only review. |

Target-state caveat: `$PDCA_TARGET` is readable and the patch applies cleanly, but the checkout reports branch `master` rather than the brief's `maintenance/gramps61`; I grounded base-code citations on the target source where present and changed/new-code citations on `patch.diff`.

§6 Human Clearance Items

1. V — Validation — fitness-to-purpose: run or inspect a representative cairo/PDF table report on the intended `maintenance/gramps61` integration branch and confirm that wrapped cell text appears across the page break with acceptable table borders/page composition. Artifact checks and the focused headless test are green, but final PDF fitness is a human acceptance decision.

### Advisory — adversary

# check-advisory-adversary.md — issue 6324 / pdf-table-cell-wrap-page-break (iteration 3)

Skeptic's pass. All probes run against `$PDCA_TARGET` source (patch applied in a scratch
clone; target left untouched). Note: `libcairodoc.py` is byte-identical between the
checkout's `master` HEAD and `origin/maintenance/gramps61`, and the patch applies cleanly
to both, so the branch-name discrepancy of the checkout is immaterial.

## Evidence attacks (red→green, production path)

- Independently re-ran the asserted proof: both tests **fail** on unpatched
  `gramps/plugins/lib/libcairodoc.py` (torn-row assertions fire with the exact pre-fix
  symptom, wrapping cell one page after its rowmate) and **pass** with the patch. The test
  drives the real `CairoDoc.paginate` / `divide` chain, and its row construction
  (`GtkDocTableRow([50, 50])`) matches production `start_row`
  (gramps/plugins/lib/libcairodoc.py:1505-1506). The iteration-1 tautology (`_text` vs
  `_plaintext`) is fixed — `_page_texts` reads `_plaintext`. **Attempted to refute the
  red→green evidence as tautological/mocked; could not.**
- Vacuity (portability) gap in test 2: `test_wrapping_cell_splits_beside_split_sibling`
  (gramps/plugins/test/cairodoc_table_pagination_test.py:442-493, `page_height =
  filler_h + 2 * line_h` at :462) guards WRAP's line count (2-3) but never asserts that
  the WRAP cell actually *failed to fit* beside the split sibling (e.g. that WRAP's tail
  lands on a later page than "Wstart"). Under different font metrics a 2-line WRAP could
  fit the 2-line gap and the test would pass pre- and post-fix without exercising the
  `force_split` branch. In the gate environment it demonstrably exercises it (red
  confirmed), so this is a future-silent-rot concern, not a current false pass.

## Fix attacks (concrete adversarial geometries, patched code)

- No content drop / no duplication in any terminating run I could construct: mid-table
  whole-row move (rows before + after intact), reversed column order [WRAP, TALL],
  multi-paragraph cell beside a splitting sibling, forced-split-fails placeholder branch
  (oversized 40pt cell beside a splitting cell — all characters render, split "BIGWOR"/"D"
  across the boundary, and that geometry **hung forever pre-fix**, so the patch is a strict
  improvement there). **Attempted to find a dropped or doubled word; could not.**
- NEEDS-HUMAN — Residual non-termination (pre-existing class, new code path): when a
  kept-together (<4-line) cell cannot fit even a full empty page (e.g. two-column row
  `[WRAP(2-3 lines), TALL]` with page_height ≈ 1 filler row + 2 lines), the new
  `GtkDocTable.divide` early return re-queues `(None, new_table)` every pass and
  `paginate_document`'s unbounded `while not self.paginate(): pass`
  (gramps/plugins/lib/libcairodoc.py:1777-1780) never returns, emitting empty pages
  forever. I verified the **same geometry also hangs pre-fix** (via the blank-cell-carry
  loop through :620's keep-together return), so this is not a new failure class — but the
  patch routes into it through a brand-new cycle, and post-fix the degraded output renders
  strictly less before hanging (pre-fix the tall sibling's text still appeared; post-fix
  nothing after the fillers). The added test tacitly acknowledges the hazard by capping its
  own paginator at 60 iterations (cairodoc_table_pagination_test.py:326-347) while
  production has no such cap. Human should decide whether "equivalent pre-existing hang" is
  acceptable residue or whether the row-move branch needs a no-progress guard (force split
  when height == full page height).
- Behavioral asymmetry, not a defect: whether a row moves whole or splits now depends on
  column order (`cell_split` is only set by columns processed *earlier* —
  patch hunk at libcairodoc.py:903-938 region): `[TALL, WRAP]` splits with a forced WRAP
  split, `[WRAP, TALL]` moves the row whole and defers TALL's start to the next page. Both
  outcomes satisfy the brief's invariant ("whole row moves, or every cell renders its first
  lines"); content verified complete in both orders. Noted for the record; not a refutation.
- Layout-regression re-check (iteration-1 finding #1): the keep-together shortcut
  (libcairodoc.py:620) is preserved for the unforced path, and rows not hitting the
  `c1 is None` case take exactly the old code path (`kept_cells` equals the original cell
  list object-for-object). Only previously-buggy (torn/blank) geometries change layout.
  **Attempted to reproduce the iteration-1 orphaned-line regression; could not** — the
  3-line-cell/2-line-room geometry now moves the row whole with all text intact.

## Verdict attacks

- `check-gates.json` C4/C5 claims verified independently above; no rationalization found
  there. One soft spot: T3 (`T3-unit`, advisory) passed against a baseline recorded on a
  different tree ("⚠ baseline tree drift: recorded detached@674e3b",
  check-gates.json rows[8]) — a newly-introduced red that happens to coincide with one of
  the "7 known test reds" would be masked. Given C4/C5 and my probes, I found no evidence
  of an actual masked failure; flagging the gate-integrity caveat only.

## Bottom line

Attempted to refute (a) the red→green evidence as tautological or non-production, (b) the
fix via content drop, duplication, column-order, multi-paragraph, oversized-font and
mid-table geometries, and (c) the iteration-1/iteration-2 regressions recurring — **could
not**. The one substantive residue is the pre-existing pagination hang class the patch
inherits (NEEDS-HUMAN above).

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: a maintainer/user must decide whether the tested pagination behavior is acceptable for real cairo/PDF reports on the intended `maintenance/gramps61` branch, because final output fitness and visual page composition are human sign-off criteria beyond artifact-only review.
- [ ] Residual non-termination (pre-existing class, new code path): when a

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: iterated-to-Do
- Iteration delta (if iterating): The row-move branch must implement a no-progress guard: when a kept-together cell cannot fit even a full empty page, divide() must force-split (or error) instead of re-queuing (None, new_table) and spinning paginate_document's unbounded loop forever. The pre-existing hang is not acceptable residue — the new code path must not inherit it.
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
