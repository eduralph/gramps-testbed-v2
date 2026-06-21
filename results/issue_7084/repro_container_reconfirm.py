# Issue 7084 verify-first reproduction — drives the PRODUCTION en_GB
# date_parser/date_displayer (the same objects the DateTest tool uses).
# Run in the sanctioned gramps-testbed:ubuntu-6.1.0 container against the
# gramps-6.1 worktree, GRAMPS_RESOURCES=. LC_ALL=en_GB.utf8.
from gramps.gen.utils.grampslocale import GrampsLocale
from gramps.gen.lib.date import Date

gl = GrampsLocale(lang='en_GB')
p = gl.date_parser
d = gl.date_displayer

tests = ['before May 1900', 'after May 1900', 'about May 1900',
         'estimated Jan 1847', 'calculated Jan 1847', 'May 1900',
         'Jan 1847', 'May 1900/01', 'before May 1900/01', 'before May 1945']
for t in tests:
    dt = p.parse(t)
    print('%-24s mod=%s qual=%s ymd=%s TEXTONLY=%s'
          % (t, dt.modifier, dt.quality, dt.get_ymd(),
             dt.modifier == Date.MOD_TEXTONLY))

fails = 0
checked = 0
mods = [Date.MOD_NONE, Date.MOD_BEFORE, Date.MOD_AFTER, Date.MOD_ABOUT]
quals = [Date.QUAL_NONE, Date.QUAL_ESTIMATED, Date.QUAL_CALCULATED]
for fmt in range(len(d.formats)):
    d.set_format(fmt)
    for mod in mods:
        for q in quals:
            for slash in (False, True):
                for month in (1, 5, 12):
                    for year in (1847, 1900, 1234):
                        src = Date()
                        src.set(quality=q, modifier=mod,
                                value=(0, month, year, slash))
                        s = d.display(src)
                        back = p.parse(s)
                        checked += 1
                        if back.modifier == Date.MOD_TEXTONLY:
                            fails += 1
                            print('FAIL fmt', fmt, 'src',
                                  (q, mod, slash, month, year), '->',
                                  repr(s), 'TEXTONLY')
                        elif ((back.get_year(), back.get_month())
                              != (year, month)
                              or back.modifier != mod
                              or back.quality != q):
                            fails += 1
                            print('MISMATCH fmt', fmt, repr(s), '->',
                                  back.get_ymd(), back.modifier, back.quality)
print('checked', checked, 'fails', fails)
