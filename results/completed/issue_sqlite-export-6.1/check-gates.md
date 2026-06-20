# Check gates — issue_sqlite-export-6.1

**Overall (gating): fail**

The Check 5/5/1: 5 correctness · 5 conformance · 1 validation.

## Correctness (5)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| C1 Spec | none | brief.md | — | — | no |
| C2 Reproduction (red pre-fix) | none | (no gate configured) | — | — | no |
| C3 Change | none | patch.diff | — | — | no |
| C4 fix verified: test red pre-fix, green post-fix | fail | ./engine/scripts/ubuntu/run-verify.sh | C4-verify | C4-verify: green-with-fix=PASS / red-without-fix=PASS | yes |
| C5 Causal adequacy | none | reviewer + human sign-off | — | — | no |

## Conformance (5)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) | fail | python3 ./engine/conformance/gate.py T1 | T1-structure | T1 ✗ Sqlite: addon dir has __init__.py — breaks plugin loading (doc16-addon §Structure, Mantis 12691) | no |
| T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer) | fail | python3 ./engine/conformance/gate.py T2 | T2-shape | T2 ⚠ ImportSql.py:897 candidate diagnostic print() — reviewer to confirm it is not intentional output (AGENTS.md §Loggin | no |
| T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix) | pass | CORE_VERSION=6.0 PDCA_T3_BASELINE=engine/baselines/run-addon-unit-60.json python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-addon-unit.sh | T3-addon-unit-60 | T3-baseline [green]: green (no failures) | no |
| T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) | fail | CORE_VERSION=6.1 PDCA_T3_BASELINE=engine/baselines/run-addon-unit-61.json python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-addon-unit.sh | T3-addon-unit-61 | T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq | no |
| T3 runtime: GUI interface smoke (launch + open tree, headless dogtail) | pass | CORE_VERSION=6.1 python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-interface.sh test_smoke.py | T3-interface | T3-baseline [baseline]: matches recorded baseline: 1 known test red(s); signature '_ErrorHolder (Glade __setattr__ name- | no |
| T3 runtime: addon E2E (addon loaded in headless gramps GUI, dogtail) | fail | python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-addon-interface.sh | T3-addon-interface | T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest) — raw runner o | no |
| T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow | pass | python3 ./engine/conformance/gate.py T4 | T4-contribution | T4 – N/A: no commit-msg.txt or pr-description.md in the bundle | no |
| T5 Judgment | none | reviewer + human sign-off | — | — | no |

## Validation (1)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| Validation — fitness-to-purpose | none | human at sign-off | — | — | no |
