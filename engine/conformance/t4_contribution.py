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
"""T4 — Contribution conformance (the *contribution-shape* tier of T1–T4).

T4 checks the *contribution wrapper* — the commit message and the PR body — not
the code, and it is **target-aware**: the commit-message rules are shared by both
guidelines' §Commit messages, but the **four-section PR body** (Root cause / Fix /
Verified against / Test) is a **core-only** rule (core §Contributor workflow); the
addon guideline only requires a Mantis bug reference in the PR body. So an addon
contribution is never failed against the core PR-body rule, nor vice versa
(testbed issue #6). Cited by **section** via :mod:`doc16` so anchors survive page
edits.

Commit message (``check_commit_msg``, both targets — §Commit messages /
§Mantis trailer keywords):

  * MUST: summary (line 1) is ≤ 70 characters
  * MUST: a single blank line separates summary from description
  * MUST: description body wrapped at ≤ 80 characters
  * MUST: another commit is referenced by FULL hash, not a short hash
  * MUST: the Mantis trailer is the last line, after a blank line
  * MUST: the trailer uses the ``Keyword #NNNN`` form (not bare/URL)

PR body (``check_pr_body``):

  * MUST (**core only**): structured Root cause / Fix / Verified against / Test
    (core §Contributor workflow)
  * MUST: references the Mantis bug with ``#NNNN`` (core §Contributor workflow /
    addon §addons-source: bug reference in PR body)

CLI::

    t4_contribution.py --commit-msg <file> [--target core|addon]
    t4_contribution.py --pr-body <file>   [--target core|addon]
    # '-' reads stdin. Either or both may be given. --target defaults to core.

Prints one ``T4 ✗ …`` line per violation; exits 1 iff any was found.
"""

from __future__ import annotations

import argparse
import re
import sys

import doc16

# The Mantis trailer keywords. "resolve" closes the bug on commit; "link"
# cross-references without closing. Both take the #NNNN form.
_RESOLVE_KW = ("Fixes", "Fixed", "Resolves", "Resolved")
_LINK_KW = ("Bug", "Bugs", "Issue", "Report")
_TRAILER = re.compile(
    r"^(?:" + "|".join(_RESOLVE_KW + _LINK_KW) + r")\s+#\d+(?:\s*,\s*#\d+)*\.?$"
)
# A trailer keyword used with a BARE number or a URL — the anti-pattern that
# misses the MantisBT auto-link. Used to give a precise message.
_TRAILER_KW_ANY = re.compile(
    r"^(?:" + "|".join(_RESOLVE_KW + _LINK_KW) + r")\b", re.IGNORECASE
)
# A short hash in brackets does not auto-link; require the full hash.
_SHORT_HASH = re.compile(r"\[[0-9a-f]{7,12}\]")

_SUMMARY_MAX = 70
_BODY_WRAP = 80


