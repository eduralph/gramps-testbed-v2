# Build notes — issue 7344 / addon-setup-locale-path-dead-slice

Target branch: `gramps-project/addons-source @ maintenance/gramps60`
Local checkout: `/home/eddie/workspace/addons-source-6.0` (detached at
`upstream/maintenance/gramps60`, `2e4ced9a2`). `$PDCA_WORKTREE` was unset, so the edit
was made in the host's `addons-source-6.0` checkout, which is the gramps60 target.

## Iteration 2 — what changed vs the rejected v1

v1 removed the dead slice only from `setup.py` (the legacy build script). Sign-off
rejected it: the **active** addon build tool on `gramps60` is `make.py` (the README and all
documented commands are `python3 make.py gramps60 …`), and `make.py` carries the *same*
dead slice at lines 164–165. v1 left the active file untouched.

This iteration removes the dead slice from **both files**:
- `make.py:164–165` (the active tool) — primary fix.
- `setup.py:786–787` (legacy script) — for completeness, so the two don't drift.

The previously-failing gate was `T3-baseline` (advisory, gramps61×6.1 matrix): 4 new
failures `LifeLineChartView.collection::import_or_collection`, `PDFFor…`. Those are
addon-level import/collection tests with no causal path to a dead-code deletion inside
`get_all_languages()` / `is_listing()` — they are pre-existing/environmental (the reviewer
reached the same conclusion in v1's check-review.md §"T3 gramps61 causation"). A two-line
removal of an overwritten assignment cannot regress addon import.

## Root cause (two sentences)

In `make.py`'s `get_all_languages()` (def `make.py:157`), the locale was first computed with
a fixed-width slice `locale = po[length-11:length-9]` (`make.py:165`) which keeps only two
characters and so mangles codes longer than 2 chars (`pt_BR` → `BR`, `zh_CN` → `CN`). That
slice is **dead code**: the very next line `locale_path, locale = po.rsplit(os.sep, 1)`
(`make.py:166`) overwrites `locale` before it is ever read, and the language is then derived
as `locale[:-9]` (`make.py:167`), stripping `-local.po` and yielding the full code for any
length. `length` (`make.py:164`) had no other reader, so it is removed too. `setup.py`'s
`is_listing()` has the identical dead pair at `setup.py:786–787`, overwritten at
`setup.py:788`.

## Does the Weblate path bypass this code? — No (carry-forward question)

The Weblate-era `extract-po` command routes **through** `get_all_languages()`:
`extract_po()` (def `make.py:314`) iterates `for lang in get_all_languages():`
(`make.py:322`) and builds `{lang}-local.po`. So the function is live and shared by the
Weblate path; the >2-char correctness of its output matters there too — and it is correct,
because the live `rsplit` derivation (`make.py:166–167`) returns the full code. The dead
slice within it is still dead on every path (`get_all_languages` is also called at
`make.py:578`, `812`, `923` for compile/build/listing). The compile path itself never used
the slice: `make.py:224`, `591`, `920` derive the locale as `os.path.basename(po[:-9])`
(full code).

## Why this is verify-first / dead-code removal (Success criterion already holds)

The 2013 defect (wrong `.mo` path for >2-char locales) does **not** reproduce on current
tooling, and removing the slice changes **no produced path** — confirmed end-to-end with
the active tool:

Manual repro (active tool, real `msgfmt`):
```
# in /tmp, GRAMPSPATH=/home/eddie/workspace/gramps-6.0
mkdir -p MyAddon/po
printf 'msgid ""\nmsgstr ""\n' > MyAddon/po/pt_BR-local.po
printf 'msgid ""\nmsgstr ""\n' > MyAddon/po/zh_CN-local.po
printf 'msgid ""\nmsgstr ""\n' > MyAddon/po/de-local.po
python3 make.py gramps60 compile MyAddon
```
Produced (patched make.py):
```
MyAddon/locale/pt_BR/LC_MESSAGES/addon.mo
MyAddon/locale/zh_CN/LC_MESSAGES/addon.mo
MyAddon/locale/de/LC_MESSAGES/addon.mo
```
Produced (pre-fix make.py from `HEAD:make.py`, dead slice present) — **byte-identical**:
```
MyAddon/locale/pt_BR/LC_MESSAGES/addon.mo
MyAddon/locale/zh_CN/LC_MESSAGES/addon.mo
```
The full-code path (`pt_BR`, not `BR`) is produced **with and without** the patch, so the
wrong-path defect does not reproduce, and the only effect of the patch is that the dead,
misleading slice (the exact lines romjerome/paulfranklin puzzled over in Mantis 7344) is
gone.

Derivation table (replicated logic):
```
po = MyAddon/po/pt_BR-local.po   dead slice='BR'  live(rsplit/[:-9])='pt_BR'  compile='pt_BR'
po = MyAddon/po/zh_CN-local.po   dead slice='CN'  live='zh_CN'                compile='zh_CN'
po = MyAddon/po/de-local.po      dead slice='de'  live='de'                   compile='de'
```

## Why no red→green test (PDCA-UNVERIFIABLE — as the brief pre-declares)

The brief states "Test file: none practical … Expect C4 PDCA-UNVERIFIABLE (no red→green
test seam)." That is correct and unavoidable here: the patch removes **dead** code, so
there is **no observable behaviour difference** between pre-fix and post-fix (the repro
above demonstrates byte-identical output). By definition no test can be red before and
green after — any behavioural assertion ("the `.mo` for `pt_BR-local.po` lands at
`locale/pt_BR/…`", "`get_all_languages()` returns `pt_BR`") is **green both before and
after**, because the truncated slice never reached any output. A characterization test
would therefore be green-only and would *fail* the C4 red→green check, not pass it;
shipping one would be counterproductive. A source-grep "the slice is gone" assertion is an
adjacent mechanical check, not a correctness verification. Fabricating red→green by
reverting the live `rsplit` line inside a test would assert against a strawman, not the
production path. Hence no test file is shipped; correctness is established by the derivation
+ the end-to-end manual repro above.

`make.py` is a top-level script (it reads `sys.argv[1]`/`[2]` at module load,
`make.py:67,69`), so `get_all_languages` cannot be imported in a headless unit without
restructuring the whole script — out of scope for a behaviour-neutral dead-code removal,
and it would still only yield a green-only test.

## Commit-readiness (target hooks)

`addons-source` @ gramps60 has no `.pre-commit-config.yaml`, `pyproject.toml`,
`setup.cfg`, `tox.ini`, or `.github/` black hook (checked) — no formatter is configured for
this repo. `make.py` is otherwise black-styled; `python3 -m black --diff make.py` reports
only **pre-existing** reformats elsewhere (lines 48, 360, 969, 1013) and **nothing** in the
edited region (162–167), so the deletion introduces no new style deviation. `setup.py` is
in the file's existing single-quote/manual-indent style and the deletion preserves it. Both
edits are pure two-line removals; commit-ready.

## Files added/removed

None. `make.py` and `setup.py` are existing build scripts (not core `.py`); no
`po/POTFILES.in` / `POTFILES.skip` registration applies (brief §New/removed files).
