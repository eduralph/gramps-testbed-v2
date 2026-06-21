# Check Review — issue 6128 / book-report-same-name-styles-collide

**Reviewer role:** Check (advisory, artifact-only, decorrelated from builder)
**Artifacts read:** brief.md, check-gates.json, patch.diff
**Deliberately withheld:** build-notes.md
**Target grounding:** `$PDCA_TARGET` is unset — all path:line citations are against patch.diff only

---

## §1 Defect & Fix Summary (re-derived)

The shared stylesheet in a Book Report is built by iterating over each book item and
calling `append_styles`, which writes each item's styles into a flat `StyleSheet` keyed
by the bare style name (e.g. `"DR-Title"`). When two items of the same report type
contribute a style under the same name the second write silently overwrites the first, so
both items then resolve that name to the last-written values.

The fix introduces a per-item namespace prefix (`"BI000-"`, `"BI001-"`, …) so each item's
styles land under a distinct key in the shared stylesheet. A new `BookItemStyleProxy`
wraps the shared document and rewrites each item's style-name references at call time to
the matching prefixed name, so the report code sees no interface change.

---

## §2 Verdict Table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — Spec | PASS | Patch scope matches brief exactly: CLI call-site (`cli/plug/__init__.py` line 877–891 in diff context) and GUI call-site (`_bookdialog.py` lines 1030–1076 in diff context) are both updated; iteration-1 carry-forward (`write_styled_note`) is addressed in `BookItemStyleProxy` (`_book.py` +229–233 in diff) |
| C2 — Reproduction (red pre-fix) | PASS | `_collate` in `book_styles_test.py` (diff lines 516–546) explicitly reproduces the pre-fix flat-collation path via `ImportError` branch; C4-verify gate records "red-without-fix=PASS" (`check-gates.json` line 37) |
| C3 — Change | PASS | `_book.py` changes are coherent and minimal — old `append_styles` body extracted to `get_item_style_sheet` + `_add_namespaced_styles`, new public API (`book_item_style_prefix`, `BookItemStyleProxy`, `add_book_item_styles`) added; `__init__.py` re-exports preserve backward compatibility for `append_styles`; both call-sites converted; `POTFILES.skip` updated |
| C4 — Verification (red→green) | PASS | Automated C4-verify gate: "green-with-fix=PASS / red-without-fix=PASS" (`check-gates.json` line 37, gating=true); test assertions (`test_two_same_type_items_keep_distinct_title_sizes` expecting `[14, 48]`) are correctly formed to detect the collision on the red leg |
| C5 — Causal adequacy | NEEDS-HUMAN | The prefix+proxy mechanism correctly targets the root cause (flat-namespace collision); BUT `BookItemStyleProxy.__getattr__` silently passes any un-overridden method call through to the shared document without prefixing — if any style-name-bearing method in the production `TextDoc`/`DrawDoc` interfaces is absent from the proxy's explicit override list, that call-path retains the collision; the complete TextDoc/DrawDoc API is not in the diff and cannot be audited here |
| T1 — Structure | N/A | Core-only change; §Structure addon-layout rules do not apply — confirmed by gate (`check-gates.json` line 55: "N/A: no addons-source path in patch.diff") |
| T2 — Shape | PASS | T2-shape gate: 4 files conform to §Coding style, 32 print() advisories (pre-existing, none in new code) (`check-gates.json` line 64); T2-potfiles gate (gating=true): new `test/__init__.py` and `test/book_styles_test.py` registered in `po/POTFILES.skip` (diff `POTFILES.skip` +688–689); GPL header present on new test file (diff `book_styles_test.py` lines 1–16) |
| T3 — Runtime | PASS | T3-baseline gate matches recorded baseline: 7 known test reds, no new failures (`check-gates.json` line 83); ⚠ tree-drift warning ("recorded detached@674e3b") noted — gate passed but baseline commit may not match current HEAD |
| T4 — Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in bundle (`check-gates.json` line 92: "N/A: no commit-msg.txt or pr-description.md") |
| T5 — Judgment | NEEDS-HUMAN | Proxy override list covers the methods enumerated in the docstring (`start_paragraph`, `start_table`, `start_cell`, `write_styled_note`, `add_media`, `draw_path`, `draw_box`, `draw_text`, `center_text`, `rotate_text`, `draw_line`); whether this list is *exhaustive* against the actual abstract interfaces (`gramps/gen/plug/docgen/textdoc.py`, `drawdoc.py`) cannot be confirmed from the diff; any gap is a silent regression path via `__getattr__` |
| V — Validation | NEEDS-HUMAN | No live book render artifact (PDF/ODF) against the Mantis 6128 repro is in the bundle; backend style-name handling of the `"BI000-"` prefix (ODF, HTML, ASCII, SVG, Cairo) needs human confirmation; single-report (non-book) rendering regression should be spot-checked |

---

## §3 Call-site Audit

Two call-sites in the pre-fix code assign `item.option_class.set_document(doc)` and then
call `append_styles(selected_style, item)`. Both are updated in this patch:

