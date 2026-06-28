# Fix date quality keyword matching inside words

## Root cause

The `DateParser.match_quality` method uses a regex (gramps/gen/datehandler/_dateparser.py:528) with an unanchored leading group and no word-boundary anchor before the quality keyword, so keywords like "est" match as substrings inside unrelated words. For input "Test data", the pattern matched group(1)="T", the keyword "est" inside "Test", then group(3)="data", and the match handler stripped the keyword, yielding corrupted text "Tdata".

## Fix

Add a word-boundary anchor `\b` before the quality keyword alternation in the regex pattern at gramps/gen/datehandler/_dateparser.py:528, changing from `r"(.* ?)%s\s+(.+)"` to `r"(.* ?)\b%s\s+(.+)"`. This ensures the keyword matches only as a whole token, so "est" inside "Test" no longer triggers, while genuinely quality-prefixed dates ("est 1900", "calculated 1900") continue to match and parse correctly.

## Verified against

- **gramps/gen/datehandler/_dateparser.py:528** — the regex pattern that was unanchored to a word boundary
- **gramps/gen/datehandler/test/dateparser_test.py:117+** — regression test added to the existing DateParserTest class, testing that free-text dates with embedded keywords are preserved and genuine quality-prefixed dates still parse

## Test

Two regression test methods added to the existing gramps/gen/datehandler/test/dateparser_test.py file:

1. `test_quality_keyword_not_matched_inside_word()` — verifies that "Test data" parses as a free-text date with text preserved (not mangled to "Tdata") and quality QUAL_NONE (not estimated).
2. `test_quality_keyword_whole_token_still_parses()` — verifies that genuine quality-prefixed dates ("est 1900", "estimated 1900", "calc 1900") continue to parse with the correct quality (QUAL_ESTIMATED or QUAL_CALCULATED) and year value.

The test was verified end-to-end against the real `DateParser` on the target base commit with the patch applied: "Test data" → text "Test data", quality QUAL_NONE ✓; "est 1900" → quality QUAL_ESTIMATED, year 1900 ✓. Production code reverted and test run confirmed red (test fails without the fix).

Fixes #5516
