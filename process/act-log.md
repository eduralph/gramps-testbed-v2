# Act log — Gramps Testbed v2

> Append-only, cross-cycle (docs 02 §ACT). Each entry records which frozen
> bundles an Act review considered, what their records exposed, the concrete
> process deltas applied (each located by a path / rule ID / template field), and
> how the next review will judge whether the delta worked. Act never re-decides a
> contribution's disposition. Newest entries on top.

<!-- Template for a new entry:

# Act review — <date> — cycles considered: <issue_ids>

## What the cycles' records exposed
- <pattern across one or more cycles, citing SUMMARY §6/§7/§10>

## Process deltas
- Spec template: <field added/clarified/removed>            (path)
- Ruleset: <rule added/retired/relaxed/tightened>           (path:line)
- Gates: <check added/promoted/moved>                       (path:line)
- Agent skills: <SKILL.md / AGENTS.md adjustment>           (path:line)

## Follow-ups routed (not process deltas — work handed to an owner)
- Another bug (project/addon): filed <tracker> #NNNN        (link)
- Design issue: <name> → dedicated design phase, owner <who>
- Testbed/driver issue: testbed GH issue #N | pdca-harness GH issue (enhancement)  (link)
- Other open Act item: <item> → owner <who>, next step <…>

## How effectiveness will be judged
- The next Do phases should not recreate <specific issue>. Watch the next K cycles.
-->

# Act review — 2026-06-20 — cycles considered: all 19 in index (issue_11589, issue_11786, issue_12576, issue_13205, issue_13636, issue_13888, issue_46, issue_820-build-toolchain-coverage, issue_820-converge-requires-mod-dedup, issue_820-description-resync, issue_820-pluginloading-gate, issue_8653, issue_8796, issue_addon-tests-init-py-gramps60, issue_glade-setattr, issue_headless-ut-segfault, issue_skip-bsddb-tests-linux, issue_sqlite-export-6.1, issue_tmg-os-test-split-gramps61)

## What the cycles' records exposed

- **Three §10 candidates already resolved — positive signal.** Before routing any
  new work, confirmed that three prior §10 items have been addressed in code since
  those SUMMARY.mds were written:
  - **glade-setattr §10 #2 (t3_baseline precedence bug):** `t3_baseline.py:130`
    now reads `if new and not sig:` — a matching `run_level_signature` takes
    precedence over per-test failures, preventing a whole-run crash that surfaces
    as a `setUpClass` id from being mislabelled as a new delta (comment cites
    "issue #13"). Fixed.
  - **820-pluginloading-gate §10 #1 (INTEGRATION.md C4 unverifiable doc):**
    `INTEGRATION.md:161–171` already documents "C4 *unverifiable* (not a
    manufactured gate)", the two triggering cases (test-only patch; no local test),
    the `PDCA-UNVERIFIABLE` + exit 77 mechanic, and the "never manufacture a
    non-`test_` module" rule — naming the pluginloading-gate helper as the
    worked example.
  - **tmg-os-test-split-gramps61 §10 (run-verify.sh N/A path for test-only):**
    `run-verify.sh:162` already emits `PDCA-UNVERIFIABLE: test-only patch — no
    non-test production file for the red-without-fix leg to revert` + exit 77.
    The C4 N/A path is live.

