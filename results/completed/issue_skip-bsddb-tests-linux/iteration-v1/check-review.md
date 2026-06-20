# Check review — issue skip-bsddb-tests-linux

Advisory, artifact-only review. Inputs: `brief.md`, `patch.diff`,
`check-gates.json`. `build-notes.md` deliberately withheld. Verdicts
are re-derived from those three files alone.

## 1. Summary

The patch generalises the existing Windows-only skip in
`gramps/plugins/test/imports_test.py:245-246` to any platform where the
bsddb backend is not loadable, by introducing a new helper
`gramps/plugins/test/_bsddb_avail.py` that probes for `berkeleydb`
then `bsddb3` (the same order the loader uses, per
`brief.md:11` / `brief.md:17`). Scope is test-harness only; runtime
code paths are untouched. The change is mechanically faithful to the
brief's success criterion and invariant.

The blocking question is **C4**: the configured verify oracle
(`./engine/scripts/ubuntu/run-verify.sh`) could not run because
`docker` is not installed on the gate host
(`check-gates.json:36-37`); the same infra failure cascades into both
T3 runners (exit 127, `check-gates.json:72-83`). None of those
failures are evidence against the patch — they are evidence the
gate-host lacks docker — but they leave the red→green claim
unverified from artifacts alone.

## 2. Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | `brief.md:8-19` carries slug, defect, success criterion, invariant, scope, repro, citations expected, prior-art — all required Plan fields present. Success criterion is testable: "five `test_imp_*_zip` … skip cleanly … on a backend-less Linux box" (`brief.md:10`). Invariant is stated over the category, not the five repro methods (`brief.md:11` SELF-TEST line). |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | No execution log of the pre-fix red run is present in the artifacts (build-notes.md withheld; `check-gates.json:15-21` shows C2 "no gate configured"). Brief asserts reproducibility on Ubuntu 24.02 and on the testbed (`brief.md:9`, `brief.md:15`), but artifact-only review cannot independently confirm the red baseline. |
| C3 — C3 Change | PASS | `patch.diff:1-58` adds `_bsddb_avail.py` with `bsddb_backend_available()` probing `berkeleydb` then `bsddb3` (matches loader probe order per `brief.md:11`,`brief.md:17`). `patch.diff:71-86` replaces the `win()` guard at `gramps/plugins/test/imports_test.py:245` with `not bsddb_backend_available()` and updates the `skipTest` message. Diff touches only the two files named in scope (`brief.md:14`) — no sqlite path, no `while True` upgrade loop, no catch-all rewrite, no `gramps/plugins/db/bsddb/`. |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | `check-gates.json:32-40` records the gating C4 oracle failed with `docker: command not found` (gate-host lacks docker). This is an infra failure, not patch logic; the red→green claim cannot be confirmed or refuted from the artifacts. Needs rerun on a docker-capable host (or substitute runner) using the brief's bundle test `test_imp_5_1_2bsd_zip` (`brief.md:16`). |
| C5 — C5 Causal adequacy | PASS | Brief locates the root cause precisely: the skip predicate is hard-coded to `win()` at `gramps/plugins/test/imports_test.py:245-246`, so backend-less Linux falls through to `make_database("bsddb")` (`brief.md:9`). The patch removes that exact predicate and replaces it with a direct probe of the backend's loadability (`patch.diff:82`), which is the invariant the brief demands (`brief.md:11`). Fix and cause are aligned; not contested. |
| T1 — T1 Structure | N/A | `brief.md:13` declares surface as "data (test harness only)"; doc-16 §Structure governs addons layout, and `check-gates.json:55` confirms no addons-source path appears in `patch.diff`. Core-only change — §Structure does not apply. |
| T2 — T2 Shape | PASS | New file `_bsddb_avail.py` carries GPL header (`patch.diff:7-23`); the helper has a module docstring and a function docstring (`patch.diff:26-37`, `patch.diff:41-45`); no `print()` calls introduced. `check-gates.json:62-64` independently records T2 ✓ for the one touched file. |
| T3 — T3 Runtime | NEEDS-HUMAN | Both T3 gates exited 127 with no parsed failures and no matching baseline signature (`check-gates.json:72-83`). Exit 127 is "command not found" — the same infra deficit that defeated C4 (no docker on the gate host). The baseline runner produced no signal about the patch; needs rerun on docker-capable infra to establish runtime delta. |
| T4 — T4 Contribution | N/A | `check-gates.json:90` records no `commit-msg.txt` or `pr-description.md` in the bundle. Per brief STOP discipline (`brief.md:21-25`), the patch is draft pre-Check-sign-off; commit/PR wrappers are not required yet. §Commit messages + §Contributor workflow cannot be evaluated against an absent artifact. |
| T5 — T5 Judgment | PASS | Patch is minimal and scope-clean. The new helper is private (`_` prefix), placed under `gramps/plugins/test/` next to its sole caller, and documents its mirroring of `bsddb.py:32-35` inline (`patch.diff:42-44`). The skipTest message names both backends (`patch.diff:84-85`), so the failure mode is self-describing. Reuses the existing `SkipTest` plumbing from `29a0bedaa0` (per `brief.md:12`) without re-architecting the catch-all block. No drive-by edits. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human at sign-off (`check-gates.json:107`). The Check reviewer cannot certify that "skip-not-fail when backend missing on every platform" is the user-facing outcome the project wants beyond the brief's framing. |

