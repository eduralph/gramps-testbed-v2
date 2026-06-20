# Brief — issue 8653 / deep-connections-excludes-start-person

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.
> **This is iteration 2.** Iteration 1 is archived in `iteration-v1/`; read the
> "What changed since iteration 1" section at the bottom before you build.

- **Slug:** deep-connections-excludes-start-person
- **Defect:** The **Deep Connections Gramplet** reports connection paths that name the Home/start person as an *intermediate relationship anchor* — e.g. "Main person / sibling of another person / **sibling of main person** / …" — so the search origin appears *inside* a path's relationship steps instead of only as its terminal root. (Mantis 8653, status `confirmed`; reporter calls the first case "definitely a bug" and concedes the parent → child-of-spouse case is "probably harder to avoid".) **Confirmed reproducible on current gramps60 in iteration 1** — the 2024 "Updated DeepConnectionsGramplet" commit rebuilt only the UI; the search algorithm is unchanged, so this is NOT POSSIBLY-FIXED.
- **Success criterion:** For the active person, the connection path(s) the gramplet produces **in production** (the search driven by `DeepConnectionsGramplet.main()`) contain the Home/start person **only** as the path's terminal `"self"` root — no produced path names the Home person as an intermediate relationship step/anchor — and each path still connects the active person to the Home person (the chain is not broken). The regression test demonstrates this by driving the **same search code `main()` runs** (see Test file), not a copy of it.
- **Invariant to restore:** In a connection search rooted at the Home person, the Home person is the search *origin* and may appear in a produced path **only as that root**; it must never be re-entered as, nor named as the anchor of, an intermediate relationship step. (Gramps-internal behavioural correctness property — the search's own semantics: the root is the origin, every interior step names how some *other* person connects toward it. No external canon; rationale stated per `docs/principles.md` §7. This is a **behavioural** defect — `docs/principles.md` §1.1 — so it draws no §6 catalogue invariant; the *structural extraction* the fix needs for testability is governed by the production-path rule §3.4, not by minimal-diff §1.2.) SELF-TEST: the property is quantified over *every produced path*, not the repro tree, and cannot be satisfied by a no-op single-module guard.
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60
  (branched from `upstream/maintenance/gramps60`; addons production, the maintainer cherry-picks forward to gramps61. `DeepConnectionsGramplet.gpr.py` declares `gramps_target_version="6.0"`; the working-tree `DeepConnectionsGramplet.py` is byte-identical to `upstream/maintenance/gramps60`, so the `path:line` citations below are valid for the target branch. INTEGRATION §2.)
- **Surfaces:** `data` — the defect and the fix live in the search / path-construction logic, verified at the logic level; no E2E-through-the-app gate is required. (The host is a GUI gramplet, but rendering is untouched — see out of scope.)
- **Scope:** Remove the defect whereby a produced connection path names the Home/start person as an *intermediate relationship anchor*, so the Home person is recorded only as the path root. Orientation (where the paths are produced — NOT a prescribed fix shape): the breadth-first connection search in `DeepConnectionsGramplet.main()` seeds the queue with the Home person as the `"self"` root (`DeepConnectionsGramplet.py:352-358`), expands each node via `get_relatives` (`:221-279`, called at `:439`), and renders the found path with `pretty_print` (`:287-316`). / **out of scope:** the parent → child-of-spouse chains the reporter conceded are "probably harder to avoid"; any change to the gramplet UI / pause-continue / progress / relationship-label wording; the pre-existing addon-structure deviations T1/T2 flag on files this fix does not touch (folder-name vs `.gpr.py` id `Deep Connections Gramplet`; missing GPL header in `DeepConnectionsGramplet.gpr.py`); and **any change that lets the Home handle be dereferenced before `main()`'s existing "No Home Person set" guard** (`:334-338`) — the no-Home-person case MUST keep returning early, no regression (iteration-1 risk T5-b).
- **Repro instruction:** fixture `example.gramps`. Add the Deep Connections Gramplet; set a Home person and an Active person connected such that the active person reaches Home through one of Home's *direct* relatives — e.g. active = child of Home's sibling (a "nibling"); Run. Observe a produced path that names the Home person as an intermediate step ("… sibling of <Home>") immediately before its root. Iteration 1 reproduced this headlessly: for Home **D** with sibling **S** (shared parent family) and S's child **A** (active), the first path is `[('child', S), ('sibling', D), ('self', D)]` — D (Home) appears as the non-root `('sibling', D)` anchor. **Repro confirmed; symptom present on gramps60.**
- **Test file:** `DeepConnectionsGramplet/tests/test_deep_connections.py` — addon convention: a `tests/` (plural) package, file `test_*.py` *prefix*, loaded by the C4 gate via the dotted path `DeepConnectionsGramplet.tests.test_deep_connections` under `xvfb-run` (`./engine/scripts/ubuntu/run-verify.sh`; INTEGRATION §3).
  - **PRODUCTION-PATH REQUIREMENT (principles §3.4 — the load-bearing fix for this iteration):** the test MUST drive the **same** connection-search / path-construction code that `DeepConnectionsGramplet.main()` runs in production. Production must route through whatever unit the test drives; the test MUST NOT validate a *parallel re-implementation* of the BFS loop. (Iteration 1 failed exactly here — it added a second BFS, `search_connections()`, that mirrored `main()`'s loop and tested that copy; `main()`'s real loop stayed untested. **Do not repeat this.**) Stated as an outcome, not a mechanism: if the search is extracted into a GUI-free seam so the test can reach it without a full Gramplet/GTK context, then `main()` must **call that seam** (it must stop carrying its own copy of the loop) and the test drives the same seam with a small in-memory DB.
  - **GENUINE RED (C2):** the test must fail on the **pre-fix behaviour** (Home named as an intermediate step), not merely error because a new module is absent. Iteration-1's C4 red was a missing-module `ImportError`, and behavioural red had to be hand-verified — that is not acceptable evidence here. Design the seam so reverting the *behavioural* change yields a behavioural assertion failure on the production path.
  - **Surface exceptions, don't let production mask them.** `main()` wraps the whole search in a broad `try/except Exception` (`:470-476`) that swallows any error and shows a generic "Error during search" — so an exception in the fix would *silently produce no result* in production rather than crash. Because the test drives the seam **outside** that handler, it MUST assert the search runs to completion and returns the expected path, so an `AttributeError`/`TypeError`/structural error from the fix fails the test instead of hiding behind the `except`.
  - Red pre-fix, green post-fix.
- **Citations expected:** Do must cite `path:line` on `maintenance/gramps60` for every change — the production search now routing through the shared seam, the behavioural exclusion itself, and any extracted unit.
- **Prior-art check (triage cycles):** searched **by file path**. Merged history — `git -C ../addons-source log upstream/maintenance/gramps60 -- DeepConnectionsGramplet/`: **no fix for this behaviour**. The non-translation/non-merge commits are the 2024 UI rewrite (`2a3c924f0`, search algorithm unchanged), a *different* "fix exception when 'Copy' is used with no home person" (`6edea4365`), FSF-address / signalling / autopep8 / initial SVN import. `upstream/maintenance/gramps61` carries the same history (no extra fix); no open fix by path. **Do must confirm closed/rejected PRs across `gramps-project/*` by the file path at build time** (INTEGRATION §5).
- **Disposition hint:** likely-fix. Repro confirmed in iteration 1 (refutes the "already fixed by the visited-cache" hypothesis — the cache blocks re-*expanding* Home, not Home being named as a root-adjacent anchor). This is **iteration 2**: do NOT re-attempt the v1 parallel-copy shape; satisfy the production-path requirement above.

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.

## What changed since iteration 1 (carry-forward — Do reads this)

Iteration 1's fix was *behaviourally* close (the reviewer's independent trace
confirmed red→green and refuted "already fixed"), but it was **iterated, not
accepted**, for these reasons. Address them; the full prior attempt is preserved in
`iteration-v1/` (patch, build-notes, check-review, check-gates).

