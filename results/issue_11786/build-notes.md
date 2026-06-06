# Build notes — issue 11786 / tag-rename-stale-name-in-listview

> Withheld from the reviewer. Rationale, alternatives, and what I ruled out.

## Root cause (verified by reading the target branch `maintenance/gramps61`)

The People list view caches a tag's *display name* keyed by the **tag** handle,
not the person handle:

- `PeopleBaseModel.get_tag_name(tag_handle)` →
  `get_cached_value(tag_handle, "TAG_NAME")` / `set_cached_value(tag_handle,
  "TAG_NAME", …)` — `gramps/gui/views/treemodels/peoplemodel.py:511-521`.
- The cache itself is the model's LRU; `clear_cache(handle)` deletes
  `lru_data[handle]` — `gramps/gui/views/treemodels/basemodel.py:46-57`.

On rename the DB emits `tag-update`, wired in
`gramps/gui/views/listview.py:850` to the view's `tag_updated`. For the People
view that handler is `BasePersonView.tag_updated`
(`gramps/plugins/lib/libpersonview.py:535-550` on the unpatched branch): it
resolves the tagged **person** backlinks and calls `row_update`
(`gramps/gui/views/listview.py:927`). `row_update` →
`update_row_by_handle(person_handle)` → `clear_cache(person_handle)`
(`gramps/gui/views/treemodels/flatbasemodel.py:683`, mirrored
`treebasemodel.py:849`). So only the **person** cache entries are dropped; the
`(tag_handle, "TAG_NAME")` entry survives, and the re-render reads the stale old
name. Confirmed the class owning `tag_updated` is `BasePersonView`
(`libpersonview.py:77`); `PersonListView`
(`gramps/plugins/view/personlistview.py:49`) inherits it.

Note the tag *colour* already refreshes: `column_tag_color` is keyed by
`data.handle`, i.e. the **person** handle (`peoplemodel.py:523-528`), which
`row_update` does clear — which is why the original docstring said "when a tag
color changes" and why colour was never reported broken. Only the name, keyed by
the tag handle, goes stale. That matches the Mantis report exactly.

## The fix (one logical change)

`gramps/plugins/lib/libpersonview.py:535` — in `tag_updated`, before resolving
backlinks, drop the renamed tag's own cache entry:

```python
self.model.clear_cache(tag_handle)
```

`clear_cache(tag_handle)` removes `lru_data[tag_handle]` (the `TAG_NAME` entry)
and clears the path cache; the subsequent `row_update` re-renders the affected
person rows, and `get_tag_name` now misses the cache and re-reads the new name
from the DB. Minimal, targeted at the exact stale key the brief names. Docstring
updated from "tag color changes" to "tag changes (name, colour or priority)"
since the handler now covers name too.

## Alternatives considered and ruled out

- **Clear the whole model cache (`self.model.clear_cache()`):** correct but
  throws away every row's cached render on any tag edit — needless churn on
  large trees. Per-tag-handle invalidation is the precise fix.
- **Invalidate inside `get_tag_name` / the treemodel:** the model has no signal
  that a tag changed; the view is where the `tag-update` signal lands. Redesigning
  the treemodel cache is explicitly out of scope per the brief.
- **Fix the sibling views too** (`eventview`, `citationlistview`, `familyview`,
  `mediaview`, `repoview`, `sourceview`, `noteview`, `libplaceview`,
  `citationtreeview` — each has an identical `tag_updated` that only differs by
  `include_classes`, and each treemodel caches `TAG_NAME` by tag handle, e.g.
  `citationbasemodel.py:317-324`, `eventmodel.py:190`): the same root cause
  applies there, so they have the same latent bug. I deliberately scoped this PR
  to People View — it is the brief's success criterion and test target, and "one
  logical change per PR" argues against touching 10 files / broadening the blast
  radius in a maintenance-branch fix. A clean follow-up would lift `tag_updated`
  (and the per-tag cache clear) into a shared `ListView` base so all list views
  inherit the invalidation; flagged for the reviewer as a known, out-of-scope
  sibling issue, not introduced by this change.

