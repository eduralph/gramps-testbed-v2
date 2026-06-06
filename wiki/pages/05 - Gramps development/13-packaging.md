---
title: "Gramps 6.1 Wiki Manual - Core Development - Building & releasing"
categories: [Developers, Gramps 6.1]
managed: true
---
<!--wiki:{{man index|6.1}}-->

<!--
  This page covers the build/install-from-source PIPELINE and the
  maintainer-run release process. The normative rules for a contributor
  (branch targeting, commit/PR shape, Mantis trailers, test-with-fix)
  live in [[16-guidelines]] — link there, don't restate.

  Authoritative scraped source for the release section:
  ../04 - Technical Documentation/what-to-do-for-a-release.md
-->

## Overview

This page covers how Gramps itself is built, installed from source, and released.

There is a sharp split in audience here, and it matters for what you do:

- **Building and installing from source** is something every core contributor does — to run the version they're patching. That's the first half of this page.
- **Cutting a release** is a *maintainer* task, run against the production branch on a coordinated timetable. A contributor's only role in a release is landing fixes on the right branch *before the freeze*. That's the second half.

The normative *rules* a fix must satisfy to be in that release (branch targeting, commit/PR shape, the test-with-fix requirement) live in [[16-guidelines]] — this page is the how-to and the calendar, not the MUST/SHOULD reference.

## Building from source

