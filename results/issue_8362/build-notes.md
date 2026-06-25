# Build notes — issue 8362 / gedcom-export-place-type-accented

Target branch: **gramps-project/gramps @ maintenance/gramps61**
(worktree `../gramps-6.1`, detached at `upstream/maintenance/gramps61`,
HEAD `b679c084f6`). All citations are `path:line` on that tree.

## What the brief asked for

Verify-first (disposition POSSIBLY-FIXED). The 2015 report (on 4.1.1) was that a
marriage `PLAC` line in a GEDCOM export differed by place **type** ("Città" vs
"Town"), which the reporter blamed on the accented "à". Success criterion: exporting
an event whose place has an accented title and a type such as "Città" produces a
correct UTF-8 `PLAC` line that round-trips the accent, and the output does **not**
differ by place type.

## Root cause / why it is OBE (two sentences)

The pre-5.0 exporter mapped place parts into the GEDCOM ADDR/CITY structure by
matching the (translated) place type against English "City"/"Town", so the type
*did* drive the output; the 5.0 place-model rewrite deleted that mapping. On
maintenance/gramps61 `GedcomWriter._place` (`gramps/plugins/export/exportgedcom.py:1579`)
emits `PLAC = <place display name>` + MAP + notes with **no** reference to the place
type (`exportgedcom.py:1596`), and Python-3 / UTF-8 carries the accent — so the
reported discrepancy cannot reproduce.

Confirmed by reading the production path end-to-end:
- `_dump_event_stats` resolves the event's place and calls `_place(place, dateobj, 2)`
  (`exportgedcom.py:1243`-`1245`) — for a family marriage event this is reached via
  `_families` → `_family` → `_family_events` (`exportgedcom.py:876`, `:894`, `:952`).
- `_place` writes only the display name; the type is never consulted
  (`exportgedcom.py:1593`-`1605`).

## The test

`gramps/plugins/export/test/exportgedcom_place_test.py` (new). It builds an in-memory
sqlite tree (`make_database("sqlite")` + `db.load(":memory:")`) with a family, a
marriage event, and a place titled `"Forlì à la Côte"` typed once as the accented
`"Città"` and once as `PlaceType.TOWN`, runs the **real** `GedcomWriter.write_gedcom_file`,
and asserts:

1. the marriage place exports as a single `2 PLAC Forlì à la Côte` line with the
   accented bytes (`ì`, `à`, `ô` as UTF-8) present in the raw file, and
2. the `PLAC` output is identical for `"Città"` and `"Town"` — type does not drive it.

It exercises the production path (the real `_place`/`_writeln`/place-displayer), not a
copy.

### Headless / import-light handling

`exportgedcom` does `from gramps.gui.plug.export import WriterOptionBox` at import
(`exportgedcom.py:64`), and the db plugin layer reachable from `gramps.gen.db` imports
`gramps.gui.dbguielement`. Importing the real `gramps.gui` package realises GTK widget
classes — exactly what crashes a no-display unit runner. Neither symbol is used on the
export path under test, so the test registers lightweight stand-ins in `sys.modules`
**before** the gramps imports (`WriterOptionBox`, `DbGUIElement`). This keeps the unit
import-light while still driving the real writer.

Verified: the test runs **green** under plain `python3` even on a host whose system
GTK is too new for `gramps.gui` to import at all (`Gtk.IconSize.MENU` AttributeError) —
which is positive proof the unit is genuinely GUI-free / headless-safe. Both tests pass
against the real production code:

```
test_accented_title_roundtrips_as_utf8 ... ok
test_place_type_does_not_drive_place_export ... ok
Ran 2 tests in 0.067s — OK
```

(The two parent packages `gramps/plugins/export/__init__.py` and `.../test/__init__.py`
are empty, and `gramps/__init__.py` has no imports, so nothing heavy loads before the
test module body installs the stubs.)

## C4-verify: expected PDCA-UNVERIFIABLE (and why patch.diff is test-only)

