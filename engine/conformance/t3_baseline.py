#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Gramps Testbed v2 — conformance engine
#
# Copyright (C) 2026  Eduard Ralph
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <https://www.gnu.org/licenses/>.
#
"""T3 baseline diff — turn a whole-suite runner's red into "new or known?".

The three T3 whole-suite gates (``run-unit`` / ``run-addon-unit`` /
``run-interface``) are run on the *unmodified* target tree, which carries
pre-existing failures no per-fix patch touches. Without a record, the reviewer +
human re-diagnose the identical reds every cycle (a §6 "baseline vs regression?"
item per cycle — testbed issue #7). This wrapper runs the underlying runner, then
**diffs the result against a checked-in baseline manifest**: a run that matches
the recorded baseline exits 0 ("known reds"), and only a **delta** — a new failing
test, or an unexplained non-zero exit — exits 1, so only a genuinely new failure
raises §6. A baseline red that *cleared* is reported (the manifest is stale →
shrink it / re-gate that suite).

Two kinds of baseline entry (the documented reds need both):

  * ``known_failures`` — per-test ``classname::name`` ids parsed from the runner's
    JUnit XML (``test-results/*.xml``). Populate with ``--update`` from a real run.
  * ``run_level_signatures`` — a ``regex`` over the combined runner output for a
    red that produces no useful per-test XML (e.g. a core-dump before discovery,
    a pip-install failure). Each carries a ``cause`` + ``tracking`` note.

Usage::

    t3_baseline.py <runner-script> [args…]      # run + diff against the manifest
    t3_baseline.py <runner-script> --update     # run + record observed reds as the baseline

Manifest path: ``engine/baselines/<runner-stem>.json`` (override with
``$PDCA_T3_BASELINE``). Exit 0 = matches baseline (or green); 1 = a delta.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree


def _root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pdca.toml").is_file():
            return parent
    return here.parents[2]


ROOT = _root()
RESULTS_DIR = ROOT / "test-results"
BASELINE_DIR = ROOT / "engine" / "baselines"


# ---------------------------------------------------------------------------
# Pure helpers (unit-tested without Docker)
# ---------------------------------------------------------------------------
def parse_junit(results_dir: Path) -> dict[str, str]:
    """``{classname::name: 'failure'|'error'}`` for every non-passing testcase in
    the JUnit XML under ``results_dir`` (best-effort; a malformed file is skipped)."""
    failing: dict[str, str] = {}
    if not results_dir.is_dir():
        return failing
    for xml in sorted(results_dir.glob("*.xml")):
        try:
            tree = ElementTree.parse(xml)
        except ElementTree.ParseError:
            continue
        for case in tree.iter("testcase"):
            kind = next(
                (k for k in ("failure", "error") if case.find(k) is not None), None
            )
            if kind is None:
                continue
            cls = case.get("classname", "").strip()
            name = case.get("name", "").strip()
            failing[f"{cls}::{name}" if cls else name] = kind
    return failing


def _signature_matched(output: str, manifest: dict) -> dict | None:
    """The first run-level signature whose regex matches the combined output."""
    for sig in manifest.get("run_level_signatures", []):
        pattern = sig.get("regex") or re.escape(sig.get("match", ""))
        if pattern and re.search(pattern, output):
            return sig
    return None


def classify(observed: dict[str, str], rc: int, output: str, manifest: dict) -> dict:
    """Decide whether a run matches the recorded baseline or is a delta.

    Returns ``{verdict, exit_code, summary, new, cleared, signature}``. ``verdict``
    is ``"green"`` / ``"baseline"`` / ``"delta"``. Conservative: any new per-test
    failure, or a non-zero exit explained by neither a known signature nor
    all-failures-known, is a delta (exit 1) — the advisory signal the human reads.
    """
    known = {e["id"] for e in manifest.get("known_failures", [])}
    new = sorted(t for t in observed if t not in known)
    cleared = sorted(t for t in known if t not in observed)
    sig = _signature_matched(output, manifest)

    if new:
        summary = (f"DELTA: {len(new)} new failure(s) not in baseline: "
                   f"{', '.join(new[:5])}{' …' if len(new) > 5 else ''}")
        verdict, code = "delta", 1
    elif rc == 0:
        verdict, code = "green", 0
        summary = "green (no failures)"
        if cleared or known:
            summary += f"; baseline now clear ({len(known)} recorded red(s) gone)"
    elif observed or sig:
        # Non-zero, but every observed failure is known and/or a known run-level
        # signature explains the red → matches the recorded baseline.
        bits = []
        if observed:
            bits.append(f"{len(observed)} known test red(s)")
        if sig:
            bits.append(f"signature {sig.get('match') or sig.get('regex')!r}")
        verdict, code = "baseline", 0
        summary = "matches recorded baseline: " + "; ".join(bits)
        if cleared:
            summary += f"; {len(cleared)} recorded red(s) cleared"
    else:
        # Non-zero exit, no parsed failures, no matching signature → unexplained new red.
        verdict, code = "delta", 1
        summary = (f"DELTA: runner exited {rc} with no parsed failures and no "
                   f"matching baseline signature (a new failure mode)")
    return {"verdict": verdict, "exit_code": code, "summary": summary,
            "new": new, "cleared": cleared, "signature": sig}


def manifest_path(runner: str) -> Path:
    env = os.environ.get("PDCA_T3_BASELINE")
    if env:
        return Path(env)
    return BASELINE_DIR / f"{Path(runner).stem}.json"


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        return {"runner": "", "known_failures": [], "run_level_signatures": []}
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Runner + CLI
# ---------------------------------------------------------------------------
def _run_runner(runner: str, args: list[str]) -> tuple[int, str]:
    """Run the underlying T3 runner, echoing and capturing its combined output."""
    proc = subprocess.run(
        [runner, *args], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    sys.stdout.write(proc.stdout)
    return proc.returncode, proc.stdout


def _update_manifest(path: Path, runner: str, observed: dict[str, str]) -> None:
    """Record the observed per-test reds as the baseline (keeps signatures/notes)."""
    m = load_manifest(path)
    m.setdefault("runner", Path(runner).name)
    m.setdefault("run_level_signatures", [])
    m["known_failures"] = [
        {"id": tid, "type": kind} for tid, kind in sorted(observed.items())
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    print(f"t3-baseline: recorded {len(observed)} known red(s) → {path}")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: t3_baseline.py <runner-script> [args…|--update]", file=sys.stderr)
        return 2
    update = "--update" in argv
    rest = [a for a in argv if a != "--update"]
    runner, runner_args = rest[0], rest[1:]
    if not Path(runner).is_file():
        print(f"t3_baseline.py: runner not found: {runner}", file=sys.stderr)
        return 2

    path = manifest_path(runner)
    rc, output = _run_runner(runner, runner_args)
    observed = parse_junit(RESULTS_DIR)

    if update:
        _update_manifest(path, runner, observed)
        return 0

    verdict = classify(observed, rc, output, load_manifest(path))
    for tid in verdict["cleared"]:
        print(f"t3-baseline: recorded red cleared (shrink the manifest?): {tid}")
    # The summary is the LAST line — the gate captures it as the evidence line.
    print(f"T3-baseline [{verdict['verdict']}]: {verdict['summary']}")
    return verdict["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
