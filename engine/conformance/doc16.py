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
"""Single source of truth for citing the vendored doc-16 guidelines.

Every conformance MUST is cited back to its normative source by **section
heading**, not line number — headings survive edits to the pages, line numbers do
not (testbed issue #6). Two guidelines apply, chosen by **contribution target**:

  * a **core** fix is judged against the Gramps-core page
    (``wiki/pages/05 - Gramps development/16-guidelines.md``) and core's
    ``AGENTS.md`` — the coding standard both pages' §Coding style defer to;
  * an **addon** fix against the addon page
    (``wiki/pages/06 - Addon development/16-guidelines.md``).

:func:`cite` returns the auditable citation string the checkers embed in each
violation (e.g. ``doc16-addon §Structure``). :func:`sections_present` lists the
headings actually in a vendored source, so a test can assert every cited section
still exists — the anchor-drift guard that makes section anchors safe even while
the pages keep changing.
"""

from __future__ import annotations

import re
from pathlib import Path


def _root() -> Path:
    """Repo root via the pdca.toml marker (matches the engine runners)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pdca.toml").is_file():
            return parent
    return here.parents[2]


_ROOT = _root()

# The vendored normative sources, by short label. ``agents`` is core's in-repo
# coding standard, a sibling-repo file the §Coding style sections defer to.
PAGES = {
    "addon": _ROOT / "wiki" / "pages" / "06 - Addon development" / "16-guidelines.md",
    "core": _ROOT / "wiki" / "pages" / "05 - Gramps development" / "16-guidelines.md",
    "agents": _ROOT.parent / "gramps" / "AGENTS.md",
}
_LABELS = {"addon": "doc16-addon", "core": "doc16-core", "agents": "AGENTS.md"}

# The page that holds the per-target ruleset (coding-style MUSTs live in ``agents``
# regardless of target; this maps the *target* to its own guideline page).
TARGET_PAGE = {"core": "core", "addon": "addon"}


def cite(source: str, section: str) -> str:
    """An auditable citation, e.g. ``doc16-addon §Structure``.

    ``source`` is one of ``"addon"`` / ``"core"`` / ``"agents"`` (a key of
    :data:`PAGES`); ``section`` is the exact section heading text.
    """
    return f"{_LABELS[source]} §{section}"


_HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*$", re.MULTILINE)


def sections_present(source: str) -> set[str]:
    """The section headings in a vendored source (for anchor validation)."""
    page = PAGES[source]
    if not page.is_file():
        return set()
    return set(_HEADING.findall(page.read_text(encoding="utf-8", errors="replace")))
