---
title: "Gramps 6.1 Wiki Manual - Core Development - Debugging"
categories: [Developers, Gramps 6.1]
managed: true
---

<!--wiki:{{man index|6.1}}-->

<!--
  Authoritative scraped source:
  ../04 - Technical Documentation/debugging-gramps.md (182L).
  This chapter is the core-developer view: the techniques that apply when
  you are editing gramps-project/gramps itself — terminal tracebacks, the
  logging tree, --debug, pdb/breakpoint, winpdb, the
  gen.utils.debug.profile cProfile hook, gdb for the C/GTK layer.
-->

## Overview

How to find out what Gramps core is actually doing when it crashes, misbehaves, or runs too slowly — from a one-line traceback off the terminal up to stepping the C/GTK layer under `gdb`.

Reach for the lightest tool that answers the question. Most core bugs are pinned by **running from a terminal and reading the traceback**, then by **raising the log level on the right logger**. The heavier tools — `pdb`/`breakpoint()`, `winpdb`, `cProfile`, `gdb` — earn their cost only when the lighter ones don't localise the fault. This page is how-to; the MUST/SHOULD rules around logging and diagnostics live in [[16-guidelines]] (§Runtime).

You must run from your source checkout, not an installed copy ([[16-guidelines]] §Source structure). Launch with `python3 Gramps.py` from the checkout root, or set `GRAMPS_RESOURCES=.` so the running program loads the code you are editing.

## Hard crashes: run from a terminal

The single most useful habit: when something crashes, **launch Gramps from a terminal** so the traceback lands on stderr instead of vanishing.

```bash
python3 Gramps.py
```

Gramps installs an `excepthook` that routes otherwise-unhandled exceptions through the logger as an `ERROR` (`gramps/grampsapp.py:172`, `exc_hook`), so an uncaught Python exception prints a full traceback with file and line. That traceback is the diagnosis — read it bottom-up to the first frame inside the code you changed.

Two cases need more than the default traceback:

