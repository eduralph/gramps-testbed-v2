# Result — issue 9267 / name-format-change-rebuilds-sort

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: Changing the Display Name format in Preferences refreshes what each row
- Success criterion: After changing the Display Name format in Edit→Preferences→
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the missing sort-order rebuild when the active display-name format changes

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): unverifiable — the interface repro was SKIPPED (or ran no test) on the UNPATCHED tree — the env could not exercise the bug (e.g. a miss
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 3 file(s) conform to doc 16 §Coding style (4 advisory)
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: runner exited 1 producing NO JUnit XML — a pre-test crash (install / GI bootstrap / test col
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review

Grounding note: `$PDCA_TARGET=/home/eddie/workspace/gramps` is readable, and `git apply --check patch.diff` succeeds there. The target checkout is pre-patch, so existing-behavior citations are grounded on `$PDCA_TARGET`, while added/changed-code citations are grounded on `patch.diff`. `build-notes.md` was not used.

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | The brief states the defect, success criterion, invariant, and scope for People flat list re-sort after a display-name format change (`brief.md:9`, `brief.md:13`, `brief.md:16`, `brief.md:25`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | The repro describes stale row order until DB reopen, and the red-without-fix verification gate passed (`brief.md:29`, `brief.md:30`, `check-gates.json:33`, `check-gates.json:37`). |
| C3 — C3 Change | PASS | The patch invalidates sort before rebuilding on format changes and makes flat rebuilds recompute cached sort keys in both search and filter paths (`patch.diff:288`, `patch.diff:298`, `patch.diff:45`, `patch.diff:65`, `patch.diff:76`). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | Core red→green verification passed, but the GUI AT-SPI repro was skipped/unverifiable; DECISION OWED: decide whether model-level red→green evidence is sufficient for this GUI-surface bug (`check-gates.json:33`, `check-gates.json:37`, `check-gates.json:41`, `check-gates.json:46`). |
| C5 — C5 Causal adequacy | PASS | The causal chain matches the patch: preferences emit `nameformat-changed`, the existing person-view callback only rebuilt, `ListView` reused model data, and flat rebuilds reused `full_srtkey_hndl_map()` unless empty (`gramps/gui/configure.py:1491`, `gramps/plugins/lib/libpersonview.py:181`, `gramps/gui/views/listview.py:361`, `gramps/gui/views/treemodels/flatbasemodel.py:589`). |
| T1 — T1 Structure | N/A | This is a core-only patch, not an addon-layout change, so addon structure rules do not apply (`patch.diff:1`, `patch.diff:273`, `check-gates.json:60`). |
| T2 — T2 Shape | PASS | The new core test carries the project GPL header and is registered in `po/POTFILES.skip`; shape and potfiles gates passed (`patch.diff:93`, `patch.diff:313`, `check-gates.json:69`, `check-gates.json:78`). |
| T3 — T3 Runtime | NEEDS-HUMAN | The unit runtime baseline crashed before producing JUnit while the GUI smoke passed; DECISION OWED: decide whether to accept this non-gating infrastructure gap or require a clean rerun (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`). |
| T4 — T4 Contribution | N/A | No commit message or PR description is present in the artifact bundle, so contribution-wrapper review is not applicable (`check-gates.json:105`, `check-gates.json:109`). |
| T5 — T5 Judgment | NEEDS-HUMAN | The patch also invalidates sort on `placeformat-changed`, while the brief centers name-format sorting and excludes other-column sorting; DECISION OWED: decide whether this scope expansion is acceptable (`brief.md:13`, `brief.md:25`, `brief.md:27`, `patch.diff:281`). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Fitness-to-purpose is user-visible People flat behavior, and the GUI repro was not exercised; DECISION OWED: manually/owner-confirm that changing Display Name format re-sorts the live People flat list without reopening (`brief.md:13`, `brief.md:29`, `check-gates.json:41`). |

## §6 Human Clearances

1. C4 — Verification sufficiency: core red→green evidence exists, but the GUI AT-SPI repro was skipped. Human must decide whether the model-level regression test adequately covers the GUI callback path, or whether sign-off requires a successful GUI repro.
2. T3 — Runtime evidence: the unit baseline failed before JUnit output, while GUI smoke passed. Human must decide whether this is acceptable non-gating infrastructure noise or whether a clean unit-suite rerun is required.
3. T5 — Scope judgment: the implementation handles `placeformat-changed` as well as `nameformat-changed`. Human must decide whether that small expansion is acceptable despite the brief’s name-format focus and out-of-scope note for other-column sorting.
4. V — Fitness-to-purpose: the actual product criterion is live People flat list re-sort after changing Display Name format. Human must confirm the UI behavior because the automated GUI repro did not run to red/green completion.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C4 — C4 Verification (red→green) — Core red→green verification passed, but the GUI AT-SPI repro was skipped/unverifiable; DECISION OWED: decide whether model-level red→green evidence is sufficient for this GUI-surface bug (`check-gates.json:33`, `check-gates.json:37`, `check-gates.json:41`, `check-gates.json:46`).
- [x] T3 — T3 Runtime — The unit runtime baseline crashed before producing JUnit while the GUI smoke passed; DECISION OWED: decide whether to accept this non-gating infrastructure gap or require a clean rerun (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`).
- [x] T5 — T5 Judgment — The patch also invalidates sort on `placeformat-changed`, while the brief centers name-format sorting and excludes other-column sorting; DECISION OWED: decide whether this scope expansion is acceptable (`brief.md:13`, `brief.md:25`, `brief.md:27`, `patch.diff:281`).
- [x] V — Validation — fitness-to-purpose — Fitness-to-purpose is user-visible People flat behavior, and the GUI repro was not exercised; DECISION OWED: manually/owner-confirm that changing Display Name format re-sorts the live People flat list without reopening (`brief.md:13`, `brief.md:29`, `check-gates.json:41`).
- [x] C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) unverifiable — the interface repro was SKIPPED (or ran no test) on the UNPATCHED tree — the env could not exercise the bug (e.g. a miss

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
- By / date: Eduard Ralph / 2026-06-28

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
