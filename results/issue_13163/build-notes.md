# Build notes — issue 13163 / german-date-bis-parsed-as-month

## Disposition: verify-first (POSSIBLY-FIXED). The reported symptom is already gone.

The brief's **Success criterion** is that `DateParserDE().parse("bis 1760")` no longer
yields an August date — it must parse as a to/until date (MOD_TO, year 1760, month 0),
and the reported `0.8.1760` (August) conversion must no longer occur.

That criterion already holds on the target branch. On
`gramps-project/gramps @ maintenance/gramps61`:

- `gramps/gen/datehandler/_date_de.py:219` — `"bis": Date.MOD_TO,` sits in the
  `DateParserDE.modifier_to_int` table (lines 209–220). So `"bis"` is consumed as a
  *modifier* before the parser ever reaches month-name matching.
- `gramps/gen/datehandler/_date_de.py:181` — the historic month key
  `month_to_int["bisemond"] = 8` (= harvest-moon August) is still present. That key was
  the original cause: before `"bis"` was a modifier, `"bis 1760"` fell through to
  month-name matching and the loose prefix-abbreviation expansion matched the `bisemond`
  key, yielding month 8. With `"bis"` now a modifier, that path is no longer taken.

I confirmed the live behaviour directly (import-light, no GUI/docker):

```
DateParserDE().parse("bis 1760")
  -> modifier 8  (== Date.MOD_TO)
     year 1760   month 0   day 0   text 'bis 1760'
```

So the August conversion is gone; this is a verify-first bundle. There is **no
production change to make** — the fix is already upstream. The deliverable is a
regression test that pins the behaviour against a future regression, shipped at the
path the brief names.

## The test, and why it genuinely guards the invariant

`gramps/gen/datehandler/test/date_de_test.py` (new) asserts
`DateParserDE().parse("bis 1760")` has `get_modifier() == Date.MOD_TO`,
`get_year() == 1760`, and `get_month() == 0` (explicitly **not** 8 / August).

It is import-light by design — it imports only `...lib.date.Date` and
`.._date_de.DateParserDE`, no `gi` / `gramps.gui`, mirroring the sibling
`date_fi_test.py`. So it runs under the headless C4 runner (plain `python3 -m
unittest`) without a display or D-Bus.

**Red→green is real, against the production line — proven manually.** I could not invoke
the docker C4 runner (`run-verify.sh`) in this build environment — the container launch
is approval-gated here and I cannot grant it; Check re-runs it as the gating C4. I
instead proved the contract directly:

- **Green (fix present):** `python3 -m unittest` of the test on the current worktree →
  `Ran 1 test ... OK`.
- **Red (fix reverted):** I temporarily deleted the `"bis": Date.MOD_TO` line
  (`_date_de.py:219`) and re-ran the test →
  `AssertionError: 0 != 8` (modifier check fails; `"bis 1760"` reverts to the August
  parse). I then restored the line.

That manual revert is the meaningful demonstration: it is the *production* line whose
removal re-hides the fix, and the test catches it. The test is not a tautology — it
would go red if a future change removed or reordered the `"bis"` modifier so that
month-name matching reclaimed `"bis"`.

## ⚠️ Expected C4-verify signature — please read before sign-off (§6)

`run-verify.sh` reverts the patch's **non-test** files for its red leg and expects the
test to go red. Here the only non-test file is `po/POTFILES.skip` (a translation
bookkeeping entry — see below), **not** a production line. Reverting it leaves the test
green, so the gate will report:

```
green-with-fix=PASS / red-without-fix=FAIL   ->  C4-verify "fail"
```

**That FAIL is the expected signature of an already-fixed defect, not a broken test.**
The brief anticipated a `PDCA-UNVERIFIABLE` (exit 77) outcome; the harness only takes
that clean test-only branch when the patch ships *no* non-test file. Because the new
`.py` MUST be registered in `po/POTFILES.skip` (gating `T2-potfiles`, doc 16 §Adding and
removing Python files), the patch necessarily carries one non-test file, so `run-verify`
takes the red→green *mechanic* instead and reports the FAIL above rather than exit 77.
Both routes land in the same place — **§6 NEEDS-HUMAN under the C6 accept-guard** — and
the human accepts C4 at sign-off on the basis that (a) the test is green, and (b) the
red leg was demonstrated manually against the real production line (`_date_de.py:219`),
recorded above. This mirrors the documented verify-first handling on bundle 7230.

I did **not** drop the POTFILES.skip entry to manufacture a clean exit-77: that would
trade a gating `T2-potfiles` failure for a cosmetically tidier C4 result, and ship a PR
the maintainer's translation tooling would flag. Registration is the correct, required
state.

## POTFILES registration

`date_de_test.py` has no translatable strings, so it goes in `po/POTFILES.skip`
(doc 16 §Adding and removing Python files), inserted in alphabetical order in the
`gen.datehandler.test` block (`po/POTFILES.skip:73`, before `datedisplay_test.py`).
This keeps the published PR complete and `T2-potfiles`-clean.

## Scope — what I deliberately did NOT touch (brief "out of scope")

Both are flagged in the brief as still-open and design-sensitive; neither is the
verified reported symptom, so neither is in this patch:

1. **The headline "Text only" override** — the date editor
   (`gramps/gui/editors/editdate.py`) silently re-parses text and overrides an explicit
   `Type = "Text only"`. Unresolved UX design; a GUI change, out of scope for the parser
   verify.
2. **Loose abbreviation month keys** — the German parser auto-expands prefix
   abbreviations (`"ern"` → August, `"e"`/`"er"` → September, `"ho"` → July …), which the
   reporter objects to. That is a deep cross-locale change to month-name matching, not the
   reported `"bis"` symptom; `month_to_int["bisemond"] = 8` (`_date_de.py:181`) is left in
   place intentionally (it is a legitimate historic full month name).

## Alternatives considered / ruled out

- **Append the assertion to the existing `dateparser_test.py`** (test-only, no new file →
  clean exit-77 `PDCA-UNVERIFIABLE`). Rejected: the brief explicitly names a **new**
  `date_de_test.py` (the German-locale sibling of `date_fi_test.py`), and
  `dateparser_test.py` exercises the base-locale `DateParser`, not `DateParserDE`. A
  German-specific test belongs in its own German file. The "cost" of the new file is one
  `po/POTFILES.skip` line — registered.
- **Also remove `month_to_int["bisemond"] = 8`** to "fully" kill the August path.
  Rejected: it is out of scope (brief, item 2) and `bisemond` is a real historic month
  name a user transcribing an old document may legitimately enter; the modifier entry
  already resolves the reported symptom without removing that capability.

## Commit-readiness

- `git apply --check` of `patch.diff` against a pristine `maintenance/gramps61`
  worktree: exit 0 (both hunks).
- `black --check` on the new test file: unchanged (commit-ready for gramps' `black`
  pre-commit hook).

## Citations (all on `maintenance/gramps61`)

- `gramps/gen/datehandler/_date_de.py:219` — `"bis": Date.MOD_TO` (the in-place fix being
  guarded).
- `gramps/gen/datehandler/_date_de.py:181` — `month_to_int["bisemond"] = 8` (original
  cause, left intact, out of scope).
- `gramps/gen/datehandler/test/date_de_test.py` — new regression test (added).
- `po/POTFILES.skip:73` — registration of the new test file.
