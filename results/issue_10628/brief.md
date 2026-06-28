# Brief — issue 10628 / deep-connections-repeats-same-path

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** deep-connections-repeats-same-path
- **Defect:** In the Deep Connections gramplet, when multiple distinct paths exist between the
  home person and the target, pressing "Continue to search for additional relations" returns the
  **same path repeatedly** instead of advancing to a genuinely different connection — so the
  user never sees the alternative paths that exist in their tree. (Addon
  ../addons-source/DeepConnectionsGramplet.) Related but distinct from the recently-merged
  "Keep the Home person out of Deep Connections path interiors" (#946) and from the
  extraneous-relationship report #11312.
- **Success criterion:** for a tree with two or more independent paths between home and target,
  successive "Continue" searches yield *distinct* paths (no immediate repeat of an
  already-reported path), so all genuinely different connections are reachable. Demonstrable by
  C4-verify driving the gramplet's path-search routine on a fixture tree.
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md §1.1).
  (Correctness requirement: an iterative path search does not re-emit a path it has already
  reported while undiscovered distinct paths remain.)
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60
- **Surfaces:** data
- **Difficulty:** medium
- **Scope:** the "find next connection" iteration that fails to exclude the
  already-reported path, causing repeats. / out of scope: the result formatting, the
  home-person-interior handling already fixed in #946, and the relationship-naming logic.
- **Repro instruction:** on ../addons-source @ maintenance/gramps60 with a tree that has ≥2
  distinct home→target paths, run Deep Connections and press "Continue" repeatedly — observe the
  same path returned each time.
- **Test file:** DeepConnectionsGramplet/tests/test_deep_connections_paths.py (NEW; addon
  `tests/` package, `test_*.py` prefix, loaded as
  `DeepConnectionsGramplet.tests.test_deep_connections_paths`). The test MUST drive the
  production path-search routine on a seeded multi-path fixture (principles.md §3.4), not a copy.
- **Citations expected:** Do must cite path:line on the target branch for every change.
- **New/removed files:** addon test (no core POTFILES). Ensure the `tests/` package convention
  (doc 16 §Testing) is followed for the addon.
- **Prior-art check (triage cycles):** searched by path `DeepConnectionsGramplet` on
  upstream/maintenance/gramps60 — recent commits are the #946 home-person-interior fix
  (323448ff7 / merge 91a759e2a); none addresses the repeated-path iteration. No open/closed PR
  found for this specific defect.
- **Mantis:** 10628
- **Disposition hint:** likely-fix
