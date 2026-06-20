# Build notes — issue 13744 / empty-date-serialization-roundtrip

## Root cause (two sentences)

An "empty" date can be modelled as `MOD_TEXTONLY` with empty `text` — produced by
`Date.set_as_text("")` (`gramps/gen/lib/date.py:1931`, the path the XML reader uses) and by
`Date.set(modifier=MOD_TEXTONLY, text="")` (the editor's text-only path). The Gramps-XML
writer emits a `MOD_TEXTONLY` date as `<datestr val="…"/>` (`gramps/plugins/export/exportxml.py:1074`),
so an empty date is written as `<datestr val=""/>` — distinct from a *missing* `<datestr>` —
which on re-import (`importxml.start_datestr` → `set_as_text("")`,
`gramps/plugins/importer/importxml.py:2774`) reconstructs the same `MOD_TEXTONLY`+empty date,
i.e. the empty date does not round-trip to a *canonical* empty date.

## Why this is the cause, not the symptom

The Verify tool flags it via `date_obj.get_valid()` (`gramps/plugins/tool/verify.py:247-248,288`),
and `get_valid()` (`gramps/gen/lib/date.py:1623`) was already patched on `maintenance/gramps61`
(commit `d31bf5aab2` "Fix invalid date when no date in data verify tool") to special-case
`MOD_TEXTONLY` + empty text as valid. That is exactly the **Verify-only guard the brief's
SELF-TEST warns about**: it stops the "Invalid death date" message but leaves the XML still
carrying `<datestr val=""/>`, and leaves the in-memory empty date in a non-canonical form. The
real defect spans serialize ↔ deserialize: an empty date should never be a *text-only* date.

I confirmed the live behaviour on the `gramps-6.1` worktree (a probe, not committed):
`Date().set_as_text("")` → modifier `6` (`MOD_TEXTONLY`), `serialize()` =
`(0, 6, 0, (0,0,0,False), '', 0, 0)`, whereas a default empty `Date().serialize()` =
`(0, 0, 0, …)`. The two empty dates serialize **differently** (modifier 6 vs 0) — the missing
≡ empty equivalence is broken at the data layer.

## The fix

Make an empty text *not* be a text-only date — normalise it to a regular empty date
(`MOD_NONE`, `dateval = Date.EMPTY`) at the two producers:

- `set_as_text(text)` (`gramps/gen/lib/date.py:1931`): empty `text` → `MOD_NONE`. This is the
  XML reader's path (`importxml.start_datestr`) and the parser's text fallback, so it closes
  the **deserialize** side — an empty `<datestr>` now imports as a canonical empty date.
- `Date.set(...)` (`gramps/gen/lib/date.py:1827`, right after `if text: self.text = text`):
  if the resulting modifier is `MOD_TEXTONLY` with empty text, normalise to `MOD_NONE`. This
  covers the editor's text-only-with-no-text path, closing the **serialize/export** side.

Consequences (the invariant restored end-to-end, not a single-module guard):
- **Export:** `write_date` (`exportxml.py:1052-1074`) already returns without writing for a
  `MOD_NONE` date whose ISO start is empty (`elif mode != MOD_TEXTONLY: … if date_str == "": return`),
  so an empty date now produces **no `<datestr>` element** — matching pre-6.0.0.
- **Import:** `<datestr val=""/>` deserialises to a canonical empty date.
- **Validate:** `get_valid()` is `True` for `MOD_NONE` (the prior `d31bf5aab2` guard becomes
  belt-and-suspenders, not load-bearing).
- **Round-trip:** `serialize → unserialize → serialize` of an empty date is stable and equal to
  a default empty `Date` (`Date().serialize()`).

The `set_as_text`/`set` paths cover how an empty date *enters* the object graph (XML import,
parser, editor). I deliberately did **not** add normalisation in `unserialize`
(`date.py:730`): the success-criterion round-trip (export → re-import → Verify) re-enters via
`set_as_text`, which is now correct, so the re-import is canonical; normalising `unserialize`
would also silently migrate pre-existing DB rows, a behavioural change beyond this brief's
scope (data migration of already-stored dates).

## Alternatives considered and rejected

1. **Guard the export only** — add `if date.is_empty(): return` at the top of `write_date`
   (`exportxml.py:998`). Rejected: it is a single-module symptom guard (the brief's SELF-TEST
   point). The in-memory date stays `MOD_TEXTONLY`+empty, the import path still reconstructs
   the non-canonical form, and — decisively — `exportxml.py` does `from gramps.gui.plug.export
   import …` at module load (`exportxml.py:66`), so the C4 headless runner cannot import it
   (`gi`/Gtk core-dumps); the test would have to drive a hand-copy of `write_date`, which the
   builder rules forbid. The data-layer fix is testable through the real production path
   (`date.py` has no `gi` import) and removes the cause for *all* surfaces at once.

2. **Strengthen the Verify guard further** — purely the validate side. Rejected for the same
   SELF-TEST reason: the XML keeps the bad `<datestr val=""/>`.

3. **Normalise in `unserialize` / a DB upgrade** — broader than the brief (out-of-scope data
   migration of existing trees) and bypassed by the XML import path anyway.

## Test (red→green) — `gramps/gen/lib/test/date_test.py`, class `EmptyDateTest`

Added to the existing `EmptyDateTest` (`date_test.py:1729`), so no new file → no
`po/POTFILES.*` change. The test imports only `gramps.gen.lib.date` (no `gi`/`gramps.gui`),
so it runs under the headless C4 runner. It exercises the **production** path
(`Date.set_as_text`, `Date.set`, `Date.serialize`, `Date.unserialize`), not a copy:

- `test_set_as_text_empty_is_regular_empty` — empty text → `MOD_NONE`, empty, valid.
- `test_empty_text_date_serializes_canonically` — an empty date's serialized tuple equals a
  default empty `Date().serialize()` (the missing ≡ empty equivalence; transitively proves the
  XML writer omits the element, since it is no longer `MOD_TEXTONLY`).
- `test_empty_date_serialize_roundtrip_stable` — serialize → unserialize → serialize stable and
  empty.
- `test_set_text_only_with_empty_text_normalizes` — the `Date.set` producer also normalises.
- `test_text_only_with_text_is_preserved` — regression guard: a genuine text-only date keeps
  `MOD_TEXTONLY` and its text (the existing `test_text_only_empty` at `date_test.py:1738`,
  which uses non-empty text, also still passes).

`run-verify.sh` (C4): `green-with-fix=PASS / red-without-fix=PASS` (45 tests; red pass shows the
4 new assertions failing once `date.py` is reverted). `black --check` clean on both touched
files.
