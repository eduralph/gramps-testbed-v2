---
title: "get_addon_translator() should resolve the addon root automatically"
managed: false
status: draft
---

<!--
  A change suggestion (vault-internal; not a published wiki page). Written to file
  directly in the Gramps Mantis tracker, **Feature Requests** project. Raised by
  bryndin while reviewing addons-source PR 941 (NameSuite, the first nested-package
  addon) and kept out of scope for GEPS 049. Inside a Mantis note, "#nnnn" means
  another Mantis ticket, so GitHub PRs are referenced as plain text + URL.
-->

# Feature Request — `get_addon_translator()` should resolve the addon root automatically

> **Project:** Feature Requests · **Category:** Translation / Plugins · **Severity:** feature

**Summary:** Make `get_addon_translator()` locate the addon's `locale/` directory on
its own, so translation works from any module of a multi-file (nested-package) addon.

**Description:**

The documented addon i18n idiom binds the translation function per module:

```python
from gramps.gen.const import GRAMPS_LOCALE as glocale
try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext
```

`get_addon_translator(__file__)` loads the catalog from `dirname(__file__)/locale`.
That works for a single-file addon, but for an addon laid out as a package
(`MyAddon/sub/pkg/module.py`) a module that binds `_` makes the lookup search
`MyAddon/sub/pkg/locale`, which does not exist — the `ValueError` is swallowed and
the user silently gets the **untranslated English** string, even though the compiled
catalog is present at `MyAddon/locale/`. (Verified against real Gramps with a
compiled `ru/LC_MESSAGES/addon.mo`: bound in a nested module a Russian user gets the
source string; anchored at the addon root they get the translation.)

The current way to make it work is a per-addon shim (an `i18n.py` that computes the
addon root and anchors the lookup there), copy-pasted into each addon. That is a
workaround for a Gramps limitation: it is not reusable, it has to be maintained per
addon, and it forces every addon author to understand Gramps's translation internals
instead of writing their addon.

**Request:** have `get_addon_translator()` discover the addon root (the directory
that holds `locale/`) itself — e.g. walk up from the caller's path to the addon's
top-level plugin directory — so the documented one-liner works regardless of which
module binds `_`, with no per-addon boilerplate.

**Additional information:**

- Raised by bryndin in addons-source PR 941
  (`https://github.com/gramps-project/addons-source/pull/941`), his "Option 1: make
  Gramps `get_addon_translator()` handle it." Benefits he notes: simplest for addon
  developers (reuse the sample code unchanged), takes load off the addons-source
  reviewers, and needs no migration of existing addons (the old `__file__` call keeps
  working — root discovery is a superset).
- It is a Gramps-core change (`gramps/gen/utils/grampslocale.py`), which is the point:
  solving it once in core removes the workaround from every multi-file addon.
- Related, separate idea (its own request): Nick Hall suggested distributing the
  *aggregated, compiled* addon translations rather than extracting them, so a
  translation-only update does not force a new addon version. Noted here only so the
  two are not conflated.
- Out of scope for GEPS 049 (the addon API-versioning proposal); files on its own.
