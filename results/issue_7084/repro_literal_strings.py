from gramps.gen.lib import Date
from gramps.gen.datehandler import parser as _dp
from gramps.gen.datehandler import displayer as _dd

literals = [
    "before May 1900", "about May 1900", "after May 1900",
    "estimated Jan 1847", "calculated Jan 1847",
    "before Jan 1847", "about Jan 1847",
    "May 1900/01", "before May 1900/01", "about May 1900/01",
    "Mar 1789", "before Mar 1789", "est May 1900",
]
print("=== literal reporter-class strings: parse, then display->reparse round-trip ===")
for s in literals:
    d = _dp.parse(s)
    to = d.get_modifier() == Date.MOD_TEXTONLY
    disp = _dd.display(d)
    d2 = _dp.parse(disp)
    rt = d2.is_equal(d)
    print(f"{s!r:22} -> parsed TEXTONLY={to} ymd={d.get_ymd()} mod={d.get_modifier()} | display={disp!r} reparse_equal={rt}")
