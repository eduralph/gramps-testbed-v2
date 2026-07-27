---
title: Addon Development — Sidebar
managed: false
---

<!--
  Vault-internal map for the Addon Development section. NOT a published
  page (managed: false) — Obsidian users navigate by this; publish.py /
  md2pdf.py skip it.

  Ordering rationale: author journey. A reader new to Gramps addon work
  goes Overview (which now includes getting started: first Gramplet,
  restart loop, where addons live) -> a tutorial -> picks the kind of
  addon they're building -> reads fundamentals when something doesn't
  behave the way they expected -> reaches for data access / API as the
  addon gets non-trivial -> testing / debug / troubleshoot when stuck ->
  code analysis / packaging when ready to ship -> compatibility /
  what's new when porting across Gramps versions.
-->

## Sidebar

1. [[01-overview]] — what an addon is, the section map, file roles, first Gramplet, restart loop, where addons live.
2. [[02-tutorials]] — end-to-end walkthroughs per addon kind.
3. [[03-addon-kinds]] — all sixteen registration kinds: Gramplets, Views, Reports, Tools, Importers, Exporters, Quick Views, Docgens, Sidebars, Map services, Relationship calculators, Rules, Database backends, Thumbnailers, citation formatters, and GENERAL.
4. [[04-fundamentals]] — `.gpr.py` registration fields, plugin discovery, the provided environment (startup-owned process state), `_()` / `ngettext`, module-level loggers, lifecycle hooks.
5. [[05-data-access]] — `DbReadBase` / `DbWriteBase`, handles vs `gramps_id`, backlinks, transactions, what `gen/` exposes.
6. [[06-api-reference]] — curated `gramps.gen.*` surface addons are allowed to import; what's stable vs. what isn't.
7. [[07-testing]] — `unittest`-only, `test_*` filename conventions, mock-vs-`example.gramps` guidance, addon-unit runners.
8. [[08-debug]] — Gramps debug mode, log levels, repro scripts that bypass the GUI, `PrerequisitesCheckerGramplet`.
9. [[09-troubleshoot]] — common failure modes: silent reload, no-symlinks rule, namespace-package binding traps, `requires_mod` vs PyPI name.
10. [[10-code-analysis]] — Black, ruff E9/F63/F7/F82, `ast.parse`, mypy (for core); what the per-repo pre-commits enforce.
11. [[11-internationalization]] — i18n, translations, gettext, _() / N_() handling, .po/.pot generation for addons.
12. [[12-packaging]] — `make.py`, `addons-source` -> `addons` flow, version-field rules, submitting to upstream.
13. [[13-community]] — after the merge: the addon-list entry, the addon's wiki page, forum announcement, Mantis support duty.
14. [[14-compatibility]] — porting across Gramps versions; `gramps_target_version`; deprecated API surface; gramps60 vs gramps61 deltas.
15. [[15-whats-new]] — per-Gramps-version API changes that affect addons.
16. [[16-guidelines]] — normative MUST / SHOULD / MAY reference for addons and the contributor workflow. The page to cite in code review.
17. [[17-roadmap]] — forward-looking: in-flight changes, deprecations, open questions, and the documentation roadmap itself. Prospective counterpart to *What's new*.


## Status

All seventeen pages are substantive and `managed: true`. Open deepening work is tracked in [[17-roadmap]] → Documentation roadmap; the outstanding item needing a running Gramps is the tutorial screenshots (`_media/SCREENSHOTS-TODO.md`).

<!-- This file is intentionally not a {{stub}} for the wiki — it lives
     vault-side only. -->
