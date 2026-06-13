#!/usr/bin/env python3
"""
Single source of truth for addon *Python* dependencies (``requires_mod``).

Sibling to ``addon_system_deps.py`` (which covers the *system* deps —
``requires_gi`` typelibs and ``requires_exe`` executables). This module covers
the third kind a Gramps addon declares in its ``.gpr.py``:

* ``requires_mod`` — importable Python module names (e.g. ``["psycopg2"]``,
  ``["life_line_chart", "svgwrite"]``). These are *import* names (doc 16
  §Runtime), which are not always the PyPI *distribution* name, so the union is
  mapped to installable names via ``_IMPORT_TO_DISTRIBUTION`` (e.g. PIL→Pillow).

The addon-unit CI jobs (``addon-unit-tests.yml`` and
``windows-addon-unit-tests.yml``) install these before running each addon's
test suite. Both jobs previously inlined an identical
``requires_mod\\s*=\\s*(\\[[^\\]]*\\])`` heredoc; that copy-paste is the drift
this module removes — the ``.gpr.py`` files stay the single source of truth and
both platforms now derive the list from one place.

Scanning approach matches ``addon_system_deps.py`` deliberately: a regex to
find each ``requires_mod = [...]`` assignment, then ``ast.literal_eval`` on the
bracketed list. Both sibling scanners therefore use the same mechanism, and the
module stays pure stdlib (no Gramps import, no executing the ``.gpr.py``), so it
can run at image-build time before Gramps is installed. Every real
``requires_mod`` in addons-source is a flat string literal, so a literal-eval
parse covers them all; a non-literal or unreadable declaration is skipped
tolerantly (logged to stderr) rather than aborting the batch — mirroring the
old inline behaviour.

A declared ``requires_mod`` value is the *importable module* name Gramps
verifies at runtime via ``importlib.util.find_spec`` (``gramps/gen/utils/
requirements.py`` ``Requirements.check_mod`` does ``find_spec(module)`` on the
declared name). The PIL→Pillow mapping above is *install-only*: it never
changes what an addon declares. So an addon that declares the PyPI
*distribution* name by mistake (``requires_mod=["Pillow"]``) pip-installs fine
yet ``find_spec("Pillow")`` is ``None`` — Gramps would silently treat the addon
as missing its dependency. ``unresolved_requires_mod`` re-runs exactly Gramps'
``check_mod`` resolution over every declared name (the *raw* import name, before
the install map) so CI can reject such a declaration; see
``run-addon-unit.sh``'s "addon requires_mod resolution" gate, which calls this
*after* the deps are pip-installed.

CLI::

    addon_python_deps.py <addons-source-dir>     # space-separated sorted union
    addon_python_deps.py --check-resolves <dir>  # fail if a declared name is
                                                 # installed but not importable
"""

from __future__ import annotations

import argparse
import ast
import glob
import importlib.util
import os
import re
import sys

# Matches a single-line ``requires_mod = ["a", "b"]`` assignment. Flat string
# lists only — the same shape addon_system_deps.py's _GI_RE/_EXE_RE assume, and
# the only shape that occurs in addons-source.
_MOD_RE = re.compile(r"requires_mod\s*=\s*(\[[^\]]*\])")

# ``requires_mod`` holds the *importable module* name (doc 16 §Runtime: declare
# "PIL", the import name, NOT "Pillow", the PyPI distribution — Gramps verifies it
# with ``importlib.util.find_spec``). But ``pip install`` wants the *distribution*
# name, which differs for some packages, so installing the raw import name fails
# (``pip install PIL`` → no such distribution; the package is ``Pillow``). Map the
# known import→distribution cases so the derived install list resolves on PyPI.
# Addons stay correct (import name); only the install side translates.
_IMPORT_TO_DISTRIBUTION = {
    "PIL": "Pillow",
}


def _gpr_files(addons_dir: str) -> list[str]:
    return sorted(glob.glob(os.path.join(addons_dir, "*", "*.gpr.py")))


