import os
os.environ.setdefault('GRAMPS_RESOURCES', '/workspace/gramps')
from gramps.gen.lib.date import Date
from gramps.gen.utils.grampslocale import GrampsLocale

loc = GrampsLocale(lang="en_GB")
displayer = loc.date_displayer
parser = loc.date_parser

fails = []
count = 0
for calendar in (Date.CAL_GREGORIAN, Date.CAL_JULIAN):
    for quality in (Date.QUAL_NONE, Date.QUAL_ESTIMATED, Date.QUAL_CALCULATED):
        for modifier in (Date.MOD_NONE, Date.MOD_BEFORE, Date.MOD_AFTER, Date.MOD_ABOUT,
                         Date.MOD_FROM, Date.MOD_TO):
            for slash1 in (False, True):
                for month in (2, 6, 12):
                    d = Date()
                    # day = 0  => partial (month+year, no day)
                    d.set(quality, modifier, calendar, (0, month, 1789, slash1))
                    for fi in range(len(displayer.formats)):
                        displayer.set_format(fi)
                        shown = displayer.display(d)
                        parsed = parser.parse(shown)
                        count += 1
                        if not d.is_equal(parsed):
                            fails.append((fi, calendar, quality, modifier, slash1, month, shown,
                                          parsed.get_modifier()))

print(f"checked {count} partial-date round trips")
print(f"FAILURES: {len(fails)}")
for f in fails[:60]:
    print(f)
