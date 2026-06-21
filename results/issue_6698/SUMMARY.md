# Result — issue 6698 / xml-export-strips-media-path-whitespace

## 1. Spec (from brief.md)              ← Check verifies against THIS
- Defect / goal: A media object whose stored path has leading (or trailing) whitespace —
- Success criterion: A media object whose path begins with a space survives a Gramps-XML
- Repo + branch target: gramps-project/gramps @ maintenance/gramps61
- Scope (one logical fix) / out of scope: the Gramps-XML media-path serialization that alters the path. Root cause:

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
- T2 shape: code shape vs doc 16 §Coding style (GPL header on touched files; print() advisory for reviewer): pass — T2 ✓ shape: 2 file(s) conform to doc 16 §Coding style
- T2 potfiles: new/removed core .py registered in po/POTFILES.in|.skip (doc 16 §Adding and removing Python files): pass — T2 ✓ potfiles: new/removed core .py registered (doc 16 §Adding and removing Python files)
- T3 runtime: gramps core unit suite (whole-suite baseline): pass — T3-baseline [baseline]: matches recorded baseline: 7 known test red(s) | ⚠ baseline tree drift: recorded detached@674e3b
- T4 contribution: commit/PR wrapper vs doc 16 §Commit messages + §Contributor workflow: pass — T4 – N/A: no commit-msg.txt or pr-description.md in the bundle
- T5 Judgment: none — reviewer + human sign-off
- T5 judgment: → see §5.

## 5. Advisory review (artifact-only, decorrelated)
Reviewer ran without build-notes.md. Summary:

# Check Review — issue 6698 / xml-export-strips-media-path-whitespace

- **Reviewer role:** Check (advisory, decorrelated from builder)
- **Artifacts read:** `brief.md`, `check-gates.json`, `patch.diff`
- **Artifact deliberately withheld:** `build-notes.md`
- **PDCA_TARGET:** unset — all source citations are grounded against `patch.diff` only
- **Date:** 2026-06-21

---

## §1 Summary

The patch is narrowly scoped to the stated root cause and the evidence chain is solid. One unverifiable risk stands: the patch replaces `self.fix(path)` with `libgrampsxml.fix_media_path(path)` in `exportxml.py` but the diff contains no new `import` statement for `libgrampsxml` in that file. Because `exportxml.py` cannot be loaded in the headless test runner (it imports `gramps.gui` at module load), no executed test confirms the identifier resolves at runtime. This must be cleared by a human before the patch ships. All other gates pass. No out-of-scope changes were found.

---

## §2 Verdict table

| Item | Verdict | Basis |
|---|---|---|
| C1 — C1 Spec | PASS | `brief.md` fully specifies defect, root cause (`exportxml.py:1392` + `fix():strip()`), success criterion (byte-for-byte path preservation), scope, and test requirements; human-authored, unambiguous. |
| C2 — C2 Reproduction (red pre-fix) | PASS | `check-gates.json` C4 `path_line` records `red-without-fix=PASS`; the pre-fix redness of the new regression test is confirmed as a by-product of the C4 gate. |
| C3 — C3 Change | PASS | Patch touches exactly the three locations named in the brief: `exportxml.py:1392` (call-site), `libgrampsxml.py` (new serializer), `po/POTFILES.skip:564` (registration); adds the required test file; no out-of-scope edits detected. |
| C4 — C4 Verification (red→green) | PASS | `check-gates.json` C4 (gating=true): `green-with-fix=PASS / red-without-fix=PASS`; both legs confirmed by the automated oracle. |
| C5 — C5 Causal adequacy | PASS | Fix removes the `.strip()` that dropped significant whitespace from the media path (brief root cause), while retaining control-char filtering (`_STRIP_DICT`) and XML-attribute escaping (`escape()` + extras dict); the logical value of the `<file src>` attribute now equals `str(media.get_path())` for paths free of XML-special chars, restoring the brief's invariant. |
| T1 — T1 Structure | N/A | Core-only change; §Structure rule is addon-only; gate confirmed: `T1 – N/A: no addons-source path in patch.diff`. |
| T2 — T2 Shape | PASS | GPL header present in new test file (`patch.diff:74-90`); `exportxml_mediapath_test.py` registered in `po/POTFILES.skip` (`patch.diff:64`); T2 shape and T2 potfiles gates both report pass. |
| T3 — T3 Runtime | PASS | Unit suite matches recorded baseline (7 known reds); `⚠ baseline tree drift: recorded detached@674e3b` is a cosmetic warning about repo state, not a test failure. |
| T4 — T4 Contribution | N/A | No `commit-msg.txt` or `pr-description.md` in bundle; gate confirmed N/A. |
| T5 — T5 Judgment | NEEDS-HUMAN | See §6-A: the patch calls `libgrampsxml.fix_media_path(path)` in `exportxml.py` but adds no `import`; `exportxml.py` cannot be loaded headless so no executed test confirms the name resolves. Additionally, `_STRIP_DICT` (patch.diff:32) is reconstructed inline — its equivalence to the original `strip_dict` in `exportxml.py:490-492` cannot be verified without reading the target branch. |
| V — Validation — fitness-to-purpose | NEEDS-HUMAN | Human must confirm the fix resolves the reporter's missing-media symptom on a real `.gpkg` round-trip and that normal (no-leading-space) paths are unaffected in practice. |

