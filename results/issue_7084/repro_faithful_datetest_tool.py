import sys, os
sys.path.insert(0, "/home/eddie/workspace/gramps-6.1")
os.environ.setdefault("GRAMPS_RESOURCES", "/home/eddie/workspace/gramps-6.1")
from gramps.gen.datehandler import parser as _dp, displayer as _dd
from gramps.gen.lib.date import Date

# Faithful reproduction of dateparserdisplaytest.py date generation
def gen_all():
    dates = []
    d_year = 1789
    for calendar in (Date.CAL_GREGORIAN, Date.CAL_JULIAN):
        for quality in (Date.QUAL_NONE, Date.QUAL_ESTIMATED, Date.QUAL_CALCULATED):
            for modifier in (Date.MOD_NONE, Date.MOD_BEFORE, Date.MOD_AFTER, Date.MOD_ABOUT):
                for slash1 in (False, True):
                    for month in range(0, 13):
                        for day in (0, 5, 27):
                            if not month and day: continue
                            d = Date(); d.set(quality, modifier, calendar, (day, month, d_year, slash1), "Text comment"); dates.append(d)
            for modifier in (Date.MOD_RANGE, Date.MOD_SPAN):
                for slash1 in (False, True):
                    for slash2 in (False, True):
                        for month in range(0, 13):
                            for day in (0, 5, 27):
                                if not month and day: continue
                                d = Date(); d.set(quality, modifier, calendar, (day, month, d_year, slash1, day, month, d_year+87, slash2), "Text comment"); dates.append(d)
                                if not month: continue
                                d = Date(); d.set(quality, modifier, calendar, (day, month, d_year, slash1, day, 13-month, d_year+87, slash2), "Text comment"); dates.append(d)
                                if not day: continue
                                d = Date(); d.set(quality, modifier, calendar, (day, month, d_year, slash1, 32-day, month, d_year+87, slash2), "Text comment"); dates.append(d)
                                d = Date(); d.set(quality, modifier, calendar, (day, month, d_year, slash1, 32-day, 13-month, d_year+87, slash2), "Text comment"); dates.append(d)
            d = Date(); d.set(quality, Date.MOD_TEXTONLY, calendar, Date.EMPTY, "This is a textual date"); dates.append(d)
    return dates

fails = 0
for fmt in range(len(_dd.formats)):
    _dd.set_format(fmt)
    for d in gen_all():
        s = _dd.display(d)
        nd = _dp.parse(s)
        if d.get_modifier() != Date.MOD_TEXTONLY and nd.get_modifier() == Date.MOD_TEXTONLY:
            fails += 1
            if fails <= 30:
                print("TOOL-FAIL fmt", fmt, "src mod", d.get_modifier(), "qual", d.get_quality(), "->", repr(s))
print("TOTAL tool failures (TEXTONLY regressions) across all formats:", fails)
