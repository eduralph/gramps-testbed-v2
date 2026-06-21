# Check Review — issue 6825 / surname-plugins-ignore-group-mapping

**Reviewer role:** Check (advisory, artifact-only, decorrelated from builder)  
**Artifacts examined:** `brief.md`, `check-gates.json`, `patch.diff`  
**Artifact withheld:** `build-notes.md` (by design)  
**$PDCA_TARGET:** unset — all path:line citations grounded on `patch.diff` hunk headers  
**Date:** 2026-06-21

---

## §1 Overall disposition

**CONDITIONAL PASS** — all mechanical gates are green; two items require human sign-off before the patch ships (§6).

---

## §2 Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — Spec | PASS | `brief.md` supplies a precise defect statement (raw `get_surname()` in `SameSurname.apply_to_one` vs. `get_group_name()` in `run()`), a binary success criterion (consumers agree on grouping), a scope boundary (no cross-plugin Utils refactor unless divergence spans them), and a repro recipe. |
| C2 — Reproduction (red pre-fix) | PASS | C4 gate records `red-without-fix=PASS`; test `test_samesurnames_filter_honors_global_mapping` (patch.diff:+106) carries an inline "Pre-fix this is RED" comment confirming the added test fails against the unmodified `apply_to_one`. build-notes.md is withheld, so narrative repro cannot be read directly, but the C4 oracle provides equivalent evidence. |
| C3 — Change | PASS | Four files changed; each change is traceable to the identified divergence. `samesurnames.py` hunk @-60: `get_surname()` → `name_grouping_name(db, name)` (root fix). `topsurnamesgramplet.py` hunk @+200/203: `get_group_name()` → `name_grouping_name(db, name)` (adds global-mapping layer the old call missed). `filterbyname.py` hunk @+237: same upgrade. No unrelated edits detected. |
| C4 — Verification (red→green) | PASS | Gate `C4-verify` is `gating:true`, result `pass`; oracle reports `green-with-fix=PASS / red-without-fix=PASS` (`check-gates.json:37-38`). |
| C5 — Causal adequacy | PASS | Root cause is the three-way call-site split: `apply_to_one` ignored all mappings (`get_surname()`), `run()` honoured only per-name override (`get_group_name()`), and the gramplet path also missed the global table. Replacing all three with `name_displayer.name_grouping_name(db, name)` — which the Gramps display layer documents as honouring both the per-name override and the DB-wide name-group table — closes the divergence at the correct abstraction layer. The fix is neither over- nor under-targeted relative to the stated invariant. |
| T1 — Structure | N/A | No addon-source path appears in `patch.diff`; §Structure conformance (folder==id, target_version, fname, no `__init__.py`) applies to addon bundles only. Gate confirms: `T1 – N/A: no addons-source path in patch.diff` (`check-gates.json:55`). |
| T2 — Shape | PASS | Gate `T2-shape` result `pass`: 4 files conform to doc 16 §Coding style (`check-gates.json:64`). Gate `T2-potfiles` result `pass` and `gating:true`: no new `.py` file is created (the test file already existed and is extended), so no POTFILES.skip registration is required (`check-gates.json:73`). No `print()` calls introduced. |
| T3 — Runtime | PASS | Gate `T3-unit` result `pass`: whole-suite baseline matches recorded baseline of 7 known-red tests; no new failures (`check-gates.json:83`). The ⚠ baseline-tree-drift note (`detached@674e3b`) is a git-state advisory, not a test failure. |
| T4 — Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle; gate records `T4 – N/A` (`check-gates.json:91`). Contribution wrapper is out of scope for this artifact set. |
| T5 — Judgment | NEEDS-HUMAN | Reviewer assessment: scope is well-calibrated — three consumers fixed, StatsGramplet correctly excluded (its surname-listing was removed, as `brief.md:27-28` establishes); `_same_surname_handles` extraction is clean; `FakeDb` minimal-interface pattern in tests is appropriate. One point for human review: `filterbyname.py` was not part of the original bug report's symptom set (it already used `get_group_name()`, so it honoured per-name overrides). The patch upgrades it to also honour the global DB mapping. This is consistent with the brief's invariant ("all surname consumers agree") but exceeds the minimal fix; human should confirm the scope widening is intentional. |
| V — Validation | NEEDS-HUMAN | Fitness-to-purpose — whether a real database with a global name-group mapping (`set_name_group_mapping("Jones","Smith")`) now produces consistent results across all UI entry points — requires human end-to-end verification against `maintenance/gramps61` per `brief.md`'s repro recipe (two persons, Group As → Group All, compare TopSurnamesGramplet vs. SameSurnames quick view). The automated test suite covers the data layer but not the rendered UI paths. |

