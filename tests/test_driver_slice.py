"""End-to-end vertical slice for the PDCA driver (stdlib unittest — no deps).

Run from the project root:  PYTHONPATH=src python -m unittest discover -s tests
Exercises the full control flow on the toy brief with stub leaves/gates:
init → Do → gates → reviewer → assembled SUMMARY → human sign-off → COMPLETE,
plus the C6 accept-gate, the independence contract, and an iterate transition.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pdca_harness import act, driver, gates, queue, leaves, signoff, state
from pdca_harness.config import Config, LeafConfig

TOY_BRIEF = Path(__file__).resolve().parents[1] / "examples" / "toy" / "brief.md"


def _stub_config(root: Path) -> Config:
    return Config(
        root=root,
        bundle_root=root / "results",
        process_dir=root / "process",
        templates_dir=root / "templates",
        default_branch="main",
        tracker_system="github",
        tracker_url="",
        issue_id_example="#1",
        builder=LeafConfig(mode="stub", family="claude"),
        reviewer=LeafConfig(mode="stub", family="codex"),
    )


class VerticalSlice(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = _stub_config(self.tmp)
        self.d = self.cfg.bundle("TOY")
        self.d.mkdir(parents=True)
        shutil.copyfile(TOY_BRIEF, self.d / "brief.md")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_runs_to_awaiting_signoff(self) -> None:
        self.assertEqual(state.state(self.d), state.PLANNED)
        final = driver.run_issue(self.d, self.cfg)
        self.assertEqual(final, state.AWAITING_SIGNOFF)
        for name in ("patch.diff", "build-notes.md", "check-gates.json", "check-review.md", "SUMMARY.md", "test_toy.py"):
            self.assertTrue((self.d / name).exists(), f"missing {name}")

    def test_independence_contract(self) -> None:
        # The reviewer's input list must never contain build-notes.md.
        inputs = leaves.reviewer_input_paths(self.d)
        self.assertNotIn(self.d / "build-notes.md", inputs)

    def test_accept_blocked_until_needs_human_cleared(self) -> None:
        driver.run_issue(self.d, self.cfg)
        summary = self.d / "SUMMARY.md"
        # Stub reviewer flags the always-human validation item → §6 is non-empty.
        self.assertTrue(signoff.open_needs_human(summary))
        # Simulate the human clearing §6 (check the box), then accept.
        summary.write_text(summary.read_text().replace("- [ ]", "- [x]"), encoding="utf-8")
        self.assertFalse(signoff.open_needs_human(summary))
        signoff.record(summary, action="accept", by="tester", date="2026-01-01")
        self.assertEqual(state.state(self.d), state.COMPLETE)

    def test_review_emits_complete_5_5_1_table(self) -> None:
        # The reviewer (stub or command) must always emit one verdict row per 5/5/1
        # element — the overview the human reads. No element may be dropped.
        driver.run_issue(self.d, self.cfg)
        review = (self.d / "check-review.md").read_text(encoding="utf-8")
        for _elem, label, _kind, _oracle in gates.canonical_elements():
            self.assertIn(label, review, f"reviewer verdict table missing {label}")
        # The validation row is NEEDS-HUMAN and reaches §6 as exactly one open item.
        self.assertEqual(len(signoff.open_needs_human(self.d / "SUMMARY.md")), 1)

    def test_needs_human_lifted_from_table_row(self) -> None:
        # A NEEDS-HUMAN verdict in the table (not a bullet) still becomes a §6 item.
        from pdca_harness import assemble
        items = assemble._needs_human(
            "| Item | Verdict | Basis |\n|---|---|---|\n"
            "| C5 Causal adequacy | PASS | grounded |\n"
            "| Validation — fitness-to-purpose | NEEDS-HUMAN | is this the right thing? |\n"
        )
        self.assertEqual(len(items), 1)
        self.assertIn("Validation", items[0])
        self.assertIn("is this the right thing?", items[0])

    def test_assemble_tolerates_missing_review(self) -> None:
        # A dropped reviewer leaves no check-review.md; assemble must NOT crash — it
        # flags a §6 re-review item and still produces SUMMARY (recovers the bundle).
        from pdca_harness import assemble
        driver.run_issue(self.d, self.cfg)
        (self.d / "check-review.md").unlink()
        (self.d / "SUMMARY.md").unlink()
        self.assertEqual(state.state(self.d), state.CHECKED)  # the crash state
        assemble.assemble_summary(self.d, self.cfg)           # must not raise
        self.assertTrue((self.d / "SUMMARY.md").exists())
        self.assertTrue(signoff.open_needs_human(self.d / "SUMMARY.md"))  # re-review flagged

    def test_review_failure_writes_fallback(self) -> None:
        # A command-mode reviewer that exits non-zero (dropped connection) must leave a
        # placeholder review flagging NEEDS-HUMAN, not nothing.
        import dataclasses
        cfg = dataclasses.replace(
            self.cfg, reviewer=LeafConfig(mode="command", family="x", argv=["false"]))
        leaves.run_review(self.d, cfg)
        review = (self.d / "check-review.md").read_text(encoding="utf-8")
        self.assertIn("NOT COMPLETED", review)
        self.assertIn("- NEEDS-HUMAN", review)

    def test_review_empty_output_writes_fallback(self) -> None:
        # A reviewer that exits 0 but writes no check-review.md is the case that crashed
        # the batch — it must also fall back, not silently leave the bundle review-less.
        import dataclasses
        cfg = dataclasses.replace(
            self.cfg, reviewer=LeafConfig(mode="command", family="x", argv=["true"]))
        leaves.run_review(self.d, cfg)
        self.assertIn("- NEEDS-HUMAN", (self.d / "check-review.md").read_text(encoding="utf-8"))

    def test_iterate_to_do_archives_downstream(self) -> None:
        # iterate-do ARCHIVES the prior attempt into iteration-v1/ (never deletes it):
        # the downstream leaves the top level → state PLANNED, brief.md stays, and the
        # patch is preserved under iteration-v1/.
        driver.run_issue(self.d, self.cfg)
        summary = self.d / "SUMMARY.md"
        signoff.record(summary, action="iterate-do", by="tester", date="2026-01-01")
        self.assertEqual(state.state(self.d), state.ITERATE_DO)
        driver.advance(self.d, self.cfg)  # archive + rebuild
        self.assertEqual(state.state(self.d), state.PLANNED)
        self.assertFalse((self.d / "patch.diff").exists())          # left the top level
        self.assertTrue((self.d / "brief.md").exists())             # brief stays for the rebuild
        self.assertTrue((self.d / "iteration-v1" / "patch.diff").exists())   # preserved, not deleted
        self.assertTrue((self.d / "iteration-v1" / "SUMMARY.md").exists())

    def test_iterate_to_plan_archives_attempt(self) -> None:
        # iterate-plan archives the WHOLE attempt incl. the brief → state UNPLANNED;
        # the brief + downstream are preserved under iteration-v1/, never deleted.
        driver.run_issue(self.d, self.cfg)
        summary = self.d / "SUMMARY.md"
        signoff.record(summary, action="iterate-plan", by="tester", date="2026-01-01")
        driver.advance(self.d, self.cfg)
        self.assertEqual(state.state(self.d), state.UNPLANNED)
        self.assertFalse((self.d / "brief.md").exists())                     # left the top level
        self.assertTrue((self.d / "iteration-v1" / "brief.md").exists())     # preserved
        self.assertTrue((self.d / "iteration-v1" / "patch.diff").exists())   # attempt preserved

    def test_iterate_do_carries_forward_into_brief(self) -> None:
        # An iterate-do must fold the prior attempt's insight into brief.md BEFORE the
        # downstream clear, so the rebuilt Do (which reads brief.md only) isn't blind:
        # the §9 rationale + the failing gate, in an `## Iteration N — carry-forward`
        # block that survives the clear.
        driver.run_issue(self.d, self.cfg)
        summary = self.d / "SUMMARY.md"
        # A failing gating gate, so the carry-forward has gate evidence to lift.
        gates_json = self.d / "check-gates.json"
        gates_json.write_text(json.dumps({"overall": "fail", "rows": [
            {"check": "C4-verify", "result": "fail", "path_line": "red-without-fix=FAIL",
             "oracle": "run-verify.sh", "rule_id": "C4-verify", "gating": True},
        ]}), encoding="utf-8")
        signoff.record(summary, action="iterate-do", by="tester", date="2026-01-01",
                       delta="test asserts the wrong attribute; assert navigation_type instead")
        self.assertEqual(state.state(self.d), state.ITERATE_DO)

        driver.advance(self.d, self.cfg)  # carry-forward, then clear

        self.assertEqual(state.state(self.d), state.PLANNED)
        self.assertTrue((self.d / "brief.md").exists())          # survived the clear
        brief_text = (self.d / "brief.md").read_text(encoding="utf-8")
        self.assertIn("## Iteration 1 — carry-forward", brief_text)
        self.assertIn("assert navigation_type instead", brief_text)   # the §9 rationale
        self.assertIn("C4-verify", brief_text)                        # the failing gate
        self.assertIn("Success criterion", brief_text)                # the end-result nudge

    def test_carry_forward_noop_without_insight(self) -> None:
        # No rationale and no failing gate → no carry-forward block appended.
        driver.run_issue(self.d, self.cfg)
        (self.d / "check-gates.json").write_text(
            json.dumps({"overall": "pass", "rows": []}), encoding="utf-8")
        signoff.record(self.d / "SUMMARY.md", action="iterate-do", by="t", date="2026-01-01")
        driver.advance(self.d, self.cfg)
        self.assertNotIn("carry-forward", (self.d / "brief.md").read_text(encoding="utf-8"))


class ConfiguredGates(unittest.TestCase):
    """The config-driven, single-sourced gates (docs 04)."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _cfg(self, checks: list[dict]) -> Config:
        cfg = _stub_config(self.tmp)
        cfg.gates_checks = checks
        return cfg

    def test_passing_and_failing_repo_gates(self) -> None:
        cfg = self._cfg([
            {"id": "ok", "tier": "T1", "label": "ok", "cmd": "true", "gating": True, "scope": "repo"},
            {"id": "bad", "tier": "T2", "label": "bad", "cmd": "false", "gating": True, "scope": "repo"},
        ])
        result = gates.run_working_tree(cfg)
        self.assertEqual(result["overall"], "fail")  # one gating row failed
        by_id = {r["rule_id"]: r["result"] for r in result["rows"]}
        self.assertEqual(by_id["ok"], "pass")
        self.assertEqual(by_id["bad"], "fail")

    def test_working_tree_skips_bundle_scope(self) -> None:
        cfg = self._cfg([
            {"id": "b", "tier": "C4", "label": "bundle-only", "cmd": "false", "gating": True, "scope": "bundle"},
        ])
        result = gates.run_working_tree(cfg)
        # The bundle-scoped failing check is skipped, so the working tree is green.
        self.assertEqual(result["overall"], "pass")
        self.assertNotIn("b", {r["rule_id"] for r in result["rows"]})


