---
title: GEPS — Sidebar
managed: false
---

<!--
  Vault-internal map for the GEPS section. NOT a published page (managed:
  false) — Obsidian users navigate by this; publish.py / md2pdf.py skip it.

  GEPS — Gramps Enhancement Proposals — are design proposals for larger
  changes to Gramps. This section holds them as Markdown, one file per
  proposal, so they can be read, searched, and cross-linked alongside the
  rest of the contributor docs. Pages here are mirrored from the upstream
  wiki via wiki/tools/scrape_wiki.py (front-matter records source +
  wiki_revid); the wiki stays the source of truth. A change that is not yet
  a formal proposal lives in [[08 - Suggestions]] and graduates here.
-->

## Sidebar

1. [[geps-049-versioned-addon-api-surface-and-2-axis-lifecyle-model]] —
   versioned addon API surface + a two-axis plugin lifecycle model.

## Status

`GEPS 049` is a draft under review (Discourse 9491 / GitHub Discussion 2311).
Mirrored from the wiki at revid 131311 — refresh with `scrape_wiki.py`.

## New proposal

Copy [[geps]] (`02 - templates/geps.md`) into this folder, fill it in, and set
the front-matter `title:` to the `GEPS NNN: …` page name. The template's header
comment covers the publish steps (`publish.py` dry-run → `--apply`).
