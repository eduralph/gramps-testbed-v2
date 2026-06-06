---
title: "Gramps 6.1 Wiki Manual - Core Development - Internationalization"
categories: [Developers, Gramps 6.1]
managed: true
---

<!--wiki:{{man index|6.1}}-->

## Overview

Gramps is a thoroughly globalized application: every user-visible string in the core repository ([`gramps-project/gramps`](https://github.com/gramps-project/gramps)) is meant to be translatable, and the project ships dozens of locale catalogs in `po/`. As a core contributor you have two distinct jobs around internationalization (i18n):

1. **Mark strings correctly** so the GNU `gettext` toolchain can extract them and translators can localize them.
2. **Keep the extraction lists current** — `po/POTFILES.in` and `po/POTFILES.skip` are maintained *by hand* in core, and CI checks them. This is the duty most easily forgotten when you add or delete a `.py` file.

This page is how-to and explanatory. The normative MUST/SHOULD rules live in [[16-guidelines]] (§Translation, §"Adding and removing Python files"); the in-repo coding standard is `gramps/AGENTS.md` §Internationalization. Cite those when reviewing — this page shows you how to satisfy them.

## Marking strings for translation

### The translation alias `_()`

Core modules obtain the translation function from the process-wide `GRAMPS_LOCALE`, conventionally aliased to `glocale`, and bind `_` to its translator:

```python
# ------------------------
# Gramps modules
# ------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale

_ = glocale.translation.gettext
```

`GRAMPS_LOCALE` is the singleton `GrampsLocale` created once at `gramps/gen/const.py:252`, with `_` defaulting to its `sgettext` translator at `gramps/gen/const.py:253`. Per-module files re-bind `_` themselves (e.g. `gramps/gen/lib/person.py:33` imports `GRAMPS_LOCALE as glocale`, and `:53` sets `_ = glocale.translation.gettext`). Wrap every user-visible string:

```python
raise ValueError(_("Invalid handle: %s") % handle)
```

This mirrors the rule in `gramps/AGENTS.md` §Internationalization and [[16-guidelines]] §Translation (MUST). What counts as "user-visible": dialog labels, menu entries, report text, error/status messages, tooltips — anything a user can read. Log messages aimed at developers and internal identifiers are *not* wrapped.

### The no-f-string / no-`.format()`-inside-`_()` rule

`xgettext` (the extractor) reads your source statically. It can pull a literal `"User %s"` out of `_("User %s")`, but it cannot evaluate an f-string or a `.format()` call to recover the template. **The translatable literal must be the bare argument to `_()`.** Interpolate *after* translating.

| | Form |
|---|---|
| **Bad** | `_(f"User {name}")` |
| **Bad** | `_("User {}".format(name))` |
| **Good** | `_("User %s") % name` |
| **Good** | `_("User {user}").format(user=name)` |

The key is that the static string literal is what `_()` receives; the substitution happens on the *result*. Old-style `%` formatting is the dominant style in core, but translating first then calling `.format()` on the returned string is equally fine — see the live example in `gramps/gen/lib/date.py:303`, where `ngettext(...).format(number_of=Span.ALIVE)` formats the *already-translated* string.

### Plurals: `ngettext`

Languages pluralize differently (English has two forms; Czech has three; Chinese has one). Never build a plural by hand with an `if n == 1`. Use `ngettext(singular, plural, n)`, which picks the right form per the target language's `Plural-Forms` header:

```python
ngettext = glocale.translation.ngettext

msg = ngettext("Found %d item", "Found %d items", count) % count
```

`ngettext` is a method on the translator (`gramps/gen/utils/grampstranslation.py:202`). [[16-guidelines]] §Translation marks this SHOULD. Both the singular and plural English literals are extracted as `msgid`/`msgid_plural`; the translator supplies one `msgstr[]` per plural form (see [`.po` format](#the-po-pot-format-for-contributors) below).

### Context: prefer `_(string, context)` over `pgettext`

The same English word can need different translations by context — the classic case is **Title** (a book's title vs. a person's nobility title). To disambiguate, pass a context. The Gramps translator's `gettext` accepts an optional second argument (`gramps/gen/utils/grampstranslation.py:183`, `def gettext(self, msgid, context="")`), so the **preferred** form is:

```python
_("Title", "book")
_("Title", "person")
```

This is preferred over calling `pgettext(context, message)` directly — `gramps/AGENTS.md` §Internationalization and [[16-guidelines]] §Translation (SHOULD). The translator still has `pgettext` (`grampstranslation.py:273`), but new core code should go through `_`.

You will also see the older **pipe-prefix** form, `_("book|Title")`, in legacy code and in Glade files; `sgettext` strips the `context|` prefix before display. Both produce a context hint the translator sees and drops in the translation. For new Python code, the two-argument `_(string, context)` form is the one to reach for.

### Deferred translation: `N_()`

Sometimes you need to *mark* a string for extraction at definition time but *translate* it later, at display time — typically a module-level constant or a lookup table built before the user's locale matters. `N_()` (the standard `gettext` "no-op" marker) does exactly this: it returns its argument unchanged so `xgettext` extracts the literal, and you call `_()` on it when you actually display it.

```python
# Defined at module load — not yet translated:
_REPORT_MODES = [N_("Ancestors"), N_("Descendants")]

# Translated only when shown to the user:
label = _(_REPORT_MODES[index])
```

[[16-guidelines]] §Translation marks `N_()` a SHOULD for this case. Note `N_` is purely a marker for the extractor — forgetting the later `_()` means the string is extracted but never actually translated at runtime.

### `glocale` / `GRAMPS_LOCALE` setup

`GRAMPS_LOCALE` (aliased `glocale`) is the application's single `GrampsLocale` instance, defined in `gramps/gen/const.py:252`. It owns the active language, the translation catalogs, and the collation/date/number formatting for the locale. Because `gramps.gen.*` must stay self-contained ([[16-guidelines]] §Source structure), importing `GRAMPS_LOCALE` from `gramps.gen.const` is the canonical way for any core module — `gen`, `gui`, or `plugins` — to reach the translator. You bind your own `_` / `ngettext` from `glocale.translation`; you do **not** call the Python stdlib `gettext` module directly.

## The `.po` / `.pot` format (for contributors)

You will occasionally read or hand-edit a catalog entry — for example to understand a translator's bug report. The mechanics below come from [Translating Gramps](wiki:Translating_Gramps); translators do the bulk of this work, but a core contributor should recognize the format.

- **`gramps.pot`** — the *template*: every extracted `msgid` with empty `msgstr`s. Generated from the source in `po/`. Translators copy it to `<lang>.po`.
- **`<lang>.po`** — one catalog per language (`fr.po`, `ru.po`, …), the template with translations filled in.
- **`.mo`** — the compiled binary catalog that the running program loads; built at install/build time.

### Header

Each `.po` starts with a header block. The fields that matter for correctness:

| Field | Purpose |
|---|---|
| `Content-Type: text/plain; charset=UTF-8` | Encoding. Gramps catalogs are UTF-8, no BOM. |
| `Plural-Forms: nplurals=N; plural=…;` | Drives how many `msgstr[]` slots `ngettext` entries need for this language. |
| `Last-Translator`, `Language-Team` | Attribution. |

### Entries: `msgid` / `msgstr` / fuzzy

```po
#: gramps/gen/lib/person.py:120
#, fuzzy
msgid "Invalid handle: %s"
msgstr "Ungültiges Handle: %s"
```

- `#:` — source file and line the string was extracted from (auto-generated; do not hand-maintain).
- `msgid` — the English source string; **never edit it in a `.po`** (it must match the source).
- `msgstr` — the translation.
- `#, fuzzy` — `gettext` guessed this translation after the source string changed. **Fuzzy entries are ignored at runtime** — the English `msgid` is shown until a translator confirms and removes the flag.

A plural entry uses `msgid_plural` and indexed `msgstr[]`:

```po
msgid "Found %d item"
msgid_plural "Found %d items"
msgstr[0] "%d Element gefunden"
msgstr[1] "%d Elemente gefunden"
```

Format placeholders (`%s`, `%d`, `%(name)s`) **must not** be translated or dropped, and their *count* must match `msgid`. A hand-edited `.po` should pass `msgfmt -c <lang>.po` before commit ([Translating Gramps](wiki:Translating_Gramps) §Plural forms).

## Core duty: maintain `po/POTFILES.in` and `po/POTFILES.skip`

This is the part of core i18n that CI will fail you on. The string extractor does not scan the whole tree blindly; it works from two hand-maintained lists in `po/`:

| File | Lists |
|---|---|
| `po/POTFILES.in` | Source files that **contain translatable strings** and must be scanned by `xgettext`. |
| `po/POTFILES.skip` | Source files that **intentionally have no translatable strings** and are deliberately excluded from the check. |

**Every `.py` file in core must be accounted for in exactly one of these two lists.** When your PR adds or removes a Python file you MUST update them ([[16-guidelines]] §"Adding and removing Python files"; `gramps/AGENTS.md` §Translation Files):

- **Add a file with user-visible strings** → add its path to `po/POTFILES.in`.
- **Add a file with no translatable strings** (pure logic, registration, etc.) → add its path to `po/POTFILES.skip`.
- **Delete a file** → remove its path from **both** lists (`POTFILES.skip` is grouped by package with comment headers — `gramps/cli/__init__.py`, test modules like `gramps/cli/test/argparser_test.py`, and so on are all listed there).

### Verifying the lists

`po/test/po_test.py` is the in-repo check that every source file appears in one list and no list references a missing file. Run it before committing:

```bash
PYTHONPATH=../../gramps python po/test/po_test.py
```

(Run from the `po/` directory; the `PYTHONPATH` points at the package root so the test can import Gramps. Both `po/POTFILES.in` and `po/test/po_test.py` exist on `maintenance/gramps61`.) A clean run means the lists are complete and consistent — it does **not** verify that your strings are *correctly marked*, only that your file is *accounted for*. Treat it as the narrow mechanical check it is ([[16-guidelines]] §"Verification before commit").

This is exactly the kind of bookkeeping that gets dropped under time pressure and surfaces as a CI failure or a hole in the extracted template, so make it part of the same commit that adds or removes the file.

## See also

- [[16-guidelines]] — the normative MUST/SHOULD reference for core (§Translation, §"Adding and removing Python files", §Source structure). Cite it in review.
- [[11-code-analysis]] — static analysis and the other mechanical checks a core PR must pass.
- `gramps/AGENTS.md` §Internationalization and §Translation Files — the in-repo coding standard this page restates.
- [Translating Gramps](wiki:Translating_Gramps) — the translator's guide: `.po` headers, plural forms, context, mnemonics.
- [Coding for translation](wiki:Coding_for_translation) — upstream's core-side string-marking conventions.
- [Python `gettext` documentation](https://docs.python.org/3/library/gettext.html) — primary reference for `gettext`, `ngettext`, and `pgettext`.

<!--wiki:{{stub}}-->
