# Result — issue 13636 / ** uimanager-update-menu-none-toolbar-parent

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: ** Closing the Gramps main window (top-right `X`) before the addons-update window has opened produces an unhandled `AttributeError: 'NoneType' object has no attribute 'remove'` from `gramps/gui/uimanager.py` `update_menu`, triggered when `gramps/gui/viewmanager.py` `page_changer` fires during teardown and iterates toolbars whose parent has already been detached. Reported against Gramps 5.1.6 on Windows / GTK 3.18.9 (Mantis 13636). The trailing "Top Surnames" gramplet warning quoted in the bug title is a separate, unrelated `_gramplet.py` log line and is **not** part of this crash.
- Success criterion: ** On `maintenance/gramps61`, calling `update_menu()` while one or more toolbars have `get_parent() is None` (the shutdown-race condition) returns cleanly without raising; consequently, closing the Gramps main window before the addons-update window opens no longer logs an unhandled exception. The regression test in the file below asserts this behaviour and is **red on the unpatched branch, green after the fix**.
- Repo + branch target: ** `gramps-project/gramps @ maintenance/gramps61` (per INTEGRATION §2 — core fixes target the current production maintenance branch, not `master`, not `maintenance/gramps60`).
- Scope (one logical fix) / out of scope: ** Add a `None`-guard in `gramps/gui/uimanager.py` `update_menu` so that a toolbar already detached from its parent (`toolbar.get_parent() is None`) is skipped without calling `.remove()` on `None`. / **Out of scope:** redesigning `viewmanager.page_changer` to suppress signals during teardown; reordering Gramps shutdown so the addons-update path can't race; the unrelated "Top Surnames" `_gramplet.py:342` warning quoted in the Mantis title; Windows-specific reproducibility (the defect is a missing Python `None`-check, platform-agnostic); any broader audit of other unguarded `get_parent()` callers in `uimanager.py` / `viewmanager.py`.

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: ** likely-fix — the defect reproduces directly from the trace, the surgical guard is bounded to one call site, and the unit-test substitute for the GUI race is straightforward.
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T3 runtime: gramps core unit suite (whole-suite baseline): fail — Generated XML report: /workspace/gramps-testbed-v2/test-results/TEST-gramps.gen.merge.test.merge_ref_test.SourceSourceCh
- T5 judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review — issue 13636 / uimanager-update-menu-none-toolbar-parent

> Advisory, artifact-only review. Inputs available to me: `patch.diff`,
> `brief.md`, `check-gates.json`. `build-notes.md` was deliberately withheld,
> so anything that lives only in the builder's notes (path:line citations,
> "Caused by" SHA, branch-target proof) I mark NEEDS-HUMAN rather than guess.
> Evidence below was re-derived from the diff itself, decorrelated from the
> builder. I did not (and cannot, in this artifact-only sandbox) re-run the
> suite; runtime claims lean on the oracle rows in `check-gates.json`, flagged
> as such.

## Summary verdict

| # | Item | Verdict |
|---|------|---------|
| 1 | C4 fix verified — test red pre-fix / green post-fix (gating) | **PASS** |
| 2 | T3 runtime — gramps core unit suite (non-gating baseline) | **PASS (with note)** |
| 3 | Scope adherence — guard bounded to one call site | **PASS** |
| 4 | Regression test is a genuine red/green oracle | **PASS** |
| 5 | Test exercises the real removal path (no false-green) | **PASS** |
| 6 | path:line + "Caused by" SHA citations | **NEEDS-HUMAN** |
| 7 | Branch target = `maintenance/gramps61` | **NEEDS-HUMAN** |
| 8 | C5 causal adequacy (early-`return` design) | **NEEDS-HUMAN** |
| 9 | T5 judgment | **NEEDS-HUMAN** |
| 10 | Validation act / fitness-to-purpose | **NEEDS-HUMAN** |

