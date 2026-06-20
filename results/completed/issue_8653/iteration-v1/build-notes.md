# Build notes — issue 8653 / deep-connections-excludes-start-person

Target branch: `addons-source` @ `upstream/maintenance/gramps60`
(HEAD `771db58`; the working-tree `DeepConnectionsGramplet.py` is byte-identical
to that branch — `git diff --stat upstream/maintenance/gramps60` is empty — so the
`path:line` citations below are valid for the target branch).

## 1. Repro established first (per the disposition hint)

The brief warned the gramplet was rewritten since the 2015 report and the BFS now
caches visited handles, so the symptom might already be gone. I checked the
algorithm's provenance before touching anything:

- `git log --all -- DeepConnectionsGramplet/DeepConnectionsGramplet.py` shows the
  2024 "Updated DeepConnectionsGramplet" commit (`2a3c924f0`) only rebuilt the
  **UI**. Diffing the pre-rewrite `get_relatives`/`main`/`pretty_print`
  (`6edea4365`) against the current file: the search algorithm — queue seed, the
  `self.cache` visited-set, `get_relatives`, `pretty_print` — is **unchanged**.
  The cache existed in 2015 too. So whatever the 2015 reporter saw is still present.
- No merged or open upstream fix by path:
  `git log upstream/maintenance/gramps60 -- DeepConnectionsGramplet/` and the
  gramps61 branch carry only translation/UI commits.

I then reproduced the exact symptom by running a faithful, GUI-free port of the
search over a tiny in-memory tree (`/tmp/scratch_search.py`). Scenario: Home person
**D** and sibling **S** are children of one family; **S** has a child **A** (the
active person). The first path the BFS returns for A is:

```
[('child', 'S'), ('sibling', 'D'), ('self', 'D')]
```

`D` (Home) appears as a **non-root** step `('sibling', 'D')` — rendered by
`pretty_print` as "... sibling of <Home person>". That is precisely the reporter's
"Main person / sibling of another person / sibling of main person" — the start
person inside the path rather than only as its root. **Symptom confirmed; not
POSSIBLY-FIXED.**

### Why it happens (root cause, two sentences)

The queue is seeded with the Home person as the `"self"` root and
`get_relatives` tags every relative with a step `(path, (relation, person_handle))`
whose anchor is the *expanded* node (`DeepConnectionsGramplet.py:221-279`,
seed at `:353-358`). The Home person is expanded first (BFS root), so its direct
relatives carry a `(relation, Home)` step; the `self.cache` guard (`:435-438`)
only stops Home from being *re-processed*, not from being recorded as that
root-adjacent anchor — so every multi-hop path ends "... <rel> of <Home>", naming
the search origin as a path step.

## 2. The fix

Two rules, applied where the brief scoped them (the BFS / `get_relatives`), so the
Home person is recorded only as the implicit root:

1. **Never re-enter Home as an intermediate node** — drop any relative whose handle
   is the start person from `get_relatives`' results.
2. **Collapse Home's own relatives onto the root** — when expanding the start
   person, link its relatives straight to the incoming root `path` instead of
   through a redundant `(relation, Home)` step.

Post-fix the same scenario yields `[('child', 'S'), ('self', 'D')]` — Home only at
the root. No information is lost: `pretty_print` already annotates each printed
step with that person's relationship-to-Home from the relationship calculator
(`DeepConnectionsGramplet.py:310-314`), so "child of S **[sister]**" still tells the
reader S is Home's sibling.

Explicitly **out of scope** (per brief): the parent → child-of-spouse chains the
reporter conceded are "probably harder to avoid", and all UI / pause-continue /
label wording.

## 3. Files changed (cited against `maintenance/gramps60`)

- **New `DeepConnectionsGramplet/connection_search.py`** — a GUI-free module (no
  `gi` / `gramps.gui` / `gramps.gen` import). Holds a verbatim port of
  `get_links_from_notes` (was `DeepConnectionsGramplet.py:204-219`) and
  `get_relatives` (was `:221-279`), with the issue-8653 exclusion added as an
  explicit post-process at the end of `get_relatives` (so `start_handle=None`
  reproduces the original behaviour exactly and the diff stays reviewable). Also
  adds `search_connections` (a headless mirror of the `main()` BFS loop,
  `:384-453`, minus the Gtk progress/pause/`yield` plumbing) and a `path_steps`
  helper for assertions.
