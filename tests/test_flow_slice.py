"""Offline slice for the continuous orchestrator, `flow.flow` (stdlib unittest).

Drives a bundle through Plan → Do → Check → sign-off → Act with **stub** leaves
and **stub** gates (no Claude, no TTY, no Docker), proving the deterministic
control flow and the load-bearing C6 guard. Run from the project root:
    PYTHONPATH=src python -m unittest discover -s tests
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from pdca_harness import brief, driver, flow, leaves, queue, signoff, state
from pdca_harness.config import Config, LeafConfig

DESIGN_TPL = Path(__file__).resolve().parents[1] / "templates" / "design-proposal.md.tpl"

# A minimal brief that flows straight through the stub Do/Check to AWAITING_SIGNOFF.
_BRIEF = (
    "- **Slug:** s\n- **Defect:** x\n- **Success criterion:** y\n"
    "- **Repo + branch target:** repo @ main\n- **Test file:** t_test.py\n"
)


def _stub_config(root: Path) -> Config:
    """All five leaves stubbed, gates empty (all-PASS stub rows)."""
    return Config(
        root=root,
        bundle_root=root / "results",
        process_dir=root / "process",
        templates_dir=root / "templates",  # empty → planner stub uses its fallback brief
        default_branch="main",
        tracker_system="github",
        tracker_url="",
        issue_id_example="#1",
        builder=LeafConfig(mode="stub", family="claude"),
        reviewer=LeafConfig(mode="stub", family="codex"),
        planner=LeafConfig(mode="stub", family="claude", interactive=True),
        signoff=LeafConfig(mode="stub", family="claude", interactive=True),
        act=LeafConfig(mode="stub", family="claude", interactive=True),
    )


class FlowSlice(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = _stub_config(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_full_flow_reaches_complete(self) -> None:
        # No brief yet: Plan (stub) authors one, then Do→Check→sign-off→COMPLETE.
        final = flow.flow(self.cfg, "FLOW", today="2026-06-04")
        self.assertEqual(final, state.COMPLETE)
        d = self.cfg.bundle("FLOW")
        self.assertTrue((d / "brief.md").exists())          # planner stub authored it
        self.assertTrue((d / "SUMMARY.md").exists())
        self.assertEqual(signoff.outcome_token(d / "SUMMARY.md"), "merged-wider")
        self.assertFalse((d / leaves.SIGNOFF_DECISION).exists())  # consumed

    def test_c6_blocks_accept_with_open_needs_human(self) -> None:
        # A sign-off leaf that accepts WITHOUT clearing §6 must not complete.
        def bad_signoff(d: Path, cfg: Config) -> None:
            (d / leaves.SIGNOFF_DECISION).write_text("accept\n", encoding="utf-8")
            # deliberately leaves §6 NEEDS-HUMAN open

        orig = leaves.run_signoff
        leaves.run_signoff = bad_signoff
        try:
            final = flow.flow(self.cfg, "BLOCKED", today="2026-06-04")
        finally:
            leaves.run_signoff = orig
        self.assertEqual(final, state.AWAITING_SIGNOFF)  # C6 stopped the accept
        d = self.cfg.bundle("BLOCKED")
        self.assertNotEqual(signoff.outcome_token(d / "SUMMARY.md"), "merged-wider")

    def test_iterate_do_then_complete(self) -> None:
        # First sign-off iterates; the flow rebuilds and the second accepts.
        calls = {"n": 0}

        def signoff_iter_then_accept(d: Path, cfg: Config) -> None:
            calls["n"] += 1
            summ = d / "SUMMARY.md"
            if calls["n"] == 1:
                (d / leaves.SIGNOFF_DECISION).write_text("iterate-do\n", encoding="utf-8")
            else:
                summ.write_text(summ.read_text().replace("- [ ]", "- [x]"), encoding="utf-8")
                (d / leaves.SIGNOFF_DECISION).write_text("accept\n", encoding="utf-8")

        orig = leaves.run_signoff
        leaves.run_signoff = signoff_iter_then_accept
        try:
            final = flow.flow(self.cfg, "ITER", today="2026-06-04")
        finally:
            leaves.run_signoff = orig
        self.assertEqual(final, state.COMPLETE)
        self.assertGreaterEqual(calls["n"], 2)  # iterated at least once

    def test_act_runs_on_complete(self) -> None:
        flow.flow(self.cfg, "ACTME", do_act=True, today="2026-06-04")
        log = self.cfg.process_dir / "act-log.md"
        self.assertTrue(log.exists())  # act stub wrote a dated review entry
        self.assertIn("2026-06-04", log.read_text(encoding="utf-8"))

    def test_batch_plans_many_and_completes_all(self) -> None:
        # The planner stub briefs two issues; the batch flow builds + signs off both.
        results = flow.flow_batch(self.cfg, do_act=True, today="2026-06-04")
        self.assertEqual(set(results), {"BATCH1", "BATCH2"})
        self.assertTrue(all(s == state.COMPLETE for s in results.values()))
        for iid in ("BATCH1", "BATCH2"):
            self.assertEqual(
                signoff.outcome_token(self.cfg.bundle(iid) / "SUMMARY.md"), "merged-wider"
            )

    def test_batch_iterate_then_complete(self) -> None:
        # One batch member iterates-do on its first sign-off; a later pass rebuilds
        # it and both end COMPLETE — exercises the multi-pass build→sign-off loop.
        # The batch sweep signs off via run_signoff_batch (one session per chunk).
        iterated = {"done": False}

        def signoff_batch(cfg: Config, bundles: list[Path]) -> None:
            for d in bundles:
                summ = d / "SUMMARY.md"
                if d.name == "issue_BATCH1" and not iterated["done"]:
                    iterated["done"] = True
                    (d / leaves.SIGNOFF_DECISION).write_text("iterate-do\n", encoding="utf-8")
                    continue
                summ.write_text(summ.read_text().replace("- [ ]", "- [x]"), encoding="utf-8")
                (d / leaves.SIGNOFF_DECISION).write_text("accept\n", encoding="utf-8")

        orig = leaves.run_signoff_batch
        leaves.run_signoff_batch = signoff_batch
        try:
            results = flow.flow_batch(self.cfg, today="2026-06-04", max_passes=4)
        finally:
            leaves.run_signoff_batch = orig
        self.assertTrue(iterated["done"])
        self.assertEqual(set(results), {"BATCH1", "BATCH2"})
        self.assertTrue(all(s == state.COMPLETE for s in results.values()))

    def test_batch_signoff_chunks_into_sessions(self) -> None:
        # The cheap-first queue is signed off in ONE session per chunk of
        # SIGNOFF_BATCH_SIZE (=5): six parked bundles → sessions of 5 then 1, all
        # reaching COMPLETE (testbed issue #2 — batch the interactive sign-off).
        ids = [f"C{i}" for i in range(6)]
        for iid in ids:
            d = self.cfg.bundle(iid)
            d.mkdir(parents=True)
            (d / "brief.md").write_text(_BRIEF, encoding="utf-8")

        sizes: list[int] = []
        real = leaves.run_signoff_batch

        def counting(cfg: Config, bundles: list[Path]) -> None:
            sizes.append(len(bundles))
            real(cfg, bundles)  # stub loops _stub_signoff → accept + clears §6

        leaves.run_signoff_batch = counting
        try:
            results = flow.flow_ids(self.cfg, ids, today="2026-06-06")
        finally:
            leaves.run_signoff_batch = real
        self.assertEqual(sizes, [flow.SIGNOFF_BATCH_SIZE, 1])   # 6 → 5 + 1, one pass
        self.assertTrue(all(s == state.COMPLETE for s in results.values()))

    def test_batch_resumes_existing_without_new_briefs(self) -> None:
        # A bundle already in flight (PLANNED) + a Plan session that briefs nothing
        # NEW must still be driven to COMPLETE — so re-running `flow --from-csv`
        # resumes where it left off instead of bailing with "no new briefs".
        d = self.cfg.bundle("RESUME")
        d.mkdir(parents=True)
        (d / "brief.md").write_text(
            "- **Slug:** resume-me\n- **Defect:** x\n- **Success criterion:** y\n"
            "- **Repo + branch target:** repo @ main\n- **Test file:** resume_test.py\n",
            encoding="utf-8",
        )
        self.assertEqual(state.state(d), state.PLANNED)
        orig = leaves.do_plan_batch
        leaves.do_plan_batch = lambda cfg, csv: None  # this Plan session briefs nothing new
        try:
            results = flow.flow_batch(self.cfg, today="2026-06-04")
        finally:
            leaves.do_plan_batch = orig
        self.assertEqual(results.get("RESUME"), state.COMPLETE)

    def test_batch_signoff_defers_iterate_rebuild(self) -> None:
        # In the batch sweep an iterate-do must be RECORDED but not rebuilt on the
        # spot (apply_now=False) — so the human reviews the whole queue first. The
        # bundle stays at ITERATE_DO with its downstream intact until the next pass.
        d = self.cfg.bundle("DEFER")
        d.mkdir(parents=True)
        (d / "brief.md").write_text(
            "- **Slug:** s\n- **Defect:** x\n- **Success criterion:** y\n"
            "- **Repo + branch target:** repo @ main\n- **Test file:** t_test.py\n",
            encoding="utf-8",
        )
        self.assertEqual(driver.run_issue(d, self.cfg), state.AWAITING_SIGNOFF)
        orig = leaves.run_signoff
        leaves.run_signoff = lambda dd, c: (dd / leaves.SIGNOFF_DECISION).write_text(
            "iterate-do\n", encoding="utf-8")
        try:
            action = flow._signoff_and_apply(
                self.cfg, d, by="t", today="2026-06-05", apply_now=False)
        finally:
            leaves.run_signoff = orig
        self.assertEqual(action, "iterate-do")
        self.assertEqual(state.state(d), state.ITERATE_DO)   # recorded, NOT yet rebuilt
        self.assertTrue((d / "patch.diff").exists())          # downstream still intact

    def test_signoff_skips_when_session_clears_summary(self) -> None:
        # An over-reaching sign-off session writes a decision AND deletes the bundle's
        # SUMMARY.md (doing the driver's transition work). The driver must skip — not
        # crash the whole sweep — and drop the stale decision so a re-drive is clean.
        d = self.cfg.bundle("WRECK")
        d.mkdir(parents=True)
        (d / "brief.md").write_text(
            "- **Slug:** s\n- **Defect:** x\n- **Success criterion:** y\n"
            "- **Repo + branch target:** repo @ main\n- **Test file:** t_test.py\n",
            encoding="utf-8",
        )
        self.assertEqual(driver.run_issue(d, self.cfg), state.AWAITING_SIGNOFF)

        def wreck(dd: Path, cfg: Config) -> None:
            (dd / leaves.SIGNOFF_DECISION).write_text("iterate-plan\n", encoding="utf-8")
            (dd / "SUMMARY.md").unlink()  # the over-reach that crashed the live batch

        orig = leaves.run_signoff
        leaves.run_signoff = wreck
        try:
            result = flow._signoff_and_apply(
                self.cfg, d, by="t", today="2026-06-06", apply_now=False)
        finally:
            leaves.run_signoff = orig
        self.assertIsNone(result)                               # skipped, no crash
        self.assertFalse((d / leaves.SIGNOFF_DECISION).exists())  # stale decision dropped

    def test_flow_ids_drives_listed_bundles_to_act(self) -> None:
        # Two already-briefed bundles (no Plan beat) + a bogus id: both reach COMPLETE,
        # the bogus id is skipped, and Act runs once at the end.
        for iid in ("IDA", "IDB"):
            d = self.cfg.bundle(iid)
            d.mkdir(parents=True)
            (d / "brief.md").write_text(
                "- **Slug:** s\n- **Defect:** x\n- **Success criterion:** y\n"
                "- **Repo + branch target:** repo @ main\n- **Test file:** t_test.py\n",
                encoding="utf-8",
            )
        results = flow.flow_ids(self.cfg, ["IDA", "IDB", "GHOST"], do_act=True, today="2026-06-05")
        self.assertEqual(set(results), {"IDA", "IDB"})
        self.assertTrue(all(s == state.COMPLETE for s in results.values()))
        self.assertTrue((self.cfg.process_dir / "act-log.md").exists())  # Act ran once

    def test_flow_ids_skips_complete_and_unbriefed(self) -> None:
        # An id with no bundle/brief and one already COMPLETE both fall out of the set.
        done = self.cfg.bundle("DONE")
        flow.flow(self.cfg, "DONE", today="2026-06-05")  # drive it to COMPLETE first
        self.assertEqual(state.state(done), state.COMPLETE)
        results = flow.flow_ids(self.cfg, ["DONE", "NEVER"], today="2026-06-05")
        self.assertEqual(results, {})  # nothing left to drive

    def test_batch_nothing_to_do_returns_empty(self) -> None:
        # No in-flight bundles + a Plan session that briefs nothing → {} (the caller
        # treats this as success, exit 0, not an error).
        orig = leaves.do_plan_batch
        leaves.do_plan_batch = lambda cfg, csv: None
        try:
            results = flow.flow_batch(self.cfg, today="2026-06-04")
        finally:
            leaves.do_plan_batch = orig
        self.assertEqual(results, {})

    def test_batch_isolates_a_failing_bundle(self) -> None:
        # One bundle's build always raises (a leaf left it half-written). The sweep
        # must isolate it and still drive the others to COMPLETE — never crash the
        # batch and lose the rest's progress (testbed issue #3).
        for iid in ("GOOD", "BAD"):
            d = self.cfg.bundle(iid)
            d.mkdir(parents=True)
            (d / "brief.md").write_text(_BRIEF, encoding="utf-8")

        real_run = driver.run_issue

        def flaky(d: Path, cfg: Config) -> str:
            if d.name == "issue_BAD":
                raise RuntimeError("boom: leaf left the bundle half-written")
            return real_run(d, cfg)

        flow.driver.run_issue = flaky
        try:
            results = flow.flow_ids(self.cfg, ["GOOD", "BAD"], today="2026-06-06")
        finally:
            flow.driver.run_issue = real_run
        self.assertEqual(results["GOOD"], state.COMPLETE)       # other bundle proceeded
        self.assertNotEqual(results["BAD"], state.COMPLETE)     # failing one isolated

    def test_queue_skips_a_bundle_whose_read_raises(self) -> None:
        # A bundle parked at AWAITING_SIGNOFF whose §6 read raises must be skipped by
        # the queue, not take the whole queue computation (and the sweep) down (#3).
        for iid in ("OKAY", "GARBLED"):
            d = self.cfg.bundle(iid)
            d.mkdir(parents=True)
            (d / "brief.md").write_text(_BRIEF, encoding="utf-8")
            self.assertEqual(driver.run_issue(d, self.cfg), state.AWAITING_SIGNOFF)

        real = signoff.open_needs_human

        def boom(p: Path) -> list[str]:
            if "GARBLED" in str(p):
                raise RuntimeError("garbled summary")
            return real(p)

        signoff.open_needs_human = boom
        try:
            names = {e.bundle.name for e in queue.awaiting_signoff(self.cfg)}
        finally:
            signoff.open_needs_human = real
        self.assertIn("issue_OKAY", names)        # healthy bundle still queued
        self.assertNotIn("issue_GARBLED", names)  # broken one skipped, no crash


class DesignProposalBrief(unittest.TestCase):
    """A GEPS-style feature brief is a richer Plan artifact, not a separate track."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = _stub_config(self.tmp)
        self.d = self.cfg.bundle("GEPS")
        self.d.mkdir(parents=True)
        shutil.copyfile(DESIGN_TPL, self.d / "brief.md")  # the design-proposal template

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_template_keeps_driver_parsed_fields(self) -> None:
        fields = brief.parse_fields(self.d / "brief.md")
        for label in ("slug", "success criterion", "repo + branch target", "test file"):
            self.assertIn(label, fields, f"design-proposal template lost parsed field: {label}")

    def test_feature_brief_flows_and_renders_goal(self) -> None:
        # Do (stub) + Check (stub gates + reviewer) run normally — there IS code.
        self.assertEqual(driver.run_issue(self.d, self.cfg), state.AWAITING_SIGNOFF)
        summary = (self.d / "SUMMARY.md").read_text(encoding="utf-8")
        self.assertIn("Defect / goal:", summary)               # assemble fallback rendered
        self.assertIn("the capability this adds", summary)     # the Goal value, not blank


if __name__ == "__main__":
    unittest.main()
