# Build notes — issue 6170 / sidebar-filter-copy-shortcut

## Root cause (target branch: gramps-project/gramps @ maintenance/gramps61)

`PageView` connects the view's key handler on the **toplevel window**:

- `gramps/gui/views/pageview.py:131` —
  `self.uistate.window.connect("key-press-event", self.key_press_handler)`

`GtkWindow` delivers `key-press-event` to the toplevel **before** the focused
child widget, so a window-level handler runs first. `NavigationView` overrides
that handler and, for Ctrl+C, unconditionally performs the object copy and
consumes the event:

- `gramps/gui/views/navigationview.py:481-490` — `key_press_handler`; the
  offending branch is `487-489`:
  ```python
  if event.keyval == Gdk.KEY_c and match_primary_mask(event.get_state()):
      self.call_copy()
      return True
  ```

`return True` stops propagation, so a focused sidebar/filter text entry never
sees Ctrl+C. `call_copy` (`navigationview.py:505-516`) →
`copy_to_clipboard` (`pageview.py:274-329`) then constructs a
`ClipboardWindow` (`pageview.py:295`) whenever a list object is selected —
which is why the symptom is "Ctrl+C pops up the Clipboard and copies the
person". Ctrl+X (cut) and Ctrl+V (paste) are unaffected because this handler
only matches `Gdk.KEY_c`; that is why the brief says they already work.

The Clipboard window's title is `_("Clipboard")`
(`gramps/gui/clipboard.py:1376`, `set_window(..., msg=_("Clipboard"))`) — this
is the AT-SPI-observable frame the repro keys on.

## The fix

`gramps/gui/views/navigationview.py:481-501` — before invoking the object copy,
consult the toplevel's current focus and let a focused **text-editable** widget
own the keystroke:

```python
focus = self.uistate.window.get_focus()
if isinstance(focus, (Gtk.Editable, Gtk.TextView)):
    return False
self.call_copy()
return True
```

Returning `False` lets GtkWindow propagate the event to the focused editable,
which performs the standard text Copy to the system clipboard; no Gramps
Clipboard window is created. When the list/tree itself (a `Gtk.TreeView`, not a
`Gtk.Editable`/`Gtk.TextView`) holds focus, `call_copy()` runs exactly as
before, so the object-copy path is preserved.

`Gtk` is already imported at `navigationview.py:42`, so no new import is needed.

### Why this restores the *invariant*, not just the symptom

The brief names an **Invariant to restore**: a view/window-level accelerator
must not shadow the standard text-editing keystrokes of a focused text-editable
widget. The fix lives in the shared `NavigationView.key_press_handler`, so it
holds for **every** navigation list view (People, Families, Events, Places,
Sources, Citations, Repositories, Media, Notes — all `NavigationView`
subclasses), whose sidebar/bottombar filter fields are `Gtk.Entry`
(a `Gtk.Editable`). This is exactly the SELF-TEST the brief demands: the
property would *fail* for a one-branch guard that special-cased only the person
view; it *holds* here because the guard is on the generic focus type, not a
per-view special case.

## Alternatives considered (with cost)

- **Guard only `libpersonview` / the People view** (a one-branch special case).
  Rejected on correctness, not cost: the invariant's SELF-TEST explicitly
  requires the property to *fail* for such a guard, and it would leave Families/
  Events/Places/etc. still stealing Ctrl+C from their sidebar entries. It is
  also *more* code — one focus check duplicated into each of ~9 view modules vs.
  the +11-line single edit here.

- **Bail only when the entry has a text selection** (e.g.
  `if isinstance(focus, Gtk.Editable) and focus.get_selection_bounds(): return False`).
  Rejected: the invariant says the focused editable owns Copy/Cut/Paste
  *regardless of selection*. With a selection-only guard, Ctrl+C in a focused-but-
  unselected entry would still copy the list object and pop the Clipboard — the
  same class of shadowing bug. Checking focus type alone is both smaller and
  correct; a focused entry with no selection simply Copies nothing, which is the
  standard GTK behaviour.

- **Rework the accelerator wiring** (move the Ctrl+C handling off the toplevel
  onto the treeview, or install a `Gtk.AccelGroup` scoped to the list). Rejected
  on cost and blast radius: it would touch the connection site at
  `pageview.py:131` and the event-routing contract shared by
  `button_press_handler` and every `NavigationView`, i.e. a multi-file
  restructuring, where the invariant is fully restored by an 11-line focus guard
  at the single point that already decides the copy. Per principles §1.2/§2 the
  target is the smallest change that restores the invariant, which this is.

