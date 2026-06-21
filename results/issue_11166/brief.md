# Brief — issue 11166 / latexdoc-pict-width-float-typeerror

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** latexdoc-pict-width-float-typeerror
- **Defect:** Generating LaTeX output from a report that places an image inside a table —
  e.g. the Complete Individual Report with pictures enabled — crashes with
  `TypeError: sequence item 1: expected str instance, float found`. The LaTeX docgen joins the
  numeric picture width straight into an emitted LaTeX string without converting it to text.
- **Success criterion:** A report containing a picture cell emits its LaTeX picture-size
  command without raising — `LaTeXDoc`'s table/picture emission joins the picture width as a
  string, so the Complete Individual Report (with images, LaTeX output) completes. Demonstrable
  by C4-verify on a docgen test that drives the picture-in-table emission and asserts no
  `TypeError`.
- **Invariant to restore:** The LaTeX docgen converts numeric width values to their string
  form before joining them into emitted LaTeX markup — no non-`str` may reach a `"".join(...)`
  of LaTeX fragments. (Internal docgen rule; a plain type/serialization correctness property,
  not a structural/import-safety category.) SELF-TEST: the bug is one of three sibling
  emission sites being inconsistent, so the property is "every width emission stringifies",
  not "guard this one call".
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Scope:** the picture-width emission in `gramps/plugins/docgen/latexdoc.py`.
  `calc_latex_widths` (`latexdoc.py:829`) joins the raw float `self.pict_width` (the bare value
  at `:849`, inside the `"".join((...))` at `:846-852`) into a LaTeX `\setlength{\grpictsize}`
  string, whereas the two sibling emission sites already stringify it — `repack_row`
  (`latexdoc.py:804`) and the cell emit at `latexdoc.py:1235` both use `repr(self.pict_width)`.
  `pict_width` defaults to `0` (`:703`) and is set numeric at `:1455`. Make the
  `calc_latex_widths` site consistent with its siblings so the value is rendered as text. / out of scope: the separate "two-or-more multicolumns"
  LaTeX crash already fixed upstream (`ed8eaa2782`), and the `IndexError` in `repack_row` seen
  in a different traceback of the report — confirm those are not re-touched; this fix is the
  `pict_width` `TypeError` only.
- **Repro instruction:** On maintenance/gramps61, with `example.gramps`, select "Garner von
  Zielinski", run the Complete Individual Report with "Add Pictures" enabled and Output Format =
  LaTeX → the report fails with the `TypeError` in `calc_latex_widths`. PDF output succeeds.
- **Test file:** gramps/plugins/docgen/test/latexdoc_test.py — extend the existing docgen test
  to drive the **production** `LaTeXDoc` table+picture path (build a table containing a
  `\grmkpicture` cell via the real doc API with a non-zero `pict_width`, run `end_table` /
  `calc_latex_widths`) and assert the emit raises no `TypeError`. It MUST exercise the real
  `LaTeXDoc`, not a hand-rolled emit copy. Adds no new `.py`.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **Prior-art check (triage cycles):** `git log upstream/maintenance/gramps61 --
  gramps/plugins/docgen/latexdoc.py` — the recent `ed8eaa2782` "Fix LaTeX report crash when a
  table has two or more multicolumns" is a *different* crash; the raw-float join at
  `latexdoc.py:849` is still present (verified). Merged history clean for this defect;
  closed-PR search by this path advised.
- **Mantis:** 11166
- **Disposition hint:** likely-fix
