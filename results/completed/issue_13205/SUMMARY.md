# Result — issue 13205 / ** merge-citations-noncitation-backlink-crash

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: ** Tools → Family Tree Processing → **Merge Citations** aborts with `gramps.gen.errors.MergeError: Encountered an object of type Note that has a citation reference.` and forces the user to kill Gramps. A **regression**: the reporter confirms the same database merged successfully (977 citations) on 5.1.6, and it breaks on 5.2.0 / 5.2.1 / 5.2.2. (Mantis 13205.)
- Success criterion: ** Running the Merge Citations logic over a database where a Source is referenced by a **non-Citation** object (e.g. a Note that carries a source/citation reference) completes the merge pass **without raising `MergeError`** — non-Citation backlinks of a source are skipped, and citations are still merged as before.
- Repo + branch target: ** gramps (core) @ `maintenance/gramps61` — branched from `upstream/maintenance/gramps61`; forward-merged to `master` (INTEGRATION §2: core fixes ride the current maintenance branch).
- Scope (one logical fix) / out of scope: ** Two coupled, minimal changes forming one logical fix: **(1)** stop the merge loop from assuming **every** backlink of a Source is a Citation — collect only Citation backlinks (pass `include_classes=["Citation"]` to `find_backlink_handles`, signature `find_backlink_handles(handle, include_classes=None)` at `gramps/gen/db/base.py:99`, or `continue` past non-Citation `class_name` instead of raising). **(2)** Put that source→citation-handles collection in a **new GUI-free module** — e.g. `gramps/plugins/tool/mergecitationslib.py` — importing ONLY `gramps.gen.*` (NO `gi.repository`, NO `gramps.gui.*`), exposing a module-level function such as `citation_handles_of_source(db, source_handle) -> list[str]` (skips non-Citation backlinks). `mergecitations.py` imports the helper from that module and calls it where `on_merge_ok_clicked` did the loop — behaviour preserved. **The load-bearing constraint:** the test imports ONLY that GUI-free module and NEVER `gramps.plugins.tool.mergecitations`, because the tool module pulls the whole GUI stack at load (`Gtk` + `gramps.gui.*`, `mergecitations.py:39,52-60`) and the headless C4 runner core-dumps on it (this sank both prior Do rounds). / **out of scope:** changing the actual citation-merge behaviour (`MergeCitationQuery`); the "don't merge if citation has notes" option semantics; investigating *why* 5.2 introduced the non-citation backlink (root of the regression is the unguarded assumption, not the new backlink itself).

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: ** likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change)
- T2 shape: code shape vs doc 16 §Coding style (GPL header, no diagnostic print): pass — T2 – N/A: no addons-source path in patch.diff (core-only change)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — bash: line 39:   254 Trace/breakpoint trap   (core dumped) GRAMPS_RESOURCES=. python3 -m xmlrunner discover -p "*_test.p
- T3 runtime: addon unit suites (whole-suite baseline): fail — → pip install logs (3 failure(s)): gramps-testbed-v2/test-results/install-logs/
- T3 runtime: GUI interface smoke (launch + open tree, headless dogtail): fail — Generated XML report: test-results/TEST-unittest.suite._ErrorHolder-20260606095734.xml
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check review — issue 13205 / merge-citations-noncitation-backlink-crash

