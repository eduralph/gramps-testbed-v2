# Build notes — issue 6250 (withheld from reviewer)

## What the brief asked

A verify-first investigation, not a code fix. Success criterion: determine on
`maintenance/gramps61` whether `Pango.AttrList.get_iterator()` / `Pango.AttrIterator`
are available via the shipped PyGObject bindings, and resolve the ticket's open
condition accordingly:
- (a) available → workaround obsolete, ticket actionable as a *separate* cleanup;
- (b) not available → wontfix/by-design, keep the workaround.

Either way the brief says: **no functional change ships, no test file, no
new/removed files.**

## Why this is a no-patch (close-disposition) bundle, not a patch

The brief explicitly scopes out "actually reintroducing/removing the workaround"
and sets `Test file: none`. So the Do artifact is a recorded finding, not a
`patch.diff`. I deliberately did **not** write an empty `patch.diff`: in this
harness the close-disposition marker *is* the Do artifact (state.py:31-34,52-54),
and an empty `patch.diff` breaks `pdca publish` (harness #95, and my standing
note "verify-first close = no patch"). So the bundle ships:
- `close-disposition` → `manual-verification` (a valid token, config.py:19-25);
- `verification-finding.md` → the visible finding (brief: "a written finding in
  the bundle");
- `pango-availability-probe.py` → reproducible evidence;
- this `build-notes.md`.

`manual-verification` is the honest token: the deliverable is a manually-run
verification producing a finding. It is **not** wontfix — the finding is (a)
available, so a follow-up cleanup is warranted; that follow-up is a separate
bundle by design.

## How I verified (not recalled)

I ran the probe against the authoritative environment, not from memory:

1. Host GI stack: `hasattr(Pango.AttrList, "get_iterator")` → True,
   `hasattr(Pango, "AttrIterator")` → True, Pango 1.57.0; the full old-code loop
   (`get_iterator()` → `get_attrs()` → `Attribute.copy()` →
   `start_index`/`end_index` → `next()`) runs and yields introspectable
   attributes.
2. The **CI testbed image** `gramps-testbed:ubuntu-6.1.0` — the exact GI stack
   the T3/C4 gates run — Pango 1.52.1: identical result, "FULLY USABLE".

I ran the probe inside the container via a one-shot `docker run … python3` over a
read-only mount of the probe — a headless, throwaway invocation purely to read
the GI capability (no test suite, no display), so the no-timeout caveat about
hand-rolled test runners does not apply (there is no test to hang; it prints and
exits). The runner-with-timeout guidance is about *test* execution; this is a
capability read.

### A false alarm I chased down

An earlier probe draft picked a contrived split `index` and hit
`OverflowError: -1 not in range 0 to 4294967295` when subtracting `index` from a
small `end_index`. That is **not** a binding gap — it is unsigned-int arithmetic
in my throwaway test (and the production code at libcairodoc.py:681-683 guards
`start_index` with exactly that `if … > index` conditional). I rewrote the probe
to assert the *API surface* (presence + usability of the iterator and its
attribute objects) without the contrived arithmetic, and it passes cleanly. The
arithmetic edge belongs to the eventual reintroduction's test, not to this
availability check.

## Why the finding generalizes beyond the two probed stacks

Gramps 6.1 requires GTK ≥ 3.24 (README.md:18). That floor pulls in a Pango far
newer than the one where `pango_attr_iterator_get_attrs` lacked its
introspection annotation (the gnome 646788 era the workaround comment cites at
libcairodoc.py:670-673). So the minimum supported configuration already has it;
1.52.1 and 1.57.0 confirm empirically.

## Citations

- Workaround site: `gramps/plugins/lib/libcairodoc.py` on
  `maintenance/gramps61` @ `cbe5699b2e`:
  - `:669` GTK3 PROBLEM comment; `:674-684` OLD EASY CODE get_iterator loop;
    `:685-714` START/END OF WORKAROUND (manual `Pango.parse_markup` re-parse at
    `:711-713`).
- GI availability result: probe output above (Pango 1.52.1 testbed image;
  1.57.0 host) — `get_iterator`/`AttrIterator` present and usable.

## Ruled out

- **Shipping the cleanup now** (reintroduce OLD EASY CODE, delete workaround):
  out of scope per brief Scope ("out of scope: actually reintroducing/removing
  the workaround"). It also needs its own regression test over paragraph-split
  attribute re-indexing — a deliberate, separate decision.
- **wontfix/by-design**: that is the (b) branch; the evidence is (a) available,
  so this would misreport the finding.
- **Empty `patch.diff`**: rejected — breaks `pdca publish` (harness #95).
