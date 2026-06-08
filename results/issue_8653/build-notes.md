# Build notes — issue 8653 / deep-connections-excludes-start-person (iteration 2)

> Withheld from the reviewer. Rationale, rejected alternatives, and the
> production-path/genuine-red reasoning that the patch + test alone don't show.
> Citations are `path:line` on `addons-source @ upstream/maintenance/gramps60`
> (the worktree file is byte-identical to upstream, brief.md:14).

## Root cause (two sentences)

In the BFS, `get_relatives(person_handle, path)` anchors every returned relative's
new path node at `person_handle` — the person being expanded — so when the **Home/
start person is the node being expanded** (it is the first node popped, the root
`(None, ("self", D))`, seeded at `DeepConnectionsGramplet.py:352-358`), each of its
relatives gets an intermediate step `(path, (relation, D))` anchored at Home, e.g.
`(S, (root, ("sibling", D)))`. That intermediate `("sibling", D)` step then sits in
the produced path *below* the `("self", D)` root, so the Home person is rendered both
as an interior "sibling of <Home>" anchor and as the root (the reporter's first,
"definitely a bug" case). The visited-cache (`:435-438`) blocks re-*expanding* Home but
not this re-*naming*, which is why the bug survives on gramps60 (refutes "already
fixed").

## The fix (smallest change that restores the invariant)

`get_relatives` (`DeepConnectionsGramplet.py:221`) gains `start_handle=None` and, at its
tail (after the original body, `:276-279`), a post-process applied only when the caller
supplies the start handle:

```python
if start_handle is not None:
    retval = [item for item in retval if item[0] != start_handle]
    if person_handle == start_handle:
        retval = [(item[0], path) for item in retval]
```

- **Line 1** drops any relative that *is* the start person, so Home is never re-entered
  as an interior node.
- **Lines 2–3** are the load-bearing fix for the reporter's case: when the start person
  itself is being expanded, its relatives attach straight to the root node (`path` is
  that root here) instead of through the redundant `(relation, start)` step. Home is then
  recorded only as the `("self", …)` root.

`main()`'s only change is at the call site (`:439`): it now passes the start handle as a
**value** — `self.get_relatives(current_handle, current_path, self.default_person.handle)`.
This is the post-guard caller; `self.default_person` is fetched at `:331` and the "No Home
Person set" early-return guard is at `:334-338`, and `get_relatives` is called *only* here,
*after* the guard. So the None-deref risk that got iteration-1 iterated (carry-forward §3 /
T5-b) **cannot occur in production**: the handle is read where Home is already known
non-None, never re-dereferenced inside `get_relatives` on a path that can run before the
guard.

**Why this is minimal, per the Invariant-to-restore rule (brief.md:13).** The Home person
becomes an *anchor* in a path node only at the one place an anchor is created — when it is
the expanded node — and it is expanded exactly once (root pop, then cached). So fixing the
root-expansion case is the whole invariant; nothing in the renderer (`pretty_print`,
`:287-316`) or the loop needs to change.

### Rendered-label effect (carry-forward §4 — for the human at sign-off)

Collapsing Home's direct relatives onto the root drops the *explicit* "… of <Home>" text
for those relatives (e.g. S no longer renders "sibling of <Home>" as a path step). S's
relationship to Home is still shown — `pretty_print` annotates each rendered step with the
relationship calculator's `[…]` result (`:310-314`), so a downstream "child of S [nephew]"
still conveys S↔Home. The brief leaves this fidelity call to sign-off; I chose the collapse
because it is the minimal structural change that restores the invariant, and because the
alternative (keeping a step but renaming its anchor away from Home) would require inventing
a new node shape the renderer doesn't have.

## Production-path requirement — how this iteration differs from v1 (carry-forward §1)

The brief's load-bearing v2 requirement: the test must drive the **same** search code
`main()` runs, not a parallel copy. v1 added a second BFS (`search_connections()`) and
tested that; `main()`'s real loop stayed untested.

**This iteration drives `main()` itself.** `tests/test_deep_connections.py` imports the
gramplet module and defines `_Harness(DeepConnectionsGramplet)` that overrides *only* the
GUI surface (`get_active_object`, `set_text`, `render_text`, `update_status`,
`update_progress`, `update_search_info`, `append_text`, `link`, `pause`, the progress/
button widgets) and `pretty_print` (to capture the path `main` hands it). It deliberately
does **not** call `Gramplet.__init__` (no GTK widgets built). `main`, `get_relatives`,
`get_links_from_notes` and `_calculate_path_depth` are the inherited *production*
implementations. So the test runs the real queue/cache/path-construction loop — there is
**no second loop and no extracted seam to drift from**. This is a stronger satisfaction of
the production-path rule than the brief's suggested "invert into a shared generator"
mechanism (which the brief explicitly leaves to my choice, §3.3): driving `main()` directly
means production and test are the *same* object code, so drift is impossible.

`main()` wraps the search in a broad `try/except Exception` (`:470-476`) that would
silently swallow a fix-induced error in production. The harness drives `main()` **outside**
any such masking and asserts a path is produced (`assertTrue(captured_paths)`) and has the
expected shape, so an `AttributeError`/`TypeError` from the fix fails the test instead of
hiding (brief.md "Surface exceptions" requirement).

## Genuine red (C2) — behavioural, not missing-module (carry-forward §2)

v1's C4 red was a vacuous `ImportError` (the new `connection_search.py` was removed in the
red pass). I analysed `run-verify.sh` (`engine/scripts/ubuntu/run-verify.sh:130-133`): the
red pass `git checkout`s **modified** prod files back to buggy and `rm`s **added** prod
files, keeping the test. So a *new* GUI-free module the test imports is always absent in
red → vacuous. The only buggy code that survives the red revert (as buggy) is the
**modified** `DeepConnectionsGramplet.py`. Therefore genuine behavioural red *requires* the
test to exercise the search through that file.

