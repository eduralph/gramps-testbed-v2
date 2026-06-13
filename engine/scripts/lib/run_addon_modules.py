#!/usr/bin/env python3
"""Run an addon's test modules each in its own subprocess with a per-module wall clock.

``run-addon-unit.sh`` used to run a whole addon's suite in ONE
``python3 -m xmlrunner mod_a mod_b …`` invocation, bounded only by the outer
whole-job ``timeout`` (default 1200s). A single hanging module therefore consumed
the entire job budget; on expiry the container was killed wholesale, the log named
no culprit, and every not-yet-run module was lost (issue testbed-per-module-timeout).

This helper restores the invariant "test execution is bounded *and attributable*":
it runs each module as its **own** ``python3 -m xmlrunner <module> -o <out> -v``
subprocess under a per-module timeout. A module that exceeds it is killed (process
group, SIGKILL) and recorded as a **named** failure — a synthetic JUnit ``<failure>``
in the output dir plus a ``module-timeout: <module>`` line on stdout — while the
**remaining modules still run**. The existing outer whole-job ``timeout`` stays as
the backstop. Mirrors PR #820's ``run_addon_tests.py`` ``MODULE_TIMEOUT_S`` model.

The subprocess command is byte-for-byte the per-module form of what the runner ran
before (``python3 -m xmlrunner <module> -o <out_dir> -v``); only the batching and
the wall clock change, so the production path is exercised, not re-implemented.

CLI::

    run_addon_modules.py --timeout N -o OUTDIR MODULE [MODULE …]

Exit code: 0 = all modules passed; 124 = at least one module hit the per-module
timeout (named on stdout); 1 = some module failed without timing out. 124 mirrors
GNU ``timeout``'s convention so the caller can distinguish a hang from a plain fail.
"""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

# Exit codes (124 = GNU timeout convention, so the shell can name the hang).
EXIT_OK = 0
EXIT_FAIL = 1
EXIT_TIMEOUT = 124

# Statuses run_modules reports per module.
PASS = "pass"
FAIL = "fail"
TIMEOUT = "timeout"


def _safe_name(module: str) -> str:
    """A filename-safe rendering of a dotted module path."""
    return module.replace("/", "_").replace(os.sep, "_")


def write_timeout_junit(out_dir: str, module: str, timeout: float) -> Path:
    """Write a JUnit ``<failure>`` naming a module that hit the per-module timeout.

    Written into the per-addon output dir as ``TEST-<module>-timeout.xml`` so the
    hang becomes a first-class, *named*, baseline-able failure
    (``<module>::module_timeout``) for ``junit_coverage`` / ``t3_baseline`` — exactly
    the attribution the wholesale outer-timeout kill destroyed.
    """
    msg = f"module exceeded the per-module timeout of {timeout:g}s and was killed"
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<testsuite name="{escape(module)}" tests="1" errors="0" failures="1" skipped="0">\n'
        f'  <testcase classname="{escape(module)}" name="module_timeout">\n'
        f'    <failure message="{escape(msg)}">{escape(msg)}</failure>\n'
        "  </testcase>\n"
        "</testsuite>\n"
    )
    out = Path(out_dir) / f"TEST-{_safe_name(module)}-timeout.xml"
    out.write_text(xml, encoding="utf-8")
    return out


def _run_one(module: str, out_dir: str, timeout: float, cwd: str | None) -> int | None:
    """Run one module under ``xmlrunner``; return its rc, or ``None`` if it timed out.

    The child runs in its own session (``start_new_session=True``) so a hanging test
    that spawned children is killed as a whole **process group** on timeout, not just
    the python interpreter.
    """
    proc = subprocess.Popen(
        [sys.executable, "-m", "xmlrunner", module, "-o", out_dir, "-v"],
        cwd=cwd,
        start_new_session=True,
    )
    try:
        return proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()
        proc.wait()
        return None


def run_modules(
    modules: list[str], out_dir: str, timeout: float, cwd: str | None = None
) -> dict[str, str]:
    """Run each module in its own timed subprocess; return ``{module: status}``.

    A hang is killed at ``timeout`` and recorded ``TIMEOUT`` (named JUnit + stdout
    line); the loop then continues so sibling modules still run. ``cwd`` defaults to
    the inherited working dir — the runner ``cd``s into ``addons-source`` first, so
    the production call passes none.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    results: dict[str, str] = {}
    for module in modules:
        rc = _run_one(module, out_dir, timeout, cwd)
        if rc is None:
            write_timeout_junit(out_dir, module, timeout)
            # Named on stdout so the runner's _run.log (and its summary) attribute it.
            print(
                f"module-timeout: {module} (killed after {timeout:g}s; siblings continue)",
                flush=True,
            )
            results[module] = TIMEOUT
        elif rc != 0:
            results[module] = FAIL
        else:
            results[module] = PASS
    return results


def _exit_code(results: dict[str, str]) -> int:
    if any(s == TIMEOUT for s in results.values()):
        return EXIT_TIMEOUT
    if any(s == FAIL for s in results.values()):
        return EXIT_FAIL
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run addon test modules each in its own per-module-timed subprocess."
    )
    parser.add_argument(
        "--timeout",
        type=float,
        required=True,
        help="per-module wall clock in seconds; a module exceeding it is killed and "
        "reported by name, while remaining modules still run",
    )
    parser.add_argument(
        "-o", "--output", required=True, help="JUnit output dir (passed to xmlrunner)"
    )
    parser.add_argument("modules", nargs="+", help="dotted test module paths")
    args = parser.parse_args(argv)

    results = run_modules(args.modules, args.output, args.timeout)
    timed_out = [m for m, s in results.items() if s == TIMEOUT]
    if timed_out:
        print(
            f"run_addon_modules: {len(timed_out)} module(s) hit the "
            f"{args.timeout:g}s per-module timeout: {' '.join(timed_out)}",
            file=sys.stderr,
        )
    return _exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
