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
"""T2 — Shape conformance (the *static code-shape* tier of T1–T4, founded on
wiki doc 16 §Coding style).

T2 is the AST/text-level scanner: rules that can be decided by reading the
source, no runtime needed (that is T3). Each rule is cited ``doc16:LINE`` back
to ``wiki/pages/06 - Addon development/16-guidelines.md``.

Per ``.py`` file:

  * MUST: a GPL-2.0-or-later licence header with copyright               doc16:99
  * MUST NOT: ``print()`` for diagnostic output (use a module logger)    doc16:71

CLI::

    t2_shape.py <path> [<path> …]        # files or directories (recursed)

Prints one ``T2 ✗ …`` line per MUST violation; exits 1 iff any was found.
``black --check`` (doc16:106, SHOULD) is intentionally NOT run here — it is a
formatter gate, run separately when the target repo enforces it; type hints /
docstrings / ``cb_`` prefixes (doc16:101-105, SHOULD) are reviewer judgment, not
mechanised, to keep T2 false-positive-free.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

# A GPL header is present if any of these markers appears in the file's head.
_GPL_MARKERS = (
    "GNU General Public License",
    "SPDX-License-Identifier: GPL",
    "under the terms of the GNU",
)
_HEADER_LINES = 40  # licence headers sit at the very top of the file

# A diagnostic print: ``print(`` not inside a comment. We do not try to prove a
# given print is "diagnostic" vs "output" — doc16:71 is a blanket MUST NOT for
# diagnostics, and as an advisory gate the human weighs any report-sink case.
_PRINT = re.compile(r"^\s*print\s*\(")


def check_file(path: str) -> list[str]:
    """Return the list of MUST violations (each citing ``doc16:LINE``) for one file."""
    violations: list[str] = []
    name = os.path.basename(path)
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as exc:  # unreadable file — surfaced, not swallowed
        return [f"{name}: unreadable ({exc})"]

    head = "".join(lines[:_HEADER_LINES])
    if not any(m in head for m in _GPL_MARKERS):
        violations.append(f"{name}: no GPL licence header in the first "
                          f"{_HEADER_LINES} lines (doc16:99)")

    for ln, line in enumerate(lines, 1):
        if _PRINT.match(line):
            violations.append(f"{name}:{ln} print() for diagnostics — use a "
                              f"module logger (doc16:71)")
    return violations


def _iter_py(paths: list[str]):
    for p in paths:
        if os.path.isfile(p) and p.endswith(".py"):
            yield p
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for f in sorted(files):
                    if f.endswith(".py"):
                        yield os.path.join(root, f)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="T2 Shape conformance (doc 16 §Coding style)")
    ap.add_argument("paths", nargs="+", help="Python files or directories")
    ns = ap.parse_args(argv)

    violations: list[str] = []
    checked = 0
    for path in _iter_py(ns.paths):
        checked += 1
        violations += check_file(path)

    for line in violations:
        print(f"T2 ✗ {line}")
    if not violations:
        print(f"T2 ✓ shape: {checked} file(s) conform to doc 16 §Coding style")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
