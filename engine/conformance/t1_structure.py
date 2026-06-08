#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Gramps Testbed v2 — conformance engine
#
# Copyright (C) 2026  Eduard Ralph
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <https://www.gnu.org/licenses/>.
#
"""T1 — Structure conformance (the *structural* tier of the T1–T4 conformance
ladder, founded on wiki doc 16, "Addon Development — Rules").

These are addon-packaging rules; they apply to an **addon** contribution only (a
core-only patch is N/A — the gate handles that). Each rule is a **MUST** from the
addon guideline's §Structure, cited by **section** (not line number) via
:mod:`doc16` so the anchor survives edits to the vendored page (testbed issue #6).

Checks one addon directory against the §Structure MUST rules (all cite
``doc16-addon §Structure``):

  * folder name is a valid Python import identifier
  * ``.gpr.py`` declares ``gramps_target_version``
  * ``fname`` points to a module shipped in the same folder
  * NO ``__init__.py`` in the addon dir (Mantis 12691 trap)
  * does NOT import a Gramps-injected name in ``.gpr.py``
  * (SHOULD) ships ``tests/`` with an ``__init__.py`` marker

CLI::

    t1_structure.py <addon-dir> [<addon-dir> …]

Prints one ``T1 ✗ …`` line per violation (MUST) and ``T1 ⚠ …`` per advisory
(SHOULD); exits 1 iff any MUST violation was found, else 0.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys

import doc16

# Every T1 MUST is a §Structure rule of the addon guideline.
_CITE = doc16.cite("addon", "Structure")

# Names Gramps injects into the .gpr.py namespace — importing them is a defect.
# ``_`` is handled separately (``import _`` exact match).
_INJECTED = ("register", "GRAMPLET", "STABLE", "UNSTABLE", "EXPERIMENTAL")


def _gpr_text(gprs: list[str]) -> str:
    out = []
    for g in gprs:
        with open(g, encoding="utf-8", errors="replace") as fh:
            out.append(fh.read())
    return "\n".join(out)


def check_addon(addon_dir: str) -> tuple[list[str], list[str]]:
    """Return ``(violations, advisories)`` for one addon directory.

    ``violations`` are MUST breaches (gate-relevant); ``advisories`` are SHOULD
    breaches (informational). Both name the addon and cite ``doc16-addon §Structure``.
    """
    must: list[str] = []
    should: list[str] = []
    name = os.path.basename(os.path.normpath(addon_dir))

    gprs = sorted(glob.glob(os.path.join(addon_dir, "*.gpr.py")))
    if not gprs:
        must.append(f"{name}: no .gpr.py — addon registers via .gpr.py ({_CITE})")
        return must, should
    text = _gpr_text(gprs)

    # MUST — folder name is a valid Python import identifier. Gramps puts each
    # addon dir on sys.path and shares code across addons via ``import <Folder>``
    # (wiki "04 - Technical Documentation/addons-development.md"), so the folder
    # name must be importable. The registration ``id`` is an independent plugin
    # key and need NOT match the folder — ~25% of addons-source declare a
    # spaced/human-readable id (e.g. folder DeepConnectionsGramplet ↔ id
    # "Deep Connections Gramplet"), and a folder may bundle several unrelated ids.
    if not name.isidentifier():
        must.append(
            f"{name}: folder name is not a valid Python import identifier "
            f"({_CITE})"
        )

    # MUST — gramps_target_version is declared.
    if not re.search(r"\bgramps_target_version\s*=", text):
        must.append(f"{name}: .gpr.py declares no gramps_target_version ({_CITE})")

    # MUST — every fname points to a module present in the folder.
    for fn in re.findall(r"""\bfname\s*=\s*["']([^"']+)["']""", text):
        if not os.path.isfile(os.path.join(addon_dir, fn)):
            must.append(
                f"{name}: fname '{fn}' is not a file in the addon folder ({_CITE})"
            )

    # MUST NOT — an __init__.py in the addon dir itself breaks the plugin loader
    # (the Mantis 12691 submodule-binding trap).
    if os.path.isfile(os.path.join(addon_dir, "__init__.py")):
        must.append(
            f"{name}: addon dir has __init__.py — breaks plugin loading "
            f"({_CITE}, Mantis 12691)"
        )

    # MUST NOT — import a name Gramps injects into the .gpr.py namespace.
    injected = re.compile(
        r"^\s*(?:import\s+_(?:\s|$)"
        r"|from\s+\S+\s+import\s+.*\b(?:" + "|".join(_INJECTED) + r")\b"
        r"|import\s+(?:" + "|".join(_INJECTED) + r")\b)"
    )
    for g in gprs:
        with open(g, encoding="utf-8", errors="replace") as fh:
            for ln, line in enumerate(fh, 1):
                if injected.match(line):
                    must.append(
                        f"{name}: {os.path.basename(g)}:{ln} imports a "
                        f"Gramps-injected name ({_CITE})"
                    )

    # SHOULD — ship a tests/ package with an __init__.py marker.
    tests_dir = os.path.join(addon_dir, "tests")
    if not os.path.isdir(tests_dir):
        should.append(f"{name}: no tests/ package ({_CITE}, SHOULD)")
    elif not os.path.isfile(os.path.join(tests_dir, "__init__.py")):
        should.append(
            f"{name}: tests/ lacks the __init__.py marker ({_CITE}, SHOULD)"
        )

    return must, should


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="T1 Structure conformance (doc 16 §Structure)")
    ap.add_argument("addon_dirs", nargs="+", help="addon directories to check")
    ns = ap.parse_args(argv)

    violations: list[str] = []
    advisories: list[str] = []
    checked = 0
    for d in ns.addon_dirs:
        if not os.path.isdir(d):
            continue
        checked += 1
        must, should = check_addon(d)
        violations += must
        advisories += should

    for line in violations:
        print(f"T1 ✗ {line}")
    for line in advisories:
        print(f"T1 ⚠ {line}")
    if not violations:
        print(
            f"T1 ✓ structure: {checked} addon(s) conform to doc 16 §Structure"
            + (f" ({len(advisories)} advisory)" if advisories else "")
        )
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
