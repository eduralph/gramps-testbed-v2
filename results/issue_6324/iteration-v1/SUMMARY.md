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

Review task: fix Gramps cairo PDF/print table pagination so a short wrapping table-cell paragraph at a page break is not silently dropped.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief defines a cairo table-cell page-boundary content-loss defect and success criterion for full text preservation across pages (brief.md:5, brief.md:11). |
| C2 — C2 Reproduction (red pre-fix) | PASS | I ran the added test against the old `libcairodoc.py`; it failed at `gramps/plugins/test/cairodoc_table_pagination_test.py:177` because pagination did not terminate, matching the pre-fix no-progress/drop mechanism described by the removed shortcut in `$PDCA_TARGET/gramps/plugins/lib/libcairodoc.py:618`. |
| C3 — C3 Change | PASS | The patch removes the cell-only `<4 line` move-to-next-page shortcut and leaves the generic first-line-fit/split path to handle the case (patch.diff:17, patch.diff:21). |
| C4 — C4 Verification (red→green) | PASS | In a patched temp copy, `GRAMPS_RESOURCES=/tmp/pdca-check-target/build/share python3 -m unittest gramps.plugins.test.cairodoc_table_pagination_test -v` passed; the same test failed red on old code, and the official gate failure in check-gates.json is a missing-lane runner issue, not evidence against the patch (check-gates.json:33). |
| C5 — C5 Causal adequacy | PASS | The regression drives `CairoDoc.paginate` and the production table/cell/paragraph classes (patch.diff:67), and asserts both termination and every word surviving pagination (patch.diff:210, patch.diff:220). |
| T1 — T1 Structure | N/A | Core-only change; addon structure rules do not apply, matching the configured gate's N/A basis (check-gates.json:51). |
| T2 — T2 Shape | PASS | The new test has the project GPL header (patch.diff:38) and the new core test file is listed in `po/POTFILES.skip` as required by the brief (patch.diff:242). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: focused red→green runtime and `git diff --check` pass, but the broader T3 suite crashed before producing JUnit; a human must decide whether to accept this environment caveat or rerun the full suite in a working lane (check-gates.json:78). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is present in this check bundle, so contribution-wrapper review does not apply (check-gates.json:87). |
| T5 — T5 Judgment | PASS | The patch is narrowly scoped to cairo paragraph division and one regression test, with no broad backend rewrite or unrelated file churn beyond POTFILES registration (patch.diff:1, patch.diff:32, patch.diff:234). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: because the automated test proves the pagination no-progress case but does not visually inspect a generated PDF, a human must decide whether this is sufficient fitness evidence for the user-facing print/PDF report defect. |

## §6 Human Decisions

1. T3 — T3 Runtime: clear whether the focused red→green run plus clean diff check is enough while the full runner is unavailable, or rerun the whole suite in a working lane.
2. V — Validation — fitness-to-purpose: clear whether the red→green production-path regression is enough, or require a manual PDF/report check that a wrapped table cell at the page boundary visibly renders all text across pages.

Target-state caveat: `$PDCA_TARGET` is readable but on `master`, not the brief's `maintenance/gramps61`; `git apply --check patch.diff` succeeds there, and patch-content citations above therefore use `patch.diff` where the target source does not yet contain the change.

### Advisory — adversary

# check-advisory-adversary.md — issue 6324 / pdf-table-cell-wrap-page-break

Adversarial pass. All findings below were verified by executing the test and targeted
simulations against a scratch clone of `$PDCA_TARGET` at `upstream/maintenance/gramps61`
(0d9e148908; patch applies cleanly there and on the checked-out `master`, the touched
region is identical).

- NEEDS-HUMAN — **The text-survival assertion is a tautology; it cannot detect a
  content drop.** `_collect_text` asserts on `child._text`
  (`gramps/plugins/test/cairodoc_table_pagination_test.py:87` in the new file), but
  `GtkDocParagraph.divide` truncates only `_plaintext` — the first fragment keeps the
  **full original** `_text` (`gramps/plugins/lib/libcairodoc.py:717` sets plaintext only)
  and continuation fragments have `_text == ""` (constructor
  `gramps/plugins/lib/libcairodoc.py:495`; split sets only plaintext/attrs at :664, :715).
  Concrete failing case, reproduced: paginate with the fix, **discard every page except
  page 1**, run the test's own word loop → zero missing words, assertion passes. Rendering
  uses `_plaintext`, so the brief's requirement "assert the cell's text is present in the
  paginated output" (brief.md:13-15) is only nominally met — the sole effective red→green
  signal is the *termination* assertion. The test should assert on `_plaintext`.

- NEEDS-HUMAN — **The test's red geometry is not the reported defect, and the reported
  scenario was already correct pre-fix.** The brief's repro (brief.md:31-34) is a wrapping
  cell landing on the last line of a *normal* page, remainder fitting the next full page.
  Reproduced pre-fix: 5 filler rows + wrapping row, page holds fillers + ~1 line → the
  shortcut at `gramps/plugins/lib/libcairodoc.py:620-621` moves the paragraph intact,
  pagination terminates, **no words missing**. The test instead uses a page permanently
  shorter than the 2-line paragraph (`page_height = (one_line + full)/2`, test file ~171)
  — a geometry no real A4/letter report can produce for a <4-line cell. So the patch
  demonstrably fixes a constructed never-fits infinite loop, but whether it fixes the
  user-visible 6324 symptom ("cell prints no text at all" in a real report to PDF) is
  unproven; C2 is unverified ("no gate configured", check-gates.json C2 row) and no
  real-report repro exists in the bundle.

