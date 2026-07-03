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
- C4 fix verified in GUI: interface repro red unpatched, green patched (headless dogtail): fail — run-verify-interface.sh: /home/eddie/gramps/gramps-6.1-lane2 has uncommitted or untracked changes — refusing to patch it
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

Task under review: fix bug 7924, where saving a parent primary editor cascade-closes a dirty child primary editor without the child's normal Save Changes guard.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief defines the defect, invariant, scope, and success criterion: parent OK must not silently discard dirty child primary-editor data, and the cascade must reuse the direct close guard ([brief.md](/tmp/pdca-review-wp6jo487/brief.md:12), [brief.md](/tmp/pdca-review-wp6jo487/brief.md:18), [brief.md](/tmp/pdca-review-wp6jo487/brief.md:32)). |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | DECISION OWED: the manual/AT-SPI reproduction is specified, but the named repro is not present in the artifact bundle or `$PDCA_TARGET`; human must confirm the pre-fix Relationships-view flow really reproduces silent loss because acceptance depends on that observed GUI baseline ([brief.md](/tmp/pdca-review-wp6jo487/brief.md:38), [brief.md](/tmp/pdca-review-wp6jo487/brief.md:42), [check-gates.json](/tmp/pdca-review-wp6jo487/check-gates.json:15)). |
| C3 — C3 Change | PASS | The patch changes the cascade so child close vetoes propagate, adds child-only pre-close traversal, and calls it before `ManagedWindow.close()` mutates parent state, matching the prior rejected sequencing issue ([patch.diff](/tmp/pdca-review-wp6jo487/patch.diff:9), [patch.diff](/tmp/pdca-review-wp6jo487/patch.diff:47), [patch.diff](/tmp/pdca-review-wp6jo487/patch.diff:77)). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | DECISION OWED: I verified `git apply --check` against `$PDCA_TARGET` and `python3 -m py_compile` on a patched temp copy pass, but the GUI red-green gate refused to run because its lane was dirty; human must run/observe the interface repro because the user-facing Save Changes prompt is the actual acceptance signal ([check-gates.json](/tmp/pdca-review-wp6jo487/check-gates.json:42), [check-gates.json](/tmp/pdca-review-wp6jo487/check-gates.json:46)). |
| C5 — C5 Causal adequacy | PASS | The existing direct primary-editor close path prompts on `data_has_changed()` ([gramps/gui/editors/editprimary.py](/home/eddie/gramps/gramps/gramps/gui/editors/editprimary.py:244)), while current cascade destroys tracked children through `close_track()` after parent state mutation ([gramps/gui/managedwindow.py](/home/eddie/gramps/gramps/gramps/gui/managedwindow.py:600)); the patch routes children through their own close and aborts if they stay open ([patch.diff](/tmp/pdca-review-wp6jo487/patch.diff:31)). |
| T1 — T1 Structure | N/A | No addon path is touched; the configured structure gate also classifies this as addon-only and not applicable ([check-gates.json](/tmp/pdca-review-wp6jo487/check-gates.json:60)). |
| T2 — T2 Shape | PASS | The configured shape and POTFILES gates passed, and the patch only modifies an existing core Python file with no new/removed core files ([check-gates.json](/tmp/pdca-review-wp6jo487/check-gates.json:69), [check-gates.json](/tmp/pdca-review-wp6jo487/check-gates.json:78)). |
| T3 — T3 Runtime | PASS | The recorded runtime gates show the core unit baseline matched known reds and the GUI smoke was green; this supports no broad runtime regression, though it is not the issue-specific GUI repro ([check-gates.json](/tmp/pdca-review-wp6jo487/check-gates.json:87), [check-gates.json](/tmp/pdca-review-wp6jo487/check-gates.json:96)). |
| T4 — T4 Contribution | N/A | No commit-message or PR-description artifact is in this bundle, and the configured contribution gate marks the wrapper check not applicable ([check-gates.json](/tmp/pdca-review-wp6jo487/check-gates.json:105)). |
| T5 — T5 Judgment | NEEDS-HUMAN | DECISION OWED: the patch is narrowly scoped and addresses the v1 ordering hazard, but shared `ManagedWindow` cascade behavior affects all tracked windows; human sign-off must decide whether aborting any child that remains open after `close()` is acceptable across the GUI manager contract ([patch.diff](/tmp/pdca-review-wp6jo487/patch.diff:29), [patch.diff](/tmp/pdca-review-wp6jo487/patch.diff:73)). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: because the success criterion is visual/user-interactive, human validation must confirm the dirty child either shows the normal Save Changes dialog or remains open with data preserved when parent OK is clicked ([brief.md](/tmp/pdca-review-wp6jo487/brief.md:12), [brief.md](/tmp/pdca-review-wp6jo487/brief.md:26)). |

