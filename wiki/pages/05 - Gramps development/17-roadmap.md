---
title: "Gramps 6.1 Wiki Manual - Core Development - Roadmap"
categories: [Developers, Gramps 6.1]
managed: true
---

<!--wiki:{{man index|6.1}}-->

## Overview

Forward-looking view of the **Gramps core** development surface — what's planned, what's in flight, what's slated for deprecation, and what open questions will eventually become rules. The audience is a core contributor working on [`gramps-project/gramps`](https://github.com/gramps-project/gramps) asking "what do I need to plan around?"

This page is the **prospective** counterpart to [[15-whats-new]], which is retrospective. An item moves from this page to *What's new* once it ships in a release. The normative rules an item must satisfy before it ships live in [[16-guidelines]]; porting guidance once it lands is [[14-compatibility]].

## How to read this page

Each entry should answer four things:

| Field | Meaning |
|-------|---------|
| **Status** | proposed / accepted / in-flight / shipped / deferred / rejected |
| **Target** | Gramps version (`6.2`, `7.0`, ...) or "unscheduled" |
| **Impact** | what core contributors / downstream callers need to do (rewrite / opt-in / nothing) |
| **Tracking** | PR / Mantis bug / GEP / mailing-list thread |

A roadmap entry without a tracking link is a wish, not a plan; either add the link or move the entry to a separate "ideas" section.

Branch targeting follows [[16-guidelines]] §Contributor workflow: **fixes** ride `maintenance/gramps61` (forward-merged to `master`), and only **genuinely new-feature** work targets `master`. Most roadmap items here — features and larger changes — are therefore `master`-bound; a roadmap entry that is really a bug fix belongs on the maintenance branch instead.

## Gramps Enhancement Proposals (GEPs)

A **GEP** (Gramps Enhancement Proposal) is the project's design-proposal mechanism for changes large enough to need a written, reviewable spec before code is cut — major architecture, public-API, data-model, or UX changes. It is the core analogue of "open an issue first": small fixes and ordinary new functionality use a normal Mantis bug and PR, but a change that would be expensive to get wrong gets a GEP so the design can be debated once, in writing.

- **Where GEPs live.** GEPs are wiki pages under the [Category:GEPS](wiki:Category:GEPS) category, reached from the [Enhancement Proposals portal](wiki:Portal:Enhancement_Proposals). The portal also carries the lighter-weight [Proposed Report Specifications](wiki:Category:Proposed_Report_Specifications) and [Proposed Tool Specifications](wiki:Category:Proposed_Tool_Specifications) categories for new reports and tools. The in-repo `TODO` file is a single pointer to this category (`TODO:1`), which is the project's way of saying "the backlog lives on the wiki, not in the tree."
- **When a GEP is required.** Use one when the change touches the public API surface, the on-disk / database schema, or cross-cutting architecture; or when a maintainer asks for one on the thread. A change that fits in a single bug-fix-shaped PR does **not** need a GEP.
- **What a GEP is not.** A GEP is a *design* artifact, not an acceptance. A page existing under [Category:GEPS](wiki:Category:GEPS) means the idea was written up, not that it was blessed — track its disposition (accepted / deferred / rejected) separately, the same way the sections below do.
- **GEP vs. the sections on this page.** A GEP is the long-form design; the **Accepted but not yet implemented** and **Open questions** sections below are the short index pointing at the GEPs (and threads) that affect day-to-day core work. Link the GEP from the entry rather than restating it.

## In flight

<!-- TODO: items currently being worked on upstream that will affect
     core contributors / downstream callers. Source these from open
     gramps PRs against maintenance/gramps61 or master that touch
     gramps.gen.* or other shared surfaces. Cite the PR number; do not
     list a PR here without confirming it is open and unmerged. -->

- _none recorded yet_

## Accepted but not yet implemented

<!-- TODO: maintainer-blessed changes with no PR yet. Source from
     accepted Mantis feature requests, GEPs under Category:GEPS that
     have maintainer buy-in, and mailing-list decisions. Link the GEP
     or the Mantis bug; "accepted" needs a citable yes from a
     maintainer, not an unanswered proposal. -->

- _none recorded yet_

## Deprecations and removals

<!-- TODO: public API marked deprecated with a stated removal target.
     Pull from DeprecationWarning sites in gramps.gen.* and the
     "Removed in N" notes in NEWS / RELEASE_NOTES on the target branch.

     NOTE: deprecation warnings exist in the tree today WITHOUT a stated
     removal version, e.g.:
       - SecondaryObject.are_equal() -> use is_equal()
         (gramps/gen/lib/url.py:170; gramps/gen/lib/ldsord.py:361,
          on maintenance/gramps61).
     Do NOT list these here as roadmap items until a removal TARGET is
     announced upstream — a warning with no removal version is a
     standing recommendation, not a scheduled removal. Record it here
     only once NEWS / a maintainer names the version it goes away. -->

- _none recorded yet_

## Open questions

<!-- TODO: design questions affecting core where the answer isn't
     settled yet. A reader landing here should be able to find the
     GEP / Mantis thread / mailing-list discussion and contribute.
     Cite the thread; an open question with no link is just an
     opinion. -->

- _none recorded yet_

## Deferred / rejected

<!-- TODO: things that came up, got considered, and were declined.
     Recording them here is the antidote to re-proposing the same
     shape and re-running the same debate. Per [[16-guidelines]]
     §Contributor workflow, a closed-unmerged PR with a given fix
     shape is the maintainer's "no" — cite the closing PR / GEP /
     thread so a future reader can see WHY before re-proposing. -->

- _none recorded yet_

## Documentation roadmap

**This page is a scaffold.** Every roadmap section above is intentionally `_none recorded yet_` with an HTML-comment TODO describing what to source and where to cite it from. The page must not list a roadmap item that cannot be backed by an open PR, an accepted Mantis bug, a GEP under [Category:GEPS](wiki:Category:GEPS), or a maintainer ruling — inventing items is worse than an empty section. Promote a section the first time there is something verifiable to record.

The rest of the core section is authored and `managed: true`: [[16-guidelines]] carries the normative MUST/SHOULD rules; the how-to pages ([[08-testing]], [[09-debug]], [[11-code-analysis]], [[12-internationalization]], [[13-packaging]], [[14-compatibility]]) defer to it; and [[15-whats-new]] is its retrospective counterpart. Keep those pages aligned with the guidelines as the rules evolve — most notably [[08-testing]] with [[16-guidelines]] §Testing (core = `test/` package + `<module>_test.py` suffix).

(For the publishing pipeline itself — `publish.py`, `md2wiki.py`, `md2pdf.py --tree` — see the testbed root, not this page.)

## See also

- [[15-whats-new]] — retrospective counterpart; an item moves here once it ships.
- [[16-guidelines]] — the normative MUST/SHOULD reference a roadmap item must satisfy before it ships.
- [[14-compatibility]] — porting guidance once a roadmap item lands.
- [Enhancement Proposals portal](wiki:Portal:Enhancement_Proposals) — where GEPs and report/tool specs are organised.
- [Category:GEPS](wiki:Category:GEPS) — the live index of Gramps Enhancement Proposals.
- [Mantis bug tracker](https://gramps-project.org/bugs) — feature requests and design discussions originate here.
- [Gramps mailing lists](https://gramps-project.org/contact/) — where larger design questions get hashed out.

<!--wiki:{{stub}}-->
