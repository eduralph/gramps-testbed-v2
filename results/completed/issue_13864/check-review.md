# Check Review — issue 13864 / dashboard-column-count-crash-locks-tree
## Iteration 2

**Reviewer role:** advisory, artifact-only, decorrelated from the builder.
**Inputs read:** `brief.md`, `check-gates.json`, `patch.diff`. `build-notes.md` withheld by design.
**Overall verdict: REVISE — do not advance to sign-off.**

Two required carry-forward items (C2/C4 test artifacts) are absent from the patch bundle. Production code is sound; the verification scaffolding is not.

---

## §1 Verdict Table

| Item | Verdict | Basis |
|---|---|---|
| C1 — Spec | PASS | `brief.md` is present, well-formed, carries success criterion, invariant, scope, and repro instruction; defect matches Mantis 13864 |
| C2 — Reproduction (red pre-fix) | FAIL | No test is present in `patch.diff`; no PDCA-UNVERIFIABLE annotation; gramps-testbed interface test (`tests/interface/test_bug_13864_dashboard_columns.py`) required by `brief.md:17` and the iteration-1 carry-forward (`brief.md:31`) is absent |
| C3 — Change | PASS | `grampletpane.py` adds `MAX_GRAMPLET_COLUMNS=100` and `clamp_column_count()`, then applies it at all three column-count intake points: constructor kwarg (line 1046), ini load (line 1226), and `set_columns` (line 1415); scope is minimal and targeted |
| C4 — Verification (red→green) | FAIL | Gate reports `unverifiable`; `brief.md:17` protocol requires either a headless `*_test.py` or a PDCA-UNVERIFIABLE flag plus gramps-testbed interface test; patch ships neither |
| C5 — Causal adequacy | PASS | `set_columns` (`grampletpane.py:1415`) is the GTK widget-allocation driver; old guard (`if num < 1`) admitted 1000 through; clamp now sits there and at both upstream intake points; iteration-1 sign-off confirmed `_config.set → set_columns` routing is the sole path (`brief.md:31`) |
| T1 — Structure | N/A | Core-only change; `§Structure` (folder==id, `.gpr.py`, `target_version`) is addon-only — gate confirms N/A (`check-gates.json:55`) |
| T2 — Shape | PASS | Gate confirms 1 file conforms to doc-16 §Coding style (`check-gates.json:64`); added function carries a proper docstring; no `print()` calls introduced |
| T3 — Runtime | FAIL | Unit-suite gate reports 1 new failure not in baseline: `setUpClass (interface.test_smoke.SmokeTest)` (`check-gates.json:73`); same delta was a failing gate in iteration 1 (`brief.md:33`) and remains unresolved; interface-smoke sub-gate passes (matches known baseline) confirming the patch itself does not break GUI smoke — but the unit-suite delta must be documented or cleared |
| T4 — Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in bundle; gate correctly records N/A (`check-gates.json:91`) |
| T5 — Judgment | NEEDS-HUMAN | `MAX_GRAMPLET_COLUMNS=100` is a product-policy cap; `brief.md:15` explicitly calls a hard cap a UX-direction decision requiring maintainer input; silent-clamp behaviour (user enters 1000, silently gets 100) is partially mitigated by the new helptext (`grampletpane.py:1669`) but the cap value and silent-clamp approach must be cleared with the maintainer (iteration-1 sign-off flagged this at `brief.md:31`) |
| V — Validation (fitness-to-purpose) | NEEDS-HUMAN | GUI crash path cannot be mechanically verified headless; success criterion (`brief.md:9`) requires a survivable outcome for any accepted column value; without the gramps-testbed interface test or a live manual repro, fitness-to-purpose is unconfirmed; human must clear at sign-off |

---

## §2 C1 — Spec

`brief.md` is structurally valid and machine-parseable. Success criterion (`brief.md:9`): "Setting the Dashboard 'Number of Columns' to any value the field accepts (including a large one such as 1000) does not crash Gramps and does not leave the family tree locked." Invariant (`brief.md:11`): any accepted column value yields a survivable layout. Scope (`brief.md:15`) excludes UX redesign and hard-cap policy decisions. No ambiguity in the spec itself. **PASS.**

---

## §3 C2 — Reproduction (red pre-fix)

`patch.diff` contains no test file of any kind. The carry-forward (`brief.md:31`) required Do to:

1. Remove the helper-only `grampletconfig_test.py` (decoupled from the crash path) — apparently done (not in patch), but
2. Add a `PDCA-UNVERIFIABLE` annotation — **absent**
3. Ship `tests/interface/test_bug_13864_dashboard_columns.py` in gramps-testbed — **absent**

Without a red test or the PDCA-UNVERIFIABLE flag, C2 has no mechanical evidence. The bug itself was confirmed externally (`brief.md:9`), but the PDCA chain requires an in-bundle reproduction artifact. **FAIL.**

---

## §4 C3 — Change

The diff touches exactly one file: `gramps/gui/widgets/grampletpane.py`.

Changes verified by reading `patch.diff`:

