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
target is derived from ``$PDCA_BUNDLE`` rather than the whole working tree, and
**the contribution target picks the guideline** (testbed issue #6):

  * **T1** — addon-packaging structure (§Structure), so addon-only: the addon(s)
    the patch touches under ``../addons-source/``. A core-only patch is **N/A**.
  * **T2** — code-shape MUSTs (``AGENTS.md`` §File Headers / §Logging) apply to
    **both** core and addon code, so it checks the touched addon dirs AND the
    touched core ``.py`` files (resolved under ``../gramps/``). N/A only if the
    patch touches no checkable ``.py`` path.
  * **T4** — the bundle's ``commit-msg.txt`` / ``pr-description.md``, judged
    against the **core** or **addon** guideline by whether the patch touches an
    addon (the four-section PR body is a core-only MUST). Neither file present →
    **N/A** → pass.

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
import t2_potfiles  # noqa: E402
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


def _patch_bpaths(patch: Path) -> list[str]:
    """The b-side paths the patch touches (deduped, in first-seen order)."""
    if not patch.is_file():
        return []
    seen: dict[str, None] = {}
    for line in patch.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _DIFF_B.match(line)
        if m:
            seen.setdefault(m.group(1), None)
    return list(seen)


def _touched_addons(patch: Path, addons_root: Path) -> list[Path]:
    """Addon directories under ``addons_root`` referenced by the patch's b-paths."""
    found: dict[str, Path] = {}
    for p in _patch_bpaths(patch):
        first = p.split("/", 1)[0]  # leading path segment = addon dir
        cand = addons_root / first
        if first and first not in found and cand.is_dir():
            found[first] = cand
    return list(found.values())


def _touched_core_files(patch: Path, addons_root: Path, core_root: Path) -> list[Path]:
    """Existing core ``.py`` files the patch touches (resolved under ``core_root``).

    A b-path is core (not addon) when its leading segment is not an addon dir.
    New files the patch *adds* don't yet exist on disk, so they're skipped — T2
    audits the touched code present in the checkout, like the addon-dir scan."""
    found: dict[str, Path] = {}
    for p in _patch_bpaths(patch):
        if not p.endswith(".py") or (addons_root / p.split("/", 1)[0]).is_dir():
            continue
        f = core_root / p
        if f.is_file() and str(f) not in found:
            found[str(f)] = f
    return list(found.values())


def _touched_addon_files(patch: Path, addons_root: Path) -> list[Path]:
    """Existing addon ``.py`` files the patch touches (added or modified), resolved
    under ``addons_root``.

    A b-path is an addon path when its leading segment is an addon dir. T2 audits
    only the ``.py`` files the contribution *touches* — not the whole addon dir —
    so a pre-existing file the patch never touched is out of scope, per the
    §File Headers MUST ("every **new** ``.py`` file") and pdca.toml's "no gating on
    legacy state the contribution did not introduce." Added files are present on
    disk once the bundle's patch is applied for the run; absent files are skipped,
    like the core scan."""
    found: dict[str, Path] = {}
    for p in _patch_bpaths(patch):
        if not p.endswith(".py") or not (addons_root / p.split("/", 1)[0]).is_dir():
            continue
        f = addons_root / p
        if f.is_file() and str(f) not in found:
            found[str(f)] = f
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
    patch = bundle / "patch.diff"
    addons_root = (root.parent / "addons-source").resolve()
    core_root = (root.parent / "gramps").resolve()
    addons = _touched_addons(patch, addons_root)
    target = "addon" if addons else "core"

    if tier == "T1":
        if not addons:
            return _na("T1", "no addons-source path in patch.diff "
                             "(core-only change; §Structure is addon-only)")
        return t1_structure.main([str(a) for a in addons])

    if tier == "T2":
        # T2 audits the .py files the patch *touches* (added or modified), not the
        # whole addon dir — pre-existing untouched files are out of scope.
        files = (_touched_addon_files(patch, addons_root)
                 + _touched_core_files(patch, addons_root, core_root))
        shape_rc = t2_shape.main([str(f) for f in files]) if files else 0
        # POTFILES registration (§Adding and removing Python files) — a CORE MUST;
        # read from the patch since a file the patch *adds* isn't on disk yet, so a
        # new-.py-only patch leaves `files` empty but still needs this check.
        pot_violations: list[str] = []
        if target == "core" and patch.is_file():
            pot_violations = t2_potfiles.check_patch(
                patch.read_text(encoding="utf-8", errors="replace"),
                already_listed=t2_potfiles.listed_on_disk(str(core_root)),
            )
            for v in pot_violations:
                print(f"T2 ✗ {v}")
        if not files and not pot_violations:
            return _na("T2", "no checkable .py path in patch.diff")
        return 1 if (shape_rc or pot_violations) else 0

    # T4 — the contribution wrapper, judged against the target's guideline.
    args: list[str] = []
    commit_msg = bundle / "commit-msg.txt"
    pr_body = bundle / "pr-description.md"
    if commit_msg.is_file():
        args += ["--commit-msg", str(commit_msg)]
    if pr_body.is_file():
        args += ["--pr-body", str(pr_body)]
    if not args:
        return _na("T4", "no commit-msg.txt or pr-description.md in the bundle")
    return t4_contribution.main(args + ["--target", target])


if __name__ == "__main__":
    sys.exit(main())
