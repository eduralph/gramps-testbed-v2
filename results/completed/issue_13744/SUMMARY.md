# Result — issue 13744 / empty-date-serialization-roundtrip

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: An empty/unset date entered in Gramps 6.0.x is serialized to Gramps XML as `<datestr val=""/>`, a form the **Verify the data** tool rejects on re-open (reports `Invalid death date`). Pre-6.0.0 omitted the `<datestr>` element entirely for an empty date, and that form validated cleanly ("no death date" → no complaint). So empty dates no longer round-trip through export → re-import / validate. (Mantis 13744; reporter's `simpson.gramps`, note 1.)
- Success criterion: An event whose date is **empty**, exported to Gramps XML and re-imported (and run through Tools → Utility → **Verify the data** with defaults), is treated as having **no date** — it does **not** raise `Invalid death date` / `Invalid date` — matching pre-6.0.0 behaviour. Equivalently: serialize → deserialize → serialize of an empty Date is stable and yields an empty Date.
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61 (core; forward-merged to master per INTEGRATION §2).
- Scope (one logical fix) / out of scope: the serialized form of an **empty** date does not round-trip to an empty date (and the Verify-data check then flags it) — make an empty date export/import/validate as "no date", matching pre-6.0.0. / **out of scope:** non-empty or partial (year-only, span, range) date format changes; the Verify tool's other heuristics; archaeology of which 6.0 commit first emitted the empty `<datestr>` beyond identifying the serialized-form change responsible.

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
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — issue 13744 / empty-date-serialization-roundtrip

> Advisory, artifact-only, decorrelated from the builder. Inputs available:
> `patch.diff`, `brief.md`, `check-gates.json` (build-notes.md withheld; gramps
> source not accessible from this sandbox). Verdicts below are re-derived from
> those three files, not copied from the gate.

## Verdict matrix (5/5/1)

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | `brief.md:10` carries a concrete, testable success criterion ("empty date → export → re-import/Verify → not flagged Invalid; serialize→deserialize→serialize stable & yields empty Date") and a category-level invariant (`brief.md:11`). Spec is well-formed and load-bearing. |
| C2 — C2 Reproduction (red pre-fix) | PASS | No C2 gate configured and build-notes withheld, but red-pre-fix is established at the production serialize path: the new assertions (`get_modifier()==MOD_NONE`, `serialize()==Date().serialize()`, patch.diff:57,70,90) contradict the old `MOD_TEXTONLY`/non-canonical-empty behavior, and `check-gates.json` C4 records `red-without-fix=PASS`. Caveat: this is a unit-level red on the `Date` layer — the literal end-to-end XML `<datestr val=""/>` + Verify "Invalid death date (1)" repro is not present in the bundle. |
| C3 — C3 Change | PASS | Coherent change targeting the spec: `gramps/gen/lib/date.py` `set_as_text()` routes empty text to `MOD_NONE`+`EMPTY` (patch.diff:32-37) and `set()` adds a guard normalizing `MOD_TEXTONLY`+empty-text to a canonical empty date (patch.diff:10-13). Single logical change; no unrelated edits. |
| C4 — C4 Verification (red→green) | PASS | Gating gate `check-gates.json` C4: `green-with-fix=PASS / red-without-fix=PASS`. Independently consistent — the five new tests (date_test.py, patch.diff:46-98) assert `MOD_NONE` and canonical serialization that the prior `MOD_TEXTONLY` empty-text form violates, so they flip red→green with the patch. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Root cause (empty date persisted as `MOD_TEXTONLY`+empty text → serialized as `<datestr val=""/>`) is plausible and fixed at the source `Date` layer, which is the right altitude per `brief.md:11` SELF-TEST. BUT the end-to-end span serialize↔deserialize↔**validate** is only asserted in code comments (patch.diff:27-31, 64-66): no artifact exercises `exportxml.py` (that it omits `<datestr>` for non-`MOD_TEXTONLY`) or `verify.py`. With gramps source inaccessible, the "XML writer omits the element / Verify no longer flags" claim cannot be re-derived from the bundle. Needs human/source confirmation of the writer + Verify path. |
| T1 — T1 Structure | N/A | Patch touches only `gramps/gen/lib/...` (core); no addons-source path present. Doc 16 §Structure (folder==id, target_version, fname, no `__init__.py`) is addon-only and does not apply. Matches gate. |
| T2 — T2 Shape | PASS | Touched hunks conform to doc 16 §Coding style — proper docstrings, no `print()`, consistent indentation/idiom (patch.diff:19-37, 46-98). Caveat: only diff hunks are visible, not full files, so GPL-header presence is inferred (edits to pre-existing modules, headers untouched), not directly observed; gate (full-file access) reports PASS for 2 files. |
| T3 — T3 Runtime | PASS | `check-gates.json` T3: matches recorded baseline (7 known reds) — the patch introduces no new failures. ⚠ Surfacing: gate also reports `baseline tree drift: recorded detached@674e3b`; "matches baseline" is therefore measured against a possibly-stale reference tree — human may wish to confirm baseline currency. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle; per `brief.md:23-27` STOP discipline the work is draft-only until sign-off, so the commit/PR wrapper is not yet expected. Doc 16 §Commit messages / §Contributor workflow not yet assessable. Matches gate. |
| T5 — T5 Judgment | NEEDS-HUMAN | Advisory read: clean, minimal, single-concern, well-tested. Open judgment for human sign-off — `set_as_text("")` / `set(MOD_TEXTONLY, text="")` semantics now change for **all** callers, not just the XML path; need confirmation this does not regress editor/UI flows that relied on an empty `MOD_TEXTONLY` date being distinct from `MOD_NONE` (scope breadth of a shared-method change). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human at sign-off (`check-gates.json` V oracle = "human at sign-off"). Does the change, as built, actually satisfy the reporter's `simpson.gramps` scenario and pre-6.0.0 parity in the real export→import→Verify flow? Requires human acceptance against the live tool. |

## §6 — Items the human must clear (NEEDS-HUMAN)

1. **C5 Causal adequacy.** Confirm against source that (a) `gramps/plugins/export/exportxml.py` omits the `<datestr>` element for an empty `MOD_NONE` date (so no `<datestr val=""/>` is written), and (b) `gramps/plugins/tool/verify.py` no longer reports "Invalid death date" for the re-imported empty date. The patch fixes the `Date` layer correctly, but the serialize→XML→validate link is asserted in comments, not demonstrated by any bundled test.
2. **T5 Judgment.** Verify the broadened `set_as_text("")`/`set()` normalization (empty text-only → `MOD_NONE`) does not regress any caller that distinguished an empty `MOD_TEXTONLY` date from `MOD_NONE` (e.g. the date editor / GUI round-trip). Scope of a shared-method behavior change.
3. **V Validation — fitness-to-purpose.** Human acceptance of the end-to-end fix against the reporter's scenario (`simpson.gramps`) and pre-6.0.0 parity in a real export → re-import → Tools→Utility→Verify-the-data run.

## Reviewer notes (advisory, non-gating)

- The strongest evidence in the bundle is the gating C4 red→green plus the directly-tested round-trip invariant `roundtrip.serialize()==once` (patch.diff:82) — the `Date`-level invariant in `brief.md:10` is genuinely exercised on the production path, not a parallel copy.
- The gap is one layer up: nothing in the bundle drives the XML writer or the Verify tool, which is exactly the symptom→root boundary the brief's SELF-TEST flags. Fixing at the `Date` layer is the correct altitude; the residual risk is purely whether the two downstream consumers key off the modifier/serialized form as the comments claim. Hence C5 → NEEDS-HUMAN rather than FAIL.
- `baseline tree drift: detached@674e3b` (T3) is the only mechanical anomaly; it does not change the verdict but should not be ignored at sign-off.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C5 — C5 Causal adequacy — Root cause (empty date persisted as `MOD_TEXTONLY`+empty text → serialized as `<datestr val=""/>`) is plausible and fixed at the source `Date` layer, which is the right altitude per `brief.md:11` SELF-TEST. BUT the end-to-end span serialize↔deserialize↔**validate** is only asserted in code comments (patch.diff:27-31, 64-66): no artifact exercises `exportxml.py` (that it omits `<datestr>` for non-`MOD_TEXTONLY`) or `verify.py`. With gramps source inaccessible, the "XML writer omits the element / Verify no longer flags" claim cannot be re-derived from the bundle. Needs human/source confirmation of the writer + Verify path.
- [x] T5 — T5 Judgment — Advisory read: clean, minimal, single-concern, well-tested. Open judgment for human sign-off — `set_as_text("")` / `set(MOD_TEXTONLY, text="")` semantics now change for **all** callers, not just the XML path; need confirmation this does not regress editor/UI flows that relied on an empty `MOD_TEXTONLY` date being distinct from `MOD_NONE` (scope breadth of a shared-method change).
- [x] V — Validation — fitness-to-purpose — Always-human at sign-off (`check-gates.json` V oracle = "human at sign-off"). Does the change, as built, actually satisfy the reporter's `simpson.gramps` scenario and pre-6.0.0 parity in the real export→import→Verify flow? Requires human acceptance against the live tool.

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
- By / date: Eduard Ralph / 2026-06-20

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
