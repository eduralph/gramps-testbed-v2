# Deep Connections: do not name the Home person as an intermediate step

Fixes Gramps bug #8653 (https://gramps-project.org/bugs/view.php?id=8653).

## Root cause
`get_relatives()` anchors every returned relative's new path node at the person
currently being expanded, and the Home/start person is the first node expanded
(the `("self", …)` root the search seeds into its queue). So each of Home's own
relatives gains an intermediate step anchored at Home, which then renders below
the root as "… / sibling of \<Home\> / …" — the Home person named mid-path as
well as at its root (the reporter's first, "definitely a bug" case). The
visited-cache prevents re-*expanding* Home but not this re-*naming*, which is
why the symptom is still present on `maintenance/gramps60`.

## Fix
`get_relatives()` takes the Home person's handle as a value passed in by its
caller and, once that handle is supplied, keeps the Home person out of the body
of every produced path: it drops any relative that *is* the Home person, and
when the Home person is the node being expanded it attaches that person's
relatives directly to the root node instead of through a redundant
`(relation, Home)` step. The Home person is therefore recorded only as the
path's terminal `"self"` root; the path still connects the active person to
Home, and the renderer and the rest of the breadth-first loop are untouched.
The handle is read by `main()` only after its existing "No Home Person set"
early-return guard and is never re-dereferenced inside `get_relatives()`, so the
no-Home-person case still returns early with no regression.

## Verified against
- `DeepConnectionsGramplet/DeepConnectionsGramplet.py:352-358` — the search
  seeds its queue with the Home person as the `("self", …)` root, confirming
  Home is the origin and is expanded first.
- `DeepConnectionsGramplet/DeepConnectionsGramplet.py:221-282` — `get_relatives()`
  builds each relative's path node anchored at the expanded person; this is the
  single place an anchor is created and where the exclusion is applied.
- `DeepConnectionsGramplet/DeepConnectionsGramplet.py:334-338` and `:439` — the
  "No Home Person set" guard returns early, and `get_relatives()` is called only
  here, after that guard, so the Home handle passed in is always non-`None`.
- `DeepConnectionsGramplet/DeepConnectionsGramplet.py:435-438` — the visited
  cache blocks re-expanding Home but not its re-naming, so the bug survives the
  cache.
- `DeepConnectionsGramplet/DeepConnectionsGramplet.py:287-316` — `pretty_print`
  renders the produced path and is left unchanged.
- `DeepConnectionsGramplet.gpr.py` declares `gramps_target_version="6.0"`, and
  the gramplet file is byte-identical to `upstream/maintenance/gramps60`; the
  same file carries forward to `gramps61` unchanged, so the fix is correct on
  the maintainer's cherry-pick target, not merely apply-clean.

## Test
`DeepConnectionsGramplet/tests/test_deep_connections.py` — a regression test that
drives the production `DeepConnectionsGramplet.main()` search itself (a harness
subclass overrides only the GUI surface and skips `Gramplet.__init__`; `main`,
`get_relatives` and the path-construction loop are the inherited production
code), so it exercises the same code path the gramplet runs, not a copy.

Using the reporter's scenario (Home `D`, sibling `S`, and `S`'s child `A` as the
active person), the test asserts the produced path routes through the
intermediate relative `S`, does **not** name the Home person `D` as an
intermediate anchor, still terminates at `D` as its `"self"` root, and names `D`
exactly once. A second test covers the direct-relative case (active = Home's
sibling). Pre-fix the path is `[('child', S), ('sibling', D), ('self', D)]` —
`D` appears mid-path — and the assertion fails; post-fix it passes. Verified
red→green on the addon version matrix (addons-source 6.0 × core 6.0 and
addons-source 6.1 × core 6.1) under `xvfb`.
