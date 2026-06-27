# Check gates — issue_7344

**Overall (gating): pass**

The Check 5/5/1: 5 correctness · 5 conformance · 1 validation.

## Correctness (5)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| C1 Spec | none | brief.md | — | — | no |
| C2 Reproduction (red pre-fix) | none | (no gate configured) | — | — | no |
| C3 Change | none | patch.diff | — | — | no |
| C4 fix verified: test red pre-fix, green post-fix | unverifiable | ./engine/scripts/ubuntu/run-verify.sh | C4-verify | patch ships no addon test (test_*.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change | yes |
| C5 Causal adequacy | none | reviewer + human sign-off | — | — | no |

## Conformance (5)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) | pass | python3 ./engine/conformance/gate.py T1 | T1-structure | T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only) | no |
| T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer) | pass | python3 ./engine/conformance/gate.py T2 | T2-shape | T2 – N/A: no checkable .py path in patch.diff | no |
| T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix) | pass | CORE_VERSION=6.0 PDCA_T3_BASELINE=engine/baselines/run-addon-unit-60.json python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-addon-unit.sh | T3-addon-unit-60 | T3-baseline [green]: green (no failures) | ⚠ baseline tree drift: recorded detached@6235c3ba3a, tested detached@32aa2962 | no |
| T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix) | fail | CORE_VERSION=6.1 PDCA_T3_BASELINE=engine/baselines/run-addon-unit-61.json python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-addon-unit.sh | T3-addon-unit-61 | T3-baseline [delta]: DELTA: 4 new failure(s) not in baseline: LifeLineChartView.collection::import_or_collection, PDFFor | no |
| T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow | pass | python3 ./engine/conformance/gate.py T4 | T4-contribution | T4 – N/A: no commit-msg.txt or pr-description.md in the bundle | no |
| T5 Judgment | none | reviewer + human sign-off | — | — | no |

## Validation (1)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| Validation — fitness-to-purpose | none | human at sign-off | — | — | no |