So the patch keeps the search where it is (a modification, not a new module) and the test
imports the gramplet module and drives `main()`. The C4 run confirms a **behavioural** red:

```
red check (production change reverted, test kept):
  steps=[('child','S'),('sibling','D'),('self','D')]   ← Home D named mid-path
  AssertionError: 'D' unexpectedly found in ['S','D']
green check (fix applied):
  OK
C4-verify: green-with-fix=PASS / red-without-fix=PASS   (both 6.0 and 6.1 legs)
```

The red message is the reporter's exact symptom, produced by the real `main()` loop — not a
missing import.

## Importing the Gtk-bound module — why it's safe here (and why it's unavoidable)

The brief warns against importing a GUI module at load time because it core-dumps the
*headless* runner. That warning is about the **core** C4 leg (plain `python3`, no display).
This is an **addon** fix: `run-verify.sh:113-114` runs the addon legs under `xvfb-run` with
the GI-version bootstrap (`engine/scripts/lib/gi_bootstrap/sitecustomize.py`), which exists
precisely so addon tests can import `gramps.gui`/Gtk under a bare display. I verified
empirically that `import DeepConnectionsGramplet.DeepConnectionsGramplet` (eager
`from gi.repository import Gtk, GLib`, `:29`) loads cleanly in that image under xvfb, and
the green+red C4 runs confirm it (no segfault on either leg). The existing
`SurnameMappingGramplet/tests/test_surnamemappinggramplet_imports.py` uses the same
"import the Gtk-bound addon module under the addon test runner" pattern, so this is an
established convention here. The harness never *constructs* a display-bound widget (it skips
`Gramplet.__init__`), so no D-Bus/AT-SPI is touched.

Given the run-verify red mechanism above, importing the gramplet module is not just safe but
**necessary** for a genuine behavioural red — a separate GUI-free module would re-introduce
v1's vacuous-import red.

## Test fixture

`_nibling_db()` builds the brief's repro (brief.md:17): Home **D** and sibling **S** share a
parent family; **S** has child **A** (active). A connects to Home as "child of D's sibling".
The multi-hop test asserts: S *is* present as an intermediate anchor (guard against a
vacuous pass — the path genuinely routes through S), D is *not* in the intermediate anchors,
the path still terminates at D as its `"self"` root, and D appears exactly once. A second
test covers the direct-relative case (active = S, Home's sibling): Home only at root.

## Files / scope / hygiene

- `DeepConnectionsGramplet/DeepConnectionsGramplet.py` — modified (get_relatives signature +
  exclusion tail; one-line `main()` call-site change).
- `DeepConnectionsGramplet/tests/__init__.py` — new, empty (matches the addon convention;
  other addons' `tests/__init__.py` are 0-byte). It carries no diff hunk, so run-verify does
  not classify/remove it; it stays applied in both passes, keeping the dotted import stable.
- `DeepConnectionsGramplet/tests/test_deep_connections.py` — new; GPL header, no diagnostic
  `print()`.
- Out of scope, untouched (brief.md:16): the parent→child-of-spouse conceded case; UI /
  pause-continue / progress / label wording; the pre-existing T1/T2 deviations on
  `DeepConnectionsGramplet.gpr.py` and the folder-vs-id mismatch (files this patch does not
  touch).
- `black` (26.5.0) run over both changed `.py` files: "left unchanged" — commit-ready for the
  target's formatter.

## Cross-version correctness (gramps60 → gramps61)

Addons are cherry-picked forward by the maintainer (INTEGRATION §2). `run-verify.sh` ran the
addon **matrix** — both `addons-source-6.0 × core 6.0` and `addons-source-6.1 × core 6.1` —
and both passed red→green. The gramplet file is the same on gramps61 (brief.md:24), so the
fix remains correct on the forward target, not merely apply-clean.

## Prior art (build-time confirmation, brief.md:24)

`gh pr list --repo gramps-project/addons-source --search DeepConnectionsGramplet --state all`
returns only translations and the 2017 "Gramplet signalling" fix (already in history) — no
PR (open, closed, or merged) addresses the start-person-as-intermediate-step behaviour. No
competing or rejected fix to reconcile with.
