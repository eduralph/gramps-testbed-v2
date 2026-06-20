# Build notes — issue 13864 (dashboard-column-count-crash-locks-tree)

> Withheld from the reviewer; for the human at sign-off.

## Root cause (diagnosed, not recalled)

The Dashboard "Number of Columns" control (`add_pos_int_entry`,
`gramps/gui/widgets/grampletpane.py:1635`) accepts **any** positive integer and feeds
it straight into `GrampletPane`, which builds **one GTK container box per column** in a
`for i in range(self.column_count)` loop (`grampletpane.py:1059`, and again in
`set_columns` at `:1399`). The value is never bounded, so a large count (the reporter
used 1000) makes GTK allocate an enormous homogeneous layout; the process freezes ("Not
responding"), is then killed, and because it died with the database open the **family
tree lock file is never released** — hence the locked tree on restart.

I reproduced and quantified the unbounded-allocation cause headlessly (Gtk.OffscreenWindow,
no DB needed):

| columns | result |
|---|---|
| 100 | built in 0.35 s (4 600 px wide) |
| 1000 | built in 3.5 s (46 000 px wide) — slow; with real gramplets each doing DB work per keystroke-rebuild this is the reporter's freeze |
| 200000 | **did not finish in 120 s** (timeout-killed) — the freeze→crash territory |

So the defect is exactly the brief's hypothesis: *an unbounded user-supplied layout
parameter drives unbounded widget allocation.* The fix restores the invariant by
**bounding/validating the value before it drives allocation**, at every entry point.

## The fix

New import-light module `gramps/gui/grampletconfig.py` (imports nothing from `gi` /
`gramps.gui`, so it is unit-testable under the headless C4 runner) exposing
`MAX_GRAMPLET_COLUMNS` and `clamp_column_count(num)` → `min(max(int(num), 1), MAX)`.

Production routes **all three** column-count entry points through it (covering the
*defect category*, per the brief's SELF-TEST — not just the single 1000 repro):

- `GrampletPane.__init__` default / kwargs — `grampletpane.py:1020` (target branch).
- `load_gramplets` reading the saved `.ini` value — `grampletpane.py:1200` (the value
  is a string from disk; `clamp_column_count` coerces + bounds it).
- `set_columns`, the configure-dialog path — `grampletpane.py:1386-1388` (replaces the
  old `if num < 1: num = 1` floor, which had no ceiling).
- `config_panel` help text updated to advertise the accepted range —
  `grampletpane.py:1635`.

`po/POTFILES.skip` registers both new `.py` files (neither carries translatable
strings; the one `_()` help-text string lives in `grampletpane.py`, already in
`POTFILES.in`) per doc 16 §Adding and removing Python files.

Test: `gramps/gui/test/grampletconfig_test.py` drives the **same** `clamp_column_count`
the production paths call (not a hand-copy), asserting any accepted value — reasonable,
zero/negative, the 1000 repro, and pathological `200000` / `10**9`, plus the `.ini`
string form — yields a bounded count in `[1, MAX]`, and that the resulting
`range(column_count)` allocation is bounded. Red→green confirmed via
`run-verify.sh`: green-with-fix=PASS / red-without-fix=PASS (red leg fails with
`ModuleNotFoundError: gramps.gui.grampletconfig`, i.e. the test genuinely depends on the
production module). `black 26.5.0 --check` clean on all three touched `.py` files.

## NEEDS-HUMAN — UX-direction flag (the brief asks for this)

The brief puts "imposing a product-level max-columns policy / a hard cap" **out of
scope** as a UX-direction call, and says *flag to the human if the only viable fix is a
hard cap*. It is: without an upper bound, the invariant ("any accepted value →
survivable") cannot hold — a sufficiently large value always exhausts memory. So a
ceiling is unavoidable to stop the crash; what is a **UX judgment** is the *number*.

- I chose `MAX_GRAMPLET_COLUMNS = 100` deliberately as a **safety ceiling**, not a
  feature policy: 100 columns build in 0.35 s (well clear of the freeze), yet 100 is
  ~10× beyond any conceivable real Dashboard layout, so practically no genuine user is
  constrained. This is intentionally *not* the prior draft's `10`, which is low enough
  to constrain legitimate layouts and to overlap the separate 13865 "~20 column"
  domain.
- **Please confirm or adjust the ceiling at sign-off.** If product direction wants a
  different number (or a spin-button with an enforced range instead of a free-text
  entry — a UX redesign that is out of scope here), only the constant
  `MAX_GRAMPLET_COLUMNS` changes.

## Scope: 13864 only, NOT 13865

The brief flags 13865 (a separate gramplet-*placement* defect) as out of scope and
"likely a different root cause — verify before a shared fix." I did not attempt to fix
13865, and the commit/PR reference 13864 only. The earlier local draft commit
(`dcd69a0`, "Limit dashboard gramplet columns") claimed "Fixes 13864, 13865" and set the
cap to 10 explicitly to dodge "the known 20-column failure" — that **conflates the two
tickets** and silently bakes in a UX policy. This patch deliberately does neither: the
ceiling is a crash-safety bound for 13864's unbounded-allocation cause, and 100 ≫ 20, so
it makes no claim about 13865's placement behaviour.

## Alternatives considered / ruled out

- **Clamp in `set_columns` only (one setter).** Rejected by the brief's SELF-TEST and by
  the cause: the saved `.ini` (`load_gramplets`, `:1200`) and the constructor default
  (`:1020`) are independent entry points — a poisoned `.ini` with `column_count=1000`
  would crash at startup *before* the dialog is ever opened. One setter leaves two paths
  unbounded. Cost of doing it right: +2 call sites (3 lines) vs the 1-line single-setter
  version — negligible, and required for the invariant.
- **Remove the cause instead of bounding (e.g. lazy/virtualized columns, or building
  columns on demand).** That is a `GrampletPane` rearchitecture touching the column
  build (`:1057-1061`), `place_gramplets` (`:1144-1183`), `set_columns` (`:1386-1405`)
  and the detach/redock paths (`:312-345`) — on the order of 100+ lines across the
  widget, and it changes runtime layout behaviour for every Dashboard user. It does not
  even remove the need for *some* bound (a virtualized 10**9-column scrollport is still
  nonsense input). Disproportionate to restoring the stated invariant.
- **Validate in the dialog widget (reject non-conforming input in the `Gtk.Entry`).**
  That is "redesigning the Gramplet-Layout UX" (out of scope) and still wouldn't guard
  the `.ini`/default paths. The model-side clamp guards every path with one helper.

## Citations (target branch `upstream/maintenance/gramps61`)

- `gramps/gui/widgets/grampletpane.py:59` — import insertion point.
- `gramps/gui/widgets/grampletpane.py:1020` — `__init__` column_count default (clamped).
- `gramps/gui/widgets/grampletpane.py:1200` — `load_gramplets` `.ini` read (clamped).
- `gramps/gui/widgets/grampletpane.py:1386-1388` — `set_columns` floor → clamp.
- `gramps/gui/widgets/grampletpane.py:1635` — `config_panel` add_pos_int_entry (helptext).
- `gramps/gui/widgets/grampletpane.py:1059`, `:1399` — the unbounded `range(column_count)`
  allocation loops the clamp protects.
- `po/POTFILES.skip:343-344`, `:463-464` — alphabetical insertion points for the two new
  files.
