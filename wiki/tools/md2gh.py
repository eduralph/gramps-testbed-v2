#!/usr/bin/env python3
"""Export a managed section tree to GitHub-native Markdown.

The vault stays the single source of truth; this tool renders a *second
publish target* alongside the MediaWiki: a directory of plain, GitHub-
renderable Markdown files (for example ``docs/addon-development/`` in the
gramps-project/addons-source repository).

What it does per page (``managed: true`` pages only):

- resolves every link flavour the vault allows -- Obsidian ``[[Page]]``,
  relative ``[label](XX-name.md#anchor)``, and authored ``[label](wiki:Page)``
  -- into the uniform ``wiki:`` form via the shared :mod:`mdcommon`
  preprocessors, then maps each ``wiki:`` target:

  * **in-batch** (the target is one of the exported pages): a relative
    ``NN-name.md`` link, so the exported tree is self-contained and
    GitHub-navigable. Anchors survive verbatim (they were GitHub-style
    anchors in the source).
  * **out-of-batch**: a full canonical wiki URL
    (``https://gramps-project.org/wiki/index.php/Page_Name``). Never a
    sandbox-prefixed title -- exported links assume canonical publication.

- converts Obsidian embeds ``![[_media/x.svg|cap]]`` to ``![cap](_media/x.svg)``.
- strips the YAML front-matter (wiki-publishing metadata, inert on GitHub)
  and the ``<!--wiki:{{...}}-->`` shim comments; other HTML comments are
  kept (invisible on GitHub, harmless).
- prepends an H1 built from the front-matter ``title``, shortened to its
  last " - " segment ("Gramps 6.0 Wiki Manual - Addon Development -
  Testing" becomes "Testing") so the exported page carries no wiki-manual
  naming. Auto-generated link labels are shortened the same way.
- copies the section's ``_media/`` (excluding ``*.md`` work-notes) and emits
  a thin ``README.md`` index for the folder.

The exported files carry NO provenance banner and no generated-file
notice -- they read as ordinary repository docs. Fenced code blocks and
inline code spans are stashed around every rewrite (mdcommon.stash_code),
so documentation examples like ``[[Category:...]]`` inside a fence pass
through untouched.

The drift loop (documented in wiki/README.md): the export is deterministic
regeneration -- run it into the target checkout, inspect ``git diff`` there
BEFORE committing; an edit made in the target since the last export shows
up as a diff against the fresh export and is reconciled back into the
vault first.

Usage:
    python3 md2gh.py "pages/06 - Addon development" --out ../addons-source/docs/addon-development
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

import yaml

import mdcommon

WIKI_BASE = "https://gramps-project.org/wiki/index.php/"

# Front-matter splitter (mirrors the md2wiki / md2pdf local copies).
FM_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)

# A <!--wiki:...--> shim comment (template pass-through for the wiki target).
# Meaningless in the GitHub rendering -- stripped, including a trailing
# newline so no blank gap is left behind.
WIKI_SHIM_RE = re.compile(r"[ \t]*<!--\s*wiki:.*?-->\n?", re.DOTALL)


def split_frontmatter(text: str) -> tuple[dict, str]:
    m = FM_RE.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, m.group(2)


def _normalise_title_forms(title: str) -> set[str]:
    """Both space- and underscore-forms of a title (MediaWiki treats them as
    the same page name; authors and the title map use either)."""
    return {title, title.replace(" ", "_"), title.replace("_", " ")}


def short_title(title: str) -> str:
    """The last " - " segment of a wiki title -- the page's own name,
    without the manual-prefix chain."""
    return title.split(" - ")[-1] if " - " in title else title


def wiki_links_to_github(body: str, batch: dict[str, str]) -> str:
    """Map every ``[label](wiki:Target[#anchor])`` to its GitHub form.

    ``batch`` maps each *normalised* in-batch title form to the exported
    filename. In-batch targets become relative links (anchor preserved);
    everything else becomes a canonical wiki URL.

    A label that merely repeats the target's title (the auto-label the
    ``[[stem]]`` conversion produces) is shortened to the title's last
    segment, so exported text reads "Rules", not the full wiki-manual
    page name.
    """

    def repl(m: re.Match) -> str:
        label = m.group(1)
        target = m.group(2)
        bare, sep, anchor = target.partition("#")
        bare = bare.strip()
        fname = batch.get(bare)
        if fname is not None:
            if label in _normalise_title_forms(bare):
                label = short_title(label.replace("_", " "))
            return f"[{label}]({fname}{sep}{anchor})"
        url = WIKI_BASE + quote(bare.replace(" ", "_"), safe="/:_'()-.,")
        return f"[{label}]({url}{sep}{anchor})"

    return mdcommon.WIKI_LINK_RE.sub(repl, body)


def convert_page(
    text: str,
    source: str,
    *,
    title_map: dict[str, list[tuple[str, str]]],
    batch: dict[str, str],
) -> str:
    """Convert one vault page to GitHub-native Markdown."""
    meta, body = split_frontmatter(text)
    title = meta.get("title")
    if not title:
        raise ValueError(f"{source}: front-matter missing required 'title'")

    body, code_tokens = mdcommon.stash_code(body)
    body, comment_tokens = mdcommon.stash_html_comments(body)
    body = mdcommon.convert_obsidian_embeds(body)
    if mdcommon.OBSIDIAN_INTERNAL_LINK_RE.search(body):
        body = mdcommon.convert_obsidian_internal_links(
            body, title_map, source_path=source
        )
    if mdcommon.RELATIVE_MD_LINK_RE.search(body):
        body = mdcommon.convert_relative_md_links(body, title_map, source_path=source)
    body = wiki_links_to_github(body, batch)
    body = mdcommon.unstash_html_comments(body, comment_tokens)
    body = WIKI_SHIM_RE.sub("", body)
    body = mdcommon.unstash_code(body, code_tokens)

    out = f"# {short_title(str(title))}\n\n{body.strip()}\n"
    # Collapse any 3+ blank-line runs the shim removal may have left.
    return re.sub(r"\n{4,}", "\n\n\n", out)


def collect_pages(section_dir: Path) -> list[tuple[Path, dict]]:
    """The managed pages of the section, sorted by filename, with metadata."""
    pages: list[tuple[Path, dict]] = []
    for p in sorted(section_dir.glob("*.md")):
        meta, _ = split_frontmatter(p.read_text(encoding="utf-8"))
        if meta.get("managed") is True and meta.get("title"):
            pages.append((p, meta))
    return pages


def make_index(pages: list[tuple[Path, dict]]) -> str:
    """The folder README.md: an index over the exported pages."""
    lines = [
        "# Gramps Addon Development manual",
        "",
        "The addon authors' manual for Gramps. Start at",
        f"[{pages[0][0].name}]({pages[0][0].name}) — the overview and section map.",
        "",
        "## Pages",
        "",
    ]
    for p, meta in pages:
        lines.append(f"- [{short_title(str(meta['title']))}]({p.name})")
    lines += [""]
    return "\n".join(lines)


def export(
    section_dir: Path,
    out_dir: Path,
    *,
    vault_root: Path | None = None,
) -> list[Path]:
    """Export ``section_dir`` to ``out_dir``; returns the written paths."""
    if vault_root is None:
        vault_root = section_dir.parent
    title_map = mdcommon.build_title_map(vault_root)
    pages = collect_pages(section_dir)
    if not pages:
        raise SystemExit(f"md2gh: no managed pages under {section_dir}")

    batch: dict[str, str] = {}
    for p, meta in pages:
        for form in _normalise_title_forms(str(meta["title"])):
            batch[form] = p.name

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for p, _meta in pages:
        converted = convert_page(
            p.read_text(encoding="utf-8"),
            str(p),
            title_map=title_map,
            batch=batch,
        )
        target = out_dir / p.name
        target.write_text(converted, encoding="utf-8")
        written.append(target)

    index = make_index(pages)
    target = out_dir / "README.md"
    target.write_text(index, encoding="utf-8")
    written.append(target)

    media_src = section_dir / "_media"
    if media_src.is_dir():
        media_out = out_dir / "_media"
        media_out.mkdir(exist_ok=True)
        for f in sorted(media_src.iterdir()):
            if f.is_file() and f.suffix.lower() != ".md":
                shutil.copyfile(f, media_out / f.name)
                written.append(media_out / f.name)

    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("section", help="section directory (e.g. 'pages/06 - Addon development')")
    ap.add_argument("--out", required=True, help="output directory (created if missing)")
    ap.add_argument(
        "--vault-root",
        help="root for link resolution (default: the section's parent directory)",
    )
    args = ap.parse_args(argv)

    section_dir = Path(args.section)
    if not section_dir.is_dir():
        ap.error(f"not a directory: {section_dir}")
    vault_root = Path(args.vault_root) if args.vault_root else None
    written = export(section_dir, Path(args.out), vault_root=vault_root)
    print(f"md2gh: wrote {len(written)} files to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
