"""Confirm the get_iterator-based algorithm from libcairodoc.py is fully
usable under the shipped GI stack: the iterator yields introspectable
PangoAttribute objects (the capability that bug 6208 / gnome 646788 lacked)."""
import gi
gi.require_version('Pango', '1.0')
from gi.repository import Pango

print('Pango typelib version:', Pango.version_string())

ok, attrlist, plaintext, accel = Pango.parse_markup(
    "<b>Bold</b> normal <i>italic</i> tail", -1, "\000")
print('parse_ok:', ok)
print('plaintext:', repr(plaintext))

# --- the exact API surface the workaround removed ---
it = attrlist.get_iterator()                     # was "not available"
print('get_iterator ->', type(it).__name__)
seen = 0
while True:
    vals = it.get_attrs()                        # bug 6208: returned unusable
    for attr in vals:
        newattr = attr.copy()                    # Attribute.copy()
        s, e = newattr.start_index, newattr.end_index  # readable + writable
        newattr.start_index = s
        newattr.end_index = e
        seen += 1
    if not it.next():
        break
print('introspectable attrs iterated:', seen)
assert hasattr(Pango.AttrList, 'get_iterator')
assert hasattr(Pango, 'AttrIterator')
assert seen > 0
print('RESULT: get_iterator path FULLY USABLE on shipped GI stack')
