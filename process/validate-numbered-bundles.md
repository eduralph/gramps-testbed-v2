# Revalidation — numbered (older-process) bundles

> **Date:** 2026-06-07 · **By:** revalidation pass (Claude), reviewed WITH the human.
> **Why:** the numbered bundles (`8653, 11589, 11786, 12576, 13205, 13636`) were
> Planned/Checked under an *older* engine + ruleset and frozen COMPLETE before several
> process deltas landed. This pass re-runs the full Check (deterministic gates **and** a
> decorrelated reviewer) against the **current** process to confirm the frozen
> dispositions still hold. It does **not** re-decide §9 — that stays the human's.

## What changed since these bundles froze

Frozen at `6ad140c` (2026-06-06 12:53). Process deltas after that commit:

| Commit | Delta | Why it matters to these bundles |
|---|---|---|
| `68a54bb` | T3 whole-suite **baseline-manifest diffing** (#7) | The frozen `check-gates.json` records *raw* T3 failures (`Trace/breakpoint trap`, smoke `setUpClass`, pip-install). Those are environmental, not defects in the fix; the new engine reports them as `[baseline]`/`[delta]`. |
| `089d09c` | Addon test **version matrix** (gramps60 × 6.0, gramps61 × 6.1) | The old "addon pip-install 3 failures" T3 red was a matrix gap, not an addon defect. |
| `d864e9f` | C4-verify reverts patch-added files by `rm` (#5) | Affects red-pass correctness for patches that add prod files. |
| `0f06e14` | Conformance cites doc 16 **by section**, core/addon by target (#6) | T1/T2/T4 citations. |
| `2a9720b` | **Solution-design discipline** — brief states the *invariant*, not the mechanism (`process/principles.md`; C5 symptom-guard smell-test) | The judgment bar these briefs are now held to. Added *after* even the slug bundles, so it post-dates all of these. |

## Method

- **Patch-applies (read-only):** `git apply --check` each `patch.diff` against its current
  target worktree (`gramps-6.1` for core, `addons-source-6.0` for addons).
- **C4-verify (Docker, authoritative):** re-ran `engine/scripts/ubuntu/run-verify.sh`
  per bundle against the current tree (core: primary `gramps`; addons: the 6.0/6.1
  matrix). The repos were clean before and after; the primary `gramps` branch was never
  changed; three empty `__init__.py` left by the runner were cleaned up.
- **Conformance (T1/T2/T4):** re-ran `engine/conformance/gate.py` per bundle.
- **Reviewer (decorrelated):** one `reviewer` subagent per bundle, fed only
  `{patch.diff, brief.md, check-gates.json}` (never `build-notes.md`), applying
  `process/principles.md` incl. the C5 symptom-guard smell-test.

## Upstream re-validation (2026-06-07, the faithful target)

> The first run below used the **forks'** checkouts (the primary `gramps` on its
> in-flight segfault branch for core; stale fork worktrees for addons). That was not
> faithful to the contribution target. This section re-runs against **`upstream/
> maintenance/gramps6{0,1}`** (freshly fetched), which is the default test target going
> forward: validate on upstream first; fall back to a local *essential* line (upstream +
> harness-enabling fixes) only when a bundle fails on upstream, and record the dependency.

| Bundle | Applies to upstream | C4-verify vs upstream | Verdict |
|---|---|---|---|
| `11786` libpersonview | ✅ | **FAIL** — `Gtk-ERROR: Can't create a GtkStyleContext` core dump | **NEEDS-ESSENTIAL → segfault** |
| `12576` date.py | ✅ | PASS | holds on upstream |
| `13205` mergecitations | ✅ | PASS (weak `ImportError` red) | holds on upstream |
| `13636` uimanager | ✅ | PASS | holds on upstream |
| `8653` DeepConnections | ✅ | PASS (6.0 + 6.1) | holds on upstream |
| `11589` PluginManager | ✅ | PASS (6.0 + 6.1) | holds on upstream |

**Empirically-derived essential set = `{segfault}`.** Only `11786` fails on clean
upstream, and only because its test's import chain hits the pre-fix `LinkTag` widget
(`issue_headless-ut-segfault`). The other five are independently valid against current
upstream; all six apply cleanly (no rebase needed). `11786`'s dependency is recorded in
`results/issue_11786/VALIDATION.md`.

## Result — all six HOLD (fork-based first pass, superseded by the upstream section above)

Every bundle was frozen as **accept ("merged-wider")** by Eduard (2026-06-05/06).
All six revalidate; **none** trips the new C5 symptom-guard discipline (each fix
removes/transforms a cause rather than guarding a capability).

| Bundle | Target | Patch applies | C4-verify (re-run, current engine) | Frozen C4 | Reviewer | Verdict |
|---|---|---|---|---|---|---|
| `11786` libpersonview tag-cache | core gramps61 | ✅ | **PASS** | **FAIL** | HOLDS-WITH-NOTES | **HOLDS** — frozen FAIL was stale |
| `12576` date.py approx-date | core gramps61 | ✅ | PASS | PASS | HOLDS-WITH-NOTES | HOLDS |
| `13205` mergecitations | core gramps61 | ✅ | PASS (weak red) | PASS | HOLDS-WITH-NOTES | HOLDS — test-quality note |
| `13636` uimanager None-guard | core gramps61 | ✅ | PASS | PASS | HOLDS-WITH-NOTES | HOLDS |
| `8653` DeepConnections | addon g60 (×6.0,6.1) | ✅ | PASS (both legs) | PASS | HOLDS-WITH-NOTES | HOLDS |
| `11589` PluginManager | addon g60 (×6.0,6.1) | ✅ | PASS (both legs) | PASS | HOLDS-WITH-NOTES | HOLDS |

(`8796` is a SKIP — never briefed, state UNPLANNED. Out of scope.)

### Headline

The numbered bundles' frozen "failures" were **stale engine/dependency artifacts, not
defects.** The clearest case is **11786**: its frozen `C4-verify green-with-fix=FAIL`
was a headless GTK-import crash — the test imports `libpersonview` → `listview` →
pageview → `grampletbar` → `grampletpane`, whose `LinkTag` class body built a `Gtk.Label`
at import (`Gtk-ERROR: Can't create a GtkStyleContext without a display connection`,
SIGTRAP). The `issue_headless-ut-segfault` fix (lazy `LinkTag.linkcolor`, `f4f94f34db`)
removes that; on the current tree C4-verify is `green-with-fix=PASS / red-without-fix=PASS`.

**This was proven, not assumed** — and distinguished from "we redefined C4" (the gate
script did change 106 lines since the freeze). Re-running 11786's C4-verify with the
**current gate** against the tree **without** the segfault fix (`f4f94f34db^`) reproduces
the frozen result exactly (`green-with-fix=FAIL`, same `Gtk-ERROR` core dump). So the
flip is the **dependency fix in the tree**, not the gate change. **Caveat:** that fix is
**unmerged** — it is not in clean `maintenance/gramps61` (11786's target), so 11786's
test only runs once `issue_headless-ut-segfault` lands there (a merge-order dependency;
see `results/issue_11786/VALIDATION.md`). All the raw T3 reds across the bundles are
likewise environmental (now baseline-diffed and matrix-split).

## Per-bundle notes (open items for the human; advisory)

- **`11786`** — HOLDS. The frozen `check-gates.json` / `SUMMARY.md` still record the
  stale `C4 FAIL`; the in-bundle `VALIDATION.md` records the green re-run so the frozen
  artifact is not mistaken later. Fix is a correct cause-removal (invalidate the
  `(tag_handle,"TAG_NAME")` cache entry on `tag-update`). No action needed beyond noting
  provenance.
- **`13205`** — HOLDS, but its regression test's **red is an `ImportError`**, not a
  behavioural red: with the production reverted the test fails because it imports the
  patched helper `citation_handles_of_source`, not because it reproduces the
  merge-over-non-Citation-backlink bug. C4's *contract* passes, but the test does not
  prove it catches the bug. Reviewer also flagged the brief **seated a mechanism**
  (named a new module `mergecitationslib.py` the builder didn't use) and a **test-path
  drift**. Flagged in the bundle's `VALIDATION.md` as a candidate for `iterate-do`
  (strengthen the red) — the human decides.
- **`8653`** — HOLDS-WITH-NOTES. Reviewer raised a latent i18n subtlety (`_("self")`
  vs literal `"self"`) that is **pre-existing and out of scope**, and the
  POSSIBLY-FIXED C2 question (BFS cache may already mask some routes). C4 green/red both
  pass on both matrix legs. Pre-existing T1/T2 advisory fails (folder≠gpr-id, gpr GPL
  header) are not patch-introduced.
- **`11589`** — HOLDS-WITH-NOTES. Reviewer: Scope over-specified the helper mechanism
  (§3.1 drift, but the named mechanism was in fact correct); fitness question on
  whether sibling-detection matches real FilterRules packaging (by-design Validation
  NEEDS-HUMAN). C4 passes both legs.
- **`12576`** — HOLDS-WITH-NOTES. The POSSIBLY-FIXED→verify obligation was met and
  independently re-confirmed: the original exact-date fix is present; the *residual*
  approximate-date defect (`2022/03/00` → fabricated precise Persian day) reproduces
  and is fixed. Fitness-to-purpose (unknown-day preservation) is a by-design human call.
- **`13636`** — HOLDS-WITH-NOTES. The `None`-guard is a legitimate runtime fix for a
  window-teardown race — explicitly **not** the import-safety category; module import is
  side-effect-free and the test stubs `gi` for headless. By-design Validation
  NEEDS-HUMAN for a race validated only at the unit layer.

## Recurring drift (Act material — not re-decided here)

1. **Stale frozen `check-gates.json` after engine fixes.** A bundle frozen under a
   broken engine carries failure rows that a later engine would not produce (11786's C4,
   every bundle's raw T3). The frozen artifact is immutable by design, but a reader can
   mistake a stale FAIL for a real one. *Candidate delta:* a `pdca revalidate` /
   re-Check-stamp, or an Act convention to annotate superseded gate rows.
2. **Briefs seating a mechanism (pre-`2a9720b`).** `13205` and `11589` named the
   implementation in Scope; `2a9720b` added the discipline that forbids this. These
   briefs predate it — expected drift, no rework warranted, but confirms the delta was
   the right call (in `13205` the builder beat the seated mechanism by ignoring it).
3. **Weak regression reds.** `13205`'s import-error red is a test-design smell the C4
   contract does not catch (red can pass for the wrong reason). *Candidate delta:* a
   reviewer check that the red failure mode matches the *defect*, not a missing symbol.

## Standing setup (Phase 2 — default-to-upstream + essential fallback)

The faithfulness gap (validating against the fork's stale branches) is now closed in the
engine, so this is the default going forward:

- **Default target = upstream.** `make worktrees` now bases `gramps-6.{0,1}` /
  `addons-source-6.{0,1}` on `upstream/maintenance/gramps6{0,1}` (fetches first, realigns
  clean existing worktrees). Core C4-verify selects the upstream worktree by the bundle's
  target version — it no longer touches the developer's working clone.
- **Essential fallback line.** `engine/essential-fixes.tsv` lists the harness-enabling
  fixes (currently just `headless-ut-segfault` on 6.1). `make essential-worktrees` builds
  `gramps-<ver>-essential` = upstream + those fixes (cherry-picked; `REBUILD=1` to
  refresh). On an upstream C4 failure, `run-verify.sh` retries there and, if it passes,
  writes `essential-dependency.json` into the bundle (`depends_on` by slug) instead of
  failing the gate.
- **Verified end-to-end:** `11786` → upstream FAIL → essential PASS → stamp (`depends_on:
  ["headless-ut-segfault"]`), exit 0; `12576` → upstream PASS, no stamp (stale stamp
  cleared), exit 0; addon matrix unaffected. A `git clean -fdq` per leg keeps the
  worktrees pristine so results don't flake on run-created residue.
- **Template feedback:** the gramps gate (`engine/scripts/ubuntu/run-verify.sh`) is
  instance-specific, but the *generic pattern* — validate against canonical upstream,
  keep a local essential overlay for harness-enabling deps, stamp dependencies rather
  than fail — may be worth offering to the `pdca-harness` template (per the
  template-vs-instance boundary). Not filed; flagged for the human.
