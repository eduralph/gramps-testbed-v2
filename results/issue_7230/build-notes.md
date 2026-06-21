# Build notes — issue 7230 (citation-tree-hides-sources-without-citations)

## TL;DR / disposition

**Verify-first finding: the defect does NOT reproduce on `maintenance/gramps61`.
The bug is already fixed.** A source with zero citations *is* shown as a top-level
node in the Citation Tree View. There is therefore **no production change** — this is
an evidenced already-fixed close, shipped with a headless regression test that drives
the production model and guards the restored invariant.

## Verify-first: I reproduced (attempted) before touching anything

Per the brief's `Success criterion` ("Verify-first: Do MUST reproduce on
maintenance/gramps61 before changing anything"), I built the **production**
`CitationTreeModel` against an in-memory SQLite db holding a citation-less source and
inspected the resulting node tree, headless (no display, no D-Bus — `DISPLAY` /
`WAYLAND_DISPLAY` unset to mirror the C4 core runner):

```
num sources 1   num cit 0
tree keys: [None, '<lonely-source-handle>']
source in tree: True
top children count: 1            # the citation-less source is a top-level node
```

And with a mixed db (one cited source + one citation-less source):

```
top-level handles: {<cited>, <lonely>}
cited source top-level: True
lonely source top-level: True
cited source children: {<citation-handle>}   # citation is a child of its source
lonely source children: 0                     # citation-less source: present, no children
```

So the *2013 report* ("a source with no citations does not appear at all") is the
**opposite** of current behaviour. The defect is closed. The `Success criterion`
("every source is a top-level node, including zero-citation sources") and the
`Invariant to restore` both **hold** on `maintenance/gramps61`.

## Root cause of the fix (why it is already fixed)

`gramps/gui/views/treemodels/citationtreemodel.py` is now a two-cursor
`has_secondary=True` model:

- The **primary** cursor iterates *all sources*, independent of citations —
  `citationtreemodel.py:83-85` binds `number_items` / `map` / `gen_cursor` to
  `db.get_number_of_sources` / `db.get_raw_source_data` / `db.get_source_cursor`.
- `add_row` (`citationtreemodel.py:192-200`) adds **every** source as a top-level
  node unconditionally: `self.add_node(None, handle, sort_key, handle)` — no
  dependence on whether a citation references it.
- The **secondary** citation cursor (`citationtreemodel.py:150-152`, `add_row2` at
  `:202-224`) only adds citation *children*. Its `else` branch (`:217-224`) that
  back-fills a missing source is now effectively defensive, because the primary
  cursor runs first (`treebasemodel.py:541-550`) and has already added every source.

The original 2013 defect existed because, in the pre-refactor single-cursor design,
sources were materialised only as a side effect of iterating citations — so a source
nobody cited never got a node. The `has_secondary` source-cursor design removed that
coupling. `git log maintenance/gramps61 -- citationtreemodel.py` shows no targeted
"show empty sources" commit; the behaviour change rode in with the tree-model
refactor, matching the brief's prior-art note.

## The regression test

`gramps/gui/views/treemodels/test/citationtreemodel_test.py` (new) drives the
**production** `CitationTreeModel.__init__` build — not a re-implementation — against
an in-memory db with one cited and one citation-less source, and asserts:

- `test_citationless_source_is_a_top_level_node` — the citation-less source is a
  top-level node (`model.tree[None]` child) with no children.
- `test_every_source_is_listed_independent_of_citations` — both sources are top-level
  nodes; the citation is a *child* of its source, not a top-level node.

It is the real production path: `CitationTreeModel(db, uistate=None, search=…)` runs
`TreeBaseModel.__init__` → `rebuild_data` → `_rebuild_search` → `add_row` for every
source from `get_source_cursor`. Nothing is copied or stubbed.

### Headless safety (why it runs under the plain C4 core runner)

- `uistate=None` is safe: the loading `ProgressMonitor`
  (`treebasemodel.py:557-564`) creates its dialog **lazily** and only when an op
  exceeds the popup threshold (`progressdialog.py:326-332, 369`). A one/two-row db
  completes instantly, so no GTK dialog and no display are needed. During the build
  `rebuild_data` sets `_in_build = True` (`treebasemodel.py:510`), which suppresses
  the `row_inserted` GTK signal emission in `add_node` (`treebasemodel.py:671-675`).