## Tests

Two tests, matching the brief's "GUI repro is load-bearing; a `*_test.py`
companion is welcome" guidance:

1. **Load-bearing GUI repro (advisory tier, pre-existing in the bundle):**
   `engine/interface/test_bug_0011786_tag_rename_listview.py` — drives Tags →
   Organize Tags → Rename under AT-SPI/dogtail and asserts the People View Tags
   column shows the new name without restart. INTEGRATION §3/§4 records the
   interface tier as advisory (per-fix interface-level C4 is staged), so this is
   the human-weighed characterisation, not the gate.

2. **Gated headless companion (the C4-verify proof):**
   `gramps/plugins/lib/test/libpersonview_test.py` (core convention: `test/`
   package + `<module>_test.py` suffix, INTEGRATION §3; new empty
   `test/__init__.py` ships alongside). It primes the **real** cache path
   (`BaseModel` LRU + the real `PeopleBaseModel.get_tag_name`) with the old name,
   renames the tag in a real sqlite DB, fires the **real**
   `BasePersonView.tag_updated` (unbound, on a `SimpleNamespace` stand-in for the
   view so no Gtk widgets are constructed — only the three collaborators
   `tag_updated` touches: `model`, `dbstate.db`, `row_update`), and asserts
   `get_tag_name` returns the new name.
   - **Pre-fix:** the stale `(tag_handle, "TAG_NAME")` entry survives →
     `get_tag_name` returns `"ToDo"` → `assertEqual(NEW)` fails (**red**).
   - **Post-fix:** `clear_cache(tag_handle)` drops it → `get_tag_name` re-reads
     `"ZZRenamed11786"` (**green**).

   This is the test `run-verify.sh` selects (it picks the `*_test.py` file from
   `patch.diff` as the test, reverts the other patched file — `libpersonview.py`
   — for the red check; the empty `__init__.py` has no `+++ b/` hunk so it is
   neither test nor reverted-prod, the same mechanism used by issue_13205).

   Why headless-importable without a display: importing `gramps.gui.*` /
   `libpersonview` pulls in Gtk but does not open a display at import time, and
   the test never instantiates a widget. Precedent: issue_13205's core test
   imports the Gtk-bound `gramps.plugins.tool.mergecitations` and runs green under
   `run-verify.sh` core mode (which sets `XVFB=""`).

## Verification status

- `git apply --check` of `patch.diff` against `maintenance/gramps61`: **clean**
  (all three files).
- `run-verify.sh` (the authoritative red→green C4 gate) is Docker-backed and was
  **blocked pending human approval in this sandbox** — I could not execute it
  here. It must be run by the driver/human:
  `PDCA_BUNDLE=results/issue_11786 ./engine/scripts/ubuntu/run-verify.sh`.
  I did not hand-roll a `docker run` (would hang on the Gtk import per the Do
  guidance). The red→green argument above is reasoned from reading the cache
  code, not yet machine-confirmed; flag for sign-off.

## Citations (target branch `maintenance/gramps61`)

- Fix site: `gramps/plugins/lib/libpersonview.py:535` (`tag_updated`), class
  `BasePersonView` at `:77`.
- Stale cache key: `gramps/gui/views/treemodels/peoplemodel.py:511-521`
  (`get_tag_name`).
- Cache primitive used: `gramps/gui/views/treemodels/basemodel.py:46-57`
  (`clear_cache`).
- Signal → handler: `gramps/gui/views/listview.py:850` (`tag-update` wiring),
  `:927` (`row_update`).
- Person-only cache clear: `gramps/gui/views/treemodels/flatbasemodel.py:683`
  (`update_row_by_handle` → `clear_cache(person_handle)`).
- Inheriting subclass: `gramps/plugins/view/personlistview.py:49`.
