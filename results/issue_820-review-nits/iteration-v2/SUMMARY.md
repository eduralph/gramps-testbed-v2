# Result — issue 820-review-nits / 820-review-nits

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: a set of independent low-risk issues in PR #820's test/harness code:
- Success criterion: each item resolved — (a) helper wired in or removed; (b)
- Repo + branch target: gramps-project/addons-source @ `maintenance/gramps60` via
- Scope (one logical fix) / out of scope: the five cleanups above. / out of scope: the lib convergence

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix (small, low-risk; splittable).
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — error: .github/workflows/ci.yml: patch does not apply
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): fail — T1 ✗ tests: no .gpr.py — addon registers via .gpr.py (doc16-addon §Structure)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 2 file(s) conform to doc 16 §Coding style
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): pass — T3-baseline [green]: green (no failures)
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — issue 820-review-nits (iteration 2)

> Advisory, artifact-only, decorrelated. Inputs: `patch.diff`, `brief.md`,
> `check-gates.json`. `build-notes.md` withheld by design — verdicts below are
> re-derived from the patch and brief, not from the builder's narrative.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | `brief.md` is a complete, coherent spec: defect (a)–(e) (brief.md:9-22), success criterion (brief.md:23-26), per-item repro (brief.md:40-43), test-file requirement (brief.md:44-46). |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | No repro gate configured (check-gates.json:15-21). (a)/(b)/(d)/(e) are behaviour-preserving/CI-observable — no failing test to reproduce. (c)'s new `test_addon_paths.py` exercises the *new* `is_in_addons_tree` helper, so it never ran red against the old `ADDONS_ROOT in pdata.fpath` code (patch.diff:247-285); red pre-fix state is unverifiable from artifacts. |
| C3 — C3 Change | PASS | All five nits implemented: (a) `make_gramps_user` removed (patch.diff:121-129); (b) public `type_plugins()` sweep (patch.diff:167-176); (c) `is_in_addons_tree` prefix check (patch.diff:99-112); (d) `.gpr.py` no longer excluded from `py_compile` (patch.diff:40-41); (e) glob tightened to `maintenance/gramps[0-9][0-9]` in ci.yml (patch.diff:14,17) and docker-build.yml (patch.diff:56). |
| C4 — C4 Verification (red→green) | FAIL | Gating gate failed: `./engine/scripts/ubuntu/run-verify.sh` → "error: .github/workflows/ci.yml: patch does not apply" (check-gates.json:33-39). red→green never executed against the verification base — same class of harness/path failure that sank iter‑1 (brief.md:59). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Sign-off gate (check-gates.json:42-48) and contested root-cause in iter‑1 (brief.md:58). My independent re-derivation supports adequacy: the `(None, *PTYPE)` sweep (patch.diff:172) makes `type_plugins(None)` recover ptype-unset records, so the union equals the old `__plugindata` master list AND a half-registered (`_ptype is None`) addon still surfaces → the iter‑1 silent-coverage-loss objection appears resolved. Human must clear the contested cause. |
| T1 — T1 Structure | N/A | Addon-layout rule (folder==id, target_version, fname, no `__init__.py`) targets *addons*; this patch adds only test modules (`tests/addon_paths.py`, `tests/test_addon_paths.py`) and workflow edits — no addon dir. The gate's "no .gpr.py" FAIL (check-gates.json:51-57) is a false positive for this change class. |
| T2 — T2 Shape | PASS | Both new files carry the GPL header and conform to doc 16 §Coding style — `addon_paths.py` (patch.diff:66-84) and `test_addon_paths.py` (patch.diff:202-220); gate confirms 2 files conform (check-gates.json:60-66). |
| T3 — T3 Runtime | NEEDS-HUMAN | 6.0 matrix green (check-gates.json:69-75); 6.1 matrix reports DELTA: 1 new failure `Sqlite...ExportSQLTestCase::test_export_sq` (check-gates.json:78-84). Patch touches no Sqlite/export code, and iter‑1 saw the same suite fail (8×, brief.md:61) — strongly suggests 6.1 baseline flakiness, not this patch. Human must confirm it reproduces without the patch before clearing. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle, so the commit/PR-wrapper rule has nothing to check (check-gates.json:87-93). |
| T5 — T5 Judgment | NEEDS-HUMAN | Ambiguous scope. `brief.md:5-6,36,50` flags the five nits as *independent* and *splittable*, the iter‑1 carry-forward explicitly says "Prefer splitting per logical change… at minimum, item (b)'s enumeration fix is its own change" (brief.md:58), and global discipline is one-logical-change-per-PR — yet this is a single combined diff covering all five. Human must decide split vs. bundle. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. Whether the resolved nits meet the brief's end goal (PR #820 CI green on the fork, success criterion brief.md:23-26) is a sign-off judgment, not derivable from artifacts. |

