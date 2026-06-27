# Build notes — issue 5965 / descendantslines-stale-report-name

## Success criterion (from brief)
Running DescendantsLines twice with different names/options produces output whose
used name matches the *current* run, with no carry-over of the prior session's
name. Demonstrable by C4-verify driving the addon's report-name/output derivation
on a fixture, if a seam exists.

## Root cause (verified against source, not recalled)
`DescendantsLines.py:316-320` (target `addons-source @ maintenance/gramps60`,
identical on gramps61) derives the graphic's output filename solely from the
report's own persisted "Destination" option:

```python
self.output_fn = self.options['output_fn']
self.output_fn = '%s.%s' % (os.path.splitext(self.output_fn)[0],
                            self.output_fmt.lower())
```

`output_fn` is a `DestinationOption` (`DescendantsLines.py:1548-1551`) whose value
is saved in the report's option state and **persists across Gramps sessions**.
The addon writes its cairo graphic to that path in `write_report` →
`draw_file(p, self.output_fn, …)` (`DescendantsLines.py:455`), entirely
independent of the destination the user selects for the current run in the
standard report dialog's "Document Options" (which the framework records as
`options_class.get_output()` and opens as `self.doc` —
`gramps/gen/plug/report/_reportbase.py:56-59`, verified in the gramps-6.0
checkout).

So the graphic always lands on the *previous* session's "Destination" value — the
reporter's "stale output filename which … overrides each new report"
(notes.json, dougbain 2012-08-04) and user396's observation that the standard
"Document Options" path "doesn't help the user". This is exactly the
"option/name read from saved option state instead of the current invocation"
the brief names.

## Fix
Derive the graphic filename from the destination chosen for the **current** run
(`options_class.get_output()`), falling back to the persisted option only when
the current run supplies no destination (e.g. CLI without `-O`). Extracted into a
pure helper `DescendantsLines/descendantslines_output.py::derive_output_filename`
and routed production through it (`DescendantsLines.py:316-324`).

`options_class.get_output()` returns `self.handler.output`
(`gramps/gen/plug/report/_options.py:914-920`) — the document destination the
user picked for this invocation — so the output now tracks the current run and
carries no prior-session name.

### Clobber guard
The standard report document is opened on `get_output()` and **closed (written)
after** `write_report` returns (`_reportbase.py:59,95-96`). If the graphic were
written to the exact same path, the document's `close()` would overwrite it.
`derive_output_filename` therefore gives the graphic a distinct `-chart` suffix
when the derived name would equal the current document destination. (When the
addon's `output_fmt` differs from the document format — the common case — the
extensions already differ and no suffix is needed.)

## Why an extracted import-light module (and not a test of the report directly)
`DescendantsLines.py` imports `cairo`, `gramps.plugins.lib.libtreebase` (`*`),
etc. at load, so it cannot be imported under the headless C4 runner. The
filename logic is extracted into a `gi`-free module; **production calls the same
function the test drives** (no parallel copy — §3.4): `DescendantsLines.py:318`
and the test both call `derive_output_filename`.

## Test — red→green proven
`DescendantsLines/tests/test_descendantslines_name.py` drives
`derive_output_filename`:
- current-run destination overrides the stale persisted option (no carry-over);
- two runs with different current destinations yield different names (the
  "run twice" criterion);
- fallback to the option when no current destination;
- distinctness from the document path (clobber guard).

Verified locally (sandbox blocked the dockerised `run-verify.sh`, so I reproduced
its exact red/green contract with the real test + helper):
- GREEN: helper present → all 4 tests pass.
- RED: remove the added `descendantslines_output.py` (what the verifier's red leg
  does to `PROD_NEW`) + keep the test → `ModuleNotFoundError:
  descendantslines_output` → fail.

Patch dry-run applies cleanly to both `addons-source-6.0` and `addons-source-6.1`
(the C4 matrix legs); `DescendantsLines.py` is byte-identical on both branches and
the three new files exist on neither.

## Alternatives considered / rejected
- **Merge the graphic into `self.doc` (draw a proper CATEGORY_DRAW document).**
  This is the architecturally "correct" removal of the dual-output design and
  would also fix the blank-ODT symptom, but it rewrites the entire rendering path
  (`draw_file`/`PNGWriter`/`draw_tree`, ~250 lines of cairo in
  `DescendantsLines.py:495-1511`) onto the gramps draw-doc API — squarely the
  "graph-drawing logic itself", which the brief puts **out of scope**. It is also
  not headlessly verifiable. Rejected as out-of-scope and disproportionate.
- **Just clear/reset the persisted `output_fn` each run.** Doesn't restore the
  invariant — it throws away the user's choice rather than honouring the current
  run's destination, and still ignores the "Document Options" filename the
  reporter was actually setting.
- **Write the graphic to `get_output()` verbatim.** Rejected: the document's
  `close()` runs after the graphic is drawn and would clobber it when paths
  coincide (hence the `-chart` guard).

## Scope / out of scope
- The blank-ODT/PDF symptom shares the same dual-output root cause but its full
  resolution is the out-of-scope draw-doc rewrite above; not addressed here.
- No `.gpr.py` version bump: the version line differs between gramps60 (1.1.14)
  and gramps61 (1.1.16), so bumping it would break cross-version `git apply` on
  the C4 matrix. A per-branch listing bump is a publish-time concern for the
  human/publisher on `maintenance/gramps60`.

## POTFILES
N/A — addon change, no core `po/POTFILES.*`. The new helper has no translatable
(`_()`) strings; the test is a test. (Brief: "addon test (no core POTFILES)".)

## Residual / verification note
The cross-session GUI behaviour itself (open dialog, run, reopen next session)
cannot be automated headlessly; the unit test pins the derivation seam that
produced the stale name. Manual repro for the human: Reports → Graphs →
DescendantsLines; set "Document Options → Filename" to name A, run; reopen and set
it to name B, run — with the fix the graphic is written for B (as `B.<fmt>` or
`B-chart.<fmt>`), not A.
