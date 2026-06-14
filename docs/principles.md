# Planning Principles — solution-design discipline for briefs

> **Status:** living document. **Owner:** Eduard Ralph.
> **Counterpart:** [`fork-discipline.md`](fork-discipline.md) — the **Check**-closing /
> contribution discipline; this file governs **Plan**-time solution design. The two are
> a deliberate pair, one per PDCA beat (doc map below).
> **Why this exists.** A brief that names a *solution mechanism* (a probe, a guard, a
> helper) instead of the *property the fix must restore* seats the fix shape before Do
> reasons about it — and no downstream gate can recover the right shape from a wrong
> success criterion. This document gives Plan the rules and a sourced invariant
> catalogue so it states the right success property before Do ever runs. It was born
> from a real cycle where a symptom-guard shipped where cause-removal was the correct,
> comparably small fix — caught only at human review, one rework round-trip too late.
>
> **Two layers.** This reference layer is the *library*: document a principle here
> freely (near-zero cost). The *active layer* — the brief-template `Invariant to
> restore` field, the planner's minimalism qualifier, and the Plan-exit gate — is the
> small set the brief actually asks about, on the matching defect category (§6). The
> reference layer holds knowledge; the active layer is the few questions worth
> interrupting planning to ask every relevant time. Graduate a principle from reference
> to active only on evidence it is being missed (§8).

**Doc map — the generic-doctrine pair and its instance answers:**

| Doc | PDCA beat | Layer |
|---|---|---|
| [`principles.md`](principles.md) (this file) | **Plan** — solution-design discipline | generic doctrine (templated) |
| [`fork-discipline.md`](fork-discipline.md) | **Check** — closing / contribution discipline | generic doctrine (templated) |
| [`INTEGRATION.md`](INTEGRATION.md) | all — the concrete per-project answers | instance |

---

## 1. Process principle — minimalism is scoped to behavioural bug fixes

- **1.1** In bug-fixing, the target is the smallest reviewable, low-risk delta against
  code you do not own.
- **1.2** The maxim does **not** apply when a fix touches *structure* — what runs at
  load/import, object lifetime, where work happens. There the target is the smallest
  change that **restores the invariant** (§5), not the smallest diff. A named invariant
  takes precedence over diff size.
- **1.3** New-feature work is not governed by minimalism at all.

> Why: when "minimal" is the only *named* currency in the room, it wins by default —
> even on a structural fix where it is out of scope per 1.2. Name the invariant so it
> has something to lose to.

## 2. Process principle — a cost used to reject an alternative must be checkable

- **2.1** Rejecting an alternative on cost requires a **verifiable basis** — a diff
  sketch or a concrete line count someone can check — never an adjective ("heavier",
  "larger", "touches every reader").
- **2.2** A precise estimate of the *wrong* comparison is still wrong. If a named
  invariant is in play, cost-vs-minimalism is not the deciding axis (1.2 governs).
  Estimation is the **backstop**, not the decision.

> Why: an unquantified "heavier" is exactly how a cheaper, better fix gets discarded.
> Make the cost claim checkable and the false ones fall away.

## 3. Process principle — a brief states the invariant, not a solution

- **3.1** Scope names the **defect to remove**. It must **not** name a probe, guard, or
  helper (a capability check, a `hasattr`, a `try/except import`). Naming a mechanism
  seats the fix shape before Do reasons about it.
- **3.2** The invariant is **quantified over the defect category**, not the repro file.
  **Self-test:** *could Do satisfy this by guarding a single module?* If yes, it is the
  narrow symptom-sentence — widen it until a one-module patch visibly fails it.
- **3.3** Mechanism is left to Do; Do prefers removing the cause over guarding the
  symptom.
- **3.4** When the fix needs a *testable seam* — extracting logic so a test can reach it
  without the GUI / heavy deps — the success evidence MUST exercise the **production
  path**: production calls the same extracted unit the test drives. A test that drives a
  *parallel re-implementation* or hand-copy of the production path (so it validates a
  copy) is not acceptable evidence — it leaves the real path untested and drift uncaught.
  This is an *outcome*, not a mechanism (so it does not violate 3.1): Plan states "the
  test drives the production path"; Do chooses how — e.g. inverting a GUI-entangled
  generator into a shared one, or a callback seam — per 3.3.

> The self-test is the load-bearing rule: a success criterion narrow enough to be met
> by guarding one module is narrow enough to let the wrong fix pass. Widen it until only
> the real requirement satisfies it.

## 4. Sourcing principle — invariants come from named, citable sources

