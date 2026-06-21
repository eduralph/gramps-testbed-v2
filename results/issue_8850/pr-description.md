## Root cause

GEDCOM 5.5.1 specifies the approximate-date qualifier keywords `CAL` (calculated), `EST` (estimated), and `INT` (interpreted) in uppercase. However, real-world GEDCOM exporters emit them in mixed case (e.g., `2 DATE Cal 1847`). The module-level `MOD` regex in `gramps/plugins/lib/libgedcom.py:886` was case-sensitive, so mixed-case variants never matched. When unmatched, the `__extract_date` method (`:1103`) failed to extract the qualifier, leaving `qual = QUAL_NONE` and passing the literal text through to the fallback parser, which imported it as a `MOD_TEXTONLY` text-only date. The Verify-the-Data tool then flags such dates as errors. The same input in all-caps imported correctly as a Calculated date, exposing the gap.

## Fix

Two edits in `gramps/plugins/lib/libgedcom.py`:

1. **Line 886** — Add `re.IGNORECASE` flag to the `MOD` regex so mixed-case qualifiers match:
   ```python
   MOD = re.compile(r"\s*(INT|EST|CAL)\s+(.*)$", re.IGNORECASE)
   ```

2. **Lines 1104–1108** — After capturing the qualifier token, normalise it to uppercase before the `QUALITY_MAP` lookup and before it is reused in range/span reconstruction. This ensures both consumers (the map lookup and the text reconstruction) operate on a consistent uppercase form, matching the behaviour of all-caps input:
   ```python
   mod = mod.upper()
   qual = QUALITY_MAP.get(mod, Date.QUAL_NONE)
   ```

This restores leniency over the entire `CAL`/`EST`/`INT` qualifier class in any case, not just the single token `"Cal"` — matching the existing permissive treatment of in-text modifier words (`ABT`/`BEF`/`AFT`).

## Verified against

- **Target branch:** `upstream/maintenance/gramps61`
- **Files modified:**
  - `gramps/plugins/lib/libgedcom.py` — lines 886, 1104–1108: the regex flag and normalisation
  - `gramps/plugins/importer/test/importgedcom_caldate_test.py` — new file: test suite
  - `po/POTFILES.skip` — line 599: registration of new test (no translatable strings)
- **Companion test:** `gramps/plugins/importer/test/importgedcom_ambiguous_date_test.py` (exists at `:79`) demonstrates the pattern of constructing a `CliUser` with a callback kwarg and importing GEDCOM via `import_as_dict` — the same pattern used in the new test.

## Test

The test suite `gramps/plugins/importer/test/importgedcom_caldate_test.py` drives the real GEDCOM importer (via `import_as_dict` → `libgedcom`) with a fixture containing four individuals:

- **Mixed Calc, Mixed Esti, Mixed Inte** — regression cases with mixed-case qualifiers (`Cal 1847`, `Est 1850`, `Int 1852`)
- **Upper Calc** — all-caps control case (`CAL 1847`) that already worked

For each person, the test:
1. Imports the GEDCOM fixture
2. Locates the person by name (format-independent, no dependency on the importer's padded `gramps_id` format)
3. Asserts the birth date has the correct quality (`QUAL_CALCULATED` or `QUAL_ESTIMATED`)
4. Asserts the year parsed correctly (e.g., 1847, 1850, 1852)
5. Asserts the date is NOT a text-only date (`MOD_TEXTONLY`)

The test fails on the three mixed-case assertions without the fix and passes on all four with the fix applied.

Fixes #8850
