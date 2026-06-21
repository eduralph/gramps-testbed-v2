# Brief — issue 6825 / surname-plugins-ignore-group-mapping

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** surname-plugins-ignore-group-mapping
- **Defect:** As filed (2013, v3.4.5): the surname-related consumers disagree on whether they
  honour the "Group As" surname mapping. TopSurnamesGramplet and the FilterByName quick view
  used `Name.get_group_name()` (respecting overrides); StatsGramplet and the SameSurnames quick
  view used `Name.get_surname()` (ignoring local *and* global Group-As mapping), so two
  surnames the user grouped together were still counted/displayed separately.
- **Success criterion:** Two persons whose surnames are grouped together via "Group As → Group
  All" (the global name-group mapping) are treated as one group consistently by the surname
  consumers — i.e. the SameSurnames quick view (and any remaining surname-counting consumer)
  group them the same way TopSurnamesGramplet does. **Verify-first**: Do MUST first reproduce
  on maintenance/gramps61 before patching — see Scope; much of the original code has changed.
- **Invariant to restore:** Surname-grouping consumers apply the **same** Group-As mapping
  (local override and the database global name-group table) consistently — counting and
  matching surnames by the user's chosen grouping, not by raw `get_surname()` in some places and
  the grouped name in others. (Internal Gramps rule; no external canon.) SELF-TEST: the property
  is "all surname consumers agree on the grouping", not "patch StatsGramplet" — widen any fix to
  the divergence, not one module.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Scope:** the divergence in how surname consumers resolve the grouped surname. NOTE the
  code has evolved since the report and Do must re-establish what still reproduces:
  `gramps/plugins/gramplet/statsgramplet.py` no longer lists/counts surname frequencies (it
  counts incomplete names — the StatsGramplet symptom appears **obsolete**); the residual
  candidate is the SameSurnames quick view, where `run()` uses `get_group_name()`
  (`gramps/plugins/quickview/samesurnames.py:121`) but the `SameSurname` filter rule's
  `apply_to_one` matches on literal `get_surname()` (`samesurnames.py:60-63`), which can miss
  group-mapped surnames — this divergence is **still present** on gramps61 (verified). Establish
  whether it yields a user-visible wrong result first, then restore consistency. / out of scope: a
  shared `Utils.get_surname()` refactor across all four plugins (the reporter's 2013 patch
  shape) unless Do finds the divergence genuinely spans them — do not over-restructure on the
  strength of a stale patch.
- **Repro instruction:** On maintenance/gramps61: add two persons, surnames Smith and Jones;
  edit Jones's surname → set "Group As" to "Smith" and choose "Group All" (global). Then compare
  TopSurnamesGramplet against the SameSurnames quick view (and StatsGramplet) — confirm whether
  they group Jones under Smith consistently.
- **Test file:** gramps/plugins/quickview/test/samesurnames_test.py (or extend
  `gramps/plugins/gramplet/test/topsurnamesgramplet_test.py`) — a data-layer test driving the
  **production** surname-grouping path with a global name-group mapping set, asserting the
  consumers agree. Ships only if Do confirms a live divergence; if the divergence is gone, route
  to §6 (no fix). New `*_test.py` → register in `po/POTFILES.skip`.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **Prior-art check (triage cycles):** `git log upstream/maintenance/gramps61` on the
  statsgramplet / samesurnames / topsurnamesgramplet paths — StatsGramplet's surname-listing was
  removed over the years (which dissolves the primary symptom); no targeted Group-As-consistency
  fix found for SameSurnames. Closed-PR search by these paths advised.
- **Mantis:** 6825
- **Disposition hint:** POSSIBLY-FIXED → verify first
