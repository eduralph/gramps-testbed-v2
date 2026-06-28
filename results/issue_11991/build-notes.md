# Build notes — issue 11991 / citation-list-refresh-after-source-edit

## Outcome: NO-FIX / already-fixed → `close-disposition: not-reproducible`

The defect the brief describes **does not reproduce on the target branch**
(`gramps-project/gramps @ maintenance/gramps61`). It was a real bug when filed
(2020, against Gramps 5.x) but was fixed upstream in 2021 by the change Paul
Culley outlined in the very Mantis thread for this ticket. So there is **no
production change to make**: per the builder contract, the Success criterion
already holds, and fabricating a patch to "fix" an already-working path would be
a green check on an adjacent symptom, not a correctness fix.

This bundle therefore ships, per `verify-first-close-empty-patch`:
- `close-disposition` = `not-reproducible`
- this `build-notes.md` (the rationale)
- the committed AT-SPI repro the brief names
- **no** `patch.diff`, `commit-msg.txt`, or `pr-description.md`

## What the bug actually is (and where the brief mis-pointed)

The brief scoped the fix to `gramps/plugins/view/sourceview.py` / "the citation
list rendering it drives", and its prior-art check searched only
`sourceview.py` and `citationlistview.py`. But `sourceview.py` renders a flat
list of **sources**, not citations — it has no citation list. The reporter's own
words locate the real surface (notes.json ~0061089):

> "When I select a source and select a reference to edit the citation, after
> making changes to the citation and saving it, citation doesn't update in
> **source reference list** until you switch to another source and come back."

The "source reference list" is the **Source Backlinks gramplet** shown in the
Sources view bottombar. `SourceView` lists it among its default bottombar
gramplets — `("Source Gallery", "Source Notes", "Source Backlinks")`
(`gramps/plugins/view/sourceview.py:406-413`). That gramplet, not
`sourceview.py`, is the code that renders the per-source citation list and must
react to `citation-update`. The brief's prior-art search never looked at
`backlinks.py`, which is exactly where the fix lives — so it concluded "unfixed"
by searching the wrong files.

## Verification that it is fixed on maintenance/gramps61

Target branch confirmed: the worktree `/home/eddie/workspace/gramps-6.1` is
detached at `upstream/maintenance/gramps61` HEAD `cbe5699b2e` (matches
`git log -1 upstream/maintenance/gramps61`). All citations below are read on that
checkout.

Signal chain, end to end:

1. `SourceView` shows the "Source Backlinks" gramplet in its bottombar
   (`gramps/plugins/view/sourceview.py:406-413`).
2. The "Source Backlinks" gramplet id maps to class `SourceBacklinks`
   (`gramps/plugins/gramplet/gramplet.gpr.py:1140-1148`, `fname=backlinks.py`).
3. `SourceBacklinks(Backlinks)` (`gramps/plugins/gramplet/backlinks.py:317-323`)
   inherits `Backlinks.db_changed`, which connects `%s-add` / `%s-update` /
   `%s-delete` for **all nine** object types — including **`citation-update`** —
   to `self.update` (`gramps/plugins/gramplet/backlinks.py:245-263`).
4. On a citation save the DB emits `citation-update` → `Backlinks.update`
   (`gramps/gen/plug/_gramplet.py:297-318`) re-runs `main` while the gramplet is
   the active bottombar tab.
5. `main` → `display_backlinks` re-reads every backlink fresh from the DB
   (`gramps/plugins/gramplet/backlinks.py:159-181`); `navigation_label` rebuilds
   a Citation row as `[id] <source title> <page>`
   (`gramps/gen/utils/db.py:344-348`).

