# Processing note — 820-description-resync

This bundle has **no `publish.json`**: it is a prose-only PR-description resync, so
"publishing" is an **in-place edit of the existing PR body**, not a new draft PR.

## Processed — 2026-06-16
- The accepted artifact (built/verified against HEAD `1466491ab`, 2026-06-13) had gone
  **stale**: commit `06b95bc` ("Strip the dependency detector and TMG test split out of the
  CI PR") removed `tests/test_addon_dependencies.py` and the TMGimporter test split, but the
  description still listed them as shipped.
- **Re-resynced** `pr-820-description.md` against the current HEAD `06b95bc` (22 commits,
  12 files): dropped the detector + TMGimporter-split content, appended the strip commit to
  the commit table. Gate policy was re-verified and unchanged (sole advisory job =
  Addon Structure).
- **Pushed** the resynced body to addons-source PR 820 via `gh pr edit 820 --body-file`;
  confirmed the live body matches `pr-820-description.md`.

Tracks addons-source fork issue #48-family work (PR 820, Mantis FR 9393). The detector and
TMG split it once described now live in their own submissions (addons-source PRs 948 / 949 /
952).
