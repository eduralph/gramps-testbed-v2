# Check review — issue 820-review-nits (iteration 2)

> Advisory, artifact-only, decorrelated. Inputs: `patch.diff`, `brief.md`,
> `check-gates.json`. `build-notes.md` withheld by design — verdicts below are
> re-derived from the patch and brief, not from the builder's narrative.

## Verdict table

| Item | Verdict | Basis |
| --- | --- | --- |
| C1 — C1 Spec | PASS | `brief.md` is a complete, coherent spec: defect (a)–(e) (brief.md:9-22), success criterion (brief.md:23-26), per-item repro (brief.md:40-43), test-file requirement (brief.md:44-46). |
| C2 — C2 Reproduction (red pre-fix) | NEEDS-HUMAN | No repro gate configured (check-gates.json:15-21). (a)/(b)/(d)/(e) are behaviour-preserving/CI-observable — no failing test to reproduce. (c)'s new `test_addon_paths.py` exercises the *new* `is_in_addons_tree` helper, so it never ran red against the old `ADDONS_ROOT in pdata.fpath` code (patch.diff:247-285); red pre-fix state is unverifiable from artifacts. |
| C3 — C3 Change | PASS | All five nits implemented: (a) `make_gramps_user` removed (patch.diff:121-129); (b) public `type_plugins()` sweep (patch.diff:167-176); (c) `is_in_addons_tree` prefix check (patch.diff:99-112); (d) `.gpr.py` no longer excluded from `py_compile` (patch.diff:40-41); (e) glob tightened to `maintenance/gramps[0-9][0-9]` in ci.yml (patch.diff:14,17) and docker-build.yml (patch.diff:56). |
| C4 — C4 Verification (red→green) | FAIL | Gating gate failed: `./engine/scripts/ubuntu/run-verify.sh` → "error: .github/workflows/ci.yml: patch does not apply" (check-gates.json:33-39). red→green never executed against the verification base — same class of harness/path failure that sank iter‑1 (brief.md:59). |
| C5 — C5 Causal adequacy | NEEDS-HUMAN | Sign-off gate (check-gates.json:42-48) and contested root-cause in iter‑1 (brief.md:58). My independent re-derivation supports adequacy: the `(None, *PTYPE)` sweep (patch.diff:172) makes `type_plugins(None)` recover ptype-unset records, so the union equals the old `__plugindata` master list AND a half-registered (`_ptype is None`) addon still surfaces → the iter‑1 silent-coverage-loss objection appears resolved. Human must clear the contested cause. |
| T1 — T1 Structure | N/A | Addon-layout rule (folder==id, target_version, fname, no `__init__.py`) targets *addons*; this patch adds only test modules (`tests/addon_paths.py`, `tests/test_addon_paths.py`) and workflow edits — no addon dir. The gate's "no .gpr.py" FAIL (check-gates.json:51-57) is a false positive for this change class. |
| T2 — T2 Shape | PASS | Both new files carry the GPL header and conform to doc 16 §Coding style — `addon_paths.py` (patch.diff:66-84) and `test_addon_paths.py` (patch.diff:202-220); gate confirms 2 files conform (check-gates.json:60-66). |
| T3 — T3 Runtime | NEEDS-HUMAN | 6.0 matrix green (check-gates.json:69-75); 6.1 matrix reports DELTA: 1 new failure `Sqlite...ExportSQLTestCase::test_export_sq` (check-gates.json:78-84). Patch touches no Sqlite/export code, and iter‑1 saw the same suite fail (8×, brief.md:61) — strongly suggests 6.1 baseline flakiness, not this patch. Human must confirm it reproduces without the patch before clearing. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in the bundle, so the commit/PR-wrapper rule has nothing to check (check-gates.json:87-93). |
| T5 — T5 Judgment | NEEDS-HUMAN | Ambiguous scope. `brief.md:5-6,36,50` flags the five nits as *independent* and *splittable*, the iter‑1 carry-forward explicitly says "Prefer splitting per logical change… at minimum, item (b)'s enumeration fix is its own change" (brief.md:58), and global discipline is one-logical-change-per-PR — yet this is a single combined diff covering all five. Human must decide split vs. bundle. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Always-human. Whether the resolved nits meet the brief's end goal (PR #820 CI green on the fork, success criterion brief.md:23-26) is a sign-off judgment, not derivable from artifacts. |

## §6 — Items the human must clear

1. **C2 (reproduction):** No red pre-fix evidence. (c)'s test validates the new
   helper, not the old substring bug; remaining items are behaviour-preserving.
   Confirm whether a genuine red→green (or a stated "no test because behaviour-
   preserving") is acceptable per item.
2. **C5 (contested root-cause):** Re-derivation finds item (b)'s `(None, *PTYPE)`
   sweep equivalent to the old `__plugindata` enumeration and no longer hiding the
   typeless-addon failure class — i.e. the iter‑1 rejection appears addressed.
   Human must ratify this causal claim.
3. **T3 (6.1 Sqlite delta):** `ExportSQLTestCase::test_export_sq` fails on the 6.1
   matrix but the patch touches no Sqlite code and the same failure preceded this
   patch in iter‑1. Confirm it is 6.1 baseline noise (reproduces without the patch),
   not a regression.
4. **T5 (scope):** Decide whether to split this combined diff into per-nit changes
   as the brief and iter‑1 carry-forward both recommend (item (b) at minimum).
5. **Validation (fitness-to-purpose):** Confirm the batch meets the brief's success
   criterion / end goal at sign-off.

## Blocking note

C4 is a **gating FAIL** ("patch does not apply" against the verification base) —
independent of every advisory item above, this batch cannot pass until the patch
applies cleanly on `origin/feature/ci-cd-pipeline-upstream` and red→green actually
runs. This is the same harness/base mismatch that sank iter‑1; rebase/rebuild on
the synced base and re-verify before sign-off.
