# Brief — issue addon-maintainer-mention / auto-comment the addon maintainer on a PR

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The automation half of gramps-testbed-v2 issue #53 (the process/checklist half ships
> separately as testbed PR #97). Tracks addons-source; non-Mantis → fork GitHub issue
> ([[gramps-addons-non-mantis-fork-issue]]).

- **Slug:** addon-maintainer-mention
- **Defect:** when a PR modifies a third-party addon in `addons-source`, nothing notifies
  the person responsible for that addon, so maintainers miss fixes to their addons. Raised
  on gramps-project/addons-source PR #946: Doug Blank (@dsblank) — *"a github workflow that
  when a PR is created, it would mention the original developer (or contributors) of the
  addon in a comment? Otherwise I could miss fixes to my addons."*; Nick Hall (@Nick-Hall)
  — *"That seems like a good idea. You should mention the current maintainer if one
  exists."* The addon's `.gpr.py` declares `authors`/`maintainers` (+emails), but no CI
  surfaces them on a PR.
- **The handle gap (decisive constraint):** a GitHub *notification* needs an **`@handle`**;
  a plain name/email in a comment does not ping. `.gpr.py` records **names/emails, not
  handles**, and resolving an email → handle at run time is **empirically unreliable** —
  tested on real maintainer emails (`matt.familienforschung@gmail.com`,
  `lamberson@yahoo.com`) both resolved to nothing via the commits API, because the `.gpr.py`
  email often isn't the person's GitHub commit email, addons are frequently committed by a
  repo maintainer on the author's behalf, and many `.gpr.py` leave the email **blank**
  (`authors_email=[""]`). **So a reliable @-mention requires the contributor's GitHub handle
  to be declared in the addon's `.gpr.py`** (a new field, e.g. `authors_github` /
  `maintainers_github`) — there is no dependable way to derive it otherwise.
- **Success criterion:** on PR open/synchronize, a GitHub Actions workflow posts (and
  keeps updated) **one** comment that **@-mentions the current maintainer of each touched
  addon** — its `maintainers` if the `.gpr.py` declares any, otherwise its `authors` (the
  de-facto current maintainer) — read from the `.gpr.py` **every run** (always current, no
  separate mapping to drift), as a heads-up so they're aware of the change (awareness, not
  attribution). The mention **reliably notifies** when the addon declares the contributor's
  GitHub handle (the prerequisite below); absent that, it degrades to best-effort
  email→handle resolution and, failing that, names the person (no ping).
- **Invariant to restore:** every addon-touching PR automatically calls out the addon's
  responsible party — stated over the category (any addon × any PR), sourced from the
  addon's own `.gpr.py`. A PR that touches no addon posts nothing.
- **Repo + branch target:** gramps-project/addons-source @ `maintenance/gramps60`; pushed
  from the `eduralph/addons-source` fork. **Independent of #820** — a new standalone
  workflow file, no overlap with `ci.yml`. **Self-contained:** addons-source must NOT
  depend on gramps-testbed-v2 — port the technique from the testbed's
  `engine/scripts/lib/addon_authors.py` into addons-source's own `.github/scripts/`, do not
  import it ([[testbed-internal-verified-out-of-band]] is the testbed side; this side stands
  alone).
- **Surfaces:** data (CI automation; no Gramps GUI).
- **Depends on (for RELIABLE operation):** a **contributor GitHub-handle field in `.gpr.py`**
  (e.g. `authors_github` / `maintainers_github`). This is an addons-source **schema
  addition** — a maintainers' call, to propose on PR #946 and backfill across addons; it is
  NOT in this bundle's build. The workflow ships and runs *without* it (best-effort + name
  fallback), but only **notifies reliably once the handle is declared**. Treat the field as
  the gating prerequisite for the success criterion's "reliably notifies" clause.
- **Scope:** `.github/workflows/addon-maintainer-mention.yml` + a small resolver script it
  calls (`.github/scripts/addon_mention.py` or similar). The resolver: from the PR's changed
  files derive the touched top-level addon dir(s) → read each `<Addon>/*.gpr.py` →
  maintainers-else-authors → pick the @-handle in this order: **(1) the declared
  `*_github` handle** (reliable, once the field exists), **(2)** best-effort email→handle
  (`/repos/{owner}/{repo}/commits?author={email}` → `author.login`), **(3)** the plain name
  (no ping) → compose the comment. The workflow: `pull_request_target`, find-and-update a
  single marker-tagged comment (idempotent, no per-sync spam). / out of scope: *adding* the
  `.gpr.py` handle field (the upstream prerequisite above — propose separately); the
  testbed-side publisher callout (testbed #97); #820's `ci.yml`.
- **Security (MUST):** `pull_request_target` runs with a token in the base-repo context —
  do **NOT** execute PR code. Only *parse* the changed `.gpr.py` as text (via the API or a
  no-build read-only checkout of the head). Never run anything from the PR.
- **Repro instruction:** open a PR on `eduralph/addons-source` touching e.g.
  `TMGimporter/` (declares `maintainers=["Sam Manzi"]`) — today no comment appears; the
  maintainer is not notified.
- **Test file:** unit-test the resolver script against synthetic `.gpr.py` fixtures
  (maintainers-else-authors; the three-step handle pick — declared `*_github` → best-effort
  email → name fallback; multi-addon PR; addon with no credit fields) — the same shape as
  the testbed's `engine/tests/test_addon_authors.py`. The live workflow is exercised
  end-to-end on the **fork's** Actions (a throwaway PR → one comment that @-mentions when a
  handle is available, else names the maintainer).
- **Citations expected:** Do cites the addon `.gpr.py` `authors`/`maintainers` fields and
  the new workflow + resolver paths.
- **Prior-art check (triage cycles):** PR #946 is the origin (Doug's proposal, Nick's
  amendment). No existing PR-comment workflow on addons-source (only #820's `ci.yml` +
  `docker-build.yml`, which don't comment). The testbed's `addon_authors.py` (PR #97) is the
  reference resolver technique to port self-contained.
- **Disposition hint:** likely-fix for the *workflow* (contained: one workflow + one
  resolver), but the **"reliably notifies" goal is gated on the `.gpr.py` handle field**
  (the Depends-on prerequisite) — without it the automation runs but mostly only names the
  maintainer (verified: real emails don't resolve). Decide at Plan/sign-off whether to ship
  the best-effort workflow now and pursue the handle field upstream in parallel, or hold the
  workflow until the field lands.

## Verification (C4 = fork CI for the workflow; local for the resolver)

The live `.github` workflow can only run on GitHub Actions — the local C4 harness
(`run-verify.sh`) cannot exercise it (no `ci.yml`/Actions in the worktree checkout; same
constraint as the #820 family). So: the **resolver script** is verified locally by its
red→green unit test; the **workflow** is verified on the **`eduralph/addons-source` fork**
(push the branch → open a throwaway PR touching an addon → confirm one idempotent comment
@-mentions/names the resolved maintainer-else-author). Acceptance signal = the fork comment
appears correctly; note this in build-notes (do not expect a local C4 pass).

## STOP discipline

Draft only until Check sign-off. A draft PR to gramps-project/addons-source MAY be opened
for fork-CI feedback; it MUST NOT be marked ready before sign-off accepts.
