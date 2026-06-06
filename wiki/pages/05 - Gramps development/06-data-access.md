---
title: "Gramps 6.1 Wiki Manual - Core Development - Data access"
categories: [Developers, Gramps 6.1]
managed: true
---
<!--wiki:{{man index|6.1}}-->

## Overview

The database API is the spine of Gramps core. Every view, every editor, every
import and export, and every report goes through the same `DbReadBase` /
`DbWriteBase` interface defined in
[`gramps/gen/db/base.py`](https://github.com/gramps-project/gramps/blob/maintenance/gramps61/gramps/gen/db/base.py).
As a core contributor you work not only with this interface but below it — on
the concrete backend, the serializer, the transaction machinery, and the
`gramps.gen.types` handle/ID types that the public API is annotated with.

This page is how-to and explanatory. The normative MUST/SHOULD rules it leans on
(transactions, `HandleError`, string-compared backlinks, handle vs ID) live in
[[16-guidelines]] under **Runtime**; cite that page in review, not this one.

You rarely construct a database. The running program threads a live `Db*`
instance through a `DbState`; in tests you open one yourself
(see [[08-testing]]). Either way, everything below is a method on that instance,
referred to here as `db`.

## The interface: `DbReadBase` / `DbWriteBase`

Two abstract base classes split read from write:

| Class | Defines | Source |
|-------|---------|--------|
| `DbReadBase` | accessors / getters / iterators — the read-only surface | `gramps/gen/db/base.py:57` |
| `DbWriteBase(DbReadBase)` | adds the mutators: `add_*`, `commit_*`, `remove_*` | `gramps/gen/db/base.py:1489` |

Read-only contexts (a proxy DB, the import-merge preview, a read-only view) are
typed against `DbReadBase` and never see the write methods. When you write a
function that only reads, annotate its parameter `DbReadBase`, not the concrete
class — it documents the contract and keeps the function usable in read-only
contexts.

Both base classes are *abstract*: the methods `raise NotImplementedError`. The
real behaviour is in the concrete backend below.

## The concrete backend: `DbGeneric` and DBAPI/SQLite

The class hierarchy on `maintenance/gramps61` is:

```text
DbReadBase, DbWriteBase            gramps/gen/db/base.py      (abstract interface)
        ▲
DbGeneric(DbWriteBase, DbReadBase) gramps/gen/db/generic.py:384
        ▲                          (backend-independent logic: txns, undo,
        │                           serialization, signals, cursors)
DBAPI(DbGeneric)                   gramps/plugins/db/dbapi/dbapi.py:103
                                   (the SQL specifics)
```

`DbGeneric` holds everything that does not depend on the storage engine.
`DBAPI` supplies only the SQL access code, talking to a
[PEP 249](https://peps.python.org/pep-0249/) connection — SQLite by default,
and that is the only configuration the project ships and tests. To stay
compatible with the historical format, DBAPI stores each object as a serialized
blob keyed by handle, and *also* writes selected flat fields (the Gramps ID,
the gender, the change time, …) into indexed SQL columns so lookups and sorts
can run in the database instead of unpickling every row.

### The legacy `bsddb` note

A `bsddb` backend still ships under
[`gramps/plugins/db/bsddb/`](https://github.com/gramps-project/gramps/tree/maintenance/gramps61/gramps/plugins/db/bsddb)
(`bsddb.gpr.py:31` still marks it `STABLE`), but it exists only to *open and
upgrade* old Berkeley-DB family trees. SQLite has been the default backend since
5.1 and is what new trees use. **Write core code against the `DbReadBase` /
`DbWriteBase` interface, never against a backend.** Do not branch on the
concrete class or assume SQLite-specific behaviour in `gramps.gen` — `gen` is
backend-agnostic by design ([[16-guidelines]] §Source structure).

## Primary objects vs secondary objects

The data model splits into two kinds of object, both defined in
[`gramps/gen/lib/`](https://github.com/gramps-project/gramps/tree/maintenance/gramps61/gramps/gen/lib):

- **Primary objects** are top-level: they have their own table, a handle, and a
  Gramps ID, and they can be looked up and cross-referenced directly. The nine
  are **Person, Family, Event, Place, Source, Citation, Repository, Media, Note**
  (`person.py`, `family.py`, `event.py`, `place.py`, `src.py`, `citation.py`,
  `repo.py`, `media.py`, `note.py`). **Tag** (`tag.py`) is also a top-level table
  object with its own table and handle, but it subclasses `TableObject`, **not**
  `PrimaryObject`, and has **no Gramps ID** — it is keyed and cross-referenced by
  handle only.
- **Secondary objects** have no table and no handle of their own. They are owned
  by a primary object and serialized inside it — `Name`, `Date`, `Address`,
  `Attribute`, `EventRef`, `ChildRef`, `LdsOrd`, and the rest. You reach them
  only through the primary object that holds them.

The `*Ref` secondary objects (`EventRef`, `ChildRef`, `MediaRef`,
`CitationRef`, …) are the connective tissue: each pairs a *handle* of a primary
object with metadata about the relationship (a role, a private flag, a
frequency). A `Person` does not hold `Event` objects — it holds an
`event_ref_list` of `EventRef`, each of whose `.ref` is an `EventHandle`.

## Handles vs Gramps IDs

Every primary object carries two identifiers, and conflating them is a recurring
bug:

| Identifier | Stable? | Shape | Role |
|------------|---------|-------|------|
| **Handle** | Yes — internal, assigned on add, never reused or changed | opaque hex string | the database key and every cross-reference |
| **Gramps ID** | No — user-editable | `I0001`, `F0001`, `E0001`, … | user-facing label, external interop |

The handle is generated from a timestamp plus random bits and is the key the
storage layer uses; it is never shown to the user. The Gramps ID is a
human-readable label the user can rename freely, and the **Reorder Gramps IDs**
tool rewrites them in bulk — so an ID you cached a moment ago may now point
nowhere. The rule ([[16-guidelines]] §Runtime): **traverse by handle, display
by Gramps ID.**

```python
# Right: keep handles for traversal
spouse = db.get_person_from_handle(spouse_handle)

# Right: show the user an ID
LOG.info("processing %s", person.gramps_id)

# Wrong: a stored ID can be reordered out from under you
person = db.get_person_from_gramps_id("I0001")
```

Annotate these as the distinct types they are, not bare `str`: use
`PersonHandle` / `PersonGrampsID` and their siblings from
[`gramps/gen/types.py`](https://github.com/gramps-project/gramps/blob/maintenance/gramps61/gramps/gen/types.py)
(`PersonHandle = NewType("PersonHandle", str)`, `types.py:41`;
`PersonGrampsID`, `types.py:65`). `mypy` is enforced in core CI
([[16-guidelines]] §Coding style), so the distinction is checked.

## Reading one object

Each primary class has both lookups — `get_<type>_from_handle` and
`get_<type>_from_gramps_id`:

```python
person = db.get_person_from_handle(handle)          # base.py:540
person = db.get_person_from_gramps_id("I0001")       # base.py:431
```

A missing or stale handle does not silently return `None` in the same way across
all callers — prefer to raise `HandleError` (from `gramps.gen.errors`) when the
caller expects the object to exist ([[16-guidelines]] §Runtime). Reuse an
existing exception before inventing one.

**Object lifetime.** Each getter returns a *fresh, detached copy*. Two calls
with the same handle return two independent objects; mutating one does not touch
the other, and neither is written back until you commit it. If two code paths
hold the same person in memory and both commit, the last write wins — keep a
single instance per object inside a transaction.

## Iterating

For sweeps over a whole type, use the generators — `iter_<plural>` for objects,
`iter_<type>_handles` for just the keys:

```python
for person in db.iter_people():            # base.py:1174
    ...

for handle in db.iter_person_handles():    # base.py:1234
    ...
```

These stream; they do not build a list. Iterating *handles* is cheaper than
iterating *objects* — deserializing each object costs, so only dereference when
you need the contents. `get_person_handles(sort_handles=False)` (`base.py:667`)
returns the full list when you genuinely need one. Counts are O(1) and never
require iteration:

```python
n = db.get_number_of_people()              # base.py:895
```

Each of the ten primary types has the matching `iter_*`, `get_*_handles`,
`iter_*_handles`, and `get_number_of_*` methods; see [[07-api-reference]] for
the full table.

## Backlinks: who references this object?

Forward references live on the object (a `Person` lists its `EventRef`s). The
*reverse* direction — "what refers to this handle?" — lives on the database:

```python
for class_name, ref_handle in db.find_backlink_handles(event.handle):
    if class_name == "Person":
        person = db.get_person_from_handle(ref_handle)
        ...
```

`find_backlink_handles` (`base.py:99`; DBAPI override at
`gramps/plugins/db/dbapi/dbapi.py:876`) is a generator yielding
`(class_name, handle)` tuples, where **`class_name` is the class name as a
`str`** — `"Person"`, `"Family"`, … — not the Python class object. Compare it as
a string:

```python
# Right
if class_name == "Person":
    ...

# Wrong — always False; the tuple holds a str, not the class
if class_name is Person:
    ...
```

This is exactly the trap [[16-guidelines]] §Runtime calls out. Optionally pass
`include_classes=["Person", "Family"]` to have the backend filter for you rather
than testing every tuple. Backlinks read an index but still scan it — useful for
orphan detection and reverse navigation, but not for a tight inner loop.

## Writing: the `DbTxn` pattern

**Every write goes through a transaction** ([[16-guidelines]] §Runtime — this is
a MUST). `DbTxn` (`gramps/gen/db/txn.py:52`; constructor
`__init__(self, msg, grampsdb, batch=False, **kwargs)`, `txn.py:103`) groups
commits into one undoable unit and records its message in the user's Undo
History, so the message must be descriptive and translated with `_()`:

```python
from gramps.gen.db import DbTxn

with DbTxn(_("Set person private"), db) as trans:
    person = db.get_person_from_handle(handle)
    person.set_privacy(True)
    db.commit_person(person, trans)        # base.py:1634
```

Three rules govern every write:

1. The transaction message is user-visible — make it descriptive and wrap it in
   `_()`.
2. The object you read is a copy; `db.commit_<type>(obj, trans)` writes it back.
   Mutating without committing changes nothing on disk.
3. Group related changes in one `DbTxn` so the user undoes them as one step.

### Add

`add_<type>(obj, trans)` inserts the object and assigns its handle (and, unless
`set_gid=False`, its Gramps ID):

```python
from gramps.gen.lib import Person, Name, Surname

with DbTxn(_("Add unknown person"), db) as trans:
    person = Person()
    name = Name()
    surname = Surname()
    surname.set_surname(family_name)
    name.add_surname(surname)
    person.set_primary_name(name)
    handle = db.add_person(person, trans)   # base.py:1550 — returns the handle
```

`add_person` signature is `add_person(self, person, transaction, set_gid=True)`
(`base.py:1550`); leave `set_gid=True` so the database allocates the next ID.
Call `find_next_person_gramps_id()` (`base.py:183`) only when you need the ID
*before* the add.

### Commit

Re-read, mutate, commit — the canonical edit, shown above. Use the
`commit_<type>` that matches the object: `commit_family`, `commit_event`, etc.

### Remove

`remove_<type>(handle, trans)` (`remove_person`, `base.py:1722`) takes the
*handle*, not the object. Removing a primary object does **not** clean up the
references other objects hold to it — those become dangling. When you remove,
either walk `find_backlink_handles` and commit the referrers in the *same*
transaction, or use the higher-level removal helpers that do this for you:

```python
with DbTxn(_("Remove person and references"), db) as trans:
    for class_name, ref_handle in db.find_backlink_handles(handle):
        # drop the reference from each referrer, then commit it in `trans`
        ...
    db.remove_person(handle, trans)
```

### Batch transactions

For large mechanical changes (imports, bulk tools) pass `batch=True`. A batch
transaction trades undo granularity and per-object signals for speed — it is not
individually undoable, so reserve it for operations the user runs as one
deliberate step. The default `batch=False` is correct for ordinary edits.

## Cursors: bulk reads

For a full pass over a type where you want raw throughput, a cursor is faster
than `iter_*` because it pulls rows in batches and skips per-object overhead.
The modern cursor is a context manager that iterates `(handle, raw_data)`
pairs:

```python
with db.get_person_cursor() as cursor:     # base.py:315
    for handle, raw_data in cursor:
        ...
```

The second element is the object's **serialized data**, not a constructed
`Person` (`DBAPI.get_person_cursor` returns `Cursor(self._iter_raw_person_data)`,
`gramps/plugins/db/dbapi/dbapi.py`; the row is read as
`(handle, serializer.string_to_data(...))`). If you need the live object, either
deserialize the row or — simpler, when the cursor's speed is not the point —
just iterate handles and call the getter:

```python
for handle in db.iter_person_handles():
    person = db.get_person_from_handle(handle)
    ...
```

Use the cursor when profiling shows the getter loop is the bottleneck;
otherwise the handle-then-getter loop is clearer and is what most core code
uses. Every primary type has its matching `get_<type>_cursor`.

## Testing data access

Open a real database against `example.gramps` — the canonical fixture, shipped
at `example/gramps/example.gramps` and `data/tests/example.gramps` — rather than
mocking `db`. A stub does not reproduce the cross-typed backlinks, reordered
IDs, and odd character data of a populated tree, so a mocked test can pass while
the real path is broken. Reproduce against `example.gramps` first
([[16-guidelines]] §Contributor workflow). Place the test as
`<module>_test.py` in a `test/` package beside the module and run it with
stdlib `unittest` — full mechanics in [[08-testing]] and [[16-guidelines]]
§Testing.

## See also

- [[05-fundamentals]] — the `gen` / `gui` / `plugins` layout this API sits in
- [[07-api-reference]] — the full per-type method inventory
- [[08-testing]] — opening a test database, `example.gramps`, the `_test.py` runner
- [[16-guidelines]] — the normative Runtime / Testing rules cited throughout
- [Using database API](wiki:Using_database_API) — the upstream standalone reference
- [Gramps Developer Reference](wiki:Gramps_6.1_Developer_Reference) — generated API docs

<!--wiki:{{stub}}-->
