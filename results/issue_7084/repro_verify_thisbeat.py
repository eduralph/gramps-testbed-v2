"""Verify-first reproduction for issue 7084 — run this beat, not recalled.

Drives the PRODUCTION en_GB DateParser / DateDisplay (the same objects the
DateTest tool and the app use). Replicates the tool's exact date generation
(dateparserdisplaytest.py) for the partial-date classes, across ALL 6 display
formats, and applies BOTH:
  (a) the tool's own fail criterion: src.mod != TEXTONLY and parsed.mod == TEXTONLY
  (b) a stricter EQUAL-Date check: modifier, quality, year, month, day, slash.
Focus: partial dates (month+year, no day) under modifier/quality/dual-year.
"""

import os
import sys

GRAMPS_CHECKOUT = "/home/eddie/workspace/gramps-6.1"
sys.path.insert(0, GRAMPS_CHECKOUT)
os.environ.setdefault("GRAMPS_RESOURCES", GRAMPS_CHECKOUT)
os.environ["LC_ALL"] = "en_GB.utf8"

from gramps.gen.lib.date import Date
from gramps.gen.utils.grampslocale import GrampsLocale

gl = GrampsLocale(lang="en_GB")
dd = gl.date_displayer
dp = gl.date_parser

D = Date

literal_fail = 0
print("=== brief representative literal strings ===")
for s in [
    "before May 1900",
    "after May 1900",
    "about May 1900",
    "estimated Jan 1847",
    "calculated Jan 1847",
    "May 1900",
    "Jan 1847",
    "May 1900/01",
    "before May 1900/01",
    "before May 1945",
]:
    d = dp.parse(s)
    to = d.get_modifier() == D.MOD_TEXTONLY
    if to:
        literal_fail += 1
    print(
        f"{s:25s} mod={d.get_modifier()} qual={d.get_quality()} "
        f"ymd={d.get_ymd()} TEXTONLY={to}"
    )
print("literal MOD_TEXTONLY failures:", literal_fail)

# Partial-date category sweep across all 6 display formats.
formats = list(range(len(dd.formats)))
tool_fail = 0
strict_fail = 0
checked = 0
for fmt in formats:
    dd.set_format(fmt)
    for calendar in (D.CAL_GREGORIAN, D.CAL_JULIAN):
        for quality in (D.QUAL_NONE, D.QUAL_ESTIMATED, D.QUAL_CALCULATED):
            for modifier in (D.MOD_NONE, D.MOD_BEFORE, D.MOD_AFTER, D.MOD_ABOUT):
                for slash1 in (False, True):
                    for month in range(1, 13):  # partial: month set, day 0
                        src = Date()
                        src.set(
                            quality,
                            modifier,
                            calendar,
                            (0, month, 1789, slash1),
                            "Text comment",
                        )
                        datestr = dd.display(src)
                        parsed = dp.parse(datestr)
                        checked += 1
                        if parsed.get_modifier() == D.MOD_TEXTONLY:
                            tool_fail += 1
                            print(f"  TOOL-FAIL fmt={fmt} '{datestr}' -> TEXTONLY")
                            continue
                        # strict equal compare on the partial-date dimensions
                        if (
                            parsed.get_modifier() != modifier
                            or parsed.get_quality() != quality
                            or parsed.get_year() != src.get_year()
                            or parsed.get_month() != month
                            or parsed.get_day() != 0
                        ):
                            strict_fail += 1
                            print(
                                f"  STRICT-FAIL fmt={fmt} '{datestr}' "
                                f"src=({src.get_ymd()},m{modifier},q{quality}) "
                                f"parsed=({parsed.get_ymd()},m{parsed.get_modifier()},"
                                f"q{parsed.get_quality()})"
                            )
print(
    f"partial-date sweep: checked={checked} tool_fail={tool_fail} "
    f"strict_fail={strict_fail}"
)
