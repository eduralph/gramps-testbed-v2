# Verify-first reproduction for Mantis 7084 (partial-date display->parse round-trip).
# Drives the PRODUCTION gramps.gen.datehandler parser/displayer (no re-implementation),
# headless (gen-only, no gi/GUI import). Point GRAMPS_SRC at a maintenance/gramps61
# checkout; defaults to the sibling worktree.
#   GRAMPS_SRC=/path/to/gramps-6.1 python3 verify_partial_roundtrip.py
# Expected on gramps61: "total fails: 0" — the reported defect does NOT reproduce.
import os, sys

GRAMPS_SRC = os.environ.get("GRAMPS_SRC", "/home/eddie/workspace/gramps-6.1")
os.environ.setdefault("GRAMPS_RESOURCES", GRAMPS_SRC)
sys.path.insert(0, GRAMPS_SRC)

import locale
try:
    locale.setlocale(locale.LC_ALL, "en_GB.utf-8")
except Exception as e:
    print("locale set failed:", e)

from gramps.gen.datehandler import parser, displayer
from gramps.gen.lib.date import Date


def make(mod, qual, y, m, d=0, slash=False):
    dt = Date()
    dt.set(quality=qual, modifier=mod, value=(d, m, y, slash))
    return dt


def make_span(mod, qual, y1, m1, y2, m2, s1=False, s2=False):
    dt = Date()
    dt.set(quality=qual, modifier=mod, value=(0, m1, y1, s1, 0, m2, y2, s2))
    return dt


mods = [Date.MOD_NONE, Date.MOD_BEFORE, Date.MOD_AFTER, Date.MOD_ABOUT,
        Date.MOD_FROM, Date.MOD_TO]
quals = [Date.QUAL_NONE, Date.QUAL_ESTIMATED, Date.QUAL_CALCULATED]

# Partial-date (month + year, no day) sweep across every modifier/quality/slash and
# every display format — the reporter's whole category, not one example.
tests = []
for mod in mods:
    for qual in quals:
        for (m, y) in [(5, 1900), (1, 1847), (12, 1066)]:
            tests.append((f"mod{mod}/qual{qual}/{m}-{y}",
                          make(mod, qual, y, m)))
            # dual-year "slash" partial date
            tests.append((f"mod{mod}/qual{qual}/{m}-{y}slash",
                          make(mod, qual, y, m, 0, True)))

# Partial-date spans (RANGE = between/and, SPAN = from/to), month+year no day.
for mod in (Date.MOD_RANGE, Date.MOD_SPAN):
    for qual in quals:
        for s1 in (False, True):
            for s2 in (False, True):
                tests.append((f"span{mod}/qual{qual}/{s1}{s2}",
                              make_span(mod, qual, 1847, 1, 1900, 5, s1, s2)))

print("formats:", displayer.formats)
print("cases per format:", len(tests))
fails = 0
for fmt in range(len(displayer.formats)):
    displayer.set_format(fmt)
    for label, dt in tests:
        shown = displayer.display(dt)
        parsed = parser.parse(shown)
        ok = parsed.is_equal(dt)
        is_text = parsed.get_modifier() == Date.MOD_TEXTONLY
        if not ok:
            fails += 1
            print(f"FAIL fmt={fmt}({displayer.formats[fmt]!r}) {label:22} "
                  f"display={shown!r:26} parsed_mod={parsed.get_modifier()} text={is_text}")
print("total fails:", fails)