class BuilderGuard(unittest.TestCase):
    """The PreToolUse hook enforcing the builder's STOP discipline."""

    GUARD = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "builder_guard.py"

    def _exit(self, command: str) -> int:
        payload = json.dumps({"tool_input": {"command": command}})
        r = subprocess.run(
            [sys.executable, str(self.GUARD)],
            input=payload, capture_output=True, text=True,
        )
        return r.returncode

    def test_allows_push_and_draft_pr(self) -> None:
        self.assertEqual(self._exit("git push origin feat"), 0)
        self.assertEqual(self._exit("gh pr create --draft --fill"), 0)

    def test_blocks_ready_and_merge(self) -> None:
        self.assertEqual(self._exit("gh pr ready 123"), 2)
        self.assertEqual(self._exit("gh pr merge 123 --squash"), 2)

    def test_blocks_ready_when_chained_after_allowed(self) -> None:
        # Each segment is checked independently; the ready-mark segment is blocked.
        self.assertEqual(self._exit("git push origin feat && gh pr ready 123"), 2)

    def test_blocks_wrapped_ready(self) -> None:
        self.assertEqual(self._exit("timeout 30 gh pr merge 123"), 2)


class SignoffQueue(unittest.TestCase):
    """The cheap-first sign-off burn-down (docs 03 §sign-off queue)."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = _stub_config(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run_issue(self, issue_id: str) -> Path:
        d = self.cfg.bundle(issue_id)
        d.mkdir(parents=True)
        shutil.copyfile(TOY_BRIEF, d / "brief.md")
        driver.run_issue(d, self.cfg)
        return d

    def test_cheap_confirms_come_first(self) -> None:
        needs = self._run_issue("NEEDS")  # stub reviewer leaves §6 non-empty
        cheap = self._run_issue("CHEAP")
        # Simulate the human having adjudicated CHEAP's §6 (box checked).
        summ = cheap / "SUMMARY.md"
        summ.write_text(summ.read_text().replace("- [ ]", "- [x]"), encoding="utf-8")

        entries = queue.awaiting_signoff(self.cfg)
        self.assertEqual([e.bundle.name for e in entries], ["issue_CHEAP", "issue_NEEDS"])
        self.assertTrue(entries[0].cheap)
        self.assertFalse(entries[1].cheap)
        self.assertEqual(entries[1].open_needs_human, 1)
        self.assertEqual(needs.name, "issue_NEEDS")


class ActTooling(unittest.TestCase):
    """The L4 Act tooling — bundle index, patterns, act-log scaffold (docs 03 §Act)."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = _stub_config(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _complete(self, issue_id: str, candidate: str) -> Path:
        d = self.cfg.bundle(issue_id)
        d.mkdir(parents=True)
        shutil.copyfile(TOY_BRIEF, d / "brief.md")
        driver.run_issue(d, self.cfg)
        summ = d / "SUMMARY.md"
        t = summ.read_text(encoding="utf-8").replace("- [ ]", "- [x]")  # clear §6
        t = t.replace("- (empty is the common case)", f"- [x] {candidate}")  # add §10 hint
        summ.write_text(t, encoding="utf-8")
        signoff.record(summ, action="accept", by="t", date="2026-06-01")
        return d

    def test_index_only_sees_frozen(self) -> None:
        self._complete("DONE", "spec field X ambiguous")
        # An in-flight bundle (no sign-off) must not appear in the Act index.
        live = self.cfg.bundle("LIVE")
        live.mkdir(parents=True)
        shutil.copyfile(TOY_BRIEF, live / "brief.md")
        driver.run_issue(live, self.cfg)  # parks at AWAITING_SIGNOFF
        names = [e.bundle.name for e in act.index(self.cfg)]
        self.assertEqual(names, ["issue_DONE"])

    def test_patterns_and_scaffold(self) -> None:
        self._complete("A", "spec field X ambiguous")
        self._complete("B", "spec field X ambiguous")
        entries = act.index(self.cfg)
        self.assertEqual(len(entries), 2)
        self.assertTrue(all(e.outcome == "merged-wider" for e in entries))
        pats = act.patterns(entries)
        self.assertTrue(pats["act_candidates"], "recurring §10 hint not detected")
        scaffold = act.scaffold_entry(entries, pats, date="2026-06-04")
        self.assertIn("2026-06-04", scaffold)
        self.assertIn("cycles considered: A, B", scaffold)
        self.assertIn("TODO", scaffold)  # deltas left to the human

    def test_append_creates_log(self) -> None:
        self._complete("A", "x")
        entries = act.index(self.cfg)
        log = act.append_entry(self.cfg, act.scaffold_entry(entries, act.patterns(entries), "2026-06-04"))
        self.assertTrue(log.exists())
        self.assertIn("Act review — 2026-06-04", log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
