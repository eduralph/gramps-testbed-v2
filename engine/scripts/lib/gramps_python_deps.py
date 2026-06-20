#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Gramps Testbed v2 — engine
#
# Copyright (C) 2026  Eduard Ralph
#
# SPDX-License-Identifier: Apache-2.0
#
"""Single source of truth for gramps' own *Python* runtime + testing deps (issue #132).

Reads the gramps checkout's ``pyproject.toml`` and returns the union of
``[project].dependencies`` and the ``[project.optional-dependencies].testing`` extra —
exactly the set the per-gate ``pip install -e ./gramps[testing]`` pulls. Baking that
resolved set into the Docker image as a layer (``engine/docker/gramps-requirements.txt``,
``COPY``-ed + ``pip install -r`` in ``Dockerfile.ubuntu``) means the per-run editable
install finds its deps already satisfied and just links gramps — the residual install
time #68's pip-cache volume can't elide.

Single-sourced like ``addon_system_deps.py`` / ``addon_python_deps.py``: the dep list is
derived from gramps' own metadata, never hand-maintained, so it can't silently drift. The
generated file is committed (so the ``engine/`` Docker build context — which excludes the
sibling ``../gramps`` — always has it) and kept honest by ``test_gramps_python_deps.py``,
which re-derives from the live ``../gramps`` and fails on drift; ``make gramps-requirements``
regenerates it on a gramps dep bump.

Pure stdlib (``tomllib``), no gramps import — runs at image-build/preflight time before
gramps is installed.

CLI::

    gramps_python_deps.py [--pyproject ../gramps/pyproject.toml] [-o <out.txt>]
    # no -o → print the requirements (one per line) to stdout
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

# The extra the gates install (`pip install -e ./gramps[testing]`); its members plus the
# base `[project].dependencies` are what we bake. NOT the gui/image/i18n/all extras —
# those aren't what the headless test gates pull.
_EXTRA = "testing"

_HEADER = (
    "# GENERATED — do not edit by hand. Source: gramps pyproject.toml\n"
    "# ([project].dependencies + the [{extra}] extra), via\n"
    "# engine/scripts/lib/gramps_python_deps.py. Baked into the Docker image as a layer\n"
    "# so the per-run `pip install -e ./gramps[{extra}]` finds these satisfied and just\n"
    "# links gramps (issue #132). Regenerate: `make gramps-requirements`; a drift test\n"
    "# (engine/tests/test_gramps_python_deps.py) fails if this is stale vs ../gramps.\n"
)


def requirements(pyproject: str | Path) -> list[str]:
    """The gramps runtime + ``testing`` deps from ``pyproject``, sorted, deduped.

    Union of ``[project].dependencies`` and ``[project.optional-dependencies].testing``
    (the exact set ``pip install -e ./gramps[testing]`` resolves). Case-insensitive sort
    + dedupe; the strings are kept verbatim (incl. any version spec) so they install the
    same as the live extra.
    """
    data = tomllib.loads(Path(pyproject).read_text(encoding="utf-8"))
    project = data.get("project", {})
    deps = list(project.get("dependencies", []))
    deps += list(project.get("optional-dependencies", {}).get(_EXTRA, []))
    # Dedupe verbatim strings (preserve version specs); stable case-insensitive order.
    return sorted(dict.fromkeys(deps), key=str.lower)


def render(pyproject: str | Path) -> str:
    """The full requirements-file text (header + one dep per line)."""
    body = "".join(f"{r}\n" for r in requirements(pyproject))
    return _HEADER.format(extra=_EXTRA) + body


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    # engine/scripts/lib/this → parents[3] is the repo root; its parent holds the
    # sibling gramps/ checkout (the WORKSPACE convention the engine runners use).
    ap.add_argument(
        "--pyproject",
        default=str(Path(__file__).resolve().parents[3].parent / "gramps" / "pyproject.toml"),
        help="path to the gramps checkout's pyproject.toml (default: ../gramps/pyproject.toml)",
    )
    ap.add_argument("-o", "--out", help="write the requirements file here (default: stdout)")
    args = ap.parse_args(argv)

    if not Path(args.pyproject).is_file():
        print(f"gramps_python_deps: no pyproject at {args.pyproject}", file=sys.stderr)
        return 2
    text = render(args.pyproject)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"→ wrote {args.out} ({len(requirements(args.pyproject))} deps)")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
