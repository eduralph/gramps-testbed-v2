# Brief — issue 13589 / family-sheet-trailing-blank-page

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** family-sheet-trailing-blank-page
- **Defect:** A blank page is appended to the end of the Reports > Textual reports >
  Family Sheet PDF for some users. Reporter (favdb) and confirmer (snoiraud) both saw it
  on Ubuntu 22.04 with PDF output; it does NOT reproduce on Windows (codefarmer, notes
  7/10) nor on Ubuntu 24.04 with current maintenance/gramps61 Family Sheet + example.gramps
  (note 11: five PID/recurse combinations exported as PDF, every last page carried real
  Family Sheet content, no trailing blank page).
- **Success criterion:** Ticket is **CLOSED in the tracker by the maintainer for lack of
  reporter feedback** — the requested retest on a current cairo/Pango stack never came. **No
  implementation.** Two findings stand on record: (1) VERIFIED by reading source — there is
  **no addon-code defect**: the Family Sheet document model emits no trailing page-break or
  trailing empty content (single `page_break()` site, FamilySheet.py:306, before each child
  sheet, never after the last; `write_report` ends at `end_table()`, FamilySheet.py:298).
  (2) The render-stack symptom (only on the reporters' Ubuntu 22.04 cairo/Pango stack) was
  never reproduced or refuted on a current stack — note 11's clean matrix (eduralph) was the
  only non-repro evidence, and the reporter never confirmed. The close stands; reopen only as
  a gramps-core cairo-PDF docgen ticket if a current-stack repro ever surfaces.
- **Repo + branch target:** gramps-project/addons-source @ maintenance/gramps60
- **Surfaces:** data (report document model) — the observable symptom is in cairo PDF
  rendering, downstream of the addon.
- **Scope:** confirm-and-close only — no code change. / out of scope: any change to
  cairo / Pango / poppler (upstream render stack, not this repo) or to gramps-core cairo
  PDF docgen; reopen as a core docgen ticket only if a current-stack repro surfaces.
- **Repro instruction:** On example.gramps, generate Reports > Textual reports > Family
  Sheet with output set to PDF. On the current stack (Ubuntu 24.04, gramps61, libpango
  1.52 / cairo 1.18) no trailing blank page appears (note 11). The defect only manifested
  on the reporters' Ubuntu 22.04 render stack.
- **Test file:** none — confirm-and-close (no code change; the addon's document model is
  not where the blank page originates).
- **Citations expected:** n/a (no patch). Diagnostic citation: FamilySheet.py:306 (the
  sole `self.doc.page_break()` call site — before each child sheet inside the descendant
  loop, never after the last sheet; write_report ends at FamilySheet.py:298 `end_table()`).
- **Prior-art check (triage cycles):** searched by file path FamilySheet.py — `page_break`
  has a single call site (FamilySheet.py:306) emitting no trailing break; no addon-side
  defect on maintenance/gramps60. Note 11's clean five-case PDF matrix on current libs is
  the verification. No open/closed PR addresses an addon-code change for this.
- **Mantis:** 13589
- **Disposition hint:** likely-close
  (Already CLOSED in the tracker by the maintainer for lack of reporter feedback — the
  current-stack retest never came. **Do NOT implement.** Source reading found no addon-code
  defect (FamilySheet.py emits no trailing page-break); the render-stack symptom was never
  confirmed or refuted on a current stack. If a current-stack repro ever surfaces it is a
  gramps-core cairo-PDF docgen ticket, not an addon defect.)

## STOP discipline

Already closed in the tracker (maintainer, no reporter feedback). No implementation, no
patch, no PR — this bundle only records the disposition and routes to sign-off to accept
the close.
