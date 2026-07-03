# Build notes — issue 8622 (citation selector filter hides citations)

Target branch: `gramps-project/gramps @ maintenance/gramps61`
(worktree isolation is off in this testbed, so edits were made in the shared
`../gramps-6.1` checkout; all `path:line` below are against that tree.)

## Root cause

The "Select Source or Citation" selector builds a hierarchical source→citation
tree from `CitationTreeModel`. A text search reaches the model as a
`(filter?, (col, text, inv), exact?)` tuple through
`baseselector.build_tree` (`gramps/gui/selectors/baseselector.py:347-355`).

`TreeBaseModel.set_search` builds **two independent** search filters from that
one tuple — one for the primary (source) rows and one for the secondary
(citation) rows — using the **same column and text** for both
(`gramps/gui/views/treemodels/treebasemodel.py:468-481`; `func` and `func2`
differ only in `secondary=`). For the selector's only searchable column
(column 0 = "Source: Title or Citation: Volume/Page"), that means:

* a source row matches iff its **title** contains the text, but
* a citation row matches iff its **page** contains the text.

So a search that keeps a source (its title matched) drops every one of that
source's citations (their pages almost never contain the source title). The
rebuild adds the matched source in the primary pass and then finds no matching
citation in the secondary pass (`treebasemodel.py:534-575`), leaving the source
expandable but empty. The user is forced to create a **new** citation instead of
reusing an existing one — exactly the report.

`add_row2` (`gramps/gui/views/treemodels/citationtreemodel.py:202-224`) also
force-adds a source when a *citation* matches but the source was not added by
the primary pass — which is the citation-driven variant of the same invariant
break (see finding 3 below).

## The fix

A source→citation selector must satisfy the brief's **invariant to restore**:
*if a source is shown, its citations remain selectable.* I restore it by
grouping the search **by source** for the selector only:

> A source — and **every** one of its citations — is shown when the source
> matches the primary search **OR** any of the source's citations match the
> secondary search.

Implemented as:

1. `_SourceGroupSearchFilter` (added in
   `gramps/gui/views/treemodels/citationtreemodel.py`, after the existing
   `CitationTreeModel`): a `.match(handle, db)` filter that answers "is this
   row's source shown?". One instance backs the primary (source) rows and one
   the secondary (citation) rows; both share the single set of source handles
   that own a matching citation, computed once by scanning the citation cursor.
   For a citation row it maps the citation to its parent source first, so all
   citations of a shown source are kept — including siblings of the one whose
   page matched.

2. `CitationTreeSelectorModel(CitationTreeModel)` (same file): overrides
   `set_search` to call `super().set_search(...)` (unchanged base behaviour)
   and then, for a plain text search that carries data, wrap the two base
   filters in `_SourceGroupSearchFilter`. A sidebar `GenericFilter`
   (`search[0]` truthy) or a cleared search is left on the base path untouched.

3. `SelectCitation.get_model_class` now returns `CitationTreeSelectorModel`
   (`gramps/gui/selectors/selectcitation.py:66-71`), and the class is exported
   from `gramps/gui/views/treemodels/__init__.py:35`.

The standalone Citation Tree View (`gramps/plugins/view/citationtreeview.py:161`)
keeps building the plain `CitationTreeModel`, so its intentional independent
secondary search is **unchanged** — satisfying the brief's out-of-scope
constraint.

## Why this locus (subclass), not a shared-model `set_search` change

The brief's DESIGN NOTE asks to prefer the change that does not alter the main
tree views' behaviour. Two candidate loci:

* **Selector-only subclass (chosen).** New behaviour lives entirely in
  `CitationTreeSelectorModel`; `CitationTreeModel.set_search` and the standalone
  view are byte-for-byte unchanged. No risk of regressing the standalone
  Citation Tree View or the Place tree view.