- **4.1** Domain invariants live in the catalogue (§5), each with a source and a
  provenance tier.
- **4.2** When Plan classifies a brief into a defect category (§6 mapping), it pulls the
  matching invariant **and its citation** into the brief's `Invariant to restore` field.
- **4.3** A sourced invariant can override "minimal" in a Do/Check argument; an
  unsourced intuition cannot. This is the content Principles 1–3 operate on — without
  it, "state the invariant" (3) just produces a plausible-sounding guess, which lands
  back on the narrow sentence.

---

## 5. The invariant catalogue (sourced)

Provenance tiers, kept separate on purpose — a planner must see *which family* a
given invariant draws its authority from. `[ACTIVE]` = also in the §6 brief mapping.

> **Provenance status (verified 2026-06-07).** Citations below were checked against
> the live sources; see §7 for the honesty rules that keep the catalogue citable.

### Tier A — Python (PEP)

- **`[ACTIVE]` Import binds names; it does no work.** No I/O, construction, probes,
  or registry population at module- or class-body scope. Defer to first use.
  - **PEP 8 — Imports** (Active; the firm anchor): import hygiene / placement.
    `https://peps.python.org/pep-0008/#imports`
  - **PEP 810 — Explicit lazy imports** (corroborating; **Accepted**, Python 3.15,
    resolved 2025-11-03): names import-time side effects and the registry pattern as
    the canonical reliance, and adds opt-in lazy-import syntax. It **motivates** the
    hazard; it does **not** forbid import-time side effects — the standing rule is
    PEP 8 + the import system, which 810 corroborates.
    `https://peps.python.org/pep-0810/`
  - **PEP 20 — The Zen of Python** (Active; *philosophy tier*, not technical):
    "explicit is better than implicit"; "special cases aren't special enough to
    break the rules." Backs the Principle 1/3 framing that a guard papering over a
    hidden side effect is the wrong shape. `https://peps.python.org/pep-0020/`
  - *Illustrative only (not authoritative):* C. Morgan, "Say 'no' to import
    side-effects in Python" — a GUI-toolkit object built at import segfaulting under
    `help('modules')`; the exact analog of #2357. Use as the war-story, cite PEP 8/810
    for the rule. `https://chrismorgan.info/blog/say-no-to-import-side-effects-in-python/`

### Tier B — GTK / PyGObject (GNOME)

> **GTK3 vs GTK4:** Gramps is **GTK3**. Pin the gtk3 URL for anything cited against
> Gramps today; init and threading details changed in GTK4 (GTK4 dropped the
> `gdk_threads_*` locking). Note "GTK4 differs" inline so a future migration does not
> silently invalidate a citation.

