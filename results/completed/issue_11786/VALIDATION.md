# VALIDATION — 2026-06-07 (provenance note; disposition HOLDS)

> Additive note from the older-process revalidation pass
> (`process/validate-numbered-bundles.md`). It does **not** change §9 — the frozen
> accept stands and is now better-supported.

**The frozen `check-gates.json` records `C4-verify: green-with-fix=FAIL` — that FAIL is
a stale engine artifact, not a defect.** It was the headless GTK-import crash: the
shipped test imports `gramps.plugins.lib.libpersonview` → `peoplemodel` → `Gtk`, and at
freeze time importing a `gramps.gui.*` chain headless core-dumped (the same bug
`issue_headless-ut-segfault` later fixed).

**Re-run 2026-06-07 against the current tree:** `C4-verify: green-with-fix=PASS /
red-without-fix=PASS`. The test now imports and runs; the
`gtk_icon_theme_get_for_screen` line is a non-fatal `Gtk-CRITICAL`, not the crash. The
fix (invalidate the `(tag_handle,"TAG_NAME")` cache entry in `tag_updated`) is a correct
cause-removal; the decorrelated reviewer found C5 passes (no symptom-guard).

**Cause of the flip — proven, not assumed.** The test imports
`gramps.plugins.lib.libpersonview` → `gui.views.listview` → pageview → `grampletbar` →
`grampletpane`, whose `LinkTag` class body built a `Gtk.Label` at import — a fatal
`Gtk-ERROR: Can't create a GtkStyleContext without a display connection` (SIGTRAP) with
no display. The fix is `issue_headless-ut-segfault` (commit `f4f94f34db`, lazy
`LinkTag.linkcolor`). Verified by isolating the variable: re-running this bundle's
C4-verify with the **current gate** against the tree **without** that fix (commit
`f4f94f34db^`) reproduces the frozen result exactly — `green-with-fix=FAIL /
red-without-fix=PASS`, dying with the same `Gtk-ERROR` core dump in both runs. So the
flip is the **dependency fix landing in the tree**, *not* the C4 gate redefinition (the
gate code was identical across both runs). (This also resolves the apparent
green=FAIL/red=PASS asymmetry: an import crash fails both runs, which the C4 contract
reads as green-FAIL + red-PASS.)

**Dependency / caveat (the one real action item).** This PASS was obtained on the
primary `gramps` checkout, which currently carries the **unmerged**
`issue_headless-ut-segfault` fix. That fix is **not** in clean `maintenance/gramps61`
(11786's stated target). On the clean target branch the test still core-dumps at import.
So 11786's regression test is only runnable once the segfault fix lands on gramps61 —
i.e. there is a **merge-order dependency**: `issue_headless-ut-segfault` must precede (or
land with) 11786, OR 11786's test must adopt the same import-safety treatment (e.g. stub
`gi` before import, as `issue_13636`'s test does). Disposition still HOLDS; flag this for
the human at contribution time.
