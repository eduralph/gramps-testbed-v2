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
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): pass — T3-baseline [green]: green (no failures) | ⚠ baseline tree drift: recorded detached@6235c3ba3a, tested detached@32aa2962
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: 4 new failure(s) not in baseline: LifeLineChartView.collection::import_or_collection, PDFFor
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# check-review.md — issue 7344 / addon-setup-locale-path-dead-slice

**Reviewer:** Check (advisory, decorrelated)  
**Grounding:** `PDCA_TARGET` unset → all path:line citations ground on `patch.diff` and `brief.md` alone.  
**C4 note:** Brief pre-declared `PDCA-UNVERIFIABLE` (build/packaging tooling; no test seam practical); gates confirm `result: "unverifiable"`. This is an expected disposition, **not** a patch defect.

---

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 Spec | PASS | Brief names defect precisely (dead fixed-width slice in `languages()` step), gives a falsifiable success criterion (dead slice removed; rsplit path survives; pt_BR .mo lands at correct path), and bounds scope tightly — brief.md:7–19, 26 |
| C2 Reproduction (red pre-fix) | PASS | Pre-fix state confirmed by presence of removed lines in patch.diff:9–10 (`length = len(po)` / `locale = po[length-11:length-9]`); brief.md:32–33 describes the static repro — no runtime test needed as this is dead-code confirmed by inspection, not a runtime failure |
| C3 Change | PASS | Patch is a pure 2-line deletion (patch.diff:9–10), scoped to exactly the dead assignments the brief identifies; no other lines added or modified; `locale` and `length` are local to the loop body and both are dead before the rsplit line (patch.diff:11) |
| C4 Verification (red→green) | NEEDS-HUMAN | Decide whether the manual build repro (exercise with a `pt_BR-local.po` file; confirm `<Addon>/locale/pt_BR/LC_MESSAGES/addon.mo` is produced) has been performed and its output recorded — static read confirms rsplit (patch.diff:11–12) is the live path and is unaffected, but runtime path output requires human confirmation; brief pre-declared PDCA-UNVERIFIABLE |
| C5 Causal adequacy | PASS | Patch only **removes** lines — the C5 guard smell-test (capability probe / try-it-and-fall-back added inside code meant to run with that capability present) does not fire on a pure deletion; the deleted slice was the original causal agent of the >2-char locale defect, and its removal cannot regress the superseding rsplit derivation |
| T1 Structure | N/A | No addon directory created or modified; T1 (folder==id, target_version, fname, no `__init__.py`) is addon-layout-only; change is to build tooling — check-gates.json T1 row confirms N/A |
| T2 Shape | PASS | Patch is a deletion-only diff — no GPL-header lines removed, no `print()` calls added; gate's stated reason ("no checkable .py path") is technically wrong (setup.py is a .py file) but the T2 violations it guards against cannot be introduced by a lines-only removal |
| T3 Runtime | NEEDS-HUMAN | Decide whether the 4 new gramps61×6.1 failures (`LifeLineChartView.collection::import_or_collection`, `PDFFor…`) are pre-existing environmental failures unrelated to this patch, or are genuinely caused by it — a 2-line dead-code deletion in `languages()` has no plausible causal path to addon-level collection/import failures, but the determination must be human-confirmed before gramps61 merge; gramps60×6.0 baseline is green (check-gates.json T3 rows) |
| T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in bundle; T4 commit/PR format check inapplicable at this stage — check-gates.json T4 row confirms N/A |
| T5 Judgment | PASS | Change is the minimal safe action for a verified dead-code situation: 2 lines deleted, no behavior altered, no guard introduced, scope matches brief exactly; only open concern is the T3 gramps61 failures flagged above — their pre-existing nature is strongly suggested but not mechanically settled |
| Validation — fitness-to-purpose | NEEDS-HUMAN | Confirm that (a) removing the dead slice closes Mantis 7344 to the reporter's satisfaction, (b) no build script or downstream caller outside `setup.py` depends on the removed `length` or pre-rsplit `locale` assignments, and (c) the manual pt_BR build repro has been recorded in build-notes as the brief requires |

---

## §6 Human-clearance checklist

- [ ] **C4 manual build repro** — Run `setup.py` against an addon with `pt_BR-local.po`; confirm `<Addon>/locale/pt_BR/LC_MESSAGES/addon.mo` is produced; record output in build-notes (brief.md:34–36)
- [ ] **T3 gramps61 failures** — Determine whether the 4 new failures (`LifeLineChartView`, `PDFFor…`) are pre-existing / environmental; if caused by this patch, block merge on gramps61; if not, document and proceed
- [ ] **Validation** — Confirm Mantis 7344 satisfaction; verify no external caller depends on the removed `length`/`locale` assignments; confirm manual repro is in build-notes

---

## Reviewer notes

**C5 smell-test result:** No capability probe or runtime guard was added — the patch is a pure deletion. Smell-test does not fire.

**T2 gate accuracy:** The gate reported "N/A: no checkable .py path in patch.diff" but `setup.py` is a Python file. The gate's detection logic appears to have missed it (possibly filtering on path patterns). This does not change the T2 verdict since no T2 violations can be introduced by removing lines, but the gate logic should be noted for future cycles.

**T3 gramps61 causation:** The failed tests (`LifeLineChartView.collection::import_or_collection`, `PDFFor…`) are addon-level collection/import tests. The patch touches only the `languages()` function that collects locale codes for translation discovery. There is no plausible mechanism by which removing `length = len(po)` and the dead `locale = po[length-11:length-9]` assignment causes those addon tests to fail. The failures are almost certainly pre-existing, but this must be confirmed rather than assumed.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C4 Verification (red→green) — Decide whether the manual build repro (exercise with a `pt_BR-local.po` file; confirm `<Addon>/locale/pt_BR/LC_MESSAGES/addon.mo` is produced) has been performed and its output recorded — static read confirms rsplit (patch.diff:11–12) is the live path and is unaffected, but runtime path output requires human confirmation; brief pre-declared PDCA-UNVERIFIABLE
- [x] T3 Runtime — Decide whether the 4 new gramps61×6.1 failures (`LifeLineChartView.collection::import_or_collection`, `PDFFor…`) are pre-existing environmental failures unrelated to this patch, or are genuinely caused by it — a 2-line dead-code deletion in `languages()` has no plausible causal path to addon-level collection/import failures, but the determination must be human-confirmed before gramps61 merge; gramps60×6.0 baseline is green (check-gates.json T3 rows)
- [ ] Validation — fitness-to-purpose — Confirm that (a) removing the dead slice closes Mantis 7344 to the reporter's satisfaction, (b) no build script or downstream caller outside `setup.py` depends on the removed `length` or pre-rsplit `locale` assignments, and (c) the manual pt_BR build repro has been recorded in build-notes as the brief requires
- [ ] C4 fix verified: test red pre-fix, green post-fix unverifiable — patch ships no addon test (test_*.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: iterated-to-Do
- Iteration delta (if iterating): setup.py has been superseded by make.py as the primary addon build tool (README documents all commands via `python3 make.py gramps60 ...`). make.py has the identical dead-slice bug at line 165 (`locale = po[length - 11 : length - 9]`, immediately overwritten by `po.rsplit(os.sep, 1)`). The patch fixes the legacy file and leaves the active one broken. Redirect the 2-line deletion to make.py (and optionally also setup.py for completeness). Note in build-notes whether the Weblate path (active for gramps60+) bypasses this code entirely.
- By / date: Eduard Ralph / 2026-06-27

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
