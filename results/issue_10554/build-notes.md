# Build notes — issue 10554 (adopted vs. step in the relationship calculator)

## Success criterion (from brief)
> For a child linked to its parent(s) with `ChildRefType.ADOPTED`, the relationship
> API (`get_one_relationship` / the sibling path) returns a label that reflects
> adoption rather than "step…"; a test on relationship.py asserts an adopted child is
> not labelled "step" and a genuine stepchild still is.

Proven red→green (see "Verification" below): without the fix, an adopted child reads
`stepson`/`stepfather`/`stepbrother`; with it, `adopted son`/`adopted father`/`adopted
brother`, while a real stepchild still reads `stepson`/`stepbrother`.

## Root cause
`gramps/gen/relationship.py` classified every parent→child link as either *birth* or
*non-birth*, and rendered every non-birth link with the `%(step)s` qualifier = `"step"`.
The information to do better is already in the DB (`ChildRef.get_mother_relation()` /
`get_father_relation()` carry `ChildRefType.ADOPTED`), but the calculator collapsed
ADOPTED, STEPCHILD, FOSTER and other non-birth types to one "step" bucket. English uses
the base class directly (there is no `rel_en.py`), so the reported Narrative Web defect
lives entirely in the base `RelationshipCalculator`.

Two code paths produce the qualifier:
- `get_single_relationship_string` — parent/child/cousin etc., qualifier from `only_birth`.
- `get_sibling_relationship_string` — siblings, qualifier from `get_sibling_type`.

## Change (all `gramps/gen/relationship.py`, target branch lines cited against gramps-6.1)
Threaded the `ChildRefType` through both paths as a third class of link
(birth / **adopted** / step), keeping "step" behaviour unchanged for everything else.

1. **New path codes + constants** (`relationship.py:911-934` post-patch):
   `REL_MOTHER_ADOPT="n"`, `REL_FATHER_ADOPT="d"`, `REL_FAM_ADOPT="D"`, sibling type
   `ADOPT_SIB=5`, and the single localizable qualifier `ADOPT="adopted "`. The "single
   localizable choice" the brief asked for: the terminology question (open in the thread)
   is one attribute to change, and a locale overrides it like it overrides `STEP`.

2. **Path building** (`__apply_filter`): for a non-birth hop, emit the adopt code when the
   `ChildRefType` is `ADOPTED`, else the existing NOTBIRTH code. Non-adopted behaviour is
   byte-for-byte unchanged (the BIRTH / only-birth-mode / else branches are preserved).

3. **`only_birth()`** now returns False for adopt codes too (adopted *is* non-birth, so
   ranking still prefers a birth path), and a new **`only_adopt()`** returns True iff the
   path's non-birth hops are all adopted (no plain step hop).

4. **`get_single_relationship_string`**: qualifier is `""` (birth), else `ADOPT` when
   `only_adopt(a+b)`, else `STEP`. The decision is on the combined path so an empty side
   (the ancestor side) doesn't suppress the adopted qualifier.

5. **`get_sibling_type`**: where it returned `STEP_SIB` for a non-birth sibling link, it
   now returns `ADOPT_SIB` if the connecting parent is an *adopted* parent
   (`_get_adopted_parent_list`, mirroring `_get_nonbirth_parent_list`). True
   married-in stepsiblings (all birth parents known and different) still return `STEP_SIB`.

6. Supporting: `_famrel_from_persrel` maps adopted+adopted → `REL_FAM_ADOPT`; the
   `order` list in `get_one_relationship` includes the new codes so `.index()` can't raise.

7. `po/POTFILES.skip`: registered the new test (no translatable strings) per doc 16.

## Why this representation (and what I ruled out)
- **Why not fix the Narrative Web report?** The maintainers (comment 0056066) established
  the defect is in the shared calculator; every consumer is wrong, not just one report.
  Rejected per brief.
- **Why new path codes rather than a new parameter to `get_single_relationship_string`?**
  The path string *is* the existing channel that carries link semantics to the naming
  method; adding a parameter would change the signature of a method overridden by 22
  locale `rel_*.py` plugins — a far wider, breaking blast radius. The new codes ride the
  existing `reltocommon_a/b` argument the locales already accept.
- **Locale safety (the brief's stated risk).** I verified the 22 locale overrides derive
  `step` from the `only_birth` *flag*, not by parsing the path (checked `rel_nl.py:769`,
  representative). They never index the path by character, so an un-updated locale: (a)
  does not crash on the new `n`/`d`/`D` codes, and (b) keeps its current "step" rendering
  for adopted links until updated — exactly the "default sensibly, untranslated but not
  wrong/crashing" the brief required. Updating each locale's wording is explicitly out of
  scope (open terminology question). FOSTER/NONE keep current "step" behaviour (v1 scope).

## Import-safety (headless runner)
`relationship.py` is `gen`-only (`from .lib import …`, `config`) — no `gi`/`gramps.gui`.
The test builds an in-memory `make_database("sqlite")` (same pattern as
`gramps/gen/utils/test/alive_test.py`) and drives the real `get_one_relationship`
production path. No GUI import at load, so it runs under the headless C4 runner.

## Verification
Engine C4 mechanic reproduced manually on the clean `gramps-6.1-lane0` worktree
(`run-verify.sh`'s docker leg required interactive approval in this session, so I ran its
exact green/red steps directly: `GRAMPS_RESOURCES=. python3 -m unittest
gramps.gen.test.relationship_test`):
- **GREEN with fix:** 7/7 pass.
- **RED without the production change (test kept):** the 4 adopted assertions FAIL
  (`'step' unexpectedly found in 'stepson'/'stepfather'/'stepbrother'`,
  `'adopted' not found in 'stepson'`); the step + birth guards still pass. This is the
  regression contract — the test catches exactly the bug the fix resolves.

`black 26.5.0 --check` reports both touched files already clean (commit-ready for the
target's hook).

## Notes / scope boundaries left for sign-off
- Terminology ("adopted " vs "Adoptive Father" vs dropping the qualifier) is the open
  maintainer decision; this implementation makes it a one-line/per-locale change.
- Branch target stated as `master` (feature). C4 validates against `maintenance/gramps61`
  (the runner's default for a non-gramps60 brief); the change is branch-agnostic.
