# Brief — issue 13418 / latex-report-subscript-strikeout-typeerror

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** latex-report-subscript-strikeout-typeerror
- **Defect:** Generating a LaTeX text report (Complete Individual Report, output LaTeX,
  include notes) for a note carrying subscript + strikeout raises `TypeError: list indices
  must be integers or slices, not str` in `latexdoc.py` `str_incr` (`if lili[i] < "z"` with
  `i` a string), reached via the multicol width path (calc_latex_widths → handle_table →
  end_table).
- **Success criterion:** N/A — close disposition. The defect no longer reproduces on the
  target branch (already fixed); no patch is authored.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** low
- **Scope:** the `str_incr` integer-indexing defect in `plugins/docgen/latexdoc.py`. / out
  of scope: the related but distinct #13417 styled-note KeyError.
- **Repro instruction:** example.gramps, person Garner von Zieliński Lewis Anderson Sr →
  Reports → Text → Complete Individual Report, output LaTeX, include notes, on a note with
  subscript + strikethrough.
- **Test file:** N/A — close disposition (no patch).
- **Mantis:** 13418
- **Disposition hint:** not-reproducible — already fixed upstream on the target branch; the
  defect no longer reproduces. Discontinue.

## STOP discipline

Draft only until Check sign-off.
