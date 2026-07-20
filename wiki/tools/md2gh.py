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
- prepends an H1 built from the front-matter ``title`` (the vault's implicit
  H1) and a GENERATED-file provenance banner naming the source file and
  commit, mirroring publish.py's ``Synced from repo@<sha>`` convention.
- copies the section's ``_media/`` (excluding ``*.md`` work-notes) and emits
  a thin ``README.md`` index for the folder.

Fenced code blocks and inline code spans are stashed around every rewrite
(mdcommon.stash_code), so documentation examples like ``[[Category:...]]``
inside a fence pass through untouched.

The drift loop (documented in wiki/README.md): the export is deterministic
regeneration -- run it into the target checkout, inspect ``git diff`` there
BEFORE committing; any upstream edit to a generated file shows up as a diff
against the fresh export and must be reconciled back into the vault first.

Usage:
    python3 md2gh.py "pages/06 - Addon development" --out ../addons-source/docs/addon-development
    python3 md2gh.py "pages/06 - Addon development" --out /tmp/x --sha abc1234   # pin banner sha
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
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


def wiki_links_to_github(body: str, batch: dict[str, str]) -> str:
    """Map every ``[label](wiki:Target[#anchor])`` to its GitHub form.

    ``batch`` maps each *normalised* in-batch title form to the exported
    filename. In-batch targets become relative links (anchor preserved);
    everything else becomes a canonical wiki URL.
    """

    def repl(m: re.Match) -> str:
        label = m.group(1)
        target = m.group(2)
        bare, sep, anchor = target.partition("#")
        bare = bare.strip()
        fname = batch.get(bare)
        if fname is not None:
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
    banner: str,
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

    out = f"{banner}\n\n# {title}\n\n{body.strip()}\n"
    # Collapse any 3+ blank-line runs the shim removal may have left.
    return re.sub(r"\n{4,}", "\n\n\n", out)


def make_banner(rel_source: str, sha: str) -> str:
    return (
        "<!-- GENERATED FILE - DO NOT EDIT HERE.\n"
        f"  Source: gramps-testbed-v2:wiki/pages/{rel_source} @ {sha}\n"
        "  Edit the source page and re-export with wiki/tools/md2gh.py;\n"
        "  direct edits here are overwritten by the next export. -->"
    )


def resolve_sha(section_dir: Path, explicit: str | None) -> str:
    """Banner sha: --sha flag, then GIT_SHA env, then the section's repo HEAD
    (same provenance chain as publish.py's edit summaries)."""
    if explicit:
        return explicit
    env = os.environ.get("GIT_SHA")
    if env:
        return env
    try:
        proc = subprocess.run(
            ["git", "-C", str(section_dir), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except OSError:
        pass
    return "unknown"


def collect_pages(section_dir: Path) -> list[tuple[Path, dict]]:
    """The managed pages of the section, sorted by filename, with metadata."""
    pages: list[tuple[Path, dict]] = []
    for p in sorted(section_dir.glob("*.md")):
        meta, _ = split_frontmatter(p.read_text(encoding="utf-8"))
        if meta.get("managed") is True and meta.get("title"):
            pages.append((p, meta))
    return pages


def make_index(pages: list[tuple[Path, dict]], banner: str) -> str:
    """The folder README.md: a generated index over the exported pages."""
    lines = [
        banner,
        "",
        "# Gramps Addon Development manual",
        "",
        "The addon authors' manual for Gramps, rendered for GitHub. Start at",
        f"[{pages[0][0].name}]({pages[0][0].name}) — the overview and section map.",
        "",
        "The same content is published to the Gramps wiki; this folder is a",
        "**generated** rendering (see the banner in each file) — to change a page,",
        "edit its source and re-export rather than editing here.",
        "",
        "## Pages",
        "",
    ]
    for p, meta in pages:
        title = str(meta["title"])
        short = title.split(" - ")[-1] if " - " in title else title
        lines.append(f"- [{short}]({p.name})")
    lines += [""]
    return "\n".join(lines)


def export(
    section_dir: Path,
    out_dir: Path,
    *,
    vault_root: Path | None = None,
    sha: str | None = None,
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

    resolved_sha = resolve_sha(section_dir, sha)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for p, _meta in pages:
        rel_source = f"{section_dir.name}/{p.name}"
        banner = make_banner(rel_source, resolved_sha)
        converted = convert_page(
            p.read_text(encoding="utf-8"),
            str(p),
            title_map=title_map,
            batch=batch,
            banner=banner,
        )
        target = out_dir / p.name
        target.write_text(converted, encoding="utf-8")
        written.append(target)

    index = make_index(pages, make_banner(f"{section_dir.name}/", resolved_sha))
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
    ap.add_argument("--sha", help="commit sha for the provenance banner (default: GIT_SHA env, then git HEAD)")
    args = ap.parse_args(argv)

    section_dir = Path(args.section)
    if not section_dir.is_dir():
        ap.error(f"not a directory: {section_dir}")
    vault_root = Path(args.vault_root) if args.vault_root else None
    written = export(section_dir, Path(args.out), vault_root=vault_root, sha=args.sha)
    print(f"md2gh: wrote {len(written)} files to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
