# Gate addon plugin-load test on hard load failures

> Reported in addons-source PR #820 review (finding R-C); no Mantis ticket
> (addons-source CI/CD pipeline follow-up). One logical fix.

## Root cause

`TestPluginLoading.test_load_all_addon_modules`
(`tests/test_plugin_registration.py:163`) accumulates genuine non-dependency
load failures into `hard_failures`, but its only response is `LOG.warning(...)`
while its sole assertion is `assertGreater(len(plugins), 0)` (`:166`). An addon
that fails to load therefore makes the test pass silently — unlike the two
sibling smoke tests in the same file, which `self.fail` on their findings.

## Fix

Replace the warning-only block (`tests/test_plugin_registration.py:224-229`)
with a direct `self.fail` when there are non-dependency hard load failures,
matching `TestImportPluginSmoke` (`:258`) and `TestExportPluginSmoke` (`:290`).
Dependency skips and subprocess crashes (typically a missing display server in
CI) stay advisory and keep logging exactly as before. The method's docstring is
updated to state that it now gates.

## Verified against

- `tests/test_plugin_registration.py:163,166` — the method and its sole prior
  gate, `assertGreater(len(plugins), 0)`; nothing failed on `hard_failures`.
- `tests/test_plugin_registration.py:224-229` — the former
  `if hard_failures: LOG.warning(...)` block now `self.fail`s with the same
  message.
- `tests/test_plugin_registration.py:258`, `:290` — sibling smoke tests already
  `self.fail`; this change brings the load check into line with that precedent.

## Test

`tests/test_plugin_load_gate.py` (new regression). It constructs a real
`TestPluginLoading` instance and calls the production
`test_load_all_addon_modules` with one synthetic always-failing addon injected
at the production module's own load seams (`_get_addon_plugins`,
`_check_dependencies`, `subprocess.run`):

- `test_hard_failure_gates_the_load_test` — asserts the method raises its
  `failureException` and the message names the addon and "failed to load".
  Before the fix the method returned normally (only warning); after, it fails.
- `test_clean_load_does_not_gate` — a clean load must not fail the test.

A dedicated module (rather than a case inside `test_plugin_registration.py`)
keeps verification deterministic: running the registration module would boot
the real registry-backed load test, which flakes on environmental addon gaps in
a minimal CI image (e.g. a missing GTK icon theme). The full registry-backed
integration test still runs in this branch's own CI.
