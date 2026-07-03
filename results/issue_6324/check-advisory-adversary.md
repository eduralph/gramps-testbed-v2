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