| Location | Before | After |
|---|---|---|
| Module level | — | `MAX_GRAMPLET_COLUMNS = 100`; `clamp_column_count(num)` added |
| `GrampletPane.__init__` line 1046 | `kwargs.get("column_count", 2)` raw | wrapped in `clamp_column_count(...)` |
| Config-load branch line 1226 | `int(cp.get(sec, "column_count"))` | `clamp_column_count(cp.get(sec, "column_count"))` |
| `set_columns` line 1415 | `if num < 1: num = 1` | `num = clamp_column_count(num)` |
| Config-dialog builder line 1669 | no `helptext` | `helptext=_("Enter a number from 1 to %d.") % MAX_GRAMPLET_COLUMNS` |

The `clamp_column_count` function coerces to `int` (handles string values from `.ini`) and bounds to `[1, MAX_GRAMPLET_COLUMNS]`. The three call sites cover all known column-count entry paths. The helptext is cosmetic/advisory and does not affect correctness. No unrelated changes. **PASS.**

---

## §5 C4 — Verification (red→green)

Gate verdict: `unverifiable` (`check-gates.json:38`). The gate fires because no `*_test.py` file is present in the patch. `brief.md:17` gives two permitted paths:

- Headless `gramps/gui/test/grampletbar_test.py` if the column-count → layout path is reachable without a running GUI, **or**
- `PDCA-UNVERIFIABLE` flag + gramps-testbed interface test (`tests/interface/test_bug_13864_dashboard_columns.py`) if it is not.

Neither path is satisfied. The patch lands production code changes with no verification artifact and no formal acknowledgement that the path is GUI-only. **FAIL.**

---

## §6 C5 — Causal adequacy

Root cause (derived from brief and patch): `GrampletPane.set_columns` builds one GTK container box per column; with 1000 columns the allocation is enormous, freezes Gramps, and kills the process before the database lock is released. The old guard (`if num < 1: num = 1`) clamped only the lower bound.

The fix inserts the upper-bound clamp at `set_columns` (the allocation site) and defensively at two upstream intake points so no code path can reach the widget builder with an unbounded value. Iteration-1 sign-off established that `self._config.set` always routes through `set_columns` via the registered setter (`brief.md:31`), so there is no bypass.

`brief.md:11` references `grampletbar.py` as a potential related path; the patch does not touch it. Based on the iteration-1 C5 confirmation, `grampletpane.py` is the correct locus — but this reviewer has no visibility into `grampletbar.py`'s call graph without the source. The human should verify no parallel column-count path exists in `grampletbar.py`. **PASS** (with the grampletbar.py caveat carried to §7).

---

## §7 T3 — Runtime detail

Two T3 sub-gates ran:

| Sub-gate | Result | Notes |
|---|---|---|
| Core unit suite | FAIL — 1 new failure not in baseline | `setUpClass (interface.test_smoke.SmokeTest)` — identical delta to iteration-1 failing gate (`brief.md:33`) |
| GUI interface smoke | PASS — matches recorded baseline | Known red: `_ErrorHolder (Glade __setattr__ name-)` — pre-existing, not patch-induced |

The unit-suite delta is pre-existing (it appeared in iteration 1 and was carried forward unresolved). It is not introduced by this patch (the interface-smoke sub-gate confirms the patch does not break the smoke suite). However, it remains an open finding that must be documented or cleared before sign-off.

---

## §8 T5 / V — Items requiring human clearance

These map to the NEEDS-HUMAN rows in the verdict table and must be cleared at sign-off.

**§8.1 T5 — Silent-clamp policy (MAX_GRAMPLET_COLUMNS=100)**

The cap value and the silent-clamp behaviour (no error raised, no dialog shown, only a helptext hint) are a product-policy decision. `brief.md:15` explicitly scopes this out as a UX-direction call. The iteration-1 sign-off flagged it (`brief.md:31`). Options the maintainer must choose between:

- Accept the silent clamp at 100 with helptext (current approach)
- Reject out-of-range input with a validation error
- Raise the cap (or lower it)
- Add a visible warning when input is clamped

**§8.2 V — Fitness-to-purpose**

The success criterion requires that setting any accepted column value "does not crash Gramps and does not leave the family tree locked." The only way to verify this end-to-end is a live GUI test or the gramps-testbed interface test called for in `brief.md:17`. Neither exists in this bundle. Human must confirm against the live application (or accept the interface test in a subsequent iteration) before sign-off.

**§8.3 Pre-existing T3 delta**

`setUpClass (interface.test_smoke.SmokeTest)` new failure must be traced to confirm it is environmental and not a latent patch interaction.

**§8.4 grampletbar.py scope**

`brief.md:11` names `grampletbar.py` as a related code path. The patch does not touch it. Human should confirm no parallel column-count allocation path exists there before sign-off.

---

## §9 Required actions before re-submission

1. **C2/C4 (blocking):** Add `tests/interface/test_bug_13864_dashboard_columns.py` to gramps-testbed per `brief.md:17`, or add a `PDCA-UNVERIFIABLE` annotation with documented justification. Without one of these, C2 and C4 remain FAIL.
2. **T3 (blocking for sign-off):** Document the `setUpClass (interface.test_smoke.SmokeTest)` delta as pre-existing and environmental, or fix the root cause.
3. **T5/V (human-clearance):** Maintainer must approve the `MAX_GRAMPLET_COLUMNS=100` silent-clamp policy before PR is marked ready.
4. **grampletbar.py (advisory):** Verify no parallel column-count path requires the same clamp.

Production code in `grampletpane.py` (C3, C5) is ready; the blocking items are all in the verification and policy layers.