---

## §3 C1 — Spec review

`brief.md` is present and complete. It identifies:

- **Defect:** `exportxml.py:1392` routes the media path through `self.fix(path)`; `fix()` at `490-492` calls `.strip()`, removing leading/trailing whitespace that is part of the filename.
- **Disagrement site:** `exportpkg.py:192` archives under `archname = str(mobject.get_path())` (un-stripped), so the XML `<file src>` and the archive entry name diverge.
- **Success criterion:** `<file src>` value equals `str(media.get_path())` for paths free of XML-special chars; byte-for-byte on re-import.
- **Scope boundary:** only the media-path serialization call; `fix()` behaviour for other text fields and sanitisation at entry time are explicitly out of scope.
- **Test requirement:** a new `*_test.py` that exercises the **production** serializer (not a hand-copied reimplementation).

No gaps found in the spec.

---

## §4 C3 — Change review

### exportxml.py (patch.diff:9-10)

```diff
-                self.fix(path),
+                libgrampsxml.fix_media_path(path),
```

Call-site change is correct and minimal. **Risk:** no `import libgrampsxml` statement appears anywhere in the exportxml.py hunk. The diff is a single-hunk, one-line patch, so if the import does not pre-exist in the file it is missing from the patch. See §6-A.

### libgrampsxml.py (patch.diff:22-55)

- `from xml.sax.saxutils import escape` added (patch.diff:22) — standard library, no new dependency.
- `_STRIP_DICT` (patch.diff:32): removes codepoints 0–8, 11–12, 14–31 (preserves `\t`/0x09, `\n`/0x0A, `\r`/0x0D). Comment confirms intent. Cannot verify equivalence to original `strip_dict` without target source.
- `fix_media_path()` (patch.diff:35-55): `escape(str(path).translate(_STRIP_DICT), {'"': "&quot;", "<": "&lt;", ">": "&gt;"})`. This correctly: (a) drops XML-illegal control chars, (b) XML-escapes `&`, `<`, `>`, `"` for safe attribute-value embedding, (c) does **not** call `.strip()`. For a path with no XML-special chars, the result equals `str(path)`, restoring the brief's invariant against `exportpkg.py`'s `archname`.

### po/POTFILES.skip (patch.diff:64)

`gramps/plugins/export/test/exportxml_mediapath_test.py` added. Correct; the file contains no translatable strings.

### exportxml_mediapath_test.py (patch.diff:68-177)

- Tests `fix_media_path` directly (the production serializer, not a copy).
- Covers: leading space, trailing space, interior/surrounding whitespace, plain path, archiver-name equivalence, control-char removal, XML metachar escaping.
- Source-level guard (`test_export_plugin_routes_path_through_fix_media_path`, patch.diff:156-172): reads `exportxml.py` as text and asserts the string `"fix_media_path(path)"` appears. This is the right approach for a module that cannot be imported headless, but it is fragile to whitespace reformatting of the call site. Acceptable given the constraint; noted for awareness.