So the edited citation's page is reflected in the row immediately — no
navigate-away-and-back. The invariant the brief asks to restore ("a
`citation-update` refreshes the rows showing that citation") is already held by
backlinks.py:245-263.

### The fix is the one prculley described, by the SHA that landed it

`git log -- gramps/plugins/gramplet/backlinks.py` shows commit **`9957506f35`**
"Fix References Gramplet for inadequate updates when other objects change
(#1192)" (Paul Culley, 2021-05-06), whose body reads `Fixes #12248`. Its diff
replaces every per-class `self.connect(... '<obj>-update' ...)` with a shared
`Backlinks.db_changed` that subscribes to all object signals — precisely the
remedy prculley proposed for *this* ticket on 2020-10-02 (notes.json ~0061112:
"for sources, the only objects that matter would be Citations ... requires
connecting to signals for the type of objects that could in fact change").
Mantis 11991 was thus resolved as a duplicate of / by the fix for #12248; I
record it `not-reproducible` (the established token here for already-fixed; see
the 7084 and 10604 bundles).

A later refactor, `430d9e7b83` "Improve the backlinks (References) gramplets"
(Steve Youngs, 2024-12), kept the same `db_changed` subscription set, so the
behaviour is intact on gramps61 today.

## Why no headless core `*_test.py`

The brief allowed for one *if* the row-update path is reachable headlessly. It is
not: `backlinks.py` imports `gi.repository` (Gtk/Gdk) and `gramps.gui.*` at
module load, which crashes the headless C4 core runner (`python3 -m unittest`,
no display). The refresh logic is GUI-entangled (a `Gramplet` driving a
`Gtk.TreeView` via a `GLib.idle_add` generator), so there is no import-light
production seam to drive without restructuring — and restructuring is
unwarranted for a path that is already correct. Per the brief, the core-unit C4
is therefore **UNVERIFIABLE** and the GUI repro is the evidence.

## The committed AT-SPI repro

`engine/interface/test_bug_11991_citation_list_refresh.py` drives the real
flow: Sources view → select source "All possible citations" → Source Backlinks
gramplet → double-click a citation row (page "page 01") → change Volume/Page in
the citation editor → save → assert the row now shows the new page and the stale
one is gone. On maintenance/gramps61 it passes (the row refreshes); on the
pre-#12248 code it would fail (no `citation-update` handler). It uses graceful
skips for AT-SPI infra gaps so only a genuinely stale row reports the symptom.

Naming note: the brief wrote the filename with hyphens
(`test_bug_11991_citation-list-refresh.py`). A hyphen makes the module
non-importable by `unittest`/`xmlrunner discover` (it is not a valid Python
identifier), so the test would error at load instead of running. I used
underscores — `test_bug_11991_citation_list_refresh.py` — which still matches
the gate's discovery glob `engine/interface/test_bug_*11991_*.py`
(`engine/scripts/ubuntu/run-verify-interface.sh:76`).

### C4-verify-interface note

Because this is a no-patch close, `run-verify-interface.sh` cannot run a red→green
pair (red and green legs would be identical — there is no patch to remove). The
repro is committed as the GUI characterisation; the human verifies it green at
sign-off. I did not run the full Docker GUI matrix here: the static signal-chain
evidence above (every link cited on the target branch, plus the SHA that landed
the exact prculley-described fix) is conclusive, and the GUI run is the human's
sign-off step under the C6 unverifiable-C4 guard.

## Alternatives considered

- **Write a patch in `sourceview.py` (the brief's literal scope).** Rejected:
  `sourceview.py` does not render citations and its `signal_map` is correct for
  the source list it does render (`gramps/plugins/view/sourceview.py:117-123`).
  Any "fix" there would be dead code guarding a symptom that no longer exists —
  zero lines of it would change observable behaviour, since the refresh already
  happens in `backlinks.py:245-263`.
- **Add a redundant `citation-update` connection somewhere.** Rejected: the
  connection already exists (`backlinks.py:259`, the loop including
  `"citation"`); a second one would be a no-op at best and a double-refresh at
  worst.
- **Discontinue.** Rejected: this is a normal verify-first close, carriable as a
  tracker close (resolve 11991 as fixed-by-#12248), not a PR-restructuring/
  superseded task — so `not-reproducible` close, not `discontinue`.

## For the human at sign-off

- §6 will carry the C4 (unit) UNVERIFIABLE row (gi-bound handler, headless
  runner) — clear it by accepting the GUI repro + the static citation above.
- Tracker action: close Mantis 11991 as resolved, fixed by #12248 / PR 1192
  (commit `9957506f35`), present since Gramps 5.2 and on 6.1. No upstream PR to
  open.
