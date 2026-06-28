# Brief — issue 12932 / verify-fanchart2way-startup-crash-fixed

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** verify-fanchart2way-startup-crash-fixed
- **Defect:** Reported startup crash: with "remember last view displayed" enabled, last
  view = 2-way fan chart, and background = time-period gradient, Gramps fails to start with
  `AttributeError: 'NoneType' object has no attribute 'append'` at
  `gui/widgets/fanchart.py` `set_userdata_timeperiod` → `userdata.append(period)`.
- **Success criterion:** On `maintenance/gramps61`, the 12932 repro no longer raises — the
  2-way fan chart restores at startup (time-period gradient enabled) without the
  AttributeError. This is a **verification**: confirm the defect is already gone so the
  tracker status can move to resolved. No production patch is expected if confirmed fixed
  (verify-first close ships a close-disposition + NO patch).
- **Invariant to restore:** (already restored upstream) every fan-chart `self.data` slot
  carries its own userdata list, so `prepare_background_box`'s age/period gradient paths
  never call `.append` on `None` regardless of whether `_fill_data_structures`
  short-circuits. Behavioural / object-initialisation invariant.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** low — verification only; the fix already landed.
- **Scope:** verify (do not re-implement) that the already-merged fan-chart startup-crash
  fix covers this 2-way + time-period-gradient case. / out of scope: any new change to
  `fanchart.py` / `fanchart2way.py`; the name-format fan-chart defect (issue 13532, a
  separate bundle); the "remember last view" preference machinery.
- **Repro instruction:** on a clean `upstream/maintenance/gramps61` worktree — set last
  view = 2-way fan chart with "Configure → Background → Time period based gradient", enable
  "remember last view displayed", restart Gramps → expected: it starts (no AttributeError).
- **Test file:** engine/interface/test_bug_12932_fanchart2way-startup.py — a committed
  AT-SPI repro that should now **pass green** on the patched-upstream worktree, evidencing
  the crash is gone (`Surfaces: gui` → `C4-verify-interface`). If the GUI repro cannot be
  driven, record the verification as performed by hand at sign-off.
- **Citations expected:** cite the already-merged fix
  (`0f3830a6e8 Fix fan chart crash at startup with age-gradient background`, "Fixes
  #13395") and the current `fanchart.py` `set_generations` slot initialisation as the
  evidence the path is fixed.
- **New/removed files:** none (verification; the interface repro lives in the testbed mount).
- **Prior-art check (triage cycles):** searched by path `gramps/gui/widgets/fanchart.py`
  on `upstream/maintenance/gramps61` — commit `0f3830a6e8` (Fixes #13395) initialises each
  `self.data` slot with its own userdata list precisely so the
  `BACKGROUND_GRAD_AGE`/`BACKGROUND_GRAD_PERIOD` `userdata.append(...)` paths cannot hit
  `None`, including the "after rename / no rootpersonh on startup" short-circuit this
  report describes. → already fixed; this bundle validates and resolves it.
- **Mantis:** 12932
- **Disposition hint:** POSSIBLY-FIXED → verify first

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