Gramps is pure Python: there is nothing to compile. "Building" means turning the source tree into installed resources (compiled translation catalogs, merged desktop/MIME/metainfo files, the man page, data files). The canonical reference is [`INSTALL`](https://github.com/gramps-project/gramps/blob/maintenance/gramps61/INSTALL) at the top of the checkout — read it before anything here.

### Run without installing

You don't have to install to run a working tree — and for development you generally shouldn't, so you don't overwrite a stable Gramps (see [running a development version](wiki:Running_a_development_version_of_Gramps)). From the source directory:

```bash
python Gramps.py
```

Or from anywhere, by pointing two environment variables at the checkout (`INSTALL`, "Running Gramps"):

```bash
export PYTHONPATH="/path/to/gramps:$PYTHONPATH"
export GRAMPS_RESOURCES="/path/to/gramps"
python -c 'from gramps.grampsapp import main; main()'
```

`GRAMPS_RESOURCES` is the same variable the test harness uses — `GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"` from the checkout root. See [[08-testing]] for the suite, [[02-get-started]] for first-run setup.

### Install with pip

```bash
sudo apt-get build-dep gramps   # dependencies, Debian/Ubuntu
pip install .
```

`pip install .` runs the project's `pyproject.toml` ([source](https://github.com/gramps-project/gramps/blob/maintenance/gramps61/pyproject.toml)), which uses the **hatchling** backend (`pyproject.toml:23-25`). The version is *not* hard-coded in the metadata — it is `dynamic` (`pyproject.toml:29`) and read from `gramps/version.py` by a custom metadata hook (`scripts/version_hook.py:38-41`). A second build hook does the actual asset compilation (`pyproject.toml:140-141`).

To install into a non-root prefix or staging dir, pass `--root` (`INSTALL`, "Custom directory installation"):

```bash
pip install . --root ~/test
```

### What the build hook produces

The build hook `scripts/build_hook.py` is what turns the source `data/` and `po/` trees into installable artifacts. On every wheel build it (`build_hook.py:43-53`):

| Step | Method | Reads | Writes |
|------|--------|-------|--------|
| Compile translations | `build_trans` | `po/<lang>.po` (per `po/LINGUAS`) | `build/share/locale/<lang>/LC_MESSAGES/gramps.mo` |
| Merge metadata | `build_intl` | `data/org.gramps_project.Gramps.{desktop,xml,metainfo.xml}.in` + `po/` | merged `.desktop` / MIME / metainfo files |
| Man page | `build_man` | `data/man/**/gramps.1.in` | versioned, gzipped `gramps.1` |
| Copy data | `copy_files` | `data/`, `images/`, `example/`, top-level docs | `build/share/...` |

The compiled `build/share` tree is mapped into the wheel as shared data (`pyproject.toml:143-144`). Translations come from `msgfmt`, so a source build needs gettext tools on `PATH`. The `test/` and `catalog/` trees are excluded from the wheel (`pyproject.toml:131-135`).

### The data/ and po/ trees

These two directories are the non-code half of the build, and the two you're most likely to touch as a contributor:

- **`data/`** — schema and runtime data files: `grampsxml.rng` / `grampsxml.dtd` (the Gramps XML schema), `holidays.xml`, `lds.xml`, `papersize.xml`, `tips.xml`, `authors.xml`, plus the `.in` templates merged at build time. Touching the XML schema is a compatibility-sensitive change — see [[14-compatibility]].
- **`po/`** — the gettext catalogs. `po/POTFILES.in` and `po/POTFILES.skip` list which source files are scanned for translatable strings; `po/LINGUAS` lists the shipped languages. **Both `POTFILES` lists are maintained by hand**: when you add a Python file with user-visible strings, add it to `POTFILES.in`; a file with none goes in `POTFILES.skip`. Validate with:

```bash
PYTHONPATH=../../gramps python po/test/po_test.py
```

The i18n discipline (wrap user strings with `_()`, `ngettext` for plurals) is normative — see [[16-guidelines]] §Translation and the [[12-internationalization]] how-to. This page only covers where those strings get *packaged*.

## Version and branch handling

The version lives in one place: `gramps/version.py`.

```python
DEV_VERSION = True
VERSION_TUPLE = (6, 1, 0)
VERSION_QUALIFIER = "-beta1"
```

— `gramps/version.py:20-22` on `maintenance/gramps61`. `DEV_VERSION` is the release/development toggle: when `True`, non-release builds append the git revision to the reported version; the maintainer flips it to `False` only for the moment a tag is cut, then back (`what-to-do-for-a-release.md`, "Working on VERSION" / "Update DEV_VERSION").

The two branches you care about:

| Branch | Role | What lands here |
|--------|------|-----------------|
| `maintenance/gramps61` | Current **production** branch (v6.1.0) | **All fixes** *and* code-cleanup, forward-merged to `master` |
| `master` | Next series | **Feature-only** |

This is the central branch rule and it is normative: fixes target `maintenance/gramps61`, not `master`, so they reach users via the next maintenance release sooner; only genuinely new-feature work targets `master` ([[16-guidelines]] §Contributor workflow, `doc16:119`; gramps-testbed `docs/INTEGRATION.md` §2). Do **not** PR `master` for a bug fix.

## Cutting a release (maintainer)

This is a condensed map of the maintainer checklist [What to do for a release](wiki:What_to_do_for_a_release); the wiki page is authoritative and longer. The shape is **freeze → translate → tag → build → announce**.

### 1. Freezes

For a major release the maintainer announces two freezes on *gramps-devel*, on a coordinated timetable:

| Freeze | Lead time | Effect on contributors |
|--------|-----------|------------------------|
| **Feature freeze** | ~4 weeks before release | No new features; **fixes only** from here |
| **String freeze** | ~2 weeks before release | No changes to translatable strings, so translators can finish |

This is where a contributor's window closes. **Land your fix on `maintenance/gramps61` before the feature freeze** for it to be in the release. A string change must be in before the *string* freeze or translators can't catch it. After the string freeze, only non-string fixes are accepted.

### 2. Translation update

Just before the string freeze, the maintainer refreshes the template. New source files are picked up into `POTFILES.in` / `POTFILES.skip` (the same hand-maintained lists from above), then:

```bash
python update_po.py -p          # regenerate po/gramps.pot
python update_po.py -k all      # sanity-check existing catalogs
```

`gramps.pot` is committed and pushed; Weblate produces updated `.po` files and a PR to merge back (`what-to-do-for-a-release.md`, "Translation update"). A translation falling below the 70% completion threshold is dropped from the shipped set.

### 3. Housekeeping before the tag

- About-box / copyright year in `gramps/gen/const.py` (`const.py:261`, `COPYRIGHT_MSG`).
- API-docs copyright year in `docs/conf.py`.
- The PyPI **Development Status** classifier in `pyproject.toml` (`pyproject.toml:47-48`, currently `4 - Beta`).
- `ChangeLog` + `NEWS` (generated from `git log` via `git2cl`, then `NEWS` hand-edited).
- An entry in `data/org.gramps_project.Gramps.metainfo.xml.in`.

### 4. Tag and build

With a clean checkout of the production branch, set `DEV_VERSION = False`, commit "Release Gramps x.y.z", verify with `python Gramps.py -v`, then tag (note the leading `v`) and push:

```bash
git commit -am "Release Gramps 6.1.0"
git tag -am "Tag 6.1.0" v6.1.0
git push origin v6.1.0
```

GitHub auto-generates a tarball on the tag push. A source distribution can also be built locally with the same `python -m build --sdist` that `INSTALL` documents for packagers:

```bash
python -m build --sdist          # produces dist/gramps-*.tar.gz
sha256sum gramps-6.1.0.tar.gz    # checksum for the release notes
```

Immediately after, the maintainer reverts `DEV_VERSION` back to `True` and commits "Set to development version" so subsequent builds report a dev version.

### 5. Announce and post-release

Publish the GitHub release (NEWS contents + sha256sum), upload to SourceForge, enable the version in Mantis for bug reporting, and announce on the mailing lists, Discourse, and the blog. Post-release, the `NEWS` file is merged forward. The full announcement matrix is in [What to do for a release](wiki:What_to_do_for_a_release), "Announcing the new release".

## Platform builds (high level)

The `pip install .` / sdist flow above is the source distribution. The downloadable installers most users run are separate, maintainer/packager-run builds, coordinated with the [package maintainers](wiki:Team#Package_Maintainers) on the same release timetable:

| Platform | Build | Notes |
|----------|-------|-------|
| **Windows** | Gramps AIO (All-In-One) | A bundled installer built under MSYS2 **UCRT64**; see [Building Gramps AIO](wiki:Building_Gramps_AIO_cx_freeze-based). The Windows unit-test matrix runs under this toolchain. |
| **macOS** | `.dmg` bundle | Built by the macOS package maintainer. |
| **Linux** | Distro packages + Flatpak | Built downstream by distro packagers from the sdist / metainfo. |

These are out of scope for a code contributor — the relevant fact is that each platform packager pulls from the *same tagged source* on `maintenance/gramps61`, so a fix that's on that branch at freeze time flows into every platform build. The interface test matrix and its platform limits (AT-SPI is Linux-only) are described in `docs/INTEGRATION.md` §3.

## See also

- [[02-get-started]] — clone, run from source, first-run setup.
- [[08-testing]] — the `*_test.py` suite the build excludes from the wheel.
- [[12-internationalization]] — wrapping strings so they reach the `po/` catalogs this page packages.
- [[14-compatibility]] — picking the right branch, and what counts as a schema/compatibility-sensitive change.
- [[16-guidelines]] — the normative rules a fix must satisfy to ride a release.
- [What to do for a release](wiki:What_to_do_for_a_release) — the authoritative maintainer checklist.
- [Building Gramps AIO](wiki:Building_Gramps_AIO_cx_freeze-based) — the Windows All-In-One build.

<!--wiki:{{stub}}-->
