---
title: "Gramps 6.1 Wiki Manual - Core Development - Tutorials"
categories: [Developers, Gramps 6.1]
managed: true
---

<!--wiki:{{man index|6.1}}-->

## Overview

End-to-end walkthroughs for a Gramps **core** contributor working on
[`gramps-project/gramps`](https://github.com/gramps-project/gramps). Each tutorial is
a numbered, runnable sequence from a clean checkout to a fix or a new plugin you can
exercise in place. They assume you already run Gramps from source on the production
branch `maintenance/gramps61` and have read the normative rules in [[16-guidelines]] —
this page is how-to; [[16-guidelines]] is the MUST/SHOULD reference these steps obey.

| Tutorial | Goal | What it shows |
|----------|------|---------------|
| [Fix a bug end-to-end](#tutorial-1-fix-a-bug-end-to-end) | A real defect, reproduced and fixed | Reproduce against `example.gramps`, write a failing `<module>_test.py` in the right `test/` package, fix, watch it go green, write the PR body |
| [Write a report](#tutorial-2-write-a-report) | A text report bundled in core | The Options/Report pair, the docgen `TextDoc` interface, registration via `.gpr.py`, `write_report()` |
| [A Quick View](#tutorial-3-a-quick-view) | A right-click report | The fixed `run()` signature, the category constant, context-menu access |

All three tutorials are end-to-end: reproduce, change, test, and prepare the
contribution. They run against the source checkout — core tests use a `test/`
package (singular) with the `<module>_test.py` suffix, target `maintenance/gramps61`,
and are gated by `mypy` and Black. See [[16-guidelines]] § Testing and § Contributor
workflow.

### A note on tutorial-style code

The code below shows the smallest thing that demonstrates each task. Two things are
omitted for readability and are **required** in shipped core code (both CI-gated):

- A **GPL-2.0-or-later license header** at the top of every `.py` file, in the
  canonical block form. Copy it from any existing core module. ([[16-guidelines]] §
  Source structure.)
- **Type hints** on every function and method, in Python 3.10+ syntax (`X | None`,
  `list[X]`). `mypy` reads `mypy.ini` (`files = ./gramps, ./test`) and is enforced on
  core PRs; `*.gpr.py` is excluded. ([[16-guidelines]] § Coding style.)

Black formats every changed `.py` file, including around the license header. Run it
before every commit ([[16-guidelines]] § Coding style).

## Tutorial 1: fix a bug end-to-end

**Goal.** Take a Mantis bug from "can't reproduce" to a reviewable PR: reproduce it
against the canonical fixture, capture it in a failing test, make the fix, watch the
test go green, and write the PR body in the required shape.

The test lands in a `test/` package beside the module, named `<module>_test.py`, and
the PR targets `maintenance/gramps61`. The example below uses a hypothetical bug — a
method on a `gramps.gen.lib` class returning the wrong value for an edge case — to
keep the mechanics in focus; substitute your real defect.

### 1. Get on the right branch from upstream

Branch from `upstream/maintenance/gramps61`, not your fork's tracking copy — fork
bases drift ([[16-guidelines]] § Contributor workflow; `docs/INTEGRATION.md` §2).

```bash
git fetch upstream
git switch -c bug-NNNNN upstream/maintenance/gramps61
```

`gramps.gen.*` is the headless, GUI-free core; running its tests needs no display.
Set `GRAMPS_RESOURCES` to the checkout root so the resource loader resolves:

```bash
export GRAMPS_RESOURCES=.
```

### 2. Reproduce against `example.gramps`

`example/gramps/example.gramps` is the canonical fixture; "couldn't reproduce" is the
most common reason a fix stalls in triage, so reproduce here first ([[16-guidelines]]
§ Contributor workflow). For a `gen`-level defect you usually don't need the GUI at
all — reproduce in the interpreter against the library object directly:

```bash
GRAMPS_RESOURCES=. python3 -c "
from gramps.gen.lib import Date
d = Date()              # an empty date
print('is_empty ->', d.is_empty())   # observe the wrong result here
"
```

If the bug only surfaces through the loaded tree, drive it from a small script that
opens the fixture and walks the affected objects (`db.iter_people()`,
`db.get_event_from_handle(...)`); see [[06-data-access]] for the read patterns. Pin
down the exact input that triggers the wrong behaviour — that input becomes your test.

### 3. Write the failing test in the right `test/` package

Place the test in a **`test/`** package (singular) alongside the module under test,
named **`<module>_test.py`** (the `_test.py` *suffix*). For a fix in
`gramps/gen/lib/date.py:1882` (`Date.is_empty`), the test goes in
`gramps/gen/lib/test/date_test.py` — which already exists; add a method to it, or
create the file with an `__init__.py` if the package is new. Putting the file
anywhere else hides it from the runner ([[16-guidelines]] § Testing;
`docs/INTEGRATION.md` §3). Use stdlib `unittest` — never `pytest`.

```python
"""Regression test for Mantis #NNNNN."""

import unittest

from ..date import Date


class TestEmptyDate(unittest.TestCase):
    """Regression: an empty Date must report itself as empty (#NNNNN)."""

    def test_empty_date_is_empty(self):
        date = Date()
        self.assertTrue(date.is_empty())
```

Prepend a class-header navigation comment to the `TestCase` in the boxed `#---` form
when several classes share the file ([[16-guidelines]] § Source structure). Run just
this file and confirm it is **red before the fix** — a test that passes pre-fix proves
nothing:

```bash
GRAMPS_RESOURCES=. python3 -m unittest gramps.gen.lib.test.date_test -v
```

### 4. Make the fix

Edit the module so the defect is corrected, citing `path:line` on
`maintenance/gramps61` in your notes (here, `gramps/gen/lib/date.py:1882`). Keep it
**one logical change** — don't fold in unrelated cleanups ([[16-guidelines]] §
Contributor workflow). Respect the submodule import rule: code in `gramps.gen.*` must
not import from `gramps.gui.*` / `gramps.plugins.*` ([[16-guidelines]] § Source
structure). Wrap any new user-visible string with `_()`, and never wrap an f-string or
`.format()` result ([[16-guidelines]] § Translation).

### 5. Watch it go green, then run the whole suite

Re-run the targeted test — it must now pass — then discover the full suite to confirm
you broke nothing else:

```bash
GRAMPS_RESOURCES=. python3 -m unittest gramps.gen.lib.test.date_test -v
GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"
```

Then the static gates, exactly as CI runs them:

```bash
git diff --name-only --diff-filter=ACMR origin/master...HEAD \
  | grep '\.py$' | xargs --no-run-if-empty black
mypy        # reads mypy.ini: files = ./gramps, ./test
```

A green test, Black clean, and `mypy` exiting 0 each verify something *narrow* —
respectively that this input now behaves, that formatting matches, and that types
check. None of them verifies the fix is correct for inputs you didn't test; say so in
your own review ([[16-guidelines]] § Verification before commit). After you push,
watch the PR's CI (`gh pr checks <PR#> --watch`) — local checks are static only.

### 6. Update the translation file list if you touched the file set

If your fix **adds or removes** a `.py` file, update `po/POTFILES.in` (has
translatable strings) or `po/POTFILES.skip` (none), and remove from **both** on
deletion. Editing an existing file needs no change here. Verify ([[16-guidelines]] §
Adding and removing Python files):

```bash
PYTHONPATH=../../gramps python po/test/po_test.py
```

### 7. Commit and write the PR body

The commit subject is ≤ 70 chars, the body wraps at 80, and the Mantis trailer is on
the **last** line ([[16-guidelines]] § Commit messages):

```
Treat an empty Date as empty in is_empty().

An empty Date object reported itself as non-empty because the modifier
check ran before the value check, so callers guarding on is_empty() did
the wrong thing. Reorder the guard so an unset value short-circuits.

Fixes #NNNNN.
```

Structure the PR body as **Root cause / Fix / Verified against / Test**, citing
`path:lines` on `maintenance/gramps61`, and end the PR body with `Fixes #NNNNN` too
([[16-guidelines]] § Contributor workflow):

```text
Root cause: gramps/gen/lib/date.py:1882 — is_empty() checked the modifier
  before the value, so a freshly constructed Date() returned False.
Fix: reorder the guard in Date.is_empty() to short-circuit on an unset value.
Verified against: gramps/gen/lib/date.py:1882 on maintenance/gramps61.
Test: gramps/gen/lib/test/date_test.py::TestEmptyDate — red before, green after.

Fixes #NNNNN
```

Open it as a **draft** against `maintenance/gramps61` for CI; mark ready only after
re-reading the diff with fresh eyes. Do not merge or mark ready as part of this work —
that is the maintainer's step ([[16-guidelines]] § Contributor workflow).

For the read/write API used while reproducing, see [[06-data-access]]; for the class
catalogue, [[07-api-reference]]; for the test runner and discovery details,
[[08-testing]].

## Tutorial 2: write a report

**Goal.** A text report that summarises the open tree — total people, counts by
gender, unique surnames, most common surname — produced through any docgen backend
(PDF, ODF, plain text, HTML).

A report is three pieces wired together: a **Report** subclass that walks the data and
emits paragraphs into the live document, an **Options** subclass that declares
user-adjustable options and default paragraph styles, and a **registration** call in a
`.gpr.py`. As a bundled core report, the files live under `gramps/plugins/`, are
imported as `gramps.plugins.*`, and bind `_` with `glocale.translation.gettext`.

### 1. Place the files in the plugins tree

A bundled core report lives in `gramps/plugins/<category>/`, e.g.
`gramps/plugins/textreport/`, paired with its `.gpr.py`:

```
gramps/plugins/textreport/
├── dbsummary.gpr.py
└── dbsummary.py
```

### 2. Register both classes in `dbsummary.gpr.py`

The `register()` call points `reportclass` at the Report and `optionclass` at the
Options, declares the category, and lists the run modes:

```python
register(
    REPORT,
    id="db_summary",
    name=_("Database Summary"),
    description=_("Produces a short summary of the family tree."),
    version="1.0",
    gramps_target_version="6.1",
    status=STABLE,
    fname="dbsummary.py",
    category=CATEGORY_TEXT,
    require_active=False,
    reportclass="DbSummaryReport",
    optionclass="DbSummaryOptions",
    report_modes=[REPORT_MODE_GUI, REPORT_MODE_CLI],
)
```

`category=CATEGORY_TEXT` makes this a text report, so Gramps offers the text-output
backends; `require_active=False` because a tree-wide summary needs no active person.
Add `REPORT_MODE_BKI` to `report_modes` to also offer it as a Book item — see
[Report API](wiki:Report_API) for the index-mark code a Book item needs. The full
registration field set is documented at
[`gen/gen_plug.html#register`](https://gramps-project.org/docs/gen/gen_plug.html#gramps.gen.plug._pluginreg.register).
`.gpr.py` files are excluded from `mypy` (per `mypy.ini`).

### 3. Implement the Report and Options in `dbsummary.py`

```python
from collections import Counter

from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.lib import Person
from gramps.gen.plug import docgen
from gramps.gen.plug.report import MenuReportOptions, Report
from gramps.gen.plug.report import stdoptions

_ = glocale.translation.gettext


class DbSummaryReport(Report):
    """A text report summarising the database."""

    def __init__(self, database, options_class, user):
        Report.__init__(self, database, options_class, user)
        self.set_locale(
            options_class.menu.get_option_by_name("trans").get_value()
        )
        self._count()

    def _count(self):
        """Walk every Person and tally."""
        self.total = 0
        gender_counts = Counter()
        surnames = Counter()
        for person in self.database.iter_people():
            self.total += 1
            gender_counts[person.get_gender()] += 1
            primary = person.get_primary_name()
            surnames[primary.get_primary_surname().get_surname()] += 1
        self.gender_counts = gender_counts
        self.unique_surnames = len(surnames)
        self.top_surname = (
            surnames.most_common(1)[0] if surnames else (_("(none)"), 0)
        )

    def write_report(self):
        """Emit paragraphs into self.doc."""
        self.doc.start_paragraph("DBS-Title")
        self.doc.write_text(self._("Database Summary"))
        self.doc.end_paragraph()

        self.doc.start_paragraph("DBS-Normal")
        self.doc.write_text(
            self._("Total persons: %d") % self.total)
        self.doc.end_paragraph()

        for gender_code, label in [
            (Person.MALE, _("Males")),
            (Person.FEMALE, _("Females")),
            (Person.UNKNOWN, _("Unknown gender")),
        ]:
            self.doc.start_paragraph("DBS-Normal")
            self.doc.write_text(
                "%s: %d" % (label, self.gender_counts.get(gender_code, 0))
            )
            self.doc.end_paragraph()

        self.doc.start_paragraph("DBS-Normal")
        self.doc.write_text(
            self._("Unique surnames: %d") % self.unique_surnames)
        self.doc.end_paragraph()


class DbSummaryOptions(MenuReportOptions):
    """Options form and default styles for DbSummaryReport."""

    def add_menu_options(self, menu):
        category = _("Report Options")
        stdoptions.add_localization_option(menu, category)

    def make_default_style(self, default_style):
        # Title: 18 pt bold sans-serif, centred, header level 1.
        font = docgen.FontStyle()
        font.set_size(18)
        font.set_type_face(docgen.FONT_SANS_SERIF)
        font.set_bold(True)
        para = docgen.ParagraphStyle()
        para.set_header_level(1)
        para.set_alignment(docgen.PARA_ALIGN_CENTER)
        para.set_font(font)
        para.set_description(_("Style used for the title of the report."))
        default_style.add_paragraph_style("DBS-Title", para)

        # Body: 12 pt serif.
        font = docgen.FontStyle()
        font.set_size(12)
        font.set_type_face(docgen.FONT_SERIF)
        para = docgen.ParagraphStyle()
        para.set_font(font)
        para.set_description(_("Style used for normal report text."))
        default_style.add_paragraph_style("DBS-Normal", para)
```

### 4. Understand the docgen abstraction

`self.doc` is **not a file** — it's a live document, an instance of one of the docgen
backends (`gramps.gen.plug.docgen`), set up for you by `Report.__init__`
(`gramps/gen/plug/report/_reportbase.py:51`). You write *into* it with the docgen
`TextDoc` calls (`start_paragraph` / `write_text` / `end_paragraph`); the backend
decides whether that becomes PDF, ODF, or plain text. A `DrawDoc` backend adds
graphics primitives (lines, boxes, text-at-coordinate) for graphical reports — those
register with `category=CATEGORY_DRAW`. The `Report` base requires you to provide
`write_report()` (`gramps/gen/plug/report/_reportbase.py:91`); the framework runs your
`__init__`, then calls `write_report()`. Anything not emitted there is never seen.

Key points for core reports:

| Concern | Rule |
|---------|------|
| Style names | Prefix every paragraph-style name (`DBS-`) — Book reports compose many reports and names must be globally unique. Define them in `make_default_style` and register with `default_style.add_paragraph_style(...)` (`gramps/gen/plug/docgen/stylesheet.py:354`). |
| Localisation | `stdoptions.add_localization_option` adds the report-locale option named `"trans"`; the report reads it via `self.set_locale(...)` (`gramps/gen/plug/report/_reportbase.py:66`), which creates `self._` bound to the *report's* chosen locale. Use `self._(...)` for report content, plain `_(...)` for the option form labels. |
| Translation hygiene | `self._("... %d") % n`, never `self._(f"... {n}")` — `xgettext` cannot extract a dynamically built string ([[16-guidelines]] § Translation). |
| Options base | `MenuReportOptions` (`gramps/gen/plug/report/_options.py:936`) handles the widget plumbing; a no-options report only overrides `add_menu_options` and `make_default_style`. |

### 5. Wire it into the build and test in place

A new plugin file under `gramps/plugins/` is a new `.py` file, so add it to
`po/POTFILES.in` (the `.gpr.py` registration also carries translatable strings) and
verify with `PYTHONPATH=../../gramps python po/test/po_test.py` ([[16-guidelines]] §
Adding and removing Python files). Run from source; the report appears under
*Reports → Text Reports → Database Summary*. Generate it through several backends and
confirm the same content reflows in each. Black and `mypy` apply as in Tutorial 1.

For the full docgen interface, see [Report Generation](wiki:Report_Generation) and
[Report API](wiki:Report_API); for the data calls (`iter_people`, `get_primary_name`),
[[06-data-access]] and [[07-api-reference]].

## Tutorial 3: a Quick View

**Goal.** A right-click report on a person that lists their siblings — brothers and
sisters from every family the person is a child in.

A Quick View is the shortest path to a usable report: no class to subclass, no options
form — just a `run()` function and a registration. It's written against the **Simple
Access API** (`SimpleAccess`, `SimpleDoc`), which hides handle dereferencing and
formatting. As a bundled core Quick View, the files live under
`gramps/plugins/quickview/`.

### 1. Place the files

```
gramps/plugins/quickview/
├── siblings.gpr.py
└── siblings.py
```

### 2. Register with the category and run function

```python
register(
    QUICKVIEW,
    id="siblings",
    name=_("Siblings"),
    description=_("Lists the active person's siblings."),
    version="1.0",
    gramps_target_version="6.1",
    status=STABLE,
    fname="siblings.py",
    category=CATEGORY_QR_PERSON,
    runfunc="run",
)
```

`category=CATEGORY_QR_PERSON` puts the entry on the **person** context menu and fixes
what the third `run()` argument is. The category determines the selected object:
`CATEGORY_QR_FAMILY` → a family, `CATEGORY_QR_PLACE` → a place, and so on
(`CATEGORY_QR_DATE` is for embedding in other reports, since there is no Date view).
`runfunc="run"` names the function Gramps calls.

### 3. Implement `run()` in `siblings.py`

```python
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.simple import SimpleAccess, SimpleDoc
from gramps.gui.plug.quick import QuickTable

_ = glocale.translation.gettext


def run(database, document, person):
    """Display all siblings of the given person."""
    sdb = SimpleAccess(database)
    sdoc = SimpleDoc(document)

    sdoc.title(_("Siblings of %s") % sdb.name(person))
    sdoc.paragraph("")

    table = QuickTable(sdb)
    sdoc.header1(_("Siblings"))
    table.columns(_("Person"), _("Gender"), _("Birth date"))

    own_gid = sdb.gid(person)
    for family in sdb.child_in(person):
        for child in sdb.children(family):
            if sdb.gid(child) == own_gid:
                continue
            table.row(child, sdb.gender(child), sdb.birth_date(child))
            document.has_data = True

    table.write(sdoc)
```

### 4. The fixed entry point and the Simple Access surface

| Element | Detail |
|---------|--------|
| `run(database, document, person)` | The signature is fixed by the Quick View kind. The third argument is the category's selected object (`CATEGORY_QR_PERSON` → person). |
| `SimpleAccess` | High-level read interface (`gramps/gen/simple/_simpleaccess.py:58`): `sdb.children(family)`, `sdb.child_in(person)`, `sdb.birth_date(person)`, `sdb.name(person)`, `sdb.gid(obj)`. It hides handles, refs, and date formatting. |
| `SimpleDoc` | Matching write interface (`gramps/gen/simple/_simpledoc.py:34`): `sdoc.title(...)`, `sdoc.paragraph(...)`, `sdoc.header1(...)`. |
| `QuickTable` | Builds an interactive table (`gramps/gui/plug/quick/_quicktable.py:73`) where each row links back to a real object — clicking a person opens that person. |
| `document.has_data = True` | Tells Gramps the report produced output; if all rows are filtered out, the empty-state path triggers instead. |

`SimpleAccess`/`SimpleDoc` are re-exported from `gramps.gen.simple`
(`gramps/gen/simple/__init__.py:23-24`), so the single import line above is enough.
`QuickTable` lives under `gramps.gui.*` — fine for a Quick View, which is GUI code, but
it means this module is **not** importable from a headless `gen`-only context
([[16-guidelines]] § Source structure).

### 5. Run it and reach it from the context menu

Add `siblings.py` (and its `.gpr.py` strings) to `po/POTFILES.in`. Run Gramps from
source, then **right-click any person** in the People view or the person editor:
*Quick View → Siblings* appears. The result opens in a Quick View window; clicking a
row opens that person. Validate against `example.gramps` to see real siblings.

For Quick Views that outgrow the Simple Access surface, drop to the full DB API
([[06-data-access]], [[07-api-reference]]); the two are complementary in one module.

## See also

- [[06-data-access]] — the DB read/write API used to reproduce bugs and walk data.
- [[07-api-reference]] — the class catalogue (`gramps.gen.lib`, report/docgen APIs).
- [[08-testing]] — the `unittest` runner, discovery, and the `test/` package layout.
- [[16-guidelines]] — the normative MUST/SHOULD rules these tutorials obey.
- [Report-writing tutorial](wiki:Report-writing_tutorial),
  [Report API](wiki:Report_API), [Report Generation](wiki:Report_Generation) — depth on
  the docgen abstraction.
- [Quick Views](wiki:Quick_Views), [Simple Access API](wiki:Simple_Access_API) — the
  Quick View read surface.

<!--wiki:{{stub}}-->
