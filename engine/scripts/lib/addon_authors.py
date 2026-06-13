#!/usr/bin/env python3
"""
Read an addon's credit metadata from its ``.gpr.py`` — author(s) and maintainer(s).

Sibling to ``addon_system_deps.py`` / ``addon_python_deps.py``. A Gramps addon
registers ``authors`` / ``authors_email`` and (sometimes) ``maintainers`` /
``maintainers_email`` in its ``.gpr.py``. This module extracts them so a PR that
modifies the addon can **@-mention the right person as a callout** — a heads-up so
they're aware of the change and don't miss it (testbed issue #53; raised on
gramps-project/addons-source PR #946) — Doug Blank: *"otherwise I could miss fixes
to my addons"*; Nick Hall: *"mention the current maintainer if one exists."* The
mention is **awareness, not attribution**: it pings the person responsible for the
addon so they can review.

Who to call out (``mention_targets``): the **maintainers** when the addon declares
any, otherwise the **authors** (Doug's "original developer / contributors"
fallback for addons with no explicit maintainer — the common case, since most
``.gpr.py`` set only ``authors``).

The ``.gpr.py`` records **names and emails, not GitHub @-handles** — resolving a
handle from an email is the caller's job (best-effort, e.g. the publisher leaf or
the addons-source workflow); this module only reads what the addon declares.

Scanning matches the sibling scanners deliberately: a regex per field, then
``ast.literal_eval`` on the bracketed list — pure stdlib, no Gramps import, no
executing the ``.gpr.py``. Every real author/maintainer field in addons-source is
a flat string list, so a literal-eval parse covers them; a non-literal or
unreadable declaration yields an empty list rather than aborting.

CLI::

    addon_authors.py <addon-dir>     # JSON: authors / maintainers (+emails) + mention
"""

from __future__ import annotations

import ast
import glob
import json
import os
import re
import sys

# Each field is a flat string list on one (occasionally wrapped) assignment. The
# `\b…\b` guards stop the `authors` pattern from matching `authors_email` (and
# `maintainers` from `maintainers_email`). `[^\]]*` spans newlines (negated class).
_FIELDS = ("authors", "authors_email", "maintainers", "maintainers_email")


def _gpr_text(addon_dir: str) -> str:
    """Concatenated text of every ``*.gpr.py`` in *addon_dir* (best-effort)."""
    out = []
    for path in sorted(glob.glob(os.path.join(addon_dir, "*.gpr.py"))):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                out.append(fh.read())
        except OSError as exc:
            print(f"addon_authors: skipping unreadable {path}: {exc}", file=sys.stderr)
    return "\n".join(out)


def _field(text: str, name: str) -> list[str]:
    """The non-empty string entries of a ``<name> = [...]`` assignment (or [])."""
    m = re.search(rf"\b{re.escape(name)}\b\s*=\s*(\[[^\]]*\])", text)
    if not m:
        return []
    try:
        value = ast.literal_eval(m.group(1))
    except (ValueError, SyntaxError):
        print(f"addon_authors: skipping non-literal {name}: {m.group(1)!r}",
              file=sys.stderr)
        return []
    return [str(x).strip() for x in value if str(x).strip()]


def addon_credits(addon_dir: str) -> dict[str, list[str]]:
    """``{authors, authors_email, maintainers, maintainers_email}`` for an addon dir."""
    text = _gpr_text(addon_dir)
    return {f: _field(text, f) for f in _FIELDS}


def mention_targets(addon_dir: str) -> tuple[str, list[tuple[str, str]]]:
    """``(role, [(name, email), …])`` — the current maintainer(s) to @-mention.

    A heads-up so the person responsible for the addon *now* is aware of the change —
    not attribution. Doug's "original developer (or contributors)" and Nick's "current
    maintainer" (addons-source PR #946) mean the **same role**: the addon's current
    maintainer. In ``.gpr.py`` terms that is the ``maintainers`` field when declared,
    else the ``authors`` — for an addon with no separate maintainer, the original
    author is the de-facto current maintainer. Names are zipped with their positional
    email (``""`` when none is declared).
    """
    c = addon_credits(addon_dir)
    if c["maintainers"]:
        names, emails = c["maintainers"], c["maintainers_email"]
        role = "maintainer"
    else:
        names, emails = c["authors"], c["authors_email"]
        role = "author"
    people = [(n, emails[i] if i < len(emails) else "") for i, n in enumerate(names)]
    return role, people


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: addon_authors.py <addon-dir>", file=sys.stderr)
        return 2
    addon_dir = argv[0]
    if not os.path.isdir(addon_dir):
        print(f"addon_authors.py: not a directory: {addon_dir}", file=sys.stderr)
        return 2
    role, people = mention_targets(addon_dir)
    out = addon_credits(addon_dir)
    out["mention"] = {"role": role, "people": [{"name": n, "email": e} for n, e in people]}
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
