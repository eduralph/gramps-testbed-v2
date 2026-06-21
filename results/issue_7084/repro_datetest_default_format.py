import sys
from gramps.gen.lib import Date
from gramps.gen.datehandler import parser as _dp
from gramps.gen.datehandler import displayer as _dd

# Mirror dateparserdisplaytest.py generation loop, but in-memory.
dates = []
d_year = 1789
for calendar in (Date.CAL_GREGORIAN, Date.CAL_JULIAN):
    for quality in (Date.QUAL_NONE, Date.QUAL_ESTIMATED, Date.QUAL_CALCULATED):
        for modifier in (Date.MOD_NONE, Date.MOD_BEFORE, Date.MOD_AFTER, Date.MOD_ABOUT):
            for slash1 in (False, True):
                for month in range(0, 13):
                    for day in (0, 5, 27):
                        if not month and day:
                            continue
                        d = Date()
                        d.set(quality, modifier, calendar, (day, month, d_year, slash1), "Text comment")
                        dates.append(d)
        for modifier in (Date.MOD_RANGE, Date.MOD_SPAN):
            for slash1 in (False, True):
                for slash2 in (False, True):
                    for month in range(0, 13):
                        for day in (0, 5, 27):
                            if not month and day:
                                continue
                            d = Date()
                            d.set(quality, modifier, calendar,
                                  (day, month, d_year, slash1, day, month, d_year + 87, slash2), "Text comment")
                            dates.append(d)

fails = []
partial_fails = []
for dateval in dates:
    try:
        datestr = _dd.display(dateval)
        ndate = _dp.parse(datestr)
    except Exception as e:
        fails.append((dateval, "EXC:" + str(e)))
        continue
    if dateval.get_modifier() != Date.MOD_TEXTONLY and ndate.get_modifier() == Date.MOD_TEXTONLY:
        fails.append((dateval, datestr, ndate.get_text()))
        ymd = dateval.get_ymd()
        is_partial = (ymd[1] != 0 and ymd[2] == 0)  # month present, day absent
        if is_partial:
            partial_fails.append((dateval, datestr, ndate.get_text()))

print("total dates:", len(dates))
print("total TEXTONLY fails:", len(fails))
print("partial-date (month, no day) fails:", len(partial_fails))
for d, s, t in fails[:40]:
    ymd = d.get_ymd()
    print(f"  mod={d.get_modifier()} qual={d.get_quality()} cal={d.get_calendar()} ymd={ymd} slash={d.get_slash()} -> display={s!r} -> TEXTONLY {t!r}")