## 3. Notes on the change itself

- **Probe order matches the loader.** The helper tries `berkeleydb`
  then `bsddb3` (`patch.diff:46-58`). The brief states this is the
  loader's order at `gramps/plugins/db/bsddb/bsddb.py:32-35`
  (`brief.md:11`); the patch comment cites the same line range
  (`patch.diff:42-44`). Re-derivation could not check the loader
  source directly (not in the artifact bundle); on trust of the brief,
  the orders align.
- **Predicate semantics.** Old: `dbid == "bsddb" and win()`; new:
  `dbid == "bsddb" and not bsddb_backend_available()`. On a backend-less
  Linux host the new predicate is true and the test skips — the
  success criterion (`brief.md:10`). On any host with either backend
  installed, the new predicate is false and the test runs as before —
  the out-of-scope clause (`brief.md:14`) is preserved. On Windows
  with no backend, behaviour is unchanged (still skips). On the
  (unusual) Windows host with a working backend, behaviour does
  change: the test would now run rather than skip — this is the
  generalisation the brief asks for (`brief.md:11-12`), not a regression.
- **Exception coverage.** `bsddb_backend_available()` only catches
  `ImportError`. If `berkeleydb` were importable but its module
  initialisation raised something else, the helper would propagate
  rather than skip. The brief does not require coverage of that case,
  and the loader at `bsddb.py:32-35` is described as using the same
  `try/except ImportError` shape, so this matches the loader's
  tolerance level.

## 4. What I could not check from artifacts

- The actual contents of `gramps/plugins/db/bsddb/bsddb.py:32-35` — to
  confirm probe order independently (not in bundle).
- The actual pre-fix and post-fix test runs — `check-gates.json`
  surfaces only the gate runner's docker-missing failure, not a real
  red or green log.
- Whether `from gramps.plugins.test._bsddb_avail import …` resolves at
  import time inside the test runner's working directory (the brief
  uses `GRAMPS_RESOURCES=.` and `python3 -m unittest`, so package
  discovery should work, but unverified).

## 5. Recommendation

**Provisional PASS on logic, BLOCKED on verification.** The change is
correct in form and scope as far as artifact-only reading can
establish. Sign-off must wait until C4 (red→green) and T3 (runtime
deltas) can be re-run on infrastructure where `docker` is present —
the current failures in `check-gates.json` are gate-host deficits,
not patch defects, but they leave the success criterion empirically
unconfirmed.

## 6. Items the human must clear

1. **C2 reproduction red pre-fix** — confirm the five `test_imp_*_zip`
   tests fail with `AssertionError … can't load database backend:
   'bsddb'` on a checkout of `upstream/maintenance/gramps61` with
   neither `berkeleydb` nor `bsddb3` installed, before the patch is
   applied. (`brief.md:15` describes the exact command.) The
   artifact bundle carries no such log.
2. **C4 verify red→green** — rerun
   `./engine/scripts/ubuntu/run-verify.sh` on a docker-capable host
   (or substitute equivalent runner) so the gating oracle can produce
   a real verdict. The bundle test is `test_imp_5_1_2bsd_zip`
   (`brief.md:16`); pre-fix must fail with the bsddb-backend message,
   post-fix must skip.
3. **T3 runtime** — rerun
   `./engine/conformance/t3_baseline.py ./engine/scripts/ubuntu/run-unit.sh`
   and the interface variant on a docker-capable host so the baseline
   delta is meaningful (current `exit 127` results contain no signal).
4. **V validation fitness-to-purpose** — human confirmation that
   "skip-not-fail on any platform where the bsddb backend is missing"
   is the desired user-facing behaviour (and that flipping the
   Windows-with-backend case from skip to run is acceptable, since
   the brief's generalisation implies it).
5. **Probe-order cross-check** — verify directly that
   `gramps/plugins/db/bsddb/bsddb.py:32-35` does in fact try
   `berkeleydb` then `bsddb3` in that order; the patch and brief
   agree on this, but neither artifact source-checks the loader.
