# Result — issue 11166 / latexdoc-pict-width-float-typeerror

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: Generating LaTeX output from a report that places an image inside a table —
- Success criterion: A report containing a picture cell emits its LaTeX picture-size
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the picture-width emission in `gramps/plugins/docgen/latexdoc.py`.

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 2 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review — issue 11166 / latexdoc-pict-width-float-typeerror

**Reviewer role:** Check (advisory, decorrelated from builder)
**Artifacts read:** `brief.md`, `check-gates.json`, `patch.diff`
**Artifact withheld:** `build-notes.md` (by design)
**Target source:** `$PDCA_TARGET` unset — all path:line citations are grounded on `patch.diff` alone; claims from `brief.md` are accepted as authoritative spec only
**Date reviewed:** 2026-06-21

---

## §1 — Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | `brief.md` names defect (TypeError at `calc_latex_widths` join), exact crash site (`latexdoc.py:849`), invariant ("every width emission stringifies"), out-of-scope exclusions (multicolumn crash `ed8eaa2782`, `repack_row` IndexError), and a measurable success criterion (no TypeError on `end_table`) |
| C2 — C2 Reproduction (red pre-fix) | PASS | `check-gates.json` C4-verify reports `red-without-fix=PASS`; the test's `assertIsInstance(doc.pict_width, float)` + bare `end_table()` call structurally reproduce the pre-fix crash path, confirming the red run was driven by the actual defect |
| C3 — C3 Change | PASS | `patch.diff:9-10` — one production line changed: `self.pict_width` → `repr(self.pict_width)` inside `calc_latex_widths`'s `"".join(...)`, consistent with the sibling sites asserted by `brief.md`; no unrelated production lines touched |
| C4 — C4 Verification (red→green) | PASS | `check-gates.json` gating element: `C4-verify green-with-fix=PASS / red-without-fix=PASS` |
| C5 — C5 Causal adequacy | PASS | Root cause is direct: `"".join()` requires all items to be `str`; `self.pict_width` (a `float`) at `patch.diff:9` violates that contract; `repr()` produces the string form; two-sentence chain is complete and needs no further decomposition |
| T1 — T1 Structure | N/A | Core-only change; §Structure (folder==id, target_version, fname, no `__init__.py`) is addon-only; confirmed by `check-gates.json` T1 `path_line`: "N/A: no addons-source path in patch.diff" |
| T2 — T2 Shape | PASS | `check-gates.json` T2 shape: 2 files conform to §Coding style; T2-potfiles (gating=true): PASS — patch modifies two existing `.py` files, adds no new ones, removes none |
| T3 — T3 Runtime | PASS | `check-gates.json` T3-unit: baseline held (7 known reds); drift note "recorded detached@674e3b" is a tree-state annotation, not a new failure |
| T4 — T4 Contribution | N/A | `check-gates.json` T4 `path_line`: "N/A: no commit-msg.txt or pr-description.md in the bundle"; contribution wrapper not yet staged |
| T5 — T5 Judgment | NEEDS-HUMAN | (see §4 and §6-T5) Cannot confirm from `patch.diff` alone that the two sibling sites (`latexdoc.py:804` `repack_row`, `latexdoc.py:1235` cell emit) already use `repr(self.pict_width)` — the brief asserts this, but the invariant "every width emission stringifies" requires all three sites to be verified on the target source |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | User-visible correctness (Complete Individual Report with "Add Pictures", LaTeX output, "Garner von Zielinski" in `example.gramps`) requires human end-to-end run on `maintenance/gramps61` with the fix applied |

---

## §2 — Element notes

### C1 — Spec
Well-formed. The brief names the exact crash site (`latexdoc.py:849`, inside `"".join((...))` at `:846-852`), the invariant to restore, which two sibling sites already comply, and explicit out-of-scope exclusions. The success criterion is testable and matches C4's gate. No ambiguity.

### C2 — Reproduction
No standalone C2 gate was configured (`check-gates.json` result: `"none"`, `oracle: "(no gate configured)"`). Reproduction is evidenced instead by the C4 red run. The test's precondition assertions (`cell.content.startswith("\\grmkpicture")` at `patch.diff:117`, `assertIsInstance(doc.pict_width, float)` at `patch.diff:118`) confirm the test reached the actual crash site before the fix. Adequate.

### C3 — Change
Minimal. The production change is one token: `self.pict_width` → `repr(self.pict_width)` at `patch.diff:10`. The test addition is new class `LaTeXPictureInTableTest` in `latexdoc_test.py` (`patch.diff:56-126`). Nothing else is modified. The out-of-scope sites (`repack_row`, multicolumn code) are untouched.

### C4 — Verification
Gating element. Both directions confirmed by the engine. Test drives the real `LaTeXDoc` (imported at `patch.diff:43`), builds a real table via the doc API, and calls `end_table()` — not a hand-rolled emit copy. Satisfies the brief's "MUST exercise the real LaTeXDoc" constraint.

