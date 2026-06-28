# Verification finding — issue 6250

**Question (ticket's open condition):** is `Pango.AttrList.get_iterator()` (and
`Pango.AttrIterator`) now available, and usable, via the PyGObject bindings the
Gramps 6.1 build ships? The ticket asked to reintroduce the proper
`get_iterator`-based code "when introspection makes get_iterator available."

**Finding: (a) AVAILABLE.** `Pango.AttrList.get_iterator()` and
`Pango.AttrIterator` are present *and fully usable* on every supported GI stack
checked. The libcairodoc workaround is therefore obsolete; the ticket is
actionable as a small cleanup. **No functional change ships from this
verification bundle** — the reintroduction + its regression test is a separate,
deliberate decision and is out of scope here (per brief Scope/Test-file).

## Evidence

Probe (`pango-availability-probe.py`, shipped in this bundle) replays the exact
API surface the workaround removed: `AttrList.get_iterator()`, then on the
returned `Pango.AttrIterator` the loop `get_attrs()` → `Attribute.copy()` →
read/write `start_index`/`end_index` → `next()`.

Run on the **CI testbed image** (`gramps-testbed:ubuntu-6.1.0`, i.e. the exact
GI stack the T3/C4 gates exercise):

```
Pango typelib version: 1.52.1
get_iterator -> AttrIterator
introspectable attrs iterated: 2
RESULT: get_iterator path FULLY USABLE on shipped GI stack
```

Run on the host GI stack (Pango 1.57.0): identical result —
`hasattr(Pango.AttrList, "get_iterator") == True`,
`hasattr(Pango, "AttrIterator") == True`, iterator + `get_attrs()`/`next()`
usable.

The capability that was missing when the workaround was written — bug 6208 /
gnome bug 646788, "`pango_attr_iterator_get_attrs` is not introspectable" — is
present: `get_attrs()` returns real, mutable `PangoAttribute` objects.

## Why this holds for *all* supported builds (not just the two probed)

Gramps 6.1 requires **GTK 3.24 or greater** (README.md:18). GTK 3.24-era stacks
ship Pango well past the version where `pango_attr_iterator_get_attrs()` gained
its introspection annotation, so the binding precondition is satisfied by the
minimum supported configuration, not merely by the newest. Both probed stacks
(1.52.1, 1.57.0) confirm it empirically.

## The workaround this finding makes obsolete

`gramps/plugins/lib/libcairodoc.py` (target branch `maintenance/gramps61`,
HEAD `cbe5699b2e`):

- `:669` `## GTK3 PROBLEM: get_iterator no longer available!!`
- `:670-673` references (bug 6208, gnome 646788, pitivit workaround commit)
- `:674-684` `## OLD EASY CODE:` — the `newattrlist.get_iterator()` loop that
  was commented out
- `:685-714` `## START OF WORKAROUND` … `##END OF WORKAROUND` — the manual
  markup re-parse (`Pango.parse_markup`, `:711-713`) that replaced it

## Disposition

`manual-verification` — the deliverable is this recorded finding, not a code
change. Recommended follow-up (separate bundle): reintroduce the OLD EASY CODE
`get_iterator` path at `libcairodoc.py:674-684`, delete the workaround
`:685-714`, and ship a regression test over the paragraph-split attribute
re-indexing. That cleanup is intentionally **not** done blind here.
