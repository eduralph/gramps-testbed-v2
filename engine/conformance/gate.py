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
"""Bundle dispatcher for the T1 / T2 / T4 conformance tiers (founded on wiki
doc 16; see ``t1_structure.py`` / ``t2_shape.py`` / ``t4_contribution.py``).

These tiers check the *contribution*, so the gate scope is ``bundle``: the
target is derived from ``$PDCA_BUNDLE`` rather than the whole working tree.

  * **T1 / T2** — the addon(s) the bundle's ``patch.diff`` touches, resolved
    under ``../addons-source/``. A core-only patch (no addon path) is **N/A**:
    the §Structure / §Coding-style addon rules don't apply, so the gate passes
    with a note.
  * **T4** — the bundle's ``commit-msg.txt`` (doc 16 §Commit messages) and/or
    ``pr-description.md`` (doc 16 §Contributor-workflow PR-body rules). Neither
    present → **N/A** → pass.

These gates are **advisory** (``gating = false`` in ``pdca.toml``): they audit
the touched contribution and surface doc-16 violations as evidence for the
reviewer and the human at sign-off, the same posture as the T3 baselines. Exit
status is 1 only on a real MUST violation; both "clean" and "N/A" exit 0.

Usage::

    PDCA_BUNDLE=results/issue_13636 gate.py T1
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import t1_structure  # noqa: E402
import t2_shape  # noqa: E402
import t4_contribution  # noqa: E402


def _repo_root() -> Path:
    """Walk up from this file to the pdca.toml marker (git-independent, matching
    the engine runners' root resolution)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pdca.toml").is_file():
            return parent
    # Fallback: engine/conformance/gate.py → repo root is two levels up.
    return here.parents[2]


def _bundle() -> Path:
    raw = os.environ.get("PDCA_BUNDLE")
    if not raw:
        print("gate.py: PDCA_BUNDLE is not set (bundle-scoped gate)", file=sys.stderr)
        sys.exit(2)
    return Path(raw)


# A diff path line: 'diff --git a/<p> b/<p>' or '+++ b/<p>'. We take the b-side.
_DIFF_B = re.compile(r"^(?:diff --git a/\S+ b/|\+\+\+ b/)(\S+)")


def _touched_addons(patch: Path, addons_root: Path) -> list[Path]:
    """Addon directories under ``addons_root`` referenced by the patch's b-paths."""
    if not patch.is_file():
        return []
    found: dict[str, Path] = {}
    for line in patch.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _DIFF_B.match(line)
        if not m:
            continue
        first = m.group(1).split("/", 1)[0]  # leading path segment = addon dir
        cand = addons_root / first
        if first and first not in found and cand.is_dir():
            found[first] = cand
    return list(found.values())


def _na(tier: str, msg: str) -> int:
    print(f"{tier} – N/A: {msg}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] not in ("T1", "T2", "T4"):
        print("usage: gate.py {T1|T2|T4}  (reads $PDCA_BUNDLE)", file=sys.stderr)
        return 2
    tier = argv[0]
    bundle = _bundle()
    root = _repo_root()
    addons_root = (root.parent / "addons-source").resolve()

    if tier in ("T1", "T2"):
        addons = _touched_addons(bundle / "patch.diff", addons_root)
        if not addons:
            return _na(tier, "no addons-source path in patch.diff (core-only change)")
        if tier == "T1":
            return t1_structure.main([str(a) for a in addons])
        return t2_shape.main([str(a) for a in addons])

    # T4 — the contribution wrapper.
    args: list[str] = []
    commit_msg = bundle / "commit-msg.txt"
    pr_body = bundle / "pr-description.md"
    if commit_msg.is_file():
        args += ["--commit-msg", str(commit_msg)]
    if pr_body.is_file():
        args += ["--pr-body", str(pr_body)]
    if not args:
        return _na("T4", "no commit-msg.txt or pr-description.md in the bundle")
    return t4_contribution.main(args)


if __name__ == "__main__":
    sys.exit(main())
