# Check review — sqlite-export-6.1 (Person round-trip on core 6.1)

> Advisory, artifact-only, decorrelated from the builder. Inputs seen: `patch.diff`,
> `brief.md`, `check-gates.json`. `build-notes.md` withheld by design — so every "green"
> claim below was re-derived from the gate JSON and the diff, not taken from Do's word.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | Brief carries a concrete, testable success criterion: `ExportSQLTestCase` green on **both** the gramps61×6.1 and gramps60×6.0 legs (brief.md:20-24); defect, invariant and scope are unambiguous. |
| C2 — C2 Reproduction (red pre-fix) | PASS | Pre-fix red is documented (`ValueError: too many values to unpack (expected 21, got 22)` at `ExportSql.py:684` in `setUp`, brief.md:58-62) and the failure is re-derivable from the diff: the old `(...) = person` unpacks 21 names against core 6.1's 22-tuple. C4 path_line reports `red-without-fix=PASS` for the 6.1 leg. No gate configured (check-gates C2 result="none"); evidence is documentary. |
| C3 — C3 Change | PASS | Change is present, minimal, symmetric and version-tolerant, confined to the in-scope surfaces: export unpack absorbs trailing fields via `*_,` (patch.diff ExportSql.py ~L708), import pads with the core default via `data += Person().serialize()[len(data):]` (patch.diff ImportSql.py ~L729), test strengthened to a real round-trip assertion (tests/test_sqlite.py `test_export_sql`). No event/family/note handlers touched — matches brief scope (brief.md:46-57). Caveat: brief cites `ExportSql.py:684`/`ImportSql.py:705` but the diff hunks land at ~702/~724 (≈18-20 line offset) — citation/line drift for the human to reconcile, not a defect in the change itself. |
| C4 — C4 Verification (red→green) | FAIL | Gating gate `C4-verify` result=**fail** (check-gates.json:34-39) and — decisively — `T3-addon-unit-61` reports the strengthened regression test itself as a **new post-fix failure**: `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sql` (check-gates.json:82). That contradicts the C4 path_line's `green-with-fix=PASS` on the 6.1 leg: the two artifacts disagree about whether the test is green on core 6.1. Red→green is therefore **not established**; the bundle does not meet its own success criterion on the load-bearing 6.1 leg. (Separate framing flagged below: the 6.0-leg `red-without-fix` is unsatisfiable by design — a no-regression leg, not red→green — but that framing does NOT excuse the 6.1-leg test failure.) |
| C5 — C5 Causal adequacy | PASS | Root cause is uncontested and well-evidenced (core 6.1 added 22nd field `familysearch_sync`, index 21, via `4972a2eb4e`; addon hardcodes a 21-tuple). The fix is applied at exactly the two serialize boundaries that consume the positional contract — not a guard or band-aid — and is symmetric (export absorbs, import pads). The diff targets the right cause at the right place. (Whether it *fully* restores the round-trip is a verification question, open under C4, not a causal-targeting one.) |
| T1 — T1 Structure | PASS | The patch introduces **no** `__init__.py` and no layout change — it touches only `ExportSql.py`, `ImportSql.py`, `tests/test_sqlite.py`. The gate's T1 ✗ ("addon dir has `__init__.py`", check-gates.json:55) concerns a file outside this diff; per the brief's own carry-forward it is "likely a false-positive on `Sqlite/tests/__init__.py`" (a legitimate test-package marker). Patch is structure-clean; gate flag is pre-existing — reviewer to confirm the offending `__init__.py` is the tests package, not the addon root. |
| T2 — T2 Shape | PASS | The flagged `print()` at `ImportSql.py:897` (check-gates.json:64) is **outside** the diff (the only ImportSql hunk is at ~L724-730) — pre-existing, not introduced here. The patch adds no `print()`/debug output and no header-stripping. Advisory; reviewer may still triage the pre-existing print separately. |
| T3 — T3 Runtime | FAIL | Mixed, with hard fails on the legs that matter: `T3-addon-unit-61` delta = new failure `ExportSQLTestCase::test_export_sql` (check-gates.json:82) — the regression test is **red on core 6.1 post-fix**; `T3-addon-interface` (E2E) delta = new failure `setUpClass (interface.test_smoke.SmokeTest)` (check-gates.json:100). `T3-addon-unit-60` is green (check-gates.json:73) and `T3-interface` matches its known-red baseline (check-gates.json:91). The 6.1 addon-unit delta is the same signal as C4 and is the blocker. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle to evaluate (check-gates.json:109); the brief explicitly waives the `Fixes/Bug #id` trailer MUST (brief.md:91-94). Nothing to check at this stage. |
| T5 — T5 Judgment | NEEDS-HUMAN | Branch target is an explicit judgment call: defect is core-6.1-only and the addon code is byte-identical across gramps60/gramps61; default path is gramps60 → cherry-pick to gramps61, but direct-to-gramps61 is defensible (brief.md:38-43, 113-117). Maintainer's preference overrides — cannot be settled from artifacts. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Whether an error-free round-trip that does **not** persist the `familysearch_sync` payload (brief scope (b), brief.md:54-56) truly satisfies the maintainer's intent is a human sign-off call by definition. |

## Summary

**Recommend: do not accept this iteration.** The advisory C/T elements that bear on the
*change itself* are sound — C1/C2/C3/C5 PASS; the diff is minimal, symmetric and
version-tolerant, and targets the right cause. T1/T2 advisory flags are pre-existing and
outside the diff. **But the verification does not close:** the gating `C4-verify` is FAIL
and `T3-addon-unit-61` independently reports the strengthened regression test
`ExportSQLTestCase::test_export_sql` as a **new failure on core 6.1**. The success
criterion (that exact test green on the 6.1 leg) is therefore unmet, and there is an
internal contradiction in the artifacts (C4 path_line claims `green-with-fix=PASS` on the
6.1 leg while T3-61 shows that test red) that must be resolved before any red→green claim
can stand. This is a different failure mode from iteration 1 (there the runner died with
exit 2 and *nothing ran*; here the test appears to run and **fail**) — so re-running is not
enough; the 6.1 round-trip failure needs to be diagnosed.

## §6 — items the human must clear

1. **T5 — Branch target (ambiguous scope / judgment).** gramps60-then-cherry-pick vs
   direct-to-gramps61, given the defect is 6.1-only. Maintainer decides (brief.md:113-117).
2. **V — Validation fitness-to-purpose.** Confirm that dropping the `familysearch_sync`
   payload (faithful round-trip of only the fields the addon schema represents) is the
   intended outcome, not a silent data gap (brief.md:54-56).

### Additional blocking notes for the human (not §6 NEEDS-HUMAN, but must be cleared before sign-off)

- **C4/T3-61 conflict (blocking).** Resolve why `C4-verify` path_line says the 6.1 leg is
  `green-with-fix=PASS` while `T3-addon-unit-61` reports `ExportSQLTestCase::test_export_sql`
  as a new failure. Either the regression test is genuinely red on core 6.1 (success
  criterion unmet) or the two harnesses ran against different inputs and one signal is
  stale. Until reconciled, red→green is unsubstantiated.
- **C4 6.0-leg framing (raised by the brief, brief.md:104-111).** The gramps60×6.0 leg has
  no pre-existing defect, so its `red-without-fix` half is unsatisfiable — it is a
  no-regression leg, not a red→green one. The human should confirm this framing so the
  6.0-leg `red-without-fix=FAIL` is not double-counted as the bundle failure. Note: this
  framing does **not** rescue C4 — the 6.1-leg test failure stands on its own.
</content>
</invoke>
