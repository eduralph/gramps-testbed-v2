import sys, os
sys.path.insert(0, "/home/eddie/workspace/gramps-6.1")
os.environ.setdefault("GRAMPS_RESOURCES", "/home/eddie/workspace/gramps-6.1")
import locale
try: locale.setlocale(locale.LC_ALL, "en_GB.utf8")
except Exception: pass
from gramps.gen.utils.grampslocale import GrampsLocale
from gramps.gen.lib.date import Date
gl=GrampsLocale(lang="en_GB"); dp=gl.date_parser
for s in ["before May 1900","after May 1900","about May 1900","estimated Jan 1847",
          "calculated Jan 1847","May 1900","Jan 1847","May 1900/01","before May 1900/01"]:
    d=dp.parse(s)
    print(f"{s:24s} mod={d.get_modifier()} qual={d.get_quality()} ymd={(d.get_year(),d.get_month(),d.get_day())} TEXTONLY={d.get_modifier()==Date.MOD_TEXTONLY}")