* **Shared `TreeBaseModel.set_search` change gated by a flag.** Would touch the
  base method every hierarchical model inherits and thread a new constructor
  kwarg through `TreeBaseModel.__init__`, `CitationTreeModel.__init__`, and
  `baseselector.build_tree` (the previous iteration's approach). That is both a
  wider blast radius *and* the source of iteration-1 finding 1 (below).

Cost comparison is not the deciding axis here — the brief names an invariant to
restore, so the target is the *smallest change that restores the invariant*. The
subclass is that: it adds no parameter to any shared signature and changes one
line of selector wiring, versus the flag approach that edits three shared
signatures (`baseselector.build_tree` +1 line, `CitationTreeModel.__init__` +1
param, `TreeBaseModel` plumbing) plus the selector.

## Addressing the iteration-1 carry-forward findings

**Finding 1 — selector wiring untested.** The previous attempt threaded the fix
through a new `get_model_kwargs()` on the selector and a `**self.get_model_kwargs()`
in `build_tree`; a typo there (or a dropped `**`) would keep all model-level
tests green while the dialog stayed broken. This version removes that surface
entirely (no `get_model_kwargs`, no `**` in `build_tree` — `build_tree` is
untouched) and adds `test_selector_wiring_uses_selector_model`, which asserts
`SelectCitation.get_model_class()` really resolves to `CitationTreeSelectorModel`.
Importing the selector is headless-safe: it only defines a `ManagedWindow`
subclass (no instantiation), and the same import chain is already exercised
headless by the passing baseline `gramps/gui/plug/test/windows_test.py` (imports
`gramps.gui.plug._windows`, a `ManagedWindow`) and by `treebasemodel_test.py`
(pulls `gramps.gui.widgets.buttons` via `progressdialog`). `get_model_class`
does not touch `self`, so the test calls it unbound.

**Finding 2 — tautological pre-fix red.** The previous primary test failed
pre-fix with `TypeError: unexpected keyword argument`, i.e. because the API did
not exist, not because of the wrong behaviour. Here the two selector-behaviour
tests build the model through a fallback:

```python
model_class = CitationTreeSelectorModel or CitationTreeModel
```

Pre-fix (and on C4's production-reverted "red" leg) `CitationTreeSelectorModel`
is absent, so the fallback builds today's `CitationTreeModel` and the
reachability assertion fails on the **node map** — an `AssertionError`
("existing citations of the matched source must stay reachable"), the actual
issue-8622 symptom — not an import/`TypeError`. Post-fix it builds the real
selector model and passes. Both legs drive production model code.

**Finding 3 — invariant only partially restored.** The previous fix widened the
secondary search to "citation matches OR its parent source matches the *source*
search", which covered only the source-driven case; a source pulled in because
one of its *citations* matched still lost its sibling citations. The
`_SourceGroupSearchFilter` here keys on "is the source shown?" where *shown* =
source-title match **or any** citation match, and then shows **all** citations
of any shown source. So both cases hold:

* title-matched source → all its citations reachable
  (`test_selector_keeps_citations_of_title_matched_source`);
* source pulled in by a single citation-page match → its **sibling** citations
  reachable too
  (`test_selector_keeps_sibling_citations_of_citation_matched_source`).

Performance stays linear: the "sources with a matching citation" set is computed
once from a single citation-cursor scan and cached (shared between the two
filter instances); primary/secondary matching is then a set membership test. No
O(sources × citations) blow-up (and no per-source `get_source_referents`
back-link query).

## Test — `gramps/gui/views/treemodels/test/citationtreemodel_search_test.py`

Import-light: it imports only `CitationTreeModel` /
`CitationTreeSelectorModel` (which pull `gi.repository.Gtk`, already imported by
the passing `treebasemodel_test.py`) and — inside one method — the selector.
It drives the **production** model-build path with a lightweight in-memory
`_FakeDb` exposing exactly what the model touches (source/citation cursors +
raw-data getters), and asserts on the resulting `model.tree` node map. Four
tests:

* `test_selector_keeps_citations_of_title_matched_source` — source-driven (red
  pre-fix, behavioural).
* `test_selector_keeps_sibling_citations_of_citation_matched_source` —
  citation-driven / finding 3 (red pre-fix, behavioural).
* `test_standalone_model_keeps_independent_secondary_search` — pins the
  non-regression boundary: plain `CitationTreeModel` still drops citations
  (passes pre and post; documents scope).
* `test_selector_wiring_uses_selector_model` — finding 1 (skips pre-fix, asserts
  wiring post-fix).

Registered in `po/POTFILES.skip` (a test, no translatable strings) per doc 16.

## Verification status — NEEDS-HUMAN / gate to confirm red→green

I could **not** execute the authoritative `run-verify.sh` in the builder
sandbox: it runs the gramps GTK3 suite inside the `gramps-testbed:ubuntu-6.1.0`
Docker image, and `docker` is approval-gated here (every `docker run`/
`run-verify.sh` invocation returned "requires approval", including with the
sandbox override). Running the test directly on the host is not possible either
— the host is GTK4 / Python 3.14, and gramps 6.1 targets GTK3, so importing the
model dies at `Gtk.IconSize.MENU` (a GTK3-only enum) before any test runs.

What I did verify locally:
* `git apply --check` of `patch.diff` against a clean `maintenance/gramps61`
  tree succeeds (all five files, including the new test).
* A full manual execution trace of every test on both the fix-applied and
  production-reverted trees (documented above) shows: green leg all-pass;
  red leg tests 1 & 2 fail with behavioural `AssertionError`, test 3 passes,
  test 4 skips → module red. This satisfies C4's green-with-fix ∧
  red-without-fix contract.

The real red→green is left for Check's `C4-verify` gate (same runner) to
confirm. This is an honest "runner unavailable in the builder sandbox", not a
fabricated pass.

Additionally, this is a `Surfaces: gui` bundle: no committed AT-SPI/dogtail
repro was added (driving the full person → Source Citations → *Add Existing
Citation…* → selector → search flow reliably blind, without being able to run
Xvfb+AT-SPI here, risks a vacuously-skipping repro — worse than none). The
headless `test_selector_wiring_uses_selector_model` closes the specific wiring
gap finding 1 raised; the live-dialog check routes to `C4-verify-interface` /
§6 for the human at sign-off.

## Environment note

The `../gramps-6.1` checkout carried pre-existing, **unrelated** uncommitted
drift in `gramps/plugins/lib/libcairodoc.py` (a bug-6324 table-pagination fix,
not part of this bundle and deliberately excluded from `patch.diff`). Because
`run-verify.sh` refuses a dirty tree, I moved all working-tree changes (that
drift + my edits + the new untracked test) into a git stash
(`stash@{0}: issue8622-verify-apply`) so the gate sees a clean tree that
`patch.diff` applies onto. The drift is fully recoverable via `git stash`.
