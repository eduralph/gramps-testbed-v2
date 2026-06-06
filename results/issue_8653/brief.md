# Brief — issue 8653 / deep-connections-excludes-start-person

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** deep-connections-excludes-start-person
- **Defect:** The **Deep Connections Gramplet** reports connection paths that route back through the start (Home) person, producing nonsensical chains such as "Main person / sibling of another person / **sibling of main person**" — the start person, which is the search origin, appears *inside* the path rather than only as its root. (Mantis 8653; reporter calls the first case "definitely a bug" and the parent/child-of-spouse case "probably harder to avoid".)
- **Success criterion:** A connection path the gramplet produces for the active person does **not** contain the Home/start person as an intermediate relationship step — the start person appears only as the implicit search root, never re-entered partway through a path.
- **Repo + branch target:** `addons-source` @ `maintenance/gramps60` — branched from `upstream/maintenance/gramps60` (addons production; the maintainer cherry-picks forward to gramps61). Confirmed: `DeepConnectionsGramplet.gpr.py` declares `gramps_target_version="6.0"`. (INTEGRATION §2.)
- **Scope:** Exclude the start (Home) person from being traversed/re-entered as an intermediate node in the connection search so it cannot appear mid-path. The relevant logic is the BFS in `DeepConnectionsGramplet/DeepConnectionsGramplet.py` `main()` (queue seeded with the default person, `:353-358`) + `get_relatives()` (`:221-279`) + `pretty_print()` (`:287-316`). / **out of scope:** the "harder" second case the reporter conceded (parent → child-of-spouse chains); any change to the gramplet's UI, pause/continue, or relationship-label wording.
- **Repro instruction:** fixture `example.gramps`. Add the Deep Connections Gramplet, set a Home person and an Active person who are connected such that a returned path passes through the Home person, and Run; observe a path that lists the start person as an intermediate step. **Do must first establish the failing repro** — see disposition.
- **Test file:** `DeepConnectionsGramplet/tests/test_deep_connections.py` — **addon** convention: a `tests/` (plural) package alongside the addon module, file `test_*.py`, loaded via the dotted path `DeepConnectionsGramplet.tests.test_deep_connections` (`./engine/scripts/ubuntu/run-addon-unit.sh DeepConnectionsGramplet`; INTEGRATION §3). The module imports `Gtk` at top and the search logic is entangled with the GUI generator (`yield`, `self.append_text`, `self.link`); Do will need to extract the path-search/exclusion into a GUI-free, testable seam, build a small in-memory DB (start person + relatives + an active person), and assert the discovered path excludes the start person. Red pre-fix, green post-fix.
- **Citations expected:** Do must cite path:line on `maintenance/gramps60` for every change (the start-person exclusion in the search, and any extracted helper).
- **Prior-art check (triage cycles):** searched — no merged fix in `addons-source` for this behaviour (`git -C ../addons-source log -- DeepConnectionsGramplet/`); confirm open/closed upstream PRs by path at Do time (INTEGRATION §5). Mantis thread carries **no developer discussion** (the scraped notes are empty), so the only guidance is the 2015 report.
- **Disposition hint:** verify repro first — the report is from 2015 (4.1.3) and the gramplet has since been **substantially rewritten** (modern Gtk UI; the BFS caches visited handles, which may already block re-entering the start person). Do must confirm the symptom reproduces on the current gramps60 code **before** changing anything; if it does **not** reproduce, report POSSIBLY-FIXED with the evidence rather than forcing a change.

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
</content>
