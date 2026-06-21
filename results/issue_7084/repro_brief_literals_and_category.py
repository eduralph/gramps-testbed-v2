import os
os.environ.setdefault('GRAMPS_RESOURCES', '/workspace/gramps')
from gramps.gen.lib.date import Date
from gramps.gen.utils.grampslocale import GrampsLocale

loc = GrampsLocale(lang="en_GB")
parser = loc.date_parser
displayer = loc.date_displayer

print("=== brief representative literal strings ===")
literals = [
    "before May 1900", "after May 1900", "about May 1900",
    "estimated Jan 1847", "calculated Jan 1847",
    "May 1900", "Jan 1847", "May 1900/01", "before May 1900/01",
]
bad = 0
for s in literals:
    d = parser.parse(s)
    to = d.get_modifier() == Date.MOD_TEXTONLY
    if to:
        bad += 1
    print(f"{s:24} -> mod={d.get_modifier()} qual={d.get_quality()} "
          f"ymd={d.get_ymd()} TEXTONLY={to} text={d.get_text()!r}")
print(f"literal MOD_TEXTONLY failures: {bad}")

print("\n=== partial-date category display->reparse sweep ===")
fails = []
count = 0
for calendar in (Date.CAL_GREGORIAN, Date.CAL_JULIAN):
    for quality in (Date.QUAL_NONE, Date.QUAL_ESTIMATED, Date.QUAL_CALCULATED):
        for modifier in (Date.MOD_NONE, Date.MOD_BEFORE, Date.MOD_AFTER,
                         Date.MOD_ABOUT, Date.MOD_FROM, Date.MOD_TO):
            for slash1 in (False, True):
                for month in (1, 2, 6, 12):
                    d = Date()
                    d.set(quality, modifier, calendar, (0, month, 1847, slash1))
                    for fi in range(len(displayer.formats)):
                        displayer.set_format(fi)
                        shown = displayer.display(d)
                        parsed = parser.parse(shown)
                        count += 1
                        if not d.is_equal(parsed):
                            fails.append((fi, calendar, quality, modifier,
                                          slash1, month, shown,
                                          parsed.get_modifier()))
print(f"checked {count} partial-date round trips; FAILURES={len(fails)}")
for f in fails[:60]:
    print(f)