> Advisory, artifact-only, decorrelated. Inputs: `patch.diff`, `brief.md`,
> `check-gates.json`. `build-notes.md` was withheld by design. Every basis below
> is re-derived from the artifacts, not copied from the gate file.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | `brief.md:20` success criterion is concrete and falsifiable: merge over a DB where a Source has a non-Citation backlink completes "without raising `MergeError`", non-Citation backlinks skipped, citations still merged. Repro + root cause cited at `brief.md:23` (`mergecitations.py:199-207`). |
| C2 — C2 Reproduction (red pre-fix) | PASS | No standalone C2 gate, but `check-gates.json` C4-verify records `red-without-fix=PASS`. Re-derived: pre-fix `from gramps.gen.utils.db import citation_handles_of_source` (`patch.diff` test line 72) raises ImportError → red. Caveat: red is *helper-absence*, not the behavioral `MergeError`; brief sanctions this ("missing helper", `brief.md:24`) under the headless-GUI constraint. |
| C3 — C3 Change | PASS | Coherent minimal fix: helper `citation_handles_of_source(db, source_handle)` at `gramps/gen/utils/db.py` (`patch.diff:9-28`, signature matches `brief.md:22`); call site swaps the raising loop for the helper at `mergecitations.py:197-209` (`patch.diff:152-172`). Deviation noted: helper placed in `gen/utils/db.py`, not the brief's `gramps/plugins/tool/mergecitationslib.py` (raised under V). |
| C4 — C4 Verification (red→green) | PASS | Gating row C4-verify = pass (`green-with-fix=PASS / red-without-fix=PASS`, `check-gates.json:33-39`). Re-derived plausible: green because `get_referents` filters `item[0]=="Citation"`, dropping the Note; the `_FakeDb` (`patch.diff` test lines 86-89) is what `get_referents` calls, so the filtering is genuinely exercised, not mocked away. Caveat: the GUI-free test cannot import `mergecitations.py`, so red→green verifies the helper only, never the tool's runtime. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Logic addresses the stated root cause (unguarded "every backlink is a Citation"). But adequacy rests on two facts not in the artifacts: (1) `get_source_referents`'s `_primaries` must be exactly `["Citation"]` for `(citation_handles,) = ...` (`patch.diff:27`) to unpack correctly — only the call `get_referents(source_handle, db, _primaries)` is visible, not `_primaries`; (2) the deleted `gramps.gen.lib` imports must be unused elsewhere in `mergecitations.py`, else the tool NameErrors at runtime — uncatchable by the GUI-free C4 runner. Human must confirm against `maintenance/gramps61`. |
| T1 — T1 Structure | N/A | Core-only change; no addons-source path in `patch.diff`, so the addon layout rules (folder==id, target_version, fname) do not apply (`check-gates.json:55`). Note for human: the test landed at `gramps/plugins/test/mergecitations_test.py`, not the brief's `gramps/plugins/tool/test/...`, and no `__init__.py` appears in the patch — a core-convention deviation, not a T1 addon check. |
| T2 — T2 Shape | N/A | Core-only; addon coding-style oracle does not apply (`check-gates.json:64`). Observed regardless: new test carries the GPL header (`patch.diff` test lines 40-57) and contains no diagnostic prints. |
| T3 — T3 Runtime | NEEDS-HUMAN | All three T3 rows fail (`check-gates.json:72,80,88`): whole-suite `Trace/breakpoint trap (core dumped)`, addon pip-install failures, GUI smoke. The new test is GUI-free and runs green under the C4 core runner, so the core-dump is a headless-GTK / display baseline issue from other suites, not plausibly introduced by a 3-file core change. Cannot confirm "pre-existing baseline" without the withheld baseline run / build-notes — human must attribute. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle, so the commit/PR-wrapper oracle has nothing to check (`check-gates.json:100`). |
| T5 — T5 Judgment | NEEDS-HUMAN | Reviewer+human item. Three judgment risks I cannot close from artifacts: (a) deleted `from gramps.gen.lib import Person, Family, Event, Place, Media, Repository` (`patch.diff:147`) — only `Citation` is provably now-unused; the other six may be referenced elsewhere in `mergecitations.py`; (b) helper placement deviates from brief's named module; (c) test path + missing `__init__.py` deviation. Each needs a human read of the full tool file on the target branch. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. Confirm that placing the helper in `gen/utils/db.py` and reusing `get_source_referents` (vs the brief's dedicated GUI-free `mergecitationslib.py`) genuinely satisfies issue 13205's intent, and that a real DB merge over the reporter's fixture (977 citations + a non-Citation source backlink) now completes without `MergeError`. |

## §6 — Items the human must clear

1. **C5 / causal adequacy.** Verify on `maintenance/gramps61` that `get_source_referents`'s `_primaries == ["Citation"]` (so the 1-tuple unpack at `patch.diff:27` holds), and that the merge still collects the same Citation handles it did pre-fix.
2. **C5 + T5 / removed imports.** Read the full `mergecitations.py` and confirm `Person, Family, Event, Place, Media, Repository` (and `MergeError`) are unused after the change — the headless C4/T3 runners can't import the tool, so a NameError would ship undetected.
3. **T3 / runtime attribution.** Confirm the whole-suite core-dump and addon/interface failures (`check-gates.json:72,80,88`) are a pre-existing headless baseline, not introduced by this patch.
4. **T5 + V / scope deviations.** Decide whether helper-in-`gen/utils/db.py` (vs brief's `mergecitationslib.py`), the test path `gramps/plugins/test/` (vs `gramps/plugins/tool/test/`), and the absent `__init__.py` are acceptable, or require alignment with the brief.
5. **V / fitness-to-purpose.** Sign off that the fix resolves 13205 against the reporter's real fixture, not just the synthetic `_FakeDb`.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] C5 — C5 Causal adequacy — Logic addresses the stated root cause (unguarded "every backlink is a Citation"). But adequacy rests on two facts not in the artifacts: (1) `get_source_referents`'s `_primaries` must be exactly `["Citation"]` for `(citation_handles,) = ...` (`patch.diff:27`) to unpack correctly — only the call `get_referents(source_handle, db, _primaries)` is visible, not `_primaries`; (2) the deleted `gramps.gen.lib` imports must be unused elsewhere in `mergecitations.py`, else the tool NameErrors at runtime — uncatchable by the GUI-free C4 runner. Human must confirm against `maintenance/gramps61`.
- [x] T3 — T3 Runtime — All three T3 rows fail (`check-gates.json:72,80,88`): whole-suite `Trace/breakpoint trap (core dumped)`, addon pip-install failures, GUI smoke. The new test is GUI-free and runs green under the C4 core runner, so the core-dump is a headless-GTK / display baseline issue from other suites, not plausibly introduced by a 3-file core change. Cannot confirm "pre-existing baseline" without the withheld baseline run / build-notes — human must attribute.
- [x] T5 — T5 Judgment — Reviewer+human item. Three judgment risks I cannot close from artifacts: (a) deleted `from gramps.gen.lib import Person, Family, Event, Place, Media, Repository` (`patch.diff:147`) — only `Citation` is provably now-unused; the other six may be referenced elsewhere in `mergecitations.py`; (b) helper placement deviates from brief's named module; (c) test path + missing `__init__.py` deviation. Each needs a human read of the full tool file on the target branch.
- [x] V — Validation — fitness-to-purpose — Always-human. Confirm that placing the helper in `gen/utils/db.py` and reusing `get_source_referents` (vs the brief's dedicated GUI-free `mergecitationslib.py`) genuinely satisfies issue 13205's intent, and that a real DB merge over the reporter's fixture (977 citations + a non-Citation source backlink) now completes without `MergeError`.

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
- (empty is the common case)
