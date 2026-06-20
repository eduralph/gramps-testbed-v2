# Build notes — sqlite-export-person-serialize-6.1

## Root cause (verified against source)

Core 6.1 added a 22nd field to `Person.serialize()`/`unserialize()` —
`familysearch_sync` at index 21 — via the `FamilySearchSyncBase` mixin
(`gramps-6.1/gramps/gen/lib/person.py:172-173` serialize, `:313-314` unserialize;
mixin at `gramps-6.1/gramps/gen/lib/fs/familysearchsyncbase.py`). Core 6.0's Person
is 21 fields.

The Sqlite addon hardcodes a fixed 21-tuple in two places on the shared (byte-identical
across `maintenance/gramps60` and `maintenance/gramps61`) source:

- **Export** `Sqlite/ExportSql.py:684-705` — `export_person` positionally unpacks
  exactly 21 names from `person.serialize()`. On core 6.1 `person.serialize()` is a
  22-tuple → `ValueError: too many values to unpack (expected 21)`. This is the crash
  the brief's repro hits in `setUp` (`exportSQL(...)`), **before** import is reached.
- **Import** `Sqlite/ImportSql.py:705-726` — `_process` builds a 21-tuple and feeds it
  to `Person.unserialize(data)`. On core 6.1 `unserialize` positionally unpacks 22 →
  it would raise `not enough values to unpack (expected 22, got 21)`. Import never ran
  in the repro only because export crashed first; the round-trip invariant requires
  both halves fixed.

## Fix (version-tolerant, the Invariant the brief names)

The Invariant: the addon's Person export/import must agree with the targeted core's
serialize field-set, on *both* 6.0 (21) and 6.1 (22) from one shared source. So the
fix must tolerate either arity, not hardcode 22 (a hardcode-to-22 would break the
gramps60×6.0 leg and would be wrong to cherry-pick forward).

- **Export** (`ExportSql.py:705`, new line): change the unpack tail
  `person_ref_list,     # 20` → add `*_,  # 21+`. `(... person_ref_list, *_,) = person`
  absorbs any fields past index 20 into a throwaway. On 6.0 `_` is `[]`; on 6.1 it is
  `[familysearch_sync_serialized]`. The export only persists handle/gid/gender/refs/
  change/private (the addon's `person` table columns), so dropping the extra is faithful
  to what the schema represents (brief Scope (b): persisting familysearch_sync is a
  separate enhancement).
- **Import** (`ImportSql.py:726`, after the 21-tuple): append the core's own defaults
  for any fields beyond index 20 — `data += Person().serialize()[len(data):]`.
  `len(data)` is 21. On 6.0 `Person().serialize()` is 21 elements → slice empty → no-op.
  On 6.1 it is 22 → appends the default `familysearch_sync.serialize()`, which
  `Person.unserialize` then passes to `set_familysearch_sync(...)`
  (`familysearchsyncbase.py:62-71` accepts the serialized form). Using core's own
  default tuple means the addon never has to know the field's shape — it stays correct
  if core adds further Person fields, without a blanket arity refactor.

`Person` is already imported in `ImportSql.py:46`, so no new import.

## Why not the alternatives

- **Hardcode the 22nd field** (`familysearch_sync` name in both spots): wrong by the
  Invariant — breaks the gramps60×6.0 leg (`ValueError: not enough values, expected 22,
  got 21` on a 21-field Person) and is exactly the change that must NOT be cherry-picked
  forward. Rejected on correctness, not cost.
- **Blanket "derive every object's tuple arity dynamically" refactor**: out of scope
  (brief Scope (c)). Verified across `gramps-6.1/gramps/gen/lib/` that **only Person**
  gained a serialize field in 6.1 — the event/family/note/etc. handlers are untouched
  by design. Touching them would be a multi-handler diff (each primary object's
  export/import pair) for zero behavioural gain.

## Test (the brief names `Sqlite/tests/test_sqlite.py`)

The existing `test_export_sql` body called `importSQL` with **no assertion** — it only
caught the bug via the `setUp` crash. Strengthened into a genuine round-trip regression
that drives the production path already present (`exportSQL`/`importSQL` directly, no
parallel copy — principles §3.4): assert the SQL re-import (`database2`) reproduces the
people exported from the source XML tree (`database1`) — equal `get_number_of_people()`
and, per source handle, equal gramps_id / gender / primary first-name / surname.
GTK pinning left to the runner's `gi_bootstrap` shim + upstream root `tests/__init__.py`
pin, per the brief — no `gi.require_version` block added, and the edit stays at the
bottom of the file, away from the gramps61-only inline pin block, so the cherry-pick to
gramps61 stays clean. Removed the file's two trailing blank lines so `git apply
--whitespace=error` is clean for the target's commit hooks.

## Verification (engine runner equivalent, both matrix legs)

Ran the C4 inner (the exact `git apply` → green → revert-prod → red sequence
`run-verify.sh` executes) in the pinned worktrees:

- **gramps61 × core 6.1** (the red→green leg): green-with-fix = `Ran 1 test … OK`;
  red-without-fix (production reverted, test kept) = `ERROR … ValueError: too many
  values to unpack (expected 21)` → `FAILED`. **green=PASS / red=PASS.**
- **gramps60 × core 6.0** (no-regression leg, per brief Verification note 1): green-
  with-fix = `Ran 1 test … OK`. Its red-without-fix half is not satisfiable (no
  pre-existing defect on 21-field Person) — expected, this leg is a no-regression check.

`git apply --whitespace=error` of the final `patch.diff` applies clean on
`addons-source-6.1`.

## Notes for sign-off (NEEDS-HUMAN, surfaced not decided)

- Branch target is `maintenance/gramps60` per the brief default; the production hunks
  are byte-identical across gramps60/gramps61 so the cherry-pick is mechanical, and it
  remains correct on gramps61 *only because the fix is version-tolerant*. Confirm the
  branch-target judgment call (brief Verification note 2).
- addons-source has no `black`/pre-commit config (no `pyproject.toml`/`.pre-commit-
  config.yaml`); the legacy `ExportSql.py`/`ImportSql.py` are not black-formatted, so I
  did **not** run black (it would reformat the whole legacy files and balloon the diff).
  Edits follow the files' existing aligned-comment style.
- No `po/POTFILES.{in,skip}` change: addon fix, no core `.py` added/removed.
