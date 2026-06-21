# Result — issue 6128 / book-report-same-name-styles-collide

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: When a Book Report contains two reports of the same type whose styles differ
- Success criterion: A book with two same-type items that define styles under the same
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the per-item style collation in `gramps/gen/plug/report/_book.py`. Root cause:

## 2. Disposition claimed               ← sign-off confirms or overrides
- Outcome: likely-fix
- Confidence: medium
- Recommendation: (set by Do)

## 3. Correctness (Check — chain)
- C1 Spec: none — brief.md
- C2 Reproduction (red pre-fix): none — (no gate configured)
- C3 Change: none — patch.diff
- C4 fix verified: test red pre-fix, green post-fix: pass — C4-verify: green-with-fix=PASS / red-without-fix=PASS
- C5 Causal adequacy: none — reviewer + human sign-off

## 4. Conformance (Check — stack)
- T1 structure: addon layout vs doc 16 §Structure (folder==id, target_version, fname, no __init__.py): pass — T1 – N/A: no addons-source path in patch.diff (core-only change; §Structure is addon-only)
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 4 file(s) conform to doc 16 §Coding style (32 advisory)
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review — issue 6128 / book-report-same-name-styles-collide

**Reviewer role:** Check (advisory, artifact-only, decorrelated from builder)
**Artifacts read:** `patch.diff`, `brief.md`, `check-gates.json`
**Source grounding:** `patch.diff` only (`$PDCA_TARGET` unset)
**Date:** 2026-06-21

---

## §1 Verdict Table

| Item | Verdict | Basis |
|------|---------|-------|
| C1 — Spec | PASS | `brief.md` specifies defect, success criterion, invariant, scope, and test-file requirements; patch delivers all: `_book.py` fix, new `test/book_styles_test.py` + `test/__init__.py`, `po/POTFILES.skip` entries — all match the brief exactly |
| C2 — Reproduction (red pre-fix) | PASS | `book_styles_test.py:441-453` contains an explicit `ImportError`-fallback path that reproduces pre-fix flat collation (`set_document(doc)` + `append_styles(selected_style, item)` with no prefix); `check-gates.json` C4 path_line confirms "red-without-fix=PASS" (test fails as expected against pre-fix tree) |
| C3 — Change | PASS | Change introduces `book_item_style_prefix` (`_book.py:136-146`), prefixed collation in `append_styles(…, prefix="")` (`_book.py:87-133`), `BookItemStyleProxy` runtime rewriter (`_book.py:149-211`), and `add_book_item_styles` orchestrator (`_book.py:214-229`); applied consistently to both CLI (`cli/plug/__init__.py:19,33`) and GUI (`gui/plug/report/_bookdialog.py:506,522`) call sites; backward compat preserved via `prefix=""` default |
| C4 — Verification (red→green) | PASS | `check-gates.json` C4 result=pass, gating=true; path_line: "green-with-fix=PASS / red-without-fix=PASS" — both legs confirmed by gate engine |
| C5 — Causal adequacy | PASS | Root cause is flat-namespace collision: pre-fix `append_styles` inserted every item's styles into the shared stylesheet keyed by unmodified style name, so a second item's same-named style silently overwrote the first's; fix eliminates this by namespacing each item's styles under a unique prefix and intercepting the item's doc calls via `BookItemStyleProxy` to rewrite references — the mechanism directly eliminates the overwrite |
| T1 — Structure | N/A | Core-only change; T1 (addon §Structure) gate reports N/A: "no addons-source path in patch.diff" (`check-gates.json` T1 path_line); addon layout rules do not apply |
| T2 — Shape | PASS | Gate result=pass for both T2-shape ("4 file(s) conform") and T2-potfiles (gating=true, result=pass); `po/POTFILES.skip` updated with both new test files (`patch.diff:541-542`); GPL header present on `book_styles_test.py` (`patch.diff:239-256`) |
| T3 — Runtime | PASS | Gate result=pass; baseline matched at 7 known failures; ⚠ path_line notes "baseline tree drift: recorded detached@674e3b" — baseline not pinned to the exact patch tip, but baseline match is confirmed by gate |
| T4 — Contribution | N/A | Gate reports N/A: "no commit-msg.txt or pr-description.md in the bundle" (`check-gates.json` T4 path_line); gating=false; nothing to evaluate |
| T5 — Judgment | NEEDS-HUMAN | `BookItemStyleProxy` overrides 10 named style-bearing methods plus `__getattr__` delegation; completeness against the full `BaseDoc`/`TextDoc`/`DrawDoc` API cannot be confirmed without source access — any unoverridden method that accepts a style-name argument silently bypasses the per-item prefix at render time; `write_note` is a suspected gap (see §6 item 1) |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Test invariant ("each item keeps its own style values") is verified for the reported case and generalized to 3 items with an arbitrary style name; real-world fitness across all document backends and the live Style Editor workflow requires human sign-off (see §6 item 2) |