- **`[ACTIVE]` No GTK/Gdk operation before init or without a display.** Widget
  construction, style-context reads, icon-theme/display queries are invalid until GTK
  is initialized and a display exists.
  - **Rule (GTK3, authoritative):** `gtk_init()` reference —
    *"Call this function before using any other GTK+ functions in your GUI
    applications." … "This function will terminate your program if it was unable to
    initialize the windowing system for some reason." … "If you want your program to
    fall back to a textual interface you want to call gtk_init_check() instead."*
    `https://docs.gtk.org/gtk3/func.init.html`
  - **Recoverable probe (GTK3, authoritative):** `gtk_init_check()` reference —
    *"does not terminate the program … Instead it returns FALSE on failure"*, letting
    the app fall back to a curses / command-line interface.
    `https://docs.gtk.org/gtk3/func.init_check.html`
    *(The `getting_started` tutorial only shows `gtk_init()` in an example; cite the
    `func.init*` reference pages for the rule itself.)*
  - **Direction of travel (GTK, forward-looking):** GNOME GTK MR 7836 — *"gdk: No
    displays before init / Don't allow to create displays before gdk has been
    initialized"* (targets `main`, addresses Nautilus-freeze issue #7035). GTK3
    tolerates pre-init display access; GTK `main` will not, so the invariant is
    forward-correct. *(The specific release version and the abort signal are not
    stated by the MR — do not attribute a `SIGTRAP` signature to it; the SIGTRAP in
    #2357 is observed in our own bundle logs.)*
    `https://gitlab.gnome.org/GNOME/gtk/-/merge_requests/7836`
  - **Note on `has_display()`:** `gramps.gen.constfunc.has_display()` wraps
    `gtk_init_check()`. The GTK docs explain *why* it exists — a recover-don't-die
    probe — and *where* it belongs: at the application boundary (decide GUI-vs-text
    once at startup), **not** scattered inside widget modules. This is the upstream
    backing for the maintainer objection on #2357.

- **`[ACTIVE]` Environment-dependent values are built in `__init__`, not as
  class-body constants.** Lazy/first-use over eager.
  - **Authoritative (official PyGObject):** GTK3 tutorial — Objects / Getting
    Started. Canonical shape: subclass the GObject type, chain the parent constructor,
    construct child widgets and read properties *inside* `__init__`, never at class
    scope. `https://python-gtk-3-tutorial.readthedocs.io/en/latest/objects.html`
    (canonical-domain mirror: `https://pygobject.gnome.org/tutorials/gtk3/`)

- **GTK has main-thread affinity.** Widgets touched only from the main thread;
  marshal background work onto the main loop with `GLib.idle_add()`.
  *(Reference layer — promote to `[ACTIVE]` only if a threading defect surfaces.)*
  - **Authoritative (official PyGObject):** Threads & Concurrency. "GTK isn't thread
    safe; only the main thread may call GTK code; schedule from other threads with
    `GLib.idle_add()`." `https://pygobject.readthedocs.io/en/latest/guide/threading.html`
    (canonical: `https://pygobject.gnome.org/guide/threading.html`)
  - C-level corroboration: GDK3 "Threads" reference — use GTK/GDK only from the
    thread `gtk_init()`/`gtk_main()` ran on.

### Tier C — Internal (Gramps project invariants; no external canon)

> These carry weight on their own as documented project rules. Do **not** borrow
> GTK/PEP authority for them — state the rationale instead.

- **Every signal connection has an owner that disconnects it** (GObject lifecycle).
  *Mixed provenance:* PyGObject Objects/signals doc covers the *mechanism*
  (`g_signal_connect`/`disconnect`); the **obligation** is your own
  `gramps-connect-without-disconnect` Semgrep rule — that is the firmer local
  authority. Maps to **Class A** (teardown/cleanup `AttributeError`).
  *(Reference layer until evidence promotes it.)*
- **A handle resolves or is cleaned up** (reference integrity). No external source;
  author as a Gramps invariant with its own documented rationale. Maps to **Class B**
  (dangling-handle / reference integrity). *(Reference layer.)*

## 6. Category → invariant mapping (the active layer)

When Plan classifies a brief into one of these, it MUST pull the invariant **and its
citation** into the brief's `Invariant to restore` field (Principle 4.2).

| Defect category | Invariant Plan must state | Cite |
|---|---|---|
| import-safety / headless / test-discovery | import binds names, does no work | PEP 8 §Imports (+ PEP 810) |
| any `gramps.gui.*` running outside a confirmed display | no GTK/Gdk before init or without a display | GTK3 `func.init` / `func.init_check` |
| "this value must depend on the running environment" | build in `__init__`, not class body | PyGObject GTK3 Objects |
| teardown / cleanup / object-lifetime (Class A) | every connection has an owner that disconnects | internal Semgrep rule |

Threading and reference-integrity (Class B) stay reference-layer; promote on evidence.

---

## 7. Provenance honesty rules (keep the catalogue citable)

- **Cite for what the source says, not an inflated ruling.** If a source documents a
  hazard while adding a feature, it does not necessarily *forbid* the thing — cite the
  standing rule for the prohibition and the newer source as corroboration.
- **Check a standard's status and target version.** Draft/Rejected ranks below
  Final/Accepted; a rule accepted for a runtime version you do not yet ship is
  corroborating, not yet enforceable. Note status and version beside each citation.
- **Authoritative vs illustrative.** Official specs and vendor docs are authoritative;
  blog posts and war-stories are illustrative — tag them so, and cite the rule from the
  page that actually *states* it, not a tutorial that only demonstrates it.
- **Pin the version you target; note where a newer major differs.**
- **Internal invariants don't borrow external authority** — state the rationale.

## 8. Evidence basis & promotion rule

Promote a principle from reference to active (or to a hard gate) only on evidence — the
same bar the act-log applies to process deltas:

- **Active / template-asked:** the symptom-vs-cause fork **recurs** in a category (a
  real failure plus repeated decision-points across cycles). One war-story is enough to
  document a principle in §5; a recurring miss is what graduates it to §6.
- **Hard gate:** reserve for a category with a **real shipped failure**. Everything else
  stays reference until a cycle shows it was missed.

Resist a growing checklist. The discipline that keeps minimalism valuable is the same
one that keeps this set small: knowledge is documented freely (§5); enforcement is
rationed (§6).
