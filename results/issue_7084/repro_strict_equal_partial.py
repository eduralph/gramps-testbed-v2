import sys, os
sys.path.insert(0, "/home/eddie/workspace/gramps-6.1")
os.environ.setdefault("GRAMPS_RESOURCES", "/home/eddie/workspace/gramps-6.1")
import locale
try: locale.setlocale(locale.LC_ALL, "en_GB.utf8")
except Exception as e: print("locale warn", e)
from gramps.gen.utils.grampslocale import GrampsLocale
from gramps.gen.lib.date import Date

gl = GrampsLocale(lang="en_GB")
dp = gl.date_parser
dd = gl.date_displayer

fails=0; checked=0; textonly=0
for fmt in range(len(dd.formats)):
    dd.set_format(fmt)
    for quality in (Date.QUAL_NONE, Date.QUAL_ESTIMATED, Date.QUAL_CALCULATED):
        for modifier in (Date.MOD_NONE, Date.MOD_BEFORE, Date.MOD_AFTER, Date.MOD_ABOUT):
            for slash in (False, True):
                for month in range(1,13):
                    for year in (1847, 1900, 1234):
                        d=Date(); d.set(quality, modifier, Date.CAL_GREGORIAN, (0, month, year, slash), "")
                        s=dd.display(d)
                        nd=dp.parse(s)
                        checked+=1
                        if nd.get_modifier()==Date.MOD_TEXTONLY:
                            textonly+=1
                        dv=nd.get_dmy(get_slash=True) if hasattr(nd,'get_dmy') else None
                        ok=(nd.get_modifier()==modifier and nd.get_quality()==quality
                                and nd.get_year()==year
                                and nd.get_month()==month and nd.get_day()==0
                                and bool(nd.get_slash())==slash)
                        if not ok:
                            fails+=1
                            if fails<=25:
                                print("FAIL fmt",fmt,"q",quality,"m",modifier,"slash",slash,"->",repr(s),
                                      "got mod",nd.get_modifier(),"q",nd.get_quality(),"ymd",(nd.get_year(),nd.get_month(),nd.get_day()),"slash",nd.get_slash())
print("checked",checked,"strict-fails",fails,"textonly",textonly)