---

## §2 Spec (C1)

`brief.md` is complete and self-consistent. The defect, invariant, success criterion, scope boundary ("out of scope: Style Editor UI; non-book single reports; document backends"), test-file location, `po/POTFILES.skip` requirement, and prior-art check instruction are all stated explicitly.

The patch satisfies every brief requirement I can verify against `patch.diff`:

- Fix is in `gramps/gen/plug/report/_book.py` ✓
- Both `gramps/gen/plug/report/test/__init__.py` and `gramps/gen/plug/report/test/book_styles_test.py` are new ✓
- Both registered in `po/POTFILES.skip` ✓
- Test exercises the real collation path (`append_styles` and `add_book_item_styles` imported from production module, not reimplemented) ✓
- Self-test invariant ("property is over *any* pair of items sharing a style name"): `test_generalizes_beyond_two_items_and_dr_title` covers an arbitrary style name ("AB-Heading") across three items ✓

---

## §3 Reproduction (C2)

The test file encodes pre-fix production behaviour in `_render_each_item` (`book_styles_test.py:441-453`):

```python
try:
    from gramps.gen.plug.report._book import add_book_item_styles
except ImportError:
    add_book_item_styles = None
…
if add_book_item_styles is None:
    item.option_class.set_document(doc)
    append_styles(selected_style, item)   # no prefix → flat collation
else:
    add_book_item_styles(selected_style, item, doc, item_number)
```

