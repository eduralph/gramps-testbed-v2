"""On-demand merge monitor: which published PRs are merged but their Mantis ticket isn't
updated yet → draft the update, and let the human flag each one done.

``pdca merged`` walks every bundle that recorded a contribution PR (``publish.json``), asks
GitHub whether each PR is merged yet, and reports the merged ones whose tracker update is
still **outstanding** — each with a drafted tracker comment (the ``tracker-comment`` template)
the human pastes into Mantis, plus the status / "Fixed in version" edits to make. Detection is
deterministic; the Mantis edit stays manual — there is no tracker write API here, only the
read-only scraper (INTEGRATION §1), and writing a public tracker is the human's call.

"Taken care of" is an explicit, durable flag — **not** "seen once". ``pdca merged --ack <id>``
writes ``tracker-update.json`` into the bundle (an artifact recording who set the ticket
resolved, to which "Fixed in version", and when); an acked bundle drops off the worklist and
stays off across runs. ``--all`` also lists the already-acked ones. The merge query reuses the
same ``gh pr view`` primitive as the wait-for-merged gate ([[merged]] / issue #107) and is
fail-open here: a PR we cannot read is reported as "unreadable", never silently merged.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import Config

ACK_FILE = "tracker-update.json"  # per-bundle: the recorded Mantis update (the "done" flag)

# Base branch → the Mantis "Fixed in version" series. Best-effort: the human sets the exact
# patch level; this names the series the merge target ships in (INTEGRATION §2 branch map).
_VERSION_BY_BASE = {
    "maintenance/gramps61": "6.1.x",
    "maintenance/gramps60": "6.0.x",
    "master": "master (unreleased)",
}


@dataclass(frozen=True)
class Published:
    """A bundle that recorded a contribution PR (its ``publish.json``)."""

    bundle: str  # bundle dir name, e.g. "issue_13163"
    dir: Path
    pr_url: str
    repo: str
    base: str
    mantis_id: str | None  # the tracker id to update, or None (slug bundle / id_pending)


def collect(cfg: Config) -> list[Published]:
    """Every published bundle under ``bundle_root`` (recursively, incl. archived/completed).

    A bundle is "published" iff it has a ``publish.json`` recording a ``pr_url``. ``mantis_id``
    is the bundle's integer id when the dir is ``issue_<digits>`` and the publish was not
    ``id_pending`` — otherwise None (a slug bundle, or an accepted-without-a-tracker-id fix).
    """
    out: list[Published] = []
    root = cfg.bundle_root
    if not root.exists():
        return out
    for pj in sorted(root.rglob("publish.json")):
        try:
            rec = json.loads(pj.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        pr_url = rec.get("pr_url")
        if not pr_url:
            continue
        name = pj.parent.name
        bare = name.removeprefix("issue_")
        mantis_id = bare if bare.isdigit() and not rec.get("id_pending") else None
        out.append(Published(bundle=name, dir=pj.parent, pr_url=pr_url,
                             repo=rec.get("repo", ""), base=rec.get("base", ""),
                             mantis_id=mantis_id))
    return out


def fixed_in_version(base: str) -> str:
    """The Mantis "Fixed in version" series for a base branch (best-effort; INTEGRATION §2)."""
    return _VERSION_BY_BASE.get(base, base or "unknown")


def ack_record(pub: Published) -> dict | None:
    """The bundle's recorded Mantis update (``tracker-update.json``), or None if not acked."""
    f = pub.dir / ACK_FILE
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}  # present but unreadable still counts as acked (don't re-nag)


def is_acked(pub: Published) -> bool:
    return (pub.dir / ACK_FILE).exists()


def _gh_view(pr_url: str) -> dict | None:
    """``gh pr view`` merge fields for ``pr_url``, or None if it can't be read (fail-open)."""
    r = subprocess.run(
        ["gh", "pr", "view", pr_url, "--json", "state,mergedAt,mergeCommit,title"],
        capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout or "{}")
    except ValueError:
        return None


@dataclass(frozen=True)
class PRState:
    """The GitHub-side state of a published PR at poll time."""

    pr_url: str
    known: bool  # could we read it at all?
    merged: bool
    merged_at: str
    merge_commit: str
    title: str


def poll(items: list[Published], gh_view=_gh_view) -> dict[str, PRState]:
    """Query merge state for each published PR, keyed by bundle name. ``gh_view`` is injectable."""
    states: dict[str, PRState] = {}
    for it in items:
        data = gh_view(it.pr_url)
        if data is None:
            states[it.bundle] = PRState(it.pr_url, known=False, merged=False,
                                        merged_at="", merge_commit="", title="")
            continue
        commit = (data.get("mergeCommit") or {}).get("oid", "") or ""
        states[it.bundle] = PRState(
            pr_url=it.pr_url, known=True, merged=data.get("state") == "MERGED",
            merged_at=data.get("mergedAt") or "", merge_commit=commit[:12],
            title=data.get("title") or "")
    return states


