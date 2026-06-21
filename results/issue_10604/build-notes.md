# Build notes — issue 10604 / docreportdialog-css-keyerror-minus-one

## Disposition: VERIFY-FIRST CLOSE — defect does NOT reproduce on maintenance/gramps61.
## No production patch, no regression test. Routes to §6 NEEDS-HUMAN per the brief's conditional Success criterion.

The brief's Success criterion is **verify-first, then conditional**:

> Do should confirm the Webstuff-hidden / empty-CSS scenario no longer raises; if it
> cannot be reproduced, route to §6 NEEDS-HUMAN (likely-close) — do not manufacture a
> change. … If the guard already covers it, no production patch ships and C4 routes to
> §6 (verify-first close).

I ran the reproduction the brief requires. **The crash does not reproduce.** Therefore,
per the criterion, I ship no patch and no test.

---

## What I verified (target branch: gramps-project/gramps @ maintenance/gramps61)

Validation worktree: `/home/eddie/workspace/gramps-6.1` (HEAD `b679c084f6`, on the
`upstream/maintenance/gramps61` line; `git status` for the file under test,
`gramps/gui/plug/report/_docreportdialog.py`, is clean — it matches upstream). Ran in
the project's Ubuntu image `gramps-testbed:ubuntu-6.1.0` with a timeout (not a bare
`docker run`).

### The production path under test

`gramps/gui/plug/report/_docreportdialog.py` — `DocReportDialog.parse_html_frame`,
lines 267–279 on maintenance/gramps61:

```
274  active = self.css_combo.get_active()
275  if active == -1:  # legal for "no active item" (see 7585, 8189, 9461)
276      active = self.style_name
277  if self.css:
278      self.css_filename = self.css[active]["filename"]
279  self.options.handler.set_css_filename(self.css_filename)
```

The reported crash was `self.CSS[self.css_combo.get_active()]["filename"]` raising
`KeyError: -1` when the Webstuff plugin is hidden:

- `_docreportdialog.py:73` — `self.css = PLUGMAN.process_plugin_data("WEBSTUFF")`. With
  Webstuff hidden, `process_plugin_data` (`gramps/gen/plug/_manager.py:526-554`) returns
  an **empty list** (no Webstuff plugin contributes `plugin.data`, no `process` callback,
  so it returns the empty `retval`).
- `_docreportdialog.py:244-256` — `setup_html_frame` then iterates an empty `self.css`,
  so the `Gtk.ComboBoxText` stays empty and `set_active(0)` on an empty combo leaves it
  with **no active item**; `get_active()` returns `-1`.
- `_docreportdialog.py:274-278` — `parse_html_frame` reads `active = -1`, the guard at
  line 275 substitutes `self.style_name`, and the `if self.css:` guard at line 277 means
  the indexing on line 278 is **skipped entirely** when the CSS map is empty. No `-1`
  index, no `KeyError`.

### Reproduction result (`repro_docreportdialog_css.py`)

The probe drives the production `DocReportDialog.parse_html_frame` (unbound, against a
light stub — it builds no widgets) with `self.css = {}` and `get_active() == -1`, i.e.
the exact Webstuff-hidden state. It first confirms the **unguarded** v4.2.8 read still
raises, so the non-reproduction is attributable to the guard, not to a missing trigger:

```
unguarded read  -> KeyError: -1   (the reported crash)
production path -> NO CRASH (css_filename=None, handler.css_filename=None)
VERIFY-FIRST RESULT: KeyError: -1 does NOT reproduce on maintenance/gramps61 —
                     the empty / no-active-item CSS state is tolerated.
```

The invariant the brief asks to restore — "a combo-box-driven selection tolerates the
empty / 'no active item' (`get_active() == -1`) state without indexing the backing map
by `-1`" — is **already intact** on gramps61.

#### Re-verification (this iterate-do run)

I re-ran the verification independently against the maintenance/gramps61 source of
`gramps/gui/plug/report/_docreportdialog.py` (guard at `:274-278`, source line
`self.css = PLUGMAN.process_plugin_data("WEBSTUFF")` at `:73`). To strengthen fidelity
over the bundled probe's `_FakeEmptyCombo`, I drove the production
`DocReportDialog.parse_html_frame` with a **real `Gtk.ComboBoxText` with no items
appended** (not a stub), bound to a light fake `self` (empty `css`, `style_name
="default"`, recording `options.handler`). Result:

```
get_active() on empty combo = -1
GUARDED PRODUCTION: no exception; css_filename = None
UNGUARDED ORIGINAL RAISED KeyError: KeyError(-1)
```

This confirms three things on the target branch: (1) an empty `Gtk.ComboBoxText` really
reports `get_active() == -1`; (2) the production `parse_html_frame` tolerates it (no
`KeyError`, `css_filename` left untouched); (3) the original v4.2.8 unguarded line
`self.css[get_active()]["filename"]` against an empty map still raises the exact reported
`KeyError(-1)` — so the non-reproduction is the guard, not a missing trigger.

