# Check gates — issue_addon-tests-init-py-gramps60

**Overall (gating): fail**

The Check 5/5/1: 5 correctness · 5 conformance · 1 validation.

## Correctness (5)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| C1 Spec | none | brief.md | — | — | no |
| C2 Reproduction (red pre-fix) | none | (no gate configured) | — | — | no |
| C3 Change | none | patch.diff | — | — | no |
| C4 fix verified: test red pre-fix, green post-fix | fail | ./engine/scripts/ubuntu/run-verify.sh | C4-verify | run-verify.sh: patch ships no addon test (test_*.py) to verify | yes |
| C5 Causal adequacy | none | reviewer + human sign-off | — | — | no |

## Conformance (5)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) | fail | python3 ./engine/conformance/gate.py T1 | T1-structure | T1 ⚠ TMGimporter: tests/ lacks the __init__.py marker (doc16-addon §Structure, SHOULD) | no |
| T2 shape: code shape vs doc 16 §Coding style (GPL header, no diagnostic print) | fail | python3 ./engine/conformance/gate.py T2 | T2-shape | T2 ✗ test_linux_libtmg.py: no GPL licence header in the first 40 lines (AGENTS.md §File Headers) | no |
| T3 runtime: gramps core unit suite (whole-suite baseline) | fail | python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-unit.sh | T3-unit | T3-baseline [delta]: DELTA: 7 new failure(s) not in baseline: gramps.plugins.test.imports_test.TestImports::test_imp_3_4 | no |
| T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix) | fail | CORE_VERSION=6.0 PDCA_T3_BASELINE=engine/baselines/run-addon-unit-60.json python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-addon-unit.sh | T3-addon-unit-60 | T3-baseline [delta]: DELTA: runner exited 1 with no parsed failures and no matching baseline signature (a new failure mo | no |
| T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) | fail | CORE_VERSION=6.1 PDCA_T3_BASELINE=engine/baselines/run-addon-unit-61.json python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-addon-unit.sh | T3-addon-unit-61 | T3-baseline [delta]: DELTA: runner exited 1 with no parsed failures and no matching baseline signature (a new failure mo | no |
| T3 runtime: GUI interface smoke (launch + open tree, headless dogtail) | fail | python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-interface.sh test_smoke.py | T3-interface | T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest) | no |
| T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow | pass | python3 ./engine/conformance/gate.py T4 | T4-contribution | T4 – N/A: no commit-msg.txt or pr-description.md in the bundle | no |
| T5 Judgment | none | reviewer + human sign-off | — | — | no |

## Validation (1)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| Validation — fitness-to-purpose | none | human at sign-off | — | — | no |
