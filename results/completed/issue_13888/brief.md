# Design proposal — issue 13888 / treedoc-image-source-option

> The Plan artifact (a GEPS-style design proposal: this enhancement reverses a deliberate
> maintainer decision (core commit 7335883f68 / "PR 1620") and changes tree-report UX, so
> it needs design buy-in). Do reads ONLY this file and implements it; Check runs the
> regular gated check on the code.

- **Slug:** treedoc-image-source-option
- **Kind:** enhancement (design proposal)
- **Goal:** Give the genealogytree (Tree) reports a user-selectable **image source** so the
  generated LaTeX/PDF can embed either the cached thumbnail (current default) or the
  **original full-resolution image** the report used before PR 1620 — and, when a thumbnail
  is used, annotate the node with the original filename as a LaTeX comment so the `.tex`
  stays identifiable/portable.
- **Success criterion:** With the new report option set to **Original images**, a generated
  tree `.tex` emits `image = {<original media path>}` (the pre-PR-1620 path); set to
  **Thumbnails** (the unchanged default) it emits the cached thumbnail path AND a
  `% original image: <path>` LaTeX comment naming the source file. The shipped test drives
  the production `write_node` path and asserts both branches.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61 (core — the image
  emission is in core `gramps/gen/plug/docgen/treedoc.py`, not the GenealogyTree addon; this
  restores prior behaviour as an opt-in — see Open questions re master)
- **Scope:** add the option + the two emission branches + the filename comment in core
  `treedoc.py` (`TreeOptions` menu, `TreeDocBase.__init__`, `write_node`). / out of scope:
  changing thumbnail size/quality in the thumbnailer plugins (`gnomethumb.py` /
  `imagethumb.py` / `gen/const.py` — azrdev's option 2, a separate broader core change); a
  crop facility (option 3); any GenealogyTree addon change (the addon only assembles the
  tree; core emits the `image = {...}`).
- **Test file:** `gramps/gen/plug/docgen/test/treedoc_test.py` (new — core `test/` package +
  `*_test.py` suffix convention, alongside the existing `graphdoc_test.py`; register the new
  file in `po/POTFILES.skip`, a test with no translatable strings). It MUST exercise the
  production `write_node` image-source branch (instantiate a concrete `TreeDocBase` subclass
  with a stub db/media + a menu carrying the option), NOT a parallel copy of the emission
  logic.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **Mantis:** 13888
- **Disposition hint:** new-feature

## Motivation

The genealogytree LaTeX/PDF tree reports embed only **cached thumbnails** since PR 1620
(core commit 7335883f68, azrdev): low quality (the reporter measured 3–12 kB thumbnails vs
500 kB–2 MB originals) and machine-tied hash filenames that make the `.tex` non-standalone
and unidentifiable (notes 1–4). PR 1620's rationale is real — original images produced
unreasonably huge PDFs with tiny faces, and special characters (comma/space) in original
paths broke the LaTeX parser (azrdev cites commits 75921ce / 2da93aa). But users who
**print** these reports need the original resolution back, and azrdev himself (note 5)
asked to *reconcile both requirements* rather than revert. This proposal does exactly that:
keep thumbnails as the safe default, add an opt-in for originals, and restore
identifiability for the thumbnail case.

## Design

Touch one file: `gramps/gen/plug/docgen/treedoc.py`.

1. **Option** — in `TreeOptions.__init__` add an `EnumeratedListOption` named `"images"`
   (label e.g. _("Images")), placed in the node/content options category alongside
   `detail` (the "Node detail" option). Items:
   - `"thumbnail"` → _("Thumbnails (smaller PDF)") — **default**, preserves PR 1620.
   - `"original"` → _("Original images (full resolution)").
   `set_help(...)` explaining the size/standalone trade-off. `menu.add_option(category,
   "images", images)`.
2. **Read it** — in `TreeDocBase.__init__` add
   `self.images = get_option("images").get_value()` (next to `self.detail`, …).
3. **Emit it** — in `write_node` (currently lines 593–604, the
   `for mediaref in person.get_media_list():` block), keep the
   `media.get_mime_type().startswith("image")` guard, the `os.path.isfile(path)` check, the
   `win()` backslash fix, and `break  # first image only`, and branch on `self.images`:
   - `"original"` → `path = media_path_full(db, media.get_path())` — the **pre-PR-1620
     emission** (verbatim from core commit 7335883f68's removed lines), then
     `image = {path}`.
   - `"thumbnail"` → `path = get_thumbnail_path(media_path_full(db, media.get_path()),
     rectangle=mediaref.get_rectangle())` (current), emit `image = {path}`, and additionally
     write a comment line `%% original image: <media_path_full(...)>` (azrdev's endorsed
     option 4) so the source file stays recorded in the `.tex`.
   `get_thumbnail_path` is already imported locally at the top of `write_node`;
   `media_path_full` (line 43), `win` (line 46) and `os` are already imported.
4. **POTFILES** — `treedoc.py` is already in `po/POTFILES.in` (line 388), so the new
   option's `_()` strings are covered with no POTFILES.in change; add the new
   `gramps/gen/plug/docgen/test/treedoc_test.py` to `po/POTFILES.skip` (the `T2-potfiles`
   gate checks this).

## Alternatives considered

- **Revert PR 1620 entirely** — regresses the users PR 1620 helped (huge PDFs, broken LaTeX
  on special-char paths). Rejected; azrdev's rationale stands and the default must not change.
- **Larger/higher-quality thumbnails** (make the 96×96 / 180×180 bounding box in
  `gnomethumb.py` / `imagethumb.py` / `gen/const.py` configurable, request ~256/512 px) —
  azrdev's option 2. Worth doing but it is a different subsystem affecting *every* thumbnail
  consumer, so it is a separate change, not coupled here.
- **Put the original filename in the thumbnail's filename** instead of a comment — azrdev
  notes this re-breaks LaTeX syntax (the very hazard PR 1620 avoided). A `%` comment is safe.

## Impact & compatibility

- **Default unchanged** (`thumbnail`): existing users and saved report settings see
  identical output; the option defaults to today's behaviour. Only opt-in `original`
  restores the pre-1620 emission.
- The thumbnail node now also carries a `%% original image: …` comment — inert to LaTeX,
  purely informational.
- `original` makes the `.tex` standalone again but inherits the **special-character path
  limitation** (comma/space) PR 1620 documented — this is the stated reason thumbnail stays
  default; see Open questions.
- New translatable strings (the option label/help) — covered by `treedoc.py` already being
  in `POTFILES.in`.

## Open questions

- **Branch target:** proposed `maintenance/gramps61` (restores prior behaviour → closer to a
  regression fix than a brand-new feature, reaches released users sooner, and is the line the
  testbed validates core against). If the maintainer classes a new report option as
  feature-only, §2 sends features to `master`; defer to azrdev / the maintainer's explicit
  base-branch request (§2 override).
- **`original` path safety:** emit verbatim (matches pre-1620) and document the comma/space
  limitation, or detect a hazardous path and fall back to the thumbnail with a logged
  warning? Proposed: emit as-is + document; revisit only if it bites.
- **Granularity:** thumbnail / original only, or also add `"none"` (omit images)? Proposed:
  thumbnail / original; add `none` only if requested.

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a draft PR
MAY happen during the cycle (CI feedback). The PR MUST NOT be marked ready before sign-off
accepts; the maintainer (azrdev) buy-in on the default and branch target is part of that.
