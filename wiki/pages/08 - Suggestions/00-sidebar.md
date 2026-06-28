---
title: Suggestions — Sidebar
managed: false
---

<!--
  Vault-internal map for the Suggestions section. NOT a published page —
  Obsidian users navigate by this; publish.py / md2pdf.py skip it.

  This section holds active *change suggestions* — proposed changes to Gramps
  that are in flight but not (yet) full GEPS: one Markdown file per suggestion.
  GEPS (the formal enhancement proposals) live in [[07 - GEPS]]; a suggestion
  that grows into a formal proposal graduates there.
-->

## Sidebar

Active change suggestions, one file per item. Lighter-weight than a formal
GEPS ([[07 - GEPS]]); a suggestion that matures into a proposal graduates.

1. [[addon-translation-auto-discovery]] — Mantis Feature Request: `get_addon_translator()`
   should resolve the addon root so translation works in nested-package addons.
2. [[addon-typed-protocol-api]] — Mantis Feature Request: typed Protocol API for addons
   (DB API first); the follow-on GEPS 049 enables.
3. [[sqlite-test-export-sql-flaky]] — addons-source bug: `test_export_sql` is flaky due
   to hardcoded `/tmp` paths and no `tearDown`; fix with `tempfile.mkdtemp()`.
4. [[lifelinechart-missing-dep-collection-crash]] — addons-source bug: `LifeLineChartView`
   raises bare `Exception` (not `ImportError`) when `life_line_chart` is absent, crashing
   pytest collection instead of producing a clean skip.
5. [[pdfforms-missing-reportlab-collection-crash]] — addons-source bug: `PDFForms`
   crashes pytest collection when `reportlab` is absent instead of skipping cleanly.
6. [[tmgimporter-dbf-silent-log-nameerror]] — addons-source bug: `TMGimporter` silently
   logs when `dbf` is absent, leaving `Table` undefined and causing `NameError` at runtime.
7. [[addon-missing-dep-guard-audit]] — general: audit all addons with optional pip deps;
   missing-dep guards must raise `ImportError` or `SkipTest`, never bare `Exception` or
   silent `LOG.error`.

## Status

Suggestions are authored as Markdown here and filed in the Gramps Mantis
**Feature Requests** project; they are not published to the wiki.
