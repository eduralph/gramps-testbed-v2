"""The current worker lane — a thread-local slot id for in-driver concurrency (docs 09).

When the driver runs the unattended Do+Check band across a worker pool
(:func:`flow._drive_and_act`), each worker thread is pinned to a fixed slot index
``0..lanes-1`` for its lifetime. Code that addresses a *shared mutable resource* a
cycle touches outside its bundle — today only the gate commands (which a project may
back with a checkout / container / port) — reads :func:`current` to scope that
resource per lane, without threading a lane parameter through every call.

The serial path (``lanes == 1``) never sets a lane, so :func:`current` returns
``None`` and gates run exactly as before — no ``PDCA_LANE`` in their environment.

**Separate-process lanes (issue #98).** The in-process pool is not the only way to run
concurrently — a human may launch several standalone ``pdca flow <id>`` processes in
separate terminals. Those share one workspace's git worktrees, so each must claim a
distinct lane too: :func:`from_env` honours an explicit ``$PDCA_LANE`` pin, and
:func:`claim` grabs a free slot via a cross-process file lock when none is pinned. Both
feed the same :func:`set_current`, so the gate-scoping contract is identical whether the
slot came from the worker pool or a separate process.
"""

from __future__ import annotations

import atexit
import os
import threading
from pathlib import Path

_local = threading.local()

# Lane-claim file handles held OPEN for the process lifetime — an flock lives only as long
# as its open fd, so keeping the handle here is what keeps the claim. A process claims at
# most one lane, but this is a list so a release is idempotent. Released at exit.
_claimed: list = []


def set_current(lane_id: int | None) -> None:
    """Pin the calling thread to ``lane_id`` (a worker slot), or clear it with ``None``."""
    _local.lane = lane_id


def current() -> int | None:
    """The calling thread's worker-slot id, or ``None`` when running serially."""
    return getattr(_local, "lane", None)


def from_env() -> int | None:
    """The lane pinned by ``$PDCA_LANE``, or ``None`` when unset / blank / non-numeric.

    A standalone ``pdca`` invocation (no in-process worker pool) reads this so a human
    can pin a terminal to a specific lane by hand — the explicit override that the
    auto-claim (:func:`claim`) yields to. A malformed value is treated as unset (serial)
    rather than crashing the command."""
    raw = os.environ.get("PDCA_LANE", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def claim(n_lanes: int, *, lanes_dir: Path) -> int | None:
    """Claim the first free lane slot ``0..n_lanes-1`` for this PROCESS, or ``None``.

    Each slot is a lockfile under ``lanes_dir``; an exclusive *non-blocking* flock that
    succeeds means the slot is ours until the process exits (the open handle is retained
    in :data:`_claimed` and the lock released at exit via :func:`_release`). This is how
    two ``pdca flow`` processes in separate terminals end up on distinct worktrees
    (``gramps-6.1-lane0`` / ``-lane1``) without a manual ``PDCA_LANE``. Returns the
    claimed slot and calls :func:`set_current`, or ``None`` when every slot is already
    held (the caller then falls back to serial — the bare worktree).

    Best-effort: on a platform without ``fcntl`` we return ``None`` (no claim, serial)
    rather than fail — separate-process lanes are a POSIX convenience, not a correctness
    requirement of the serial path."""
    if n_lanes <= 0:
        return None
    try:
        import fcntl
    except ImportError:
        return None
    lanes_dir.mkdir(parents=True, exist_ok=True)
    for k in range(n_lanes):
        handle = open(lanes_dir / f"lane{k}.lock", "w", encoding="utf-8")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()  # held by another process — try the next slot
            continue
        _claimed.append(handle)
        set_current(k)
        return k
    return None


@atexit.register
def _release() -> None:
    """Drop every held lane claim (flock + close) so the slot frees on process exit."""
    try:
        import fcntl
    except ImportError:
        fcntl = None  # type: ignore[assignment]
    for handle in _claimed:
        try:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()
        except OSError:
            pass
    _claimed.clear()
