# Brief — issue 13744 / empty-date-serialization-roundtrip

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** empty-date-serialization-roundtrip
- **Defect:** An empty/unset date entered in Gramps 6.0.x is serialized to Gramps XML as `<datestr val=""/>`, a form the **Verify the data** tool rejects on re-open (reports `Invalid death date`). Pre-6.0.0 omitted the `<datestr>` element entirely for an empty date, and that form validated cleanly ("no death date" → no complaint). So empty dates no longer round-trip through export → re-import / validate. (Mantis 13744; reporter's `simpson.gramps`, note 1.)
- **Success criterion:** An event whose date is **empty**, exported to Gramps XML and re-imported (and run through Tools → Utility → **Verify the data** with defaults), is treated as having **no date** — it does **not** raise `Invalid death date` / `Invalid date` — matching pre-6.0.0 behaviour. Equivalently: serialize → deserialize → serialize of an empty Date is stable and yields an empty Date.
- **Invariant to restore:** An empty `Date` must survive a Gramps-XML export → import (and the Verify-data date check) as an empty date — the serialized form of an empty Date deserializes back to an empty Date, and an empty Date is never reported as an *invalid* date by validation. (Round-trip stability: `Date` serialize/unserialize as mutual inverses for the empty case, plus the XML schema's equivalence of a *missing* vs *empty* `<datestr>`. Source: `gramps/gen/lib/date.py` serialization; the Gramps-XML writer/reader.) SELF-TEST: guarding only the Verify tool would mask the defect while the XML still carried the bad empty `datestr` — the invariant spans serialize ↔ deserialize ↔ validate, so it is category-level, not a single-module guard.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61 (core; forward-merged to master per INTEGRATION §2).
- **Surfaces:** data
- **Scope:** the serialized form of an **empty** date does not round-trip to an empty date (and the Verify-data check then flags it) — make an empty date export/import/validate as "no date", matching pre-6.0.0. / **out of scope:** non-empty or partial (year-only, span, range) date format changes; the Verify tool's other heuristics; archaeology of which 6.0 commit first emitted the empty `<datestr>` beyond identifying the serialized-form change responsible.
- **Repro instruction:** fixture — reporter's `simpson.gramps` (note 1) exhibits it; Do should build a **minimal** equivalent (a tree with one event carrying an empty date). Steps: in 6.0.x assign an empty death date to a person, export to **Gramps XML (family tree)**, observe `<datestr val=""/>` on the event; run **Tools → Utility → Verify the data** (defaults 102, 17, 50, 3, 30, 99, both checked) → `Invalid death date (1)`. Root cause to confirm by reading the empty-date write/read path in `gramps/gen/lib/date.py` and the XML serializer (`gramps/plugins/export/exportxml.py`) plus the Verify check in `gramps/plugins/tool/verify.py` — locate where an empty date emits `datestr val=""` rather than omitting the element.
- **Test file:** `gramps/gen/lib/test/date_test.py` — **core** convention: a `test/` (singular) package, `*_test.py` suffix (INTEGRATION §3). Red pre-fix (an empty Date does not round-trip / its serialized form re-reads as a non-empty invalid date); green post-fix (empty Date → serialize → deserialize → empty Date; no invalid-date verdict). If the defect is specifically in the XML `datestr` element, Do may instead/also place a round-trip test next to the export/import code — confirm the exact module at Do time; the test must exercise the production serialize/deserialize path, not a parallel copy.
- **Citations expected:** Do must cite path:line on `maintenance/gramps61` for every change.
- **New/removed files:** none expected (edits existing modules + an existing `test/` package). If a new `test/` file is created, register it in `po/POTFILES.skip` (no translatable strings) per doc 16 §Adding and removing Python files.
- **Prior-art check (triage cycles):** search by path at Do time — `git -C ../gramps log upstream/maintenance/gramps61 -- gramps/gen/lib/date.py gramps/plugins/export/exportxml.py` (also `master`) + closed/rejected PRs by path. Related: **13747** (sibling serialization-stability fix — deterministic ordering on metadata sets; **distinct root cause**, do not bundle).
- **Mantis:** 13744
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
