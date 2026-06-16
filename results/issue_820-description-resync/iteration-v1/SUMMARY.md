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
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): pass — T3-baseline [green]: green (no failures)
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T3 runtime: addon E2E (addon loaded in headless gramps GUI, dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — issue 820-description-resync

> Advisory, artifact-only, decorrelated from the builder. Inputs seen:
> `patch.diff`, `brief.md`, `check-gates.json` (build-notes.md withheld by design).
> The deliverable is a **PR-description prose rewrite** — `patch.diff` is the
> before/after of PR #820's body, not a code change. It touches **zero repo files**.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | brief.md gives an explicit defect (3 enumerated drifts), success criterion (brief.md:19-21), and scope fence (brief.md:28-30). Spec is unambiguous. |
| C2 — C2 Reproduction (red pre-fix) | N/A | Prose-only change — no executable red test is possible. The "before" column of `patch.diff` (lines 7, 17, 25, 28, 58-59, 63, 70-77, 100) IS the documented stale state; repro is the 3 manual commands in brief.md:31-34. No gate configured (check-gates.json:16). |
| C3 — C3 Change | PASS | Diff addresses all three defects: advisory→only Addon Structure (patch.diff:60-61); six omitted files restored (patch.diff:34-36 scripts, :41 test_addon_dependencies, :51-52 CONTRIBUTING/CI-MAINTAINER); commit table 7→21 rows (patch.diff:79-92). Internally consistent. |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | C4 gate FAILs and is gating: "patch ships no addon test (test_*.py)" (check-gates.json:33-39). But the deliverable is prose; brief.md:35-37 declares "no test — documentation change (principles §1.1)," manual verification only. The gate applies a code-change oracle to a doc change. Human must accept the no-test exemption — it is the only gating failure. |
| C5 — C5 Causal adequacy | PASS | Root cause = description drifted from HEAD; fix rewrites the description and leaves `ci.yml`/gate wiring untouched per scope (brief.md:28-30, "the state is correct; only the description is stale"). Approach targets the actual defect, not a symptom. Root cause uncontested. (advisory; oracle = reviewer + human sign-off) |
| T1 — T1 Structure | N/A | No addons-source / addon path in `patch.diff` — §Structure (folder==id, target_version, fname) is addon-only; nothing checkable (check-gates.json:55). |
| T2 — T2 Shape | N/A | No checkable `.py` path in `patch.diff` — GPL-header / print() shape rules do not apply to a description rewrite (check-gates.json:64). |
| T3 — T3 Runtime | N/A | `patch.diff` changes no runtime code. The 3 red deltas (gramps61 `ExportSQLTestCase::test_export_sq`, GUI smoke `setUpClass` ×2 — check-gates.json:82,91,100) cannot be caused by a PR-description edit; they are pre-existing/environmental and not attributable to this change. gramps60 is green (check-gates.json:73). |
| T4 — T4 Contribution | PASS | The contribution IS the rewritten PR body in `patch.diff`; it is well-formed (Scope, What's-in-the-PR, Gate policy, 21-row commit table, Companion PRs). Note: gate auto-N/A'd looking for `pr-description.md`/`commit-msg.txt` by filename (check-gates.json:109) — a filename miss, the artifact is present. |
| T5 — T5 Judgment | NEEDS-HUMAN | Oracle = reviewer + human sign-off (check-gates.json:116). Advisory read is positive: coherent, all three defects resolved, no scope creep into `ci.yml`. Final judgment is the human's. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. The success criterion is "matches HEAD's tree and ci.yml's actual continue-on-error settings" (brief.md:19-21). Neither HEAD's tree, `ci.yml`, nor `gh pr files` is in this bundle — I verified the body's **internal** consistency against the brief's assertions, not against HEAD itself. Human must confirm the after-text actually matches HEAD `1466491ab`. |

## §6 — Items the human must clear

1. **C4 — documentation no-test exemption (gating).** The only gating gate failure
   is C4: the harness expects a `test_*.py` and the prose change ships none. brief.md:35
   invokes principles §1.1 (documentation change → no test, manual verification). The
   human must accept this exemption to clear the gating fail, OR reject it if a
   verification artifact is expected.

2. **T5 — reviewer/human judgment sign-off.** Per oracle, T5 needs human sign-off.
   My advisory read is favourable; no blocker found beyond the artifact-bundle limits.

3. **V — fitness-to-purpose, after-text vs HEAD.** I could not verify the rewritten
   body against HEAD's real tree or `ci.yml` (not in the bundle). A human must run the
   brief.md:31-34 commands against HEAD and confirm: (a) only `addon-structure` carries
   `continue-on-error: true`; (b) the six listed files match `gh pr view 820 --files`;
   (c) the 21-commit table matches `git log feature/ci-cd-pipeline-upstream`.

## Notes on the red gates (decorrelation)

The overall check-gates verdict is `fail`, driven by one **gating** gate (C4) and three
non-gating T3 deltas. None of the four are attributable to this change:

- **C4** fails structurally — a prose diff can't carry a `test_*.py`; the gate's oracle
  is mis-matched to a documentation deliverable (handled as §6 item 1).
- **T3** gramps61/GUI-smoke deltas are runtime tests of Gramps/addon code; `patch.diff`
  edits no code, so these are environmental/pre-existing, not regressions from this PR.

No defect in the change itself was found in the artifacts provided. Residual risk is the
HEAD-match (V), which is unverifiable from this bundle by design.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C4 — C4 Verification (red→green) — C4 gate FAILs and is gating: "patch ships no addon test (test_*.py)" (check-gates.json:33-39). But the deliverable is prose; brief.md:35-37 declares "no test — documentation change (principles §1.1)," manual verification only. The gate applies a code-change oracle to a doc change. Human must accept the no-test exemption — it is the only gating failure.
- [ ] T5 — T5 Judgment — Oracle = reviewer + human sign-off (check-gates.json:116). Advisory read is positive: coherent, all three defects resolved, no scope creep into `ci.yml`. Final judgment is the human's.
- [ ] V — Validation — fitness-to-purpose — Always-human. The success criterion is "matches HEAD's tree and ci.yml's actual continue-on-error settings" (brief.md:19-21). Neither HEAD's tree, `ci.yml`, nor `gh pr files` is in this bundle — I verified the body's **internal** consistency against the brief's assertions, not against HEAD itself. Human must confirm the after-text actually matches HEAD `1466491ab`.

## 7. Proven / not proven
- Proven by which oracle: gates overall = fail (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: iterated-to-Do
- Iteration delta (if iterating): Rebuild on the latest code foundation. This bundle was built/reviewed against a stale tree: local main is 11 commits behind origin/main AND dirty (uncommitted edits to engine/scripts/lib/addon_system_deps.py + addon_python_deps.py). A "description-resync to HEAD" deliverable is only meaningful against the CURRENT HEAD, so the rebuild must happen after gramps-testbed-v2 is synced to latest. Why iterate rather than accept (the change itself is sound): - The advisory review found no defect in the prose rewrite (C1/C3/C5/T4 PASS); the diff correctly resolves the three documented drifts (gate policy, the six restored file entries, 7->21 commit table). - BUT the success criterion is "matches HEAD (1466491ab) and ci.yml's actual continue-on-error settings" (V). That match could NOT be verified against a stale/dirty tree, and HEAD may have moved past 1466491ab. Re-derive the "after" text against the freshly-synced HEAD so the description provably matches it, then re-confirm V (gh pr view 820 --files; git log on the PR branch; the addon-structure-only continue-on-error grep). - C4 is a non-blocker: doc/prose change, no-test exemption under principles §1.1 — not a reason to change anything. Batch note: stop the flow after this batch completes and update gramps-testbed-v2 to origin/main (reconcile the local lib edits first) before any rebuild runs.
- By / date: Eduard Ralph / 2026-06-10

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
