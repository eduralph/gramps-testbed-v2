---
title: "REPLACE ME — exact wiki page title in GEPS NNN form (e.g. GEPS 050: Concise proposal title)"
categories:
  - GEPS
  - Developers
managed: true
---

<!--
  GEPS TEMPLATE — for a Gramps Enhancement Proposal: a design proposal for a
  larger change to Gramps core or the addon ecosystem. Lives under
  07 - GEPS/ by convention, one file per proposal.

  How this template differs from its siblings:
    technical-documentation.md — Gramps internals reference (existing behaviour).
    addon-development.md        — how-to for addon authors.
    user-guide.md               — end-user, in-app workflows.
    geps.md (this)              — a PROPOSAL for a change not yet made; carries
                                  the standard GEPS header (Type / Status /
                                  Authors) and ships to the wiki's GEPS series.

  Publishing (repo -> wiki) via wiki/tools/publish.py:
    * Set front-matter `title:` to the EXACT wiki page name in the
      "GEPS NNN: Title" form — it becomes the published page title verbatim.
    * `managed: true` is the publish gate; keep it.
    * `categories: [GEPS, ...]` lands the page in the GEPS category index.
      publish.py creates/updates the PAGE only; adding it to the GEPS index
      list page is a separate manual wiki edit.
    * Dry-run first (offline, no browser):
        cd wiki && python3 tools/publish.py --filter "GEPS NNN"
      A brand-new GEPS (not yet on the wiki) shows as CREATE — no --force.
    * Publish (host-side, needs your cleared-Cloudflare Chrome):
        cd wiki && python3 tools/publish.py --filter "GEPS NNN" --apply
    * Editing a GEPS that ALREADY exists on the wiki is the adopt path: a
      one-time `--force --apply` (a deliberate pandoc reformat — review the
      dry-run). See [[geps-049-versioned-addon-api-surface-and-2-axis-lifecyle-model]]
      as a worked example of the published structure.

  Conversion notes (md2wiki.py, pandoc gfm -> mediawiki):
    * Plain GFM converts cleanly: headings, lists, tables, fenced code,
      bold/italics, links. Eyeball the generated wikitext on the dry-run for
      long docs (footnotes, nested tables) before --apply.
    * Obsidian [[wikilinks]] / ![[embeds]] are rewritten; external links pass
      through. Diagrams: drop images in 07 - GEPS/_media/ and embed with
      ![[_media/foo.png|caption]].

  Delete this comment block (and the inline <!-- guidance --> below) before
  publishing.
-->

# REPLACE ME — GEPS NNN: Title

## Type

<!-- One of: Standards Track (a change to Gramps / addon behaviour or
     interfaces), Process (a change to how the project works), Informational
     (guidance, no mandate). -->

Standards Track

## Status

<!-- Draft | Under review | Accepted | Rejected | Deferred | Final | Withdrawn.
     Link the discussion / review threads (Discourse, GitHub Discussion / PR). -->

Draft

## Authors

<!-- One per line: Name (handle) — role / contribution. -->

-

## Abstract

<!-- One to three short paragraphs: what this proposes and why, readable on its
     own. A reviewer should grasp the whole proposal from this section alone. -->

## Motivation

<!-- The problem. Concrete symptoms, who is affected, why the status quo is
     inadequate. Cite real cases (issues, PRs, specific addons). -->

## Rationale

<!-- Why THIS design — the alternatives considered and why they were not chosen. -->

### Goals

-

### Non-goals

<!-- Explicitly out of scope; bounds the proposal and pre-empts review churn. -->

-

## Specification

<!-- The normative detail: the actual change. Interfaces, fields, file formats,
     behaviour, with MUST / SHOULD / MAY where it matters. Split into Parts or
     Phases if independently landable. Put code / wikitext in fenced blocks. -->

## Backwards Compatibility

<!-- What breaks, what stays. Impact on addon authors, the addons-source
     maintainer, and end users. Migration / deprecation path, if any. -->

## Reference implementation

<!-- Optional: link a branch / PR / prototype, or state "none yet". -->

## Open questions

<!-- Unresolved points for reviewers to weigh in on. -->

-

## References

<!-- Discussions, PRs, prior GEPS, external specs. Plain links. -->

-
