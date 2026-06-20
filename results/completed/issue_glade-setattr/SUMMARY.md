# Result — issue glade-setattr / ** glade-setattr-name-mangling

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: ** `gramps/gui/glade.py` — `Glade(Gtk.Builder).__setattr__` (~L62–69) raises `AttributeError: Ad-hoc attribute _Glade__dirname is not permitted.` whenever a `Glade()` is constructed, blocking GUI startup (reds the `T3-interface` smoke; testbed #1). Two bugs were introduced by `f8c1fc0f50` ("Don't use slots on GObject-derived classes.", on `maintenance/gramps61` and `master`): (1) the guard whitelist lists the **unmangled** names `"__toplevel"/"__filename"/"__dirname"`, but `__init__` assigns `self.__dirname`/`self.__filename`/`self.__toplevel`, which Python name-mangles to `_Glade__dirname` etc. → rejected by the guard; (2) `super().__setattr__(self, name, value)` passes `self` twice — a bound `super()` method already carries it — so once the guard is satisfied it raises `TypeError`. Both confirmed in `git -C ../gramps show maintenance/gramps61:gramps/gui/glade.py` (setattr ~L62–69; mangled assignments at the `self.__dirname, self.__filename = os.path.split(path)` line and the `self.__toplevel = …` lines).
- Success criterion: ** constructing `Glade()` (and loading a real `.glade` file) raises no `AttributeError`/`TypeError`; the `T3-interface` smoke launches the GUI.
- Repo + branch target: ** `gramps @ maintenance/gramps61` (core fix per INTEGRATION §2; cherry-picked forward to `master`).
- Scope (one logical fix) / out of scope: ** the two-line fix to `Glade.__setattr__` — whitelist the **mangled** attribute names and drop the duplicate `self` from the `super().__setattr__` call / out of scope: any other refactor of `glade.py`, touching `__init__`, or reworking how the slots-removal in `f8c1fc0f50` was done elsewhere.

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: ** likely-fix (regression in `f8c1fc0f50`).
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
- T2 shape: code shape vs doc 16 §Coding style (GPL header, no diagnostic print): pass — T2 ✓ shape: 1 file(s) conform to doc 16 §Coding style
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — T3-baseline [delta]: DELTA: runner exited 133 with no parsed failures and no matching baseline signature (a new failure 
- T3 runtime: addon suites — addons-source gramps60 × core 6.0 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 1 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: addon suites — addons-source gramps61 × core 6.1 (matrix): fail — T3-baseline [delta]: DELTA: runner exited 1 with no parsed failures and no matching baseline signature (a new failure mo
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): fail — T3-baseline [delta]: DELTA: 1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — glade-setattr-name-mangling

Advisory, artifact-only review. Inputs: `patch.diff`, `brief.md`, `check-gates.json`
(`build-notes.md` withheld by design). Verdicts re-derived independently below.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | brief.md:10 gives an unambiguous success criterion; defect, scope, and two-line fix spec (brief.md:9,12,16–24) are concrete and verified against `maintenance/gramps61`. |
| C2 — C2 Reproduction (red pre-fix) | PASS | No C2 gate configured, but reproduction is demonstrated by C4-verify `red-without-fix=PASS` (check-gates.json:37); matches brief repro (brief.md:13) — `_Glade__dirname` AttributeError pre-fix. |
| C3 — C3 Change | PASS | patch.diff:9–18 matches the brief fix spec verbatim (mangled whitelist + dropped duplicate `self`); only `__setattr__` and the new test touched, `__init__` untouched — in scope (brief.md:12). |
| C4 — C4 Verification (red→green) | PASS | check-gates.json:33–39 gating C4-verify `green-with-fix=PASS / red-without-fix=PASS`; new test (patch.diff:85–101) drives the real `Glade()` path per Iteration-1 ask (brief.md:39). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Root cause of the AttributeError/TypeError is well-supported, but the fix is not shown causally adequate to the stated criterion "launch the GUI": T3-interface still reds with a NEW `setUpClass` failure (check-gates.json:100). Whether that residual is environmental or a real gap is contested — human must decide. |
| T1 — T1 Structure | N/A | Core-only change; no addons-source path in patch.diff and doc 16 §Structure is addon-only (check-gates.json:55). |
| T2 — T2 Shape | PASS | check-gates.json:64 — 1 file conforms to §Coding style; missing GPL header on the new test accepted as repo test-file convention, non-blocking (brief.md:39). |
| T3 — T3 Runtime | FAIL | T3-interface — the success-criterion smoke — still red: `1 new failure(s) not in baseline: setUpClass (interface.test_smoke.SmokeTest)` (check-gates.json:100). T3-unit exited 133 / addon-60 / addon-61 also fail (check-gates.json:73,82,91). |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle (check-gates.json:109). |
| T5 — T5 Judgment | NEEDS-HUMAN | Code change is sound, minimal, in-scope and unit-green, yet the end-to-end criterion (GUI smoke) is unmet (T3-interface red). Accept/reject hinges on the contested setUpClass residual — reviewer+human sign-off (check-gates.json:114). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human at sign-off. Brief success criterion "the T3-interface smoke launches the GUI" (brief.md:10) is not demonstrably met; fitness-to-purpose cannot be auto-asserted. |

## §6 — Items the human must clear

1. **C5 — causal adequacy / contested root-cause.** The `__setattr__` two-bug fix
   removes the AttributeError/TypeError, but T3-interface smoke still shows a NEW
   `setUpClass (interface.test_smoke.SmokeTest)` failure not in baseline. Determine
   whether this is an environmental headless-dogtail `setUpClass` failure or a real
   residual blocking GUI startup — exactly the open question carried forward from
   Iteration 1 (brief.md:39). Baseline re-promotion (brief.md:26) cannot proceed
   until it is green for the right reason.

2. **T5 — judgment.** Unit-level verification is green (C4), the real `Glade()`
   construction path is now exercised (addresses the Iteration-1 ask), and the diff
   is minimal/in-scope — but the brief's load-bearing success criterion is the GUI
   smoke, which is still red. Human to weigh whether the unit-green fix is acceptable
   despite the unmet end-to-end criterion.

3. **V — validation fitness-to-purpose.** Human at sign-off must confirm the fix
   actually restores GUI startup as intended, given T3-interface is not green.

## Notes (advisory, non-gating)

- T3-unit exited 133 with no parsed failures and no matching baseline signature
  (check-gates.json:73) and the addon matrices exited 1 (lines 82, 91). These read
  as runner/environment deltas rather than failures attributable to this two-line
  core change, but they are unexplained from the artifacts alone and should not be
  silently treated as pass. Only T3-interface bears directly on the success criterion.
- Positive: the new test (patch.diff:43–49, 85–101) deliberately loads a real,
  display-free `GtkListStore` `.glade` through the real `__init__`, directly answering
  the Iteration-1 request to stop relying on a synthetic `__setattr__` bypass.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C5 — C5 Causal adequacy — Root cause of the AttributeError/TypeError is well-supported, but the fix is not shown causally adequate to the stated criterion "launch the GUI": T3-interface still reds with a NEW `setUpClass` failure (check-gates.json:100). Whether that residual is environmental or a real gap is contested — human must decide.
- [x] T5 — T5 Judgment — Code change is sound, minimal, in-scope and unit-green, yet the end-to-end criterion (GUI smoke) is unmet (T3-interface red). Accept/reject hinges on the contested setUpClass residual — reviewer+human sign-off (check-gates.json:114).
- [x] V — Validation — fitness-to-purpose — Always-human at sign-off. Brief success criterion "the T3-interface smoke launches the GUI" (brief.md:10) is not demonstrably met; fitness-to-purpose cannot be auto-asserted.

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
- By / date: Eduard Ralph / 2026-06-06

## 10. Act candidates (hints for the next Act review)
- Success-criterion misframing (planner/brief): this fix was gated on the repo-scoped
  T3-interface smoke going green, but a repo gate never applies the bundle's patch.diff
  — so it stayed red on the very `_Glade__dirname` bug the patch fixes and could only
  clear post-merge. C4-verify (bundle-scoped, patch applied) was green and is the real
  per-fix proof. A per-fix success criterion must be achievable by the bundle (C4 red→
  green), not a whole-suite/repo gate that only clears once the fix is merged.
- t3_baseline precedence bug (testbed engine): `classify()` flags a parsed per-test
  failure as a delta BEFORE checking `run_level_signatures`, so a known whole-run
  baseline red (the `_Glade__dirname`/`_ErrorHolder` smoke, surfacing as a `setUpClass`
  failure) is mislabeled "new". A matching run-level signature should classify the run
  as baseline even when per-test failures are parsed — or record the `setUpClass` id in
  `engine/baselines/run-interface.json` `known_failures`.
- Publish target parsing fragile (testbed driver + template): first bundle taken to
  `pdca publish` could not resolve a target. Two compounding faults — (1) `parse_fields`'
  regex (`brief.py:15`) expects `**Label**:` (colon outside the bold), but
  `templates/brief.md.tpl` and every brief write `**Label:**` (colon inside), so the
  closing `**` leaks into every field value; (2) `_resolve_target` (`publish.py:139`)
  `partition("@")`s the raw value, so backticks, a trailing parenthetical, and a bare
  repo name (`gramps`, not the `owner/repo` that `gh --repo` needs) all flow into the
  git/gh commands. Unblocked by hand-cleaning `brief.md:11` to
  `**Repo + branch target**: gramps-project/gramps @ maintenance/gramps61`. Real fix:
  make `parse_fields` tolerate `**Label:**`; have `_resolve_target` strip backticks /
  take only the `repo @ branch` token / normalize the repo to `owner/repo`; align the
  template. Carry the template change back to the pdca-harness template.
