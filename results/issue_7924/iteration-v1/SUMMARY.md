# Result — issue 7924 / child-editor-unsaved-data-lost-on-parent-save

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: Primary editors are non-modal, so a parent editor (e.g. EditFamily) and a child
- Success criterion: With a parent editor and a child editor both open and the child holding
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the `ManagedWindow.close()` cascade (`gramps/gui/managedwindow.py:591-607`, via

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: unverifiable — patch ships no core test (*_test.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change)
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): unverifiable — the interface repro was SKIPPED (or ran no test) on the UNPATCHED tree — the env could not exercise the bug (e.g. a miss
- C5 test exercises the production path (not a copy): pass — added test(s) import the production package 'gramps'

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style (1 advisory)
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): pass — T3-baseline [green]: green (no failures); baseline now clear (1 recorded red(s) gone) | ⚠ baseline tree drift: recorded 
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

Review task: fix bug 7924 so a parent editor's cascade close cannot silently discard unsaved changes in an open child primary editor.

Target-state caveat: `$PDCA_TARGET` is readable but currently shows the pre-fix `managedwindow.py`; the patch applies cleanly there, so unchanged behavior is cited from target source and proposed behavior from `patch.diff`.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states a concrete defect, invariant, scope, and success criterion for preserving child primary-editor dirty guards during parent cascade close (`brief.md:5`, `brief.md:12`, `brief.md:18`, `brief.md:32`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | Pre-fix target code routes cascade close through `close_track()` -> `recursive_action()` -> `close_item()` and then destroys the item window without consulting the child direct-close result (`gramps/gui/managedwindow.py:180`, `gramps/gui/managedwindow.py:208`, `gramps/gui/managedwindow.py:210`, `gramps/gui/managedwindow.py:217`), while the dirty prompt exists only in direct `EditPrimary.close()` (`gramps/gui/editors/editprimary.py:244`). |
| C3 — C3 Change | PASS | The patch changes `close_track()`/`recursive_action()` to propagate a veto, makes `close_item()` treat still-open children as vetoes, and restores the parent `opened` state when a child veto aborts the cascade (`patch.diff:14`, `patch.diff:31`, `patch.diff:46`, `patch.diff:63`). |
| C4 — C4 Verification (red->green) | NEEDS-HUMAN | DECISION OWED: the GUI red->green claim turns on running the interface repro in an available lane; the recorded interface gate did not exercise it because its worktree was missing (`check-gates.json:42`, `check-gates.json:46`), and the non-interface verify gate says no local core test was shipped (`check-gates.json:33`, `check-gates.json:37`). |
| C5 — C5 Causal adequacy | PASS | The change reuses the existing synchronous `SaveDialog` direct-close guard (`gramps/gui/editors/editprimary.py:247`, `gramps/gui/dialog.py:87`) and prevents cascade teardown when that guarded close leaves the child open (`patch.diff:46`, `patch.diff:53`), addressing the bypass rather than adding parallel dirty state. |
| T1 — T1 Structure | N/A | No addon layout is involved; the bundle's T1 gate reports N/A because `patch.diff` has no `addons-source` path (`check-gates.json:60`, `check-gates.json:64`). |
| T2 — T2 Shape | PASS | The shape and POTFILES gates pass for the one touched core file and no new/removed core Python files needing registration (`check-gates.json:69`, `check-gates.json:73`, `check-gates.json:78`, `check-gates.json:82`). |
| T3 — T3 Runtime | NEEDS-HUMAN | DECISION OWED: runtime confidence turns on whether external CI or a repaired local runner covers this GUI change; both recorded runtime gates exited before producing JUnit XML, so they do not establish a product regression signal (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`). |
| T4 — T4 Contribution | N/A | No commit message or PR description artifact is in this review bundle, and the contribution gate explicitly records N/A (`check-gates.json:105`, `check-gates.json:109`). |
| T5 — T5 Judgment | PASS | The patch is narrowly scoped to the shared cascade-close path named in the brief (`brief.md:32`) and does not introduce a new dirty-tracking layer; the residual acceptance risk is the unrun GUI/runtime verification captured in C4/T3. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: final fitness depends on a human confirming the user-facing editor flow preserves or prompts for the child edit in the real GUI, which the brief explicitly expects at sign-off (`brief.md:12`, `brief.md:26`, `brief.md:27`). |

## §6 Human Clearances

- C4: Run the GUI repro against a patched target: Relationships view -> "Add a new family with person as parent" -> in Family editor click "Add a new person as mother" -> type a mother name in Person editor -> click the Family editor OK. Clear this only if the Person editor's unsaved change is either guarded by the existing "Save Changes?" dialog or otherwise remains recoverable; reject if the Person editor closes silently and loses the entry.
- T3: Re-run the core unit and interface smoke runners in a valid lane or rely on equivalent CI. Clear this only if failures, if any, are unrelated to the `ManagedWindow` cascade-close change.
- V: Decide whether the resulting UX is acceptable when a child veto leaves the parent editor open after the parent OK click; the patch prevents silent loss, but product acceptance of that interaction requires human sign-off.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C4 — C4 Verification (red->green) — DECISION OWED: the GUI red->green claim turns on running the interface repro in an available lane; the recorded interface gate did not exercise it because its worktree was missing (`check-gates.json:42`, `check-gates.json:46`), and the non-interface verify gate says no local core test was shipped (`check-gates.json:33`, `check-gates.json:37`).
- [ ] T3 — T3 Runtime — DECISION OWED: runtime confidence turns on whether external CI or a repaired local runner covers this GUI change; both recorded runtime gates exited before producing JUnit XML, so they do not establish a product regression signal (`check-gates.json:87`, `check-gates.json:91`, `check-gates.json:96`, `check-gates.json:100`).
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: final fitness depends on a human confirming the user-facing editor flow preserves or prompts for the child edit in the real GUI, which the brief explicitly expects at sign-off (`brief.md:12`, `brief.md:26`, `brief.md:27`).
- [ ] C4 fix verified: test red pre-fix, green post-fix unverifiable — patch ships no core test (*_test.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change)
- [ ] C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail) unverifiable — the interface repro was SKIPPED (or ran no test) on the UNPATCHED tree — the env could not exercise the bug (e.g. a miss

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
- Iteration delta (if iterating): Manual GUI verification on patched gramps-6.1 revealed the fix has a sequencing bug: ManagedWindow.close() sets self.opened=False and calls _save_position()/_save_size() before calling close_track(), so by the time the child's SaveDialog fires during the cascade the parent GTK container is already partially destroyed. Symptoms observed: (1) the "Save Changes?" dialog rendered only as an outline with no usable content; (2) clicking Cancel crashed with AttributeError: 'NoneType' object has no attribute 'serializer' in editsecondary.py:139 (self.db already None); (3) "Missing item from window manager [0, 1]" warning confirmed the window tree was left in an inconsistent state. The approach (veto the cascade at the child save-guard) is correct but the parent must not begin its own teardown before the child veto is resolved — the sequence in ManagedWindow.close() needs to be reordered so the child-veto check runs before any self state is mutated.
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- Pre-existing crash: `AttributeError: 'ChildEmbedList' has no attribute 'tree'` in `embeddedlist.py:594` ← `editfamily.py:297` (`child_ref_edited` → `rebuild`) when saving a Child Reference Editor that has no entry in "Relationship to Father" or "Relationship to Mother"; found during 7924 manual verification, unrelated to patch — file as new Mantis.
