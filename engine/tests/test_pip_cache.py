"""Regression guard: every Docker-backed runner mounts the persistent pip cache, and the
image pre-creates that cache dir owned by `runner` (issue #68).

The per-run `pip install -e ./gramps[testing]` is the recurring minutes-cost of a
Docker-backed gate. Mounting one named volume at the runner's pip cache lets that install
reuse downloaded/built wheels across runs (measured ~41s → ~24s on the C4 image). These
checks are structural + Docker-free: they keep a new runner from silently dropping the
mount, and keep the Dockerfile from dropping the ownership pre-create that lets the
non-root `runner` write a freshly-mounted named volume.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNERS_DIR = REPO_ROOT / "engine/scripts/ubuntu"
DOCKERFILE = REPO_ROOT / "engine/docker/Dockerfile.ubuntu"

CACHE_PATH = "/home/runner/.cache/pip"
# The mount line each runner uses (name overridable via $GRAMPS_TESTBED_PIPCACHE).
_MOUNT = re.compile(
    r'-v\s+"\$\{GRAMPS_TESTBED_PIPCACHE:-[^}]+\}":' + re.escape(CACHE_PATH)
)


def _docker_backed_runners() -> list[Path]:
    """Every run-*.sh that starts a container (so must mount the cache)."""
    return sorted(
        p for p in RUNNERS_DIR.glob("run-*.sh")
        if "docker run" in p.read_text(encoding="utf-8")
    )


class PipCacheMount(unittest.TestCase):
    def test_there_are_docker_backed_runners(self) -> None:
        # Guard the guard: if the glob finds nothing, the assertions below are vacuous.
        self.assertTrue(_docker_backed_runners(), "no Docker-backed runners found")

    def test_every_docker_runner_mounts_the_pip_cache(self) -> None:
        missing = [
            p.name for p in _docker_backed_runners()
            if not _MOUNT.search(p.read_text(encoding="utf-8"))
        ]
        self.assertEqual(
            missing, [],
            f"Docker-backed runner(s) missing the {CACHE_PATH} cache mount — a repeat "
            f"gate run will re-resolve gramps' deps every container start (issue #68): "
            + ", ".join(missing),
        )


class DockerfilePrecreatesCacheDir(unittest.TestCase):
    def test_cache_dir_is_made_and_owned_by_runner(self) -> None:
        body = DOCKERFILE.read_text(encoding="utf-8")
        # A freshly-mounted named volume inherits the image dir's ownership; the dir must
        # be pre-created (under the mkdir that the `chown -R runner:runner /home/runner`
        # then covers) or the non-root runner can't write the cache.
        self.assertRegex(
            body, re.compile(r"mkdir -p[^\n]*" + re.escape(CACHE_PATH)),
            f"Dockerfile must `mkdir -p {CACHE_PATH}` so the named cache volume initializes "
            "owned by `runner` (issue #68)",
        )
        self.assertRegex(
            body, re.compile(r"chown -R runner:runner[^\n]*/home/runner"),
            "the pre-created cache dir must be chown'd to runner (the `chown -R "
            "runner:runner … /home/runner` recurses into .cache/pip)",
        )


if __name__ == "__main__":
    unittest.main()
