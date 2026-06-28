# Build notes — issue 7344 / addon-setup-locale-path-dead-slice

Target branch: `gramps-project/addons-source @ maintenance/gramps60`
Local checkout: `/home/eddie/workspace/addons-source-6.0` (detached at
`upstream/maintenance/gramps60`, 2e4ced9a2). `$PDCA_WORKTREE` was unset, so the edit
was made in the host's `addons-source-6.0` checkout, which is the gramps60 target.

## Root cause (two sentences)

In `setup.py`'s `is_listing()` (def at `setup.py:742`), the "Get all languages from all
addons" loop computed the locale with a fixed-width slice `locale = po[length-11:length-9]`
(`setup.py:787` on the target branch) which only keeps two characters and so mangles
locale codes longer than 2 chars (`pt_BR` → `BR`, `zh_CN` → `CN`). That slice is **dead
code**: the very next line `(locale_path, locale) = po.rsplit('/', 1)` (`setup.py:788`)
overwrites `locale` before it is ever read, and the language is then derived as
`locale[:-9]` (`setup.py:789`), which strips the trailing `-local.po` and yields the full
locale code for any length.

## Why this is already-fixed → verify-first, remove dead code

The original 2013 defect (wrong `.mo` path for >2-char locales) does **not** reproduce on
the current tooling, because nothing downstream consumes the truncated slice:

- Listing/languages path (`is_listing`): `setup.py:788–789` use `rsplit('/',1)` then
  `locale[:-9]` — the full code.
- Compile path (`is_listing`): `setup.py:774` uses `os.path.basename(po[:-9])` — the full
  code — to build `<Addon>/locale/<locale>/LC_MESSAGES/addon.mo` (`setup.py:775–778`).
- Build path (`build` cmd): `setup.py:683–684` use `os.path.basename(po[:-3])` then
  `f[:-6]` — also the full code.

Empirical confirmation of every derivation (run locally):

```
po = "MyAddon/po/pt_BR-local.po"
  dead slice  po[len-11:len-9]      -> 'BR'      (truncated, but NEVER USED)
  listing     rsplit/[:-9]          -> 'pt_BR'   (correct, full code)
  compile     basename(po[:-9])     -> 'pt_BR'   (correct, full code)
po = "MyAddon/po/zh_CN-local.po"
  dead slice                        -> 'CN'
  listing                           -> 'zh_CN'
  compile                           -> 'zh_CN'
po = "MyAddon/po/de-local.po"  -> dead 'de' / listing 'de' / compile 'de'
po = "MyAddon/po/nl-local.po"  -> dead 'nl' / listing 'nl' / compile 'nl'
```

So the Success criterion ("building/compiling an addon with a `pt_BR` translation produces
`<Addon>/locale/pt_BR/LC_MESSAGES/addon.mo`; the original wrong-path defect does not
reproduce") **already holds**. The remaining defect is the dead, misleading slice itself —
the bug thread (Mantis 7344, romjerome/paulfranklin) flagged exactly this leftover and was
unsure what `rsplit` did. The patch removes the dead slice (and its sole feeder
`length = len(po)`, which had no other reader) without changing any produced path.

## The change

`setup.py:786–787` removed (target-branch line numbers):
```
-            length = len(po)
-            locale = po[length - 11:length - 9]
```
`length` was used only by the deleted slice, so it is removed too. The live derivation at
`setup.py:788–789` is untouched, so every produced path/listing is byte-for-byte identical.

## Why no red→green test (PDCA-UNVERIFIABLE — as the brief anticipates)

The brief states "Test file: none practical … Expect C4 PDCA-UNVERIFIABLE (no red→green
test seam)." This is correct and unavoidable: the patch removes **dead** code, so there is
**no observable behaviour difference** between pre-fix and post-fix. By definition no test
can be red before and green after — any behavioural assertion (e.g. "the `.mo` for a
`pt_BR-local.po` lands at `locale/pt_BR/...`") is **green both before and after** the
patch, because the truncated slice never reached any output. Fabricating red→green (e.g. by
reverting the live `rsplit` line inside a test) would test a strawman, not the production
path. A source-grep "the slice is gone" test would be a mechanical/adjacent check, not a
correctness verification, and would itself be green-only-post (not red-pre on behaviour).
Hence no test file is shipped; correctness is established by reading the derivation
(above) plus the manual repro (below).

## Manual repro (verifies Success criterion holds, pre- and post-patch)

```
# in a maintenance/gramps60 addons-source checkout with GRAMPSPATH set:
mkdir -p MyAddon/po
printf 'msgid ""\nmsgstr ""\n' > MyAddon/po/pt_BR-local.po   # minimal valid .po
python3 setup.py --listing all        # invokes is_listing() -> compile + languages
ls MyAddon/locale/pt_BR/LC_MESSAGES/addon.mo   # exists at the FULL-code path
```
Expected (both with and without this patch): the `.mo` is written under
`MyAddon/locale/pt_BR/LC_MESSAGES/` (full `pt_BR`, not `BR`), and the computed `languages`
set contains `pt_BR`. The wrong-path defect does not reproduce; the only difference the
patch makes is that the dead `locale = po[length-11:length-9]` line is gone.

## Commit-readiness

`addons-source` has no `.pre-commit-config.yaml`, `pyproject.toml`, `setup.cfg`, or
`tox.ini` at the repo root (checked) — no black/flake8 hook is configured for this repo, so
there is no formatter to run. The two-line deletion preserves the surrounding file's
existing (non-black) continuation style, so the patch is commit-ready for the target's
hooks.

## Files added/removed

None. `setup.py` is an existing build script (not a core `.py`); no `po/POTFILES.in` /
`POTFILES.skip` registration applies.
