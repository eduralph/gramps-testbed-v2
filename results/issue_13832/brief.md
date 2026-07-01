# Brief — issue 13832 / graphview-hyphenated-web-handles

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** graphview-hyphenated-web-handles
- **Defect:** People created in Gramps-Web get UUIDv4 handles containing hyphens (e.g.
  `_22e6b2a0-269e-4c58-8e27-0c38b2ef5a10`); after sync/import to the desktop, Graph View
  blanks out (or truncates the handle at the first hyphen) whenever an active person
  connects to such a Web-created person. The schema allows any ≤50-char handle string, so
  the affected path must accept hyphenated handles.
- **Success criterion:** N/A — close disposition. The defect no longer reproduces on the
  target branch (already fixed); no patch is authored.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** gui
- **Difficulty:** medium
- **Scope:** the affected Graph View / handle-handling path's assumption about handle
  charset. / out of scope: #13830 (path-to-home short-circuit), a distinct GraphView cause.
- **Repro instruction:** import the reporter's example.gramps (hyphenated Web handles) and
  make a "Broken"-suffixed person active in Graph View.
- **Test file:** N/A — close disposition (no patch).
- **Mantis:** 13832
- **Disposition hint:** not-reproducible — already fixed upstream on the target branch; the
  defect no longer reproduces. Discontinue.

## STOP discipline

Draft only until Check sign-off.