This is verify-first: there is **no production change** to revert, so C4's
red-without-fix leg cannot go red. `engine/scripts/ubuntu/run-verify.sh` treats a
test-only patch (no non-test production file to revert) as unverifiable and emits
`PDCA-UNVERIFIABLE` (exit 77), which `src/pdca_harness/gates.py` routes to SUMMARY §6
NEEDS-HUMAN (non-gating), exactly as the brief predicts.

`patch.diff` therefore contains **only** the new test file. I attempted the docker
`run-verify.sh` (engine runner) but docker invocation is blocked in this sandbox; the
classification is deterministic from the script and is the basis for the note below.

### The POTFILES.skip tension (NEEDS-HUMAN at commit)

The brief's *New/removed files* field and the standing "register new core .py in
POTFILES" MUST both call for adding the test to `po/POTFILES.skip` (it has no
translatable strings). I deliberately did **not** put that change in `patch.diff`,
because it would convert C4 from the brief-expected *unverifiable* into a blocking
*hard fail*:

`run-verify.sh` (lines 142-162) classifies every non-`*_test.py` file in the patch as a
production file. `po/POTFILES.skip` is non-test, so with it in the patch C4 no longer
takes the test-only `PDCA-UNVERIFIABLE` branch (line 162); instead it runs the
red/green contract — the red pass does `git checkout -- po/POTFILES.skip` (lines
197-199), the test still passes (POTFILES has no bearing on export behaviour), so
`red-without-fix` = FAIL and the gate returns rc 1 → `gates.py` status **fail**
(gating). I.e.:

- test-only → C4 **unverifiable** (→ §6, non-gating) ✓ matches brief; T2-potfiles
  raises one **advisory** note;
- test + POTFILES.skip → C4 **hard fail** (gating, blocks sign-off); T2 passes.

A single `patch.diff` cannot satisfy both blocking-C4 and T2 for a verify-first
new-test-file bundle under the current harness. I chose the non-blocking path that
matches the brief's explicit prediction, and surface the registration here so the human
applies it when committing (or moots it by closing by-design — the brief notes the
maintainer's standing position and disposition hint both point that way).

**Exact hunk to add to the commit** (the test sorts before `exportvcard_test.py`,
`po/POTFILES.skip:568`):

```diff
--- a/po/POTFILES.skip
+++ b/po/POTFILES.skip
@@ -565,6 +565,7 @@ gramps/plugins/export/__init__.py
 #
 # plugins/export/test directory
 #
+gramps/plugins/export/test/exportgedcom_place_test.py
 gramps/plugins/export/test/exportvcard_test.py
 #
 # plugins/gramplet directory
```

(Harness follow-up worth filing per `pdca-harness-changes-via-issue`: let a
verify-first test-only patch carry its POTFILES registration without tripping the C4
red/green contract — e.g. treat the two POTFILES manifests as non-production for the
red-pass classification.)

## Alternatives considered

- **subprocess `Gramps.py -e - -f ged`** (the pattern `exportvcard_test.py` uses):
  rejected. It needs the full CLI runtime and still imports `gramps.gui` via
  `exportgedcom`; under the headless C4 core runner (plain `python3`, no display) that
  is the GUI-import crash the brief warns about. The in-process writer + `sys.modules`
  stub is ~40 lines and stays headless.
- **Mutating `config` (`preferences.place-auto`)** to force `display()` down the
  `place.title` branch: rejected as an unnecessary global side effect. The test sets
  the `PlaceName` value so it works under the default `place-auto=True` branch
  (`gramps/gen/display/place.py:88` → `gramps/gen/utils/location.py:39`) *and* sets the
  title, so it is robust to either config default without touching global state.
- **Writing a production fix:** out of scope and impossible — there is nothing to fix;
  the type→ADDR/CITY mapping was already removed by the 5.0 rewrite. Fabricating a
  no-op "fix" purely to make C4 go red→green would be dishonest (the test would no
  longer be driving a real defect).