def draft_comment(cfg: Config, pub: Published, st: PRState) -> str:
    """The drafted Mantis comment for a merged fix, from the ``tracker-comment`` template.

    Falls back to a minimal inline body if the template is missing, so the report never
    breaks on a stripped checkout.
    """
    pr_ref = _pr_ref(pub)
    commit = f" (merge {st.merge_commit})" if st.merge_commit else ""
    tpl = cfg.templates_dir / "tracker-comment.md.tpl"
    lines = [
        f"**Issue:** {pub.mantis_id}",
        "**Disposition:** Fixed",
        "",
        f"Fixed upstream; the contribution was merged into `{pub.base}`{commit}.",
        "",
        "**Evidence:**",
        f"- {pr_ref}, merged {st.merged_at or '(date on GitHub)'}.",
        "",
        "**Set on this ticket:**",
        "- Status → resolved",
        f"- Fixed in version → {fixed_in_version(pub.base)}",
    ]
    body = "\n".join(lines)
    if tpl.exists():
        return f"{body}\n\n(voice/format: {tpl})"
    return body


def _pr_ref(pub: Published) -> str:
    """Plain-text PR reference — never a cross-linking URL into the upstream repo (INTEGRATION
    §1 'no upstream-repo links'). The merge worklist is host-side only, so a bare 'PR N' is
    enough to find it."""
    num = pub.pr_url.rstrip("/").rsplit("/", 1)[-1]
    return f"upstream PR {num}" if num.isdigit() else f"PR {pub.pr_url}"


def resolve(items: list[Published], ident: str) -> Published | None:
    """The published bundle named by ``ident`` — a Mantis id, a bundle dir, or its bare id."""
    want = ident.removeprefix("issue_")
    for it in items:
        if it.mantis_id == want or it.bundle == ident or it.bundle == f"issue_{want}":
            return it
    return None


def ack(cfg: Config, ident: str, *, by: str, date: str, version: str = "",
        out=print) -> int:
    """Flag a merged ticket's Mantis update as done — write ``tracker-update.json`` (#bundle).

    Records the disposition, the "Fixed in version" (derived from the base unless overridden),
    and who/when, so the worklist stops surfacing it. Refuses an unknown id or a bundle with
    no Mantis number (nothing to update on the tracker)."""
    items = collect(cfg)
    pub = resolve(items, ident)
    if pub is None:
        out(f"merged: no published bundle for '{ident}'")
        return 2
    if not pub.mantis_id:
        out(f"merged: {pub.bundle} has no Mantis number — nothing to record on the tracker")
        return 2
    rec = {
        "mantis_id": pub.mantis_id,
        "pr_url": pub.pr_url,
        "status": "resolved",
        "fixed_in_version": version or fixed_in_version(pub.base),
        "by": by,
        "date": date,
    }
    (pub.dir / ACK_FILE).write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    out(f"recorded Mantis {pub.mantis_id} resolved (Fixed in {rec['fixed_in_version']}) "
        f"→ {pub.dir / ACK_FILE}")
    return 0


def report(cfg: Config, *, show_all: bool = False, gh_view=_gh_view, out=print) -> int:
    """Scan published PRs; report merged ones whose Mantis update is still outstanding.

    A merged + ticketed bundle stays on the worklist until it's acked (``--ack``); ``show_all``
    additionally lists the already-acked ones. Returns 0 always (a report, not a gate)."""
    items = collect(cfg)
    if not items:
        out("(no published PRs to monitor)")
        return 0
    states = poll(items, gh_view=gh_view)
    by_bundle = {it.bundle: it for it in items}

    merged = [b for b in by_bundle if states[b].merged]
    open_n = sum(1 for b in by_bundle if states[b].known and not states[b].merged)
    unknown = [b for b in by_bundle if not states[b].known]
    # Outstanding = merged, has a Mantis number, not yet acked. No-ticket merges are
    # informational; acked ones are done.
    outstanding = [b for b in merged if by_bundle[b].mantis_id and not is_acked(by_bundle[b])]
    acked = [b for b in merged if by_bundle[b].mantis_id and is_acked(by_bundle[b])]
    no_ticket = [b for b in merged if not by_bundle[b].mantis_id]

    out(f"{len(items)} published · {len(merged)} merged · {open_n} open · "
        f"{len(unknown)} unreadable    →  {len(outstanding)} need a Mantis update"
        f" ({len(acked)} done)")

    for b in sorted(outstanding, key=lambda b: by_bundle[b].mantis_id or ""):
        pub, st = by_bundle[b], states[b]
        out("")
        out(f"● Mantis {pub.mantis_id}  ·  {_pr_ref(pub)}  ·  merged {st.merged_at} "
            f"·  base {pub.base}")
        out(f"  {pub.repo}  ·  bundle {pub.bundle}")
        out(f"  flag done:  pdca merged --ack {pub.mantis_id}")
        out("  ── drafted tracker comment " + "─" * 30)
        for line in draft_comment(cfg, pub, st).splitlines():
            out(f"  {line}")
        out("  " + "─" * 56)

    if no_ticket:
        out("")
        out("Merged, no Mantis ticket (informational — addons w/o ticket, slug, id_pending):")
        for b in sorted(no_ticket):
            pub = by_bundle[b]
            out(f"  · {pub.bundle}  {_pr_ref(pub)}  ({pub.repo})")

    if show_all and acked:
        out("")
        out("Already recorded as updated in Mantis (--ack):")
        for b in sorted(acked, key=lambda b: by_bundle[b].mantis_id or ""):
            pub, r = by_bundle[b], (ack_record(by_bundle[b]) or {})
            when = f" on {r['date']}" if r.get("date") else ""
            out(f"  · Mantis {pub.mantis_id}  Fixed in {r.get('fixed_in_version', '?')}{when}")

    if unknown:
        out("")
        out("Could not read (rerun when gh/network is back):")
        for b in sorted(unknown):
            out(f"  · {by_bundle[b].bundle}  {by_bundle[b].pr_url}")
    return 0
