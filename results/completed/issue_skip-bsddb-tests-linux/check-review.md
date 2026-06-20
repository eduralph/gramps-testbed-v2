# Check Review — skip-bsddb-import-tests-when-backend-unavailable

Advisory, artifact-only review. Inputs seen: `patch.diff`, `brief.md`,
`check-gates.json`. `build-notes.md` deliberately withheld; verdicts below are
re-derived from the diff and the brief, not from the builder's narration.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | Brief states a single load-bearing success criterion (`brief.md:10`): backend-less Linux must skip the five `test_imp_*_zip` tests, with-backend behaviour unchanged. It is concrete and testable; the invariant (`brief.md:11`) is stated over the right category ("a backend-dependent test on any platform"), not the five repro methods. |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | No reproduction gate configured (`check-gates.json:15-21`, result `none`), build-notes withheld, and the only red→green gate (C4) never executed (docker socket denied). The brief *describes* a clean repro (`brief.md:15`) but I cannot confirm from artifacts that the pre-fix FAIL was actually observed this iteration. |
| C3 — C3 Change | PASS | Diff replaces the `win()`-only skip with `not bsddb_backend_available()` (`imports_test.py` hunk `@@ -241,9 +251,15`, new skip at ~`:256-261`) and adds prober `_bsddb_avail.py:38-59` that tries `berkeleydb` then `bsddb3` — exactly the loader's probe order cited in the brief (`gramps/plugins/db/bsddb/bsddb.py:32-35`). Change is minimal, on-scope, touches only the test harness. |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | Gating gate failed not on patch logic but on infra: `permission denied … docker.sock` (`check-gates.json:33-39`). Red→green for `test_imp_5_1_2bsd_zip` is empirically unconfirmed; the with-backend-installed half of the criterion can only be checked on the dockerised oracle. A human must re-run on a docker-capable host with socket access. |
| C5 — C5 Causal adequacy | PASS | Root cause per brief: skip gated on `win()` only, so backend-less Linux falls through to `make_database("bsddb")` which raises (`brief.md:9`). The fix removes the OS proxy and tests the *actual* loadability condition, generalising the existing Windows special-case rather than papering over it. Root cause is uncontested and the fix attacks it directly. |
| T1 — T1 Structure | N/A | Core test-harness change only; no addons-source path in the diff. §Structure (folder==id, target_version, fname, no `__init__.py`) is addon-only and does not apply. Matches gate (`check-gates.json:55`). |
| T2 — T2 Shape | PASS | New file `_bsddb_avail.py` carries the full GPL header (`patch.diff:7-23`); edited file unchanged in header. No stray `print()`. Conforms to doc 16 §Coding style; agrees with gate (`check-gates.json:64`). |
| T3 — T3 Runtime | NEEDS-HUMAN | Both runtime baselines failed as infra non-signal: "runner exited 1/127 with no parsed failures and no matching baseline signature" (`check-gates.json:73,82`) — the same docker deficit, advisory not gating. No regression *and* no clean delta can be asserted from artifacts; needs a working runner to clear. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle (`check-gates.json:91`), so §Commit messages / §Contributor workflow have nothing to grade. Consistent with the brief's STOP discipline (draft-only until sign-off). |
| T5 — T5 Judgment | PASS | Change is well-scoped and self-consistent: prober mirrors the cited loader contract, the `except ImportError` fallback returns `True` (fail-open: don't mask a real backend error), and out-of-scope surfaces (sqlite path, `while True` loop, catch-all block, `db/bsddb/`) are untouched per `brief.md:14`. Broad `except Exception` in the prober is acceptable — it matches the loader's own tolerance. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. Whether flipping five FAILs to skips genuinely satisfies the maintainers' intent (vs. e.g. expecting the tests to actually run under a provided backend in CI) is a judgment the artifacts cannot settle. |

## §6 — Items the human must clear (each NEEDS-HUMAN row)

1. **C2 Reproduction** — Confirm the pre-fix red was actually observed this
   iteration (no repro gate ran; build-notes withheld). Re-run
   `GRAMPS_RESOURCES=. python3 -m unittest gramps.plugins.test.imports_test` on a
   backend-less checkout of `upstream/maintenance/gramps61` and confirm
   `FAILED (failures=5, …)` before the patch.
2. **C4 Verification (red→green)** — The gating C4 gate failed on
   `permission denied … docker.sock`, not on patch logic. Re-run
   `./engine/scripts/ubuntu/run-verify.sh` for bundle `test_imp_5_1_2bsd_zip` on a
   host where the invoking user can reach the docker socket; require pre-fix FAIL
   (`can't load database backend: 'bsddb'`) → post-fix `skipped`. This is the only
   gate that also covers the **with-backend-installed** half of the success
   criterion (no regression on the real-import path).
3. **T3 Runtime** — Both runtime baselines returned infra non-signal (exit 1/127).
   Re-run `run-unit.sh` and `run-interface.sh` through `t3_baseline.py` on working
   infra and confirm a clean (empty) delta against baseline.
4. **Validation — fitness-to-purpose** — Human sign-off that skip-not-fail is the
   intended resolution for the maintainers, and that scope (test-harness only,
   forward-merge to `master`) is what was wanted.

## Note on disposition

The patch logic is sound and on-scope (C1/C3/C5/T2/T5 PASS; T1/T4 N/A). Every open
item is a **gate-host deficit** — the docker socket was unreachable this iteration
exactly as in iteration 1 (`brief.md:28-31`) — not a defect in the change. The
verdict cannot rise above NEEDS-HUMAN until the red→green and runtime gates fire on
infra with docker socket access.
