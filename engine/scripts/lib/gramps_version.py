#!/usr/bin/env python3
"""Print a Gramps checkout's version as X.Y.Z, read from gramps/version.py.

Single source for the image-tag version read. Parses the file as Python (ast)
rather than pattern-matching the literal, so upstream reformatting of the
VERSION_TUPLE assignment can't silently yield an empty version.

Usage: gramps_version.py <gramps-checkout-dir | path/to/version.py>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if path.is_dir():
        path = path / "gramps" / "version.py"
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        print(f"gramps_version.py: cannot parse {path}: {exc}", file=sys.stderr)
        return 1
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "VERSION_TUPLE" for t in node.targets
        ):
            try:
                tup = ast.literal_eval(node.value)
            except ValueError:
                continue  # dynamic assignment — keep looking
            if isinstance(tup, tuple) and len(tup) >= 3:
                print(".".join(str(part) for part in tup[:3]))
                return 0
    print(f"gramps_version.py: no literal VERSION_TUPLE in {path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