- **`DeepConnectionsGramplet/DeepConnectionsGramplet.py`**
  - `import connection_search` added after the GRAMPS imports (after `:40`).
  - `get_links_from_notes` (`:204-219`) and `get_relatives` (`:221-279`) replaced
    by thin delegators to the module; `get_relatives` passes
    `start_handle=self.default_person.handle` (set at the top of `main()`,
    `:331`, before any call). `main()`'s loop is otherwise untouched and now
    benefits from the fixed `get_relatives` it already calls at `:439`.
- **New `DeepConnectionsGramplet/tests/__init__.py`** (empty; addon `tests/`
  package marker, per INTEGRATION §3).
- **New `DeepConnectionsGramplet/tests/test_deep_connections.py`** — the named
  test.

## 4. The test

`DeepConnectionsGramplet/tests/test_deep_connections.py` loads **only**
`connection_search.py` by file path via `importlib` (the established repo pattern,
cf. `LinesOfDescendency/tests/test_linesofdescendency_guards.py`) — it never
imports the Gtk-bound gramplet module, so it runs under a plain
`python3 -m unittest` with no display / D-Bus / AT-SPI. It builds the nibling tree
in memory and asserts, on the first connection path A↔Home:

- it genuinely routes through the intermediate `S` (guards against a vacuous pass),
- Home (`D`) is **not** among the non-root step handles (the bug), and
- Home is still present **exactly once**, as the `"self"` root.
A third case checks a direct sibling of Home still connects with Home only at root.

## 5. Verification (red → green)

- **Green with fix** — applied `patch.diff` to a clean checkout,
  `python3 -m unittest DeepConnectionsGramplet.tests.test_deep_connections` → `OK`
  (3 tests).
- **Red without fix (gate's exact sequence)** — reverted
  `DeepConnectionsGramplet.py` and removed `connection_search.py` (PROD_MOD /
  PROD_NEW as `run-verify.sh` classifies them), kept the test → the test errors
  (`FileNotFoundError` on the absent fix module) → non-green = red. So the C4
  contract holds: green-with-fix ∧ red-without-fix.
- **Behavioural red (faithfulness)** — because the extracted module is a *new*
  file, the gate's red is module-absence rather than the buggy code path. To prove
  the test actually catches the *behaviour*, I monkey-patched `get_relatives` back
  to its pre-fix form (`start_handle=None`) and re-ran the suite
  (`/tmp/check_red.py`): all three tests fail with
  `path=[('child','S'),('sibling','D'),('self','D')]` — i.e. they fail on the
  assertion, against the genuine pre-fix output, not on an import error.

### Note on running the Docker C4 gate here

`./engine/scripts/ubuntu/run-verify.sh` (the authoritative C4 gate) requires
Docker + unsandboxed git/filesystem access, which is gated behind human approval in
this environment, so I could not execute it directly. I instead reproduced its
**exact** red/green steps by hand (§5 above): the gate ultimately runs
`python3 -m unittest <MODULE>` on the addons-source checkout, and since this test
imports no `gi`/`gramps` it needs neither the gramps install nor xvfb the gate
otherwise provides — so the manual run is equivalent. The patch's file
classification was confirmed against `run-verify.sh`'s logic: MODE=addon,
TEST=`tests/test_deep_connections.py`, PROD_MOD=`DeepConnectionsGramplet.py`,
PROD_NEW=`connection_search.py`. **Recommend the human re-run the Docker gate at
sign-off.**

## 6. Alternatives considered / ruled out

- **Suppress the Home step only in `pretty_print`** (display-side). Rejected: the
  brief scopes the fix to the *search* ("exclude … from being traversed/re-entered
  … so it cannot appear mid-path"), and a display-only change leaves Home's handle
  in the path data (so the data-level regression test could not go red→green
  without importing the Gtk-bound renderer).
- **Only filter Home out of `get_relatives` results, leave the seed alone.**
  Rejected as insufficient: the `self.cache` guard already discards re-enqueued
  Home, so that filter alone changes no produced path — the visible bug is the
  root-adjacent `(relation, Home)` anchor, which needs the collapse rule.
- **Make `DeepConnectionsGramplet.py` importable headless (guard the `gi` import)
  and test the gramplet directly.** Rejected: the brief forbids importing the
  Gtk-bound tool module in the C4 test; the GUI-free seam is the prescribed shape.
