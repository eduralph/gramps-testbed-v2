# Brief — issue 6250 / verify-pango-get-iterator-availability

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** verify-pango-get-iterator-availability
- **Defect:** Reported (v4.1.0): under GTK3 introspection, `get_iterator()` was not
  available on a Pango attribute list, so a workaround was added (libcairodoc). The ticket
  asks to reintroduce the proper `get_iterator`-based code "when introspection makes
  get_iterator available."
- **Success criterion:** On `maintenance/gramps61`, determine whether
  `Pango.AttrList.get_iterator()` (and `Pango.AttrIterator`) is now available via the
  PyGObject bindings the Gramps build ships. The verification answers the ticket's
  open condition: (a) **available** → the workaround is obsolete and the ticket is
  actionable as a small cleanup (record that finding; the cleanup itself is a separate
  decision, not done blind here); (b) **not available** → the workaround is still required
  → resolve as wontfix/by-design (keep the workaround). Either way, no functional change
  ships from this verification bundle.
- **Invariant to restore:** n/a — investigative verification of a binding-availability
  precondition, not a user-facing defect to repair.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** low — verification/probe only.
- **Scope:** verify availability of `Pango.AttrList.get_iterator` in the supported GI
  stack and report whether the libcairodoc workaround
  (`gramps/plugins/lib/libcairodoc.py`, the `## GTK3 PROBLEM: get_iterator no longer
  available!!` block) is still needed. / out of scope: actually reintroducing/removing the
  workaround, touching the cairo doc rendering, any behaviour change.
- **Repro instruction:** there is no user-facing repro; the workaround prevents the
  original error. Probe: in the build's python, `from gi.repository import Pango;
  hasattr(Pango.AttrList, "get_iterator")` (and whether it is usable) on
  `maintenance/gramps61`.
- **Test file:** none — investigative verification; the result is a written finding in the
  bundle. If `get_iterator` is confirmed available, a follow-up bundle would own the
  reintroduction + its regression test.
- **Citations expected:** cite the workaround site
  `gramps/plugins/lib/libcairodoc.py` (`## GTK3 PROBLEM: get_iterator no longer
  available!!`, the surrounding fallback) and the Pango GI availability result.
- **New/removed files:** none.
- **Prior-art check (triage cycles):** searched by path
  `gramps/plugins/lib/libcairodoc.py` on `upstream/maintenance/gramps61` — the workaround
  comment and fallback are still present; no reintroduction commit. → status unchanged
  since the report; this bundle verifies the binding precondition and resolves accordingly.
- **Mantis:** 6250
- **Disposition hint:** POSSIBLY-FIXED → verify first

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.

## Iteration 1 — carry-forward (from the previous attempt)
- Sign-off rationale: Brief scoped out the actual cleanup ("no functional change ships from this verification bundle"). Finding confirmed get_iterator is fully available (Pango 1.52.1 CI image, 1.57.0 host). Re-scope the brief to: reintroduce the OLD EASY CODE get_iterator loop (libcairodoc.py:674-684), remove the workaround (libcairodoc.py:685-714), and ship a regression test over the paragraph-split attribute re-indexing path. The verification finding in this bundle stands as evidence for the new brief.
- Failing gate: C4 fix verified: test red pre-fix, green post-fix — run-verify.sh: no patch.diff in /home/eddie/workspace/gramps-testbed-v2/results/issue_6250
- Full previous attempt preserved in `iteration-v1/` (patch.diff, build-notes.md, SUMMARY.md, check-*).
- Address the above; do NOT re-attempt the rejected approach unchanged. Satisfy the brief's Success criterion (the end result).
