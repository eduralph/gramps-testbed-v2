# Check review — issue 11589 / pluginmanager-uninstall-destroys-shared-dir

> Advisory, artifact-only, decorrelated from the builder. Inputs: `patch.diff`,
> `brief.md`, `check-gates.json` (build-notes.md withheld by design). Every
> verdict below is re-derived from those three artifacts, not copied from the
> gate `result` fields.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | `brief.md:18-23` carries a single, testable success criterion (uninstall a shared-dir plugin → only its own files go; siblings + unrelated content + the dir survive; sole-occupant still removes the dir). Defect, root cause, scope and out-of-scope are all stated. Spec is well-formed. |
| C2 — C2 Reproduction (red pre-fix) | PASS | Regression test exists (`patch.diff:59-285`, `test_uninstall_shared_dir.py`) and `check-gates.json` C4-verify reports `red-without-fix=PASS` — the test was executed (not skipped) and failed pre-fix, i.e. the temp dir was wiped, reproducing the defect. |
| C3 — C3 Change | PASS | Diff is coherent and scoped to the named target: adds `__plugins_sharing_dir` (`patch.diff:9-23`) + `__remove_plugin_files` (`patch.diff:25-41`) and branches `__uninstall` on `siblings` *before* the rmtree path (`patch.diff:46-54`). Touches only `PluginManager.py` + a new test — no scope creep into core/install-path/repackaging. |
| C4 — C4 Verification (red→green) | PASS | `check-gates.json` C4-verify (gating=true) result=`pass`, `green-with-fix=PASS / red-without-fix=PASS`. The fix flips the test red→green under the verify harness. |
| C5 — C5 Causal adequacy | PASS | Root cause (unconditional `shutil.rmtree(pdata.fpath)` on a shared dir, `brief.md:13-17`) is uncontested (Mantis `confirmed`, maintainer-corroborated). The fix attacks exactly that: it intercepts the shared-dir case and removes only the selected plugin's own files. Root-cause-addressing, not symptomatic. *Residual for human (see §6): the `.gpr.py` name is derived as `splitext(fname)[0] + ".gpr.py"` and the sibling guard keys on `.py` `fname` only — assumes strict 1:1 `*.py`/`*.gpr.py` pairing in the real pack.* |
| T1 — T1 Structure | PASS | `check-gates.json` T1-structure result=`pass` ("1 addon(s) conform to doc 16 §Structure"); re-derive consistent — the diff adds no structural files (no folder rename, no target_version/fname change), only a method body and a `tests/test_*.py`. |
| T2 — T2 Shape | NEEDS-HUMAN | Gate failed on `__init__.py: no GPL licence header in the first 40 lines` — but **no `__init__.py` appears in `patch.diff`**. Both files the patch *does* add/change are shape-clean (test carries full GPL header, `patch.diff:65-83`; no diagnostic prints in either). The violation sits in an untouched bundle file → ambiguous scope: human must decide whether the pre-existing `__init__.py` header gap blocks this contribution. |
| T3 — T3 Runtime | NEEDS-HUMAN | All three runtime suites are `fail` but the failure modes are not plausibly caused by a 2-file addon change to `__uninstall`: core unit suite `Trace/breakpoint trap (core dumped)` (segfault in gramps **core**, which the diff never touches), addon-unit `pip install logs (3 failure(s))` (install/env), interface smoke (`_ErrorHolder`). Marked "whole-suite baseline" in the gate — human must diff against the pre-change baseline to confirm these are pre-existing/environmental, not regressions. |
| T4 — T4 Contribution | N/A | `check-gates.json` T4 path_line: "N/A: no commit-msg.txt or pr-description.md in the bundle." No commit/PR wrapper artifact exists to evaluate against doc 16 §Commit messages / §Contributor workflow. |
| T5 — T5 Judgment | NEEDS-HUMAN | Always-human element (oracle "reviewer + human sign-off"). Overall contribution judgment — code quality, idiom fit, whether the sibling-detection approach is the right shape — is reserved for human sign-off. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human element (oracle "human at sign-off"). Whether the change actually solves the user's problem against the *real* FilterRules pack layout (13 rule pairs in one dir) — not just the temp-dir stand-in — is a fitness-to-purpose call only the human can make. |

## §6 — Items the human must clear

1. **T2 (shape / ambiguous scope).** The T2 gate fails on a missing GPL header in
   `__init__.py`, but that file is **not in `patch.diff`** — the patch's own two
   files conform. Decide whether the pre-existing `__init__.py` header violation is
   in scope for this fix (out-of-band cleanup) or should be left untouched. The
   change should not be failed for a file it does not modify.

2. **T3 (runtime / attribution).** Confirm against the pre-change baseline that the
   three failing suites are pre-existing/environmental. Strong signals they are:
   the core unit suite *core-dumps* (a C-level crash in gramps core, which this
   addon-only diff cannot reach), and the addon-unit failures are pip-install
   logs. If the baseline is equally red, T3 is not a regression of this change.

3. **T5 (judgment).** Human sign-off on overall contribution quality and the
   chosen approach (sibling enumeration via `self._preg.type_plugins` across
   `PTYPE_STR`).

4. **V (fitness-to-purpose).** Validate against the actual installed FilterRules
   pack, not only the test's temp-dir stand-in. Specifically check the residual
   noted in C5: the fix derives the registration file as
   `splitext(pdata.fname)[0] + ".gpr.py"` and guards siblings on `.py` `fname`
   only. If, in the real pack, one `*.gpr.py` registers several rules or the
   `.gpr.py` basename does not match its `.py`, the fix could either orphan a
   `.gpr.py` or unregister a still-present sibling. Confirm the 1:1 pairing the
   brief asserts (`brief.md:14-16`) holds in production.
