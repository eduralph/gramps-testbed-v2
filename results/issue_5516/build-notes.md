# Build notes — issue 5516 (date quality keyword matches inside a word)

## Root cause (verified against the target branch)

`maintenance/gramps61`, `gramps/gen/datehandler/_dateparser.py:528`:

```python
self._qual = re.compile(r"(.* ?)%s\s+(.+)" % self._qual_str, re.IGNORECASE)
```

`self._qual_str` (built at `_dateparser.py:490` via `re_longest_first`,
`_dateparser.py:461-468`) expands to a capturing alternation of the quality keys,
longest first: `(estimated|calculated|est.|calc.|est|calc)`. So the whole pattern is

```
(.* ?)(estimated|calculated|est.|calc.|est|calc)\s+(.+)
```

`match_quality` (`_dateparser.py:880-890`) strips the keyword:
`text = match.group(1) + match.group(3)`.

The leading `(.* ?)` is unanchored, so for input `Test data` the engine matches
group(1)=`T`, the keyword `est` **inside** `Test`, `\s+`=` `, group(3)=`data` —
yielding `text = "T" + "data" = "Tdata"`. The keyword is matched as a *substring of
an unrelated word* instead of a whole token. (The reporter and romjerome diagnosed
this exact regex in the Mantis thread, ~0022857.)

## Fix

Anchor the keyword to a word boundary by inserting `\b` before the alternation
(`_dateparser.py:528` on target → patched line):

```python
self._qual = re.compile(r"(.* ?)\b%s\s+(.+)" % self._qual_str, re.IGNORECASE)
```

The right edge was already a whole-token boundary (`\s+` after the keyword); only the
left edge was missing one. `\b` requires a word boundary immediately before the
keyword, so `est` inside `Test` (between two word chars `T`/`e`) can no longer match,
while a keyword that genuinely starts a token (`est 1900`, after start-of-string or a
space) still does.

This is the smallest change that restores the stated correctness requirement — "a
date quality keyword is recognised only as a whole token, never as a substring inside
an unrelated word."

## Verification (red→green)

The C4 docker gate could not be invoked here (the docker/test invocation is gated
behind manual approval in this environment), so I verified two ways:

1. **Regex-level**, reproducing production's `_qual_str` construction and
   `group(1)+group(3)` strip exactly:
   - old: `Test data` → group(1)=`T`, group(2)=`est`, group(3)=`data` → `Tdata`.
   - new: `Test data` → **no match** → text preserved.
   - new still matches `est 1900` / `estimated 1900` / `calc 1900` / `calc. 1900`
     / `est. 1900` / `calculated 1900` → group(1)=``, group(3)=year.

2. **End-to-end** against the real `DateParser` in an isolated detached worktree off
   the target base commit `b679c084f6`, with the patch applied:
   - With fix: `parse("Test data")` → text `Test data`, modifier `MOD_TEXTONLY`,
     quality `QUAL_NONE`; `est/estimated/calc 1900` → year 1900 with the right
     quality. **ALL_GREEN.**
   - Production reverted (test kept): `parse("Test data")` → `Tdata` →
     `test_quality_keyword_not_matched_inside_word` **FAILS**. The other cases still
     pass, confirming the test isolates the bug.

   This is exactly the contract the C4-verify gate re-runs (green-with-fix,
   red-without-fix) and the authoritative run happens there during Check.

   Note on the quality assertion: when the corrupted text (`Tdata`) fails to parse as
   a date, `set_date` falls through to `set_as_text`, which does not apply the `qual`
   value — so the *observable* corruption in the reporter's case is the text
   (`Tdata`), and that is the assertion that flips red→green. The quality assertion
   (`QUAL_NONE`) holds either way and documents that the free-text date is not marked
   estimated, matching the Success criterion.

## Test placement

Added two methods to the existing
`gramps/gen/datehandler/test/dateparser_test.py` (core `*_test.py` suffix
convention) inside `DateParserTest`, driving the production `DateParser.parse` path:
- `test_quality_keyword_not_matched_inside_word` — the regression (the discriminating
  case).
- `test_quality_keyword_whole_token_still_parses` — guards the in-scope behaviour
  (genuine quality-prefixed dates keep working).

The test imports only `gramps.gen.*` (`grampslocale`, `lib.date`) — no `gi` /
`gramps.gui` — so it is safe for the headless C4 runner.

## Alternatives considered / rejected

- **Rewrite `match_quality` to tokenise the string and compare whole words** instead
  of a regex. Rejected: far larger and riskier than needed. It would replace the
  single regex + the 3-line `match_quality` body and would have to re-implement the
  longest-first / case-insensitive / mid-string ("bef est 1900") semantics the regex
  gives for free. Concretely that is a ~15-20 line rewrite of `match_quality`
  (`_dateparser.py:880-890`) plus removal/retuning of the `_qual` compile, versus the
  1-character-effective change here (`\b`). The brief names a correctness requirement
  (whole-token recognition), and `\b` restores exactly that at the cause.
- **Anchor with `(^|.*\s)` instead of `\b`** — equivalent effect but more intrusive
  to the existing group numbering (`match_quality` reads `group(2)`/`group(3)` by
  position; adding a group shifts them and would require touching `match_quality`
  too). `\b` is zero-width and preserves the group indices, so no second site
  changes.
- **Also fix the modifier regexes (`_modifier`, `_modifier_after`,
  `_dateparser.py:539-542`)** for the same class of hazard. Out of scope per the
  brief (Success criterion + Scope are quality-specific), and the leading anchor
  differs there (`_modifier` is already start-anchored with no leading `.*`). Left
  untouched to keep one logical change.

## Files / housekeeping

- `gramps/gen/datehandler/_dateparser.py` — production fix (modified, not added).
- `gramps/gen/datehandler/test/dateparser_test.py` — test (modified existing file).
- No files added or removed → no `po/POTFILES.in` / `POTFILES.skip` change needed.
- `black` (26.5.0) run over both touched files; no reformatting beyond my edit.
