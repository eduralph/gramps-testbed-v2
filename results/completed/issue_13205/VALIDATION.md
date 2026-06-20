# VALIDATION — 2026-06-07 (disposition HOLDS; one iterate candidate for the human)

> Additive note from the older-process revalidation pass
> (`process/validate-numbered-bundles.md`). It does **not** change §9. The frozen
> accept stands; the item below is for the human to decide whether to `iterate-do`.

**Disposition HOLDS.** Re-run 2026-06-07: `C4-verify green-with-fix=PASS /
red-without-fix=PASS`, patch applies clean to `maintenance/gramps61`. The fix is a
genuine cause-removal — replacing the over-strict `raise MergeError` on non-Citation
backlinks with the existing class-filtered `get_source_referents` path; the decorrelated
reviewer found C5 passes (no symptom-guard).

## Iterate candidate (human decides) — weak regression red

The regression test's **red-without-fix passes via `ImportError`, not behaviour**: with
the production reverted, the test fails because it imports the patched helper
`citation_handles_of_source` from `gramps.gen.utils.db` (which no longer exists once
reverted), *not* because it reproduces the merge-over-non-Citation-backlink bug. The C4
*contract* (test fails when prod reverted) is satisfied, but the test does not prove it
catches the actual defect — a red can pass for the wrong reason.

Secondary, lower-priority:
- **Brief seated a mechanism (pre-`2a9720b`):** Scope named a new module
  `mergecitationslib.py` with a prescribed signature; the builder correctly ignored it
  and reused `gramps.gen.utils.db`. Expected drift for a brief authored before the
  invariant-discipline delta; no rework warranted on this ground alone.
- **Test-path drift:** brief named `gramps/plugins/tool/test/mergecitations_test.py`;
  patch ships `gramps/plugins/test/mergecitations_test.py`.

**Suggested action (NEEDS-HUMAN):** consider an `iterate-do` to make the red
behavioural — exercise the merge path so the test fails *because the bug reproduces*
when the production change is reverted, independent of the helper symbol. If the
unit-level proof is judged sufficient, record that and leave as-is.
