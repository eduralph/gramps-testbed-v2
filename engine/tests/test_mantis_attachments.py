"""Unit tests for the Mantis scraper's image-attachment download (issue #319).

Exercises collect_attachments / _is_image / _safe_attachment_name against a fake `page`
whose `.evaluate` returns canned listing + fetch results, so no browser (and no Playwright)
is needed. mantis_notes imports Playwright only inside main(), so the module imports here.
"""

from __future__ import annotations

import base64
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import mantis_notes  # noqa: E402

PNG_B64 = base64.b64encode(b"\x89PNG\r\n\x1a\nfake-image-bytes").decode()


class FakePage:
    """`.evaluate(js)` (the listing) returns `listing`; `.evaluate(js, url)` (a fetch)
    returns `fetches[url]`. Mirrors how collect_attachments calls page.evaluate."""

    def __init__(self, listing, fetches=None, raise_on_list=False):
        self._listing = listing
        self._fetches = fetches or {}
        self._raise_on_list = raise_on_list
        self.fetched: list = []

    def evaluate(self, js, arg=None):
        if arg is None:
            if self._raise_on_list:
                raise RuntimeError("boom")
            return self._listing
        self.fetched.append(arg)
        return self._fetches.get(arg)


def _img(size=17, ct="image/png", b64=PNG_B64):
    return {"ok": True, "status": 200, "content_type": ct, "size": size, "b64": b64}


class CollectAttachments(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_saves_image_and_links_bundle_relative_path(self) -> None:
        url = "https://gramps-project.org/bugs/file_download.php?file_id=42&type=bug"
        page = FakePage([{"file_id": "42", "filename": "shot.png", "url": url}], {url: _img()})
        recs = mantis_notes.collect_attachments(page, "9457", self.tmp)
        self.assertEqual([r["status"] for r in recs], ["saved"])
        self.assertEqual(recs[0]["local_path"], "attachments/shot.png")
        saved = self.tmp / "issue_9457_attachments" / "shot.png"
        self.assertTrue(saved.is_file())
        self.assertEqual(saved.read_bytes(), base64.b64decode(PNG_B64))

    def test_non_image_extension_is_skipped_without_downloading(self) -> None:
        url = "https://x/file_download.php?file_id=7"
        page = FakePage([{"file_id": "7", "filename": "report.pdf", "url": url}], {})
        recs = mantis_notes.collect_attachments(page, "1", self.tmp)
        self.assertEqual(recs[0]["status"], "skipped-non-image")
        self.assertEqual(page.fetched, [])  # never fetched the non-image
        self.assertFalse((self.tmp / "issue_1_attachments").exists())

    def test_access_denied_html_degrades_to_skip(self) -> None:
        # A .png link that actually returns 200 text/html (a login / permission page).
        url = "https://x/file_download.php?file_id=9"
        page = FakePage(
            [{"file_id": "9", "filename": "priv.png", "url": url}],
            {url: _img(ct="text/html", b64=base64.b64encode(b"<html>Access Denied").decode())},
        )
        recs = mantis_notes.collect_attachments(page, "1", self.tmp)
        self.assertEqual(recs[0]["status"], "skipped-non-image")
        self.assertFalse((self.tmp / "issue_1_attachments").exists())

    def test_download_failure_is_recorded(self) -> None:
        url = "https://x/file_download.php?file_id=5"
        page = FakePage([{"file_id": "5", "filename": "s.png", "url": url}], {url: {"ok": False, "status": 403}})
        recs = mantis_notes.collect_attachments(page, "1", self.tmp)
        self.assertEqual(recs[0]["status"], "download-failed:403")

    def test_filename_collision_gets_a_unique_name(self) -> None:
        u1 = "https://x/file_download.php?file_id=1"
        u2 = "https://x/file_download.php?file_id=2"
        page = FakePage(
            [{"file_id": "1", "filename": "a.png", "url": u1},
             {"file_id": "2", "filename": "a.png", "url": u2}],
            {u1: _img(), u2: _img()},
        )
        recs = mantis_notes.collect_attachments(page, "1", self.tmp)
        self.assertEqual(sorted(r["local_path"] for r in recs),
                         ["attachments/2_a.png", "attachments/a.png"])
        d = self.tmp / "issue_1_attachments"
        self.assertEqual(sorted(p.name for p in d.iterdir()), ["2_a.png", "a.png"])

    def test_disabled_returns_empty_and_does_nothing(self) -> None:
        page = FakePage([{"file_id": "1", "filename": "a.png", "url": "u"}])
        self.assertEqual(mantis_notes.collect_attachments(page, "1", self.tmp, enabled=False), [])
        self.assertFalse((self.tmp / "issue_1_attachments").exists())

    def test_listing_failure_is_best_effort(self) -> None:
        recs = mantis_notes.collect_attachments(FakePage([], raise_on_list=True), "1", self.tmp)
        self.assertTrue(recs and recs[0]["status"].startswith("list-failed:"))


class IsImage(unittest.TestCase):
    def test_content_type_wins(self) -> None:
        self.assertTrue(mantis_notes._is_image("noext", "image/png"))
        self.assertTrue(mantis_notes._is_image("x", "image/jpeg; charset=binary"))
        self.assertFalse(mantis_notes._is_image("x", "text/html"))

    def test_extension_fallback(self) -> None:
        self.assertTrue(mantis_notes._is_image("a.PNG", ""))
        self.assertFalse(mantis_notes._is_image("a.pdf", ""))


class SafeName(unittest.TestCase):
    def test_strips_path_traversal_and_sanitizes(self) -> None:
        taken: set = set()
        self.assertEqual(mantis_notes._safe_attachment_name("../../etc/passwd", "9", taken), "passwd")
        self.assertEqual(mantis_notes._safe_attachment_name("weird name!.png", "3", taken), "weird_name_.png")

    def test_empty_falls_back_to_file_id(self) -> None:
        self.assertEqual(mantis_notes._safe_attachment_name("", "42", set()), "file_42")


if __name__ == "__main__":
    unittest.main()
