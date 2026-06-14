# Brief — issue <id> / <slug>

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** <short-kebab-slug>
- **Defect:** <what is wrong — the observable problem>
- **Success criterion:** <the observable condition that means it is fixed>
- **Invariant to restore:** <the property the fix must make true, stated over the
  defect CATEGORY, not the repro file. NOT a mechanism. Cite its source (language spec /
  framework docs / internal rule) per `docs/principles.md` §3–§6. SELF-TEST: could Do
  satisfy this by guarding a single module? If yes, it's the narrow symptom-sentence —
  widen it. Omit only for non-structural behavioural bug fixes (principles.md §1.1).>
- **Repo + branch target:** <owner/repo> @ <branch>   (resolve here at Plan — do not leave to Do)
- **Depends on:** <id>[, <id>…]   (optional — batch/lane scheduling waits until these bundles are COMPLETE before this one runs; docs 09)
- **Conflicts with:** <id>[, <id>…]   (optional — never co-schedule these in the same concurrent wave, e.g. they edit a shared file; docs 09)
- **Verification base:** <remote>/<branch>   (optional, addon only — verify C4/T3 against a FORK PR branch instead of clean upstream, e.g. `origin/feature/ci-cd-pipeline-upstream` when the fix lives on the fork; needs `make fork-worktrees` + an engine/fork-bases.tsv row; issue #96)
- **Surfaces:** <where the change is observable — `gui` (touches the frontend / an E2E
  through the app is needed), `data` (backend/logic only), or `both`. Drives which
  runtime gates apply (e.g. an E2E gate runs only when this is `gui`). Optional.>
- **Scope:** <the defect to remove — one logical fix. MUST NOT name a probe/guard/helper
  (a capability check, `hasattr`, `try/except import`): naming a mechanism seats the fix
  shape for Do. Leave mechanism to Do; Do prefers removing the cause over guarding it
  (principles.md §3.1, §3.3).> / out of scope: <what is explicitly excluded>
- **Repro instruction:** <fixture + exact steps on the target branch>
- **Test file:** <path where the regression test ships — must fail pre-fix, pass post-fix.
  If the fix needs a testable seam (extraction so the test avoids the GUI / heavy deps),
  the test MUST exercise the PRODUCTION path — production routes through the same
  extracted unit the test drives — NOT a parallel copy that mirrors production
  (principles.md §3.4).>
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** <if the fix ADDS or REMOVES a core `.py` (a new test, a probe
  helper, …), name its `po/POTFILES.{in,skip}` placement — a file with translatable
  strings → `POTFILES.in`, one without (tests/helpers) → `POTFILES.skip`; a deletion is
  removed from both (doc 16 §Adding and removing Python files). Do registers it in the
  same patch; `T2-potfiles` checks it. Omit for a patch that adds/removes no `.py`.>
- **Prior-art check (triage cycles):** <searched by file path — merged history / open PRs / closed PRs — result>
- **Mantis:** <the tracker issue id (e.g. `13418`) — or `none — <why this fix has no
  tracker ticket>` for a fix that genuinely has none (e.g. it originated from GitHub
  PR feedback or is internal cleanup). Drives the T4 trailer: an id ⇒ a `Fixes/Bug
  #id` trailer is required; `none` ⇒ the trailer MUST is waived (the publisher omits
  it and the PR body states the origin) — never invent or borrow an unrelated id.>
- **Disposition hint:** <likely-fix | likely-close | POSSIBLY-FIXED → verify first | UPSTREAM | EXTERNAL | NO-NOTES>

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
