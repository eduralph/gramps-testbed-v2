# Brief — issue 3214 / preformatted-note-fontsize-reset-to-default

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** preformatted-note-fontsize-reset-to-default
- **Defect:** In the Note editor, changing a (preformatted) note's font size away from the
  default (10) and then back to 10 does **not** clear the FONTSIZE style: the buffer removes
  the old FONTSIZE tag and then unconditionally applies a new *explicit* FONTSIZE=10 tag, even
  though 10 is the style default. The note looks fine in the editor, but reports apply that
  explicit size as an absolute override on top of the report's Preformatted paragraph style,
  so the rendered size differs from an unchanged note — and the user cannot get back to the
  original.
- **Success criterion:** Applying a style value equal to its default leaves the text with **no
  explicit tag for that style** — identical to a note whose size was never changed. Demonstrable
  by driving the buffer's style-apply path with FONTSIZE = default and asserting the resulting
  `StyledText` carries no FONTSIZE tag (red pre-fix: a FONTSIZE tag persists; green post-fix: none).
- **Invariant to restore:** Setting a character-style value equal to `StyledTextTagType.STYLE_DEFAULT[style]`
  must leave the selection in the same tagged state as if the style had never been applied — no
  residual absolute override. The buffer's OWN clear path already honours this
  (`clear_selection` only removes a tag when `value != STYLE_DEFAULT[style]`,
  `gramps/gui/widgets/styledtextbuffer.py:521`); the apply path must uphold the same invariant.
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data — the defect is in the `StyledTextBuffer` tag model; the regression test
  drives the production apply method and inspects the resulting `StyledText` tags. No E2E through
  the app is required (a unit test that imports the buffer is sufficient).
- **Difficulty:** low — a localized guard in one method.
- **Scope:** the `int` (and, for consistency, `str`) branch of
  `StyledTextBuffer._apply_style_to_selection` (`gramps/gui/widgets/styledtextbuffer.py:476-483`)
  applies a tag even when `value == StyledTextTagType.STYLE_DEFAULT[style]`; it must skip applying
  an explicit tag for the default value (after removing any prior one), so no override is written.
  / out of scope: the docgen absolute-size handling (correct once no explicit default tag exists);
  the `bool`-style branch; any refactor of the style-state machinery.
- **Repro instruction:** Note editor on a Preformatted note: select text, set Font size to 12, then
  back to 10 — the stored `StyledText` retains a FONTSIZE=10 tag, and a text report renders it at a
  size differing from the Preformatted default. Unit form: exercise the buffer's style-apply path
  with `FONTSIZE = STYLE_DEFAULT[FONTSIZE]` and assert `get_text()` / the retrieved `StyledText`
  has no FONTSIZE tag.
- **Test file:** gramps/gui/widgets/test/styledtextbuffer_test.py — a headless unit test that
  exercises the PRODUCTION method (`_apply_style_to_selection`, via the buffer's public apply path)
  — NOT a parallel copy — and asserts no explicit tag remains after setting the default. Must fail
  pre-fix, pass post-fix.
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** adds `gramps/gui/widgets/test/styledtextbuffer_test.py` (a test, no
  translatable strings) → register in `po/POTFILES.skip`; add its `test/__init__.py` if the dir is new.
- **Prior-art check (triage cycles):** searched `gramps/gui/widgets/styledtextbuffer.py` on
  maintenance/gramps61 — `_apply_style_to_selection` (:476) applies unconditionally; `clear_selection`
  (:502-522) already guards on `value != STYLE_DEFAULT`. Editor combo path at
  `gramps/gui/widgets/styledtexteditor.py:657-663`; docgens apply FONTSIZE absolutely (e.g.
  `latexdoc.py`). No fix in git history.
- **Mantis:** 3214
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a draft PR MAY
happen during the cycle (useful for CI). The PR MUST NOT be marked ready before sign-off accepts.
