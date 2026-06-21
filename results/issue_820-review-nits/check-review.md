# Check Review — issue_820-review-nits (iteration 4)

Advisory, artifact-only, decorrelated from the builder. Inputs: `patch.diff`,
`brief.md`, `check-gates.json` (build-notes.md withheld by design). Every verdict
below was re-derived from the artifacts, not copied from `check-gates.json`.

## §5 — Verdict matrix

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | `brief.md:8-26` is complete: slug, five-item defect (a)–(e), success criterion, repro instruction, test-file expectation, citations. A workable spec exists. |
| C2 — C2 Reproduction (red pre-fix) | FAIL | No red-pre-fix reproduction demonstrated. The only new test (`test_addon_paths.py`) imports `tests.addon_paths.is_in_addons_tree` — a helper that does not exist on the unpatched tree (`patch.diff:99` adds it new), so it would ImportError, not go meaningfully red, against pre-fix code; the substring bug it guards lived inline. C4 (which runs red→green) also never applied. Items (a)/(d)/(e) are behaviour-preserving/CI-observable with no red oracle. |
| C3 — C3 Change | PASS | `patch.diff` implements all five items: (a) `make_gramps_user` removed, `tests/gramps_test_env.py:121-129`; (b) `type_plugins()` sweep over `(None, *PTYPE)` replaces `_PluginRegister__plugindata`, `patch.diff:172-173`; (c) prefix check `startswith(addons_root + os.sep)`, `tests/addon_paths.py:112`; (d) `! -name '*.gpr.py'` dropped from find, `patch.diff:40-41`; (e) `maintenance/gramps[0-9][0-9]` in `ci.yml:14,17` + `docker-build.yml:56`. |
| C4 — C4 Verification (red→green) | FAIL | `check-gates.json` C4-verify is gating FAIL: `error: .github/workflows/ci.yml: patch does not apply`. Third consecutive iteration failing on patch-apply against the verification base — red→green was never executed, so the fix is unverified. Re-cut all hunks against current `origin/feature/ci-cd-pipeline-upstream`. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Contested root cause carried from iter-1. Patch now sweeps `(None, *PTYPE)` and claims `{None} ∪ PTYPE` reproduces the full master list so a typeless (`_ptype is None`) addon still surfaces (`patch.diff:157-174`). The claim hinges on `registry.type_plugins(None)` actually returning `_ptype is None` records — that depends on gramps `_pluginreg.py`, which is not in the bundle and cannot be verified artifact-only. Human must confirm against `gen/plug/_pluginreg.py`. |
| T1 — T1 Structure | N/A | `patch.diff` touches only `tests/` and `.github/workflows/`; it adds no addon (no addon folder, no `.gpr.py`). The doc-16 addon-layout gate (folder==id, target_version, fname, no `__init__.py`) is inapplicable to a tests/CI cleanup. The gate's advisory FAIL (`no .gpr.py`) is an addon-oriented false positive here. |
| T2 — T2 Shape | PASS | Both new files carry the full GPL header and follow the section-comment idiom: `tests/addon_paths.py` (`patch.diff:66-83`) and `tests/test_addon_paths.py` (`patch.diff:202-219`). Matches `check-gates.json` T2 ✓ (2 files conform). |
| T3 — T3 Runtime | NEEDS-HUMAN | `check-gates.json`: gramps60×6.0 green; gramps61×6.1 delta = 1 new failure `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq`. The patch touches no Sqlite code (`patch.diff`), and the delta shrank 8→1→1 across iters — strongly suggests 6.1 baseline noise, but attribution (noise vs regression) is a human call; confirm it reproduces on the base without this patch. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle to evaluate against doc-16 §Commit messages / §Contributor workflow (`check-gates.json` T4 path_line). |
| T5 — T5 Judgment | NEEDS-HUMAN | Scope/splitting concern standing since iter-1. The brief flags the five nits as independent and splittable and invokes one-logical-change-per-PR (`brief.md:5-6,37,51`); iter-1/iter-2 carry-forward direct that item (b)'s enumeration fix be its own change at minimum. `patch.diff` bundles all five into one diff. Whether to split is a human judgment. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. Does this satisfy the brief's success criterion — each nit resolved AND PR #820 CI green on the `eduralph/addons-source` fork? CI-green cannot be observed from the bundle (and C4 never ran). Human sign-off required. |

## §6 — Items the human must clear (each NEEDS-HUMAN row)

1. **C5 — causal adequacy of item (b).** Verify against gramps `gen/plug/_pluginreg.py`
   that `type_plugins(None)` returns records with `_ptype is None`, so the
   `(None, *PTYPE)` sweep truly re-includes a half-registered/typeless addon (the
   exact silent-coverage-loss the iter-1 rejection named). Not verifiable artifact-only.
2. **T3 — gramps61×6.1 Sqlite delta.** Confirm `ExportSQLTestCase::test_export_sq` is
   pre-existing 6.1 baseline noise (patch touches no Sqlite code; delta trend 8→1→1)
   and not a regression introduced by the `.gpr.py`/`py_compile` or `type_plugins()` change.
3. **T5 — scope/splitting.** Decide whether the five independent nits ship as one PR
   or split per logical change (item (b) at minimum), per `brief.md:5-6,37,51` and the
   standing carry-forward.
4. **V — fitness-to-purpose.** Confirm the end result meets the brief's success
   criterion, including PR #820 CI green on the fork — not observable from the bundle.

## §7 — Gating blocker (independent of the human items)

**C4 is a gating FAIL** and blocks sign-off regardless of the §6 items: the patch does
not apply to the verification base (`.github/workflows/ci.yml`), so red→green was never
run. This is the same failure mode as iterations 2 and 3. The patch must be re-cut
against the current `origin/feature/ci-cd-pipeline-upstream` and the C4 run must go
red-pre/green-post before the §6 advisory items are worth re-adjudicating.

_Minor (non-gating) note for the builder: `tests/test_addon_paths.py:285` passes
`None` to `is_in_addons_tree`, whose signature annotates `fpath: str`; the runtime
`if not fpath` guard handles it, but the annotation and the test disagree._
