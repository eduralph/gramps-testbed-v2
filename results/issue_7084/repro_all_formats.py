import sys
from gramps.gen.lib import Date
from gramps.gen.datehandler import parser as _dp
from gramps.gen.datehandler import displayer as _dd

print("num formats:", len(_dd.formats), _dd.formats)

# Build partial dates (month + year, no day) across modifier/quality/slash/calendar.
dates = []
d_year = 1789
for calendar in (Date.CAL_GREGORIAN, Date.CAL_JULIAN):
    for quality in (Date.QUAL_NONE, Date.QUAL_ESTIMATED, Date.QUAL_CALCULATED):
        for modifier in (Date.MOD_NONE, Date.MOD_BEFORE, Date.MOD_AFTER, Date.MOD_ABOUT):
            for slash1 in (False, True):
                for month in range(1, 13):
                    d = Date()
                    d.set(quality, modifier, calendar, (0, month, d_year, slash1), "Text comment")
                    dates.append(d)

for fmt in range(len(_dd.formats)):
    _dd.set_format(fmt)
    fails = []
    for dateval in dates:
        try:
            datestr = _dd.display(dateval)
            ndate = _dp.parse(datestr)
        except Exception as e:
            fails.append((dateval, "EXC", str(e)))
            continue
        if ndate.get_modifier() == Date.MOD_TEXTONLY:
            fails.append((dateval, datestr, ndate.get_text()))
    print(f"--- format {fmt} ({_dd.formats[fmt]!r}): {len(fails)} partial-date TEXTONLY fails / {len(dates)}")
    for item in fails[:8]:
        d = item[0]
        print(f"    mod={d.get_modifier()} qual={d.get_quality()} cal={d.get_calendar()} ymd={d.get_ymd()} slash={d.get_slash()} -> {item[1]!r}")
