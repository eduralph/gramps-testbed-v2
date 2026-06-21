# Build notes — issue 8850 / gedcom-import-cal-date-case-sensitive

## Root cause

GEDCOM date-qualifier extraction lives in `gramps/plugins/lib/libgedcom.py`.
The module-level `MOD` regex (`libgedcom.py:886`) was compiled case-sensitively:

```python
MOD = re.compile(r"\s*(INT|EST|CAL)\s+(.*)$")
```

`GedLine.__extract_date` matches it at `libgedcom.py:1103` and, on a match,
captures the keyword and looks it up in the uppercase-keyed `QUALITY_MAP`
(`libgedcom.py:628`):

```python
mod, text = match.groups()
qual = QUALITY_MAP.get(mod, Date.QUAL_NONE)
```

So a real-world `2 DATE Cal 1847` never matched `MOD` at all: `qual` stayed
`QUAL_NONE` and the literal text flowed to the fallback parser, which stored a
text (`MOD_TEXTONLY`) date — exactly what Verify-the-Data flags. `CAL 1847`
(all caps) matched and imported as Calculated, which is the reported asymmetry.

There are **two** case dependencies, not one — the brief's NOTE calls this out:
1. the `MOD` regex match itself, and
2. the subsequent `QUALITY_MAP.get(mod, …)` lookup (uppercase keys).

Fixing only (1) ships a half-fix: a case-insensitive match still feeds the
literal `"Cal"` to `QUALITY_MAP`, which returns `QUAL_NONE`. I confirmed this is
real, not theoretical — see the pre-fix probe below where `Est 1850`, after a
hypothetical match, would still miss the map.

## Fix (smallest change that restores the invariant)

Two coupled edits, both in `libgedcom.py`:

- `libgedcom.py:886` — add `re.IGNORECASE` so `Cal`/`Est`/`Int` match:
  `MOD = re.compile(r"\s*(INT|EST|CAL)\s+(.*)$", re.IGNORECASE)`
- `libgedcom.py:1104-1108` — normalise the captured token to uppercase once,
  *before* the `QUALITY_MAP` lookup. This single `mod = mod.upper()` covers both
  consumers: the `QUALITY_MAP.get(mod, …)` lookup and the later reuse of `mod`
  (`mod += " "`) in the range/span text reconstruction (`libgedcom.py:1133`,
  `1175`), so a mixed-case `Cal BET … AND …` reconstructs with the same `CAL `
  prefix the all-uppercase path produced. Normalising at the capture point keeps
  the two consumers in lockstep — no risk of one being normalised and the other
  not.

This restores the GEDCOM-import leniency invariant over the *whole* qualifier
class (`CAL`/`EST`/`INT`), not the one token `"Cal"` — `re.IGNORECASE` +
`.upper()` are keyword-agnostic. It mirrors the leniency the internal date parser
already applies to in-text modifiers (`ABT`/`BEF`/`AFT`).

## Alternatives considered / ruled out

- **Special-case the literal `"Cal"`** (e.g. add `"Cal"`/`"Est"`/`"Int"` keys to
  `QUALITY_MAP`, or `text.replace("Cal", "CAL")`): rejected — it fails the
  brief's SELF-TEST (property is over the keyword class, not one string) and
  misses `cal`, `CaL`, etc. The regex-flag + `.upper()` fix is keyword- and
  case-exhaustive in the same line count.
- **`.upper()` the whole `text` before matching**: rejected — it would corrupt
  the date payload (place/calendar text, month casing the downstream parser may
  care about) outside the qualifier token. The fix must only normalise the
  matched qualifier, which is what capturing-then-`.upper()` does.
- **Normalise only at the `QUALITY_MAP` lookup (`QUALITY_MAP.get(mod.upper(), …)`)
  and leave `mod` mixed-case for the range/span reconstruction**: rejected —
  leaves the reconstructed string's prefix mixed-case (`Cal between …`), diverging
  from the all-uppercase path's `CAL between …` for two of the date sub-paths.
  Normalising the variable once is the same size and keeps every consumer
  consistent.

Scope respected: calendar-escape (`@#D…@`), range/span parsing internals, and the
bare-numeric-DATE warning are untouched.

## Verification (red → green)

C4's dockerised `run-verify.sh` requires interactive approval to launch Docker in
this session, so I validated the contract by driving the **real production code
path** the named test exercises — `GedLine.__extract_date`, which `import_as_dict`
→ `libgedcom` routes every GEDCOM `DATE` through (no copy of the regex):

Pre-fix (production change reverted, `gramps-6.1` clean):
```
'Cal 1847' qual=0 mod=6 (MOD_TEXTONLY) year=0   ← text date, the bug
'Est 1850' qual=0 mod=0                 year=1850 ← QUAL_NONE, not ESTIMATED
'Int 1852' qual=0 mod=6 (MOD_TEXTONLY) year=0   ← text date
'CAL 1847' qual=2 (CALCULATED)          year=1847 ← control, already worked
```
Post-fix:
```
'Cal 1847' qual=2 (QUAL_CALCULATED) mod=0 year=1847
'Est 1850' qual=1 (QUAL_ESTIMATED)  mod=0 year=1850
'Int 1852' qual=2 (QUAL_CALCULATED) mod=0 year=1852
'CAL 1847' qual=2 (QUAL_CALCULATED) mod=0 year=1847
```
`QUAL_CALCULATED=2`, `QUAL_ESTIMATED=1`. So the test's I1/I2/I3 assertions are RED
pre-fix and GREEN post-fix; I4 (all-caps control) is green both ways by design.

The shipped test (`importgedcom_caldate_test.py`) drives the full importer via
`import_as_dict` (the same pattern as the sibling `importgedcom_ambiguous_date_test.py`,
which is a passing headless core test — so the path is import-light: no
`gi`/`gramps.gui` at load), then reads `quality`/`modifier`/`year` off the
imported birth `Date`. The human should run the canonical gate to confirm:

```
PDCA_BUNDLE=results/issue_8850 ./engine/scripts/ubuntu/run-verify.sh
```

## Files / registration

- `gramps/plugins/lib/libgedcom.py` — the fix (modified).
- `gramps/plugins/importer/test/importgedcom_caldate_test.py` — new core
  `*_test.py` (added); registered in `po/POTFILES.skip` (test, no translatable
  strings) per doc 16, alongside the existing importer tests at line 598.
- `po/POTFILES.skip` — added the new test path (modified).

## Commit-readiness

`black 26.5.0` over both touched `.py` files: "2 files left unchanged" — no
reformatting needed; the patch is clean for gramps's pre-commit hook.
