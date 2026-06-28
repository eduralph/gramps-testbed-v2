---
title: "Note navigation label: hardcoded 40-character truncation in gramps/gen/utils/db.py should use a config setting"
managed: false
status: draft
---

<!--
  Surfaced during the Gramps Testbed v2 PDCA cycle for issue_8597
  (verify-note-preview-length-configurable). The Note Preview-column path was
  already fixed (hardcoded 79 → interface.note-preview-length config); this
  residual hardcoded limit on the status-bar / navigation-label path was found
  during verification and scoped out of that bundle as a follow-up decision.
-->

# Suggestion — make the Note navigation-label truncation configurable

> **Repo:** gramps-project/gramps · **Branch:** maintenance/gramps61 ·
> **Category:** Enhancement / consistency · **Severity:** minor

**Summary:** `gramps/gen/utils/db.py` `navigation_label()` still truncates Note
text at a hardcoded `40` characters for the status-bar / navigation label, even
after the Note Preview-column fix (bug 8597) made `Note.get_preview()` honour the
configurable `interface.note-preview-length` setting. The two surfaces are now
inconsistent.

**Location:**

```python
# gramps/gen/utils/db.py:353–360  (maintenance/gramps61)
elif nav_type == "Note":
    label = obj.get()
    ...
    if len(label) > 40:
        label = label[:40] + "..."
```

**Background:**

Mantis 8597 reported that the Note view Preview column truncated at a hardcoded
79 characters. That was fixed upstream: `Note.get_preview()` now reads
`config.get("interface.note-preview-length")` (default 80, user-editable via
Preferences → Display). However `navigation_label()` — which builds the text
shown in the bottom status bar when a Note is selected — still hard-codes `40`.

**Decision required:**

Three reasonable paths exist; the right one is a project/maintainer call:

1. **Share `interface.note-preview-length`** — use the same config key for both
   Preview-column and navigation-label truncation. Simple and consistent, but
   couples two surfaces that may have different layout constraints.

2. **Add a separate config key** (e.g. `interface.note-nav-label-length`) —
   gives independent control, at the cost of another Preferences entry.

3. **Keep the constant, raise it** — if 40 is just too short (the original
   reporter mentioned it), bump it to match the Preview default (80) without
   adding a preference knob.

**Suggested action:**

Raise a Mantis enhancement against `gramps-project/gramps` scoped to
`gramps/gen/utils/db.py navigation_label()` to decide between the three options
above and implement the chosen one.
