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
