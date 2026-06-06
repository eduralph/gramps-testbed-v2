---
title: "Gramps 6.1 Wiki Manual - Core Development - What's new"
categories: [Developers, Gramps 6.1]
managed: true
---

<!--wiki:{{man index|6.1}}-->

## Overview

Per-Gramps-version changes that affect **core** contributors — API and behaviour
deltas in `gramps-project/gramps`. The audience is someone with a working knowledge
of the previous minor asking *"what moved under me, and what do I need to change
before my code builds and passes CI on this release?"*

This is the developer-facing counterpart to [[17-roadmap]]: the roadmap looks
forward at intended direction, this page looks backward at what already landed. It
is the inventory; [[14-compatibility]] is the procedure for actually porting code
across these releases.

This page is deliberately a **structured pointer**, not a replacement for the change
log. The authoritative, exhaustive record is the in-tree `NEWS` file on the target
branch ([`gramps/NEWS`](https://github.com/gramps-project/gramps/blob/maintenance/gramps61/NEWS));
the entries here are filtered down to the ones a core developer has to *act* on — an
API rename, a build-system swap, a new static-analysis gate — and skip the
user-facing feature and translation churn that fills most of `NEWS`.

## How to read this page

Each entry is one verifiable change, written as four fields:

| Field | What it tells you |
|-------|-------------------|
| **Version** | the minor release the change landed in (section heading) |
| **Change** | what moved, in one line |
| **Impact on dev / API** | what *you* must do differently — the actionable part |
| **Source** | where it is verifiable: a commit hash, a `Fixes #NNNN` from `NEWS`, or `path:line` on `maintenance/gramps61` |

Conventions:

- Sections are **incremental** — an entry describes the delta *from the previous
  minor*, not the cumulative API surface.
- Every entry cites an auditable origin. A commit hash or `Fixes #NNNN` comes
  straight from `NEWS`; a `path:line` was confirmed against the checkout on
  `maintenance/gramps61`. Where specifics could not be pinned to a verifiable
  source, the entry is a marked outline with a `TODO` pointing at `NEWS` rather than
  an invented detail — mirror that discipline when you extend this page.
- The **normative** rules (what you MUST/SHOULD do) live in [[16-guidelines]]; this
  page is the *what changed* explainer, not the rule reference. Where an entry has a
  rule consequence, it links to the relevant [[16-guidelines]] section rather than
  restating it.
- The *current* state of any surface (what exists right now) is the source on the
  target branch, not this page.

## Gramps 6.1

Targeted from `maintenance/gramps61` (the current production branch), forward-merged
to `master`; see [[16-guidelines]] → Contributor workflow for branch targeting. The
6.1.0-beta1 entry in `NEWS` is dated 2026-04-21.

### Build / toolchain

- **Build system converted to `pyproject.toml`.** Gramps moved off its older build
  scripts to a `pyproject.toml`-based build.
  - *Impact:* build and install invocation changes; package metadata
    (including the minimum Python, below) now lives in `pyproject.toml`. If you
    script a from-source build, re-read it. See [[14-compatibility]].
  - *Source:* commit `6233d44744` ("Convert to using a `pyproject.toml` based build
    system"); `pyproject.toml` at repo root.

- **Minimum Python is now 3.10.** Python 3.9 reached end-of-life in October 2025 and
  is no longer supported.
  - *Impact:* you can rely on 3.10+ language features unconditionally — `X | None`
    instead of `Optional[X]`, `list[X]` instead of `typing.List[X]` — with no
    compatibility shim. This is exactly what the type-hint rule in [[16-guidelines]]
    → Coding style now requires.
  - *Source:* `requires-python = ">= 3.10"` (`pyproject.toml:41`); `NEWS` 6.1.0-beta1
    ("Update minimum python version. Python 3.9 reached EOL in October 2025.").

- **Windows AIO migrated to MSYS2 UCRT64.** The Windows all-in-one build moved off
  MINGW64 to the MSYS2 UCRT64 environment.
  - *Impact:* if you build or test on Windows, the MINGW64 environment is gone; use
    UCRT64. Windows is upstream-tested on `maintenance/gramps61` and `master` only.
  - *Source:* `NEWS` 6.1.0-beta1 ("Migrate Windows AIO to MSYS2 UCRT64 environment.
    Fixes #14149.").

### Static analysis

- **mypy is now part of the codebase.** A mypy configuration was added and the tree
  is being typed (`py.typed` marker added).
  - *Impact:* `mypy` is **enforced in CI** — changed files must pass it. It reads
    `mypy.ini` (`files = ./gramps, ./test`, with `*.gpr.py` excluded). Type-hint all
    new functions and methods. This is the gate behind the mypy MUST in
    [[16-guidelines]] → Testing.
  - *Source:* `files = ./gramps, ./test` (`mypy.ini:2`); `py.typed` at repo root;
    `NEWS` 6.1.0-beta1 ("Add mypy configuration." / "Add `py.typed` to indicate the
    code base is (becoming) typed.").

- **`AGENTS.md` added as the in-repo coding standard.** A contributor/agent guideline
  file landed at the repo root.
  - *Impact:* `AGENTS.md` is now the **native, authoritative** core coding standard —
    the source [[16-guidelines]] restates. When this wiki and `AGENTS.md` disagree on
    the target branch, `AGENTS.md` wins ([[16-guidelines]] → Repository scope).
  - *Source:* commit `3eda7b1e49` ("Add AGENTS.md with contributor and agent
    guidelines", 2026-03-25); `AGENTS.md` at repo root.

### API changes

- **`apply()` renamed to `apply_to_one()` on filter rules.** The per-object filter
  entry point was renamed to reflect a global change made in v6.0.
  - *Impact:* if you implement or call a filter rule's single-object test, use
    `apply_to_one(db, data)`; the bare `apply()` name no longer carries that meaning.
    The filter-*level* `apply()` (the whole-database run) is a separate method and
    remains.
  - *Source:* commit `b326c20c92` ("Rename apply to apply_to_one to reflect global
    change in v6.0"); `gramps/gen/filters/_genericfilter.py:232`
    (`def apply_to_one(self, db, data: dict) -> bool:`),
    `gramps/gen/filters/rules/_rule.py:162`.

- **Core library decoupled from GObject introspection.** Work landed to remove the
  hard dependency on GI from the core library code.
  - *Impact:* reinforces the long-standing rule that `gramps.gen.*` is the headless,
    GUI-free core — `gen` must not pull in GUI/GI machinery. See [[16-guidelines]] →
    Source structure (the `gen` self-containment MUST).
  - *Source:* commit `5007d76023` ("Decouple the core library code from GObject
    introspection").

### Behaviour / fixes (developer-relevant)

- **bsddb tests skipped on Windows.** The unit-test suite now skips BSDDB tests where
  the backend is unavailable.
  - *Impact:* if you write a test that exercises the BSDDB backend, guard it (e.g.
    `@unittest.skipUnless(...)`) so it doesn't fail on a tree without bsddb. Test
    layout itself is unchanged — core stays `test/` + `<module>_test.py`
    ([[16-guidelines]] → Testing).
  - *Source:* `NEWS` 6.1.0-beta1 ("Skip bsddb tests on Windows.").

<!-- TODO: more 6.1 developer-facing API/behaviour deltas remain unverified in this
     pass. Before adding any, confirm against NEWS on maintenance/gramps61 and the
     checkout. Candidates spotted in NEWS that need a verifiable path:line or commit
     before they earn an entry here:
       - "Pass an object rather than a handle to the note editor callback." (Fixes
         #13702, #13884) — callback-signature change; verify the affected callable.
       - "Replace hexlify with `getSortKey()` bytes, drop binascii import." (Bug
         #10077) — sort-key API; verify the symbol and module.
       - "Rename apply to apply_to_one" interplay with "Require User in filter
         apply()" (commit 19f63037ba) — the User argument may now be required on the
         filter-level apply(); verify the signature before documenting.
     Do NOT promote these out of this comment without a green grep / commit. -->

### Deprecated / Removed

*None verified in this pass.* The authoritative list of runtime deprecations is the
source: grep `gramps/gen/**/*.py` on `maintenance/gramps61` for `DeprecationWarning`.
See [[14-compatibility]] for the recipe.

<!-- TODO: scan NEWS on maintenance/gramps61 for explicit "Remove …" entries that
     drop a public symbol or module (developer-relevant removals), and add verified
     entries here. The MINGW64 gitignore removal in NEWS is build cleanup, not an API
     removal — do not list it as a Removed API. -->

## Earlier releases (6.0 and before)

6.0 was the major release that set this manual's baseline. The developer-facing
highlights a core contributor still meets in the codebase:

- **SQLite is the default database backend** (since 6.0). Code that goes through the
  `gramps.gen.db.*` abstraction is unaffected; code that reached into BSDDB-specific
  APIs had to migrate to the portable interface.
- **Python 3.10+** became the floor at 6.0 and is carried into 6.1 (above).

The 5.x → 6.0 transition was a major release with broad API churn. The authoritative
reference for cross-major deltas is the upstream
[release-notes pages](https://www.gramps-project.org/wiki/index.php/Portal:Using_Gramps#Release_notes)
and the `NEWS` history on the relevant branch — not this page, which tracks per-minor
developer deltas from 6.0 forward.

<!-- TODO: if a 6.0.x point release introduced a developer-facing API/behaviour
     change worth flagging, add a verified entry. The 6.0.x sections of NEWS are
     mostly user-facing fixes and translations; confirm before promoting anything. -->

## See also

- [[14-compatibility]] — how to actually port core code across these releases; the
  procedural companion to this inventory.
- [[17-roadmap]] — the forward-looking counterpart: intended direction, not landed
  change.
- [[16-guidelines]] — the normative MUST/SHOULD reference these entries point into.
- `gramps/AGENTS.md` — the native, in-repo coding standard (added in 6.1; see above).
- [`gramps/NEWS`](https://github.com/gramps-project/gramps/blob/maintenance/gramps61/NEWS)
  — the full in-tree change log on the target branch (this page is a filtered slice).
- [Portal:Using Gramps → Release notes](https://www.gramps-project.org/wiki/index.php/Portal:Using_Gramps#Release_notes)
  — upstream release notes (full, not developer-filtered).

<!--wiki:{{stub}}-->