| Call-site | Pre-fix | Post-fix |
|-----------|---------|----------|
| `gramps/cli/plug/__init__.py` (cl_book) | `set_document(doc)` then `append_styles(…)` | `add_book_item_styles(selected_style, item, doc, item_number)` before report construction |
| `gramps/gui/plug/report/_bookdialog.py` (BookDialog.run) | same pattern | same pattern |

Both now call `add_book_item_styles` *before* `get_write_item` / `write_book_item`, which
is required because reports grab their document from `option_class.get_document()` at
construction. Order is correct in both sites.

---

## §4 Proxy Override Assessment

`BookItemStyleProxy` explicitly overrides the following style-name-bearing methods:

**TextDoc:**
- `start_paragraph(style_name, …)` — prefixed
- `start_table(name, style_name)` — `style_name` prefixed
- `start_cell(style_name, …)` — prefixed
- `write_styled_note(…, style_name, …)` — prefixed *(iteration-1 carry-forward item: addressed)*
- `add_media(…, style_name=None, …)` — prefixed when not None

**DrawDoc:**
- `draw_path(style, …)` — prefixed
- `draw_box(style, …)` — prefixed
- `draw_text(style, …)` — prefixed
- `center_text(style, …)` — prefixed
- `rotate_text(style, …)` — prefixed
- `draw_line(style, …)` — prefixed

**Stylesheet lifecycle:**
- `get_style_sheet()` — returns item's own un-prefixed sheet copy
- `set_style_sheet(sheet)` — mirrors changes into the shared document under prefix, never replaces

`__getattr__` is a fallback for all other attributes and methods. If any style-name-bearing
method of the real `TextDoc` or `DrawDoc` abstract interface is absent from this list, it
passes through un-prefixed silently. This cannot be ruled out from patch.diff alone.

---

## §5 Test Quality

Five tests in `BookStyleCollationTest` cover:

1. `test_two_same_type_items_keep_distinct_title_sizes` — the reported Mantis 6128 repro
   (two DR-Title paragraph styles, 14pt vs 48pt)
2. `test_write_styled_note_keeps_per_item_style` — the iteration-1 carry-forward method
3. `test_draw_box_embedded_paragraph_ref_stays_per_item` — draw-style embedded paragraph
   reference namespacing (the extra fix in `_add_namespaced_styles`)
4. `test_runtime_set_style_sheet_is_per_item` — the run-time compute pattern
   (AncestorTree/DescendTree/FanChart)
5. `test_generalizes_beyond_two_items_and_dr_title` — three items, arbitrary style name
   (brief's SELF-TEST requirement)

All five tests drive the production `add_book_item_styles` path via `_collate`. The
dual-mode `ImportError` branch in `_collate` correctly reproduces the pre-fix collision for
the C4 red leg.

One minor observation: the test file imports `append_styles` at module level (diff
`book_styles_test.py` line 353) with a comment noting it "exists on both trees"; it also
imports `add_book_item_styles` inside `_collate` with a try/except. This means the test
module will import successfully pre-fix, and the fallback path runs correctly.

---

## §6 Items Requiring Human Clearance

Each NEEDS-HUMAN verdict above becomes a mandatory human clearance item before sign-off:

**§6.1 (from C5) — Proxy coverage completeness:**
Read `gramps/gen/plug/docgen/textdoc.py` and `gramps/gen/plug/docgen/drawdoc.py` in the
target branch and compare every abstract method that accepts a style name (paragraph,
table, cell, draw, or any other style kind) against the explicit override list in
`BookItemStyleProxy` (`_book.py` post-fix). For each match, confirm the proxy prefixes the
right argument. For any method absent from the proxy, determine whether it can be called by
a `REPORT_MODE_BKI` report; if so, add an override.

**§6.2 (from T5) — Judgment on completeness claim:**
The proxy docstring asserts it "overrides every style-name-bearing method of the abstract
`TextDoc` and `DrawDoc` interfaces." This claim must be verified against the actual
interface source (not the diff). Confirm or correct. Any gap found in §6.1 is also a T5
failure.

**§6.3 (from V) — Live render validation:**
Reproduce the Mantis 6128 scenario:
- Build a Book Report with two same-type text reports (e.g. two Descendant Reports)
- Configure item-1 title at 14pt, item-2 title at 48pt via the Style Editor
- Generate to PDF (and optionally ODF)
- Confirm item-1 renders at 14pt and item-2 renders at 48pt
- Confirm a single-item book (non-colliding case) renders unchanged
- Optionally spot-check that `"BI000-"` style prefixes do not surface as visible
  artefacts in any backend's output (e.g. ODF style names in the XML, HTML class
  attributes)

---

## §7 Reviewer Verdict

**Automated gates:** All gating gates PASSED (C4-verify, T2-potfiles).

**Check reviewer verdict:**
- C1 C2 C3 C4 T1 T2 T3 T4: **PASS**
- C5 T5 V: **NEEDS-HUMAN** (§6.1–6.3 above must be cleared before sign-off)

The mechanism is sound and the test coverage is strong. The single unresolved risk is proxy
coverage completeness — a structural property of the fix that requires reading the
production abstract interfaces, which are outside the artifact bundle. If §6.1 confirms the
override list is exhaustive, C5 and T5 can be upgraded to PASS and V can proceed to live
render validation (§6.3) as the remaining gate.
