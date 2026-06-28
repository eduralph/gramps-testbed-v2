# Build notes — issue 4862 / narrative-marriage-uses-preferred-not-birth-name

## Root cause (two sentences)

The shared narrator renders the spouse in a marriage/relationship sentence with
`name_display.display(spouse)` (`gramps/plugins/lib/libnarrate.py:2369-2372` on
`upstream/maintenance/gramps61`), which always formats the spouse's **primary
(preferred) name**. When the spouse later divorces and remarries, their preferred
name becomes a later married name, so the past-tense sentence about the *earlier*
marriage silently switches to that later name — the ambiguity the reporter (Mantis
4862) and Gramps note ~0042628 describe.

## Fix — chosen name-selection rule (NEEDS-HUMAN design call)

The brief leaves the exact rule to the human (Disposition hint), but states the
Success criterion: the spouse must be named by a **stable** name "(the spouse's
primary/birth name) that does not change when the spouse acquires a later preferred
married name." I implemented the minimal rule that satisfies that:

> Use the spouse's **Birth Name** (`NameType.BIRTH`) when one exists; fall back to
> the currently-preferred primary name only when the spouse has no Birth Name.

A birth name does not change on remarriage, so it removes the divorced-and-remarried
ambiguity while preserving today's output for everyone who has no separate birth
name (the common case). The reviewer/human ratifies the rule at sign-off.

### Changes (all on `gramps-6.1-lane0` == target `maintenance/gramps61`)

- `gramps/plugins/lib/libnarrate.py`
  - import `NameType` (after `libnarrate.py:39`).
  - new module-level helpers `_get_birth_name(person)` and
    `_get_spouse_name(spouse, name_display)` (after `convert_prefix`, ~`libnarrate.py:94`).
    `_get_birth_name` scans `[primary] + alternate_names` and returns the first
    `NameType.BIRTH` name (primary first, so a preferred birth name still wins);
    `_get_spouse_name` displays that Birth Name via `display_name(name)`, else falls
    back to `display(spouse)` (the historical primary-name path).
  - `get_married_string` now calls `_get_spouse_name(spouse, name_display)` in place
    of the inline `_nd.display / name_display.display` branch (`libnarrate.py:2369-2372`).

The report call sites are unchanged and route through the same shared method, e.g.
`gramps/plugins/textreport/detdescendantreport.py:624`
`self.__narrator.get_married_string(family, is_first, self._name_display)` — so the
production path is fixed for every narrative report that uses the narrator, not a copy.

### Test — `gramps/plugins/lib/test/libnarrate_test.py` (new)

Drives the **production** `Narrator.get_married_string` over in-memory `Person` /
`Family` objects and a tiny fake db (the narrator only needs `get_person_from_handle`).
Three cases:
1. `test_uses_birth_name_not_later_preferred_married_name` — spouse whose preferred
   name is a later `MARRIED` name but who keeps her `BIRTH` name as an alternate:
   sentence must contain the birth surname ("Red"), not the later one ("White").
2. `test_stable_when_a_later_preferred_name_is_acquired` — the same person before vs.
   after acquiring a later preferred married name must yield the **same** sentence.
3. `test_falls_back_to_preferred_name_without_a_birth_name` — non-regression guard:
   with no birth name the preferred name is still used.

Import-light: imports only `gramps.gen.lib` + `gramps.plugins.lib.libnarrate`
(no `gi` / `gramps.gui`), so it runs under the headless C4 runner.

New core `.py` files registered in `po/POTFILES.skip` (test package, no translatable
strings): `gramps/plugins/lib/test/__init__.py` and
`gramps/plugins/lib/test/libnarrate_test.py`.

## Verification (red→green)

The C4 docker runner could not be launched from this Do session (docker invocation
required an approval the headless builder cannot grant). I instead ran the **same
red→green contract** directly against the lane0 source tree (host has gramps + the
lane0 checkout on the target base), which exercises the identical production path the
C4 runner uses:

- GREEN (patch applied): all 3 tests pass.
- RED (only `libnarrate.py` reverted, test kept): tests 1 and 2 FAIL with
  `AssertionError: 'He married Red, Agnes. ' != 'He married White, Agnes. '` /
  `'Red' not found in 'He married White, Agnes. '` — exactly the bug. Test 3 (the
  fallback guard) stays green both ways, as intended.

This is the same green-with-fix / red-without-fix mechanic C4-verify asserts; the
gate re-runs it in the container.

## Worktree note (not part of the deliverable)

`PDCA_WORKTREE` was unset; the serial default worktree `gramps-6.1` was being raced by
another concurrent worker (foreign `libsurnames` changes appeared and a concurrent
`git checkout` reverted my edits mid-build). I moved all edits to the clean, isolated
`gramps-6.1-lane0` worktree (same HEAD `b679c084f6`, target `maintenance/gramps61`) and
generated `patch.diff` from there. The patch is scoped to only the four issue-4862 files.

## Alternatives considered

- **Take the name from the marriage *event* / name-event-type** (note ~0042628's
  "take the Event type into account"): there is no per-event name reference in the
  Gramps data model — a `Name` has a `NameType`, not a date range tying it to an
  event — so honoring "the name held at the time" would require new modelling, which
  the brief lists as **out of scope** ("alternate-name *type* modelling"). The
  birth-name rule achieves the stated stability goal without any model change.
- **Add a report option ("use maiden/birth name")** like web/calendar reports: larger
  surface (new menu option wired through every narrative report's options + docs) and
  it does not by itself fix the default ambiguity. Concretely it would touch the
  options class of each narrative report (detdescendant, detancestor, …) plus
  `stdoptions`; the chosen fix is the single ~30-line shared-narrator change verified
  here. The human can still layer an option on top later if desired.