Overall posture: **consistent with `overall: pass`** in `check-gates.json` for
the gating machine checks; the open items are the always-human ones plus two
items I cannot verify because their evidence sits in the withheld build-notes.

---

## Per-item findings

### 1. C4-verify (gating) — PASS
`check-gates.json` reports `C4-verify: green-with-fix=PASS / red-without-fix=PASS`.
I independently confirm the test is *constructed* to deliver that result:

- **Red without fix:** On unpatched code the flow is
  `toolbar_parent = toolbar.get_parent()` → `toolbar_parent.remove(toolbar)`.
  With `toolbar.get_parent.return_value = None`, that second line is
  `None.remove(...)` → `AttributeError`, which
  `test_detached_toolbar_does_not_raise` converts to a `self.fail(...)`.
- **Green with fix:** the inserted `if toolbar_parent is None: ... return`
  short-circuits before `.remove()`.

The test also asserts `toolbar.get_parent.assert_called_once_with()`, which
guards against a *false* red (i.e. it proves the failure, when it happens, comes
from the toolbar path and not from some earlier exception). Gating check is
satisfied. This is the load-bearing match against the brief's success criterion
("red on the unpatched branch, green after the fix"). **PASS.**

### 2. T3-unit (non-gating) — PASS (with note)
The row is `result: fail`, `gating: false`, with `path_line` pointing at
`TEST-gramps.gen.merge.test.merge_ref_test.SourceSourceCh...`. That failing test
lives in `gramps.gen.merge` — a module with no coupling to `gramps/gui/uimanager.py`.
A `None`-guard added to a GUI toolbar path cannot causally affect a merge-ref
test, so this is a pre-existing whole-suite baseline failure, not a regression
introduced by this patch. It is correctly non-gating. **PASS**, with the note
that the human should confirm `merge_ref_test...SourceSourceCh` is a *known*
baseline red (not newly broken) — I can assert non-causation from the diff, but
"known baseline" is a fact about suite history I don't have.

### 3. Scope adherence — PASS
The diff touches exactly two files: the one-call-site guard in
`gramps/gui/uimanager.py` and the new `gramps/gui/tests/uimanager_test.py`.
Nothing in the out-of-scope list (page_changer redesign, shutdown reordering,
the unrelated "Top Surnames" `_gramplet.py` warning, a broader audit of other
`get_parent()` callers) is touched. The guard is surgical and bounded as the
brief requires. **PASS.**

### 4. Regression test is a genuine red/green oracle — PASS
See item 1. The test is at the unit layer as the brief mandates (interface
runner not yet ported), mocks `Gtk` and `config` so no display is needed, drives
a `get_parent()→None` toolbar through `update_menu(init=False)`, and asserts no
`AttributeError`. It is in the canonical home `gramps/gui/tests/uimanager_test.py`
with the `*_test.py` discovery suffix. **PASS.**

### 5. Test exercises the real removal path — PASS
Two defences against a false green:
- `test_detached_toolbar_does_not_raise` asserts `get_parent` was actually
  reached (`assert_called_once_with()`), so a green can't come from the function
  bailing out earlier.
- `test_attached_toolbar_is_still_updated` is a positive control: with a real
  parent it asserts `parent.remove(toolbar)` *and* `parent.pack_start` fire,
  proving the new `None`-guard does not short-circuit the normal (attached) path.

Caveat I cannot close artifact-only: I can't confirm `update_menu(init=False)`
reaches line ~257 without an earlier `init`-gated branch diverting it, nor that
`UIManager.__init__` survives with `Gtk` mocked. The passing C4 oracle is
empirical evidence that it does; I note the dependence rather than re-derive it.