### The only other `-1`/`active` path is also safe

When `self.css` is **non-empty**, `setup_html_frame` calls `set_active(active_index)`
with a valid in-range index (`active_index` defaults to `0`, line 242), so `get_active()`
returns `>= 0` — never `-1`. The `active = self.style_name` substitution (and hence any
`self.css["default"]` lookup) is therefore only ever taken when `self.css` is empty, in
which case line 277's guard skips the index. There is no residual path that indexes the
CSS map by `-1` (or by an absent `"default"` key on a non-empty map). No latent crash.

## Root cause of the non-reproduction (two sentences)

The 2010-era report (v4.2.8) predates the explicit `active == -1` / `if self.css:` guard,
which was added in 2016 by commit `5f1b719810` ("legal for 'no active item' (see 7585,
8189, 9461)") — long before the maintenance/gramps61 base. That guard closes exactly the
empty-CSS / Webstuff-hidden index-by-`-1` path the ticket describes, so the crash cannot
occur on the target branch.

(`git -C gramps-6.1 log -S 'legal for "no active item"' -- gramps/gui/plug/report/_docreportdialog.py`
→ `5f1b719810`, present in the target branch's history — confirms the brief's prior-art note.)

## Why no patch / no test

- **Brief mandate.** The criterion routes a non-reproduction to §6 and explicitly forbids
  manufacturing a change ("do not manufacture a change"; "no production patch ships"). The
  Invariant-to-restore is already satisfied, so the smallest change that restores it is the
  **empty** change.
- **A regression test cannot satisfy C4 here, and shipping one is self-contradictory under
  the gates.** With no production fix, a test driving `parse_html_frame` is **green on the
  unmodified tree** — there is no red leg, so C4-verify's red→green contract cannot hold.
  Worse, the new `*_test.py` must be registered in `po/POTFILES.skip` (T2-potfiles, doc 16
  §Adding/removing Python files). `run-verify.sh` then classifies that `POTFILES.skip` hunk
  as a *production* file (it is not `*_test.py`), so the patch is **not** "test-only": C4
  runs the red leg (revert `POTFILES.skip`, keep the test) and the test still **passes** →
  `green-with-fix=PASS / red-without-fix=FAIL` → C4 hard-fails (exit 1), which blocks accept
  rather than routing to §6. I verified this concretely: with the test + `POTFILES.skip`
  staged, `PDCA_BUNDLE=… run-verify.sh` reported `reverting: po/POTFILES.skip` and
  `error: po/POTFILES.skip: patch does not apply` on the retry leg — a failing gate, not a
  §6 route. Shipping the test would therefore *block* the brief-mandated verify-first close.
- **POTFILES.** No `.py` added or removed → `T2-potfiles` is N/A.
- **C4-verify.** With no `patch.diff`, the red→green mechanic has nothing to revert — the
  `PDCA-UNVERIFIABLE` / §6 NEEDS-HUMAN path applies (INTEGRATION §3). This mirrors the
  accepted verify-first precedent issue_7084 (same `POSSIBLY-FIXED → verify first`
  disposition), which likewise shipped build-notes + repro scripts and no patch/test.

## For the human at §6 sign-off

- The non-reproduction matches the brief's stated likely outcome (`POSSIBLY-FIXED → verify
  first`; "the reported crash path appears closed").
- Suggested Mantis disposition: **resolved / no-change-needed on 6.1** — the empty-CSS /
  Webstuff-hidden `parse_html_frame` read is guarded against `KeyError: -1` by commit
  `5f1b719810` (2016), present in the gramps61 ancestry; cite that commit.
- Reproduction is re-runnable from the bundle against a clean gramps61 worktree:
  `GRAMPS_RESOURCES=. python3 results/issue_10604/repro_docreportdialog_css.py`
  (needs `gramps` on the path; imports Gtk but creates no display objects, so it runs
  headless under the project's Ubuntu image).

## Alternatives considered and rejected

- **Ship a green-on-clean regression test anyway** (as a future guard for the 2016 fix).
  Rejected on two concrete grounds: (1) it has no red leg, so C4 cannot prove red→green;
  and (2) the gate interplay makes it actively *break* the close — the mandatory
  `POTFILES.skip` registration makes `run-verify.sh` treat the patch as having a production
  file, so C4 runs a red leg the test passes and **hard-fails (exit 1)** instead of routing
  to §6 (reproduced above: `red-without-fix=FAIL`). Cost of the rejected path is therefore
  *negative* — it converts a clean §6 close into a blocked gate.
- **Touch `_docreportdialog.py` to "harden" the read** (e.g. an extra `active != -1`
  belt-and-braces guard). Rejected: no confirmed live divergence; the Invariant-to-restore
  is already satisfied by lines 275/277, so the smallest change that restores it is the
  empty change. Any edit would be a behaviour-neutral churn with no failing case behind it,
  contradicting the brief's "do not manufacture a change."