- **`Gtk.Editable` only (drop `Gtk.TextView`)**. Would cover every reported
  case (all sidebar/filter fields are entries). I included `Gtk.TextView` at one
  extra tuple element of cost because the invariant is stated for "a focused
  text-editable widget" generally; a focused multi-line text area (e.g. a
  bottombar gramplet) is equally entitled to own Copy. No downside: no
  navigation list view expects object-copy while a `TextView` holds focus.

## Test — `engine/interface/test_bug_0006170_sidebar_filter_copy.py`

This behaviour is irreducibly GUI/focus/clipboard-bound: the bug is a GTK key
propagation decision that depends on which real widget holds keyboard focus in a
running Gramps. It cannot be reduced to an import-light unit without
re-implementing GTK focus routing (a parallel copy the task forbids). The
testbed's designated vehicle for exactly this is the AT-SPI/dogtail interface
repro run headless (xvfb + D-Bus + AT-SPI) by the **C4-verify-interface** gate
(`engine/scripts/ubuntu/run-verify-interface.sh`), which drives the *real*
patched `gramps` process — production, not a copy.

The repro: open the People category, select a person (so the object-copy path
has a handle — otherwise `copy_to_clipboard` opens no window and the red symptom
cannot form), focus the sidebar/filter text entry, type + select text, press
Ctrl+C, then assert **no showing top-level frame titled "Clipboard"** exists.
The role filter (`frame`/`dialog`/`window`) ensures the Edit-menu/toolbar
"Clipboard" *button* is never mistaken for the Clipboard *window*.

- **Red (unpatched):** Ctrl+C is stolen by the toplevel handler → the selected
  person is copied → a `ClipboardWindow` titled "Clipboard" appears →
  `assertFalse` fails.
- **Green (patched):** focus is a `Gtk.Editable` → handler returns `False` → the
  entry copies its text, no Clipboard window → passes.

Graceful `skipTest` fallbacks cover infra gaps (category switch, row select,
entry discovery); the red-leg skip-guard in the runner treats an all-skipped red
leg as PDCA-UNVERIFIABLE rather than a false red-pass.

## Verification status (NEEDS-HUMAN / gate)

I confirmed structurally in this session:
- `patch.diff` applies cleanly to pristine
  `upstream/maintenance/gramps61:gramps/gui/views/navigationview.py` (fetched via
  `gh api`) and produces the intended code (`git apply` clean, verified).
- The patched module and the test both parse/compile (`ast.parse` /
  `py_compile`).
- The red↔green discriminator is real: `ClipboardWindow` is titled "Clipboard"
  (`clipboard.py:1376`) and is only created when a list object is selected
  (`pageview.py:295`), so it appears pre-fix and not post-fix.

I could **not** execute the docker-backed `run-verify-interface.sh` red→green in
this sandbox (the container/docker invocation is denied here, and background
runs were unavailable). The per-fix GUI red→green is therefore left for the
**C4-verify-interface** gate / human sign-off to confirm — it runs exactly this
committed repro against the pinned `gramps-6.1` worktree. No fabricated stand-in
was substituted; the shipped test drives real production.

Manual validation steps (if run by hand):
1. On `maintenance/gramps61`, People view, select a person.
2. Click the sidebar/filter "Name" entry, type text, select it (Ctrl+A).
3. Press Ctrl+C. Pre-fix: the Clipboard window opens and the person is copied.
   Post-fix: no Clipboard window; the text is on the system clipboard (paste it
   elsewhere to confirm).
4. Click a row in the person list (focus the tree) and press Ctrl+C: the person
   is still copied to the Gramps clipboard (object-copy preserved).

## Formatting / commit-readiness

`black` is not installable in this sandbox (no `pip`), so I hand-matched the
project's black style: the added lines reuse the surrounding indentation, stay
well under the 88-column limit (longest added line is 71 cols:
`if isinstance(focus, (Gtk.Editable, Gtk.TextView)):`), and add no constructs
black would reflow. The single edit is confined to one function body.

## POTFILES

No POTFILES change is required: `patch.diff` adds/removes no core `.py` file (it
edits an existing one), and the AT-SPI repro ships in the testbed
`engine/interface/`, outside gramps' `po/POTFILES` scope (brief §New/removed
files).

## Scratch

`results/issue_6170/.src/` holds builder scratch (target sources fetched via
`gh api` for diffing + a throwaway git repo used only to `git apply --check` the
patch). It is not a deliverable and can be discarded; the sandbox denied its
removal here.