### 6. path:line + "Caused by" SHA citations — NEEDS-HUMAN
The brief requires Do to cite `path:line` on `maintenance/gramps61` for the
guarded call site and the test, and—if `git blame` finds the introducing
commit—a separately-labelled "Caused by: <SHA>" line (fix-side "Verified
against" lines staying SHA-free). Those citations live in `build-notes.md`,
which is withheld. The diff's hunk header (`@@ -257,7`) is *a* line anchor but
is not a substitute for the branch-relative citation the brief demands.
**NEEDS-HUMAN** to confirm the citations exist and resolve on the target branch.

### 7. Branch target `maintenance/gramps61` — NEEDS-HUMAN
The brief is explicit that the fix targets `gramps-project/gramps @
maintenance/gramps61` (not master, not gramps60). A bare unified diff carries no
branch identity, and this sandbox is not a git repo, so I cannot verify the
patch was cut against, and still applies cleanly to, `maintenance/gramps61`
(including that line 257 is the equivalent call site there). **NEEDS-HUMAN.**

### 8. C5 causal adequacy — NEEDS-HUMAN
Oracle is "reviewer + human sign-off" (always-human). My substantive concern to
hand the human: the guard does a **full `return` from `update_menu`**, not a
narrow skip of the toolbar-removal statement. The brief's scope says the
detached toolbar should be "skipped without calling `.remove()` on `None`," and
the success criterion only requires "returns cleanly without raising," which the
early return satisfies. But the wording is ambiguous between *skip the toolbar
block and continue* vs *exit the function*. If there exists any non-shutdown
path where a toolbar legitimately has no parent yet the menu/menubar/popup
updates further down `update_menu` still need to run, the early `return` would
silently drop those updates. In the reported (shutdown/teardown) scenario this
is harmless. Low risk given the framing, but it is a real behavioural choice the
human should ratify. **NEEDS-HUMAN.**

### 9. T5 judgment — NEEDS-HUMAN
Oracle is "reviewer + human sign-off." Defer. (Disposition hint in the brief is
"likely-fix," consistent with what I see.) **NEEDS-HUMAN.**

### 10. Validation act / fitness-to-purpose — NEEDS-HUMAN
Oracle is "human at sign-off." Whether the unit-layer substitute adequately
stands in for the un-ported GUI shutdown-race repro, and whether closing the
real main window now behaves, is a fitness judgment outside machine reach.
**NEEDS-HUMAN.**

---

## Notes for the human reviewer
- The patch is small, on-scope, and the regression test is a real red/green
  oracle — the gating machine evidence (C4) holds up to independent re-derivation.
- Two non-human items I could *not* clear are evidence-withheld, not failures:
  the path:line/SHA citations (item 6) and branch-target proof (item 7). If the
  withheld `build-notes.md` carries them and they resolve on
  `maintenance/gramps61`, both flip to PASS.
- One design point worth a glance at sign-off: the guard returns from the whole
  function (item 8). Confirm that's intended vs. a narrower skip.
- T3-unit's red is the unrelated `gramps.gen.merge` test; confirm it's a known
  baseline before discounting it (item 2).

## 6. NEEDS-HUMAN — items the human must clear before sign-off
> The advisory review (§5) flagged items 6–10 as NEEDS-HUMAN; recorded here and
> cleared by the human at sign-off (explicit OK, 2026-06-04).
- [x] Item 6 — path:line citations present in build-notes (uimanager.py:258,260,269; viewmanager.py:1061,1062,1066). Human accepts; "Caused by" SHA intentionally not asserted (blame not run, not fabricated).
- [x] Item 7 — branch target maintenance/gramps61 (build-notes: .git/HEAD → refs/heads/maintenance/gramps61). Human accepts.
- [x] Item 8 — C5 early-`return` design ratified (same toolbar_parent re-derefed at :269; full return is the correct minimal behaviour on a closing window).
- [x] Item 9 — T5 judgment: likely-fix. Human accepts.
- [x] Item 10 — Validation / fitness-to-purpose: unit-layer mock accepted as stand-in for the un-ported GUI shutdown-race repro. Human accepts.

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
- By / date: Eduard Ralph / 2026-06-04

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
