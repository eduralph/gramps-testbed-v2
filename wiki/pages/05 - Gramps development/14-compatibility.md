---
title: "Gramps 6.1 Wiki Manual - Core Development - Compatibility"
categories: [Developers, Gramps 6.1]
managed: true
---
<!--wiki:{{man index|6.1}}-->

## Overview

Cross-version concerns for a Gramps **core** contributor: which Python and GUI stack the codebase targets, which branch a fix rides and how it propagates, how deprecations reach the consumers of the public API, and why a clean cherry-pick is not a correct one. This page is how-to and explanatory; the MUST/SHOULD rules it leans on are in [[16-guidelines]] — cite that page in review, not this one.

The runtime baselines below are declared in-repo and rarely move within a minor series. The branch-and-propagation discipline is where most cross-version mistakes happen in practice, so it gets the most space here.

## Runtime baselines

| Baseline | Value | Declared in |
|----------|-------|-------------|
| Python | **3.10 or greater** | `pyproject.toml:41` (`requires-python = ">= 3.10"`) |
| GTK | **3.24 or greater** (GTK **3**, not 4) | `README.md:18`; `gramps/grampsapp.py:264` (`gi.require_version("Gtk", "3.0")`) |
| PyGObject | **3.12 or greater** | `README.md:19` |

The 3.10 floor is what lets [[16-guidelines]] require modern type-hint syntax — `X | None` over `Optional[X]`, `list[X]` over `typing.List[X]`. Don't write code that only works on a newer interpreter than 3.10 unless the whole project floor moves; the floor was last raised in 6.1 ("Update minimum python version. Python 3.9 reached EOL in October 2025." — `NEWS`, 6.1.0-beta1), so 3.9-isms that lingered in 6.0 are now safe to drop, but 3.11+-only features are not.

The GUI stack is **GTK 3 via PyGObject** (GObject Introspection), pinned by the `gi.require_version("Gtk", "3.0")` calls throughout `gramps/gui/`. There is no GTK 4 port in 6.1. The `gen` submodule is GUI-free by rule — `gramps.gen.*` imports no other Gramps submodule ([[16-guidelines]] §Source structure) — so core logic you put in `gen` carries no GTK dependency at all, which is also why headless tooling can build on it.

## Branches: maintenance/gramps61 vs master

Gramps keeps a **current production branch** and a **feature branch** in parallel:

| Branch | Role | What targets it |
|--------|------|-----------------|
| `maintenance/gramps61` | current production (6.1.x) | **all fixes and code-cleanup** |
| `master` | feature-only | genuinely new functionality |

