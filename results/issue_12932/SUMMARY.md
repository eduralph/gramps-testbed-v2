# Result — issue 12932 / verify-fanchart2way-startup-crash-fixed

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: Reported startup crash: with "remember last view displayed" enabled, last
- Success criterion: On `maintenance/gramps61`, the 12932 repro no longer raises — the
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: verify (do not re-implement) that the already-merged fan-chart startup-crash

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: POSSIBLY-FIXED → verify first
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: fail — run-verify.sh: no patch.diff in /home/eddie/workspace/gramps-testbed-v2/results/issue_12932
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): fail — run-verify-interface.sh: no patch.diff in /home/eddie/workspace/gramps-testbed-v2/results/issue_12932
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 – N/A: no checkable .py path in patch.diff
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2-potfiles – N/A: no patch.diff
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review

Target caveat: `$PDCA_TARGET` is readable, but it is checked out on `fix/bug-8850-gedcom-import-cal-date-case-sensitive`, not the requested `maintenance/gramps61`; the fan-chart fix commit is present in that target, so source citations below are grounded there. `patch.diff` is absent from this review directory; for this verify-only brief that is not by itself a C4 patch-defect blocker.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines a concrete startup crash, target branch, success criterion, scope, repro, and expected citations for a verify-only close (`brief.md:8`, `brief.md:13`, `brief.md:22`, `brief.md:25`, `brief.md:29`, `brief.md:36`). |
| C2 — C2 Reproduction (red pre-fix) | N/A | This is explicitly a verification of an already-fixed upstream defect with no production patch expected, so a fresh pre-fix red run is outside this bundle's scope (`brief.md:13`, `brief.md:15`, `brief.md:25`). |
| C3 — C3 Change | N/A | No production patch is expected for the confirmed-fixed disposition, and the review directory contains no `patch.diff`; the gate failure records absence of `patch.diff`, not a faulty code change (`brief.md:15`, `brief.md:16`, `check-gates.json:37`). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | DECISION OWED: decide whether source/regression evidence is sufficient for tracker closure, or require the requested green AT-SPI/manual startup sign-off, because the specific GUI repro artifact is absent and the gate only failed on missing `patch.diff` (`brief.md:32`, `brief.md:34`, `check-gates.json:37`, `check-gates.json:46`). |
| C5 — C5 Causal adequacy | PASS | The crash path appends to `userdata` for time-period gradients, while the 2-way startup short-circuit now leaves each ascendance slot with its own list before `prepare_background_box` iterates it (`gramps/gui/widgets/fanchart.py:340`, `gramps/gui/widgets/fanchart.py:352`, `gramps/gui/widgets/fanchart2way.py:137`, `gramps/gui/widgets/fanchart2way.py:141`, `gramps/gui/widgets/fanchart2way.py:227`, `gramps/gui/widgets/fanchart2way.py:232`, `gramps/gui/widgets/fanchart2way.py:247`, `gramps/gui/widgets/fanchart2way.py:249`, `gramps/gui/widgets/fanchart2way.py:393`, `gramps/gui/widgets/fanchart2way.py:395`). |
| T1 — T1 Structure | N/A | Addon layout rules do not apply to this core verify-only bundle with no new or removed files (`brief.md:23`, `brief.md:40`, `check-gates.json:60`, `check-gates.json:65`). |
| T2 — T2 Shape | N/A | There is no patch and no checkable touched Python path in the submitted artifacts, so code-shape/POTFILES checks are not applicable (`check-gates.json:69`, `check-gates.json:83`). |
| T3 — T3 Runtime | PASS | The available runtime gates passed: unit baseline matched known reds and GUI interface smoke was green, with recorded target drift caveats (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`). |
| T4 — T4 Contribution | N/A | No commit message or PR wrapper is present or expected in this no-patch verification artifact set (`brief.md:16`, `brief.md:17`, `check-gates.json:105`, `check-gates.json:110`). |
| T5 — T5 Judgment | PASS | The artifact shape stays within the stated verify-only scope and avoids the out-of-scope fanchart reimplementation/name-format/preference machinery (`brief.md:25`, `brief.md:28`, `brief.md:40`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: a human must decide whether this evidence is fit to resolve Mantis 12932, especially because the requested 2-way time-period startup verification is not captured as a green artifact here (`brief.md:13`, `brief.md:17`, `brief.md:32`, `brief.md:35`, `brief.md:47`). |

## §6 Human Decisions Owed

1. C4 — Verification: decide whether the current source invariant plus existing regression coverage are enough, or require a recorded green run/manual sign-off of `engine/interface/test_bug_12932_fanchart2way-startup.py` for the 2-way time-period-gradient startup scenario. This matters because the automated C4 failure is only "no patch.diff", which is expected for a verify-only close, but it does not prove the issue-specific startup path was exercised.
2. V — Fitness-to-purpose: decide whether this bundle can move issue 12932 to resolved. The impact is tracker correctness: accepting closes a possibly-fixed report based on source-level causal coverage; rejecting requires an explicit GUI/startup verification artifact before closure.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C4 — C4 Verification (red→green) — DECISION OWED: decide whether source/regression evidence is sufficient for tracker closure, or require the requested green AT-SPI/manual startup sign-off, because the specific GUI repro artifact is absent and the gate only failed on missing `patch.diff` (`brief.md:32`, `brief.md:34`, `check-gates.json:37`, `check-gates.json:46`).
- [x] V — Validation — fitness-to-purpose — DECISION OWED: a human must decide whether this evidence is fit to resolve Mantis 12932, especially because the requested 2-way time-period startup verification is not captured as a green artifact here (`brief.md:13`, `brief.md:17`, `brief.md:32`, `brief.md:35`, `brief.md:47`).

## 7. Proven / not proven
- Proven by which oracle: gates overall = fail (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: discontinued
- Iteration delta (if iterating): Re-dispositioned from merged-wider (signed off 2026-06-28) to discontinued per maintainer decision, 2026-07-01.
- By / date: Eduard Ralph / 2026-07-01

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
