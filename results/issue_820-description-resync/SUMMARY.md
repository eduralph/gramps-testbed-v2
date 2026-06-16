# Result — issue 820-description-resync / 820-description-resync

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: PR #820's description is materially out of sync with HEAD of
- Success criterion: the PR #820 description's gate policy, file list, and commit
- Repo + branch target: gramps-project/addons-source — PR #820 description text
- Scope (one logical fix) / out of scope: rewrite the PR #820 description prose to match HEAD. / out of scope: any

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix (prose; trivial, high reviewer-trust payoff).
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — run-verify.sh: patch ships no addon test (test_*.py) to verify
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 – N/A: no checkable .py path in patch.diff
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 2 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [baseline]: matches recorded baseline: 1 known test red(s); signature '_ErrorHolder (Glade __setattr__ name-
- T3 runtime: addon E2E (addon loaded in headless gramps GUI, dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — 820-description-resync (advisory, artifact-only)

Decorrelated re-derivation from `patch.diff`, `brief.md`, `check-gates.json` only
(`build-notes.md` withheld). `patch.diff` is **not** a repo-file patch — it is the
before→after of the gramps-project/addons-source PR #820 *description body*. The
change touches **no repo files**.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | `brief.md:8-21` gives a well-formed spec: three concrete drifts (gate policy, six omitted files, 7-of-21 commit table) + a testable success criterion (body matches HEAD tree & `ci.yml` `continue-on-error`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The diff "before" half exhibits all three drifts on its face: gate policy lists Lint+both Unit jobs as advisory (`patch.diff:67`), file list omits the six paths, commit table stops at `205b21c` = 7 rows (`patch.diff:78-85`). Claim that before == live `gh pr view 820` body is unverifiable artifact-only → deferred to V. |
| C3 — C3 Change | PASS | After-text resolves every documented drift: only Addon Structure advisory (`patch.diff:68-69`); six files restored — `addon_system_deps.py`/`run_addon_tests.py`/`gi_bootstrap/sitecustomize.py` (`patch.diff:42-44`), `test_addon_dependencies.py` (`:49`), `CONTRIBUTING.md` (`:59`), `CI-MAINTAINER.md` (`:60`); commit table now 21 rows `774a9ac`…`1466491` (`patch.diff:78-100`). |
| C4 — C4 Verification (red→green) | N/A | No red→green test, and none required: documentation/prose change under the no-test exemption (`brief.md:35-37`, principles §1.1). The gating `C4-verify` FAIL ("patch ships no addon test", `check-gates.json:33-39`) is a mechanical false-positive against an exempt doc change — it does not establish incorrectness. The substantive verification ("after-text provably matches HEAD") is not a test gate and is routed to V. |
| C5 — C5 Causal adequacy | PASS | Each fix maps to its cause: the staleness is description-vs-HEAD drift on three axes, and the rewrite corrects each axis at its source rather than papering over symptoms. Root cause is not contested. Whether the three enumerated drifts are the *complete* set of stale sections is a fitness question → V. |
| T1 — T1 Structure | N/A | §Structure is addon-only; `patch.diff` contains no addons-source path (prose-only PR-description change). Matches gate basis `check-gates.json:55`. |
| T2 — T2 Shape | N/A | No checkable `.py` path in `patch.diff`; GPL-header / code-shape rules do not apply to a PR-description body. Matches gate basis `check-gates.json:64`. |
| T3 — T3 Runtime | N/A | Patch alters zero repo files, so it cannot change any test's runtime behaviour. The advisory T3 deltas in `check-gates.json:69-103` (addon-unit 60/61, addon E2E `setUpClass` smoke failure) are not attributable to a prose-only change — they are pre-existing/environment noise (consistent with the carry-forward's stale+dirty-tree note, `brief.md:50`). All T3 rows are `gating:false`. |
| T4 — T4 Contribution | PASS | The deliverable *is* a contribution wrapper (PR body) and it conforms to the PR-description conventions — Scope / What's in the PR / Gate policy / Commits table / Local reproduction / Companion PRs, with the Claude Code footer (`patch.diff:111`). Gate reported N/A because the body is carried as `patch.diff` rather than a `pr-description.md` file (`check-gates.json:109`), so the mechanical gate did not inspect it; on direct read it is well-formed. |
| T5 — T5 Judgment | PASS | Advisory judgment: the change is proportionate and stays inside the declared scope (prose only; no `ci.yml` / workflow edit, per `brief.md:28-30`). Final ratification remains a human sign-off (oracle: reviewer + human). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human, and genuinely unverifiable artifact-only: the success criterion is "body matches HEAD's tree & `ci.yml` `continue-on-error` so a reviewer reading only the body draws correct conclusions" (`brief.md:19-21`). The patch *asserts* after == HEAD @ `1466491ab` and before == live PR body, but confirming both — and that no other PR section is still stale — requires the live repo + PR (network), which this bundle lacks. The carry-forward flags exactly this gap: the match could not be confirmed against the prior stale/dirty tree and HEAD may have moved past `1466491ab` (`brief.md:50`). |

## §6 — items the human must clear

1. **V — Validation / fitness-to-purpose (NEEDS-HUMAN).** Re-derive/confirm the
   "after" body against the *currently-synced* HEAD of
   `feature/ci-cd-pipeline-upstream`, then run the brief's three repro commands
   (`brief.md:31-34`): `grep -n continue-on-error .github/workflows/ci.yml` →
   `addon-structure` only; `gh pr view 820 --json files` vs the body's file list;
   `git log --oneline feature/ci-cd-pipeline-upstream` = 21 commits vs the body's
   table. Also confirm the live PR body equals the diff's "before" (so the diff is
   the actual edit) and that no PR section beyond the three enumerated drifts is
   still stale. Until done, the success criterion is asserted, not verified.

## Note on the gating gate

The bundle's `overall: fail` is driven solely by the one `gating:true` row,
`C4-verify` (`check-gates.json:39`). That FAIL is the no-addon-test gate firing on a
documentation change that the brief explicitly exempts (§1.1). As advisory Check, I
do **not** treat C4 as a blocker here; the only open question is V, above.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] V — Validation — fitness-to-purpose — Always-human, and genuinely unverifiable artifact-only: the success criterion is "body matches HEAD's tree & `ci.yml` `continue-on-error` so a reviewer reading only the body draws correct conclusions" (`brief.md:19-21`). The patch *asserts* after == HEAD @ `1466491ab` and before == live PR body, but confirming both — and that no other PR section is still stale — requires the live repo + PR (network), which this bundle lacks. The carry-forward flags exactly this gap: the match could not be confirmed against the prior stale/dirty tree and HEAD may have moved past `1466491ab` (`brief.md:50`).

## 7. Proven / not proven
- Proven by which oracle: gates overall = fail (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-06-13

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