- **One §10 item still open — success-criterion C4-achievability
  (glade-setattr §10 #1).** The brief template's `Success criterion` field had
  no guard against scoping the criterion to a repo-wide / whole-suite gate. The
  glade-setattr brief stated success as "T3-interface smoke goes green" — a gate
  that applies the full upstream tree and only clears post-merge. C4-verify was
  green (the real per-fix proof) but didn't match the stated criterion, creating a
  misleading gate-fail at Check. Fix: add a C4-achievability note to the template
  field. Addressed in this review (see Process deltas; filed as testbed #175).

- **Recurring NEEDS-HUMAN (V / T5 / C5) — no delta.** All three appear in
  every cycle by oracle design. The 2026-06-20 predecessor entry already confirmed
  this is correct system behaviour; reconfirmed here.

- **C2 "no gate configured" (2× signal — threshold not yet met).** Two cycles
  (addon-tests-init-py-gramps60 and skip-bsddb-tests-linux) show C2 NEEDS-HUMAN
  because the fix type (structural discovery fix; test-skip with docker required)
  makes a traditional failing-test repro impossible. Both were handled acceptably
  at sign-off. The two causes differ; n=2 is below the threshold for a uniform
  process delta. Carry forward; act if it recurs.

- **issue_8653 §10 — still open.** Both items (run-addon-unit.sh exit-1 root-cause;
  C4-green/T3-red-split guidance) were carried from the 2026-06-08 review and
  the previous 2026-06-20 entry. No new evidence to drive a process delta. Filed
  as testbed #176 (see Follow-ups).

## Process deltas

- **Spec template (applied):** `Success criterion` field in `templates/brief.md.tpl`
  (line 10) expanded with a C4-achievability note: the criterion must be
  demonstrable by C4-verify (patch applied in isolation at Check); whole-suite T3
  passes and fork-CI greens are not acceptable as the per-fix criterion because
  they only clear post-merge. Supplementary evidence only.
  (`templates/brief.md.tpl:10`)

## Follow-ups routed (not process deltas — work handed to an owner)

- **Testbed GH #175 — brief template success-criterion C4-achievability:**
  the template change above is applied; #175 tracks the acceptance signal
  (next GUI-fix brief should name a C4-achievable criterion).
  https://github.com/eduralph/gramps-testbed-v2/issues/175

- **Fork issue eduralph/addons-source #50 — drop `tests/plugin_load_gate.py`
  helper (820-pluginloading-gate §10 #2):** the helper was manufactured to give
  run-verify a file to revert; now that the PDCA-UNVERIFIABLE path exists, it is
  dead scaffolding. Cleanup: remove the helper, inline the call in
  `test_plugin_registration.py`. Owner: human.
  https://github.com/eduralph/addons-source/issues/50

- **Testbed GH #176 — run-addon-unit.sh exit-1 diagnosis + C4/T3-split guidance
  (issue_8653 §10 both items):** diagnose the recurring "exited 1 / no parsed
  failures, no matching baseline signature" mode; add INTEGRATION.md §3 note on
  the expected green-C4/red-T3 split and correct the reviewer's wrong model of the
  runner's bootstrap capabilities. Owner: human.
  https://github.com/eduralph/gramps-testbed-v2/issues/176

## How effectiveness will be judged

- The next brief for a GUI fix (or any fix that could tempt a T3 success
  criterion) should name a C4-achievable observable: "the regression test passes
  with the patch applied" or equivalent. No future bundle should show a misleading
  Check gate-fail because the success criterion required a whole-suite T3 green.
  Watch the next 2–3 GUI-fix cycles.
- If the run-addon-unit.sh exit-1 cause (testbed #176) turns out to be a
  `t3_baseline.py` parsing gap, the fix belongs in the next T3-baseline machinery
  cycle; if it is a real test failure, it becomes a separate bundle. Track at next
  review.

# Act review — 2026-06-20 — cycles considered: all 11 in index (13174, 13268, 13716, 13744, 13864, 13865, 46, 820-build-toolchain-coverage, 820-pluginloading-gate, 8653, glade-setattr); first revalidation run

## What the cycles' records exposed

- **New bundles (issue_13716, issue_820-build-toolchain-coverage) — no pattern.** Both
  are merged-wider with no §10 candidates. Each carries exactly one NEEDS-HUMAN: `V —
  fitness-to-purpose (always-human)` — oracle-by-design. No new process delta warranted.

- **V / C5 / T5 NEEDS-HUMAN recurring — by design, confirmed again.** The act-index
  recurring signals (`needs_human_classes`) show C5 and V appearing in every cycle.
  This is the 4th consecutive review to confirm it is correct system behaviour. No delta.

- **T3-interface baseline cleared (positive maintenance signal).** issue_13716's
  `check-gates.json` reports `T3-interface: green (no failures); baseline now clear (1
  recorded red(s) gone)`. The Glade `__setattr__` fix (issue_glade-setattr) has landed in
  upstream `maintenance/gramps61` and the one previously-recorded smoke red is gone. The
  T3 baseline is naturally shrinking as upstream defects are fixed — no process action
  needed; consistent with the 2026-06-09 (T3 mechanism) Act prediction.

- **First-ever revalidation run — issue_13174 completed, remainder in-progress.**
  `make revalidate` was run before this review per the Act protocol. As of writing,
  issue_13174's `revalidation-2026-06-20.json` is complete; the remaining 10 bundles are
  still running in the background (Docker-backed gates, ~3 min/bundle). The
  issue_13174 delta set:
  - **T1: frozen FAIL → current PASS** (non-gating). Confirms the `_touched_addons`
    gate fix (testbed #158, `engine/conformance/gate.py`) is **live** in the current
    engine. This is the expected stale-recorded-red outcome; no regression.
  - **T2-potfiles: frozen — → current PASS** (gating). The T2-potfiles gate was added
    to the engine after issue_13174 was frozen; it now runs and passes. New gate, not a
    regression.
  - **C4-verify-interface: frozen — → current UNVERIFIABLE** (non-gating). New interface
    gate blocked by uncommitted changes in the gramps-6.1 workspace (environmental). Not
    a regression.
  - **T3-unit: text output reports pass→fail; JSON record reports pass→pass.** A
    discrepancy between the console summary and the written JSON for the same run.
    T3-unit is non-gating. The most likely cause is baseline tree drift (noted in prior
    entries: recorded `detached@674e3b`, workspace has since moved). Needs investigation;
    no gating regression either way (`regression: false` in the JSON). Carried as an open
    item (see Follow-ups).
  - **Overall `regression: false`**: no frozen gating PASS → current FAIL across
    issue_13174.

- **All prior §10 candidates addressed.** Every §10 item in the current index was
  filed or resolved in the two earlier 2026-06-20 Act entries (testbed #158, #159, #176;
  addons-source #50; template change for success-criterion C4-achievability). Nothing
  carried forward requires a new delta here.

## Process deltas

No new process delta is warranted for this review pass. All recurring signals are
oracle-by-design. The §10 candidates are exhausted. The new bundles (13716,
820-build-toolchain-coverage) surface no new pattern.

## Follow-ups routed (not process deltas — work handed to an owner)

- **Open Act item — T3-unit JSON / text discrepancy in revalidation.** The first
  revalidation run (issue_13174) shows the console summary reporting T3-unit pass→fail
  while the written `revalidation-2026-06-20.json` records new=pass, changed=false. Root
  cause is unestablished: could be a race between JSON write and gate completion, a
  display formatting bug in the summary printer, or genuine baseline drift being classified
  differently by the text path vs. the structured path. Non-blocking (T3-unit is
  non-gating; no gating regression), but the discrepancy means the revalidation report
  cannot be read at face value until it is resolved. Owner: human. Next step: compare the
  raw gate output for T3-unit against the baseline manifest for the current worktree state;
  if it is a harness bug, file as a testbed engine issue.

- **Open Act item — complete remaining revalidation JSONs.** 10 of 11 bundles are still
  being revalidated (background task at time of writing). Once the task completes,
  read each `revalidation-2026-06-20.json` for PASS→FAIL deltas on **gating** checks —
  those require routing as regressions. FAIL→PASS deltas (stale recorded reds) should be
  noted so frozen baseline manifests and INTEGRATION.md can be trimmed. Owner: human.
  Next step: after background task finishes, run
  `grep -l '"regression": true' results/*/revalidation-2026-06-20.json` to surface any
  gating regressions quickly.

- **Maintenance — T1 stale recorded reds in frozen bundles (13174, 13268, 13865,
  13876).** Revalidation confirmed T1 is now a FAIL→PASS in issue_13174. The same delta
  is expected in the remaining three core bundles once their revalidation JSONs are
  written. These stale reds in the frozen records are not regressions; they are a natural
  consequence of the gate fix (#158) landing after those bundles were frozen. No process
  action needed; note them at the next review as candidates for baseline shrinkage.

## How effectiveness will be judged

- Running `make revalidate` regularly (e.g., after every gate-fix PR merges to main)
  will keep the stale-recorded-red count visible. At the next review, the T1 FAIL→PASS
  delta should appear across all four core bundles, confirming the gate fix is uniform.
- The T3-unit discrepancy (JSON vs text) should be resolved before revalidation output is
  used to triage any T3 regression. Track at the next review.
- T3-interface baseline shrinkage (one red cleared in issue_13716) is a positive signal;
  if the T3-unit segfault is also fixed upstream in coming cycles, the recorded baseline
  will shrink further. Track alongside testbed #176.

# Act review — 2026-06-20 — cycles considered: 13174, 13268, 13744, 13864, 13865, 13876 (2026-06-20 signoffs); open §10 items from index (issue_46, issue_8653, issue_820-pluginloading-gate)

## What the cycles' records exposed

- **T1 false-positive fires on every core patch that registers `po/POTFILES.skip`
  (5 instances: 13174, 13268, 13865, 13876, 820-review-nits).** Every §4 T1 row
  above reads `T1 ✗ po: no .gpr.py — addon registers via .gpr.py (doc16-addon
  §Structure)` (or `T1 ✗ tests: no .gpr.py` for the addons-source patch). This is
  a **gate bug, not a contribution defect.**
  - Root cause: `_touched_addons()` in `engine/conformance/gate.py:119` uses
    `cand.is_dir()` — it checks whether the leading path-segment of any patch
    b-path resolves to a directory under `../addons-source/`. The `po/` directory
    (addons-source translations) and `tests/` (shared test infra, added by the
    #820 series) both exist as directories there. So any core patch that touches
    `po/POTFILES.skip` or `tests/` paths is misclassified as an addon contribution
    and T1 is run against those non-addon dirs, which have no `*.gpr.py`.
  - This is particularly noisy because the 2026-06-12 Act review **mandated** that
    every core patch adding a new `.py` file must register it in `po/POTFILES.skip`
    — so the gate delta from that review directly triggers this false-positive on
    every subsequent core bundle that complies. Two Act-review deltas collide.
  - Fix: `_touched_addons()` must additionally require
    `any(cand.glob("*.gpr.py"))` before classifying a dir as an addon — a dir
    without any `*.gpr.py` is not an addon, regardless of existence.

- **T3 baseline tree drift (maintenance, not a process gap).** All six June-20
  bundles report `⚠ baseline tree drift: recorded detached@674e3b`. The baseline
  manifests (`engine/baselines/run-unit.json`, etc.) were recorded at commit
  `674e3be80a` and the `maintenance/gramps61` worktree has moved since. The T3
  gate still passes (known reds still match), so no regression is masked — the
  drift is a stale-capture advisory. No process delta; baseline needs re-recording
  via `make preflight` when the worktree is next aligned.

- **Open §10 item — issue_46 runner stderr discarding.** The index flags (issue_46
  §10): the `run-addon-unit.sh` `bash -c` single-quote nesting bug at line 268–269
  caused an exit-2 that was invisible in the bundle's summarized signature. Not
  yet filed as a testbed engine issue. Filing now (see Follow-ups).

- **Open §10 item — issue_8653 run-addon-unit standalone analysis.** The index
  flags a standalone root-cause investigation: "exited 1 / no parsed failures, no
  matching baseline signature" from `run-addon-unit.sh` — cause never established
  (install/setup/all-skipped crash, `t3_baseline.py` parsing blind spot, or
  genuine addon test). Still open; carried below.

- **V / T5 / C5 NEEDS-HUMAN (recurring, by design).** The Act index recurring
  signals (`needs_human_classes`) show V / T5 / C5 in every cycle. These are
  **oracle-by-design** — `check-gates.json` routes them to "reviewer + human
  sign-off" / "human at sign-off" and there is no gate that can close them. No
  process delta warranted; the pattern is correct system behaviour.

## Process deltas

- **Gate (delta warranted):** `_touched_addons()` in
  `engine/conformance/gate.py:113–121` must require the candidate directory to
  contain at least one `*.gpr.py` file before classifying it as an addon target
  for T1/T2 checks. The one-line fix:
  ```python
  if first and first not in found and cand.is_dir() and any(cand.glob("*.gpr.py")):
  ```
  This makes `po/`, `tests/`, `.github/` and other non-addon dirs in
  addons-source invisible to the addon classifier — they have no `*.gpr.py`.
  A matching test change belongs in
  `engine/tests/test_conformance.py` (or a new file).
  *Implementation routed as testbed engine issue (see Follow-ups).*
  (`engine/conformance/gate.py:119`)

## Follow-ups routed (not process deltas — work handed to an owner)

- **Testbed engine issue — T1 false-positive (`_touched_addons` non-addon dirs):**
  the gate bug above is an instance/engine change (`engine/conformance/gate.py`).
  Filed as testbed GH **#158** https://github.com/eduralph/gramps-testbed-v2/issues/158
  Owner: human. Next step: implement the one-liner + test, then re-record any
  now-changed FAIL→N/A revalidation deltas across the affected frozen bundles
  (13174, 13268, 13865, 13876 — all now correctly N/A for T1).

- **Testbed engine issue — issue_46 stderr discarding + `bash -c` nesting in
  `run-addon-unit.sh:268–269`:** an exit-2 from a single-quote nesting bug was
  summarized as an opaque signature, hiding the real cause from the bundle review.
  Fix: persist raw runner stderr in the bundle artifact + move `synth_junit`
  attribution outside the `bash -c` body.
  Filed as testbed GH **#159** https://github.com/eduralph/gramps-testbed-v2/issues/159
  Owner: human.

- **Open Act item — `run-addon-unit.sh` "exited 1 / no parsed failures, no
  matching baseline signature" root-cause:** first flagged in issue_8653 §10,
  carried forward. The cause (install/setup crash, `t3_baseline.py` parsing
  blind spot, or genuine test failure) was never established. Owner: human.
  Next step: run `run-addon-unit.sh` standalone on a clean cycle and trace the
  exit-1 path.

- **Maintenance — T3 baseline re-recording:** run `make preflight` against the
  current `maintenance/gramps61` HEAD to re-anchor the baseline manifests at a
  current commit and clear the drift warning across future bundles. Not a process
  change; a one-time maintenance run. Owner: human.

## How effectiveness will be judged

- The next core bundle that adds a `.py` file (and therefore registers it in
  `po/POTFILES.skip`) should report T1 as **N/A** (core-only change, no addon
  path), not a false-positive FAIL. Watch the next 2 such cycles after the gate
  fix lands.
- If `run-addon-unit.sh` exit-1 analysis surfaces a `t3_baseline.py` parsing gap,
  the fix belongs in the next T3 baseline machinery cycle; if it surfaces a real
  addon test failure, it becomes a separate bundle. Track at next review.

# Act review — 2026-06-19 — cycles considered: cross-cycle token-cost review (no single bundle re-decided; triggered by testbed GH #149)

## What the cycles' records exposed
- **The six model leaves are the engine's only token spend, yet every leaf was pinned
  uniformly to `claude-opus-4-8 --effort high` (planner `xhigh`)** — see the leaf history
  in `pdca.toml` (the 2026-06-14 note that pinned builder/reviewer/signoff/publisher/act
  to opus/high). That decision fixed a real problem (an un-versioned `~/.claude` default
  left the implementer weaker than the interactive session) but over-corrected: it set the
  *strongest* tier everywhere, including the human-in-the-loop leaves whose model output is
  only an assist (sign-off, publisher, act) and the advisory reviewer. `--effort` in
  particular is a direct thinking-token multiplier applied on every leaf call across a batch.

## Process deltas
- Leaf config: retier `[leaves.*]` by leverage, not uniformly.            (`pdca.toml:91-136`)
  - planner — opus `xhigh`  — UNCHANGED (a thin brief poisons Do + Check; highest leverage).
  - builder — opus `high`   — UNCHANGED (writes the patch; correctness-critical).
  - reviewer — opus/high → **Sonnet/medium** (codex still not on PATH, so the documented
    same-vendor fallback; restore codex when available — the decorrelation ideal).
  - signoff  — opus/high → **Sonnet/medium** (interactive; the model only assists §6 clearing).
  - publisher — opus/high → **Haiku/low** (drafts commit-msg + PR prose; mechanics stay deterministic).
  - act       — opus/high → **Sonnet/medium** (cross-cycle prose synthesis).

## Follow-ups routed (not process deltas — work handed to an owner)
- Testbed/driver issue: testbed GH #149 (this delta implements it) ·
  close-disposition fast path integrated from pdca-harness #60 (v0.21.0) ·
  pdca-harness GH #62 (brief Disposition-hint vocabulary alignment, open).

## How effectiveness will be judged
- Watch the next K cycles for a quality regression traceable to the downgrade: a Check
  sign-off that misses something the advisory review should have caught, or a publisher
  draft (commit-msg / pr-description) that needs heavier human rework than before. If one
  appears, raise that specific leaf back a tier — do not blanket-revert to uniform opus.

# Act review — 2026-06-12 — cycles considered: glade-setattr (PR #2356 review feedback; cross-ref new-core-`.py` POTFILES omission across all such bundles)

## What the cycles' records exposed
- **A documented doc-16 MUST with no owner in the cycle — surfaced by a maintainer at
  review, not by any gate (issue_glade-setattr / gramps PR #2356).** Nick-Hall asked
  for the new test file to be listed in `po/POTFILES.{in,skip}`. The rule is explicit
  and sourced: *"When a core PR adds or removes a `.py` file — MUST update
  `po/POTFILES.in` (translatable strings) or `po/POTFILES.skip` (none)"*
  (`wiki/pages/05 - Gramps development/16-guidelines.md:97-100`, citing
  `gramps/AGENTS.md §Translation Files`). It is not exotic — it simply has no encoding
  in our T1–T4 ladder, no prompt in the brief template, and no builder checklist item.
- **The omission fell through every beat.** Plan: the brief named the new test file but
  never stated the POTFILES obligation. Do: the builder reads `brief.md` only and has no
  independent doc-16 checklist, so the file shipped unregistered. Check/gates: T1 is
  addon-only; `T2-shape` checks file *shape* (GPL header, `print()`); `T4-contribution`
  checks the commit/PR *wrapper* (doc 16 §Commit messages / §Contributor workflow) —
  none implement doc 16 §Translation Files. New-file→manifest registration falls in the
  gap **between T2 (shape) and T4 (wrapper)**; neither owns it. C4-verify runs only the
  bundle's one named test.
- **The one upstream test that touches POTFILES would not have caught it either.**
  `gramps/po/test/po_test.py` only asserts membership for files that *contain*
  translatable-string markers; a no-`_()` test file like `glade_test.py` never enters
  its `found` branch. And it runs inside `T3-unit`, which is advisory and baseline-red
  (the segfault), so it informs nothing today regardless.
- **Systemic, not a one-off.** Every prior core bundle that adds a `.py` file has the
  same missing POTFILES hunk — `13636` (uimanager_test.py), `8653`, `8796`, `11589`,
  `11786`, `13205`, `headless-ut-segfault`. `issue_glade-setattr` is the *only* bundle
  whose `patch.diff` now carries a POTFILES hunk, and only because it was added by hand
  after Nick-Hall's review (see follow-up). The addon bundle
  (`addon-tests-init-py-gramps60`) is out of scope — addons carry their own translation
  handling, not core `po/`.

## Process deltas (candidates — routed for engineering, NOT applied here)
- Gate (candidate, highest-value): add a **bundle-scoped, deterministic** check — for a
  *core* bundle whose `patch.diff` adds a `.py` file, assert that file appears in
  `po/POTFILES.in` **or** `po/POTFILES.skip` (and, on a deletion, in neither). Directly
  implements doc 16:99-100, is **target-aware** (core-only; N/A for addon bundles), and
  needs **no Docker** so it runs on this host. Natural home: extend `t2_shape.py` (it
  already walks the patch's touched core `.py` files) or add a sibling
  `t2`-class file-registration checker.   (`engine/conformance/t2_shape.py` / new
  `engine/conformance/`; cite doc 16 §Translation Files by section per the anchor rule)
- Spec template (candidate): the brief's **Test file** / new-file guidance gains a line —
  *a new core source file MUST name its `POTFILES.{in,skip}` placement* — so the
  obligation is surfaced at Plan and the builder (which reads only the brief) is told to
  register it.   (`templates/brief.md.tpl`)
- Agent skill — builder (candidate): when a fix **adds a new core `.py`**, the builder
  MUST add the corresponding `POTFILES.{in,skip}` line in the same patch (`.skip` when
  the file has no translatable strings — e.g. tests).   (`.claude/agents/builder.md`)

## Follow-ups routed (not process deltas — work handed to an owner)
- **Project under test (core) — already done:** `gramps/gui/test/glade_test.py`
  registered in `po/POTFILES.skip`; pushed to PR #2356 (commit `fedd265159`,
  `fix/bug-glade-setattr-glade-setattr-name-mangling`). The bundle's `patch.diff` was
  synced to match. No open code work; recorded for trace.   (gramps PR #2356)
- **Back-fill question (open Act item):** the seven prior core bundles above shipped /
  published without their POTFILES entry. For any whose upstream PR is still open,
  the same one-line `.skip`/`.in` addition is owed. Owner: human — audit the open PRs
  (13636, 8653, 8796, 11589, 11786, 13205, headless-ut-segfault) and add where merged
  state allows. Next step: list which are still open.
- **Testbed/driver issue:** the file-registration gate + brief/builder lines are
  **generic** doc-16 conformance (the POTFILES MUST is core gramps, but the *pattern*
  "new file → repo manifest" recurs) → candidate to feed the `pdca-harness` template
  per the template-vs-instance boundary. Owner: human (template work).

## How effectiveness will be judged
- Over the next ~3 cycles that **add a new core `.py`**: the new gate should fail the
  bundle at Check (not a maintainer at review) when the file is absent from
  `POTFILES.{in,skip}`, and build-notes should show the registration line in the same
  patch. No future PR should draw a "list this in POTFILES" review comment. Once the
  gate runs clean across those cycles, consider promoting it from advisory to gating
  (it is a hard MUST, deterministic, and Docker-free).

# Act review — 2026-06-09 — cycles considered: 8796 publish (publish-field-parse failure class; cross-ref #23a/#23b)

## What the cycles' records exposed
- **A recurring publish-failure class, not three unrelated bugs.** `pdca publish` is a
  deterministic step that turns the human-authored, free-prose `Repo + branch target`
  brief field plus git/gh invocations into exact commands — and each past failure was a
  real input shape it didn't anticipate, surfacing as a cryptic git/gh error *mid-run*
  (after artifacts were drafted) and re-diagnosed from scratch. Prior: #23a (commit
  must stage patch-ADDED files), #23b (fork PR `--head` must be `OWNER:BRANCH`). This
  cycle (issue 8796 publish): `_resolve_target` used everything after `@` as the base
  ref, so the field's trailing annotation reached `git checkout -B … upstream/<base>`
  → `fatal: 'upstream/maintenance/gramps61 (core fix; …)' is not a commit`. The
  **repo_spec half of the same field** was the same bug latent — `gramps (core)`,
  ``gramps (fork `eduralph/gramps`)``, bare `addons-source` would all fail `gh --repo`;
  only saved so far because every *published* bundle happened to use a clean OWNER/REPO.

## Process deltas (applied this cycle)
- Gates (applied): `_resolve_target` now takes the first token of BOTH halves (strips
  markdown backticks / trailing prose) and maps a repo shorthand to canonical
  OWNER/REPO via a new `[publisher.repo_aliases]`.  (`src/pdca_harness/publish.py`
  `_resolve_target`/`_first_token`/`_canonical_repo`; `pdca.toml [publisher.repo_aliases]`;
  `src/pdca_harness/config.py` `repo_aliases`)
- Gates (applied): publish now **preflights** the parsed target — `git rev-parse
  --verify upstream/<base>` + `gh repo view <repo>` — *before any mutation*, so a
  mis-parsed field fails fast with a named-field message instead of a cryptic mid-run
  git/gh error. This is the generalizable guard for the whole class.
  (`src/pdca_harness/publish.py` `_preflight`)
- Tests: `test_resolve_target_normalizes_repo_and_branch` (both annotation forms ×
  repo aliases) + `test_preflight_rejects_unresolvable_target`.  (`tests/test_publish_slice.py`)

## Process deltas (candidate — routed for engineering, NOT applied)
- Spec template (candidate): make the brief's `Repo + branch target` a **structured**
  field — separate machine `repo:` / `branch:` keys (or a constrained `OWNER/REPO@ref`
  grammar) — so there is nothing to mis-parse and annotation lives in a free-text note.
  Removes the root cause rather than hardening the parser around it.  (`templates/brief.md.tpl`;
  `src/pdca_harness/publish.py _resolve_target`; pdca-harness template feedback)

## Follow-ups routed (not process deltas — work handed to an owner)
- **Template feedback:** the parse-hardening + preflight + structured-field idea are
  pdca-harness-template-relevant (the publish mechanic is shared) — fold into the next
  template catch-up. Owner: human.

## How effectiveness will be judged
- No future publish should fail with a cryptic git/gh error from a brief-field shape:
  a bad parse now fails at preflight with a clear, field-named message. Watch the next
  publishes of the prose-target bundles (12576, 13636, 11589, 46). If the structured
  field lands, `repo_aliases` + the token-stripping can later retire.

# Act review — 2026-06-09 — cycles considered: 8796 (T3 mechanism; cross-ref headless-ut-segfault, glade-setattr)

## What the cycles' records exposed
- **The advisory T3 gate masked, not informed, across issue_8796's 4 iterations.**
  C4 was green from iter-3 (the `views_to_show([])` fix is verified, no collateral
  delta), yet sign-off bounced the bundle to Do four times over T3 reds that are
  **pre-existing tree defects, not patch-induced** — proven by the T3 delta set
  being byte-identical (`test_imp_3_4` ×7, `SmokeTest.setUpClass`) across iterations
  whose test plumbing changed completely. Iterating Do cannot clear a red Do did not
  cause; the loop was structural.
- **`t3_baseline.classify()` is blind to tests that did not run.** It diffs observed
  failing ids vs `known_failures` with no executed/expected-count check
  (`engine/conformance/t3_baseline.py:116-156`). A known red that collapses a subtree
  at `setUpClass`/import (the segfault; the Glade crash) emits one failing id; record
  it and the verdict is "baseline" (exit 0) while every test behind it silently never
  ran — a *new* regression there is fully masked.
- **T3 has no pinned substrate.** `run-unit.sh`/`run-interface.sh` mount the developer
  working clone `../gramps` (today a fix branch), not the `gramps-$leg` upstream
  worktree C4-verify uses; the manifest records no captured commit. So a T3 delta is
  not attributable (clone drift vs patch) and a stale baseline is undetectable.
- **`merged-wider` ≠ in upstream.** `issue_glade-setattr` and
  `issue_headless-ut-segfault` are recorded `merged-wider`, but neither fix is present
  in `upstream/maintenance/gramps61` @ `674e3be80a` (the Glade `__setattr__` bug is
  still verbatim at `gramps/gui/glade.py:64-69`). The bundle outcome overstates the
  upstream state the T3 gate validates against.

## Process deltas (candidates — routed for engineering, NOT applied here)
- Triage principle (ruleset): **a red that prevents other tests from running belongs
  on the essential line (`engine/essential-fixes.tsv`), never in `known_failures`** —
  parking a harness-blocker in the baseline masks its collapsed subtree. Only *leaf*
  reds (one test, runs-but-asserts-false) are baseline-eligible.  (docs/INTEGRATION.md §3)
- Gate: add an **executed-count invariant** to `classify()` — record `expected_total`
  (or per-class counts) and treat *fewer executed than baseline* as a delta even when
  the failing-id set matches. Highest-value change; closes the subtree-collapse blind
  spot.  (`engine/conformance/t3_baseline.py:116-156`)
- Gate: **pin T3 to the `gramps-$leg` worktree** like C4-verify, and stamp the manifest
  with the captured upstream commit; warn when the live tree ≠ that commit.
  (`engine/scripts/ubuntu/run-{unit,interface}.sh`; baseline manifest schema)
- Gate: **guard `--update`** to accept only the pinned, unmodified tree; add per-id
  `cause`+`tracking`; enforce shrink-on-clear (fail if a recorded red cleared and was
  not removed).  (`engine/conformance/t3_baseline.py:185`)
- Ruleset: narrowest-possible `run_level_signatures`, prefer per-test ids over regexes.

## Follow-ups routed (not process deltas — work handed to an owner)
- **Bundle-outcome integrity:** `issue_glade-setattr` / `issue_headless-ut-segfault`
  say `merged-wider` but the fixes are not in `upstream/maintenance/gramps61` tip.
  Verify the upstream PR merge state and reconcile the recorded outcome. Owner: human.
- **Un-mask the smoke subtree:** route the Glade `__setattr__` fix onto
  `engine/essential-fixes.tsv` (alongside the segfault fix) so `T3-interface` actually
  executes the smoke tests instead of collapsing at `setUpClass`. Owner: human (engine).
- **C4/T3 substrate asymmetry → testbed issue:** wire the T3 whole-suite runners to the
  pinned worktree + essential fallback (the seam `run-verify.sh` already has), a
  prerequisite for ever re-promoting T3 to gating. Owner: human (engine; cross-ref
  testbed issue #7).

## How effectiveness will be judged
- Future whole-suite reds should be **attributable** (pinned substrate) and a collapsed
  subtree should raise as a *delta*, not pass as "baseline." Sign-off should stop
  routing all-human/environmental §6 sets back to Do (cross-ref the iterate-to-Do
  guard candidate). Watch the next ~3 cycles for a repeat of the 8796 loop.

# Act review — 2026-06-08 — cycles considered: 8653

## What the cycles' records exposed
- **A test validated a *copy* of production, not production — a *planning-phase* miss
  (issue_8653, T5(a) NEEDS-HUMAN).** The fix is correct, but its test drives
  `connection_search.search_connections`, a hand-port of the gramplet's BFS loop, while
  the real loop in `DeepConnectionsGramplet.main()` is never exercised (only the shared
  `get_relatives` is). `build-notes.md:79` calls it openly *"a headless mirror of the
  `main()` BFS loop"*, and §6 records the builder **considered** testing the gramplet
  directly and rejected it. So this was a disclosed, deliberate trade-off — not
  sloppiness — and the deterministic C4 gate went green on the copy. Only the human's
  T5 caught it.
- **Root cause is upstream of Do — an instruction interaction, not a one-off brief.**
  (a) Plan is *correctly* forbidden from naming a mechanism (principles §3.1), so the
  brief could only say "extract a GUI-free, testable seam" (outcome) and not prescribe
  the dedup mechanism. (b) `builder.md` told Do to "extract the logic into an
  import-light module and test *that*" — which a parallel copy satisfies literally when
  `main()`'s loop can't be made import-light without restructuring. (c) **Nothing
  required the test to exercise the production path.** A green test of a copy met every
  written instruction. Companion fear T5(b) (`default_person is None`) was **not live** —
  `main():334` guards it before the only call site (`:439`); flagged only because
  `main()` was absent from the review bundle.

## Process deltas
- **Reference (applied):** new principle **§3.4 — test the production path**: when a fix
  needs a testable seam, the success evidence MUST exercise the production path
  (production routes through the same extracted unit the test drives); a parallel
  re-implementation that mirrors production is not acceptable evidence. Stated as an
  *outcome*, so it composes with §3.1 (mechanism stays with Do).   (`docs/principles.md` §3.4)
- **Spec template (applied):** brief **Test file** field now reminds that the test must
  drive the production path, not a parallel copy (§3.4).   (`templates/brief.md.tpl` Test file)
- **Agent skill — builder (applied):** the "extract import-light and test that" guidance
  now requires production to *route through* the extracted module; if a path can't be
  made import-light without restructuring, restructure (shared generator / callback)
  rather than reimplementing in parallel.   (`.claude/agents/builder.md` §running-tests)
- **Agent skill — planner (applied):** Plan-exit gate gains a binary — *does Success/Scope
  force the test to drive the production path (no parallel copy)?*   (`.claude/agents/planner.md` Plan-exit gate)
- **Model/effort (applied):** the Plan leaf — the highest-leverage beat — is pinned to
  the strongest model + raised effort rather than inheriting an un-versioned machine
  default: `--model claude-opus-4-8 --effort xhigh` in the planner leaf spawn.
  (`pdca.toml` `[leaves.planner].argv`)

## Follow-ups routed (not process deltas — work handed to an owner)
- **Instance rebuild (issue_8653) — iterate the Do leaf, not a sign-off hand-patch:**
  with the §3.4-corrected brief, dedupe via control inversion (one `search_connections`
  events generator that `main()` consumes and the test drives headless), preserving the
  `default_person` guard. Owner: human (re-run Do). The rule-2 label-loss question
  (C5/T5-d) is a separate fidelity decision, untouched here.
- **Testbed/driver issue:** §3.4 + the planner/builder/template/leaf changes are
  **generic** → candidates to feed back to the `pdca-harness` template per the
  template-vs-instance boundary. Owner: human (template work).

## How effectiveness will be judged
- Over the next ~3 **seam-extraction** cycles: the Plan-exit gate should reject a brief
  whose test could pass against a copy; build-notes should show production routing
  through the extracted unit; and no T5 "test validates a copy" item should reach the
  human. Watch the next K cycles.
- Track whether the Plan-leaf model/effort bump lowers the T5/Check NEEDS-HUMAN rate —
  the empirical test of Track B; revisit at the next review.

# Act review — 2026-06-07 — cycles considered: headless-ut-segfault (+ decision-point cross-ref 8653, 12576)

## What the cycles' records exposed
- **A symptom-guard shipped where cause-removal was correct — a *planning-phase*
  miss (issue_headless-ut-segfault).** The fix (gramps PR #2357) guarded a class-body
  Gtk widget construction with `has_display()` instead of removing the import-time
  cause (compute `linkcolor` lazily in `__init__`). Maintainer Nick-Hall rejected it
  on review — *"using `has_display` in GUI code designed to run with a display just
  looks wrong"* — costing a rework round-trip. Root cause is **upstream of Do**: the
  brief's Scope seated a *mechanism* ("reuse the existing `has_display()`"), so no
  downstream gate could recover the right fix shape. Then Do mis-priced the better
  alternative: `results/issue_headless-ut-segfault/build-notes.md:50-56` rejected
  cause-removal as *"heavier … touches every `self.linkcolor` reader"* — **false**;
  the accepted rework is one class attr reassigned in `__init__`, touching no readers.
  An *unquantified* "heavier" discarded the cheaper, better fix. Recorded as testbed
  **issue #15**.
- **Evidence basis (honest, per "don't force a delta").** n=1 *failure* but n=3
  *decision-point*: issue_8653 and issue_12576 hit the same symptom-vs-cause fork and
  chose **correctly**, with quantified reasoning (their `build-notes.md` "alternatives
  ruled out"). So the fork recurs (a heuristic generalises) while only one cycle
  shipped the wrong side. Only **import-safety** earns a hard gate today; everything
  else stays reference-layer until a cycle shows it missed.

## Process deltas
- **Reference (applied):** new sourced invariant catalogue + solution-design
  principles so Plan states the *invariant to restore*, not a mechanism, with a
  citation Do/Check can lean on.                          (`docs/principles.md`, new)
- **Spec template (applied):** brief gains an **`Invariant to restore`** field (stated
  over the defect category, self-test "guardable by one module?") and the **Scope**
  field must not name a probe/guard/helper.    (`templates/brief.md.tpl:11,16-19`)
- **Agent skill — planner (applied):** minimalism-is-scoped qualifier (principle 1.2)
  + a category-gated **Plan-exit gate** (Scope names no mechanism; invariant not
  satisfiable by guarding one module).         (`.claude/agents/planner.md` §Solution-design discipline)
- **Agent skill — reviewer (applied, backstop):** C5 gains a concrete **symptom-guard
  smell-test** — a capability probe/guard inside code meant to run *with* that
  capability → C5 NEEDS-HUMAN asking if the cause is removable. The downstream twin of
  the Plan-exit gate.                          (`.claude/agents/reviewer.md` §C5 symptom-guard smell-test)
- **Agent skill — builder (applied):** rejecting an alternative on cost MUST show a
  diff sketch / line count, never an adjective; a named invariant outranks
  cost-vs-minimalism (principle 2).            (`.claude/agents/builder.md` §Output)
- **Scope discipline:** only **import-safety** is hard-gated (real shipped failure);
  the rest of the catalogue is reference-layer, promoted on evidence (`docs/principles.md` §8).

## Follow-ups routed (not process deltas — work handed to an owner)
- **Project under test (core) — already reworked:** gramps PR #2357 was updated to
  lazy-compute `linkcolor` and drop the `has_display` import (the human's rework after
  the maintainer objection). No open code work; recorded for trace.   (gramps PR #2357)
- **Testbed/driver issue:** five framework assets changed here are **generic** → fed
  back to the `pdca-harness` template per the template-vs-instance boundary.
  (`docs/template-feedback.md` rows #25–#29). Owner: human (template work).

## How effectiveness will be judged
- Over the next ~3 **guard-shaped** cycles (import-safety / lifecycle / structural):
  the **Plan-exit gate** should stop a mechanism-in-Scope brief; build-notes should
  **quantify** any rejected cause-removal; and the reviewer's **C5 smell-test** should
  catch any guard that still reaches Check — before upstream review, not at it.
- If the Plan-exit gate fires cleanly with no false positives across those cycles,
  consider making it unconditional (drop the category gate). Track whether any new
  symptom-guard reaches a maintainer.

# Act review — 2026-06-06 — cycles considered: 11589, 11786, 12576, 13205, 13636

## What the cycles' records exposed
- **Recurring NEEDS-HUMAN class — T3 whole-suite baseline re-attribution (all 5
  cycles).** The auto-detector reported "no recurring signal", but reading the §6/§10
  records directly, every cycle's three advisory T3 gates fail with the *same*
  signature, and every cycle that produces a §6 item asking the human to confirm
  "pre-existing baseline vs regression":
  - `T3-unit` core suite — `Trace/breakpoint trap (core dumped)` (11589, 11786, 12576,
    13205, 13636).
  - `T3-addon-unit` — `pip install … 3 failure(s)` (11589, 12576, 13205, 13636).
  - `T3-interface` smoke — `_ErrorHolder` (11589, 12576, 13205, 13636).
- **The signature is not noise — issue_13636 diagnosed two of the three causes**
  (SUMMARY §6/§10): the `_ErrorHolder` smoke red is a Dashboard/gramplet startup crash
  (`AttributeError: Ad-hoc attribute _Glade__dirname is not permitted`, a core bug);
  the pip-install ×3 red is `QuiltView`/`CombinedView` shipping `gramps_target_version`
  "6.0", rejected by core 6.1.0-beta1 (addon-maintenance). The core-unit segfault is a
  third, still-unisolated defect. Because the baseline is never *recorded*, the reviewer
  + human re-diagnose it from zero each cycle — recurring toil a record + a baseline
  diff can remove without weakening regression detection (a *new* failure type still
  surfaces). `pdca.toml:107-110` already anticipates re-gating "once green-baseline".
- The other every-cycle §6 entries — **T5 Judgment** and **V fitness-to-purpose** — are
  always-human by oracle design (`check-gates.json` oracles "reviewer + human sign-off"
  / "human at sign-off"). These are intended, not a gap; **no delta warranted** for them.

## Process deltas
- Spec/ruleset (applied): recorded the **Known T3 baseline signature** + its three
  diagnosed causes as an authoritative comparison point, so T3 attribution becomes
  "matches recorded baseline / is this new?" rather than a from-scratch §6 diagnosis
  each cycle.                                  (`docs/INTEGRATION.md` §3, new bullet after `:127`)
- Gates (proposed, routed — engineering, not applied here): have the T3 runners emit a
  structured pass/fail set and the gate **diff against a checked-in baseline manifest**
  of the target branch's known reds, so a matching baseline auto-resolves and only the
  *delta* (a new failure type) raises §6.     (testbed issue #7; `pdca.toml:107-142`; `engine/scripts/ubuntu/run-{unit,addon-unit,interface}.sh`)
- Ruleset (candidate, not applied — single-cycle, needs a doc-16 call): whether the
  `T2-shape` GPL-header MUST should **exempt 0-byte package `__init__.py` markers**, or
  whether the marker should carry a header (11589 §10).   (testbed issue #6, folded in; `engine/conformance/t2_shape.py`; doc 16 §Coding style)

## Follow-ups routed (not process deltas — work handed to an owner)
- **Another bug (project under test — core):** Dashboard/gramplet startup crash
  `AttributeError: Ad-hoc attribute _Glade__dirname is not permitted` (the recurring
  `T3-interface` `_ErrorHolder` baseline) → **file in Mantis**. Owner: human (Mantis
  login required, host-side per INTEGRATION §1). Next step: file + record the id here.
- ~~**Another bug (addon-maintenance — addons-source):** `QuiltView` and `CombinedView`
  ship `gramps_target_version` "6.0" … → bump `target_version` on both addons.~~
  **CORRECTED (this routing was wrong).** The addons are *correct per-branch* — "6.0"
  on `maintenance/gramps60`, "6.1" on `maintenance/gramps61` (fixes cherry-pick
  forward). The `T3-addon-unit` red was a **testbed matrix gap**: it ran the gramps60
  addons against 6.1 core (a version mismatch core 6.1 rejects by exact-minor match),
  not an addon defect. Fixed by making the addon gates a per-version matrix (each
  branch × its matching core) → **testbed issue #10**. No addon code change.
- **Open Act item:** isolate the `T3-unit` `Trace/breakpoint trap (core dumped)`
  segfault, then file as a core bug. Owner: human. Next step: diagnose on an unmodified
  `maintenance/gramps61` checkout; revisit next review.
- **Testbed/driver issue:** the gate baseline-diff above is an `engine/**` + `pdca.toml`
  change → filed as **testbed GitHub issue #7** (instance/engine, per
  `docs/template-feedback.md`): T3 whole-suite gates diff against a recorded baseline
  manifest instead of re-raising the same NEEDS-HUMAN each cycle. Owner: human (engine work).
- **Open Act item (11589 §10):** decide the `T2-shape` 0-byte-`__init__.py` question
  above (header vs gate exemption); also check `maintenance/gramps60`
  `PluginManager/tests/__init__.py`. Folded into **testbed GitHub issue #6** (vendored
  doc-16 conformance re-anchoring) as an explicit checklist item, since the decision
  must be pinned to the right vendored guideline. Owner: human. Revisit next review.

## How effectiveness will be judged
- The next cycles should **not** recreate the from-scratch T3 baseline-attribution §6
  items: with the recorded signature, the reviewer should report T3 reds as "matches
  recorded baseline" and reserve §6 for a *new* failure type. Watch the next ~3 cycles.
- As each underlying defect is fixed, its T3 gate should be re-promoted to `gating`
  (`pdca.toml:107-110`); track baseline shrinkage across reviews.
