"""Run a subprocess while ticking an elapsed-time heartbeat (docs 03 §automation).

A headless ``claude -p`` leaf and a Docker-backed gate both produce no output for
minutes; without a heartbeat the flow looks hung and the human kills a job that is
working. This is the single place that pattern lives — shared by the model leaves
(:mod:`pdca_harness.leaves`) and the deterministic gates (:mod:`pdca_harness.gates`).
"""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterable
from pathlib import Path


def run_with_heartbeat(
    cmd,
    *,
    cwd=None,
    shell: bool = False,
    env=None,
    input_text: str | None = None,
    capture: bool = False,
    interval: int = 15,
    label: str = "",
    status: Callable[[], str] | None = None,
) -> tuple[int, str]:
    """Run ``cmd``, printing ``… still working (NmSSs elapsed)`` every ``interval`` s.

    Returns ``(returncode, output)``. ``output`` is the combined stdout+stderr when
    ``capture`` is True (so a gate can keep its evidence line), else ``""`` and the
    child inherits the terminal. ``input_text``, if given, is written to stdin.

    ``status``, if given, is called on every tick to append a live snapshot of the
    child's work (e.g. which artifacts exist yet, a running test container) — so the
    heartbeat shows *what* is happening, not just that time passed. It is best-effort:
    any exception it raises is swallowed so a probe can never break the run.
    """
    stdin = subprocess.PIPE if input_text is not None else None
    stdout = subprocess.PIPE if capture else None
    stderr = subprocess.STDOUT if capture else None
    proc = subprocess.Popen(
        cmd, cwd=cwd, shell=shell, env=env, text=True,
        stdin=stdin, stdout=stdout, stderr=stderr,
    )

    chunks: list[str] = []
    reader: threading.Thread | None = None
    if capture:
        def _drain() -> None:
            assert proc.stdout is not None
            for line in proc.stdout:  # drain so the pipe can't fill and stall the child
                chunks.append(line)
        reader = threading.Thread(target=_drain, daemon=True)
        reader.start()

    if input_text is not None:
        try:
            assert proc.stdin is not None
            proc.stdin.write(input_text)
            proc.stdin.close()
        except BrokenPipeError:
            pass

    suffix = f" — {label}" if label else ""
    start = time.monotonic()
    while True:
        try:
            proc.wait(timeout=interval)
            break
        except subprocess.TimeoutExpired:
            mins, secs = divmod(int(time.monotonic() - start), 60)
            extra = ""
            if status is not None:
                try:
                    snap = status()
                    if snap:
                        extra = f" · {snap}"
                except Exception:  # a status probe must never break the run
                    extra = ""
            print(f"   … still working ({mins}m{secs:02d}s elapsed){suffix}{extra}",
                  file=sys.stderr, flush=True)
    if reader is not None:
        reader.join(timeout=5)
    return proc.returncode, "".join(chunks)


# ----------------------------------------------------------------------------
# Status probes — what a leaf/gate is doing right now (Tier 1: artifacts +
# file-write staleness in the watched dir; Tier 2: a running gramps test container).
# ----------------------------------------------------------------------------
def bundle_activity(watch_dir, expected: Iterable[str] = ()) -> str:
    """A one-line snapshot of the work in ``watch_dir`` for a heartbeat tick.

    Reports each ``expected`` artifact (``name ✓ <size>`` once written, else
    ``name —``); then either a running gramps test container (Tier 2 — the activity
    *is* the container, so no staleness is shown) or, failing that, how long since the
    newest write in the dir (``last write 12s ago`` / soft ``⚠ no writes 6m`` once a
    leaf has gone quiet for ≥5 min). Best-effort — returns ``""`` on any error.
    """
    try:
        watch = Path(watch_dir)
        parts: list[str] = []

        arts = [
            f"{name} ✓ {_fmt_size((watch / name).stat().st_size)}"
            if (watch / name).exists() else f"{name} —"
            for name in expected
        ]
        if arts:
            parts.append(" · ".join(arts))

        container = _running_test_container()
        if container:
            parts.append(f"running test ({container})")
        else:
            newest = _newest_mtime(watch)
            if newest:
                age = int(time.time() - newest)
                if age >= 300:
                    parts.append(f"⚠ no writes {age // 60}m")
                elif age >= 120:
                    parts.append(f"last write {age // 60}m ago")
                else:
                    parts.append(f"last write {age}s ago")
        return " · ".join(p for p in parts if p)
    except Exception:
        return ""


def _fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n}B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f}KB"
    return f"{n / 1024 / 1024:.1f}MB"


def _newest_mtime(watch: Path) -> float:
    newest = 0.0
    try:
        for f in watch.iterdir():
            if f.is_file():
                newest = max(newest, f.stat().st_mtime)
    except OSError:
        return 0.0
    return newest


def _running_test_container() -> str:
    """Compact age of a live ``grampstest-`` container (e.g. ``2m``), or ``""``."""
    try:
        out = subprocess.run(
            ["docker", "ps", "--filter", "name=grampstest-", "--format", "{{.RunningFor}}"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""
    first = out.splitlines()[0].strip() if out else ""
    return _compact_duration(first)


def _compact_duration(s: str) -> str:
    """``"About a minute ago"`` → ``"1m"``, ``"2 minutes ago"`` → ``"2m"``, etc."""
    if not s:
        return ""
    s = s.replace(" ago", "").strip().lower()
    lead = s.split()[0] if s.split() else ""
    n = int(lead) if lead.isdigit() else 1
    if "second" in s:
        return f"{n if lead.isdigit() else 0}s"
    if "minute" in s:
        return f"{n}m"
    if "hour" in s:
        return f"{n}h"
    if "day" in s:
        return f"{n}d"
    return s