| Symptom | Approach |
|---|---|
| Crash with no usable traceback (the interpreter dies mid-frame) | trace every executed line: `python3 -m trace -t Gramps.py >/tmp/trace.out` |
| Hard process death — segfault, abort — with no Python traceback at all | drop to the C layer with `gdb` (see [gdb for the C/GTK layer](#gdb-for-the-cgtk-layer)) |

`python3 -m trace -t` writes one line of output for every Python statement executed, which is enormous and slows the program down — always redirect to a file and `grep` the tail to find the last statement before the crash:

```bash
python3 -m trace -t Gramps.py >/tmp/trace.out
tail -n 100 /tmp/trace.out
```

### `__debug__` / assertions

Gramps can be launched under the optimize flag, which strips `assert` statements and sets `__debug__` to `False`:

```bash
python3 -O Gramps.py     # assertions stripped, __debug__ == False
python3    Gramps.py     # assertions live,     __debug__ == True
```

Core already guards a handful of diagnostics behind `if __debug__:` (e.g. `gramps/gen/dbstate.py:88`, `gramps/grampsapp.py:586`). You MAY add an `assert` or an `if __debug__:` block for a development-only check that costs nothing in a `-O` run; this is a debugging aid, not a substitute for raising the error a user should see.

## Logging, not `print()`

Diagnostic output goes through the stdlib `logging` tree, never `print()` — this is a **MUST NOT** in [[16-guidelines]] (§Runtime; `gramps/AGENTS.md` §Logging). `print()` is invisible in a windowed launch with no terminal attached and bypasses the in-app surfaces below.

Every module gets a module-level logger:

```python
import logging

LOG = logging.getLogger(__name__)     # canonical: dotted module name, a child of the root

LOG.debug("Computed candidate set: %s", candidates)
LOG.info("Processed %d people", n)
LOG.warning("Skipping malformed event %s", event.gramps_id)
LOG.error("Could not parse %s", filename)
```

Acquire the logger with `logging.getLogger(__name__)` (`gramps/AGENTS.md` §Logging; matches [[16-guidelines]] and [[05-fundamentals]]): `__name__` is the module's dotted import path, so every logger is a named child of the root logger Gramps configures at startup. Some older core modules instead pass an explicit dotted name like `logging.getLogger(".locale")` (`gramps/grampsapp.py:35,652`); the targeting below works the same either way, because both forms produce a stable dotted name you can lower individually with `--debug`.

### Default level and where output lands

Gramps configures the **root logger at `WARNING`** at startup (`gramps/grampsapp.py:158,168`); `DEBUG` and `INFO` are filtered out by default. The handlers attached to the root are:

| Surface | Level | Source | What you see |
|---|---|---|---|
| stderr / terminal | `DEBUG` | `gramps/grampsapp.py:161-169` (`StreamHandler`) | everything the root passes — so once you lower the root or a child logger, it appears here |
| Status-bar warning button | `WARNING` | `gramps/gui/displaystate.py:489-493` (`WarnHandler`, capacity 400) | `WARNING`+ records buffer up; the warning button appears in the status bar and shows them on click |
| Error report window | `ERROR` | `gramps/gui/grampsgui.py:750-756` (`GtkHandler` + `RotateHandler`) | `ERROR`/`CRITICAL` pop the bug-report assistant with the surrounding log context |

The stderr handler is set to `DEBUG`, so the gate is the **logger's** level, not the handler's: the root sits at `WARNING`, which is why you only see warnings and above until you lower a logger. (The older scraped wiki refers to a "Help → Log window"; in current core the in-app surfaces are the **status-bar warning button** for `WARNING`+ and the **error report assistant** for `ERROR`+, both fed by the same root logger.)

### `--debug=<logger_name>`: the warn/error filter, lowered per logger

To see `DEBUG`/`INFO` from one area without drowning in the rest, launch with `--debug` naming the logger to lower:

```bash
python3 Gramps.py --debug=.                 # lower the root logger (everything)
python3 Gramps.py --debug=.locale           # just the locale logger
python3 Gramps.py -d gramps.gen.db          # short form -d
```

The flag does exactly `logging.getLogger(value).setLevel(logging.DEBUG)` on the named logger (`gramps/cli/argparser.py:340-343`) — it is strictly opt-in per logger, which is why it lives on the launch command rather than in code. Name the logger you set up above; other loggers stay at `WARNING`, so you are not swimming in noise. The flag accepts the empty/root name `.` to lower everything at once.

### Module-level override (development only)

While iterating tightly on one module you MAY lower its logger in place:

```python
import logging
logging.getLogger(__name__).setLevel(logging.DEBUG)   # development only — just this module
```

Remove it before committing — shipping code must rely on `--debug=…` so users are not forced into verbose output, and a stray `setLevel` is a review finding.

## Profiling with `cProfile`

Core ships a convenience wrapper around `cProfile` at `gramps/gen/utils/debug.py:36` (`profile`). It runs a callable under the profiler and prints per-function call counts and timings, sorted by time, plus the callers report:

```python
from gramps.gen.utils.debug import profile

def cb_save(self, *obj):          # was: connected directly to self.save
    profile(self.save, *obj)
```

Rewire the call you want to measure so the profiled function is the **first argument** to `profile`, with its own arguments following — e.g. swap the editor's OK-button connection from `self.save` to a `cb_save` that calls `profile(self.save, *obj)`. On the next save, the report goes to stdout (note: `profile` prints to `sys.stdout`, so capture it from the terminal). The report pins where the time actually goes — usually a surprising hot loop, not where you guessed.

See [GEPS 016: Enhancing Gramps Processing Speed](wiki:GEPS_016:_Enhancing_Gramps_Processing_Speed) for a worked profile analysis. For a repeatable performance check, formalise the slow path as a test rather than a manual profiling session — see [[08-testing]].

## Python debugging: `pdb` / `breakpoint()`

For stepping Python, use the stdlib debugger. Drop a breakpoint at the line of interest and launch from a terminal:

```python
breakpoint()        # Python 3.7+; equivalent to `import pdb; pdb.set_trace()`
```

When execution reaches it, Gramps freezes and you get an interactive `(Pdb)` prompt in the terminal:

| Command | Action |
|---|---|
| `n` | next line (step over) |
| `s` | step into |
| `c` | continue |
| `l` | list source around the current line |
| `p expr` | print an expression |
| `w` | where — the current stack |

You can also start the whole program under the debugger:

```bash
python3 -m pdb Gramps.py
```

On startup under `-m pdb` you usually need one `c` (continue) to let Gramps run up to your first `breakpoint()`. Full reference: [Python pdb docs](https://docs.python.org/3/library/pdb.html).

## winpdb for GUI debugging

`pdb` blocks the terminal, which is awkward when the bug is in the running GTK event loop. [Winpdb-reborn](https://pypi.org/project/winpdb-reborn/) is a graphical front-end to the Python debugger that drives a running, still-interactive Gramps:

```bash
sudo apt-get install winpdb       # Debian/Ubuntu
winpdb Gramps.py
```

![[_media/Winpdb.png|Winpdb debugging a running Gramps]]

In the **File → Open Source** dialog open the file you want to debug, put the cursor on a line, and use **run to line**. The debugger runs Gramps to that point and shows the local variables with their values plus the stack frame, while the GUI stays live. This is the tool when you need to inspect widget state at a specific moment without freezing the whole process at a terminal prompt.

{{-}}

## gdb for the C/GTK layer

With GObject Introspection, faults can originate below Python — in GLib, GObject, or GTK — and surface as a **segfault or abort with no Python traceback**. For these, run the interpreter under `gdb`:

```bash
gdb python3
(gdb) run Gramps.py
# … reproduce the crash / segfault …
(gdb) bt
```

Install the matching debug symbols first (e.g. `libglib2.0-0-dbg`, `python3-gobject-dbg`, and the relevant `gir1.2-*` packages) so the backtrace has names instead of addresses. After the `SIGSEGV`, `bt` prints the C backtrace pinning the failing call:

```
Program received signal SIGSEGV, Segmentation fault.
0x00007ffff5e7226b in g_type_check_value () from /usr/lib/x86_64-linux-gnu/libgobject-2.0.so.0
(gdb) bt
```

### Trace GObject/GTK warnings

GTK emits warnings to the terminal that often signal a real problem even when nothing visibly breaks. To catch the originating call, break on the GLib log function under `gdb`:

```bash
gdb python3
(gdb) b g_log if log_level < 32
(gdb) r Gramps.py
# … reproduce …
(gdb) bt
```

To turn warnings into hard, catchable failures instead, set `G_DEBUG=fatal-warnings` so the first warning aborts with a backtrace:

```bash
G_DEBUG=fatal-warnings gdb python3
(gdb) r Gramps.py
```

The same env var makes warnings fatal under a plain run or a trace, e.g. `LC_ALL=C G_DEBUG=fatal-warnings python3 -m trace -t Gramps.py`. Other values are listed in the [GLib running docs](https://docs.gtk.org/glib/running.html).

A C-level crash on a core branch is rarely a bug in Gramps' own C — it is usually a wrong/mismatched typelib version or a GI binding mismatch. The C backtrace plus your installed `gir1.2-*` / library versions point at the offending package; capture both in the Mantis ticket so a maintainer can confirm the environment.

## See also

- [[05-fundamentals]] — logger setup conventions and where the logging tree comes from.
- [[08-testing]] — turning a repro or a profiled slow path into a regression test that fails pre-fix and passes post-fix.
- [[10-troubleshoot]] — symptom-first guide to the failure modes these tools surface.
- [[16-guidelines]] — the normative rules: logger over `print()`, run from source, regression test with every fix (§Runtime, §Source structure, §Testing).
- [Debugging Gramps](wiki:Debugging_Gramps) — the standalone upstream wiki page; primary scraped source.
- [Logging system](wiki:Logging_system) — deeper reference for Gramps' logging configuration.

<!--wiki:{{stub}}-->
