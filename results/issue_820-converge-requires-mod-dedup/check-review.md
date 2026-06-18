# Check review — issue_820-converge-requires-mod-dedup

Advisory, artifact-only. Inputs: `patch.diff`, `brief.md`, `check-gates.json`
(`build-notes.md` withheld by design — Do's own narrative is NOT an input here).
Each Basis below is re-derived from the artifacts, not copied from the gate output.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | `brief.md` is complete and well-formed: slug, defect (3 `requires_mod` heredocs + ~6 `is_active()` copies), success criterion (single owned module + one sourced helper, derived sets unchanged), per-category invariant, scope and out-of-scope all stated (`brief.md:15-66`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Red-pre-fix is structural: `tests/test_requires_mod_dedup.py:611` imports `addon_python_deps` at module load (ImportError when the new module is absent → every test errors), and `test_no_requires_mod_heredoc_remains` / `test_no_inline_is_active_definition_remains` (`:677,:702`) assert against ci.yml content that exists pre-fix. No gate configured (`check-gates.json` C2 "none"); the red contract is re-derivable from the test as written. |
| C3 — C3 Change | PASS | Diff implements the scope cleanly: 3 `requires_mod` heredocs → `addon_python_deps.py --install-list` (`patch.diff:309,399,489`), 3 validator heredocs → `--check-resolves` (`:357,447,537`), 6 inline `is_active()` → `source .github/scripts/active_addons.sh` (`:250,267,284,374,464,554`). New module + helper + regression test added. Counts match the test's own expectations (3/3/≥6). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | `brief.md:37-41` states C4 is `.github/` CI-infra the local `run-verify.sh` cannot exercise; fork-CI green on `eduralph/addons-source` is the acceptance signal. The gate's local fail is environmental (`check-gates.json:37` "worktree … missing"), and fork-CI status is not observable from these artifacts (build-notes withheld). Human must confirm fork CI is green. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Dedup itself fully addresses the (uncontested) copy-paste root cause. BUT `_IMPORT_TO_DISTRIBUTION = {"PIL": "Pillow"}` (`addon_python_deps.py:101-103`) changes the derived *install* union vs the old map-less heredoc — `brief.md:80-86` flags this as an in-scope-correction-vs-scope-creep decision that must be stated; build-notes (withheld) is where that decision would live. The regression test bakes the same map into its "old" oracle (`tests/test_requires_mod_dedup.py:616,661`), so it does NOT detect the change. Scope/correctness decision is human's. |
| T1 — T1 Structure | N/A | Gate "fail" is a false positive: it expects a Gramps addon (`.gpr.py`, `folder==id`, `target_version`), but the patch adds CI scripts (`.github/scripts/*`) and a root-level test (`tests/test_requires_mod_dedup.py`) — no addon package is added or changed. Addon-structure rules do not apply. |
| T2 — T2 Shape | N/A | No addon-package `.py` is touched (gate scopes the GPL-header / `print()` check to addon dirs; `check-gates.json:64`). Advisory only: the two new files `addon_python_deps.py` and `tests/test_requires_mod_dedup.py` carry no GPL header — outside the gate's scope but worth a human glance against doc 16 §Coding style. |
| T3 — T3 Runtime | NEEDS-HUMAN | core-6.0 lane green (`check-gates.json:73`); core-6.1 lane shows 1 new delta `Sqlite…ExportSQLTestCase::test_export_sq` (`:82`). The patch touches only `.github/` + a root test and cannot plausibly affect a Sqlite addon export suite, so the delta is decorrelated from this diff (flaky / pre-existing baseline drift) — but a red delta cannot be self-cleared from artifacts. Human to confirm it is not diff-caused. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle (`check-gates.json:91`); nothing to check against doc 16 §Commit messages / §Contributor workflow. |
| T5 — T5 Judgment | NEEDS-HUMAN | Oracle is reviewer + human sign-off. Mechanically the refactor is sound and behaviour-preserving on the find_spec (raw-name) side (`tests/test_requires_mod_dedup.py:664-675`), but the open PIL→Pillow scope call (C5) and missing GPL headers (T2 advisory) need a holistic human judgment before sign-off. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always human at sign-off (`check-gates.json:107`; `brief.md:68-71` STOP discipline). Acceptance = PR #820 CI green on the fork with derived sets unchanged — a fitness judgment not observable from artifacts. |

## §6 — Items the human must clear

Each NEEDS-HUMAN row above is a §6 item:

1. **C4 — fork-CI verification.** Confirm `feature/ci-cd-pipeline-upstream` pushed to
   `eduralph/addons-source` ran `ci.yml` + `docker-build.yml` **green**. The local C4
   fail is environmental and expected per `brief.md:37-41`; it is NOT the acceptance signal.

2. **C5 / scope — PIL→Pillow install-name map.** The new module introduces
   `_IMPORT_TO_DISTRIBUTION = {"PIL": "Pillow"}` (`addon_python_deps.py:101-103`), which
   the pre-fix heredocs lacked. This **changes the derived install union** for
   EditExifMetadata (`pip install PIL` → `pip install Pillow`). `brief.md:80-86` requires
   this be decided as in-scope-correction vs scope-creep and stated; the decision lives in
   the withheld build-notes. The regression test cannot flag it — it folds the same map
   into its oracle (`tests/test_requires_mod_dedup.py:616,661`). Human must ratify the
   behaviour change (or rule it scope creep). Raw declared names *are* preserved, so the
   `find_spec` gate is unaffected (`:664-675`).

3. **T3 — core-6.1 delta.** `Sqlite…ExportSQLTestCase::test_export_sq` is a new failure on
   the 6.1 lane only. Re-derived as decorrelated from this `.github`-only diff (flaky /
   pre-existing baseline), but a human must confirm it is not diff-caused before clearing.

4. **T5 — holistic sign-off** gating on (2) and the T2 GPL-header advisory.

5. **V — fitness-to-purpose** at sign-off.

## Advisory notes (non-gating)

- **GPL header.** `addon_python_deps.py` and `tests/test_requires_mod_dedup.py` ship no
  license header (doc 16 §Coding style). Outside the T2 gate's scope but flag for the human.
- **Behaviour-preservation claim.** The test's "behaviour-preserving" docstring is accurate
  for the **raw** name set (find_spec gate) but NOT for the **install** union, where the
  PIL→Pillow map is a deliberate change baked into the oracle — see §6.2.
- **Per-category invariant honoured.** `test_every_is_active_call_site_sources_the_helper`
  (`tests/test_requires_mod_dedup.py:710-723`) checks every calling step sources the helper,
  not "at least once" — matches `brief.md:87-89`.