def _declared_mods(text: str, path: str) -> list[str]:
    """The *raw* (un-mapped) ``requires_mod`` import names declared in one
    ``.gpr.py`` body. Tolerant: a non-literal value is skipped with a note to
    stderr, mirroring the old inline behaviour. Shared by both the install
    union and the resolution check so they read the declarations identically.
    """
    out: list[str] = []
    for m in _MOD_RE.finditer(text):
        try:
            value = ast.literal_eval(m.group(1))
        except (ValueError, SyntaxError):
            print(f"addon_python_deps: skipping non-literal requires_mod "
                  f"in {path}: {m.group(1)!r}", file=sys.stderr)
            continue
        for mod in value:
            if mod:
                out.append(mod)
    return out


def requires_mod_by_addon(addons_dir: str) -> dict[str, list[str]]:
    """Map each addon directory name to the *raw* import names it declares in
    ``requires_mod`` (the names Gramps verifies via ``find_spec`` — NOT the
    install-mapped distribution names). Unreadable files are skipped with a
    note to stderr; an addon with no declaration is omitted.
    """
    by_addon: dict[str, list[str]] = {}
    for path in _gpr_files(addons_dir):
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            print(f"addon_python_deps: skipping unreadable {path}: {exc}",
                  file=sys.stderr)
            continue
        mods = _declared_mods(text, path)
        if mods:
            addon = os.path.basename(os.path.dirname(path))
            by_addon.setdefault(addon, []).extend(mods)
    return by_addon


def requires_mod_union(addons_dir: str) -> list[str]:
    """Return the sorted union of ``requires_mod`` across every addon's
    ``.gpr.py`` under *addons_dir*, mapped to pip *distribution* names.

    Best-effort and tolerant: a file that cannot be read, or a
    ``requires_mod`` value that is not a literal list, is skipped (with a note
    to stderr) instead of aborting — the addon-unit jobs would rather install
    the modules they *can* resolve than fail the whole step on one odd file.
    """
    mods: set[str] = set()
    for path in _gpr_files(addons_dir):
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            print(f"addon_python_deps: skipping unreadable {path}: {exc}",
                  file=sys.stderr)
            continue
        for mod in _declared_mods(text, path):
            mods.add(_IMPORT_TO_DISTRIBUTION.get(mod, mod))
    return sorted(mods)


def unresolved_requires_mod(addons_dir: str) -> list[tuple[str, str]]:
    """Return ``(addon, module)`` pairs whose declared ``requires_mod`` import
    name does NOT resolve under ``importlib.util.find_spec`` — the same check
    Gramps' ``Requirements.check_mod`` performs at runtime
    (``gramps/gen/utils/requirements.py``).

    This is the name-resolution gate: run it *after* the install union has been
    pip-installed, so a name that still fails ``find_spec`` is a genuinely
    wrong declaration (e.g. the PyPI distribution ``"Pillow"`` instead of the
    import name ``"PIL"``: pip installs it but ``find_spec("Pillow")`` is
    ``None``), not merely a not-yet-installed one. The declared name is checked
    verbatim — NOT the install-mapped distribution name — because that is what
    Gramps imports. Sorted by ``(addon, module)``; empty list == all resolve.
    """
    bad: list[tuple[str, str]] = []
    for addon, mods in requires_mod_by_addon(addons_dir).items():
        for mod in mods:
            if importlib.util.find_spec(mod) is None:
                bad.append((addon, mod))
    return sorted(set(bad))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "addons_dir",
        help="path to the addons-source checkout (scans <dir>/*/*.gpr.py)",
    )
    parser.add_argument(
        "--check-resolves",
        action="store_true",
        help="instead of printing the install union, verify every declared "
        "requires_mod import name resolves under importlib.util.find_spec "
        "(Gramps' check_mod). Prints each addon + bad name and exits 1 if any "
        "declared name installs but does not import; 0 if all resolve.",
    )
    args = parser.parse_args(argv)
    if args.check_resolves:
        bad = unresolved_requires_mod(args.addons_dir)
        for addon, mod in bad:
            print(
                f"× {addon}: requires_mod={mod!r} is not importable "
                f"(find_spec returned None) — declare the import name Gramps "
                f"verifies, not the PyPI distribution name",
                file=sys.stderr,
            )
        return 1 if bad else 0
    print(" ".join(requires_mod_union(args.addons_dir)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