1. **Test validated a copy of production, not production (principles §3.4 — primary).**
   v1 extracted only `get_relatives`/`get_links_from_notes` into a new module and then
   wrote a *second* BFS, `search_connections()`, that paralleled `main()`'s loop — the
   test drove that copy. `main()` kept its own loop, so loop-level drift would go
   uncaught. **v2 requirement:** one shared search code path that `main()` and the test
   both run (see Test file → PRODUCTION-PATH REQUIREMENT). The carry-forward's named
   *possibility* — inverting `main()` into a shared generator the GUI consumes and the
   test consumes — is one mechanism; the choice is yours (§3.3), the **outcome** is
   fixed.
2. **Vacuous C4 red.** v1's red came from removing the new module (`ImportError`), not
   from the buggy behaviour. v2's test must go red on the *behaviour* on the production
   path (see GENUINE RED).
3. **`default_person is None` regression risk (T5-b — the known exception risk).** v1
   introduced a hard `self.default_person.handle` dependency inside `get_relatives`,
   which raises `AttributeError` if no Home person is set. `main()` already returns early
   when no Home person is set (`:334-338`), and `get_relatives` is called **only** from
   `main()` at `:439` — *after* that guard. So the fix MUST take the Home handle as a
   value passed in by that post-guard caller; it must not re-fetch / re-dereference
   `default_person` on a path that can run before the guard. Done that way, the
   None-deref cannot occur in production.
4. **Label-fidelity is a sign-off (C5/V) judgment, not prescribed here.** Whether a
   *direct* relative of Home keeps an explicit "… of <Home>" label or is shown relative
   to the root is for the human to weigh at sign-off; the brief requires only that Home
   not appear as an intermediate step and that the path still connects active→Home. Do
   should state, in build-notes, what its chosen shape does to the rendered label so the
   human can judge it.
5. **Pre-existing T1/T2 fails are out of scope** (folder-name vs `.gpr.py` id; missing
   GPL header in `DeepConnectionsGramplet.gpr.py`) — files this fix does not touch. New
   files the patch adds MUST carry the GPL header and no diagnostic `print()`.