### C5 — Causal adequacy
The `"".join(seq)` call requires every item in `seq` to be `str`. `self.pict_width` is a float (set numerically, defaulting to `0`). The fix applies `repr()`, which for a float or int always returns a non-empty string. The fix is a type-serialization correction, not a guard; it is causally sufficient for the reported crash and consistent with the sibling sites as described in the brief.

### T1 — N/A
No addon paths in diff; gate correctly classified this as inapplicable.

### T2 — Shape / Potfiles
Both files modified by the patch carry GPL headers (visible in `patch.diff:18-22`). No `print()` calls introduced. No new `.py` files added. Potfiles gate (gating=true) passed.

### T3 — Runtime
Baseline held at 7 known failing tests. The tree-drift annotation ("recorded detached@674e3b") indicates the baseline was recorded against a detached-HEAD state; this is a process note, not a new regression.

### T4 — N/A
No commit message or PR description artifact present. Human submits these separately.

### T5 — Judgment (NEEDS-HUMAN)
The fix is minimal, targeted, and internally consistent with the brief's diagnosis. One concern cannot be closed from `patch.diff` alone:

**T5-a (completeness):** The brief's SELF-TEST states the invariant is "every width emission stringifies" across three sibling sites. The patch fixes only the one site in `calc_latex_widths`. The brief asserts the other two sites (`repack_row` at `:804`, cell emit at `:1235`) already use `repr()`. This must be confirmed on the target source before the invariant can be declared fully restored.

Minor observation not escalated: `_make_doc` in the test constructs `PaperSize("Letter", 27.94, 21.59)` with dimensions that appear transposed for portrait orientation (Letter portrait is 21.59 cm × 27.94 cm). This does not affect the TypeError test and C4 confirms it does not cause a test failure, so it is noted but not a blocker.

### V — Validation (NEEDS-HUMAN)
The test verifies the crash is eliminated. Whether the emitted LaTeX `\setlength{\grpictsize}{<float_repr>\grbaseindent}` is semantically correct LaTeX and produces a well-formed output file requires a human to run the complete report flow.

---

## §3 — Scope boundary check

The brief excludes two items from scope:
1. The "two-or-more multicolumns" crash (`ed8eaa2782`) — `patch.diff` contains no changes to multicolumn-related code. ✓
2. The `IndexError` in `repack_row` — `patch.diff` does not touch `repack_row`. ✓

No scope creep detected.

---

## §4 — Remaining risk register

| # | Risk | Severity | Closed by |
|---|------|----------|-----------|
| R1 | Sibling sites at `:804` and `:1235` may not both use `repr()` — if either is missing it, the invariant is not fully restored | Medium | T5-a human check (§6) |
| R2 | `repr()` of an int zero (`0`) yields `'0'`, not `'0.0'` — if the LaTeX macro `\grpictsize` requires a float literal the default `pict_width=0` (int) path may differ from the float path | Low | Confirmed acceptable if sibling sites use identical repr() call and existing tests pass that path |
| R3 | End-to-end LaTeX output quality with `repr(float)` as the size argument | Low | V human check (§6) |

---

## §5 — Overall assessment

**CONDITIONAL PASS — awaiting §6 human clearance.**

The production fix is a one-line, causally sound, minimal change. The test covers the defect mechanically and exercises the real API. All automated gates passed. Two human items must be cleared before this can be marked fully done.

---

## §6 — NEEDS-HUMAN clearance items

These items block final sign-off. Each must be cleared by a human with access to the target source on `maintenance/gramps61`.

### §6-T5 — Verify completeness of the "every width emission stringifies" invariant

**Action:** On `maintenance/gramps61`, open `gramps/plugins/docgen/latexdoc.py` and confirm:
- `latexdoc.py:804` (inside `repack_row`) already uses `repr(self.pict_width)`, not the bare `self.pict_width`
- `latexdoc.py:1235` (the cell emit site) already uses `repr(self.pict_width)`, not the bare `self.pict_width`

If either site is missing `repr()`, the patch is incomplete and an additional change is required at that site.

**Clears:** T5 → PASS

### §6-V — End-to-end manual validation

**Action:** On `maintenance/gramps61` with the patch applied, run the Complete Individual Report with "Add Pictures" enabled, LaTeX output format, on the "Garner von Zielinski" subject in `example.gramps`. Confirm:
1. No `TypeError` is raised.
2. The generated `.tex` file contains a well-formed `\setlength{\grpictsize}{...}` command with a numeric string (not an empty token or Python-repr artefact).
3. The document compiles to PDF without LaTeX errors related to the picture size.

**Clears:** V → PASS

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] T5 — T5 Judgment — (see §4 and §6-T5) Cannot confirm from `patch.diff` alone that the two sibling sites (`latexdoc.py:804` `repack_row`, `latexdoc.py:1235` cell emit) already use `repr(self.pict_width)` — the brief asserts this, but the invariant "every width emission stringifies" requires all three sites to be verified on the target source
- [x] V — Validation — fitness-to-purpose — User-visible correctness (Complete Individual Report with "Add Pictures", LaTeX output, "Garner von Zielinski" in `example.gramps`) requires human end-to-end run on `maintenance/gramps61` with the fix applied

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
- By / date: Eduard Ralph / 2026-06-21

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
