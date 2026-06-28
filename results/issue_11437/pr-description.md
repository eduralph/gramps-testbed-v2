# DWR tree: preserve hyphens in displayed names

## Root cause

The SVG tree renderer in `DynamicWeb/templates/dwr_default/data/dwr_svg.js` splits tree-node names for line-wrapping using a regex that treats hyphens as word separators. The fragments are then rejoined with a space, converting hyphens to spaces in the rendered output. Every other DWR surface (indexes, tabs, mouse-over) emits the Python-side name string verbatim, which is why the hyphen survives elsewhere — only the tree passes the name through this destructive splitter.

## Fix

Change `dwr_svg.js:2939` to split on spaces only (`/ +/g` instead of `/[ \-]+/g`), so hyphens become ordinary characters inside words and render intact. This is the minimal change that restores the invariant: a rendered name preserves the stored characters. The trade-off is that a very long hyphenated word can no longer wrap *at* its hyphen (it wraps only at spaces), but that layout nicety is explicitly out of scope.

## Verified against

- `DynamicWeb/templates/dwr_default/data/dwr_svg.js:2939` — the buggy regex split that treats hyphens as word separators
- `DynamicWeb/templates/dwr_default/data/dwr_svg.js:2862` — the same-line fragment join that combines the split tokens with a space
- `DynamicWeb/templates/dwr_default/data/dwr_svg.js:2835` — the `calcTextTab()` function context
- `DynamicWeb/dynamicweb.py:1052–1055` — the `get_name()` method that exports the hyphen-bearing name to the tree
- `DynamicWeb/dynamicweb.py:923–924` — the `jdata["name"]` assignment that feeds the same name to both the tree and indexes

## Test

`DynamicWeb/tests/test_dwr_tree_names.py` — a regression test that reads the production splitter regex live from the shipped `dwr_svg.js` file and reproduces the tree's same-line join logic (mirroring `dwr_svg.js:2862`). The test asserts that hyphenated names like "Jan-Åke", "HAMILTON-SMITH", and "Joe St-Pierre" survive the split→join cycle intact. Reverting the JS fix flips the regex back to `/[ \-]+/g`, and the test turns red; the fix turns it green. The test is stdlib-only (`os`/`re`/`unittest`) and can run headless.

Fixes #11437
