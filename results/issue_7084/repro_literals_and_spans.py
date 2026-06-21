import os
os.environ.setdefault('GRAMPS_RESOURCES', '/workspace/gramps')
from gramps.gen.lib.date import Date
from gramps.gen.utils.grampslocale import GrampsLocale

loc = GrampsLocale(lang="en_GB")
parser = loc.date_parser

# Parse the reporter's literal strings (month-name partial dates) directly.
literals = [
    "before May 1900", "after May 1900", "about May 1900",
    "est May 1900", "estimated May 1900", "calc Jan 1847", "calculated Jan 1847",
    "May 1900", "Jan 1847", "May 1900/01", "from May 1900 to Jun 1901",
    "between May 1900 and Jun 1901", "before May 1900/01",
]
for s in literals:
    d = parser.parse(s)
    print(f"{s:32} -> mod={d.get_modifier()} qual={d.get_quality()} ymd={d.get_ymd()} "
          f"textonly={d.get_modifier()==Date.MOD_TEXTONLY} text={d.get_text()!r}")

# span/range partial dates round-trip via displayer
displayer = loc.date_displayer
fails = 0
count = 0
for quality in (Date.QUAL_NONE, Date.QUAL_ESTIMATED, Date.QUAL_CALCULATED):
    for modifier in (Date.MOD_RANGE, Date.MOD_SPAN):
        for slash1 in (False, True):
            for slash2 in (False, True):
                for month in (2, 6, 12):
                    d = Date()
                    d.set(quality, modifier, Date.CAL_GREGORIAN,
                          (0, month, 1789, slash1, 0, 13 - month, 1876, slash2))
                    for fi in range(len(displayer.formats)):
                        displayer.set_format(fi)
                        shown = displayer.display(d)
                        parsed = parser.parse(shown)
                        count += 1
                        if not d.is_equal(parsed):
                            fails += 1
                            print(f"SPAN FAIL fmt{fi} {shown!r} -> {parsed.get_modifier()}")
print(f"\nspan/range partial round trips checked={count} failures={fails}")