## §6 Human-Clearance Items

1. C2 reproduction baseline: On an unpatched maintenance/gramps61 tree, run the Relationships view flow from [brief.md](/tmp/pdca-review-wp6jo487/brief.md:38) and confirm clicking the Family editor OK silently closes the dirty Person editor without a Save Changes prompt.
2. C4 red-to-green verification: On a patched tree, repeat the same flow and confirm the Person editor's Save Changes guard appears, or the child close is blocked, and no entered child data is lost without acknowledgement.
3. T5 shared-window-manager judgment: Decide whether treating `item.opened` after `item.close()` as a generic cascade veto is acceptable for all tracked `ManagedWindow` children, not only dirty primary editors.
4. V fitness-to-purpose: Confirm the visible GUI behavior satisfies the brief's user-facing invariant: no dirty primary-editor data is discarded without a user prompt, regardless of whether the parent or child initiated the close.


## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] C2 — C2 Reproduction (red pre-fix) — DECISION OWED: the manual/AT-SPI reproduction is specified, but the named repro is not present in the artifact bundle or `$PDCA_TARGET`; human must confirm the pre-fix Relationships-view flow really reproduces silent loss because acceptance depends on that observed GUI baseline ([brief.md](/tmp/pdca-review-wp6jo487/brief.md:38), [brief.md](/tmp/pdca-review-wp6jo487/brief.md:42), [check-gates.json](/tmp/pdca-review-wp6jo487/check-gates.json:15)).
- [ ] C4 — C4 Verification (red→green) — DECISION OWED: I verified `git apply --check` against `$PDCA_TARGET` and `python3 -m py_compile` on a patched temp copy pass, but the GUI red-green gate refused to run because its lane was dirty; human must run/observe the interface repro because the user-facing Save Changes prompt is the actual acceptance signal ([check-gates.json](/tmp/pdca-review-wp6jo487/check-gates.json:42), [check-gates.json](/tmp/pdca-review-wp6jo487/check-gates.json:46)).
- [ ] T5 — T5 Judgment — DECISION OWED: the patch is narrowly scoped and addresses the v1 ordering hazard, but shared `ManagedWindow` cascade behavior affects all tracked windows; human sign-off must decide whether aborting any child that remains open after `close()` is acceptable across the GUI manager contract ([patch.diff](/tmp/pdca-review-wp6jo487/patch.diff:29), [patch.diff](/tmp/pdca-review-wp6jo487/patch.diff:73)).
- [ ] V — Validation — fitness-to-purpose — DECISION OWED: because the success criterion is visual/user-interactive, human validation must confirm the dirty child either shows the normal Save Changes dialog or remains open with data preserved when parent OK is clicked ([brief.md](/tmp/pdca-review-wp6jo487/brief.md:12), [brief.md](/tmp/pdca-review-wp6jo487/brief.md:26)).
- [ ] C4 fix verified: test red pre-fix, green post-fix unverifiable — patch ships no core test (*_test.py) — C4 red/green cannot run locally (e.g. a prose / ci.yml / fork-CI-verified change)

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: iterated-to-Plan
- Iteration delta (if iterating): Second failed Do iteration. v1: SaveDialog rendered as empty outline, crashed on Cancel (self.db already None). v2: SaveDialog renders but Save button has no effect — data still lost with a misleading prompt. The plan approach (route cascade through EditPrimary save-guard before parent state mutation) is correct but two builder attempts have failed on the sequencing. Update brief.md to specify a stronger model for the next Do attempt; carry forward both iteration findings so the builder understands the sequencing constraint fully before attempting again.
- By / date: Eduard Ralph / 2026-07-02

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
