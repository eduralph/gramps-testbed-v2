# Brief — issue 13174 / addon-manager-refresh-missing-listing-crash

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** addon-manager-refresh-missing-listing-crash
- **Defect:** In the Addon Manager, adding a Project URL whose listing `.json` is missing (e.g. an old `gramps51` path, or any URL where `addons-<lang>.json` 404s) and pressing **Refresh** can **hard-crash** Gramps. jralls diagnosed the crash as a **dangling window pointer passed to the Gtk draw cycle** when the refresh fails (note 6: "not a Mac-specific problem"). The 404 itself is expected; the crash is not. (Mantis 13174; reproduced on Win10 5.2.0-rc1 first-refresh, note 3; crash report note 5.)
- **Success criterion:** Refreshing the Addon Manager against a Project whose listing file is missing (HTTP 404) **fails gracefully** — Gramps does not crash and no dangling window is left — the not-found is surfaced as a handled warning/condition, and a subsequent valid refresh still works.
- **Invariant to restore:** A failed Addon Manager refresh (missing/404 listing) must not crash the process or leave a dangling window pointer in the Gtk draw cycle — the refresh path tears down cleanly on failure. (A network/HTTP failure during refresh must not corrupt the widget/window lifecycle. Source: the Addon Manager refresh path in `gramps/gui/plug/_windows.py` and the listing fetch in `gramps/gen/plug/utils.py`.) SELF-TEST: stated over *any* failed refresh, not the one 5.1 URL — the defect category.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61 (core).
- **Surfaces:** gui
- **Scope:** an Addon Manager refresh against a missing/404 listing leaves a dangling window pointer and crashes — make the failed-refresh path tear down cleanly (no crash). Optional, if cheap and in the same teardown path: actionable user feedback for a bad/empty Project URL (note 8 items 1–3). / **out of scope:** the locale-fallback ask (English fallback already exists — that is **13906**, a separate close); changing the listing format or `make.py` output; the expected 404 warning itself.
- **Repro instruction:** **VERIFY-FIRST** — the crash was reported on 5.2.0-rc1 and several testers could not reproduce on later Win10/11 builds (notes 1, 2, 7); confirm it still reproduces on `maintenance/gramps61` before writing a fix. If it no longer reproduces, the outcome is an **evidenced can't-reproduce close** citing the builds tried. Repro path: Addon Manager → add a Project URL pointing at a nonexistent/old listings dir (e.g. `…/isotammi-addons/master/addons/gramps51`) → Refresh → (first time) crash to desktop. Root cause to confirm against the refresh/teardown path in `gramps/gui/plug/_windows.py` — the dangling-window-pointer hypothesis (note 6).
- **Test file:** prefer a **headless** core unit test on the refresh-with-missing-listing path if reachable without the live GUI: `gramps/gen/plug/test/utils_test.py` (the fetch/not-found handling) or `gramps/gui/plug/test/_windows_test.py` — `test/` singular, `*_test.py` suffix (INTEGRATION §3) — asserting a 404/missing listing is handled without exception. The GUI crash itself (dangling window) may only be reachable via an interface test `tests/interface/test_bug_13174_addon_refresh.py` in gramps-testbed (advisory); if the red→green C4 mechanic can't run, flag `PDCA-UNVERIFIABLE` per INTEGRATION §3.
- **Citations expected:** Do must cite path:line on `maintenance/gramps61` for every change.
- **New/removed files:** if a new core `test/` file is added, register it in `po/POTFILES.skip` (no translatable strings) per doc 16 §Adding and removing Python files.
- **Prior-art check (triage cycles):** search by path at Do time — `git -C ../gramps log upstream/maintenance/gramps61 -- gramps/gui/plug/_windows.py gramps/gen/plug/utils.py` (also `master`) + closed/rejected PRs for "addon manager" / "refresh crash". Related: **13906** (shares the 404 *symptom* but a *different cause* — working-fallback close vs this crash; do **not** bundle, per both verdicts' cluster note).
- **Mantis:** 13174
- **Disposition hint:** POSSIBLY-FIXED → verify first (likely-fix if it still reproduces; evidenced can't-reproduce close otherwise)

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