---

## §3 Patch mechanics (re-derived)

**`samesurnames.py` — core fix**

- `SameSurname.apply_to_one` (diff hunk @-60): old code tested `name.get_surname().upper() == src.upper()` — raw surname, no mapping. New code: `group = name_displayer.name_grouping_name(db, name); if group and group.upper() == src`. `src` is already `.upper()` (line 256 is unchanged), so the comparison is correct. The `db` parameter was already in scope as the method's first argument.
- `_same_surname_handles` (new helper, diff @+272): extracts the filter-building logic from `run()` and uses `name_grouping_name` for `rsurname` derivation, replacing the old `person.get_primary_name().get_group_name()`. `run()` now delegates to it.

**`topsurnamesgramplet.py`**

- `record_surnames` gains `db` as its new first positional parameter (diff @+173). Two internal calls (`primary_surname` and `allnames` set-comprehension) switch from `get_group_name()` to `name_grouping_name(db, name)`. The single call site in the gramplet's loop (diff @+212) is updated to pass `self.dbstate.db`. No other callers exist in the diff; the test helper `tally()` now threads a `FakeDb()` default through.

**`filterbyname.py`**

- One call site changed (diff @+237): `name.get_group_name()` → `name_displayer.name_grouping_name(database, name)`. The structural shape of the loop is otherwise unchanged.

**Test additions (`topsurnamesgramplet_test.py`)**

- `FakeDb`: minimal stand-in exposing `get_name_group_mapping(surname)` only; allows existing tests (which exercise the no-grouping case) to keep passing without an in-memory DB.
- `SurnameGroupingConsistencyTest`: uses a real in-memory SQLite DB via `make_database("sqlite")`; sets `db.set_name_group_mapping("Jones","Smith")`; asserts that `SameSurname.apply_to_one`, `_same_surname_handles`, and `record_surnames` all agree. The four test methods collectively exercise every repaired call site.

---

## §4 Concerns (non-blocking)

1. **`filterbyname.py` scope**: see T5 above — the change is defensible but slightly outside the minimum fix. No functional objection; flagged for human confirmation only.
2. **`_same_surname_handles` is a private symbol** (underscore prefix) imported directly by the new test. This is acceptable test practice but means future refactors of the helper's name will break the test silently unless the test file is updated in the same commit.
3. **Baseline drift warning** (`detached@674e3b`): the T3 gate passes against the recorded baseline, but the tree is in detached-HEAD state. If further patches land before this one merges, the baseline comparison should be re-run from a named branch tip.

---

## §5 Gate summary

| Gate | Gating? | Result |
|------|---------|--------|
| C4-verify | yes | PASS |
| T2-potfiles | yes | PASS |
| T1-structure | no | N/A |
| T2-shape | no | PASS |
| T3-unit | no | PASS |
| T4-contribution | no | N/A |

Both gating gates pass. No blockers from mechanical checks.

---

## §6 Human-required clearances

The following must be cleared by a human before the patch is accepted:

**H1 (from T5):** Confirm that widening `filterbyname.py` from per-name-override-only (`get_group_name()`) to both-override-and-global-mapping (`name_grouping_name()`) is intentional and within the agreed scope for this issue. If yes, no code change needed. If no, revert the `filterbyname.py` hunk and re-run C4.

**H2 (from V):** Manually run the repro recipe from `brief.md` on `maintenance/gramps61` with the patch applied: add Smith and Jones persons, apply "Group As → Group All" mapping, open TopSurnamesGramplet and SameSurnames quick view, and confirm both surfaces show the two persons in the same group. Sign off or file a new defect if they diverge.