## §6 — Items the human must clear

1. **C2 (reproduction):** No red pre-fix evidence. (c)'s test validates the new
   helper, not the old substring bug; remaining items are behaviour-preserving.
   Confirm whether a genuine red→green (or a stated "no test because behaviour-
   preserving") is acceptable per item.
2. **C5 (contested root-cause):** Re-derivation finds item (b)'s `(None, *PTYPE)`
   sweep equivalent to the old `__plugindata` enumeration and no longer hiding the
   typeless-addon failure class — i.e. the iter‑1 rejection appears addressed.
   Human must ratify this causal claim.
3. **T3 (6.1 Sqlite delta):** `ExportSQLTestCase::test_export_sq` fails on the 6.1
   matrix but the patch touches no Sqlite code and the same failure preceded this
   patch in iter‑1. Confirm it is 6.1 baseline noise (reproduces without the patch),
   not a regression.
4. **T5 (scope):** Decide whether to split this combined diff into per-nit changes
   as the brief and iter‑1 carry-forward both recommend (item (b) at minimum).
5. **Validation (fitness-to-purpose):** Confirm the batch meets the brief's success
   criterion / end goal at sign-off.

## Blocking note

C4 is a **gating FAIL** ("patch does not apply" against the verification base) —
independent of every advisory item above, this batch cannot pass until the patch
applies cleanly on `origin/feature/ci-cd-pipeline-upstream` and red→green actually
runs. This is the same harness/base mismatch that sank iter‑1; rebase/rebuild on
the synced base and re-verify before sign-off.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C2 — C2 Reproduction (red pre-fix) — No repro gate configured (check-gates.json:15-21). (a)/(b)/(d)/(e) are behaviour-preserving/CI-observable — no failing test to reproduce. (c)'s new `test_addon_paths.py` exercises the *new* `is_in_addons_tree` helper, so it never ran red against the old `ADDONS_ROOT in pdata.fpath` code (patch.diff:247-285); red pre-fix state is unverifiable from artifacts.
- [ ] C5 — C5 Causal adequacy — Sign-off gate (check-gates.json:42-48) and contested root-cause in iter‑1 (brief.md:58). My independent re-derivation supports adequacy: the `(None, *PTYPE)` sweep (patch.diff:172) makes `type_plugins(None)` recover ptype-unset records, so the union equals the old `__plugindata` master list AND a half-registered (`_ptype is None`) addon still surfaces → the iter‑1 silent-coverage-loss objection appears resolved. Human must clear the contested cause.
- [ ] T3 — T3 Runtime — 6.0 matrix green (check-gates.json:69-75); 6.1 matrix reports DELTA: 1 new failure `Sqlite...ExportSQLTestCase::test_export_sq` (check-gates.json:78-84). Patch touches no Sqlite/export code, and iter‑1 saw the same suite fail (8×, brief.md:61) — strongly suggests 6.1 baseline flakiness, not this patch. Human must confirm it reproduces without the patch before clearing.
- [ ] T5 — T5 Judgment — Ambiguous scope. `brief.md:5-6,36,50` flags the five nits as *independent* and *splittable*, the iter‑1 carry-forward explicitly says "Prefer splitting per logical change… at minimum, item (b)'s enumeration fix is its own change" (brief.md:58), and global discipline is one-logical-change-per-PR — yet this is a single combined diff covering all five. Human must decide split vs. bundle.
- [ ] V — Validation — fitness-to-purpose — Always-human. Whether the resolved nits meet the brief's end goal (PR #820 CI green on the fork, success criterion brief.md:23-26) is a sign-off judgment, not derivable from artifacts.

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
- Iteration delta (if iterating): issue_820-review-nits: C4 was a gating FAIL ("patch does not apply" against the verification base) — root cause was the brief missing the branch/base information, so the patch was verified against the wrong base. The brief has now been updated with the correct branch target. Rebuild on the synced base so the patch applies and red→green actually runs; then re-verify the §6 items (C2 repro, C5 causal, T3 6.1 noise, T5 scope). Also honor the standing carry-forward on T5 scope: split the combined diff per logical change (item (b)'s enumeration fix is its own change at minimum), per the brief and iter-1 carry-forward.
- By / date: Eduard Ralph / 2026-06-19

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
