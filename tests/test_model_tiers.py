"""The instance's model-tier configuration (PR #334) and the two guarantees the Codex
review on that PR asked for.

INSTANCE-SPECIFIC: these read the real ``pdca.toml`` at the repo root, because what is
under test is this instance's LADDER — which tier a bundle routes to, and whether a
codex-built bundle still gets a differently-vendored read. A template test cannot assert
that; the template ships the ladder commented out.

The telemetry half (:func:`leaves._record_loop_attempt` recording model+effort) is a
change to template machinery, staged here pending the upstream enhancement issue on
pdca-harness — see the PR description.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from pdca_harness import families, leaves
from pdca_harness.config import Config
from pdca_harness.leaves import LeafConfig

ROOT = Path(__file__).resolve().parents[1]


def _resolved_argv(cfg: Config, leaf: LeafConfig) -> list[str]:
    """The argv the driver would actually spawn: the leaf's own, plus whatever the
    family profile maps from the `model` / `effort` keys."""
    argv = list(leaf.argv)
    return argv + leaves._mapped_argv(leaf, families.resolve(leaf.family, cfg.families), argv)


class LadderRouting(unittest.TestCase):
    """Each tier is reachable, and reachable only the way the config says."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg = Config.load(ROOT / "pdca.toml")

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _bundle(self, *, difficulty: str = "", pin: str = "") -> Path:
        d = self.tmp / "issue_1"
        d.mkdir(exist_ok=True)
        body = "# Brief\n\n- **Slug:** s\n"
        if difficulty:
            body += f"- **Difficulty:** {difficulty}\n"
        if pin:
            body += f"- **Do model:** {pin}\n"
        (d / "brief.md").write_text(body, encoding="utf-8")
        return d

    def _tier(self, *, difficulty: str = "", pin: str = "", n: int = 1) -> tuple[str, str, str]:
        b = leaves.select_builder(self._bundle(difficulty=difficulty, pin=pin), self.cfg, n)
        return b.family, leaves._effective_model(b, self.cfg), b.effort

    def test_base_tier_is_the_cheap_one(self) -> None:
        self.assertEqual(self._tier(difficulty="low"), ("claude", "sonnet", "high"))

    def test_high_difficulty_auto_routes_to_opus(self) -> None:
        self.assertEqual(self._tier(difficulty="high"), ("claude", "opus", "xhigh"))

    def test_iterate_escalates_above_every_first_attempt_tier(self) -> None:
        # The ladder must OUTRANK the auto-route, or a `high` bundle would iterate onto
        # the very tier it just failed on.
        self.assertEqual(self._tier(difficulty="low", n=2), ("claude", "opus", "max"))
        self.assertEqual(self._tier(difficulty="high", n=2), ("claude", "opus", "max"))

    def test_every_pin_lands_on_its_own_backend(self) -> None:
        for pin, expected in {
            "sonnet": ("claude", "sonnet", "high"),
            "fable": ("claude", "fable", "high"),
            "opus": ("claude", "opus", "xhigh"),
            "opus-max": ("claude", "opus", "max"),
            "codex": ("codex", "gpt-5.6-sol", "high"),
        }.items():
            with self.subTest(pin=pin):
                self.assertEqual(self._tier(pin=pin), expected)

    def test_a_pin_overrides_the_difficulty_route(self) -> None:
        # `sonnet` exists precisely to force the base tier on a bundle the router would
        # otherwise send to opus.
        self.assertEqual(self._tier(difficulty="high", pin="sonnet"), ("claude", "sonnet", "high"))

    def test_effort_is_pinned_on_every_tier(self) -> None:
        # An unpinned tier would inherit whatever the CLI defaults to that week — the one
        # thing the ladder must not do.
        for pin in ("sonnet", "fable", "opus", "opus-max", "codex"):
            with self.subTest(pin=pin):
                self.assertTrue(self._tier(pin=pin)[2])

    def test_claude_tiers_keep_the_narrow_bash_grant(self) -> None:
        # The ladder changes which model runs, never what it is allowed to run: this
        # instance confines Bash to git/python3 rather than granting it wholesale.
        for pin in ("", "sonnet", "fable", "opus", "opus-max"):
            with self.subTest(pin=pin):
                b = leaves.select_builder(self._bundle(pin=pin), self.cfg, 1)
                tools = b.argv[b.argv.index("--allowedTools") + 1]
                self.assertIn("Bash(git *)", tools)
                self.assertNotIn("Bash,", tools)


