# Brief — issue 13518 / dbman-rcs-stderr-bytes-decode

> The Plan artifact (docs 02 §PLAN). Human-authored. Do reads ONLY this file.

- **Slug:** dbman-rcs-stderr-bytes-decode
- **Defect:** In gramps/gui/dbman.py the RCS (archive) helpers open a subprocess with
  `stderr=subprocess.PIPE` (binary mode) and then build an error message with
  `"\n".join(proc.stderr.readlines())`. `readlines()` returns `bytes`, so joining them
  into a `str` raises `TypeError: sequence item 0: expected str instance, bytes found`,
  crashing the operation whenever the subprocess writes anything to stderr. Five sites
  do this: lines 637, 809, 1179, 1224, 1255. The reported repro is renaming an archived
  backup in the Tree Manager; check-in/check-out/archive hit the same defect.
- **Success criterion:** When an RCS subprocess in dbman.py writes to stderr, the code
  that assembles the error message decodes the bytes to `str` and produces a usable
  string message without raising `TypeError`. Demonstrable by C4-verify: a test that
  routes a stubbed subprocess whose `stderr.readlines()` returns `bytes` through the
  production message-assembly path returns a `str` and does not raise.
- **Invariant to restore:** n/a — non-structural behavioural bug fix (principles.md
  §1.1). (Correctness requirement: bytes read from a binary subprocess pipe must be
  decoded to text before string operations.)
- **Repo + branch target:** gramps-project/gramps @ maintenance/gramps61
- **Surfaces:** data — the defect and its test live in the message-assembly logic, not
  the GUI widgets; the Tree Manager is only how a user triggers it.
- **Difficulty:** low — one file; five near-identical sites; localized.
- **Scope:** every site in dbman.py that joins `proc.stderr.readlines()` into a message
  string must decode the bytes to text first, so an RCS subprocess that emits stderr no
  longer crashes the operation. / out of scope: switching unrelated subprocess calls to
  text mode; reworking the RCS feature; the secondary `NameError: name 'self' is not
  defined` one commenter saw on 6.0.3 — that was a mis-applied-patch artifact (wrong line
  offsets), confirmed in the thread, not a real defect in the current tree.
- **Repro instruction:** On maintenance/gramps61 with `rcs` installed: open the Tree
  Manager and Rename a backup/archive of a family tree → `TypeError`. For the regression
  test, drive one of the dbman message-assembly code paths with a fake `subprocess.Popen`
  whose `stderr.readlines()` returns `[b"...error...\n"]`; assert pre-fix raises
  `TypeError` and post-fix returns the decoded message.
- **Test file:** gramps/gui/test/dbman_test.py — must fail pre-fix (TypeError on bytes)
  and pass post-fix. If a testable seam is needed to reach the decode without a real RCS
  subprocess or the GUI, the test MUST exercise the PRODUCTION path (production routes
  through the same unit the test drives), not a parallel copy (principles.md §3.4).
- **Citations expected:** Do must cite path:line on maintenance/gramps61 for every change.
- **New/removed files:** adds gramps/gui/test/dbman_test.py (no translatable strings) →
  po/POTFILES.skip. (gramps/gui/test/ already exists.)
- **Prior-art check (triage cycles):** searched gramps/gui/dbman.py history on
  upstream/maintenance/gramps61 (pinned worktree) — all five `"\n".join(proc.stderr.
  readlines())` sites are present and undecoded; recent dbman.py commits are unrelated
  (black reformat, license text, list expansion). No merged/open/closed PR for this
  decode defect. Not previously fixed.
- **Mantis:** 13518
- **Disposition hint:** likely-fix

## STOP discipline

Draft only until Check sign-off. Pushing to a feature/draft branch and opening a
draft PR MAY happen during the cycle (useful for CI). The PR MUST NOT be marked ready
before sign-off accepts.
