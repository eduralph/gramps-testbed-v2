# Provision source-built addon deps in CI instead of silent skip

Tracks addons-source PR #820 (bundle 820-build-toolchain-coverage); no Mantis
ticket — this is CI-pipeline feedback on the #820 branch.

## Root cause
The `gramps-ci` Dockerfile purged the build toolchain (`gcc`, `python3-dev`,
`pkg-config`) immediately after installing Gramps, and the source-built addon
`requires_mod` with no wheel on a CI platform (`pygraphviz`, `psycopg2`,
`psycopg`) had no system package provisioned on either lane. So a CI-runtime
`pip install` of those failed for a missing compiler/header, the failure was
swallowed by the install step's `|| echo … (continuing)`, and an addon that
hard-imports them ran a silently degraded suite while the job stayed green —
coverage loss reported as success.

## Fix
- Keep the build toolchain in the image: drop the `apt-get purge` so the
  apt-lane source builds have a compiler.
- Add `MOD_BUILD_PACKAGES` to the single-source dependency map: each
  source-built `requires_mod` maps to its apt `-dev`/libpq header and its
  prebuilt conda-forge package (never `None`), derived from the addons'
  `.gpr.py` exactly like `requires_gi`/`requires_exe`. ci.yml installs that
  set **before** the runtime pip step on both the apt and conda lanes, so the
  affected suites run rather than skip.
- Close the category over future additions: every declared `requires_mod` must
  be classified as wheel-only (`WHEEL_ONLY_MODS`) or source-built, and the
  `--unmapped` drift guard now fails CI on any module that is neither — a new
  source-built dep cannot silently reopen the gap.

## Verified against
- `.github/docker/gramps-ci/Dockerfile:111` — the `RUN apt-get purge -y gcc
  python3-dev pkg-config && apt-get autoremove -y` line is removed; the
  toolchain stays in the image.
- `.github/workflows/ci.yml:262`, `:468`, `:614` — the `|| echo … (continuing)`
  swallow that hid the failed builds; the new "Install addon system deps" steps
  now run before each lane's runtime pip step.
- `.github/scripts/addon_system_deps.py` — `MOD_BUILD_PACKAGES`
  (pygraphviz→libgraphviz-dev/pygraphviz, psycopg2/psycopg→libpq-dev/conda
  package), `WHEEL_ONLY_MODS`, `scan_modules()`, `packages()` includes the new
  table, and `unmapped()`/`main()` report and exit 1 on a `mod:` drift.
- `PostgreSQLEnhanced/postgresqlenhanced.gpr.py:46` declares `requires_mod`
  `psycopg`, hard-imported at `PostgreSQLEnhanced/connection.py:38` — the
  source-built module that was missing from the original map; pygraphviz
  (`NetworkChart/NetworkChart.gpr.py`) and psycopg2 (`PostgreSQL`,
  `SharedPostgreSQL`) are the other two.
- Scanned every `*/*.gpr.py` on the target branch: the nine declared
  `requires_mod` split into six wheel-only and the three source-built modules
  above; `--unmapped .` reports no drift.

## Test
`tests/test_addon_system_deps.py` — a stdlib-only regression suite driving the
production derivation path (`deps.packages(...)`, `deps.unmapped(...)`,
`deps.main(["--platform", …])`/`["--unmapped", …]`, the exact calls ci.yml
makes). It asserts both lanes surface every source-built `requires_mod`'s
package (apt `-dev`/libpq and a non-`None` conda package), that every declared
`requires_mod` is classified, and that the Dockerfile no longer purges the
toolchain. Red→green confirmed via the dockerised `run-verify.sh` against the
verification base (`origin/feature/ci-cd-pipeline-upstream`): with the fix
applied `Ran 11 tests … OK`; with the production change reverted the suite goes
red (FAILED, failures=3, errors=5).
