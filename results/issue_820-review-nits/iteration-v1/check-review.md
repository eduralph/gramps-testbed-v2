# Check review — issue 820-review-nits

> Advisory, artifact-only, decorrelated from the builder. Inputs: `patch.diff`,
> `brief.md`, `check-gates.json`. `build-notes.md` deliberately withheld. Verdicts
> below are re-derived independently; mechanical gate rows are cross-checked, not
> trusted.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | `brief.md:9-26` gives a concrete per-item success criterion for each of (a)–(e) plus repro instructions (`brief.md:37-40`); oracle well-defined. |
| C2 — C2 Reproduction (red pre-fix) | N/A | No gate configured (`check-gates.json:18`). Batch is behaviour-preserving / CI-observable for (a),(b),(d),(e); (c)'s added `test_addon_paths.py` exercises the *new* `is_in_addons_tree` predicate (`patch.diff:234-272`) — it validates the fix, it is not a captured red of the old `ADDONS_ROOT in fpath` substring test. |
| C3 — C3 Change | PASS | `patch.diff` implements all five: (a) `make_gramps_user` removed `patch.diff:120-128`; (b) `type_plugins(ptype)` `patch.diff:159-161`; (c) `is_in_addons_tree` prefix check `patch.diff:98-111`; (d) `.gpr.py` exclusion dropped `patch.diff:39-40`; (e) `gramps[0-9][0-9]` filter `patch.diff:9-17,52-55`. |
| C4 — C4 Verification (red→green) | FAIL | Gating gate red: `run-verify.sh` errored `tests/test_plugin_registration.py: No such file or directory` (`check-gates.json:33-39`). Red→green never established; this is the gate driving `overall: "fail"`. See §6. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Oracle = reviewer + human (`check-gates.json:44`). (b) replaces `registry._PluginRegister__plugindata` (all pdata) with a union over `for ptype in PTYPE: type_plugins(ptype)` (`patch.diff:159-161`); equivalence holds only if every plugin's ptype ∈ PTYPE and no pdata is double-counted — unverifiable artifact-only without `_pluginreg.py`. |
| T1 — T1 Structure | N/A | Gate mechanically failed "no .gpr.py" (`check-gates.json:55`), but the patch is test-harness + workflow cleanup, not an addon submission (`brief.md:33`, Scope). Addon-structure rules (folder==id, `.gpr.py`, target_version) do not apply. Non-gating. |
| T2 — T2 Shape | PASS | New `.py` files carry the GPL header (`patch.diff:65-83` addon_paths.py, `patch.diff:189-207` test_addon_paths.py); no stray `print()`. (Gate self-reported "N/A: no checkable .py path", `check-gates.json:64` — but the added files are checkable and conform.) |
| T3 — T3 Runtime | FAIL | gramps60 × core 6.0 green (`check-gates.json:73`); gramps61 × core 6.1 red with baseline DELTA: 8 new `Sqlite...ExportSQLTestCase::test_export_sq` failures (`check-gates.json:82`). Real runtime regression on the 6.1 axis; attribution to this harness/workflow patch is not established — see §6. Non-gating. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle to evaluate (`check-gates.json:91`). |
| T5 — T5 Judgment | NEEDS-HUMAN | Oracle = reviewer + human (`check-gates.json:98`). Five independent cleanups shipped in one patch; `brief.md:5-6,47` flags they are splittable and global discipline is one-logical-change-per-PR. Whether to land as one PR or split is a human scope/judgment call. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human at sign-off (`check-gates.json:108`). |

## §6 — items the human must clear

1. **C5 (causal adequacy of item b).** Confirm that `for ptype in PTYPE: registry.type_plugins(ptype)` enumerates exactly the set previously obtained from `_PluginRegister__plugindata` — i.e. PTYPE covers every registered plugin's type and no pdata is yielded under more than one type. If a plugin's ptype is outside PTYPE it would be silently dropped from `_get_addon_plugins`. Verify against `_pluginreg.py` on the PR branch.

2. **T5 (scope / one-PR-vs-split).** Decide whether the five independent nits (a)–(e), spanning `ci.yml`, `docker-build.yml`, `gramps_test_env.py`, and `test_plugin_registration.py`, should land as one PR or be split per `brief.md:5-6` and the one-logical-change discipline.

3. **V (fitness-to-purpose).** Human sign-off that the batch as a whole meets the intent of PR #820's nits review.

## Blocking / advisory notes (not NEEDS-HUMAN rows, but must be resolved)

- **C4 is the hard blocker (gating, overall=fail).** `run-verify.sh` could not find `tests/test_plugin_registration.py` (`check-gates.json:37`). The patch *modifies* that file, so it exists on the branch — this looks like a harness/path mismatch in the verify run rather than a missing file in the change itself. Re-run verification against the branch so red→green can actually be observed before sign-off; do not clear C4 on the strength of the diff alone.
- **T3 6.1 delta attribution.** The 8 new failures are in the Sqlite addon's *own* `ExportSQLTestCase`, independent of `test_plugin_registration.py`; this patch touches only harness/workflow code. Likeliest causes: baseline drift on the 6.1 axis or the newly-included `.gpr.py` py_compile step (item d) surfacing something. Confirm whether the delta reproduces on a clean checkout *without* this patch before attributing it here.
- **Per-item C3 confirmation** (each maps to its brief defect): (a) `brief.md:10-12`→`patch.diff:120-128`; (b) `brief.md:13-14`→`patch.diff:159-161`; (c) `brief.md:15-16`→`patch.diff:98-111`+test; (d) `brief.md:17-19`→`patch.diff:39-40`; (e) `brief.md:20-22`→`patch.diff:9-17,52-55`. All five present.

**Disposition:** advisory — NOT sign-off. Gating C4 is red; T3 6.1 carries an unattributed regression delta; C5/T5/V require human clearance. PR must remain draft (STOP discipline, `brief.md:49-52`).
