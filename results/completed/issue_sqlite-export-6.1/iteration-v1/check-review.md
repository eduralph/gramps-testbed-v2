# Check review — sqlite-export-person-serialize-6.1

Advisory, artifact-only (patch.diff + brief.md + check-gates.json; build-notes.md
withheld). Verdicts below are re-derived independently, not copied from the gate run.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | brief.md:20-24 carries an explicit, load-bearing success criterion (round-trip green on **both** gramps61×6.1 and gramps60×6.0) and a restorable invariant (brief.md:25-37). Spec is well-formed and self-contained. |
| C2 — C2 Reproduction (red pre-fix) | PASS | 6.1 red is concrete and is the original surfacing signal: `ValueError: too many values to unpack (expected 21, got 22)` at `ExportSql.py:684`, surfaced by the `T3-addon-unit-61` matrix gate (brief.md:18,58-63). Caveat: the gramps60×6.0 leg has **no** reproducible red by design (no pre-existing defect) — see §6/C4 framing. |
| C3 — C3 Change | PASS | Change exists and is in-scope: export side absorbs the extra field via `*_,` (patch.diff ExportSql.py `@@ -702`, the new `# 21+ familysearch_sync` line); import side pads to core arity via `data += Person().serialize()[len(data):]` (patch.diff ImportSql.py `@@ -724`). Both are version-tolerant, Person-only, confined to the two files named in brief.md:46-57 plus the test. |
| C4 — C4 Verification (red→green) | FAIL | Gating gate `C4-verify` = **fail** (check-gates.json:33-40). Corroborated: post-fix `T3-addon-unit-61` does **not** show clean green but a DELTA — "runner exited 2 with no parsed failures … a new failure mode" (check-gates.json:78-85). So green is not demonstrated even on the 6.1 leg that should red→green cleanly. The gramps60×6.0 leg's "red-without-fix" half is not satisfiable (no defect) — a framing question the brief flags (brief.md:104-111) but which does **not** rescue C4 because the 6.1 leg itself is non-green. |
| C5 — C5 Causal adequacy | PASS | Fix targets the documented root cause — hardcoded 21-tuple vs core 6.1's 22-field `Person.serialize()`/`unserialize()` (field #21 `familysearch_sync`, commit `4972a2eb4e`) — symmetrically at both ends (export unpack + import rebuild). Padding-with-core-default rather than persisting `familysearch_sync` is the agreed scope (brief.md:51-57(b)); the addon schema stores only a subset. Root cause is uncontested, so the always-human "contested root-cause" trigger does not fire. |
| T1 — T1 Structure | NEEDS-HUMAN | `T1-structure` = fail: "Sqlite: addon dir has __init__.py — breaks plugin loading" (check-gates.json:51-58). But **no `__init__.py` appears in patch.diff** — the change modifies only existing `.py` files. Cannot determine from the three artifacts whether this is a pre-existing addon-root issue or a false-positive matching the legitimate `Sqlite/tests/__init__.py` test-package marker. Human to confirm; not introduced by this change. |
| T2 — T2 Shape | PASS | The flagged `print()` is at `ImportSql.py:897` (check-gates.json:64), well outside this patch's hunks (ImportSql.py `@@ -724,6 +724,12`, i.e. ~724-735) — pre-existing code, not introduced by Do. The touched lines carry no `print()`/style violation; existing files retain their GPL headers. The ⚠ advisory belongs to pre-existing code, not this change. |
| T3 — T3 Runtime | FAIL | The two addon-unit legs that bear the fix both regress from baseline: `T3-addon-unit-60` and `T3-addon-unit-61` each DELTA "runner exited 2 with no parsed failures and no matching baseline signature (a new failure mode)" (check-gates.json:69-85); `T3-addon-interface` E2E adds a new failure (`setUpClass SmokeTest`, :96-103). Only `T3-interface` smoke matches baseline (:87-94). The fix is not demonstrated green on any addon-unit leg. |
| T4 — T4 Contribution | N/A | `T4-contribution` = "N/A: no commit-msg.txt or pr-description.md in the bundle" (check-gates.json:105-111). No commit/PR wrapper present to evaluate; the `Fixes/Bug #id` trailer is waived (fork-tracked, brief.md:91-94). Nothing to assess. |
| T5 — T5 Judgment | NEEDS-HUMAN | Always-human sign-off (oracle "reviewer + human sign-off", check-gates.json:114-120). The branch-target choice — gramps60 → cherry-pick to gramps61 vs direct-to-gramps61 — is an explicit judgment call (brief.md:42-43,113-117); cherry-pick correctness holds only because the fix is version-tolerant (brief.md:119-128). |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human at sign-off (oracle "human at sign-off", check-gates.json:122-129). Whether the round-trip fix as shipped satisfies the addon's real cross-version purpose is the human's call. |

## §6 — Items the human must clear (NEEDS-HUMAN)

1. **T1 / structure — `__init__.py` flag is unattributable from artifacts.** Gate
   reports the Sqlite addon dir has an `__init__.py` that "breaks plugin loading", but
   no `__init__.py` is in patch.diff. Confirm whether this is (a) a pre-existing
   addon-root file (a real, separate defect not this fix's responsibility) or (b) a
   gate false-positive on the legitimate `Sqlite/tests/__init__.py` package marker.
   Note the possible causal tie to the T3 "exited 2 / no parsed failures" runner state
   below — if the addon truly fails to load, that would explain why the addon-unit legs
   produced no parsed test results.

2. **T5 / branch target.** gramps60 (brief default) → cherry-pick to gramps61, vs
   direct-to-gramps61. Maintainer preference overrides. The picked-forward change must
   stay version-tolerant (a hardcode-to-22 fix would break the 6.0 leg).

3. **V / validation fitness-to-purpose.** Human sign-off that the round-trip assertion
   and the pad/`*_` approach meet the addon's cross-version agreement-with-core purpose.

4. **C4 framing the brief asks Check to confirm (does NOT clear C4).** The brief
   (brief.md:104-111) asks that the gramps60×6.0 leg be treated as a *no-regression*
   check, not a red→green one, because there is no pre-existing 6.0 defect. That framing
   is reasonable — but it cannot by itself flip C4 to PASS, because the **6.1** leg
   (the one that should red→green cleanly) post-fix shows a *new failure mode* (runner
   exit 2, no parsed failures), not green. Resolve the 6.1-leg runner state before C4
   can be accepted.

## Bottom line

- **Engineering of the diff is sound and in-scope** (C1/C2/C3/C5 PASS): the export `*_`
  unpack and the import `data += Person().serialize()[len(data):]` pad are minimal,
  symmetric, and version-tolerant exactly as the invariant requires.
- **But verification is not demonstrated** (C4 FAIL gating, T3 FAIL): post-fix the
  addon-unit legs do not show clean green — they exit 2 with no parsed failures, a new
  failure mode versus baseline. Until that runner state is explained and the 6.1 leg
  shows a real green, the bundle's red→green claim is unsubstantiated. This is the
  decisive gap, independent of the gramps60-leg framing question.
