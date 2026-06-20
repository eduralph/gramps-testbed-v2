# Brief — issue 13205 / merge-citations-noncitation-backlink-crash

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.
> The field labels below are parsed by the driver — keep the `- **Label:** value`
> shape. The success criterion is the load-bearing field: it is the sentence
> Check tests "did this work" against.

> **Iteration note (v2 — was iterate-plan; see brief.v1.md).** Two Do rounds shipped
> a test that did `from gramps.plugins.tool.mergecitations import MergeCitations` to
> reach the extracted helper. That module imports the **entire GUI stack at load
> time** (`gi.repository.Gtk` at `mergecitations.py:39`; `gramps.gui.utils/.plug.tool/
> .dialog/.display/.managedwindow/.glade` at `:52-60`), so importing it under the
> **headless C4 runner** (`run-verify.sh` core mode = plain `python3 -m unittest`, no
> display / D-Bus / AT-SPI) core-dumps → C4 `green-with-fix=FAIL`, T3 crash. A static
> method *on the GUI class* does not help — you still import the module. v2 makes the
> extraction target explicit below.

- **Slug:** merge-citations-noncitation-backlink-crash
- **Defect:** Tools → Family Tree Processing → **Merge Citations** aborts with `gramps.gen.errors.MergeError: Encountered an object of type Note that has a citation reference.` and forces the user to kill Gramps. A **regression**: the reporter confirms the same database merged successfully (977 citations) on 5.1.6, and it breaks on 5.2.0 / 5.2.1 / 5.2.2. (Mantis 13205.)
- **Success criterion:** Running the Merge Citations logic over a database where a Source is referenced by a **non-Citation** object (e.g. a Note that carries a source/citation reference) completes the merge pass **without raising `MergeError`** — non-Citation backlinks of a source are skipped, and citations are still merged as before.
- **Repo + branch target:** gramps (core) @ `maintenance/gramps61` — branched from `upstream/maintenance/gramps61`; forward-merged to `master` (INTEGRATION §2: core fixes ride the current maintenance branch).
- **Scope:** Two coupled, minimal changes forming one logical fix: **(1)** stop the merge loop from assuming **every** backlink of a Source is a Citation — collect only Citation backlinks (pass `include_classes=["Citation"]` to `find_backlink_handles`, signature `find_backlink_handles(handle, include_classes=None)` at `gramps/gen/db/base.py:99`, or `continue` past non-Citation `class_name` instead of raising). **(2)** Put that source→citation-handles collection in a **new GUI-free module** — e.g. `gramps/plugins/tool/mergecitationslib.py` — importing ONLY `gramps.gen.*` (NO `gi.repository`, NO `gramps.gui.*`), exposing a module-level function such as `citation_handles_of_source(db, source_handle) -> list[str]` (skips non-Citation backlinks). `mergecitations.py` imports the helper from that module and calls it where `on_merge_ok_clicked` did the loop — behaviour preserved. **The load-bearing constraint:** the test imports ONLY that GUI-free module and NEVER `gramps.plugins.tool.mergecitations`, because the tool module pulls the whole GUI stack at load (`Gtk` + `gramps.gui.*`, `mergecitations.py:39,52-60`) and the headless C4 runner core-dumps on it (this sank both prior Do rounds). / **out of scope:** changing the actual citation-merge behaviour (`MergeCitationQuery`); the "don't merge if citation has notes" option semantics; investigating *why* 5.2 introduced the non-citation backlink (root of the regression is the unguarded assumption, not the new backlink itself).
- **Repro instruction:** fixture: a tree where a Source is referenced by something other than a Citation (reporter's `borg_2024-03-05.gramps` exhibits it; Do should build a minimal equivalent — a Source, a Citation referencing it, plus a second object that backlinks the Source with `class_name != "Citation"`). Run the merge loop with default options ("Ignore date", "Don't merge if citation has notes" unchecked). Root cause verified by reading `gramps/plugins/tool/mergecitations.py:199-207`: the loop does `for class_name, citation_handle in db.find_backlink_handles(source_handle)` and `raise MergeError(...)` whenever `class_name != Citation.__name__` (line 202-207), aborting the whole tool.
- **Test file:** `gramps/plugins/tool/test/mergecitations_test.py` — **core** convention: a `test/` (singular) package with an `__init__.py`, file named with the `*_test.py` suffix (INTEGRATION §3). Red pre-fix (a non-Citation source backlink is not skipped → `MergeError` / missing helper); green post-fix (the helper returns only the Citation handle, non-Citation backlink skipped, no `MergeError`). It imports ONLY the new GUI-free module and asserts against its function directly — see Scope for the load-bearing import constraint and the helper signature.
- **Citations expected:** Do must cite path:line on `maintenance/gramps61` for every change (the guarded backlink iteration / new `mergecitationslib.py`, and the call site in `mergecitations.py`).
- **Prior-art check (triage cycles):** searched gramps history by path — `git -C ../gramps log -- gramps/plugins/tool/mergecitations.py` on gramps61 shows only style/translation churn since the regression window; no merged fix for this `MergeError`. Confirm open/closed upstream PRs by path at Do time (INTEGRATION §5).
- **Disposition hint:** likely-fix