---

## §5 C5 — Causal adequacy

The brief's causal chain:

1. `write_media()` → `self.fix(path)` → `fix()` calls `.strip()` → leading/trailing whitespace removed
2. `<file src>` written with stripped value
3. `exportpkg.py` archives under un-stripped `str(mobject.get_path())`
4. XML path ≠ archive entry name → "missing" on re-import

The fix severs link (1) → (2): `fix_media_path()` never calls `.strip()`. Links (3) and (4) are resolved by the fix alone — no changes to `exportpkg.py` are needed or made. The causal adequacy is direct.

---

## §6 Items requiring human clearance

### §6-A (T5) — Missing `import libgrampsxml` in exportxml.py  *(must clear before ship)*

The patch replaces `self.fix(path)` with `libgrampsxml.fix_media_path(path)` at `exportxml.py:1392` but the diff contains no `import` statement for `libgrampsxml` in that file. `exportxml.py` imports `gramps.gui` at module load, so it cannot be loaded in the headless test runner; consequently no executed test confirms `libgrampsxml` is a name in scope at the call site. If the import does not pre-exist in the target branch, this will raise `NameError` at runtime on every media export.

**Action:** Confirm that `from gramps.plugins.lib import libgrampsxml` (or equivalent) exists in `exportxml.py` on the target branch prior to the patch. If it does not, add it.

### §6-B (T5) — `_STRIP_DICT` equivalence to original `strip_dict` *(verify before ship)*

`_STRIP_DICT` in `libgrampsxml.py` is constructed from scratch. It should be equivalent to the `strip_dict` used by `exportxml.fix()` at `490-492`. This cannot be confirmed from `patch.diff` alone. A mismatch would mean `fix_media_path()` retains or drops different control codepoints than the rest of the serializer.

**Action:** Read `exportxml.py:490-492` on the target branch and confirm the two dicts cover the same set of codepoints.

### §6-C (V) — End-to-end `.gpkg` round-trip validation *(fitness-to-purpose)*

The regression test exercises `fix_media_path()` as a unit. No executed test does a full export→import round-trip (the headless constraint makes this impractical in CI). Human validation that a media object with a leading-space path survives a `.gramps` / `.gpkg` export and re-import without showing as "missing" is required before this is closed as fixing the reporter's issue.

**Action:** Manual or integration test on the target branch: create a tree with `" example.png"`, export to `.gpkg`, re-import, confirm the media resolves.

---

## §7 Overall disposition

**CONDITIONAL PASS** — all automated gates pass and the logic is sound. Ship is blocked on §6-A (the `import` question) and advisory on §6-B and §6-C. Once §6-A is confirmed clear and §6-B/C satisfied by the human reviewer, this patch is ready to proceed.

## 6. NEEDS-HUMAN — items the human must clear before sign-off
- [x] T5 — T5 Judgment — See §6-A: the patch calls `libgrampsxml.fix_media_path(path)` in `exportxml.py` but adds no `import`; `exportxml.py` cannot be loaded headless so no executed test confirms the name resolves. Additionally, `_STRIP_DICT` (patch.diff:32) is reconstructed inline — its equivalence to the original `strip_dict` in `exportxml.py:490-492` cannot be verified without reading the target branch.
- [x] V — Validation — fitness-to-purpose — Human must confirm the fix resolves the reporter's missing-media symptom on a real `.gpkg` round-trip and that normal (no-leading-space) paths are unaffected in practice.

## 7. Proven / not proven
- Proven by which oracle: gates overall = pass (stub oracles).
- Unproven / needs manual run: anything flagged in §6.

## 8. Ready-to-ship attachments
- patch.diff
- tracker-comment.md     (ALWAYS, every tracker item)
- build-notes.md         (builder rationale — for the human, not the reviewer)

## 9. Check sign-off                     ← human completes Check here
- Disposition confirmed / overridden:
- Outcome: merged-wider
- Iteration delta (if iterating):
- By / date: Eduard Ralph / 2026-06-21

## 10. Act candidates (hints for the next Act review)
- (empty is the common case)
