# Check Review — issue 13888 / treedoc-image-source-option

**Reviewer role:** Check (advisory, artifact-only, decorrelated from builder)
**Inputs:** `patch.diff`, `brief.md`, `check-gates.json` (build-notes.md withheld by design)
**Date:** 2026-06-20

---

## §1 Verdict table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — Spec | PASS | `brief.md` states a complete, verifiable success criterion: `images="original"` → `image = {<original path>}` + no comment; `images="thumbnail"` → thumbnail path + `%% original image:` comment. All three branches (spec, test requirement, POTFILES) are present in the patch. |
| C2 — Reproduction (red pre-fix) | PASS | No independent C2 gate configured; derived from C4: `red-without-fix=PASS` confirms the three new test methods (`test_default_is_thumbnail`, `test_original_emits_full_resolution_path`, `test_thumbnail_emits_thumbnail_path_and_comment`) were failing before the production change landed. |
| C3 — Change | PASS | Patch touches exactly the three files `brief.md` §Scope mandates: `treedoc.py` (production change), `treedoc_test.py` (new test), `po/POTFILES.skip` (test registration). No out-of-scope files touched; thumbnailer plugins and GenealogyTree addon are untouched as specified. |
| C4 — Verification (red→green) | PASS | Automated gate `C4-verify` (gating=true): `green-with-fix=PASS / red-without-fix=PASS` — check-gates.json:37–38. |
| C5 — Causal adequacy | PASS | The defect is that PR 1620 (commit 7335883f68) unconditionally routed through `get_thumbnail_path`; the fix inserts a branch at the identical decision point (`write_node`:`for mediaref in person.get_media_list()`) and uses the exact call (`media_path_full(db, media.get_path())`) that PR 1620 removed — matching the stated pre-1620 behaviour without touching any other subsystem. |
| T1 — Structure | FAIL | Automated gate reports `T1 ✗ po: no .gpr.py` (check-gates.json:55). **Likely false positive:** this gate enforces addon layout (doc16-addon §Structure); the patch is a core change (`gramps/gen/plug/docgen/treedoc.py`) and correctly has no `.gpr.py`. Gate is misapplied to a core submission; non-gating (gating=false). Human must confirm gate scope mismatch before closing. |
| T2 — Shape | PASS | Automated gate `T2 ✓ shape: 1 file(s) conform` (check-gates.json:64). New file `treedoc_test.py` carries a GPLv2+ header (patch.diff:7–24); touched production file already had one. |
| T3 — Runtime | PASS | Automated gate `T3-baseline`: matches recorded baseline of 7 known test reds (check-gates.json:73). Note: baseline recorded at `detached@674e3b` — tree drift flag present but suite passes at that baseline; non-gating. |
| T4 — Contribution | N/A | Automated gate self-reports N/A: no `commit-msg.txt` or `pr-description.md` in bundle (check-gates.json:82–83). Contribution wrapper artifacts are outside this patch's scope; gate passed without finding a violation. |
| T5 — Judgment | PASS | (a) Default unchanged: `EnumeratedListOption("images", "thumbnail")` preserves PR 1620 behaviour for all existing users (treedoc.py:197). (b) Comment ordering: `%% original image:` is written before `image = {...}` — inert in LaTeX, no semantic risk. (c) `media_path_full` called once and stored in `original`; no redundant call. (d) Mock target `gramps.gen.utils.thumbnails.get_thumbnail_path` — validity depends on import style; C4 `green-with-fix=PASS` confirms the mock intercepts correctly in practice. (e) Special-character path limitation for `original` mode is acknowledged in `brief.md` §Open questions and not silently inherited. One minor flag: the test mock target would silently do nothing if `get_thumbnail_path` is imported into `treedoc.py`'s namespace with `from ... import`; C4 evidence overrides this concern since the test is confirmed green. |
| V — Validation | NEEDS-HUMAN | Fitness-to-purpose requires human sign-off: (1) print-quality outcome with `original` mode on real media has not been exercised in this review; (2) UI label/placement of the new `"Images"` option in the report dialog needs UX confirmation; (3) branch target (`maintenance/gramps61` vs `master`) requires maintainer (azrdev) explicit decision per `brief.md` §Open questions; (4) the LaTeX comment format (`% original image:` vs some other convention) needs maintainer acceptance. |

---

## §2 Gate summary

| Gate ID | Gating? | Result |
|---------|---------|--------|
| C4-verify | YES | PASS |
| T1-structure | no | FAIL (see §3) |
| T2-shape | no | PASS |
| T3-unit | no | PASS |
| T4-contribution | no | N/A |

Overall mechanical gate result from `check-gates.json`: **pass** (only gating gate is C4; T1 FAIL is non-gating).

---

## §3 NEEDS-HUMAN items (must be cleared before sign-off)

**V-1 — Fitness-to-purpose: print quality**
A human with access to a Gramps installation must generate a tree report with `images = original`, open the resulting PDF, and confirm the embedded image is full-resolution and acceptable for print. The tests verify the *path routing* in LaTeX source, not the rendered output quality.

**V-2 — UI placement and label**
The new `"Images"` option is placed in the node/content options category alongside `"detail"`. A human must open the Tree report dialog and confirm the option label ("Thumbnails (smaller PDF)" / "Original images (full resolution)"), help text, and category placement match the project's UI conventions. The test does not drive the GUI.

**V-3 — Branch target decision**
`brief.md` §Open questions explicitly defers the `maintenance/gramps61` vs `master` branch target to the maintainer (azrdev). This is a policy/scope decision outside the automated gates. A human must record azrdev's explicit response before the PR is marked ready.

**V-4 — T1 gate scope mismatch**
T1 failed with "no .gpr.py" — a check for addon registration that does not apply to a core patch. A human must either (a) confirm the T1 gate is intentionally run on core patches and that a `.gpr.py` is genuinely missing (unlikely), or (b) record that the gate is misapplied and close the T1 FAIL as a false positive. Until resolved it stays open.

---

## §4 Observations (advisory, non-blocking)

- **`%%` formatting in production and test are consistent.** Both `self.write(level + 1, "%% original image: %s\n" % original)` (treedoc.py) and `self.assertIn("%% original image: %s" % self.image_path, tex)` (treedoc_test.py:164) evaluate to `% original image: <path>` — a single-`%` LaTeX comment. No mismatch.
- **`_StubDb` surface is minimal and correct.** Only `get_media_from_handle` is needed; `media_path_full` resolves to an absolute path (setUp writes `self.image_path` as absolute), so the media base-path lookup in `_StubDb` is never reached — the stub comment at treedoc_test.py:76–77 correctly explains this.
- **`po/POTFILES.in`** does not need a new entry (brief.md §Design point 4 is correct: `treedoc.py` is already listed at line 388 of that file, covering the new `_()` strings).
- **Baseline tree drift** (`detached@674e3b`) is a T3 non-gating warning. It indicates the baseline was recorded on a detached HEAD rather than a named branch tip. Low risk for this patch (unit suite still passes), but the testbed operator should re-anchor the baseline to a branch ref when convenient.
