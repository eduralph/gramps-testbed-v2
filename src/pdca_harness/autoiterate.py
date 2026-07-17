"""Auto-iterate: resolve implementation-only Check findings without stopping for a human.

Issue #264. A big Do lands with implementation defects the reviewer or the adversary
catches — a logic slip, a weak test, a failing gate. Today every one of those parks the
bundle at ``AWAITING_SIGNOFF`` and asks the human to press "iterate-do", which is exactly
the decision the driver could have made itself. The human's judgment is owed only to
findings that are *architecturally* relevant.

The split already exists in the codebase: ``gates._FIVE_FIVE_ONE`` tags each of the 11
check cells ``input | gate | judgment``. The ``gate`` cells (C2 reproduction, C4
verification, T1..T4) are mechanically checkable, so a rebuild can address them; the
``judgment`` cells (C5 causal adequacy, T5 judgment, V validation) and the ``input`` cells
(C1 spec, C3 change) are the human's. ``assemble.collect_needs_human`` tags every §6 item
IMPL or HUMAN from exactly that source.

So: when a bundle reaches ``AWAITING_SIGNOFF`` with at least one IMPL item, the driver
writes an ``iterate-do`` decision and re-drives Do. Anything else — an empty §6 (a clean
bundle awaiting a human accept), a HUMAN-only finding set, an exhausted budget — halts as
before.

INSTANCE RULE (2026-07-17, diverges from upstream #264): situational HUMAN items do NOT
veto the rebuild — when Check finds implementation defects beside judgment items, the
defects are auto-iterated and the judgment items return with the fresh Check for the human
to weigh against the repaired implementation. (Upstream also exempts the reviewer's
STANDING ``Validation — fitness-to-purpose`` row, hard-coded NEEDS-HUMAN on every cycle and
so signal-free, #293; under the instance rule that exemption is subsumed.)

Three properties hold by construction:

* **It only ever writes ``iterate-do``.** Never ``accept``, never ``discontinue``. The
  decision goes through the same C6-guarded ``flow._apply_decision`` a human sign-off uses,
  so §9 stays authored solely by ``signoff.record``.
* **It never clears a §6 box.** An ``iterate-do`` archives the whole SUMMARY, unticked, into
  ``iteration-v<N>/``; the rebuild produces a fresh §6.
* **It is bounded.** ``[driver].max_auto_iters`` automatic rounds per bundle, counted in
  ``auto-iterate.json`` (deliberately NOT in ``driver.DOWNSTREAM_OF_BRIEF``, so the archive
  step doesn't move it and the count accumulates across rebuilds). On exhaustion the bundle
  is left at ``AWAITING_SIGNOFF`` for the human — never dropped.

Opt-in: ``[driver].auto_iterate = false`` by default.
"""

from __future__ import annotations

import json
from pathlib import Path

from .assemble import HUMAN, IMPL, INFRA, NeedsHumanItem
from .leaves import SIGNOFF_DECISION

BUDGET_FILE = "auto-iterate.json"

# The only token this module is ever allowed to write.
DECISION = "iterate-do"


def eligible(items: list[NeedsHumanItem]) -> bool:
    """True iff a rebuild is the right next step: at least one IMPL finding.

    An **empty** §6 is deliberately not eligible — that is a clean bundle awaiting a human
    *accept*, and auto-iterate must never accept. A HUMAN-only set is not eligible either:
    there is no defect Do can fix, so the bundle halts for the human as before.

    INSTANCE RULE (2026-07-17, diverges from upstream #264/#293): a situational HUMAN item
    does NOT veto the rebuild. When Check finds implementation defects *beside* judgment
    items, the defects are still Do's to fix — halting first only makes the human press
    "iterate-do" for them anyway. So the driver rebuilds now; the HUMAN items are not
    consumed (nothing here ticks a §6 box) and return with the fresh Check, where the human
    reviews them against the repaired implementation. The bundle still halts as soon as no
    IMPL finding remains. Known cost, accepted: an IMPL-classified gate red actually caused
    by a missing external dependency spins for up to [driver].max_auto_iters rounds before
    handing over.

    ONE veto remains: an INFRA item — a review/advisory artifact that is empty because the
    leaf's infrastructure failed (#278). That is not a finding riding along; it means Check
    did not actually happen, and rebuilding blind would loop against the same broken leaf.

    (The STANDING `Validation — fitness-to-purpose` row was already exempt upstream — it is
    emitted NEEDS-HUMAN on every cycle by design, carries no signal, and never vetoed (#293).
    Under the instance rule it simply rides along like any other non-IMPL item.)
    """
    return (any(item.kind == IMPL for item in items)
            and not any(item.kind == INFRA for item in items))


def count(d: Path) -> int:
    """How many automatic iterations this bundle has already spent. Tolerant of a missing
    or garbled file, like ``loop-telemetry.json``."""
    try:
        return int(json.loads((d / BUDGET_FILE).read_text(encoding="utf-8"))["count"])
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def bump(d: Path) -> int:
    """Spend one automatic iteration; return the new count."""
    n = count(d) + 1
    (d / BUDGET_FILE).write_text(json.dumps({"count": n}) + "\n", encoding="utf-8")
    return n


def rationale(items: list[NeedsHumanItem], *, attempt: int) -> str:
    """The §9 "Iteration delta" line, which the driver folds into the brief's carry-forward
    so the next Do iteration isn't blind about why it was rejected.

    IMPL items ONLY. Non-IMPL items ride along in ``items`` (they do not veto the rebuild —
    the STANDING `Validation` row by upstream #293, situational HUMAN items by the instance
    rule above), but none of them is a defect a builder can act on — carrying one forward
    would hand the next Do a human-only judgment call as though it were a defect to fix
    (PR #294 review). HUMAN items are instead *counted* in the line, so §9 stays honest
    that judgment items remain and will return with the next Check.
    """
    findings = "; ".join(item.text for item in items if item.kind == IMPL)
    pending = sum(1 for item in items if item.kind == HUMAN)
    aside = (f" ({pending} human-judgment item(s) ride along and return with the next Check)"
             if pending else "")
    return (f"Auto-iterate (round {attempt}): Check found implementation-level defects Do "
            f"can fix{aside} — {findings}")


def write_decision(d: Path, items: list[NeedsHumanItem]) -> None:
    """Write the ``iterate-do`` decision + rationale, and spend one round of the budget.

    Guarded: refuses to write anything for an ineligible item set, so no caller can turn
    this into an auto-accept.
    """
    if not eligible(items):
        raise ValueError("auto-iterate: refusing to decide on a non-implementation finding set")
    attempt = bump(d)
    (d / SIGNOFF_DECISION).write_text(
        f"{DECISION}\n{rationale(items, attempt=attempt)}\n", encoding="utf-8")
