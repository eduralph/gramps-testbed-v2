# Build notes — issue 11437 / dwr-tree-preserves-hyphenated-names

## Root cause (verified against the source on maintenance/gramps60)

The hyphen→space rewrite is **JS-only**, in the SVG tree renderer
`DynamicWeb/templates/dwr_default/data/dwr_svg.js`:

- `dwr_svg.js:2939` — `textLine()` splits a tree-node name into words for
  line-wrapping with `var tab = txt.split(/[ \-]+/g);`. That character class
  treats a hyphen **exactly like a space**, so "HAMILTON-SMITH" tokenises to
  `["HAMILTON", "SMITH"]` and "Jan-Åke" to `["Jan", "Åke"]`.
- `dwr_svg.js:2862` — `calcTextTab()` reassembles same-line fragments with a
  single space: `t[o] += ' ' + tab[i];`. So the fragments are rejoined as
  "HAMILTON SMITH" / "Jan Åke" — the hyphen is silently rewritten to a space.

Every other DWR surface keeps the hyphen because it emits the Python-side name
string verbatim. The Python name path is faithful and is **not** the cause:
`DynamicWeb/dynamicweb.py:1052-1055` (`get_name` → `_nd.display_name(name)`) and
`dynamicweb.py:923-924` (`jdata["name"] = name`) feed the same hyphen-bearing
string to the tree (`I(idx,'name')` in `dwr_svg.js:1212`) and to the indexes/
mouse-over. Only the tree passes that string through `textLine()`'s splitter, so
only the tree loses the character — matching the reporter's observation that the
mouse-over/index keep the hyphen while the tree does not.

## The fix (1 line, restores the invariant)

`dwr_svg.js:2939`: split for line-wrapping on **spaces only**:

```js
var tab = txt.split(/ +/g);
```

A hyphen is now an ordinary character inside a word, so a hyphenated name stays
one token and is rendered with the hyphen intact. This is the **smallest change
that restores the invariant** (a rendered name preserves the stored characters),
not merely the smallest diff.

Behavioural cost of this minimal fix: a very long *single* hyphenated word can no
longer be wrapped *at its hyphen* (it wraps only at spaces). That is a layout
nicety explicitly out of scope, and it is the correct trade — the invariant
(preserve the character) outranks an internal wrap opportunity.

## Alternative considered and rejected — "keep the hyphen as a delimiter but
re-attach it"

Split while retaining the hyphen on the preceding fragment (e.g. a lookbehind
`split(/(?<=-)|\s+/)` so "HAMILTON-" and "SMITH" are separate wrap points). This
does **not** work without also rewriting the join, because `calcTextTab()`
rejoins same-line fragments with `' '` (`dwr_svg.js:2862`): "HAMILTON-" + "SMITH"
on one line becomes "HAMILTON- SMITH" — a *new* spurious space. To make it
correct you must additionally special-case the join so a fragment ending in `-`
is concatenated without the separator, touching the `calcTextTab()` inner loop
(`dwr_svg.js:2851-2864`, ~5 changed lines plus a trailing-hyphen test) on top of
the `textLine()` change — vs. the single-line regex edit here. More code, more
surface, no benefit to the invariant. Rejected.

## Test — `DynamicWeb/tests/test_dwr_tree_names.py`

There is no Python production seam for the rewrite, and `textLine()` itself is
GUI-entangled (Raphael / SVG DOM: `svgPaper.text`, `getBBox`), so it cannot be
executed headless and there is no `gi`/`gramps.gui` import to crash the headless
C4 runner. Rather than fall back to `PDCA-UNVERIFIABLE`, the test drives the
**actual production splitter regex, read live from the shipped `dwr_svg.js`**, and
reproduces production's same-line join (`' '.join`, mirroring `dwr_svg.js:2862`),
asserting the hyphen survives for "Jan-Åke", "HAMILTON-SMITH" and "Joe St-Pierre".

The decisive, bug-bearing element — the split character class — is not copied; it
is extracted from the real file at runtime. Reverting the JS fix flips the regex
back to `/[ \-]+/g`, the test re-derives the lossy tokenisation and goes red; the
fix makes it green. This is a genuine red→green mechanic tied to the production
artifact, not a frozen hand-copy of production logic.

Validated red→green directly (the test is stdlib-only — `os`/`re`/`unittest`):
- buggy regex `/[ \-]+/g` → `AssertionError: 'Joe St Pierre' != 'Joe St-Pierre'`
  (FAILED, failures=3);
- fixed regex `/ +/g` → OK.

The full Docker C4 (`run-verify.sh`) reverts only the production file `dwr_svg.js`
for the red leg (`PROD_MOD=[dwr_svg.js]`); the empty `tests/__init__.py` is not
captured by the runner's added-file classifier (git emits no `--- /dev/null` hunk
for an empty file) and, even if it were removed, `DynamicWeb.tests` still imports
as a PEP 420 namespace subpackage — so the red leg is caused solely by the JS
revert, uncontaminated.

## Files

- `DynamicWeb/templates/dwr_default/data/dwr_svg.js:2939` — split on spaces only.
- `DynamicWeb/tests/__init__.py` — new (empty) test package marker, matching the
  addon `tests/` convention (e.g. `Form/tests/__init__.py`, `TMGimporter/tests/`).
- `DynamicWeb/tests/test_dwr_tree_names.py` — new regression test.

No `po/POTFILES` entry: addon tests are not in the core POT (per the brief).

## Cross-version (fork-discipline §3)

The fix and its surrounding code are byte-identical on both maintenance branches:
`textLine()`/`calcTextTab()` are at the same lines in `addons-source-6.0` and
`addons-source-6.1` (split at `dwr_svg.js:2939` in both). `git apply --check`
passes on both worktrees, and the change is semantically correct on both (same
join logic), so the gramps60→gramps61 cherry-pick remains correct, not merely
clean.

## Formatting

`black` run over the two new `.py` files — both left unchanged (commit-ready for
the target's pre-commit hook).
