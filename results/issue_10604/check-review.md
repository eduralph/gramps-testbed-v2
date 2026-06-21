# Check Review — issue 10604 / docreportdialog-css-keyerror-minus-one

**Reviewer role:** Check (advisory, artifact-only, decorrelated from builder)
**Artifacts read:** `brief.md`, `check-gates.json`, `patch.diff`
**Withheld artifact:** `build-notes.md` (intentionally absent)
**Source grounding:** `$PDCA_TARGET` unset — all path:line citations derived from `brief.md`
and `check-gates.json` only; no live source tree was read.

---

## §1 Summary

`patch.diff` is empty (0 bytes). The Do took the verify-first / no-change path explicitly
described in `brief.md` ("if it cannot be reproduced, route to §6 NEEDS-HUMAN
(likely-close) — do not manufacture a change"). The disposition is structurally consistent
with the brief, but three items cannot be closed by artifact review alone and route to §6.

---

## §2 Verdict Table

| Item | Verdict | Basis |
|---|---|---|
| C1 — Spec | PASS | `brief.md` is present and complete: defect, success criterion, invariant, scope, repro steps, test-file location, prior-art commit (`5f1b719810`), disposition hint, all populated. |
| C2 — Reproduction (red pre-fix) | NEEDS-HUMAN | `patch.diff` is empty and `build-notes.md` is withheld; no artifact in the bundle confirms a repro was attempted on maintenance/gramps61 and found non-reproducible. `brief.md` requires "Do MUST reproduce … before writing any production change." The cannot-reproduce conclusion must be documented by a human. |
| C3 — Change | N/A | `patch.diff` is 0 bytes — no production change was shipped. `brief.md` explicitly authorises this outcome ("do not manufacture a change" / "no production patch ships"). |
| C4 — Verification (red→green) | NEEDS-HUMAN | No test added; no code changed; `check-gates.json` C4-verify: `unverifiable` (gating); C4-verify-interface: `unverifiable`. `brief.md` routes C4 to §6 for the verify-first close ("C4 routes to §6 (verify-first close)") and flags GUI instantiation as likely impractical for headless test. Manual repro confirmation required. |
| C5 — Causal adequacy | NEEDS-HUMAN | `brief.md` identifies the guard at `_docreportdialog.py:274-279` (commit `5f1b719810`, 2016) as causally adequate, but `$PDCA_TARGET` is unset and no source lines appear in `patch.diff`; the Check reviewer cannot independently confirm the guard exists and covers the `active == -1` + empty-CSS path. Requires human verification against the live tree. |
| T1 — Structure | N/A | `check-gates.json` T1: "N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)"; confirmed by 0-byte patch — no addon layout to check. |
| T2 — Shape | N/A | `check-gates.json` T2: "N/A: no checkable .py path in patch.diff"; T2-potfiles: pass (trivially — no .py files added or removed). Confirmed by 0-byte patch. |
| T3 — Runtime | PASS | `check-gates.json` T3-unit: pass (matches recorded baseline, 7 known reds); T3-interface: pass ("green (no failures); baseline now clear (1 recorded red(s) gone)"). Both carry "⚠ baseline tree drift: recorded detached@674e3b" — noted but not blocking; tree drift affects confidence in baseline comparisons, not the no-change submission. |
| T4 — Contribution | N/A | `check-gates.json` T4: "N/A: no commit-msg.txt or pr-description.md in the bundle." No change was committed; nothing to wrap. |
| T5 — Judgment | PASS | Do correctly followed the brief's POSSIBLY-FIXED → verify-first disposition: did not manufacture a change, did not patch around a non-reproducible crash, and (implicitly) routed to §6. The empty-patch outcome is the judgment `brief.md` specified for the cannot-reproduce path. |
| V — Validation (fitness-to-purpose) | NEEDS-HUMAN | Always-human item: human must confirm that "verify-first close / no patch" is the appropriate final disposition for Mantis 10604 and that no regression risk is introduced by leaving the existing guard as the sole protection. |

---

## §3 Gate summary

| Gate | Automated result | Gating? | Check verdict |
|---|---|---|---|
| C4-verify | unverifiable | yes | NEEDS-HUMAN (§6.2) |
| C4-verify-interface | unverifiable | no | NEEDS-HUMAN (§6.2) |
| T1-structure | N/A | no | Accepted — no addons |
| T2-shape | N/A | no | Accepted — no .py changed |
| T2-potfiles | pass | yes | Accepted — trivially satisfied |
| T3-unit | pass | no | Accepted with drift caveat |
| T3-interface | pass | no | Accepted with drift caveat |
| T4-contribution | N/A | no | Accepted — no commit shipped |

One gating gate (C4-verify) is `unverifiable`; it is explicitly permitted by `brief.md`
to route to §6 for the verify-first-close path, so it does not block the overall
check verdict.

---

## §4 Observations

**T3 baseline tree drift.** Both T3 runs report "⚠ baseline tree drift: recorded
detached@674e3b". This means the recorded baseline was captured at a different tree state
than the test run. T3-interface additionally reports one previously-recorded red is now
gone — this *could* reflect environment change rather than a product fix, and the
baseline should be refreshed before future runs are treated as authoritative.

**C2 / build-notes gap.** The brief's verify-first instruction ("Do MUST reproduce on
maintenance/gramps61 before writing any production change") implies that if the Do found
the bug non-reproducible, that finding should be documented. `build-notes.md` is the
natural home for this, but it is withheld from this review. The human reviewer should
confirm that `build-notes.md` (or an equivalent artifact) records a genuine repro
attempt, not a skipped step.

**Prior-art guard confidence.** `brief.md` is detailed and specific: commit `5f1b719810`
(2016) added `active == -1` handling at `_docreportdialog.py:274-279`, citing bugs
7585/8189/9461 as prior context. This is a strong signal, but it is the brief-author's
assertion, not a live read by the Check reviewer. §6.1 closes this.

---

## §5 Overall verdict

**CONDITIONAL PASS — three §6 items must be cleared by a human before final close.**

The structural decision (no production change, verify-first close) is correct and
brief-compliant. The automated gates that ran are consistent. Nothing in the available
artifacts contradicts the builder's conclusion. The three NEEDS-HUMAN items are genuine
open questions, not defects in the submission.

---

## §6 Human-clearance items

The following must be reviewed and signed off by a human before issue 10604 is closed.

### §6.1 — C2 / C5: Confirm repro attempt and causal adequacy

**Action required:** Open the live maintenance/gramps61 source and confirm:

1. The guard at `_docreportdialog.py:274-279` is present on the branch HEAD (not just in
   `brief.md`'s description).
2. The guard covers the exact path: `get_active() == -1` with an empty `self.css` list —
   i.e., it substitutes `self.style_name` and does not index `self.CSS[-1]`.
3. Confirm (from `build-notes.md` or equivalent) that the Do attempted the repro scenario
   on maintenance/gramps61 (Help → Plugin Manager → Hide Webstuff; restart; run HTML/graph
   report; click OK) and found no `KeyError: -1` raised.

**Clearance condition:** Human signs off that (a) the guard is confirmed live in the tree
and (b) the repro attempt is documented as non-reproducible.

### §6.2 — C4: Manual verification (verify-first close)

**Action required:** Perform (or confirm was performed) the manual repro sequence:

> Help → Plugin Manager → Hide the "Webstuff" plugin → Restart Gramps → Run a report
> that offers an HTML/CSS document option → Click OK with no CSS selectable.

Confirm: no `KeyError: -1` is raised; the dialog handles the empty-CSS / `get_active()
== -1` state gracefully.

**Clearance condition:** Human records the observed behaviour and signs off that the
existing guard is sufficient. If a headless dogtail test is later deemed practical, a
regression test in `gramps/gui/plug/report/test/_docreportdialog_test.py` (with entry in
`po/POTFILES.skip`) should be added at that time; it is not required to close this issue.

### §6.3 — V: Fitness-to-purpose sign-off

**Action required:** Human confirms that the "no patch / verify-first close" disposition
is the correct final outcome for Mantis 10604 — i.e., that no additional fix, back-port,
or user-visible change is needed, and that the issue can be closed as ALREADY-FIXED.

**Clearance condition:** Human sign-off recorded in the issue tracker (Mantis 10604) with
reference to commit `5f1b719810` as the resolution.
