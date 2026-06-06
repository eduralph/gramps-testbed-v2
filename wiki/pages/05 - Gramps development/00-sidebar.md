---
title: Core Development — Sidebar
managed: false
---

<!--
  Vault-internal map for the Core Development section. NOT a published
  page (managed: false) — Obsidian users navigate by this; publish.py /
  md2pdf.py skip it.

  Ordering rationale: author journey. A reader new to Gramps core work
  goes Overview -> Get started -> a tutorial -> architecture to learn
  how the subsystems fit -> reads fundamentals when something doesn't
  behave the way they expected -> reaches for data access / API as the
  change gets non-trivial -> testing / debug / troubleshoot / code
  analysis when stuck -> internationalization / packaging when ready to
  ship -> compatibility / what's new when porting across Gramps versions.
-->

## Sidebar

1. [[01-overview]] — what Gramps core is, repo layout, where the pieces live.
2. [[02-get-started]] — cloning, dev environment, running from source, the edit loop.
3. [[03-tutorials]] — end-to-end walkthroughs through the core codebase.
4. [[04-architecture]] — subsystems and how they fit: `gen/`, `gui/`, `plugins/`, the DB layer, the event/signal flow.
5. [[05-fundamentals]] — primary objects, handles vs `gramps_id`, `_()` / `ngettext`, module-level loggers, the registration and lifecycle model.
6. [[06-data-access]] — `DbReadBase` / `DbWriteBase`, transactions, backlinks, what `gen/db` exposes and guarantees.
7. [[07-api-reference]] — the `gramps.gen.*` surface, what's public/stable vs. internal.
8. [[08-testing]] — `unittest` conventions, `*_test.py` filenames in `test/` packages, fixtures vs `example.gramps`, the core test runners.
9. [[09-debug]] — Gramps debug mode, log levels, repro scripts that bypass the GUI.
10. [[10-troubleshoot]] — triage and common failure modes; reading tracebacks back to the responsible subsystem.
11. [[11-code-analysis]] — Black, ruff E9/F63/F7/F82, `ast.parse`, mypy; what the pre-commits enforce.
12. [[12-internationalization]] — i18n, translations, gettext, `_()` / `N_()` handling, .po/.pot generation.
13. [[13-packaging]] — building and releasing: build scripts, version-field rules, packaging the release.
14. [[14-compatibility]] — porting across Gramps versions; deprecated API surface; 6.0 → 6.1 API deltas.
15. [[15-whats-new]] — per-Gramps-version changes that affect core development.
16. [[16-guidelines]] — normative MUST / SHOULD / MAY reference for core and the contributor workflow. The page to cite in code review.
17. [[17-roadmap]] — forward-looking: in-flight changes, deprecations, open questions, and the documentation roadmap itself. Prospective counterpart to *What's new*.


## Status

Section is complete. All 17 content pages are published (`managed: true`).

<!-- This file is intentionally not a {{stub}} for the wiki — it lives
     vault-side only. -->
