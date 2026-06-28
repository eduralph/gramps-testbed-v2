# check-review.md — issue 4862 / narrative-marriage-uses-preferred-not-birth-name

> Reviewer: Claude (advisory, artifact-only). `$PDCA_TARGET` unset — all
> citations grounded on `patch.diff` alone.

---

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 Spec | PASS | Brief names the defect, success criterion, scope, target file (`libnarrate.py`), and explicitly delegates the name-selection design rule to the human — well-formed. |
| C2 Reproduction (red pre-fix) | PASS | No dedicated C2 gate; C4 oracle asserts `red-without-fix=PASS`. Independently inferred from code logic: pre-fix the `display(spouse)` path returns the primary (later-married) name "White", so `assertIn("Red", sentence)` in `test_uses_birth_name_not_later_preferred_married_name` fails — red confirmed by construction. patch.diff:190–193 |
| C3 Change | PASS | Four files, all within stated scope: (1) `libnarrate.py` — new `NameType` import, two new helpers `_get_birth_name` / `_get_spouse_name`, one callsite replaced (patch.diff:5–66); (2) new test module `libnarrate_test.py` driving production `get_married_string` path (patch.diff:73–233); (3) empty `__init__.py` for the test package; (4) `po/POTFILES.skip` entry for both new files. No out-of-scope touch. |
| C4 Verification (red→green) | PASS | Gate reports `green-with-fix=PASS / red-without-fix=PASS`. Logic independently verified: `test_uses_birth_name_not_later_preferred_married_name` and `test_stable_when_a_later_preferred_name_is_acquired` are red pre-fix (primary name returned instead of birth name) and green post-fix; `test_falls_back_to_preferred_name_without_a_birth_name` is green both ways. check-gates.json:38 |
| C5 Causal adequacy | PASS | Root cause is direct: `_nd.display(spouse)` / `name_display.display(spouse)` always resolves to the *current primary* name, which is mutable. Fix changes resolution to `_get_birth_name` → `display_name(name)`, a stable data-type selection — not a symptom guard. C5 smell-test does not fire: no `hasattr`, no try/except capability probe, no runtime guard over a path that assumes the capability present. patch.diff:17–52, 62–66 |
| T1 Structure | N/A | Core-only change; addon-layout check (doc 16 §Structure) is addon-specific. Gate correctly marked N/A. check-gates.json:55 |
| T2 Shape | PASS | GPL-2.0+ header present in new test file (patch.diff:79–96); `po/POTFILES.skip` extended with both new `.py` files in correct location (patch.diff:238–245). Gating T2-potfiles gate PASS. check-gates.json:64,72 |
| T3 Runtime | PASS | Baseline comparison: 7 known-red tests, matches recorded baseline, no new failures introduced. Tree-drift note (`detached@674e3b`) is a staleness caveat on the baseline tree, not a patch defect. check-gates.json:83 |
| T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in bundle; gate correctly waived. check-gates.json:91 |
| T5 Judgment | PASS | Change is tight and well-scoped: two small pure-function helpers, one callsite, 155-line test covering the three required scenarios. One minor undocumented edge: if a person carries *multiple* `NameType.BIRTH` names, `_get_birth_name` takes the first in primary-then-alternate order (patch.diff:25–27); this is reasonable but the behavior is unspecified. Adding `__init__.py` to the pre-existing `gramps/plugins/lib/test/` directory converts it from a namespace package to a regular package — standard Gramps practice and needed for test discovery in this layout. No scope creep; no Plan-exit smell. |
| Validation — fitness-to-purpose | NEEDS-HUMAN | **Design call: should narrative-report marriage sentences name spouses by Birth Name rather than currently-preferred name?** — the fix implements this rule but the brief explicitly reserves the choice to the human (§Disposition); wrong rule means correct mechanics solving the wrong problem, so human sign-off on the name-selection policy is required before merge. |

---

## Notes for human sign-off (§6 items)

- [ ] **V — Name-selection rule design decision.** The fix adopts "use `NameType.BIRTH` if present, else fall back to primary name." Confirm this is the intended rule for the Gramps narrative engine. Specifically: (a) is `NameType.BIRTH` the right discriminator (vs. e.g. the *first* name the person held at event time)? (b) is the fallback to primary name acceptable when no Birth Name exists, or should it also be flagged / produce a warning? The mechanical implementation is correct for the stated rule; the rule itself is the open question.

---

*Advisory review — does not gate accept. All NEEDS-HUMAN rows above must be cleared by the human before merge.*
