---
title: "Typed Protocol API for addons (DB API first)"
managed: false
status: draft
---

<!--
  A change suggestion (vault-internal; not a published wiki page). Written to file
  directly in the Gramps Mantis tracker, **Feature Requests** project. Raised by
  bryndin while reviewing GEPS 049 in addons-source PR 941. Inside a Mantis note,
  "#nnnn" means another Mantis ticket, so GitHub PRs are referenced as plain text +
  URL.
-->

# Feature Request — Express the addon-facing API as typed Python Protocols (DB API first)

> **Project:** Feature Requests · **Category:** Plugins / API · **Severity:** feature

**Summary:** Define the addon-facing Gramps API as typed `typing.Protocol` interfaces,
starting with the database API, so addon authors get static type-checking against a
named, stable contract.

**Description:**

Addons couple to Gramps through an implicit, untyped surface — whatever names in
`gramps.*` happen to import and work. There is no machine-checkable definition of
"the API an addon may rely on," so authors infer the contract from source and editors/
type-checkers cannot help them. The proposal: express the addon-facing contract as
Python `Protocol` classes, **beginning with the database API** (the most-used, most
sharply-defined surface), and grow to the object model and plugin base classes over
time. Addons then type their dependencies against the Protocol and get `mypy`/IDE
checking; core gets a precise statement of what it has promised to keep stable.

**Additional information:**

- Raised by bryndin in his review of GEPS 049, addons-source PR 941
  (`https://github.com/gramps-project/addons-source/pull/941`). Protocols give static
  typing (which Gramps largely lacks), better isolation of addons from internals, and
  a contract that is clear to human *and* AI developers — stronger than an allowlist
  of importable modules, which documents the surface without typing or enforcing it.
  His note: Gramps' DB API "can and should be converted to Protocols anyway."
- **Relationship to GEPS 049 — complementary and sequenced.** GEPS 049 is the
  *prerequisite*: it enumerates the addon API surface and adds mechanical
  change-detection (griffe) so the surface is known and held stable. A `Protocol` can
  only be written for a surface that is already stable, so Protocol-typing is the
  *destination* that work enables (recorded as Future Work in the GEPS). This request
  is that follow-on; it does not replace API versioning.
- Natural first target: the DBAPI base class — also relevant to provider-side backend
  addons such as PostgreSQLEnhanced. GEPS 049 wiki page:
  `https://www.gramps-project.org/wiki/index.php/GEPS_049:_Versioned_Addon_API_surface_and_2_axis_lifecyle_model`
- If a maintainer would rather track this under the GEPS umbrella, it can instead be a
  pointer on the GEPS discussion — but as a tracker item it files in Feature Requests.