- `search=(False, None, False)` is the "no filter / no search" tuple a view passes;
  it routes `set_search` to the no-op branch (`treebasemodel.py:467-487`) and avoids
  the `None[2]` crash the bare default would hit for a `has_secondary` model
  (`treebasemodel.py:490-491`).
- `import gi; gi.require_version("Gtk", "3.0")` is set before the gramps GUI import,
  matching the established pattern in `gramps/gui/plug/test/windows_test.py:54-58`.
  The C4 docker image carries only the Gtk 3 typelib so the bare `from gi.repository
  import Gtk` in `treemodels/__init__.py → peoplemodel → … → widgets/buttons.py`
  resolves to 3.0 there; the explicit pin makes the test robust on hosts that also
  have Gtk 4 (where the default would otherwise load Gtk 4 and break the import at
  `widgets/buttons.py:50`, `Gtk.IconSize.MENU`).

### Red→green evidence

I ran the test headless (display + Wayland unset, Gtk pinned to 3.0 to reproduce the
docker resolution) via `python3 -m unittest` — the same invocation the C4 core runner
uses:

```
test_citationless_source_is_a_top_level_node ... ok
test_every_source_is_listed_independent_of_citations ... ok
Ran 2 tests in 0.026s — OK
```

The patch applies cleanly to a pristine `maintenance/gramps61` worktree
(`git apply --check` on the clean `gramps-6.1-lane0` worktree: exit 0). `black --check`
on the test file: unchanged (commit-ready for gramps' black pre-commit hook).

## Expected C4-verify behaviour — please read before sign-off (§6)

This is an **already-fixed** bug, so there is **no production cause to revert**. C4's
red→green mechanic (`run-verify.sh`) reverts the patch's non-test file(s) and expects
the test to go *red*. Here the only non-test file is `po/POTFILES.skip` (a translation
bookkeeping entry, not a fix), so the "red" leg reverts it, the test stays **green**,
and C4 reports `green-with-fix=PASS / red-without-fix=FAIL`.

**That FAIL is the expected signature of an already-fixed defect, not a bogus test.**
The red→green *mechanic* cannot demonstrate a regression for a bug that upstream
already resolved by refactor — there is no production line whose removal re-hides the
source. The test is green and genuinely guards the invariant against a *future*
regression (it would go red if `add_row` or the primary source-cursor wiring were
reverted to the pre-refactor coupling). I recommend the human accept C4 on that basis
at sign-off (clear the §6 item), exactly as the harness's `PDCA-UNVERIFIABLE` path is
intended for "the red/green mechanic genuinely cannot run."

## POTFILES registration

The new `.py` has no translatable strings, so it is registered in
`po/POTFILES.skip` (doc 16 §Adding and removing Python files), keeping the published
PR complete and `T2-potfiles`-clean.

## Alternatives considered / ruled out

- **Test `add_row` in isolation (bypass `__init__`).** Cheaper to set up, but it would
  exercise only *one* method, not the source-cursor wiring (`:83-85`) that is the
  actual reason every source appears — and it would not be the production build path.
  The full-build test costs ~0.03 s headless and exercises the real path, so there is
  no reason to weaken it.
- **A live `uistate`/GTK ManagedWindow / interface test.** Unnecessary and
  C4-incompatible: it would import `gramps.gui.*` GUI widgets that need a display and
  would crash the headless core runner. The data-layer build is sufficient and the
  brief explicitly preferred it ("data-layer test driving the production
  CitationTreeModel").
- **A production change.** None is warranted: the `Invariant to restore` is already
  restored. The smallest change that restores the invariant is the empty change; per
  `docs/principles.md` §1.2/§2 a fabricated edit would be wrong, not minimal.
- **Ship no test (pure evidenced close).** The brief asks for "a regression test if
  practical," and it is practical headless (proven above), so the test adds durable
  regression protection at negligible cost.
