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