A bug fix or cleanup PRs against `maintenance/gramps61`; the maintainer **forward-merges** that branch into `master`, so the fix reaches `master` without you opening a second PR. You do **not** PR `master` for a fix — routing through maintenance gets the fix to users in a point release sooner, and the forward-merge keeps `master` current. (`doc16:113`; jralls on gramps#2298; `INTEGRATION.md` §2.) A maintainer's explicit base-branch request on a specific PR overrides this default (e.g. Nick-Hall asking for `master` on gramps#2299).

Branch from `upstream/maintenance/gramps61`, not your fork's tracking copy — fork bases drift, and gramps PRs 2315/2316 each carried a stray `AGENTS.md` picked up from a stale fork base. (`INTEGRATION.md` §2.) The normative form of all of the above is in [[16-guidelines]] §Contributor workflow; this section is the why.

### Forward-merge, not back-port

The direction matters: fixes flow **maintenance → master** by merge, automatically, in the maintainer's hands. You are not expected to back-port from `master` to maintenance, and you MUST NOT merge across branches yourself — PRs containing merge commits are rejected upstream ([[16-guidelines]] §Contributor workflow; `gramps/AGENTS.md` §Branch merges). Rebase your branch on the target; never merge the target into it.

## Deprecation policy

Core deprecates an API by leaving it in place and emitting a `DeprecationWarning` from it, with the docstring pointing at the replacement. Two real examples on `maintenance/gramps61`:

```python
# gramps/gen/lib/url.py:170
def are_equal(self, other):
    """Deprecated - use :meth:`~.SecondaryObject.is_equal` instead."""
    warn("Use is_equal instead of are_equal", DeprecationWarning, 2)
    return self.is_equal(other)
```

`gramps/gen/lib/ldsord.py:361` follows the same shape. The pattern is: keep the old symbol callable, warn on use, document the replacement, and remove it no sooner than the next **major** release — never silently within a minor.

This is the contract downstream consumers depend on, because they consume `gramps.gen.*` and `gramps.gui.*` as their API surface. When you deprecate or change a public symbol in core, you are changing the surface everything downstream builds on:

- **Add the `DeprecationWarning` and keep the symbol** — don't delete a public method in a minor release. Code that calls it should keep working (with a warning), not break.
- **Document the replacement in the docstring**, as the examples above do, so a caller who sees the warning knows where to go.
- A change to a public signature, or removal of a public symbol, is a human-judgment item by design — the reviewer flags any change touching the upstream public API surface for human sign-off (`INTEGRATION.md` §4). Treat it as one.

The authoritative deprecated surface is always the source: grep `gramps/gen/**/*.py` and `gramps/gui/**/*.py` for `DeprecationWarning` on the target branch. For the API itself, see [[07-api-reference]].

## "Applies cleanly" is not "remains correct"

A cherry-pick or forward-merge that `git` accepts without conflict can still be **wrong** on the target branch. The patch's own hunks didn't conflict, but the *related* code on the other branch may have moved underneath it — and `git` doesn't check semantics, only text.

This is the same trap [[16-guidelines]] §Verification before commit names: a green mechanical check (`git cherry-pick` applies, Black clean, `mypy` exits 0, build green) is evidence of *that narrow check*, never of correctness. **"Cherry-pickable" means *remains correct on the target branch*, not *applies without conflict*.**

The check, before treating a cross-branch port as done:

1. **Diff the related code on the target branch** — not just the file your patch touched. Read the surrounding functions and the modules the changed code calls into.
2. **Run the regression test on the target branch**, not only on the branch you wrote it against. Red-before / green-after has to hold *there*.
3. **Reproduce against `example.gramps` on the target branch** — the canonical fixture is identical across minors, so an output difference is an actionable signal.

Cross-branch cherry-pick correctness is a human-judgment item by design (`INTEGRATION.md` §4): when a fix has to land on more than one branch, the maintainer verifies the second landing, the tooling does not gate it.

## Windows toolchain (UCRT64 for 6.1+)

The Windows all-in-one build migrated from MINGW64 to **MSYS2 UCRT64** in 6.1 (`NEWS`: "Migrate Windows AIO to MSYS2 UCRT64 environment. Fixes #14149."; commit `8be3e6bba0e01752078c7e40d471506d31e0fe2c` on `maintenance/gramps61`). The forcing reason was the new `pyproject.toml`-based build pulling `orjson`, whose `maturin` backend rejects the MINGW64 Python target triple.

For a core contributor this means:

- **6.1+ Windows work happens on UCRT64.** A 6.0 MINGW64 environment is the wrong toolchain for 6.1; don't assume DLL names, library paths, or build steps carry over from a 6.0 setup.
- The same NEWS cycle added "Skip bsddb tests on Windows" — a test-skip you'll encounter if a change of yours exercises the BSDDB backend; on Windows 6.1 the backend isn't present, so don't write a Windows test that assumes it.
- The testbed verifies Windows on UCRT64 for unit tests only; interface (AT-SPI/dogtail) tests are Linux-only (`INTEGRATION.md` §3, §Optional). A "verified" claim is honest only about the platforms the test actually ran on.

## Concrete 6.0 → 6.1 deltas

A few entries from `NEWS` (6.1.0-beta1) that bear on cross-version core work. The complete, authoritative list is `NEWS` on `maintenance/gramps61` — consult it rather than treating the table below as exhaustive.

| Delta | NEWS line | Why it matters cross-version |
|-------|-----------|------------------------------|
| Python floor 3.9 → **3.10** | "Update minimum python version. Python 3.9 reached EOL…" | 3.10+ syntax is now safe; 3.9 workarounds can be dropped |
| Windows AIO → **UCRT64** | "Migrate Windows AIO to MSYS2 UCRT64 environment. Fixes #14149." | 6.0 MINGW64 setups don't transfer to 6.1 |
| **Skip bsddb tests on Windows** | "Skip bsddb tests on Windows." | BSDDB backend absent on Windows 6.1 |
| **`pyproject.toml`** build system | "Convert to using a `pyproject.toml` based build system." | replaces the older build; pulls `orjson` (the UCRT64 forcing reason) |
| **mypy** config added; `py.typed` | "Add mypy configuration."; "Add `py.typed`…" | mypy is now CI-enforced for core ([[16-guidelines]] §Testing) |
| Default Gramps IDs → `%05d` | "Change the default gramps IDs to %05d." | user-facing ID width changed between minors |
| 6.0 directory compatibility kept | "Maintain compatibility with the directories used by Gramps 6.0." | a 6.1 install reuses 6.0 user directories |

For the retrospective, full-narrative version of what changed, see [[15-whats-new]]; for what's coming, [[17-roadmap]].

## See also

- [[15-whats-new]] — retrospective: the per-release change narrative.
- [[17-roadmap]] — prospective: what's planned for upcoming releases.
- [[07-api-reference]] — the API surface that deprecations and cross-version changes act on.
- [[16-guidelines]] — normative branch-target, testing, and verification rules cited throughout this page.
- `NEWS` on `maintenance/gramps61` — the authoritative changelog; the delta table above is a selection, not the whole list.

<!--wiki:{{stub}}-->
