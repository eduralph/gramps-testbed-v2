#!/usr/bin/env python3
"""Write a synthetic JUnit ``<error>`` for an addon test-collection crash.

``run-addon-unit.sh`` runs each addon's suite via ``python3 -m xmlrunner``. When
an addon raises at **import** — e.g. GraphView's module-level
``raise Exception("GraphViz … is required")`` — the unittest loader crashes
during *collection*, so xmlrunner runs 0 tests and writes **no JUnit XML at all**.
``t3_baseline`` then sees zero parsed failures and can only report an
unattributable "runner exited N with no parsed failures" delta (issue_8653).

This helper emits a minimal, valid JUnit file with one ``<error>`` testcase so the
crash becomes a first-class, *named*, baseline-able failure
(``<addon>.collection::import_or_collection``). It is written **flat** into the
results dir (``test-results/TEST-<addon>-collection-crash.xml``), matching the
run-unit / run-interface layout, so ``t3_baseline.parse_junit`` finds it
regardless of its glob depth.

CLI::

    synth_junit.py <results_dir> <addon> <rc> [run_log]
"""

from __future__ import annotations

import sys
from pathlib import Path
from xml.sax.saxutils import escape

_TAIL_LINES = 12  # last lines of the crash log to embed as the error detail


def write_crash(results_dir: str, addon: str, rc: int, log_path: str | None = None) -> Path:
    """Write ``test-results/TEST-<addon>-collection-crash.xml`` and return its path."""
    detail = ""
    if log_path:
        try:
            lines = Path(log_path).read_text(encoding="utf-8", errors="replace").splitlines()
            detail = "\n".join(lines[-_TAIL_LINES:])
        except OSError:
            pass
    suite = f"{addon}.collection"
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<testsuite name="{escape(suite)}" tests="1" errors="1" failures="0" skipped="0">\n'
        f'  <testcase classname="{escape(suite)}" name="import_or_collection">\n'
        f'    <error message="addon test collection crashed (rc={int(rc)}, 0 tests run)">'
        f'{escape(detail)}</error>\n'
        '  </testcase>\n'
        '</testsuite>\n'
    )
    out = Path(results_dir) / f"TEST-{addon}-collection-crash.xml"
    out.write_text(xml, encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 3:
        print("usage: synth_junit.py <results_dir> <addon> <rc> [run_log]", file=sys.stderr)
        return 2
    results_dir, addon, rc = argv[0], argv[1], argv[2]
    log_path = argv[3] if len(argv) > 3 else None
    try:
        rc_int = int(rc)
    except ValueError:
        rc_int = 1
    out = write_crash(results_dir, addon, rc_int, log_path)
    print(f"synth_junit: recorded collection crash → {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
