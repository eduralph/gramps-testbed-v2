# Result — issue 7344 / addon-setup-locale-path-dead-slice

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: Reported (2013, addons for Gramps 4.0.x): addon translation `.mo` files landed at
- Success criterion: building/compiling an addon that has a `pt_BR` (or other >2-char)
- Repo + branch target: gramps-project/addons-source @ maintenance/gramps60
- Scope (one logical fix) / out of scope: the dead fixed-width locale-slice in the addons build/`languages` step (and

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: POSSIBLY-FIXED → verify first
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: unverifiable — patch ships no addon test (test_*.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 – N/A: no checkable .py path in patch.diff
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: DeepConnectionsGramplet.tests.test_deep_connections_paths.
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# check-review.md — Issue 7344 / addon-setup-locale-path-dead-slice (Iteration 2)

> Reviewer: Claude (advisory, artifact-only). `$PDCA_TARGET` is **unset**;
> all path:line citations are grounded on `patch.diff` alone.  
> A workspace checkout at `/home/eddie/workspace/addons-source/` was read
> **advisory-only** to confirm line numbers and context — it is not used as a
> grounding source and no verdicts depend solely on it.

---

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 Spec | PASS | Brief is unambiguous: remove the dead `length`/`locale` slice from both `make.py` and `setup.py`; confirm `rsplit`-based derivation is correct for >2-char locales. Success criterion and scope are explicit. |
| C2 Reproduction (red pre-fix) | PASS | `patch.diff` shows the dead lines present in both files pre-fix (`make.py` hunk -161+2, `setup.py` hunk -783+2); advisory workspace confirms at make.py:164-165 and setup.py:786-787. The defect (dead overwritten slice) is structurally self-evident from the context lines alone. |
| C3 Change | PASS | Patch deletes exactly the two dead-assignment lines from each file and nothing else; iteration 1's rejection cause (make.py omitted) is addressed; no new code, no functional change to surviving logic (`rsplit`+`locale[:-9]` path untouched). patch.diff:1-13 (make.py), 14-26 (setup.py). |
| C4 Verification (red→green) | N/A | Brief pre-declared `PDCA-UNVERIFIABLE`; gate confirms `"result": "unverifiable"`; no test seam exists for build-tooling locale enumeration. C4 red→green cannot run; manual build repro required (see V row). |
| C5 Causal adequacy | PASS | Fix is a pure deletion of dead assignments that were already overwritten; no capability probe, `hasattr`, `try/except` import guard, or any new guard added. C5 smell-test does not trigger. Causal chain: dead code removed → dead code no longer present. No symptom-vs-root-cause ambiguity. |
| T1 Structure | N/A | No addon layout paths in patch.diff (change is build-tooling only); gate confirms N/A for §Structure addon-layout check. |
| T2 Shape | PASS | Patch removes lines only; no new files, no GPL-header obligation, no `print()` added. Gate reports N/A for automated T2 check; manual inspection of diff confirms no shape violations. |
| T3 Runtime | NEEDS-HUMAN | **Decide whether the 2 new T3 failures are pre-existing baseline drift or patch-caused — the decision matters because a causal link would indicate an unexpected side-effect of a dead-code removal.** Gate reports 1 new failure in each matrix: `DeepConnectionsGramplet.tests.test_deep_connections_paths` (gramps60) and `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` (gramps61). Neither addon touches `make.py`/`setup.py` locale enumeration; patch only removes dead variable assignments that were already overwritten; a causal link is implausible but must be confirmed. Iteration 1 had 4 different new failures (LifeLineChartView, PDFForms, …), suggesting rolling baseline drift rather than patch causation, but that inference is NEEDS-HUMAN to confirm. Both T3 rows are `"gating": false`. |
| T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in bundle; gate confirms N/A. |
| T5 Judgment | PASS | Iteration 1 deficiency (make.py omitted) is resolved; fix is minimal and correctly scoped to both build tools. Prior-art check (brief §prior-art) found no conflicting open/closed PR removing the dead slice. Weblate bypass question (brief §iteration 1) is noted but does not affect correctness of the removal. No scope creep observed. |
| Validation — fitness-to-purpose | NEEDS-HUMAN | **Confirm via manual build that a `pt_BR-local.po` (or other >2-char locale) produces `<Addon>/locale/pt_BR/LC_MESSAGES/addon.mo` with the patched make.py — this is the only available verification given C4-UNVERIFIABLE.** Also: confirm whether the Weblate path used for gramps60+ bypasses `get_all_languages()` entirely (noted in iteration 1 carry-forward); if so, the impact of this removal on active builds should be explicitly bounded. |

---

## Supporting notes

### C5 smell-test (capability-probe guard scan)
Scanned `patch.diff` in full: no `hasattr`, no `try: import`, no feature-probe,
no `if sys.version`, no fallback guard of any kind. The fix is deletion-only.
Smell-test: **no trigger**.

### T3 new failures — causation assessment
The removed code (`length = len(po)` / `locale = po[length-11:length-9]`) is a
dead assignment immediately overwritten by the `rsplit` on the next line. It has
no effect on the runtime behaviour of `DeepConnectionsGramplet` or `Sqlite`
tests, which exercise completely separate addon logic. The failure set also
differs from iteration 1's 4 failures (LifeLineChartView, PDFForms, …), which
is consistent with rolling test-suite drift rather than a fixed patch-caused
regression. Human confirmation is still required because the baseline diffing is
done by the engine, not re-run independently here.

### Prior-art / fork-discipline
Brief records a triage prior-art check by path (`setup.py` on
`upstream/maintenance/gramps60`): no open or closed PR removing the dead slice
was found. The rsplit-based derivation that supersedes the buggy slice is already
upstream (brief:42). This removal is additive-clean relative to upstream.
Cross-version correctness (fork-discipline §3): the change applies only to
dead code that is structurally identical on the target branch; no semantic
risk from version skew.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] T3 Runtime — **Decide whether the 2 new T3 failures are pre-existing baseline drift or patch-caused — the decision matters because a causal link would indicate an unexpected side-effect of a dead-code removal.** Gate reports 1 new failure in each matrix: `DeepConnectionsGramplet.tests.test_deep_connections_paths` (gramps60) and `Sqlite.tests.test_sqlite.ExportSQLTestCase::test_export_sq` (gramps61). Neither addon touches `make.py`/`setup.py` locale enumeration; patch only removes dead variable assignments that were already overwritten; a causal link is implausible but must be confirmed. Iteration 1 had 4 different new failures (LifeLineChartView, PDFForms, …), suggesting rolling baseline drift rather than patch causation, but that inference is NEEDS-HUMAN to confirm. Both T3 rows are `"gating": false`.
- [x] Validation — fitness-to-purpose — **Confirm via manual build that a `pt_BR-local.po` (or other >2-char locale) produces `<Addon>/locale/pt_BR/LC_MESSAGES/addon.mo` with the patched make.py — this is the only available verification given C4-UNVERIFIABLE.** Also: confirm whether the Weblate path used for gramps60+ bypasses `get_all_languages()` entirely (noted in iteration 1 carry-forward); if so, the impact of this removal on active builds should be explicitly bounded.
- [x] C4 fix verified: test red pre-fix, green post-fix unverifiable — patch ships no addon test (test_*.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-06-27

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
