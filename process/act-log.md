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
- Testbed/driver issue: testbed GH issue #N | template-feedback.md entry  (link)
- Other open Act item: <item> → owner <who>, next step <…>

## How effectiveness will be judged
- The next Do phases should not recreate <specific issue>. Watch the next K cycles.
-->

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
