# Check gates — issue_6583

**Overall (gating): pass**

The Check 5/5/1: 5 correctness · 5 conformance · 1 validation.

## Correctness (5)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| C1 Spec | none | brief.md | — | — | no |
| C2 Reproduction (red pre-fix) | none | (no gate configured) | — | — | no |
| C3 Change | none | patch.diff | — | — | no |
| C4 fix verified: test red pre-fix, green post-fix | pass | ./engine/scripts/ubuntu/run-verify.sh | C4-verify | C4-verify: green-with-fix=PASS / red-without-fix=PASS | yes |
| C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) | unverifiable | ./engine/scripts/ubuntu/run-verify-interface.sh | C4-verify-interface | no interface repro engine/interface/test_bug_*6583_*.py for bundle issue_6583 — the per-fix GUI red→green cannot run; th | no |
| C5 Causal adequacy | none | reviewer + human sign-off | — | — | no |

## Conformance (5)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py) | pass | python3 ./engine/conformance/gate.py T1 | T1-structure | T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only) | no |
| T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer) | pass | python3 ./engine/conformance/gate.py T2 | T2-shape | T2 ✓ shape: 11 file(s) conform to doc 16 §Coding style (1 advisory) | no |
| T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files) | pass | python3 ./engine/conformance/gate.py T2-potfiles | T2-potfiles | T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files) | yes |
| T3 runtime: gramps core unit suite (whole-suite baseline) | pass | CORE_VERSION=6.1 python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-unit.sh | T3-unit | T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b | no |
| T3 runtime: GUI interface smoke (launch + open tree, headless dogtail) | pass | CORE_VERSION=6.1 python3 ./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-interface.sh test_smoke.py | T3-interface | T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded  | no |
| T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow | pass | python3 ./engine/conformance/gate.py T4 | T4-contribution | T4 – N/A: no commit-msg.txt or pr-description.md in the bundle | no |
| T5 Judgment | none | reviewer + human sign-off | — | — | no |

## Validation (1)

| Check | Result | Oracle | Rule | Evidence | Gating |
|---|---|---|---|---|---|
| Validation — fitness-to-purpose | none | human at sign-off | — | — | no |
