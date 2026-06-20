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
