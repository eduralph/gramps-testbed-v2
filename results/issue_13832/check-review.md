# Advisory review — SKIPPED (close disposition), evidence recorded

The reviewer leaf was skipped: this bundle's Plan concluded a close / no-fix disposition, so there is no patch to review.

## Close evidence (fixed upstream / superseded)

This is a **fixed-upstream** close, not an unverified "cannot reproduce". The reported
defect — Graph View rendering blank when an active person connects to a Gramps-Web person
whose UUIDv4 handle contains hyphens — is resolved by a **merged** commit whose root cause
matches the reporter's diagnosis (unquoted DOT node ids split at the hyphen):

- **`gramps-project/addons-source@8204d023`** (branch `maintenance/gramps61`, 2026-05-29) —
  *"Quote handles in GraphView Graphviz output … Graphviz splits an unquoted id at the
  hyphen, so the node, edge and cluster names were mangled and the view rendered blank.
  Quote the handle at the three sites where it is emitted as a DOT id. **Fixes #13832**"*.
- **`gramps-project/addons-source@4d40d02d`** (same branch, 2026-05-29) —
  *"GraphView tests: skip only on genuine import absence … **Fixes #13832**"* (test hardening).

Note: the fix lives in the **GraphView addon** (`addons-source`), not core `gramps` as the
brief's target field implied. No further repro run is required — a merged fix at the exact
emit sites is stronger evidence than a one-off GUI reproduction.

- [x] NEEDS-HUMAN — Close disposition confirmed: superseded by merged fix `addons-source@8204d023` (Fixes #13832).
