# Check review — issue tmg-os-test-split-gramps61 / addons-source #48

> Advisory, artifact-only, decorrelated from the builder. Inputs: `patch.diff`,
> `brief.md`, `check-gates.json` only (`build-notes.md` withheld). Every basis below
> was re-derived from the artifacts, not copied from the gate row.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | `brief.md` is a complete human-authored plan: explicit success criterion (`brief.md:20-25`), invariant (`:26-36`), scope/out-of-scope (`:41-53`), named gramps60 convergence blobs `4851746a` / `35bd117` (`:47-48`). |
| C2 — C2 Reproduction (red pre-fix) | N/A | No runtime red applies: the brief deliberately authors no fresh regression test (`:60-62`) and the Windows hang cannot be reproduced here (no Gramps 6.1 on conda-forge — issue #32 stays open, `:51-53`). Pre-fix co-location is nonetheless evidenced by the diff minus-lines (pin block `patch.diff:12-25`, `win32` skip `:75-80`, DB classes `:105-1252`). |
| C3 — C3 Change | PASS | Diff performs exactly the scoped move: removes the inline `gi.require_version` block (`patch.diff:12-25`), the `win32` `SkipTest` from `_make_db` (`:75-80`), the DB-backed classes + helpers + imports from `test_libtmg.py`, reducing its import to `from gramps.gen.lib import Date` (`:93`); adds them verbatim to new `test_linux_libtmg.py` (`:1254-2477`). No gramps60 path and no `libtmg` production file touched. |
| C4 — C4 Verification (red→green) | FAIL | Gating gate `C4-verify` (`run-verify.sh`) returned **fail** (`check-gates.json:33-39`). The artifact does not demonstrate the success criterion (both files discovered + green under `CORE_VERSION=6.1`); red→green is not shown. Blocks sign-off. |
| C5 — C5 Causal adequacy | PASS | Root cause (DB tests co-located in an OS-portable file the Windows lane runs) is addressed at the correct layer — relocation into a `test_linux_*` file the lane excludes by convention (`run-addon-unit.sh:235-247`, `brief.md:31`), removing the two runtime stopgaps rather than guarding. Mechanism is proven on gramps60 and the new file is byte-identical to it (blob `35bd117` re-derived below); root cause is documented and uncontested. |
| T1 — T1 Structure | PASS | Addon layout conforms to doc 16 §Structure (`check-gates.json:51-56`); diff adds/edits only files under `TMGimporter/tests/`, no `__init__.py`, folder==id unaffected. |
| T2 — T2 Shape | NEEDS-HUMAN | Gate flags no GPL header in first 40 lines of `test_libtmg.py` (`check-gates.json:64`); confirmed — new file opens with a docstring + imports, no licence header (`patch.diff:1260-1289`). But adding one would break the brief's byte-for-byte parity with gramps60 blobs `4851746a`/`35bd117` (header is absent upstream too) and sits outside scope (`brief.md:53`). Human must adjudicate header-convention vs. verbatim-convergence. |
| T3 — T3 Runtime | NEEDS-HUMAN | Both runtime lanes exited 2 — "runner exited 2 with no parsed failures and no matching baseline signature (a new failure mode)" (`check-gates.json:73,82`). Ambiguous: the gramps60×6.0 lane also fails, yet this patch must not and does not touch gramps60 — smells like a harness/baseline/env break, not a genuine test regression. Human must triage whether the suites actually run before this can be read as a real failure. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle to evaluate (`check-gates.json:91`); the PDCA STOP discipline (`brief.md:87-91`) keeps this draft pre-wrapper. |
| T5 — T5 Judgment | NEEDS-HUMAN | Artifact quality is strong (verbatim relocation, new-file blob match verified, scope respected), but `T5` carries a "reviewer + human sign-off" oracle and two material concerns remain open — gating C4 red and the ambiguous T3 runtime. Judgment cannot be finalized until those clear. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. Whether converging gramps61 onto gramps60's post-split layout actually serves the operator's goal — Windows lane no longer runs/hangs on the DB tests, both files green on Linux against matching 6.1 — is decided by the human at sign-off. |

## §6 — Items the human must clear

1. **(C4, gating) Verification is red.** `run-verify.sh` returned fail; the bundle does not
   show the two files discovered and green under `CORE_VERSION=6.1`. Sign-off is blocked until
   a green red→green verification exists. This is the gating blocker.
2. **(T3) Ambiguous runtime failure mode.** Both T3 lanes exited 2 with no parsed failures and
   no matching baseline signature — including the gramps60×6.0 lane, which this patch neither
   touches nor should affect. Determine whether the runner/baseline/env is broken (most likely,
   given the untouched lane also fails) or whether there is a genuine regression, before C4/T3
   can be re-read. Resolving this likely resolves C4.
3. **(T2) GPL header vs. verbatim gramps60 parity.** The shape gate wants a GPL licence header
   on the touched test files; the brief's success criterion requires byte-for-byte identity with
   gramps60 blobs `4851746a`/`35bd117`, which lack such a header. Decide whether to (a) accept the
   gap as a pre-existing, project-wide concern preserved for parity, or (b) diverge from gramps60
   to add the header (and accept that the named-blob criterion no longer holds).
4. **(T5/V) Fitness sign-off.** Confirm the relocation meets the invariant
   (`brief.md:26-36`) and purpose, accepting that addons-source #32 (Windows real-DB coverage)
   stays open by design.

## Independent verifications performed

- **`test_linux_libtmg.py` (new) is byte-identical to gramps60's merged blob.** Reconstructed the
  1218 added lines from `patch.diff:1259-2477` and computed the git blob hash:
  `35bd117175815c810bb9eac7fb59d95c4e457f10` — matches the diff index `35bd11717` and the brief's
  named blob `35bd117`. The moved classes/helpers are therefore a verbatim relocation, and the
  upstream cosmetic quirk (the "Pure functions: num_to_month…" header sitting above
  `TestShortPlaceName`, `patch.diff:1857-1860`) is faithfully reproduced, not introduced.
- **`test_libtmg.py` (modified) post-image.** Cannot be reconstructed from the diff alone (modify
  against an unverified base), so its parity with gramps60 blob `4851746a` rests on the diff's
  `index 44cab9913..4851746a6` line (`patch.diff:2`), whose abbreviation matches the brief's named
  blob. Verified the deletions remove exactly the pin block, the `win32` skip, the DB classes and
  the surplus imports, leaving `from gramps.gen.lib import Date` — consistent with the named target.
- **Scope.** The diff's only two files are `TMGimporter/tests/test_libtmg.py` and
  `TMGimporter/tests/test_linux_libtmg.py`; no gramps60 path, no `libtmg` production code, no
  `POTFILES` change — consistent with `brief.md:40-53,73-77`.
