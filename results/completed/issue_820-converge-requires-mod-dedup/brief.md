# Brief — issue 820-converge-requires-mod-dedup / dedup requires_mod + is_active

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> Decomposed from `results/issue_pr820-ci-checkin/` (improvement C2; subsumes review
> finding R-D). Tracks addons-source PR #820.

> **Re-plan note (2026-06-13):** this is an *improvement ported from the testbed*, not a
> convergence onto it. #820 must stay **self-contained** — it must NOT import or depend
> on gramps-testbed-v2 (maintainer decision; [[gramps-addons-non-mantis-fork-issue]]).
> So the dedup is done **inside #820's own `.github/scripts`**, adopting the testbed's
> *technique* (its `addon_python_deps.py` is reference only). The earlier dependency on
> `820-converge-system-deps-lib` (C1) is **dropped** — C1 is closed (see its `CLOSED.md`),
> and #820 already ships its own dep scripts. C2 now heads the `ci.yml` serial chain.

- **Slug:** 820-converge-requires-mod-dedup
- **Defect:** in PR #820's `.github/workflows/ci.yml` the `requires_mod` derivation is
  inlined as an **identical Python heredoc in three jobs** (`unit-test-linux`,
  `unit-test-windows`, `integration-test`) — the exact copy-paste the testbed long ago
  replaced with a single `addon_python_deps.py` derivation (its docstring records why),
  which also centralises the **PIL→Pillow** install-name map; PR #820's separate
  `find_spec` validator step partly re-implements that. Separately, the `is_active()`
  bash helper is duplicated verbatim across ~6 `ci.yml` job steps. A one-line change to
  either is a 3–6-site edit and the copies can silently diverge.
- **Success criterion:** the `requires_mod` derivation is obtained from **one** module
  **that #820 owns under `.github/scripts/`** (consumed by all three jobs), and
  `is_active()` lives in **one** sourced helper consumed by every job; the derived
  module list and active-addon set are unchanged (PR #820 CI green on the
  `eduralph/addons-source` fork). No dependency on gramps-testbed-v2 — the testbed's
  `addon_python_deps.py` is the design reference, not an import.
- **Invariant to restore:** no derivation or helper is duplicated across CI jobs — each
  lives in one place, in the repo's own scripts. Stated over the category (every per-job
  derivation). Source: `docs/principles.md` (DRY / single-source).
- **Repo + branch target:** gramps-project/addons-source @ `maintenance/gramps60` via
  `feature/ci-cd-pipeline-upstream` (synced @ `1466491ab`). Tested on the
  `eduralph/addons-source` fork.
- **Verification base:** origin/feature/ci-cd-pipeline-upstream
- **Onto branch:** origin/feature/ci-cd-pipeline-upstream
- **Verification (C4 = fork CI, NOT local):** the fix is `.github/` CI-infra, which the
  local `run-verify.sh` cannot exercise (no `ci.yml` in the testbed/worktree checkout).
  Demonstrate red→green by pushing `feature/ci-cd-pipeline-upstream` to
  `eduralph/addons-source` → `docker-build.yml` + `ci.yml` run; **green on the fork is
  the acceptance signal.** Do/Check must not expect a local C4 pass.
- **Surfaces:** data.
- **Depends on:** —
  (none — C1 closed. C2 is the **head** of the `ci.yml` serial chain: C3
  (`820-build-toolchain-coverage`) and nits (`820-review-nits`) edit the same workflow and
  declare `Depends on` C2/C3 respectively, so the batch stacks them after it, never
  concurrently. The `—` value parses to no dependency.)
- **Scope:** replace the three `requires_mod` heredocs with a call to a single
  derivation module #820 owns under `.github/scripts/` (extend its existing dep script,
  or add one — adopting the testbed's `requires_mod_union()` approach in #820's own
  code); factor `is_active()` into one sourced helper (e.g.
  `.github/scripts/active_addons.sh`) consumed by every job. / out of scope: the
  system-deps lib (C1, closed); the `find_spec` name-gate *logic* (keep — but have it
  consume the shared derivation, not its own copy).
- **Repro instruction:** `grep -c "requires_mod\\s*=\\s*(\\[" .github/workflows/ci.yml`
  (three heredoc copies) and `grep -c 'is_active()' .github/workflows/ci.yml` (~six).
- **Test file:** behaviour-preserving refactor — no new addon `test_*.py`; prove the
  derived `requires_mod` union and active-addon set are identical pre/post (a small
  assertion script #820 owns, and primarily the fork CI staying green).
- **Citations expected:** Do cites the three `ci.yml` `requires_mod` heredoc line ranges
  and the `is_active()` copies on the PR branch; may cite the testbed's
  `engine/scripts/lib/addon_python_deps.py` as the **design reference** (not a dependency).
- **Prior-art check (triage cycles):** review finding R-D + improvement C2; the testbed's
  `addon_python_deps.py` is the reference technique (it exists precisely to kill this
  heredoc). No prior landed fix on #820.
- **Disposition hint:** likely-fix (mechanical, behaviour-preserving; self-contained).

## STOP discipline

Draft only until Check sign-off. The PR MUST NOT be marked ready before sign-off
accepts.

## Prior attempt — learnings to carry (fresh Do, not an iterate)

The earlier attempt (and its `iteration-v1/`) were built on the rejected
"reuse/import the testbed's `addon_python_deps`" approach; both were removed, since the
self-contained reframe above supersedes them. This is a **fresh Do** against
`feature/ci-cd-pipeline-upstream` @ `1466491ab` — not an iterate of the old patch. Two
design learnings from that attempt still apply:

- **PIL→Pillow — resolve explicitly, don't leave it silent.** EditExifMetadata declares
  `requires_mod=["PIL"]`. The install-name map (`PIL`→`Pillow`) belongs on the INSTALL
  side only; the `find_spec` name-gate must keep consuming the **raw** import name. But
  normalizing the derived *install* list does change it for EditExifMetadata (`pip
  install PIL` fails; the distribution is `Pillow`) — arguably a correction. Decide
  in-scope-correction vs scope creep and **state the decision** in build-notes.
- **`is_active()` coverage must be per-category.** A structural test asserting the helper
  is sourced "at least once" is too weak — assert it is sourced in **every** active-addon
  filtering job-step (the brief's per-category invariant), so a missed step is caught.