On a pre-fix tree `add_book_item_styles` is not importable; the fallback executes `append_styles(selected_style, item)` with no prefix — identical to the pre-fix production call in `cl_book`. The shared stylesheet ends up with a single "DR-Title" entry (the second item's value wins). The assertion `assertEqual(sizes, [14, 48])` then fails with `[48, 48]`. This is the correct red signal for the reported bug.

The C4 gate confirms the red leg ran and produced the expected failure ("red-without-fix=PASS").

Note: the pre-fix simulation relies on `ImportError` from the production module, not from a separate stub — so it is tied to the actual production symbol, not a parallel re-implementation. That satisfies the brief's "MUST exercise the real book collation" requirement for the red leg.

---

## §4 Change (C3)

### 4.1 Algorithm

`append_styles` is refactored to accept a `prefix` parameter (default `""`). Every style inserted into the shared `selected_style` is stored under `prefix + this_style_name` instead of the bare name. With `prefix=""` the old behaviour is preserved for any existing callers.

`book_item_style_prefix(item_number)` returns `"BI%03d-" % item_number`, giving unique prefixes `"BI000-"`, `"BI001-"`, … up to 999 items. The character set (upper-case letters, digits, hyphen) is the same as existing style names, so it survives every document backend's style-name handling.

### 4.2 Proxy

`BookItemStyleProxy` wraps the shared document and prepends `self._prefix` to the style-name argument in every intercepted method. `get_style_sheet()` returns the item's own un-prefixed stylesheet so report code that reads styles back by original name keeps working. `__getattr__` delegates everything else to the real document unchanged.

### 4.3 Orchestration

`add_book_item_styles` combines `book_item_style_prefix` + `append_styles` + `BookItemStyleProxy` construction + `item.option_class.set_document(proxy)` in one call. The comment at both call sites (`cli/plug/__init__.py:28-32`, `_bookdialog.py:517-521`) correctly states the ordering constraint: the proxy must be installed before the report object is constructed (because the report reads its document at construction via `item.option_class.get_document()`).

### 4.4 Call site parity

Both CLI (`cl_book`) and GUI (`BookDialog.make_report`) are updated identically: `enumerate`, `add_book_item_styles` before `get_write_item()`, `rptlist.append(obj)` unconditional. The removed `if obj:` guard in the CLI path was always True (a tuple is always truthy in Python) — removing it is correct.

### 4.5 Concern noted for T5

The proxy overrides 10 named-style methods. The `__getattr__` fallback passes all other attributes/calls to the real document without prefix injection. If any method in the concrete `BaseDoc`/`TextDoc`/`DrawDoc` interface accepts a style-name argument and is not listed in the proxy, those calls silently bypass the prefix. Cannot verify completeness without source access.

---

## §5 Verification (C4)

Gate result: `"green-with-fix=PASS / red-without-fix=PASS"`, gating=true, result=pass.

The two test methods cover:
1. `test_two_same_type_items_keep_distinct_title_sizes` — the exact reported case: "DR-Title", 14pt vs 48pt, asserts `[14, 48]`
2. `test_generalizes_beyond_two_items_and_dr_title` — "AB-Heading", 10/20/30pt, three items, asserts `[10, 20, 30]`

Both tests drive the production collation code (`add_book_item_styles` → `append_styles` → `BookItemStyleProxy`) and resolve styles through `_RecordingTextDoc`, which mirrors the real backend resolution: `get_style_sheet().get_paragraph_style(style_name)`.

The C4 gate ran both the pre-fix (ImportError fallback) and post-fix legs and observed the expected red→green transition.

T3 baseline note: gate reports "baseline tree drift: recorded detached@674e3b". The baseline was recorded on a commit that may not be identical to the patch tip. However, the gate reported "matches recorded baseline: 7 known test red(s)", so no new failures were introduced. Minor concern, not a blocker.

---

## §6 Human Must Clear

Two NEEDS-HUMAN items require human sign-off before this patch can be accepted:

### 6.1 T5 — `BookItemStyleProxy` method completeness

**Item:** `BookItemStyleProxy` overrides 10 style-name-bearing methods: `start_paragraph`, `start_table`, `start_cell`, `add_media`, `draw_path`, `draw_box`, `draw_text`, `center_text`, `rotate_text`, `draw_line`. Every other attribute/call goes through `__getattr__` without prefix injection.

**Action required:** Open `gramps/gen/plug/docgen/basedoc.py` (and `textdoc.py`, `drawdoc.py` if separate) on `maintenance/gramps61` and enumerate every method that accepts a style-name argument. Confirm each is overridden in `BookItemStyleProxy`. Pay particular attention to:
- `write_note` — in some Gramps versions this accepts a paragraph-style name; if so, it is a gap.
- Any method added in the 6.1 cycle not yet in the 5.x base interface.

**Risk if uncleared:** At render time, a report that calls an unintercepted style-name method will pass the un-prefixed name to the shared document, which holds only prefixed names; the style lookup returns `None` or a default, producing incorrect rendering that the tests do not catch.

### 6.2 V — Real-world backend and workflow validation

**Item:** The test uses `_RecordingTextDoc`, a minimal stub that mimics the `get_style_sheet().get_paragraph_style()` resolution path of real backends. It does not exercise concrete backends (AsciiDoc, Cairo/PDF, ODT, HTML).

**Action required:** Perform the repro from `brief.md` on the post-fix tree with a real document backend (PDF is the reported medium): two text Descendant Reports, title style 14pt for item 1 and 48pt for item 2; generate and inspect that item 1's title is 14pt and item 2's is 48pt. Also confirm the Style Editor workflow (custom named stylesheets) is unaffected — that `get_item_style_sheet` still reads the user's selected stylesheet correctly.

**Risk if uncleared:** A concrete backend may override `set_style_sheet`/`get_style_sheet` in a way the proxy does not account for, or may have additional style-name-bearing methods outside the abstract interface, leaving a rendering regression invisible to the unit suite.

---

## §7 Overall

Both NEEDS-HUMAN items (§6.1 and §6.2) must be cleared before the patch is accepted. All gating checks passed. The algorithmic approach (namespacing + transparent proxy) is correct and the fix is causally adequate. No blocking issues were found in the elements this reviewer can assess from `patch.diff` alone.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [ ] T5 — Judgment — `BookItemStyleProxy` overrides 10 named style-bearing methods plus `__getattr__` delegation; completeness against the full `BaseDoc`/`TextDoc`/`DrawDoc` API cannot be confirmed without source access — any unoverridden method that accepts a style-name argument silently bypasses the per-item prefix at render time; `write_note` is a suspected gap (see §6 item 1)
- [ ] V — Validation — fitness-to-purpose — Test invariant ("each item keeps its own style values") is verified for the reported case and generalized to 3 items with an arbitrary style name; real-world fitness across all document backends and the live Style Editor workflow requires human sign-off (see §6 item 2)

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: iterated-to-Do
- Iteration delta (if iterating): BookItemStyleProxy is incomplete: write_styled_note(styledtext, format, style_name) in TextDoc is not overridden, so any book-eligible report that calls it (Detailed Descendant, Family Group, Complete Individual, Detailed Ancestral — all REPORT_MODE_BKI) passes the un-prefixed style name to the shared document, which holds only prefixed names and falls back to defaults. Add write_styled_note to the proxy's overridden methods (prefix the style_name argument before delegating), and audit draw-report equivalents for any further style-name-bearing methods not yet covered.
- By / date: Eduard Ralph / 2026-06-21

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
