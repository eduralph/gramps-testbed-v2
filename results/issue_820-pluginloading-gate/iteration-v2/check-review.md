# Check review — 820-pluginloading-gate (iteration 2)

> Advisory, artifact-only, decorrelated from the builder. Inputs: `patch.diff`,
> `brief.md`, `check-gates.json`. `build-notes.md` withheld by design. All
> verdicts re-derived from the diff and brief, not lifted from the gates file.

## Verdict

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | Brief is well-formed: a concrete defect, a success criterion permitting *gate* **or** *documented-advisory*, an invariant, and a repro instruction (brief.md:8-39). Spec is actionable. |
| C2 — C2 Reproduction (red pre-fix) | PASS | New `tests/test_plugin_load_gate.py` now drives the *real* production method `TestPluginLoading.test_load_all_addon_modules` (patch.diff:226-238) via seam mocks, not just the extracted helper — directly closing iteration-1's C2 rejection. Pre-fix the method only `LOG.warning`-ed and returned, so `assertIsInstance(outcome, failureException)` (patch.diff:253-258) is red by construction. Design adequate; **but never executed red** — see C4. Residual unknown: I cannot see `test_load_all_addon_modules`' hard-vs-crash classification body (not in diff), so that the synthetic stderr lands in `hard_failures` is asserted, not confirmed. |
| C3 — C3 Change | PASS | The gating decision is the only production edit: `LOG.warning(...)` block replaced by `self.fail(hard_load_failure_message(hard_failures))` (patch.diff:104-112), with the docstring rewritten to declare the gate (patch.diff:86-95). Implements the brief's *gate* option; scope of the production edit matches the named file/method. |
| C4 — C4 Verification (red→green) | FAIL | Gating row failed: `run-verify.sh` errored `tests/test_plugin_registration.py: No such file or directory` (check-gates.json:33-39) — the **same** harness/checkout defect that sank iteration 1 (brief.md:54). Red→green was never executed for the second time; the fix is unverified regardless of how sound the test design is. Decisive reject reason. |
| C5 — C5 Causal adequacy | PASS | Root cause is uncontested and two-sentence-clear: the method named `hard_failures` but only logged them, so its sole assertion (`assertGreater(len(plugins),0)`) let non-dependency load failures pass silently. The patch makes that exact path `self.fail`, restoring the brief's invariant (brief.md:20-23). Fix targets the cause, not a symptom. |
| T1 — T1 Structure | N/A | The advisory T1 "no .gpr.py / addon layout" failure (check-gates.json:51-57) is an addon-submission gate; this patch adds **no addon**, only three `tests/*.py` modules (patch.diff:1,116). The check is mis-targeted at a tests-only change. |
| T2 — T2 Shape | PASS | Both new modules carry the full GPL header (patch.diff:7-25, 122-140); no `print()`; type hints and docstrings present. (Gates row recorded N/A "no checkable .py path" — I re-derive PASS, since the diff does add checkable `.py` with conformant headers.) |
| T3 — T3 Runtime | NEEDS-HUMAN | Advisory runtime rows are red (check-gates.json:69-103): addon-unit 6.0/6.1 "runner exited 2 with no parsed failures", plus `setUpClass (test_smoke.SmokeTest)` and a Sqlite export delta. Last cycle these were ruled environmental/baseline drift, decorrelated from a tests/ gating change (brief.md:53). But the addon-unit **exit-2 / no-parsed-failures** signature may share the same broken-checkout root as the C4 file-not-found; a human with the harness env must confirm the decorrelation rather than assume it. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle (check-gates.json:104-111); nothing to check against doc 16 §Commit/§Contributor. |
| T5 — T5 Judgment | NEEDS-HUMAN | Two deliberate calls need a human: (1) **disposition** — builder chose the *gate* contract over the brief's equally-permitted *documented-advisory* alternative (brief.md:15-19); confirm gate is intended. (2) **scope** — the fix adds two modules (`tests/plugin_load_gate.py`, `tests/test_plugin_load_gate.py`) beyond the brief's named edit surface (`tests/test_plugin_registration.py`, brief.md:27,36). The extract-for-testability and isolation rationales are well-argued in-diff (patch.diff:30-45, 152-167), but the scope expansion is a human accept/reject. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always human. Cannot be assessed while C4 is unproven: there is no executed red→green showing the gate actually fires on a real synthetic load failure in a checkout containing the addons-source tests/ tree. Fitness-to-purpose is unestablished. |

## §6 — items the human must clear

1. **(T3) Confirm the runtime failures are decorrelated, not the C4 defect resurfacing.**
   The addon-unit 6.0/6.1 rows show `runner exited 2 with no parsed failures and no
   matching baseline signature`. That is an execution/infrastructure failure, and the
   gating C4 row failed because the verify checkout lacked
   `tests/test_plugin_registration.py`. Verify these are genuinely environmental drift
   (as last cycle assumed) and not the same missing/incomplete addons-source checkout.

2. **(T5 — disposition) Confirm the *gate* contract is the intended outcome.**
   The brief permits either a real gate or an explicit diagnostic-only/advisory
   declaration. The builder chose to gate (`self.fail`). This is deliberate and must be
   ratified at sign-off.

3. **(T5 — scope) Accept or reject the scope expansion to two new test modules.**
   The brief named only `tests/test_plugin_registration.py`. The patch adds
   `tests/plugin_load_gate.py` (policy extract) and `tests/test_plugin_load_gate.py`
   (regression module). The rationale (deterministic verification without booting the
   real registry; avoiding the icon-theme flakiness described at patch.diff:155-162) is
   defensible but is an ambiguous-scope call reserved for the human.

4. **(V) Validation fitness-to-purpose** — reserved for human at sign-off; blocked
   until C4 produces a real red→green.

## Disposition (advisory)

**Reject — re-derived.** The gating failure is **C4**: red→green was never executed,
for the *second* consecutive iteration, with the identical
`tests/test_plugin_registration.py: No such file or directory` error. The build made a
real improvement — the C2 reproduction now drives the production method end-to-end
rather than only the extracted helper, which answers iteration-1's substantive C2
objection — but a fix whose verification harness cannot even locate the file under test
is unproven. The corrective is the one already named in the carry-forward (brief.md:54):
rebuild and run `run-verify.sh` in a checkout that actually contains the addons-source
`tests/` tree (re-sync first), then demonstrate red pre-fix → green post-fix. Until then
C4, V, and the residual C2 classification unknown stay open.
