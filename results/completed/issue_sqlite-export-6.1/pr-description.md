# Sqlite: tolerate core 6.1's 22-field Person serialization

Origin: tracked on eduralph/addons-source #47 (upstream addons-source has
GitHub issues disabled); no Mantis ticket. Surfaced as the
`addons-source gramps61 × core 6.1` leg of the addon-unit matrix.

## Root cause
Gramps core 6.1 added a 22nd field, `familysearch_sync` (index 21), to
`Person.serialize()`/`unserialize()`, but the Sqlite addon unpacks a fixed
21-field tuple on export and builds a fixed 21-field tuple on import — so the
`example.gramps` export→import round-trip raises `ValueError: too many values
to unpack (expected 21, got 22)` in `export_person`. The same shared source
ships on both `maintenance/gramps60` (core 6.0, 21 fields) and
`maintenance/gramps61` (core 6.1, 22 fields), so the fix must agree with
either core, not hardcode the new field.

## Fix
`export_person` now ends its positional unpack with `*_,`, absorbing any
fields past the ones the addon's `person` table stores (no-op on core 6.0,
drops `familysearch_sync` on 6.1 — persisting it is a separate enhancement).
The import path pads its 21-field tuple with the targeted core's own Person
defaults via `data += Person().serialize()[len(data):]`, which is a no-op on
core 6.0 and supplies the default `familysearch_sync` on 6.1. Using core's own
default tuple keeps the addon correct if core adds further Person fields,
without a blanket arity refactor. Person is the only `gramps/gen/lib` object
whose serialize tuple changed in 6.1, so no other object handler is touched.

## Verified against
- `Sqlite/ExportSql.py:704-705` — the `person_ref_list, # 20` / `) = person`
  unpack tail; `*_,` is inserted before the close so the 22-tuple no longer
  overflows the 21 names.
- `Sqlite/ImportSql.py:726-729` — the 21-field tuple ending `person_ref_list,)`
  feeding `g_pers.unserialize(data)`; the pad line is added before
  `unserialize` so the tuple matches the targeted core's arity. `Person` is
  already imported at `Sqlite/ImportSql.py:46`.
- core `gramps/gen/lib/person.py` `serialize`/`unserialize` — the positional
  contract the addon consumes; field 21 (`familysearch_sync`) was added in
  gramps core commit 4972a2eb4e746aac511174692967ae4a13621166.

## Test
`Sqlite/tests/test_sqlite.py:35` — `ExportSQLTestCase.test_export_sql` is
strengthened from a no-assertion `importSQL` call into a genuine round-trip
regression: it asserts the SQL re-import (`database2`) reproduces the people
exported from the source tree (`database1`) — equal person count, and equal
gramps_id / gender / primary first-name / surname per source handle. It drives
the production `exportData`/`importData` path directly (no parallel copy).
Red→green confirmed on the gramps61 × core 6.1 leg (reverting the production
hunks re-raises the `ValueError`); the gramps60 × core 6.0 leg is a
no-regression check (green with the fix; it has no pre-existing defect, so its
red-without-fix half is structurally not applicable). `git apply --check`
is clean on both the gramps60 target and the gramps61 cherry-pick target.
