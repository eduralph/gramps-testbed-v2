# Cross-vendor reviewer (advisory, artifact-only)

Reviewer family: codex. Inputs: patch.diff, brief.md, check-gates.json (build-notes.md withheld).

## Per-item verdicts
- PASS — re-ran asserted evidence: stub red→green confirmed.
- PASS — every cited path:line grounds on the target branch.
- PASS — diff stays within one logical fix (model-decidable).
- NEEDS-HUMAN — validation fitness-to-purpose: is this the right thing at all? (always-human by design)
