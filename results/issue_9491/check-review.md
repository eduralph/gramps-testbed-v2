# Check Review

Artifact note: `patch.diff` is absent from this review directory. The brief describes this as verification-only with no patch, so I treat the missing diff as expected context rather than a patch defect. `$PDCA_TARGET` is readable, but its working tree is currently on `fix/bug-8850-gedcom-import-cal-date-case-sensitive`; the `maintenance/gramps61` ref is present and was used for target evidence. `git ls-tree --name-only maintenance/gramps61` lists `pyproject.toml` at root entry 34 and no `setup.py`; `pyproject.toml:23` and `pyproject.toml:25` show the PEP-517 build entry.

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | The success target is narrow and checkable: the old direct `setup.py` invocation premise is gone because the target root has no `setup.py` and `pyproject.toml:23` defines the build-system table. |
| C2 — C2 Reproduction (red pre-fix) | N/A | The original red case was `./setup.py build`, but on `maintenance/gramps61` there is no root `setup.py` to execute, so pre-fix reproduction is obsolete rather than runnable. |
| C3 — C3 Change | N/A | No source patch is expected or present; the target condition already exists, with the build backend declared at `pyproject.toml:25`. |
| C4 — C4 Verification (red→green) | PASS | Verification fits this cycle: root listing of `maintenance/gramps61` shows no `setup.py`, and `pyproject.toml:23`/`pyproject.toml:25` confirm the build entry has moved to `pyproject.toml`; the missing-diff gate failure is not a substantive verification failure for a no-patch cycle. |
| C5 — C5 Causal adequacy | PASS | The reported failure path depended on executing root `setup.py`; that artifact is absent on the target ref, so the python2 shebang misselection path is removed rather than merely masked. |
| T1 — T1 Structure | N/A | No addon or layout-bearing patch exists; root packaging evidence is limited to `pyproject.toml:23`, outside addon structure rules. |
| T2 — T2 Shape | N/A | No Python source was changed or added, so GPL/header/style/POTFILES checks have no touched-file surface. |
| T3 — T3 Runtime | PASS | There is no runtime code delta to regress, and the verification target is static packaging state: `pyproject.toml:23`/`pyproject.toml:25` define the build entry while root `setup.py` is absent. |
| T4 — T4 Contribution | N/A | No commit message, PR body, or code contribution wrapper is part of this verification-only artifact set. |
| T5 — T5 Judgment | PASS | Reviewer judgment finds no patch-level blocker: the only automation failure is the expected absence of `patch.diff`, while target evidence satisfies the stated obsolete-defect claim. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | DECISION OWED: decide whether issue 9491 should be closed as obsolete on `maintenance/gramps61`, because the evidence proves the `setup.py` shebang path is gone but only a human can accept that as the tracker disposition rather than requiring historical backport work. |

## §6 Human Clearance

1. V — Validation — fitness-to-purpose: Decide whether to close issue 9491 as obsolete for `maintenance/gramps61`. The impact is tracker disposition: accepting closure means no code change or test is required because the defect's invocation surface is gone; rejecting it means the team wants some other action outside this verification-only scope.
