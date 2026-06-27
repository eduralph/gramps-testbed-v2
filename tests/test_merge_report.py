"""Offline slice for `pdca merged` — the published-PR merge monitor (merge_report).

Proves: collect() finds only bundles with a recorded PR and derives the Mantis id (integer
bundle, not id_pending), recursing into archived completed/; poll() maps gh fields to merge
state with a fail-OPEN "unknown" for unreadable PRs; the worklist shows a merged + ticketed
fix until it is explicitly acked, and `--ack` writes a durable tracker-update.json that drops
it off and survives across runs (not the fragile "seen once"); ack refuses a no-ticket bundle;
and the drafted comment carries the tracker update without an upstream cross-link. `gh` is
injected — no network.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from pdca_harness import merge_report
from pdca_harness.config import Config, LeafConfig

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


def _cfg(root: Path) -> Config:
    return Config(
        root=root,
        bundle_root=root / "results",
        process_dir=root / "process",
        templates_dir=TEMPLATES,
        default_branch="main",
        tracker_system="mantis",
        tracker_url="https://gramps-project.org/bugs",
        issue_id_example="1",
        builder=LeafConfig(mode="stub"),
        reviewer=LeafConfig(mode="stub"),
    )


def _publish(cfg: Config, bundle: str, **rec) -> Path:
    d = cfg.bundle_root / bundle
    d.mkdir(parents=True, exist_ok=True)
    (d / "publish.json").write_text(json.dumps(rec), encoding="utf-8")
    return d


def _gh(states: dict[str, dict | None]):
    """A fake gh_view: pr_url → the json dict gh would return (or None = unreadable)."""
    return lambda pr_url: states.get(pr_url)


def _merged_gh(pr_url: str):
    return _gh({pr_url: {"state": "MERGED", "mergedAt": "2026-06-26T00:00:00Z",
                         "mergeCommit": {"oid": "deadbeefcafe0000"}, "title": "fix"}})


class Collect(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = _cfg(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_only_bundles_with_a_pr_url(self) -> None:
        _publish(self.cfg, "issue_13163", pr_url="https://x/pull/2411",
                 repo="gramps-project/gramps", base="maintenance/gramps61")
        _publish(self.cfg, "issue_999")  # publish.json without a pr_url → skipped
        (self.cfg.bundle_root / "issue_nopublish").mkdir(parents=True)
        got = {p.bundle for p in merge_report.collect(self.cfg)}
        self.assertEqual(got, {"issue_13163"})

    def test_mantis_id_derivation(self) -> None:
        _publish(self.cfg, "issue_13163", pr_url="u1")            # integer → tracked
        _publish(self.cfg, "issue_glade-setattr", pr_url="u2")    # slug → none
        _publish(self.cfg, "issue_945", pr_url="u3", id_pending=True)  # pending → none
        ids = {p.bundle: p.mantis_id for p in merge_report.collect(self.cfg)}
        self.assertEqual(ids, {"issue_13163": "13163",
                               "issue_glade-setattr": None, "issue_945": None})

    def test_finds_archived_completed_bundles(self) -> None:
        _publish(self.cfg, "completed/issue_13716", pr_url="u",
                 repo="gramps-project/gramps", base="maintenance/gramps61")
        self.assertEqual([p.bundle for p in merge_report.collect(self.cfg)], ["issue_13716"])


class Poll(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = _cfg(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_poll_maps_merge_state_and_unknown(self) -> None:
        _publish(self.cfg, "issue_1", pr_url="open")
        _publish(self.cfg, "issue_2", pr_url="done")
        _publish(self.cfg, "issue_3", pr_url="err")
        items = merge_report.collect(self.cfg)
        st = merge_report.poll(items, gh_view=_gh({
            "open": {"state": "OPEN"},
            "done": {"state": "MERGED", "mergedAt": "2026-06-26T00:00:00Z",
                     "mergeCommit": {"oid": "abcdef1234567890"}, "title": "fix"},
            "err": None,
        }))
        self.assertFalse(st["issue_1"].merged)
        self.assertTrue(st["issue_1"].known)
        self.assertTrue(st["issue_2"].merged)
        self.assertEqual(st["issue_2"].merge_commit, "abcdef123456")  # 12-char trim
        self.assertFalse(st["issue_3"].known)


class Worklist(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = _cfg(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_merged_ticket_is_outstanding_until_acked(self) -> None:
        _publish(self.cfg, "issue_13163", pr_url="https://x/pull/2411",
                 repo="gramps-project/gramps", base="maintenance/gramps61")
        gh = _merged_gh("https://x/pull/2411")

        first: list[str] = []
        merge_report.report(self.cfg, gh_view=gh, out=first.append)
        self.assertTrue(any("1 need a Mantis update" in ln for ln in first))
        self.assertTrue(any("Mantis 13163" in ln for ln in first))

        # Re-running WITHOUT acking still shows it (not a fragile seen-once suppression).
        again: list[str] = []
        merge_report.report(self.cfg, gh_view=gh, out=again.append)
        self.assertTrue(any("Mantis 13163" in ln for ln in again))

        # Ack it → durable tracker-update.json, then it drops off and stays off.
        rc = merge_report.ack(self.cfg, "13163", by="Tester", date="2026-06-27",
                              out=lambda *_: None)
        self.assertEqual(rc, 0)
        rec = json.loads((self.cfg.bundle_root / "issue_13163"
                          / merge_report.ACK_FILE).read_text())
        self.assertEqual(rec["status"], "resolved")
        self.assertEqual(rec["fixed_in_version"], "6.1.x")  # derived from the base
        self.assertEqual(rec["by"], "Tester")

        after: list[str] = []
        merge_report.report(self.cfg, gh_view=gh, out=after.append)
        self.assertTrue(any("0 need a Mantis update (1 done)" in ln for ln in after))
        self.assertFalse(any(ln.startswith("● Mantis 13163") for ln in after))

    def test_ack_version_override(self) -> None:
        _publish(self.cfg, "issue_7", pr_url="p", repo="r", base="maintenance/gramps61")
        merge_report.ack(self.cfg, "7", by="T", date="2026-06-27", version="6.1.4",
                         out=lambda *_: None)
        rec = json.loads((self.cfg.bundle_root / "issue_7"
                          / merge_report.ACK_FILE).read_text())
        self.assertEqual(rec["fixed_in_version"], "6.1.4")

    def test_ack_refuses_no_ticket_bundle(self) -> None:
        _publish(self.cfg, "issue_glade-setattr", pr_url="p", repo="r", base="b")
        out: list[str] = []
        rc = merge_report.ack(self.cfg, "issue_glade-setattr", by="T",
                              date="2026-06-27", out=out.append)
        self.assertEqual(rc, 2)
        self.assertFalse((self.cfg.bundle_root / "issue_glade-setattr"
                          / merge_report.ACK_FILE).exists())

    def test_ack_unknown_id_errors(self) -> None:
        rc = merge_report.ack(self.cfg, "99999", by="T", date="2026-06-27",
                              out=lambda *_: None)
        self.assertEqual(rc, 2)

    def test_unreadable_pr_is_reported_not_merged(self) -> None:
        _publish(self.cfg, "issue_5", pr_url="p", repo="r", base="maintenance/gramps61")
        out: list[str] = []
        merge_report.report(self.cfg, gh_view=_gh({"p": None}), out=out.append)
        self.assertTrue(any("unreadable" in ln for ln in out))
        self.assertTrue(any("Could not read" in ln for ln in out))


class Draft(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.cfg = _cfg(self.tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_draft_has_update_fields_and_no_upstream_link(self) -> None:
        pub = merge_report.Published(
            bundle="issue_13163", dir=self.tmp, pr_url="https://x/pull/2411",
            repo="gramps-project/gramps", base="maintenance/gramps61", mantis_id="13163")
        st = merge_report.PRState(pr_url=pub.pr_url, known=True, merged=True,
                                  merged_at="2026-06-26T00:00:00Z",
                                  merge_commit="deadbeefcafe", title="fix")
        body = merge_report.draft_comment(self.cfg, pub, st)
        self.assertIn("Status → resolved", body)
        self.assertIn("Fixed in version → 6.1.x", body)
        self.assertIn("upstream PR 2411", body)        # plain-text, not a link
        self.assertNotIn("https://x/pull/2411", body)  # no upstream cross-link


if __name__ == "__main__":
    unittest.main()
