# Check review — addon-tests-init-py-gramps60 (addons-source #43)

> Advisory, artifact-only, decorrelated. Inputs: `patch.diff`, `brief.md`,
> `check-gates.json`. `build-notes.md` deliberately withheld. Every verdict below
> is re-derived from the artifacts, not copied from `check-gates.json`.

## Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — C1 Spec | PASS | brief.md is complete and well-formed: defect (brief.md:8-14), success criterion (15-17), invariant stated over the category (18-24), scope/out-of-scope (28-31), repro command (32-36). Spec is sufficient to adjudicate. |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | No C2 gate configured (check-gates.json:15-22, result "none"); build-notes.md withheld so the *behavioural* red (suites skipped pre-fix) is not in my artifacts. Structural absence is corroborated — all four entries are `new file ... e69de29bb` (patch.diff:1-12), proving the markers did not exist — but "run-addon-unit does not discover the four suites" (brief.md:35-36) is asserted, not evidenced. Human must confirm the red was observed. |
| C3 — C3 Change | PASS | patch.diff adds exactly the four dirs named in brief.md (`CalculateEstimatedDates`, `DataEntryGramplet`, `Form`, `TMGimporter`), each `tests/__init__.py`, each the empty blob `e69de29bb` (patch.diff:1-12). Matches scope (empty markers, brief.md:28); no gramps61 path touched (respects brief.md:25-27). |
| C4 — C4 Verification (red→green) | NEEDS-HUMAN | Two-part problem a human must clear. (a) The only gating row, `C4-verify` (check-gates.json:33-40, gating:true), fails on "patch ships no addon test (test_*.py)" — but brief.md:42-44 explicitly de-gates this oracle for a structural/discovery fix; that mechanical fail is mis-targeted and is what drives the overall `fail`. (b) The brief's *designated* substitute oracle `T3-addon-unit-60` is itself red (check-gates.json:78-84) with an unparsed "runner exited 1 ... no matching baseline signature" mode — so green-after-fix is not demonstrated by any oracle. Verification is not established. |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Root cause (missing package marker → dotted-path `<Addon>.tests.<module>` not importable) maps 1:1 to the fix (add the marker), which is causally clean on its face. But the marker-adding patch leaves `T3-addon-unit-60` red (check-gates.json:78-84): if the markers were the whole cause, gramps60 discovery should now go green. Either the red is environmental/baseline drift or the fix is necessary-but-not-sufficient — uncontestable only with a clean post-fix run. Oracle is reviewer + human sign-off (check-gates.json:42-48). |
| T1 — T1 Structure | PASS | doc16 §Structure wants no `__init__.py` at the addon root but a marker in `tests/`; the patch adds `tests/__init__.py` at exactly that location (patch.diff). The recorded T1 fail "TMGimporter tests/ lacks the __init__.py marker (SHOULD)" (check-gates.json:51-57) is the pre-application tree — i.e. the very defect being fixed — not a property of the patched tree. (Flagging that the T1 oracle inspected the unpatched working tree while C4-verify inspected the patch file: confirm gate ran against applied tree.) |
| T2 — T2 Shape | N/A | The T2 fail is "test_linux_libtmg.py: no GPL header" (check-gates.json:60-66) — a pre-existing `test_*.py` the patch does not touch (patch.diff adds only empty markers). Missing-header on an unmodified file is a pre-existing condition and out of scope per brief.md:31 ("any test-logic or production change" excluded). Not attributable to this change; empty package markers carry no header, matching the gramps61 ones (brief.md:28). |
| T3 — T3 Runtime | NEEDS-HUMAN | The brief's gating runtime check `T3-addon-unit-60` is red with an unparsed/ambiguous failure mode (check-gates.json:78-84) and needs human triage — it cannot be auto-adjudicated. The other red rows are not plausibly caused by a four-empty-file patch: core `gramps.plugins.test.imports_test::test_imp_3_4` +6 (check-gates.json:69-75) and interface smoke `setUpClass` (96-102) have no execution path from adding empty `__init__.py` files, so they read as environmental/baseline drift, not regressions from this change. `T3-addon-unit-61` red is expected — brief.md:25-27/42-44 says gramps61 already conforms and must not be touched. |
| T4 — T4 Contribution | N/A | No commit-msg.txt or pr-description.md in the bundle (check-gates.json:104-110), consistent with STOP discipline / draft-only (brief.md:55-59). Nothing to evaluate; gate's pass-as-N/A is correct. |
| T5 — T5 Judgment | NEEDS-HUMAN | Oracle is reviewer + human sign-off (check-gates.json:113-120). On its face the change is low-risk, parity-restoring, scope-respecting. But judgment cannot be cleanly PASS while the designated gate (`T3-addon-unit-60`) is red and the gating oracle is mis-configured per brief — both are live human-judgment items. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human (check-gates.json:123-129, "human at sign-off"). Does the fix actually achieve the success criterion — the four suites *discovered and run, not skipped* (brief.md:15-17) — in the maintainer's gramps60 environment? Cannot be settled from artifacts. |

## §6 — Items the human must clear

1. **C2 Reproduction** — confirm the pre-fix red (four suites skipped by `run-addon-unit.sh CORE_VERSION=6.0`) was actually observed; not in withheld build-notes.md.
2. **C4 Verification** — (a) confirm `C4-verify` is correctly de-gated for this structural fix per brief.md:42-44 (it is currently the *only* gating row and is forcing overall `fail`); (b) re-run / triage the designated gate `T3-addon-unit-60`, which is red with an unparsed failure — green-after-fix is not yet demonstrated.
3. **C5 Causal adequacy** — decide whether the residual `T3-addon-unit-60` red is environmental, or evidence the markers alone are not sufficient (necessary-but-not-sufficient root cause).
4. **T3 Runtime** — triage the ambiguous `T3-addon-unit-60` failure mode; confirm the core-unit and interface-smoke deltas are pre-existing baseline drift (no causal path from empty markers) rather than caused here.
5. **T5 Judgment** — overall accept/reject given the gate-config mismatch above.
6. **V Validation** — sign-off that the four addon suites are discovered and run on gramps60, meeting the stated purpose.

## Reviewer note (config mismatch)

The bundle's overall `fail` is driven solely by `C4-verify` (the one `gating:true`
row), which brief.md:42-44 explicitly says does **not** apply to this structural
fix. The brief's intended gate, `T3-addon-unit-60`, is recorded `gating:false`.
The gate configuration and the brief disagree about what gates this issue; this is
the central item for the human at sign-off. Separately, T1 appears to have been
evaluated against the unpatched tree (it reports the marker the patch adds as still
missing) — verify each runtime/structure oracle ran against the *applied* patch.
