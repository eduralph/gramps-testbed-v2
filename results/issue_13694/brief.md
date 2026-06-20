# Brief — issue 13694 / make-listing-wipes-json

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** make-listing-wipes-json
- **Defect:** Running `make.py <ver> listing <Addon>` against an addon whose .gpr.py
  declares `include_in_listing=False` (or whose .addon.tgz is not yet built) overwrote
  the per-language `addons/<ver>/listings/addons-<lang>.json` files with `[]`, wiping
  every previously-listed addon — what the reporter saw as "the JSON files are all
  corrupt." prculley (note 1) correctly notes `listing` is not meant to unlist, but that
  does not cover the destructive truncation of the whole listing.
- **Success criterion:** A single-addon `listing` that yields no eligible plugin leaves
  the existing listings files untouched (and prints how to remove an entry on purpose with
  `unlist`), instead of writing `[]`; verified by a test on make.py that asserts the file
  is not wiped. This fix already shipped on the target branch — the brief confirms it is
  present; there is no patch.diff to carry, so the bundle is discontinued as superseded by
  the fix, with the commits referenced.
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60
- **Surfaces:** data (build tooling; no GUI).
- **Scope:** confirm the already-merged fix is present and close. / out of scope: any new
  change to make.py; reworking the listing/merge design; the separate `unlist`/`as-needed`
  workflow (by design per note 1).
- **Repro instruction:** In addons-source, with a built listings set, run
  `make.py gramps60 listing <Addon>` where `<Addon>` has `include_in_listing=False`;
  pre-fix the listings JSON files were emptied. Post-fix they are left untouched.
- **Test file:** addons-source `tests/test_make_listing.py` (already shipped with the fix
  commit ca6f0c217) — exercises make.py's listing write path; no new test needed for the
  close.
- **Citations expected:** n/a (no new patch). Fix already present at make.py listing
  write-out (the single-addon guard added by ca6f0c217: when `cmd_arg != "all"` and
  `listings` is empty and the listings file exists, skip the write and `continue`).
- **Prior-art check (triage cycles):** searched by file path make.py — already fixed on
  maintenance/gramps60 by commit ca6f0c217 ("Fix make.py listing wiping addons-<lang>.json
  for excluded addon", Resolves 13694) plus follow-up 1cf301138 ("make.py listing: also
  fix multi-gpr corruption", PR 915 follow-up). Both merged; test_make_listing.py ships
  alongside.
- **Mantis:** 13694
- **Disposition hint:** likely-close

## STOP discipline

Draft only until Check sign-off. No patch.diff to carry — the fix is already merged.
**Recommended sign-off disposition: `discontinue`** (`pdca signoff --discontinue`),
superseded by addons-source commits ca6f0c217 + 1cf301138 (PR 915 + follow-up) — per
INTEGRATION §7 (work superseded by an already-merged change). No new PR.