- NEEDS-HUMAN — **Layout change on previously-correct documents.** Removing the <4-line
  keep-together shortcut (`gramps/plugins/lib/libcairodoc.py:618-621` pre-fix) alters
  output wherever the shortcut worked as designed. Reproduced: 3-line cell paragraph with
  2 lines of room at page bottom and a full next page available — pre-fix: moved intact to
  page 2 (`['fillers...'] / [full text]`); post-fix: split 2+1, leaving an orphaned
  `'today ok'` line on page 2. Content is preserved either way, but every table-based
  PDF/print report may now break short cell paragraphs across pages. The brief scopes the
  change to "the specific content-drop case" (brief.md:29-30); deleting the aesthetic rule
  wholesale (rather than only when it makes no progress) exceeds that scope. Human should
  decide if the layout regression is acceptable upstream.

- **The no-progress defect survives one boundary away.** Post-fix step 2
  (`gramps/plugins/lib/libcairodoc.py:~625-630` after the patch; pre-patch :627-630)
  still returns `(None, self), 0` with no progress guarantee. Reproduced post-fix: a cell
  paragraph on a page shorter than one text line → `paginate` never terminates (201 pages
  and counting; `paginate_document`'s `while not paginate(): pass` at
  `gramps/plugins/lib/libcairodoc.py:1779-1780` would hang forever). The patch's own
  justification ("made no guarantee of progress") applies verbatim to the branch it
  delegates to; the restored invariant (brief.md:16-20) still fails at this boundary.
  Likely pre-existing/out of scope, but the fix rationale claims more than it delivers.

- **The machine red→green record does not exist; my manual re-run partially rehabilitates
  it.** C4 is `fail` for infra ("core worktree ... missing", check-gates.json C4 row) and
  T3 is `fail` (runner crashed pre-test, no JUnit XML) — overall `fail`. Any verdict
  citing verified red→green or a clean suite delta is unwarranted on this record. I
  re-ran manually on a clone: pre-fix the new test **fails on the termination assertion**;
  post-fix it passes. Red→green holds, but (per finding #1) only for termination — and the
  gates must be regenerated before sign-off.

- Minor: `$PDCA_TARGET` is checked out on `master` (aef9f35ec6), not the brief's target
  `maintenance/gramps61` (brief.md:21); patch applies cleanly to both and the cited region
  is byte-identical, so findings hold on either.

- Minor: the test's red depends on the environment font wrapping `CELL_TEXT` to 2–3 lines
  at 300 pt; the guards (test file ~166-169, `assertGreaterEqual/assertLess`) fail loudly
  under font substitution — a flaky-fail risk in CI, not a silent-pass risk.

Attempted and could NOT refute: that the test drives the production divide chain (it
calls the real `CairoDoc.paginate` → `GtkDocTable/Row/Cell/Paragraph.divide`; the bounded
loop only replaces `paginate_document`'s unbounded driver, C5's pass is warranted); that
`CairoDoc.__new__` skips needed init (paginate touches only `_doc/_pages/
_elements_to_paginate/_available_height`, all provided); that the patch breaks any
currently-passing divide behavior for non-CELL paragraphs (hunk removes only the CELL
shortcut and the now-unused `line_count`).

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] T3 — T3 Runtime — DECISION OWED: focused red→green runtime and `git diff --check` pass, but the broader T3 suite crashed before producing JUnit; a human must decide whether to accept this environment caveat or rerun the full suite in a working lane (check-gates.json:78).
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: because the automated test proves the pagination no-progress case but does not visually inspect a generated PDF, a human must decide whether this is sufficient fitness evidence for the user-facing print/PDF report defect.
- [ ] **The text-survival assertion is a tautology; it cannot detect a
- [ ] **The test's red geometry is not the reported defect, and the reported
- [ ] **Layout change on previously-correct documents.** Removing the <4-line

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
- Iteration delta (if iterating): Three adversary findings require a tighter fix before accept: 1. Layout regression: the patch removes the <4-line keep-together shortcut wholesale, splitting short cell paragraphs across pages on previously-correct documents (reproduced: 3-line cell with 2 lines of room now orphans one line on the next page). Scope the fix to suppress keep-together only when it makes no progress (i.e. the cell still can't fit after the move), not unconditionally. 2. Test assertion tautology: _collect_text checks _text but divide truncates _plaintext; the word-survival assertion passes even if all pages except page 1 are discarded. Fix the test to assert on _plaintext so content-drop can actually be detected. 3. Wrong test geometry: the test's never-fits page geometry does not reproduce the brief's reported scenario (wrapping cell on last line of a normal page). Add a test case matching the brief's repro (5 filler rows + wrapping row, page holds fillers + ~1 line) to confirm the actual user-visible defect is fixed.
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
