# Build notes — issue 6250 (libcairodoc paragraph-split attr re-index)

Target branch: `gramps-project/gramps @ maintenance/gramps61` (HEAD `cbe5699b2e`).
All path:line citations below are against that branch's pre-patch tree.

## Root cause

`GtkDocParagraph.divide` (`gramps/plugins/lib/libcairodoc.py:552`) rebuilds the
second part's `Pango.AttrList` after a page-break split. The 2012 workaround
(`:685-714`, the `## START OF WORKAROUND … ##END OF WORKAROUND` block) re-serialises
the split by walking the **markup** string (`self._text`) byte-by-byte and counting
plaintext bytes, then re-parses the reconstructed markup (`Pango.parse_markup`,
`:711-713`). Because it walks markup, an escaped entity (`&amp;`/`&lt;`/`&gt;`) is
counted as its 4–5 markup bytes instead of the single plaintext byte Pango attribute
offsets are defined against. Any paragraph whose plaintext has `&`/`<`/`>` before the
split desyncs the cursor and the second part's style runs land on the wrong characters
(verified: `"A &amp; B <b>BOLD</b> tail"` split at index 6 reconstructs the wrong
fragment `'; B <b>BOLD</b> tail'`). The workaround existed only because
`pango_attr_iterator_get_attrs` was not introspectable (bug 6208 / gnome 646788); this
bundle's iteration-v1 `verification-finding.md` established that capability is now
present on every supported GI stack (Pango 1.52.1 CI, 1.57.0 host).

## Fix

Replace the markup re-serialisation with re-indexing of the already-parsed attribute
list, expressed in plaintext byte offsets — so it is independent of markup serialisation.

### Why a new module (`gramps/plugins/lib/libcairodocattr.py`) instead of an in-file function

The brief's literal reading puts the seam in `libcairodoc.py` and has the test import it
(the `latexdoc_test.py → str_incr` pattern). That does **not** work here: `libcairodoc.py:64`
is `from gramps.gui.utils import SystemFonts`, and `gramps/gui/utils.py:48` does
`from gi.repository import Gdk` at module top. The C4 runner is **headless** (`run-verify.sh`
core mode = plain `python3 -m unittest`, no display/D-Bus), and importing a `gramps.gui`
module there pulls Gdk and risks the very `Trace/breakpoint trap (core dumped)` the project
already tracks as the T3-unit baseline. So importing `libcairodoc` from the test is unsafe
and recurs on every iterate-do.

The fix therefore **restructures so production and test share one implementation**
(principles §3.4): the re-index logic lives in a new import-light module that imports only
`from gi.repository import Pango` (Pango needs no display). `divide()` calls
`reindex_split_attrlist(layout.get_attributes(), index)` (`libcairodoc.py` new line, was
`:666-715`); the test drives **that same function**. No hand-copy of the loop in the test
(avoids the issue-8653 mirror trap).

The new `.py` has no translatable strings, so it is registered in `po/POTFILES.skip`
(under a new `gramps/plugins/lib/libcairodocattr.py` line in the `# plugins/lib directory`
section). The two test files go in a new `# plugins/lib/test directory` section, mirroring
the existing `# plugins/docgen/test directory` entries (`POTFILES.skip:557-558`).
`T2-potfiles` checks all three. (The brief's New/removed-files field listed only the two
test files; the helper module is an additional added `.py` and must be registered too —
done.)

### Why `get_iterator()` and not the OLD EASY CODE verbatim

The brief warns the `## OLD EASY CODE` comment (`:674-684`) is a starting point, not gospel.
It is genuinely broken and I did not paste it:
- `while oldattrlist.next():` advances **before** reading, so the first iterator segment is
  skipped.
- `newattr.start_index -= index if start>index else 0` leaves a straddling run's start at its
  original value instead of clamping it to 0.
- it inserts the shifted copies **into the same list that still holds the originals** →
  duplicated/garbage runs.
- the `Pango.AttrIterator` reports an attribute once **per segment it spans** (proved
  empirically: a run over two segments appears in both `get_attrs()` calls), so a naive
  insert duplicates multi-segment runs.

`reindex_split_attrlist` builds a **fresh** `Pango.AttrList`, reads each segment before
`next()`, de-dups repeated runs by `(type, start, end)`, drops runs with
`end_index <= index` (entirely in the first part), clamps `start_index` to
`max(start-index, 0)`, and shifts `end_index` by `index`. (I considered
`AttrList.get_attributes()`, which returns each run once and would drop the de-dup set; I
kept the `get_iterator()` API because that is exactly what iteration-v1 proved usable on the
CI stack — using it removes any availability risk on the gate.)

### Why the `filter`/`filterattr` call had to go (invariant, not just the workaround block)

This is the non-obvious part. The brief's Scope says to compute from the *already-`filter`ed*
list (`:666-667`, `filterattr` at `:734`). But I proved empirically that `filterattr` **drops
the boundary run**: an attribute whose `start_index == index` is removed (the repro's bold
starts at byte 6 and the split is at 6 → `AttrList.filter` removes it, leaving an empty list).
The Invariant to restore explicitly requires a run straddling/at the split to be **preserved
with its start clamped to 0**, and the Success criterion's expected output is a single
weight=bold run over the second part's bytes 0–4. With the buggy `filterattr` the re-index
input would be empty and the bold would be lost entirely — failing the success criterion.

Per principles §1.2/§2 (when an Invariant is named, the target is the smallest change that
*restores the invariant*, not the smallest diff), `reindex_split_attrlist` performs selection
**and** re-indexing in one pass using the correct predicate (`end_index > index` ⇒ keep). That
makes the test able to exercise the boundary headlessly through the real production path, and
restores the invariant for the boundary case the old `filterattr` mishandled. `filterattr`
(`:734-740`) becomes dead (its only caller was `:667`) and is removed; `layout.get_attributes()`
is passed straight to the seam. `__set_attrlist` (`:536`) is unchanged.

This is *not* scope creep beyond the workaround: the boundary attribute is precisely the run
the success criterion asserts, and `filterattr` was the thing discarding it.

## Verification (red→green)

Reproduced locally without Docker (the gating Docker C4 runner needs human approval from the
builder sandbox; Check re-runs the real `run-verify.sh`):
- `git apply patch.diff` → `pytest gramps/plugins/lib/test/libcairodoc_test.py` → **4 passed**
  (green-with-fix): the `index==start` boundary (bold→0–4), a straddle (`index=8`→0–2), a
  wholly-after run (`index=5`→1–5), and a wholly-before drop (`index=11`→∅).
- revert `libcairodoc.py` + remove `libcairodocattr.py`, keep the test → collection
  `ModuleNotFoundError` (red-without-fix). This is the standard extract-to-seam red: the
  corrected production function the patch introduces is absent.

`git apply --check` is clean against the worktree. `black` run over all four touched files
(libcairodoc.py / libcairodocattr.py / the two test files) — all clean (the test was
reformatted by black before the diff was cut), so the publish commit will pass the gramps
pre-commit `black` hook.

## Rejected alternatives

- **Keep `filterattr`, fix only its boundary, put a reindex-only seam after it.** The boundary
  fix would then live in `filterattr` — a `GtkDocParagraph` method that can only be reached by
  importing `libcairodoc` (GUI-entangled), so the test could not exercise it headlessly. The
  test would cover re-indexing but not selection, leaving the exact boundary the success
  criterion asserts untested. Rejected: fails the "test exercises the production path" bar.
- **`hasattr`/`try` capability fallback for `get_iterator`.** Explicitly forbidden by the brief;
  iteration-v1 settled availability.