class CrossVendorReview(unittest.TestCase):
    """A codex-built bundle must still get a differently-vendored read (Codex review,
    PR #334): [leaves.reviewer] is codex, so pinning the codex BUILDER collides with the
    reviewer≠builder contract in docs/INTEGRATION.md §4."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg = Config.load(ROOT / "pdca.toml")

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _applicable(self, body: str) -> list[dict]:
        d = self.tmp / "issue_1"
        d.mkdir(exist_ok=True)
        (d / "brief.md").write_text(body, encoding="utf-8")
        return [s for s in self.cfg.advisory_leaves if leaves._advisory_applies(s, d)]

    def test_the_reviewer_is_codex(self) -> None:
        # The premise of this whole class; if it ever changes, re-derive the gap.
        self.assertEqual(self.cfg.reviewer.family, "codex")

    def test_codex_built_low_difficulty_bundle_still_gets_a_claude_advisory(self) -> None:
        # THE REGRESSION THE REVIEW CAUGHT: before the `adversary-codex-built` entry, this
        # returned [] — codex builder + codex reviewer + no advisory = no cross-vendor read.
        applicable = self._applicable("- **Difficulty:** low\n- **Do model:** codex\n")
        self.assertTrue(applicable)
        self.assertTrue(any(s["family"] == "claude" for s in applicable))

    def test_every_claude_builder_tier_leaves_the_codex_reviewer_decorrelated(self) -> None:
        # The common path needs no advisory to be cross-vendor: claude builder vs codex
        # reviewer is already decorrelated, so a low-difficulty claude bundle running zero
        # advisories is correct, not a gap.
        self.assertEqual(self._applicable("- **Difficulty:** low\n"), [])

    def test_high_difficulty_still_runs_the_adversary(self) -> None:
        ids = {s["id"] for s in self._applicable("- **Difficulty:** high\n")}
        self.assertIn("adversary", ids)

    def test_advisory_entries_are_pinned_and_distinctly_named(self) -> None:
        ids = [s["id"] for s in self.cfg.advisory_leaves]
        self.assertEqual(len(ids), len(set(ids)))  # distinct ⇒ distinct artifact files
        for spec in self.cfg.advisory_leaves:
            with self.subTest(id=spec["id"]):
                self.assertTrue(spec.get("model"))
                self.assertTrue(spec.get("effort"))


class TelemetryRecordsTheTier(unittest.TestCase):
    """loop-telemetry.json must distinguish tiers WITHIN a vendor (Codex review, PR #334):
    sonnet/high, opus/xhigh and opus/max all report family `claude`, so family alone cannot
    answer the escalation-calibration question the file exists to answer."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = Config.load(ROOT / "pdca.toml")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _record(self, builder: LeafConfig, n: int = 1) -> dict:
        d = self.tmp / "issue_1"
        d.mkdir(exist_ok=True)
        leaves._record_loop_attempt(d, n, builder, self.cfg)
        return json.loads((d / "loop-telemetry.json").read_text(encoding="utf-8"))

    def test_model_from_the_key(self) -> None:
        leaf = LeafConfig(mode="command", family="claude", argv=["claude"],
                          model="opus", effort="xhigh")
        entry = self._record(leaf)["attempts"][0]
        self.assertEqual((entry["model"], entry["effort"]), ("opus", "xhigh"))

    def test_model_from_argv_when_the_key_is_the_brief_pin_selector(self) -> None:
        # Every builder_variant is in this shape: `model` is the #167 selector, so the CLI
        # model exists ONLY in argv. Reading builder.model alone would record "".
        leaf = LeafConfig(mode="command", family="claude",
                          argv=["claude", "-p", "--model", "sonnet"], effort="high")
        self.assertEqual(self._record(leaf)["attempts"][0]["model"], "sonnet")

    def test_codex_model_flag_is_read_too(self) -> None:
        leaf = LeafConfig(mode="command", family="codex",
                          argv=["codex", "exec", "-m", "gpt-5.6-sol"], effort="high")
        self.assertEqual(self._record(leaf)["attempts"][0]["model"], "gpt-5.6-sol")

    def test_argv_beats_the_key_when_they_disagree(self) -> None:
        # THE BUG THE LOCAL CODEX REVIEW CAUGHT: _mapped_argv does NOT append the key's flag
        # when argv already carries one, so argv is what runs. Telemetry preferring the key
        # would name a model+effort the command never used — and silently corrupt exactly the
        # escalation calibration this file exists for.
        leaf = LeafConfig(mode="command", family="claude",
                          argv=["claude", "-p", "--model", "sonnet", "--effort", "low"],
                          model="opus", effort="high")
        # Cross-check the premise against the real mapper: it adds nothing here.
        self.assertEqual(_resolved_argv(self.cfg, leaf), leaf.argv)
        entry = self._record(leaf)["attempts"][0]
        self.assertEqual((entry["model"], entry["effort"]), ("sonnet", "low"))

    def test_argv_beats_the_key_for_codex_too(self) -> None:
        leaf = LeafConfig(mode="command", family="codex",
                          argv=["codex", "exec", "-m", "gpt-5.6-sol",
                                "-c", "model_reasoning_effort=xhigh"],
                          model="other-model", effort="medium")
        self.assertEqual(_resolved_argv(self.cfg, leaf), leaf.argv)
        entry = self._record(leaf)["attempts"][0]
        self.assertEqual((entry["model"], entry["effort"]), ("gpt-5.6-sol", "xhigh"))

    def test_equals_form_of_a_flag_is_read(self) -> None:
        leaf = LeafConfig(mode="command", family="claude",
                          argv=["claude", "--model=fable", "--effort=max"],
                          model="opus", effort="high")
        entry = self._record(leaf)["attempts"][0]
        self.assertEqual((entry["model"], entry["effort"]), ("fable", "max"))

    def test_the_key_still_wins_when_argv_is_silent(self) -> None:
        # The interactive leaves are in this shape — keys only, no flags in argv.
        leaf = LeafConfig(mode="command", family="claude", argv=["claude", "--agent", "act"],
                          model="sonnet", effort="medium")
        entry = self._record(leaf)["attempts"][0]
        self.assertEqual((entry["model"], entry["effort"]), ("sonnet", "medium"))

    def test_codex_short_model_flag_is_not_matched_inside_another_flag(self) -> None:
        # `-m` as a substring test would fire on `--model`; the probe must be exact.
        leaf = LeafConfig(mode="command", family="codex",
                          argv=["codex", "exec", "--model-info", "x"], model="from-key")
        self.assertEqual(self._record(leaf)["attempts"][0]["model"], "from-key")

    def test_unpinned_tier_records_empty_not_a_guess(self) -> None:
        leaf = LeafConfig(mode="command", family="claude", argv=["claude", "-p"])
        entry = self._record(leaf)["attempts"][0]
        self.assertEqual((entry["model"], entry["effort"]), ("", ""))

    def test_the_ladder_is_distinguishable_end_to_end(self) -> None:
        # The point of the fix: three attempts on the real config must be tellable apart.
        d = self.tmp / "issue_1"
        d.mkdir(exist_ok=True)
        (d / "brief.md").write_text("- **Difficulty:** high\n", encoding="utf-8")
        seen = []
        for n in (1, 2):
            b = leaves.select_builder(d, self.cfg, n)
            leaves._record_loop_attempt(d, n, b, self.cfg)
        tel = json.loads((d / "loop-telemetry.json").read_text(encoding="utf-8"))
        seen = [(a["family"], a["model"], a["effort"]) for a in tel["attempts"]]
        self.assertEqual(seen, [("claude", "opus", "xhigh"), ("claude", "opus", "max")])
        self.assertEqual(len(set(seen)), 2)  # family alone would have collapsed these

    def test_family_and_builder_keys_are_unchanged(self) -> None:
        # _resolved_builder_family (#200 vendor-complement) reads `family`; the added keys
        # must not disturb the shape it depends on.
        leaf = LeafConfig(mode="command", family="codex", argv=["codex", "exec"])
        entry = self._record(leaf)["attempts"][0]
        self.assertEqual((entry["n"], entry["builder"], entry["family"]), (1, "codex", "codex"))


if __name__ == "__main__":
    unittest.main()
