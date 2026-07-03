Task under review: fix issue 7924 so saving a parent primary editor first resolves any dirty child primary editor and commits the completed reference graph rather than dropping the child reference.

Target caveat: `$PDCA_TARGET` is readable and `git apply --check patch.diff` succeeds, but the checkout is `master` at `aef9f35ec6` while the brief targets `maintenance/gramps61`; citations for unchanged source are grounded on `$PDCA_TARGET`, and citations for added code are grounded on `patch.diff`.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The brief states the bug, intended linked DB end-state, shared save-boundary scope, and abort-on-cancel behavior at `brief.md:18`, `brief.md:24`, `brief.md:36`, and `brief.md:43`. |
| C2 — C2 Reproduction (red pre-fix) | PASS | The red condition is re-derived from source: `EditFamily.add_mother_clicked` spawns `EditPerson` with `new_mother_added` at `/home/eddie/gramps/gramps/gramps/gui/editors/editfamily.py:946`, but `__do_save` reads `get_mother_handle()` before closing children at `/home/eddie/gramps/gramps/gramps/gui/editors/editfamily.py:1295` and `/home/eddie/gramps/gramps/gramps/gui/editors/editfamily.py:1340`. |
| C3 — C3 Change | PASS | The patch routes OK through a shared `EditPrimary` pre-save hook and adds descendant-window traversal, matching the requested shared-layer change rather than a Family-only guard (`patch.diff:17`, `patch.diff:46`, `patch.diff:126`). |
| C4 — C4 Verification (red->green) | FAIL | `git apply --check patch.diff` passes, but the bundle has no runnable red->green core/interface test in `patch.diff`, and the configured C4 gate records verification as unverifiable because no core test ships (`check-gates.json:33`). |
| C5 — C5 Causal adequacy | FAIL | The patch sets `outcome["proceed"] = True` before `self.save()` returns (`patch.diff:102`), but child saves can show an error and return without closing or firing the callback, e.g. empty or duplicate Person at `/home/eddie/gramps/gramps/gramps/gui/editors/editperson.py:918`, `/home/eddie/gramps/gramps/gramps/gui/editors/editperson.py:929`, and `/home/eddie/gramps/gramps/gramps/gui/editors/editperson.py:962`; parent save can still proceed with the reference unresolved. |
| T1 — T1 Structure | N/A | No addon path or addon manifest is touched; the patch changes only core files under `gramps/gui/...` (`patch.diff:1`, `patch.diff:118`). |
| T2 — T2 Shape | PASS | The patch modifies existing GPL-covered Python files only, adds no new core `.py` file requiring POTFILES registration, and the configured T2 gates pass (`check-gates.json:60`, `check-gates.json:69`). |
| T3 — T3 Runtime | PASS | The recorded runtime gate matches the baseline with 7 known reds and notes only baseline tree drift, not a patch-specific runtime regression (`check-gates.json:78`). |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` is in the bundle, so contribution-wrapper review does not apply (`check-gates.json:87`). |
| T5 — T5 Judgment | FAIL | The shared-hook direction is sound, but the failed-child-save path above preserves the original class of incomplete parent commits; this should not pass Check without a success signal from the child save. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: after C5 is fixed and red->green verification exists, a human must drive the GUI flow from `brief.md:24` and decide whether the observed Save/Cancel/discard behavior is acceptable for real users and nested editor chains. |

## 6 Human Decisions

1. V — Validation fitness-to-purpose: clear only after a patched build is manually driven through the reporter flow: Relationships view -> Add a new family with person as parent -> add a new mother -> enter a name -> click Family OK -> choose Save in the child prompt -> confirm the family has `mother_handle` linked to the saved person and the person has the family back-reference. Also check Cancel keeps the parent open and uncommitted, and Close without saving intentionally discards the child contribution.

## Blocking Finding

The patch does not distinguish "child save succeeded" from "child save was attempted but validation failed." In `_resolve_before_parent_commit`, `_save()` sets `outcome["proceed"] = True` before calling `self.save()` (`patch.diff:102`), but existing primary editor saves can abort after validation errors while leaving the editor open and without invoking the completion callback, as `EditPerson.save()` does for empty or duplicate records (`/home/eddie/gramps/gramps/gramps/gui/editors/editperson.py:918`, `/home/eddie/gramps/gramps/gramps/gui/editors/editperson.py:929`, `/home/eddie/gramps/gramps/gramps/gui/editors/editperson.py:962`). In that case the parent proceeds to commit even though the child reference never landed, which is the defect class the patch is meant to eliminate.
