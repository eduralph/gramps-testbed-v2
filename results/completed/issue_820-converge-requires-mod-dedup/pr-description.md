# Single-source the requires_mod derivation and is_active helper

> Part of the addon CI pipeline work (upstream PR #820), on
> `feature/ci-cd-pipeline-upstream` → `maintenance/gramps60`. One logical fix:
> de-duplicate the per-job `requires_mod` derivation and the `is_active()` helper.
> Tracking slug: #820-converge-requires-mod-dedup.

## Root cause
`.github/workflows/ci.yml` inlined the `requires_mod` install derivation as an
**identical** Python heredoc in three jobs and the `find_spec` name-gate validator
verbatim alongside it, while the `is_active()` bash helper was copy-pasted into six
job steps. A one-line change to any of them was a three- to six-site edit and the
copies could silently diverge — the copy-paste DRY violation this change removes.

## Fix
Two new files the workflow owns under `.github/scripts/` (self-contained, pure
stdlib, no external/project import):
- `addon_python_deps.py` — exposes `install_list(root)` (the install union the three
  install steps print) and `check_resolves(root)` (the `find_spec` name-gate the three
  validate steps run), scanning `*/*.gpr.py` with the same regex + `ast.literal_eval`
  mechanism as the sibling `addon_system_deps.py`. CLI: `--install-list .` /
  `--check-resolves .`.
- `active_addons.sh` — the single `is_active()` definition, sourced by each filtering
  step.

In `ci.yml` each install heredoc becomes `addon_python_deps.py --install-list .` (3
sites), each validator heredoc becomes `--check-resolves .` (3 sites), and each inline
`is_active()` becomes `source .github/scripts/active_addons.sh` (6 sites). The
surrounding step logic is untouched. The module also centralises the import→distribution
map (`PIL`→`Pillow`) **install-side only**; `--check-resolves` keeps validating the raw
declared import name, exactly as Gramps' `check_mod()` does.

## Verified against
- `.github/workflows/ci.yml:242-258`, `:448-464`, `:594-610` — the three identical
  `requires_mod` install heredocs, now single calls to `--install-list`.
- `.github/workflows/ci.yml:279-318`, `:478-517`, `:624-663` — the three identical
  `find_spec` validator heredocs, now single calls to `--check-resolves`.
- `.github/workflows/ci.yml:76-84`, `:119-127`, `:161-169`, `:337-345`, `:525-533`,
  `:693-701` — the six verbatim `is_active()` copies, now `source` lines.
- `.github/scripts/addon_python_deps.py:1-199` — the new derivation module; the
  install map lives in `_IMPORT_TO_DISTRIBUTION` and is applied only in
  `install_list`, never in `declared_mods`.
- `.github/scripts/active_addons.sh:1-21` — the single `is_active()` definition.
- `install_list(.)` over the current tree equals the old heredoc output byte-for-byte
  (`boto3 dbf life_line_chart litellm networkx psycopg psycopg2 pygraphviz svgwrite`);
  no `requires_mod=["PIL"]` exists in any of the 166 `.gpr.py`, so the map is a no-op
  today and the derived list is unchanged.

## Test
`tests/test_requires_mod_dedup.py:1-164` (runs under the integration job's
`unittest discover -s tests`, pure stdlib / GUI-free). It pins behaviour preservation
— `install_list` and `declared_mods` equal an independent oracle running the old
heredoc algorithm over the real tree, and the install map never leaks into the raw
declared-name set — and the DRY invariant per category: no inline `is_active()` and no
`requires_mod` heredoc survive in `ci.yml`, all three jobs call the module, and **every**
step that calls `is_active` also sources the helper (asserted step-by-step, ≥6 sites),
so a missed step is caught rather than masked. Red→green confirmed on the
`eduralph/addons-source` fork base: green with the module present, red
(`ModuleNotFoundError: addon_python_deps`) with the production files reverted. Final
acceptance is fork CI staying green (`ci.yml` + `docker-build.yml`).
