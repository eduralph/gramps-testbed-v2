# Build notes — issue 8850 / gedcom-import-cal-date-case-sensitive (iteration 2)

## What changed since iteration 1

The production fix from iteration 1 was accepted as correct at sign-off (manual
red→green confirmed) — **only the test scaffolding failed the C4 Docker gate**. This
iteration keeps the production fix unchanged and rebuilds the test so it actually runs
green-with-fix / red-without-fix on the headless runner. The C4 gate now passes
**cleanly on clean `upstream/maintenance/gramps61`** (no essential-line fallback):

```
→ green check (fix applied):        Ran 4 tests ... OK
→ red check (production reverted):  FAILED (failures=3)   ← the 3 mixed-case cases
C4-verify: green-with-fix=PASS / red-without-fix=PASS
```

### Root cause of the iteration-1 test failure

The iteration-1 test looked persons up by GEDCOM xref id, `db.get_person_from_gramps_id("I1")`.
But the importer does **not** keep `I1` as the gramps_id: `IdFinder.__getitem__`
(`libgedcom.py:2117`) runs every xref through `id2user_format` (`:2131`), which pads to
the configured `preferences.iprefix` format — `I1` → `I0001` (`libgedcom.py:2132-2133`
comment spells this out). So `get_person_from_gramps_id("I1")` returned `None`, the
`assertIsNotNone(person)` tripped, and the test was red even with the fix applied —
i.e. the test was wrong, not the fix.

The carry-forward also flagged `CliUser(callback=...)`. I verified that is fine: the
sibling `importgedcom_ambiguous_date_test.py:79` constructs `CliUser(..., callback=lambda *a, **k: None)`,
so `callback` is a valid kwarg on this branch. Left as-is. The real defect was solely
the id-format assumption.

### The fix in the test

Rather than hard-code a padded id (which re-couples the test to a config-driven format),
the test now keys lookups on the person **name**, which it controls in the fixture:
after import it walks `db.iter_people()` (`generic.py:1738`) and builds
`{"<First> <Surname>": birth Date}` (`importgedcom_caldate_test.py:97-107`), then asserts
per case. Distinct surnames (`Calc`/`Esti`/`Inte`) plus given names (`Mixed`/`Upper`)
disambiguate the four individuals with no dependency on the importer's id padding.

## Production root cause (unchanged from iteration 1)

GEDCOM date-qualifier extraction is in `gramps/plugins/lib/libgedcom.py`. Two coupled
case dependencies, both required for a complete fix (brief NOTE):

1. The module-level `MOD` regex was case-sensitive (`libgedcom.py:886`):
   `MOD = re.compile(r"\s*(INT|EST|CAL)\s+(.*)$")`. `GedLine.__extract_date` matches it
   at `libgedcom.py:1103`, so `Cal`/`Est`/`Int` never matched at all → `qual` stayed
   `QUAL_NONE` and the literal text flowed to the fallback parser as a `MOD_TEXTONLY`
   date — exactly what Verify-the-Data flags.
2. On a match, the captured token is looked up in the **uppercase-keyed** `QUALITY_MAP`
   (`libgedcom.py:628-632`) via `QUALITY_MAP.get(mod, …)` (`libgedcom.py:1107` pre-fix).
   A case-insensitive *match* that still fed `"Cal"` to that map would return
   `QUAL_NONE` — a half-fix.

## Fix (smallest change restoring the invariant)

Two edits in `libgedcom.py`:

- `libgedcom.py:886` — add `re.IGNORECASE` so `Cal`/`Est`/`Int` (any case) match.
- `libgedcom.py:1104-1108` (post-fix) — normalise the captured token once,
  `mod = mod.upper()`, **before** the `QUALITY_MAP` lookup. This single normalisation
  covers both consumers: the map lookup *and* the later `mod += " "` reuse in the
  range/span text reconstruction, so a mixed-case `Cal BET … AND …` reconstructs with
  the same `CAL ` prefix the all-uppercase path produced. Keeping the variable
  normalised at the capture point keeps the two consumers in lockstep.

This restores leniency over the **whole** qualifier class (`CAL`/`EST`/`INT`), not the
one token `"Cal"` (brief SELF-TEST) — `re.IGNORECASE` + `.upper()` are keyword- and
case-exhaustive. It mirrors the leniency the internal parser already applies to in-text
modifiers (`ABT`/`BEF`/`AFT`).

## Alternatives considered / ruled out

- **Special-case the literal `"Cal"`** (add `"Cal"`/`"Est"`/`"Int"` keys to `QUALITY_MAP`,
  or `text.replace("Cal","CAL")`): rejected — fails the SELF-TEST (one token, not the
  class) and misses `cal`, `CaL`, … The regex-flag + `.upper()` is keyword-/case-
  exhaustive in the *same* line count (3 changed lines either way).
- **`.upper()` the whole `text` before matching**: rejected — corrupts the date payload
  (place / calendar-escape text downstream of the qualifier) outside the matched token.
- **Normalise only at the lookup (`QUALITY_MAP.get(mod.upper(), …)`)**: rejected — leaves
  `mod` mixed-case for the range/span reconstruction (`Cal between …` vs `CAL between …`),
  diverging from the all-uppercase path for two sub-paths. Normalising the variable once
  is the same size and keeps every consumer consistent.
- **Test: hard-code padded id `I0001`**: rejected — re-couples the test to the
  `preferences.iprefix` config format. Name-keyed lookup is format-independent.

Scope respected: calendar-escape (`@#D…@`), range/span internals, and the bare-numeric-
DATE warning are untouched.

## Files / registration

- `gramps/plugins/lib/libgedcom.py` — the fix (modified): `:886`, `:1104-1108`.
- `gramps/plugins/importer/test/importgedcom_caldate_test.py` — new core `*_test.py`
  (added), drives the real importer via `import_as_dict` (no copy of the regex).
- `po/POTFILES.skip:599` — registered the new test (a test, no translatable strings)
  per doc 16, alongside the existing importer tests.

## Commit-readiness

`python3 -m black --check` on both touched `.py` files: "would be left unchanged" — the
patch is clean for gramps's pre-commit hook (the Py3.14-vs-3.15 AST warning is the
runner's interpreter, not a formatting issue).

## Verification

`PDCA_BUNDLE=…/results/issue_8850 ./engine/scripts/ubuntu/run-verify.sh` →
green-with-fix=PASS, red-without-fix=PASS, on clean `upstream/maintenance/gramps61`
(core leg, no essential-line fallback). The red leg fails precisely the three
mixed-case assertions; the all-caps control (`Upper Calc`) is green both ways by design.
