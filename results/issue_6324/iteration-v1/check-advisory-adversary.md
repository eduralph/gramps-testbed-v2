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
