# Brief — issue 13532 / fanchart-view-respects-name-format

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** fanchart-view-respects-name-format
- **Defect:** The Fan Chart view (and the related Descendant / 2-way fan views) does not
  honour the active "Name format" preference. Changing Edit→Preferences→Display→"Name
  format" updates the list views but leaves the fan-chart person labels unchanged.
- **Success criterion:** With a given active "Name format", the names drawn in the Fan
  Chart view match that format (changing the preference is reflected in the chart's
  person labels), rather than always rendering in a fixed format.
- **Invariant to restore:** A person label rendered by a view reflects the user's active
  display-name format — the fan chart resolves names through the configured name displayer
  (and re-renders when that configuration changes), not a hard-pinned format. (Behavioural
  consistency invariant; rationale: the name displayer is the single source of the user's
  chosen presentation, so all views must defer to it.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** medium — the fan-chart widget registers its own two-line format entries
  (`TWO_LINE_FORMAT_1/2`) and the view (`fanchartview.py`) wires several config-update
  callbacks; a reviewer must hold the name-format resolution + config-refresh path in view.
- **Scope:** the fan-chart view rendering names without applying the active name-format
  preference / without re-rendering when it changes
  (`gramps/gui/widgets/fanchart.py` name resolution + `gramps/plugins/view/fanchartview.py`
  config wiring). / out of scope: the two-line-name feature toggle, font/background/maxgen
  options, the list-view name handling, the name-format editor.
- **Repro instruction:** example.gramps → Charts → Fan Chart (note the displayed name
  style) → Edit→Preferences→Display → set "Name format" to "Given" (or another) → Close →
  the Fan Chart labels are unchanged; expected: they follow the chosen format.
- **Test file:** engine/interface/test_bug_13532_fanchart-name-format.py (committed
  AT-SPI repro; `Surfaces: gui` → `C4-verify-interface`). If the name-resolution path is
  reachable headlessly, additionally ship a core `*_test.py` driving the production name
  build the chart uses (principles §3.4); otherwise record C4 (unit) unverifiable for
  human sign-off.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** none expected for the gramps tree; a new core `*_test.py` →
  `po/POTFILES.skip`.
- **Prior-art check (triage cycles):** searched by path `gramps/gui/widgets/fanchart.py`
  and `gramps/plugins/view/fanchartview.py` on `upstream/maintenance/gramps61` — the
  startup-crash fix (#13395), https/comment commits only; no name-format-respect fix. No
  matching fork PR by this path. → unfixed.
- **Mantis:** 13532
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