def check_commit_msg(text: str, target: str = "core", *, require_trailer: bool = True) -> list[str]:
    """Return the commit-message MUST violations (each citing its section).

    ``require_trailer=False`` is the declared-ticketless path (the brief states
    ``Mantis: none``): a missing trailer is then **not** a violation, but a trailer
    that *is* present must still be well-formed — so a borrowed/mis-typed
    ``Bug #NNNN`` is never silently accepted (issue #71)."""
    cm = doc16.cite(target, "Commit messages")
    tk = doc16.cite(target, "Mantis trailer keywords")
    violations: list[str] = []
    lines = text.rstrip("\n").split("\n")
    if not lines or not lines[0].strip():
        return [f"commit: empty summary line ({cm})"]

    # summary ≤ 70 chars.
    summary = lines[0]
    if len(summary) > _SUMMARY_MAX:
        violations.append(
            f"commit: summary is {len(summary)} chars > {_SUMMARY_MAX} ({cm})"
        )

    # a single blank line separates summary from description.
    if len(lines) > 1 and lines[1].strip():
        violations.append(f"commit: no blank line after the summary ({cm})")

    # description body wrapped at ≤ 80 chars.
    for ln, line in enumerate(lines[2:], start=3):
        if len(line) > _BODY_WRAP:
            violations.append(
                f"commit:{ln} body line is {len(line)} chars > {_BODY_WRAP} ({cm})"
            )

    # full hash, not a bracketed short hash.
    for ln, line in enumerate(lines, start=1):
        if _SHORT_HASH.search(line):
            violations.append(
                f"commit:{ln} short-hash reference — use the full hash ({cm})"
            )

    # the Mantis trailer is the last non-empty line and uses the Keyword #NNNN form.
    nonempty = [ln for ln in lines if ln.strip()]
    last = nonempty[-1].strip() if nonempty else ""
    if _TRAILER.match(last):
        # The trailer line exists and is well-formed; it MUST follow a blank line.
        idx = len(lines) - 1
        while idx > 0 and not lines[idx].strip():
            idx -= 1
        if idx > 0 and lines[idx - 1].strip():
            violations.append(
                f"commit: Mantis trailer is not separated from the body by a "
                f"blank line ({cm})"
            )
    elif _TRAILER_KW_ANY.match(last):
        # A trailer keyword used but mis-formed — always a violation, even ticketless:
        # a present-but-wrong trailer must never pass.
        violations.append(
            f"commit: trailer must use the '#NNNN' form, not a bare number "
            f"or URL ({tk}) — got: {last[:50]!r}"
        )
    elif require_trailer:
        violations.append(
            f"commit: last line is not a Mantis trailer "
            f"(e.g. 'Fixes #12345') ({tk}) — got: {last[:50]!r}"
        )
    # else: declared ticketless and no trailer attempted — OK.
    return violations


# The four required PR-body sections — a CORE rule (core §Contributor workflow).
_PR_SECTIONS = ("Root cause", "Fix", "Verified against", "Test")
_BUG_REF = re.compile(r"#\d+")


def check_pr_body(text: str, target: str = "core", *, require_trailer: bool = True) -> list[str]:
    """Return the PR-body MUST violations for the given target.

    The four-section structure (Root cause / Fix / Verified against / Test) is a
    **core-only** MUST; the addon guideline only mandates a Mantis bug reference.
    ``require_trailer=False`` (declared ticketless) waives the ``#NNNN`` reference —
    the section structure is still required.
    """
    violations: list[str] = []
    low = text.lower()
    if target == "core":
        cite = doc16.cite("core", "Contributor workflow")
        for section in _PR_SECTIONS:
            if section.lower() not in low:
                violations.append(
                    f"pr-body: missing '{section}' section — core PR body must be "
                    f"Root cause / Fix / Verified against / Test ({cite})"
                )
        bug_cite = cite
    else:
        bug_cite = doc16.cite("addon", "addons-source: bug reference in PR body")
    if require_trailer and not _BUG_REF.search(text):
        violations.append(f"pr-body: no Mantis bug reference '#NNNN' ({bug_cite})")
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
    ap.add_argument("--target", choices=("core", "addon"), default="core",
                    help="contribution target — picks the guideline (default: core)")
    ap.add_argument("--no-trailer", action="store_true",
                    help="declared-ticketless: don't require a Mantis trailer / #NNNN "
                         "(a present-but-malformed trailer is still flagged)")
    ns = ap.parse_args(argv)
    if not ns.commit_msg and not ns.pr_body:
        ap.error("give --commit-msg and/or --pr-body")

    require = not ns.no_trailer
    violations: list[str] = []
    if ns.commit_msg:
        violations += check_commit_msg(_read(ns.commit_msg), ns.target, require_trailer=require)
    if ns.pr_body:
        violations += check_pr_body(_read(ns.pr_body), ns.target, require_trailer=require)

    for line in violations:
        print(f"T4 ✗ {line}")
    if not violations:
        print(f"T4 ✓ contribution: commit/PR wrapper conforms to doc16-{ns.target} "
              f"§Contributor workflow")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
