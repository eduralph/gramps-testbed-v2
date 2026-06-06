# Check gates — issue_11786

**Overall (gating): fail**

The Check 5/5/1: 5 correctness · 5 conformance · 1 validation.

## Correctness (5)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| C1 Spec | none | brief.md | — | — | no |
| C2 Reproduction (red pre-fix) | none | (no gate configured) | — | — | no |
| C3 Change | none | patch.diff | — | — | no |
| C4 fix verified: test red pre-fix, green post-fix | fail | ./engine/scripts/ubuntu/run-verify.sh | C4-verify | C4-verify: green-with-fix=FAIL / red-without-fix=PASS | yes |
| C5 Causal adequacy | none | reviewer + human sign-off | — | — | no |

## Conformance (5)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) | pass | python3 ./engine/conformance/gate.py T1 | T1-structure | T1 – N/A: no addons-source path in patch.diff (core-only change) | no |
| T2 shape: code shape vs doc 16 §Coding style (GPL header, no diagnostic print) | pass | python3 ./engine/conformance/gate.py T2 | T2-shape | T2 – N/A: no addons-source path in patch.diff (core-only change) | no |
| T3 runtime: gramps core unit suite (whole-suite baseline) | fail | ./engine/scripts/ubuntu/run-unit.sh | T3-unit | bash: line 39:   254 Trace/breakpoint trap   (core dumped) GRAMPS_RESOURCES=. python3 -m xmlrunner discover -p "*_test.p | no |
| T3 runtime: addon unit suites (whole-suite baseline) | fail | ./engine/scripts/ubuntu/run-addon-unit.sh | T3-addon-unit | → pip install logs (3 failure(s)): gramps-testbed-v2/test-results/install-logs/ | no |
| T3 runtime: GUI interface smoke (launch + open tree, headless dogtail) | fail | ./engine/scripts/ubuntu/run-interface.sh test_smoke.py | T3-interface | Generated XML report: test-results/TEST-unittest.suite._ErrorHolder-20260605210630.xml | no |
| T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow | pass | python3 ./engine/conformance/gate.py T4 | T4-contribution | T4 – N/A: no commit-msg.txt or pr-description.md in the bundle | no |
| T5 Judgment | none | reviewer + human sign-off | — | — | no |

## Validation (1)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| Validation — fitness-to-purpose | none | human at sign-off | — | — | no |
