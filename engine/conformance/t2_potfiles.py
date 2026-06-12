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
"""T2 — POTFILES registration (the *Adding and removing Python files* MUST).

doc 16 §Adding and removing Python files (sourced to ``gramps/AGENTS.md``
§Translation Files) is a **core** MUST:

  * a core PR that **adds** a ``.py`` file MUST list it in ``po/POTFILES.in``
    (the file has translatable strings) or ``po/POTFILES.skip`` (it has none);
  * a core PR that **deletes** a ``.py`` file MUST remove its reference from
    **both** lists.

This is a *contribution*-level check (the evidence is the patch, not a file on
disk): when the bundle-scoped gates run, a file the patch *adds* does not yet
exist in the checkout, so the registration is verified by reading the patch —
the new ``.py`` paths and the lines the same patch adds to / removes from the
two ``POTFILES`` manifests. An ``already_listed`` set (the manifests' current
on-disk contents) is folded in so a re-added path that is already listed passes
and a deletion is only required to deregister a path that was actually there.

Addon-only: the rule is core's; addons carry their own translation handling, so
the dispatcher invokes this for a **core**-target bundle only. Cited by section
heading via :mod:`doc16` so the anchor survives source edits (issue #6).
Advisory, like the rest of the T1/T2/T4 ladder.
"""

from __future__ import annotations

import argparse
import os
import sys

import doc16

_CITE = doc16.cite("core", "Adding and removing Python files")

_POTFILES = ("po/POTFILES.in", "po/POTFILES.skip")


class _FileDiff:
    __slots__ = ("bpath", "apath", "is_new", "is_deleted", "added", "removed")

    def __init__(self, bpath: str, apath: str) -> None:
        self.bpath = bpath
        self.apath = apath
        self.is_new = False
        self.is_deleted = False
        self.added: list[str] = []    # content lines added (without the leading '+')
        self.removed: list[str] = []  # content lines removed (without the leading '-')


def _parse_diff(text: str) -> list[_FileDiff]:
    """Split a unified ``git diff`` into per-file records (paths, new/deleted
    flags, and the added/removed content lines of each hunk)."""
    files: list[_FileDiff] = []
    cur: _FileDiff | None = None
    for line in text.splitlines():
        if line.startswith("diff --git "):
            # 'diff --git a/<p> b/<p>' — take both sides (paths may contain spaces
            # only in pathological cases; the b-side is re-confirmed by '+++').
            parts = line.split(" ")
            a = parts[2][2:] if len(parts) > 2 and parts[2].startswith("a/") else ""
            b = parts[3][2:] if len(parts) > 3 and parts[3].startswith("b/") else a
            cur = _FileDiff(b, a)
            files.append(cur)
        elif cur is None:
            continue
        elif line.startswith("new file mode"):
            cur.is_new = True
        elif line.startswith("deleted file mode"):
            cur.is_deleted = True
        elif line.startswith("--- "):
            tail = line[4:]
            if tail != "/dev/null" and tail.startswith("a/"):
                cur.apath = tail[2:]
        elif line.startswith("+++ "):
            tail = line[4:]
            if tail != "/dev/null" and tail.startswith("b/"):
                cur.bpath = tail[2:]
        elif line.startswith("+") and not line.startswith("+++"):
            cur.added.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            cur.removed.append(line[1:])
    return files


def _listed_paths(lines: list[str]) -> set[str]:
    """The file paths a POTFILES hunk lists (skip blanks and ``#`` comments)."""
    out: set[str] = set()
    for ln in lines:
        s = ln.strip()
        if s and not s.startswith("#"):
            out.add(s)
    return out


def check_patch(patch_text: str, *, already_listed: set[str] | None = None) -> list[str]:
    """Return the POTFILES-registration MUST violations for a core patch.

    ``already_listed`` is the union of the current on-disk ``POTFILES.in`` /
    ``POTFILES.skip`` entries (optional); it lets a path that is *already* listed
    satisfy the add rule, and scopes the delete rule to paths that were there.
    """
    already = already_listed or set()
    files = _parse_diff(patch_text)

    registered_add: set[str] = set()
    registered_del: set[str] = set()
    for f in files:
        if f.bpath in _POTFILES or f.apath in _POTFILES:
            registered_add |= _listed_paths(f.added)
            registered_del |= _listed_paths(f.removed)

    violations: list[str] = []
    for f in files:
        if f.is_new and f.bpath.endswith(".py"):
            if f.bpath not in registered_add and f.bpath not in already:
                violations.append(
                    f"new core file {f.bpath} is not registered in po/POTFILES.in "
                    f"or po/POTFILES.skip ({_CITE})"
                )
        elif f.is_deleted and f.apath.endswith(".py"):
            if f.apath in already and f.apath not in registered_del:
                violations.append(
                    f"deleted core file {f.apath} is still referenced in "
                    f"po/POTFILES.* — remove it from both ({_CITE})"
                )
    return violations


def listed_on_disk(core_root: str) -> set[str]:
    """Union of the paths currently listed in ``<core_root>/po/POTFILES.{in,skip}``
    (empty if the manifests are absent — the checker then relies on the patch)."""
    out: set[str] = set()
    for name in _POTFILES:
        p = os.path.join(core_root, name)
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                out |= _listed_paths(fh.read().splitlines())
        except OSError:
            pass
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="T2 POTFILES registration (doc 16 §Adding and removing Python files)"
    )
    ap.add_argument("patch", help="path to the bundle's patch.diff")
    ap.add_argument("--core-root", default="",
                    help="gramps checkout root (to read current POTFILES.{in,skip})")
    ns = ap.parse_args(argv)

    try:
        with open(ns.patch, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"T2 ✗ potfiles: unreadable patch ({exc})", file=sys.stderr)
        return 2

    already = listed_on_disk(ns.core_root) if ns.core_root else set()
    violations = check_patch(text, already_listed=already)
    for v in violations:
        print(f"T2 ✗ {v}")
    if not violations:
        print("T2 ✓ potfiles: new/removed core .py files are registered "
              "(doc 16 §Adding and removing Python files)")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
