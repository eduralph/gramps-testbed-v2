# Brief — issue 6250 / libcairodoc-pango-get-iterator-attr-reindex

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

- **Slug:** libcairodoc-pango-get-iterator-attr-reindex
- **Defect:** When `GtkDocParagraph.divide` splits a styled paragraph across a page
  break, it re-indexes the second part's Pango attributes with a 2012 workaround
  (`gramps/plugins/lib/libcairodoc.py:685-714`) added when `get_iterator` was not yet
  introspectable (bug 6208 / gnome 646788). `get_iterator` is now available on every
  supported GI stack (verified in this bundle's iteration-v1 `verification-finding.md`:
  Pango 1.52.1 CI image, 1.57.0 host). The workaround is not only obsolete but **wrong**:
  it rebuilds the second part's attribute list by walking the *markup* string and counting
  bytes, treating an escaped entity (`&amp;`/`&lt;`/`&gt;`) as multiple plaintext bytes.
  Any paragraph whose plaintext contains `&`, `<`, or `>` before the split point desyncs
  the byte cursor, so the second part's style runs (bold/italic/font/colour) land on the
  wrong characters or are dropped (verified: markup `"A &amp; B <b>BOLD</b> tail"` split at
  `BOLD` reconstructs the wrong fragment `'; B <b>BOLD</b> tail'`).
- **Success criterion:** On `maintenance/gramps61`, when `GtkDocParagraph.divide` splits a
  styled paragraph at plaintext byte offset `index`, the second part's `Pango.AttrList`
  carries each surviving style run rebased to the second part's plaintext byte offsets —
  correct **even when the paragraph's plaintext contains an escaped markup character
  (`&`/`<`/`>`) before the split point**. A regression test builds such a paragraph, drives
  the production split/re-index code, and asserts the second part's run (attribute type +
  `start_index`/`end_index`); it is RED against the current markup-reparse workaround and
  GREEN once the `get_iterator`-based re-indexing replaces it. Demonstrable by C4-verify
  (patch applied in isolation) — do not lean on a whole-suite T3 pass.
- **Invariant to restore:** Splitting a paragraph at plaintext byte offset `index` must
  preserve every style run — the second part's attribute list applies the same attributes to
  the same characters as the original paragraph applied over `plaintext[index:]`, with each
  run's offsets rebased to the second part's text (a run straddling the split clamps its start
  to 0). This must hold for ALL paragraph content, including plaintext that contains characters
  which are escaped in Pango markup (`&`, `<`, `>`), because attribute offsets are defined as
  byte indices into the **parsed plaintext** (Pango `PangoAttribute.start_index`/`end_index`
  contract), independent of how the source markup was serialised. This is the property only —
  the HOW (re-index the parsed attribute list via the now-available iteration approach rather
  than re-serialising markup) is the ticket's reintroduction and lives in Scope, not here.
  SELF-TEST (could Do satisfy this by guarding a single module? — no: it is a correctness
  property of the split output, not an import guard).
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data
- **Difficulty:** medium — blast radius is one method in one file, but `divide()` feeds the
  pagination of styled paragraphs in **every** cairo-rendered report (PDF/PS/etc.), so the
  reviewer must hold behavioural-equivalence across that output surface in view and confirm
  the new red→green; the testable-seam extraction also adds one in-file call site. Single-file
  reach but non-trivial behavioural propagation → rated up from low.
- **Scope:** Replace the obsolete markup-reparse workaround in `GtkDocParagraph.divide`
  (`gramps/plugins/lib/libcairodoc.py:685-714`, the `## START OF WORKAROUND … ##END OF
  WORKAROUND` block) with attribute re-indexing computed from the already-parsed,
  already-`filter`ed `Pango.AttrList` — the algorithm preserved in the `## OLD EASY CODE`
  comment at :674-684 — so the split second part's runs derive from the parsed attrlist's
  plaintext byte offsets. The OLD EASY CODE comment is a starting point, not gospel: Do must
  confirm the reintroduced loop is itself correct against the invariant (its `while
  oldattrlist.next():` ordering advances before reading the first segment, and `end_index -=
  index` is unguarded) and that it passes the test, rather than pasting it verbatim. The
  `get_iterator` availability is settled (iteration-v1 `verification-finding.md`) — do NOT add
  a `hasattr`/`try` capability fallback. / out of scope: the other `divide()` overloads in the
  file (GtkDocTable / Image / …), the marklist split, `draw()`, the split-point computation
  (`splitline`/`index`/`layout_line.start_index`), any other docgen backend, and behaviour for
  paragraphs that do not split.
- **Repro instruction:** On `maintenance/gramps61`: build a `GtkDocParagraph` whose markup
  text is `"A &amp; B <b>BOLD</b> tail"` (plaintext `A & B BOLD tail`; the bold run covers
  plaintext bytes 6–10) and drive the production paragraph split at the byte offset of `BOLD`
  (index 6). Inspect the second `GtkDocParagraph`'s attribute list. Current code: the bold run
  is misplaced/corrupted because the workaround walks the *markup* string and counts `&amp;`
  as 4 plaintext bytes, desyncing the cursor (verified: it reconstructs `'; B <b>BOLD</b>
  tail'`). Expected: a single weight=bold run over the second part's bytes 0–4 (`BOLD`).
- **Test file:** `gramps/plugins/lib/test/libcairodoc_test.py` (new; with a new
  `gramps/plugins/lib/test/__init__.py`). The test MUST exercise the PRODUCTION re-index path:
  extract the re-indexing into an importable unit that `divide()` itself calls (the testable
  seam), and have the test import and drive **that same unit** — following the existing
  `gramps/plugins/docgen/test/latexdoc_test.py` → `str_incr` pattern — NOT a copy of the loop
  pasted into the test (principles §3.4). Operate on a `Pango.AttrList` from `Pango.parse_markup`
  so the test stays headless (no display / cairo surface needed). Red pre-fix, green post-fix.
- **Citations expected:** Do must cite path:line on `maintenance/gramps61` for every change:
  the second-part plaintext + filter setup (`gramps/plugins/lib/libcairodoc.py:664-667`), the
  `## GTK3 PROBLEM` / `## OLD EASY CODE` comments (:669, :674-684), the removed workaround block
  (:685-714), `filterattr` (:734), and `__set_attrlist` (:536).
- **New/removed files:** adds `gramps/plugins/lib/test/__init__.py` and
  `gramps/plugins/lib/test/libcairodoc_test.py` — both have no translatable strings (tests), so
  register both in `po/POTFILES.skip` under a new `# plugins/lib/test directory` section
  (mirror the existing `# plugins/docgen/test directory` entries at POTFILES.skip:557-558). No
  `.py` is removed (the workaround is deleted in place, not a whole file). `T2-potfiles` checks
  this.
- **Prior-art check (triage cycles):** searched by path `gramps/plugins/lib/libcairodoc.py` on
  `upstream/maintenance/gramps61` — the workaround block (:669-714) and the `## OLD EASY CODE`
  comment are still present; no reintroduction commit in merged history; no open/closed PR for
  it. THIS bundle's iteration-v1 confirmed `get_iterator` availability (`verification-finding.md`,
  `pango-availability-probe.py`) but deliberately shipped no code change, deferring the
  reintroduction to this cycle. → actionable now.
- **Mantis:** 6250
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI feedback). The PR MUST NOT be
marked ready before sign-off accepts.
