"""Separate-process lane safety (issue #98): the env pin, the cross-process claim, and
the publish checkout lock.

The in-process worker pool was always lane-safe; these cover the *standalone-process*
path — a human running several ``pdca flow <id>`` terminals over one workspace. All
stdlib, no Docker, no network (the flock mechanics run against scratch lockfiles).
"""

from __future__ import annotations

import fcntl
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from pdca_harness import lane, publish


class FromEnv(unittest.TestCase):
    """``$PDCA_LANE`` is the explicit, by-hand lane pin; a bad value reads as serial."""

    def _from_env(self, value: str | None) -> int | None:
        env = {} if value is None else {"PDCA_LANE": value}
        with mock.patch.dict(os.environ, env, clear=False):
            if value is None:
                os.environ.pop("PDCA_LANE", None)
            return lane.from_env()

    def test_unset_is_none(self) -> None:
        self.assertIsNone(self._from_env(None))

    def test_blank_is_none(self) -> None:
        self.assertIsNone(self._from_env("   "))

    def test_numeric(self) -> None:
        self.assertEqual(self._from_env("0"), 0)
        self.assertEqual(self._from_env("2"), 2)
        self.assertEqual(self._from_env(" 3 "), 3)

    def test_garbage_is_none(self) -> None:
        # A malformed pin must not crash the command — treat it as serial.
        self.assertIsNone(self._from_env("lane1"))


class Claim(unittest.TestCase):
    """``claim`` hands out distinct slots and refuses once every slot is held."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        # Each test starts with no claims held and no current lane.
        lane._release()
        lane.set_current(None)
        self.addCleanup(lane._release)
        self.addCleanup(lane.set_current, None)

    def test_first_claim_is_slot_zero_and_sets_current(self) -> None:
        self.assertEqual(lane.claim(2, lanes_dir=self.tmp), 0)
        self.assertEqual(lane.current(), 0)

    def test_distinct_slots_until_exhausted(self) -> None:
        # flock keys off the open file description, so a second open() of the same
        # lockfile contends even within one process — exactly the cross-process case.
        self.assertEqual(lane.claim(2, lanes_dir=self.tmp), 0)
        self.assertEqual(lane.claim(2, lanes_dir=self.tmp), 1)
        self.assertIsNone(lane.claim(2, lanes_dir=self.tmp))  # all slots held

    def test_zero_lanes_is_none(self) -> None:
        self.assertIsNone(lane.claim(0, lanes_dir=self.tmp))
        self.assertIsNone(lane.current())

    def test_release_frees_the_slot(self) -> None:
        self.assertEqual(lane.claim(1, lanes_dir=self.tmp), 0)
        lane._release()
        # The lockfile is free again, so a fresh claim re-grabs slot 0.
        self.assertEqual(lane.claim(1, lanes_dir=self.tmp), 0)


class CheckoutLock(unittest.TestCase):
    """``publish._checkout_lock`` holds an exclusive flock for its whole body, so a
    concurrent publish queues instead of racing the dirty guard (#98)."""

    def setUp(self) -> None:
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.repo, True)
        (self.repo / ".git").mkdir()

    def test_held_lock_blocks_a_second_acquirer(self) -> None:
        lock_path = self.repo / ".git" / "pdca-publish.lock"
        with publish._checkout_lock(self.repo):
            # A second, independent open of the same lockfile must NOT be grantable while
            # the context manager holds it — prove it with a non-blocking acquire.
            other = open(lock_path, "w", encoding="utf-8")
            self.addCleanup(other.close)
            with self.assertRaises(OSError):
                fcntl.flock(other.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Once released, the same non-blocking acquire succeeds.
        fcntl.flock(other.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(other.fileno(), fcntl.LOCK_UN)

    def test_second_acquirer_proceeds_after_release(self) -> None:
        # Two threads contending the blocking lock serialize: the second only enters its
        # body after the first leaves. Order is recorded to prove no interleave.
        order: list[str] = []
        first_in = threading.Event()
        release = threading.Event()

        def first() -> None:
            with publish._checkout_lock(self.repo):
                order.append("first-enter")
                first_in.set()
                release.wait(2)
                order.append("first-exit")

        def second() -> None:
            first_in.wait(2)
            with publish._checkout_lock(self.repo):
                order.append("second-enter")

        t1 = threading.Thread(target=first)
        t2 = threading.Thread(target=second)
        t1.start()
        first_in.wait(2)
        t2.start()
        # Give the second thread a beat to *try* (and block) before we let the first out.
        t2.join(0.2)
        release.set()
        t1.join(2)
        t2.join(2)
        self.assertEqual(order, ["first-enter", "first-exit", "second-enter"])


class AssignLane(unittest.TestCase):
    """``cli._assign_lane`` is the wiring: explicit pin wins; standalone worktree-driving
    commands auto-claim when lanes exist; pooled / non-worktree commands don't."""

    def setUp(self) -> None:
        from types import SimpleNamespace

        from pdca_harness import cli

        self.cli = cli
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        # cfg.root.parent is the workspace; put a couple of lane worktrees beside it.
        self.root = self.tmp / "testbed"
        self.root.mkdir()
        self.cfg = SimpleNamespace(root=self.root, lanes=1)
        self.NS = SimpleNamespace
        lane._release()
        lane.set_current(None)
        self.addCleanup(lane._release)
        self.addCleanup(lane.set_current, None)

    def _args(self, **kw):
        kw.setdefault("issue_id", None)
        kw.setdefault("lanes", None)
        return self.NS(**kw)

    def test_explicit_pin_wins(self) -> None:
        with mock.patch.dict(os.environ, {"PDCA_LANE": "1"}):
            self.cli._assign_lane(self.cfg, self._args(cmd="flow", issue_id="x"))
        self.assertEqual(lane.current(), 1)

    def test_standalone_flow_claims_when_lane_worktrees_exist(self) -> None:
        (self.tmp / "gramps-6.1-lane0").mkdir()
        (self.tmp / "gramps-6.1-lane1").mkdir()
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PDCA_LANE", None)
            self.cli._assign_lane(self.cfg, self._args(cmd="flow", issue_id="x"))
        self.assertEqual(lane.current(), 0)

    def test_no_lane_worktrees_stays_serial(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PDCA_LANE", None)
            self.cli._assign_lane(self.cfg, self._args(cmd="flow", issue_id="x"))
        self.assertIsNone(lane.current())

    def test_pooled_batch_does_not_claim(self) -> None:
        # `batch` fans out across the in-process pool, which assigns slots per worker —
        # the main thread must not also grab one.
        (self.tmp / "gramps-6.1-lane0").mkdir()
        self.cfg.lanes = 2
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PDCA_LANE", None)
            self.cli._assign_lane(self.cfg, self._args(cmd="batch"))
        self.assertIsNone(lane.current())


if __name__ == "__main__":
    unittest.main()
