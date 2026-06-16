# Check gates — issue_tmg-os-test-split-gramps61

**Overall (gating): fail**

The Check 5/5/1: 5 correctness · 5 conformance · 1 validation.

## Correctness (5)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| C1 Spec | none | brief.md | — | — | no |
| C2 Reproduction (red pre-fix) | none | (no gate configured) | — | — | no |
| C3 Change | none | patch.diff | — | — | no |
| C4 fix verified: test red pre-fix, green post-fix | fail | ./engine/scripts/ubuntu/run-verify.sh | C4-verify | — | yes |
| C5 Causal adequacy | none | reviewer + human sign-off | — | — | no |

## Conformance (5)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) | pass | python3 ./engine/conformance/gate.py T1 | T1-structure | T1 ✓ structure: 1 addon(s) conform to doc 16 §Structure | no |
| T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer) | fail | python3 ./engine/conformance/gate.py T2 | T2-shape | T2 ✗ test_libtmg.py: no GPL licence header in the first 40 lines (AGENTS.md §File Headers) | no |
| T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix) | fail | CORE_VERSION=6.0 PDCA_T3_BASELINE=engine/baselines/run-addon-unit-60.json python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-addon-unit.sh | T3-addon-unit-60 | T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo | no |
| T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) | fail | CORE_VERSION=6.1 PDCA_T3_BASELINE=engine/baselines/run-addon-unit-61.json python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-addon-unit.sh | T3-addon-unit-61 | T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo | no |
| T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow | pass | python3 ./engine/conformance/gate.py T4 | T4-contribution | T4 – N/A: no commit-msg.txt or pr-description.md in the bundle | no |
| T5 Judgment | none | reviewer + human sign-off | — | — | no |

## Validation (1)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| Validation — fitness-to-purpose | none | human at sign-off | — | — | no |
