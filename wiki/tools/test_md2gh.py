#!/usr/bin/env python3
"""Tests for md2gh.py — the GitHub-native section exporter.

Offline, hermetic: builds a tiny vault in a temp dir, exports it, and pins
the conversion behaviour for every construct the real section uses.

Run:  cd tools && python3 test_md2gh.py
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import md2gh

SECTION = "06 - Addon development"

PAGE_A = """---
title: "Gramps 6.0 Wiki Manual - Addon Development"
categories: ["Addons"]
managed: true
---

[Index](wiki:Gramps 6.0 Wiki Manual - Addon Development) · [Next →](wiki:Gramps 6.0 Wiki Manual - Addon Development - Testing)

## Overview

See [[07-testing]] and [[07-testing|the testing page]].
Jump to [deep dive](07-testing.md#the-pin-contract) for anchors.
Outside: [the addon list](wiki:6.0_Addons) and
[core rules](../05%20-%20Core%20development/16-rules.md).

![[_media/diagram.svg|Fig. 1 — the diagram]]

```text
Literal examples must survive: [[Category:Addons]] and [x](wiki:Nope)
```

Inline literal: `[[07-testing]]` stays.

<!-- author note: kept -->
<!--wiki:{{stub}}-->
"""

PAGE_B = """---
title: Gramps 6.0 Wiki Manual - Addon Development - Testing
categories:
  - Addons
managed: true
---

[← Previous](wiki:Gramps 6.0 Wiki Manual - Addon Development) · [Index](wiki:Gramps 6.0 Wiki Manual - Addon Development)

## The pin contract

Body text.
"""

PAGE_UNMANAGED = """---
title: Section Sidebar
managed: false
---

## Sidebar

1. [[07-testing]]
"""

PAGE_OUTSIDE = """---
title: Gramps 6.1 Wiki Manual - Core Development - Rules
managed: true
---

## Rules
"""


def build_vault(root: Path) -> Path:
    section = root / "pages" / SECTION
    (section / "_media").mkdir(parents=True)
    (section / "01-overview.md").write_text(PAGE_A, encoding="utf-8")
    (section / "07-testing.md").write_text(PAGE_B, encoding="utf-8")
    (section / "00-sidebar.md").write_text(PAGE_UNMANAGED, encoding="utf-8")
    (section / "_media" / "diagram.svg").write_text("<svg/>", encoding="utf-8")
    (section / "_media" / "diagram.dot").write_text("digraph {}", encoding="utf-8")
    (section / "_media" / "WORK-NOTE.md").write_text("note", encoding="utf-8")
    other = root / "pages" / "05 - Core development"
    other.mkdir(parents=True)
    (other / "16-rules.md").write_text(PAGE_OUTSIDE, encoding="utf-8")
    return section


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        cls.section = build_vault(root)
        cls.out = root / "export"
        md2gh.export(cls.section, cls.out, sha="cafe123")
        cls.a = (cls.out / "01-overview.md").read_text(encoding="utf-8")
        cls.b = (cls.out / "07-testing.md").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    # ---- link conversions -------------------------------------------------

    def test_inbatch_wiki_link_becomes_relative(self):
        self.assertIn("[← Previous](01-overview.md)", self.b)
        self.assertIn("[Next →](07-testing.md)", self.a)

    def test_obsidian_links_become_relative(self):
        self.assertIn("[Gramps 6.0 Wiki Manual - Addon Development - Testing](07-testing.md)", self.a)
        self.assertIn("[the testing page](07-testing.md)", self.a)

    def test_relative_link_keeps_anchor(self):
        self.assertIn("[deep dive](07-testing.md#the-pin-contract)", self.a)

    def test_outofbatch_wiki_link_becomes_url(self):
        self.assertIn(
            "[the addon list](https://gramps-project.org/wiki/index.php/6.0_Addons)",
            self.a,
        )

    def test_crossfolder_md_link_becomes_url(self):
        self.assertIn(
            "[core rules](https://gramps-project.org/wiki/index.php/"
            "Gramps_6.1_Wiki_Manual_-_Core_Development_-_Rules)",
            self.a,
        )

    def test_no_wiki_scheme_or_obsidian_links_remain(self):
        for name, text in (("a", self.a), ("b", self.b)):
            body = text.split("```")  # crude: even indices are outside fences
            outside = "".join(body[::2])
            self.assertNotIn("](wiki:", outside, name)
            self.assertNotIn("![[", outside, name)

    # ---- code masking -----------------------------------------------------

    def test_fenced_block_literals_survive(self):
        self.assertIn("[[Category:Addons]] and [x](wiki:Nope)", self.a)

    def test_inline_code_literal_survives(self):
        self.assertIn("`[[07-testing]]`", self.a)

    # ---- embeds, comments, front-matter ----------------------------------

    def test_embed_becomes_markdown_image(self):
        self.assertIn("![Fig. 1 — the diagram](_media/diagram.svg)", self.a)

    def test_wiki_shim_stripped_author_comment_kept(self):
        self.assertNotIn("<!--wiki:", self.a)
        self.assertIn("<!-- author note: kept -->", self.a)

    def test_frontmatter_stripped_and_h1_added(self):
        self.assertFalse(self.a.lstrip("<!-- GENERATED").startswith("---"))
        self.assertNotIn("managed:", self.a)
        self.assertIn("\n# Gramps 6.0 Wiki Manual - Addon Development\n", self.a)

    def test_banner_present_with_sha_and_source(self):
        self.assertIn("GENERATED FILE - DO NOT EDIT HERE", self.a)
        self.assertIn(f"{SECTION}/01-overview.md @ cafe123", self.a)

    # ---- tree behaviour ---------------------------------------------------

    def test_unmanaged_page_not_exported(self):
        self.assertFalse((self.out / "00-sidebar.md").exists())

    def test_media_copied_without_md_notes(self):
        self.assertTrue((self.out / "_media" / "diagram.svg").exists())
        self.assertTrue((self.out / "_media" / "diagram.dot").exists())
        self.assertFalse((self.out / "_media" / "WORK-NOTE.md").exists())

    def test_index_readme_generated(self):
        idx = (self.out / "README.md").read_text(encoding="utf-8")
        self.assertIn("[01-overview.md](01-overview.md)", idx)
        self.assertIn("- [Testing](07-testing.md)", idx)
        self.assertIn("GENERATED FILE", idx)

    def test_determinism(self):
        first = {p.name: p.read_bytes() for p in self.out.rglob("*") if p.is_file()}
        md2gh.export(self.section, self.out, sha="cafe123")
        second = {p.name: p.read_bytes() for p in self.out.rglob("*") if p.is_file()}
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main(verbosity=2)
