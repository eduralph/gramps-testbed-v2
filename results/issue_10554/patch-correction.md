# Patch correction (post-accept) — 2026-07-01

`patch.diff` was regenerated to remove a wave-stacking contaminant and make the
bundle publish-ready. The previous version is preserved as
`patch.diff.contaminated.bak`.

## What was wrong

The accepted `patch.diff` carried a stray `po/POTFILES.skip` hunk adding
`gramps/plugins/importer/test/importxml_daterange_test.py` — a file this patch
does **not** create. That line belongs to `issue_14014` (confirmed: the same line
appears in `results/issue_14014/patch.diff`). It was swept in because 10554 was
built on a stacked-wave tree that had 14014's changes underneath.

Consequences: the patch **failed to apply to a clean `master`** (`git apply` error
at `po/POTFILES.skip:598`), and it registered a POTFILES.skip entry for a file
absent from the change.

## The correction

Dropped only the stray hunk. Verified in an `origin/master` worktree:

- The substantive change — `gramps/gen/relationship.py` and the new
  `gramps/gen/test/relationship_test.py` — is **byte-identical** to the accepted,
  C4-verified version (diff of added lines is empty). The corrected POTFILES.skip
  hunk still registers the real new test file `gramps/gen/test/relationship_test.py`.
- `git apply --check results/issue_10554/patch.diff` now **applies cleanly to
  `upstream/master`**.

Because only a non-functional translation-extraction line was removed (POTFILES.skip
is not consumed by the test runner), the recorded C4 red→green result
(`check-gates.json`: `green-with-fix=PASS / red-without-fix=PASS`) still holds — the
production code and the shipped test are unchanged. §9 sign-off is unaffected.

## Not corrected here (pre-existing, tracked separately)

- The advisory **reviewer never completed** (transient infra); `check-review.md` is
  "NOT COMPLETED" and the §6 review item was cleared by human judgement, not by a
  produced review. Re-running the reviewer leaf remains advisable before publish.
- Minor unhandled edge case in `_famrel_from_persrel`: a family with **one birth
  and one adoptive parent** (e.g. stepparent adoption) is not classified the way
  birth+step is. Uncommon; left as-is.
