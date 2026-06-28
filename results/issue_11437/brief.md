# Brief — issue 11437 / dwr-tree-preserves-hyphenated-names

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** dwr-tree-preserves-hyphenated-names
- **Defect:** The Dynamic Web Report (DWR) **tree** view replaces hyphens inside names
  with spaces — a given name "Jan-Åke" or surname "HAMILTON-SMITH" renders as "Jan Åke" /
  "HAMILTON SMITH" in the SVG tree only. Every other DWR surface (indexes, text tabs,
  mouse-over) shows the hyphen as entered. The inconsistency is the defect (the hyphen is a
  valid name character).
- **Success criterion:** A person whose given name or surname contains a hyphen renders
  with the hyphen intact in the DWR tree (SVG) view, matching how the same name appears in
  the DWR indexes/tabs.
- **Invariant to restore:** A rendered name preserves the characters of the stored name —
  the tree renderer does not silently rewrite a hyphen to a space. (Behavioural / data-
  fidelity invariant; rationale: the tree is one presentation of the same name shown
  faithfully elsewhere, so it must not lose characters the model holds.)
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60
- **Surfaces:** data
- **Difficulty:** medium — confined to the DynamicWeb addon, but the hyphen→space rewrite
  may live in the name data exported by `DynamicWeb/dynamicweb.py` OR in the SVG tree
  renderer `DynamicWeb/dwr_svg.js`; Do must locate which (the other surfaces keep the
  hyphen, so the rewrite is specific to the tree path).
- **Scope:** the hyphen→space substitution applied only on the DWR tree-node name path in
  the DynamicWeb addon (the Python name export feeding the tree, or the JS tree renderer).
  / out of scope: the DWR indexes/text tabs/search (already correct), other addons,
  non-hyphen characters, the SVG layout/styling.
- **Repro instruction:** build a tree with hyphenated names (e.g. given "Jan-Åke", surname
  "HAMILTON-SMITH") → Reports → Web → Dynamic Web Report → open the generated report →
  navigate to such an individual in the **tree** view: the hyphen shows as a space, while
  the indexes/tabs/mouse-over keep the hyphen.
- **Test file:** DynamicWeb/tests/test_dwr_tree_names.py (addon convention: `tests/`
  package, `test_*.py` prefix, loaded as `DynamicWeb.tests.test_dwr_tree_names`). Assert
  the tree-node name produced by the **production** name path retains the hyphen. If the
  rewrite turns out to be JS-only (`dwr_svg.js`) with no Python seam, there is no red→green
  unit mechanic — record C4 as `PDCA-UNVERIFIABLE` (test-only / no production-Python seam)
  for human sign-off, and ship the JS fix + a stated manual repro.
- **Citations expected:** Do must cite path:line on maintenance/gramps60 for every change.
- **New/removed files:** test lives in the addon (`DynamicWeb/tests/`), not core — no
  `po/POTFILES` entry (addons are not in the core POT).
- **Prior-art check (triage cycles):** searched by path `DynamicWeb/` on
  `upstream/maintenance/gramps60` — recent commits are the OSM `feature.get('name')` fix
  (bug 12544) and the Python-2 cleanup; no hyphen/name-rendering fix. No matching fork PR
  by this path. → unfixed.
- **Mantis:** 11437
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
