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
"""T4 — Contribution conformance (the *contribution-shape* tier of T1–T4,
founded on wiki doc 16 §Commit messages, §Mantis trailer keywords, and the
PR-body rules in §Contributor workflow).

T4 checks the *contribution wrapper* — the commit message and the PR body — not
the code. Each rule is cited ``doc16:LINE`` back to
``wiki/pages/06 - Addon development/16-guidelines.md``.

Commit message (``check_commit_msg``):

  * MUST: summary (line 1) is ≤ 70 characters                          doc16:137
  * MUST: a single blank line separates summary from description       doc16:138
  * MUST: description body wrapped at ≤ 80 characters                  doc16:138
  * MUST: another commit is referenced by FULL hash, not a short hash  doc16:141
  * MUST: the Mantis trailer is the last line, after a blank line      doc16:142
  * MUST: the trailer uses the ``Keyword #NNNN`` form (not bare/URL)   doc16:144-165

PR body (``check_pr_body``):

  * MUST: structured Root cause / Fix / Verified against / Test        doc16:118
  * MUST: references the Mantis bug with ``#NNNN``                     doc16:119

CLI::

    t4_contribution.py --commit-msg <file>      # validate a commit message
    t4_contribution.py --pr-body <file>         # validate a PR body
    # '-' reads stdin. Either or both may be given.

Prints one ``T4 ✗ …`` line per violation; exits 1 iff any was found.
"""

from __future__ import annotations

import argparse
import re
import sys

# doc16:144-163 — the Mantis trailer keywords. "resolve" closes the bug on
# commit; "link" cross-references without closing. Both take the #NNNN form.
_RESOLVE_KW = ("Fixes", "Fixed", "Resolves", "Resolved")
_LINK_KW = ("Bug", "Bugs", "Issue", "Report")
_TRAILER = re.compile(
    r"^(?:" + "|".join(_RESOLVE_KW + _LINK_KW) + r")\s+#\d+(?:\s*,\s*#\d+)*\.?$"
)
# A trailer keyword used with a BARE number or a URL — the doc16:165 anti-pattern
# (misses the MantisBT auto-link). Used to give a precise message.
_TRAILER_KW_ANY = re.compile(
    r"^(?:" + "|".join(_RESOLVE_KW + _LINK_KW) + r")\b", re.IGNORECASE
)
# doc16:141 — a short hash in brackets does not auto-link; require the full hash.
_SHORT_HASH = re.compile(r"\[[0-9a-f]{7,12}\]")

_SUMMARY_MAX = 70
_BODY_WRAP = 80


def check_commit_msg(text: str) -> list[str]:
    """Return the list of MUST violations (each citing ``doc16:LINE``)."""
    violations: list[str] = []
    lines = text.rstrip("\n").split("\n")
    if not lines or not lines[0].strip():
        return ["commit: empty summary line (doc16:137)"]

    # doc16:137 — summary ≤ 70 chars.
    summary = lines[0]
    if len(summary) > _SUMMARY_MAX:
        violations.append(
            f"commit: summary is {len(summary)} chars > {_SUMMARY_MAX} (doc16:137)"
        )

    # doc16:138 — a single blank line separates summary from description.
    if len(lines) > 1 and lines[1].strip():
        violations.append("commit: no blank line after the summary (doc16:138)")

    # doc16:138 — description body wrapped at ≤ 80 chars.
    for ln, line in enumerate(lines[2:], start=3):
        if len(line) > _BODY_WRAP:
            violations.append(
                f"commit:{ln} body line is {len(line)} chars > {_BODY_WRAP} (doc16:138)"
            )

    # doc16:141 — full hash, not a bracketed short hash.
    for ln, line in enumerate(lines, start=1):
        if _SHORT_HASH.search(line):
            violations.append(
                f"commit:{ln} short-hash reference — use the full hash (doc16:141)"
            )

    # doc16:142 + doc16:144-165 — the Mantis trailer is the last non-empty line
    # and uses the Keyword #NNNN form.
    nonempty = [ln for ln in lines if ln.strip()]
    last = nonempty[-1].strip() if nonempty else ""
    if not _TRAILER.match(last):
        if _TRAILER_KW_ANY.match(last):
            violations.append(
                f"commit: trailer must use the '#NNNN' form, not a bare number "
                f"or URL (doc16:165) — got: {last[:50]!r}"
            )
        else:
            violations.append(
                f"commit: last line is not a Mantis trailer "
                f"(e.g. 'Fixes #12345') (doc16:142,144) — got: {last[:50]!r}"
            )
    else:
        # The trailer line exists and is well-formed; it MUST follow a blank line.
        idx = len(lines) - 1
        while idx > 0 and not lines[idx].strip():
            idx -= 1
        if idx > 0 and lines[idx - 1].strip():
            violations.append(
                "commit: Mantis trailer is not separated from the body by a "
                "blank line (doc16:142)"
            )
    return violations


# doc16:118 — the four required PR-body sections.
_PR_SECTIONS = ("Root cause", "Fix", "Verified against", "Test")
_BUG_REF = re.compile(r"#\d+")


def check_pr_body(text: str) -> list[str]:
    """Return the list of MUST violations for a PR body (doc16:118-119)."""
    violations: list[str] = []
    low = text.lower()
    for section in _PR_SECTIONS:
        if section.lower() not in low:
            violations.append(
                f"pr-body: missing '{section}' section — body must be "
                f"Root cause / Fix / Verified against / Test (doc16:118)"
            )
    if not _BUG_REF.search(text):
        violations.append("pr-body: no Mantis bug reference '#NNNN' (doc16:119)")
    return violations


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="T4 Contribution conformance (doc 16)")
    ap.add_argument("--commit-msg", help="commit message file ('-' for stdin)")
    ap.add_argument("--pr-body", help="PR body file ('-' for stdin)")
    ns = ap.parse_args(argv)
    if not ns.commit_msg and not ns.pr_body:
        ap.error("give --commit-msg and/or --pr-body")

    violations: list[str] = []
    if ns.commit_msg:
        violations += check_commit_msg(_read(ns.commit_msg))
    if ns.pr_body:
        violations += check_pr_body(_read(ns.pr_body))

    for line in violations:
        print(f"T4 ✗ {line}")
    if not violations:
        print("T4 ✓ contribution: commit/PR wrapper conforms to doc 16 §Contributor workflow")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
