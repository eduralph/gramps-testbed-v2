# Design proposal — issue 10554 / relationship-adopted-vs-step

> The Plan artifact for an enhancement that needs design buy-in (relationship-naming
> semantics with cross-locale + translation impact). Do reads ONLY this file and
> implements it; Check runs the regular gated check on the code. Keep the
> `- **Label:** value` lines (the driver parses them).

- **Slug:** relationship-adopted-vs-step
- **Kind:** enhancement (design proposal)
- **Goal:** The relationship calculator distinguishes an *adopted* parent/child/sibling
  link from a *step* link, so a child connected to a parent with
  `ChildRefType.ADOPTED` is no longer reported as a "step" child/sibling (and reciprocally
  for the parent). Today `gramps/gen/relationship.py` classifies every non-birth link as
  "step" via the `%(step)s` interpolation, so an adopted child shows as a stepchild in the
  Narrative Web report and elsewhere even though Gramps holds the adoption relation.
- **Success criterion:** For a child linked to its parent(s) with `ChildRefType.ADOPTED`,
  the relationship API (`get_one_relationship` / the sibling-relationship path) returns a
  label that reflects adoption rather than "step…"; a test on relationship.py asserts an
  adopted child is not labelled "step" and a genuine stepchild still is.
- **Repo + branch target:** gramps-project/gramps @ master   (new relationship semantics
  with translation impact — feature work targets master per INTEGRATION §2; the maintainer
  may redirect to a maintenance line, an explicit base request wins per §2)
- **Scope:** introduce, in the shared relationship calculator, a distinction between
  birth / adopted / step (and foster) parentage derived from `ChildRefType`, so the
  naming path can choose an adopted qualifier instead of "step" for adopted links. / out
  of scope: settling the exact translated wording for every locale (an open question,
  below); hand-editing every locale `rel_*.py` plugin's string tables beyond what the
  shared mechanism requires; report-side formatting (the calculator is the source of
  truth — fixing it fixes the Narrative Web and other consumers).
- **Difficulty:** high — `relationship.py` is the base class for ~30 locale `rel_*.py`
  plugins and carries hundreds of `%(step)s`-interpolated relationship strings; adding an
  "adopted" distinction touches the shared naming mechanism, every locale's strings, and
  the translation catalogue. Wide cross-file blast radius.
- **Test file:** gramps/gen/test/relationship_test.py (new) — build a tree with an
  adopted child and a stepchild, assert the adopted child's computed relationship is not
  "step…" and the stepchild's is.
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **Disposition hint:** new-feature

## Motivation

When a person is adopted, Gramps records the relation explicitly
(`ChildRefType.ADOPTED` on the child reference) and the editor's "Relation within this
family (if not by birth)" field shows it. But the relationship calculator collapses
every non-birth link to "step", so reports (the Narrative Web being the most visible)
call an adopted child a *stepchild* and adopted parents *step-parents*. This is
genealogically and legally wrong — an adoptee is treated as born into the family — and
the information to do better is already in the database. The reporter hit this preparing
a Narrated Web for an adopted child; the maintainers confirmed it is a
`gramps/gen/relationship.py` issue (comment 0056066), independent of any one report.

## Design

`relationship.py` currently decides "step" purely from a birth / non-birth flag. The
proposal: thread the child-reference type through to the naming decision so the calculator
can tell *adopted* from *step* from *foster*.

- Where the calculator walks family→child links it already has the `ChildRef`; classify
  the link as birth / adopted / step / foster from `child_ref.get_mother_relation()` /
  `get_father_relation()` (`ChildRefType`) instead of a binary birth/non-birth.
- Carry that classification to the point where `%(step)s` is filled, and select an
  adopted qualifier for adopted links (parent, child, and sibling forms — siblings
  inherit from how each child links to the shared parent).
- The shared English string set in `relationship.py` gains the adopted forms; each locale
  `rel_*.py` overrides as it already overrides the step forms. Keep "step" behaviour
  unchanged for genuine `STEPCHILD` links so nothing regresses.

Do chooses the concrete representation (e.g. an extra interpolation token alongside
`%(step)s`, or a small classifier returning the qualifier) — this proposal fixes the
*outcome* (adopted ≠ step), not the mechanism.

## Alternatives considered

- **Fix only the Narrative Web report.** Rejected: the maintainers established the defect
  is in the shared calculator (it surfaces in many reports); patching one report leaves
  the rest wrong and duplicates logic.
- **Drop the qualifier entirely for adopted (call them plain father/mother/brother).**
  This was the reporter's first preference, but it loses information some users want and
  is the larger behavioural change. The adopted-qualifier approach is more conservative
  and reversible per-locale. (This is the open terminology question below.)

## Impact & compatibility

- Behaviour change: adopted relations render with an adopted qualifier instead of "step"
  across all relationship consumers (Narrative Web, relationship view/tool, reports).
- Translation impact: new strings in `relationship.py` and the locale `rel_*.py` plugins;
  the `po/` catalogue gains adopted forms. Existing "step" strings are unchanged.
- Risk: the locale plugins are numerous and individually maintained; the shared mechanism
  must default sensibly so an un-updated locale still produces a correct (if untranslated)
  result rather than crashing.

## Open questions

- **Terminology (needs maintainer/human decision before merge).** The thread did not
  settle this: "Adoptive Father / Adoptive Mother" + plain "Brother/Sister", vs.
  "adopted" as a parallel to "step" on every form, vs. dropping the qualifier. The
  implementation should make the qualifier a single localizable choice so the decision is
  cheap to change.
- **Foster (`ChildRefType.FOSTER`) and `NONE`.** Treat foster as its own qualifier, or
  fold into "step"? Proposed: out of scope for v1 (keep current "step" behaviour for
  non-adopted, non-birth) — adopted is the reported, highest-value case.
- **Branch target.** Stated as master (feature); confirm with the maintainer whether they
  want it on a maintenance line instead.

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a draft PR
MAY happen during the cycle (useful for CI). The PR MUST NOT be marked ready before
sign-off accepts.
